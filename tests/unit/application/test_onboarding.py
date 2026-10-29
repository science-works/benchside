import io
import json
import sys

import pytest

from benchside.application.app import App
from benchside.application.bridge import run
from benchside.cli.main import main
from benchside.config import configure_local_storage, resolve_paths
from benchside.domain.shared.error import BenchsideError


def test_shared_project_keeps_records_and_per_session_app_metadata(paths):
    first = App(paths).run(
        {"action": "setup", "host": "claude", "project_key": "shared", "title": "Extraction study"}
    )
    second = App(paths).run(
        {"action": "setup", "host": "chatgpt", "project_id": first["project_id"]}
    )
    assert first["project_id"] == second["project_id"]
    assert first["session_id"] != second["session_id"]
    assert App(paths).run({"action": "projects"}) == [
        {"project_id": first["project_id"], "title": "Extraction study"}
    ]
    # Another app opening the project must not overwrite the first session's host.
    original = App(paths).run({"action": "start", "role": "methods-clinic", **first})
    assert original["sitting"]["host"] == "claude"
    context = {**first, "sitting_id": original["sitting"]["id"]}
    App(paths).run(
        {
            "action": "decide",
            "decision": "Run spike controls",
            "rationale": "Locate loss",
            **context,
        }
    )
    resumed = App(paths).run({"action": "start", "role": "methods-clinic", **second})
    assert resumed["sitting"]["id"] == context["sitting_id"]
    assert resumed["recall"]["recent_decisions"][0]["decision"] == "Run spike controls"
    other_role = App(paths).run({"action": "start", "role": "study-design", **second})
    assert other_role["sitting"]["host"] == "chatgpt"
    other_project = App(paths).run({"action": "setup", "project_key": "other"})
    with pytest.raises(BenchsideError, match="another project"):
        App(paths).run(
            {"action": "start", "role": "pi", **second, "project_id": other_project["project_id"]}
        )


def test_unknown_existing_project_is_not_created(paths):
    with pytest.raises(BenchsideError, match="existing project"):
        App(paths).run({"action": "setup", "project_id": "p-" + "a" * 32})
    assert App(paths).run({"action": "projects"}) == []


def test_local_choice_is_remembered_without_migration(monkeypatch, tmp_path):
    monkeypatch.delenv("BENCHSIDE_HOME", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    old = resolve_paths().home
    old.mkdir(parents=True)
    (old / "untouched").write_text("original records")
    target = tmp_path / "research records"
    configured = configure_local_storage(str(target))
    assert not configured["migrated"]
    assert resolve_paths().home == target
    assert run({"action": "storage.check", "token": configured["token"]})["matched"]
    assert (old / "untouched").read_text() == "original records"
    assert not (target / "untouched").exists()
    monkeypatch.setenv("BENCHSIDE_HOME", str(old))
    assert resolve_paths().home == old
    with pytest.raises(ValueError, match="overrides"):
        configure_local_storage(str(target))


def test_storage_inside_git_rejected_before_preference_is_written(monkeypatch, tmp_path):
    monkeypatch.delenv("BENCHSIDE_HOME", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    with pytest.raises(BenchsideError, match="outside Git"):
        configure_local_storage(str(repo / "journal"))
    assert not (tmp_path / "config/benchside/storage.json").exists()


@pytest.mark.parametrize("agent", ["codex", "generic", "claude"])
def test_source_install_provides_shared_skill_and_json_bridge(agent, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("BENCHSIDE_HOME", str(tmp_path / "records"))
    target = tmp_path / "agent-skills"
    assert main(["setup", "--agent", agent, "--skills-dir", str(target)]) == 0
    capsys.readouterr()
    assert (target / "benchside/references/onboarding.md").is_file()
    assert len(list((target / "benchside/references/roles").glob("*.md"))) == 7
    assert not (target / "settings.json").exists()
    monkeypatch.setattr(
        sys, "stdin", io.StringIO(json.dumps({"action": "setup", "project_key": "synthetic"}))
    )
    assert main(["app"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] and result["result"]["project_id"].startswith("p-")
    monkeypatch.setattr(sys, "stdin", io.StringIO('{"action":"native.create"}'))
    assert main(["app"]) == 0
    assert json.loads(capsys.readouterr().out)["result"]["snapshot"]["revision"] == 0
    monkeypatch.setattr(sys, "stdin", io.StringIO("invalid json"))
    assert main(["app"]) == 1
    assert not json.loads(capsys.readouterr().out)["ok"]


@pytest.mark.parametrize("agent", ["codex", "generic"])
def test_project_install_for_other_agents_does_not_register_claude_hooks(
    agent, tmp_path, monkeypatch
):
    project = tmp_path / "research-project"
    project.mkdir()
    monkeypatch.chdir(project)
    monkeypatch.setenv("BENCHSIDE_HOME", str(tmp_path / "private-records"))
    assert main(["init", "--yes", "--agent", agent]) == 0
    assert (project / ".bench/config.yaml").is_file()
    assert (project / ".agents/skills/benchside/SKILL.md").is_file()
    assert not (project / ".claude").exists()
