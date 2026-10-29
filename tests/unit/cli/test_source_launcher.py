"""Source-installed skills keep working after leaving the checkout and its shell."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from benchside.cli.main import main


@pytest.fixture
def source_skill(tmp_path, monkeypatch):
    monkeypatch.setenv("BENCHSIDE_HOME", str(tmp_path / "private-records"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.delenv("BENCHSIDE_REPO", raising=False)
    target = tmp_path / "agent's skills with spaces"
    assert main(["setup", "--agent", "generic", "--skills-dir", str(target)]) == 0
    skill = target / "benchside"
    unrelated = tmp_path / "next-project"
    unrelated.mkdir()
    environment = {**os.environ, "PATH": "/usr/bin:/bin"}
    environment.pop("PYTHONPATH", None)

    def launch(request, *options):
        response = subprocess.run(
            [sys.executable, str(skill / "scripts/benchside_app.py"), *options],
            cwd=unrelated,
            env=environment,
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        result = json.loads(response.stdout)
        assert response.returncode == (0 if result["ok"] else 1), response.stderr
        return result

    return skill, launch


def test_source_version_check_needs_no_research_store(source_skill, tmp_path):
    from benchside import __version__

    _, launch = source_skill
    assert launch({"action": "version"})["result"] == {"version": __version__}
    assert not (tmp_path / "private-records").exists()


@pytest.mark.parametrize("populated", [False, True])
def test_response_file_keeps_exact_native_candidate_without_printing_payload(
    source_skill, tmp_path, populated
):
    from benchside.application.native import reference, run_native

    _, launch = source_skill
    destination = tmp_path / "candidate ' with spaces.json"
    request = {"action": "native.create"}
    if populated:
        empty = run_native(request)
        context = {
            "project_id": {"$ref": "setup.project_id"},
            "session_id": {"$ref": "setup.session_id"},
        }
        steps = [
            {
                "id": "setup",
                "project_document": {"document_id": "synthetic", "title": "Synthetic"},
                "request": {"action": "setup", "host": "claude", "project_key": "synthetic"},
            },
            {"id": "start", "request": {"action": "start", "role": "methods-clinic", **context}},
        ]
        for i in range(12):
            steps.append(
                {
                    "id": f"decision{i}",
                    "request": {
                        "action": "decide",
                        **context,
                        "sitting_id": {"$ref": "start.sitting.id"},
                        "decision": f"Synthetic Δ decision {i}: compare paired controls",
                        "rationale": "Separate extraction and detection; retain the donor pairing.",
                    },
                }
            )
        request = {
            "action": "native.batch",
            "document": empty["markdown"],
            "workspace_id": empty["snapshot"]["workspace_id"],
            "steps": steps,
        }
    summary = launch(request, "--response-file", str(destination))
    full = json.loads(destination.read_text())
    assert full["ok"] and not full["result"]["saved"]
    assert summary["result"]["candidate"] == reference(full["result"]["snapshot"])
    assert summary["response_file"] == str(destination)
    assert "payload" not in json.dumps(summary)
    assert destination.stat().st_mode & 0o077 == 0
    confirmed = run_native(
        {
            "action": "native.confirm",
            "workspace_id": full["result"]["snapshot"]["workspace_id"],
            "document": full["result"]["markdown"],
            "expected": summary["result"]["candidate"],
        }
    )
    assert confirmed["saved"]
    if populated:
        assert full["result"]["changed"]
        restored = run_native(
            {
                "action": "native.run",
                "workspace_id": confirmed["workspace_id"],
                "document": full["result"]["markdown"],
                "request": {
                    "action": "recall",
                    "project_id": full["result"]["result"]["project_id"],
                    "history": "all",
                },
            }
        )
        assert len(restored["result"]["recent_decisions"]) == 12
        assert restored["result"]["recent_decisions"][0]["decision"].startswith(
            "Synthetic Δ decision 0"
        )
    original = destination.read_bytes()
    refused = launch(
        {"action": "setup", "project_key": "must-not-run"}, "--response-file", str(destination)
    )
    assert not refused["ok"]
    assert destination.read_bytes() == original
    assert not (tmp_path / "private-records").exists()


def test_source_launcher_restores_records_from_fresh_processes(source_skill, tmp_path):
    skill, launch = source_skill
    metadata = skill / "runtime/source.json"
    settings = json.loads(metadata.read_text())
    # Neither path interpolation nor changing into the source directory is needed.
    source_alias = tmp_path / "source ' $(not-a-command)"
    source_alias.symlink_to(settings["package_root"], target_is_directory=True)
    settings["package_root"] = str(source_alias)
    metadata.write_text(json.dumps(settings))
    assert settings["python"] == str(Path(sys.executable).absolute())
    assert not (skill / "runtime/manifest.json").exists()
    assert len(launch({"action": "roles"})["result"]) == 7
    setup = launch({"action": "setup", "project_key": "synthetic-source-check"})["result"]
    context = {key: setup[key] for key in ("project_id", "session_id")}
    started = launch({"action": "start", "role": "methods-clinic", **context})["result"]
    saved = launch(
        {
            "action": "decide",
            "decision": "Run synthetic paired controls",
            "rationale": "Locate the discrepancy",
            "sitting_id": started["sitting"]["id"],
            **context,
        }
    )
    assert saved["ok"]
    recalled = launch({"action": "recall", "project_id": setup["project_id"]})
    assert recalled["result"]["recent_decisions"][0]["decision"] == "Run synthetic paired controls"


@pytest.mark.parametrize("missing", ["python", "package_root"])
def test_missing_source_runtime_returns_repair_guidance(source_skill, tmp_path, missing):
    skill, launch = source_skill
    metadata = skill / "runtime/source.json"
    settings = json.loads(metadata.read_text())
    settings[missing] = str(tmp_path / "removed-source-environment")
    metadata.write_text(json.dumps(settings))

    response = launch({"action": "roles"})

    assert not response["ok"]
    assert response["code"] == "setup_failed"
    assert "unavailable" in response["error"]
    assert "rerun bench setup" in response["error"]
    assert not (skill / "runtime/manifest.json").exists()


@pytest.mark.parametrize("legacy", [False, True])
def test_claude_init_selects_one_default_recording_route(tmp_path, monkeypatch, legacy):
    project = tmp_path / "research"
    project.mkdir()
    monkeypatch.chdir(project)
    monkeypatch.setenv("BENCHSIDE_HOME", str(tmp_path / "records"))
    monkeypatch.delenv("BENCHSIDE_REPO", raising=False)
    args = ["init", "--yes", "--agent", "claude"]
    if legacy:
        args.append("--legacy-cli")
    assert main(args) == 0
    skills = project / ".claude/skills"
    if legacy:
        assert not (skills / "benchside/SKILL.md").exists()
        assert (project / ".claude/settings.json").is_file()
        for skill in skills.glob("*/SKILL.md"):
            assert skill.read_text().startswith("---\ndisable-model-invocation: true\n")
    else:
        assert [path.name for path in skills.iterdir()] == ["benchside"]
        assert not (project / ".claude/settings.json").exists()
        assert (skills / "benchside/runtime/source.json").is_file()


def test_switching_to_shared_entry_preserves_journals_and_custom_skills(
    tmp_path, monkeypatch, capsys
):
    project = tmp_path / "research"
    project.mkdir()
    monkeypatch.chdir(project)
    memory = tmp_path / "records"
    monkeypatch.setenv("BENCHSIDE_HOME", str(memory))
    monkeypatch.delenv("BENCHSIDE_REPO", raising=False)
    assert main(["init", "--yes", "--legacy-cli"]) == 0
    assert main(["sitting", "open", "--persona", "pi"]) == 0
    assert main(["hypothesis", "Synthetic continuity check"]) == 0
    journal = memory / "projects/research/journal.jsonl"
    original_journal = journal.read_bytes()
    skills = project / ".claude/skills"
    recognized = skills / "pi/SKILL.md"
    original_generated = recognized.read_text().replace("disable-model-invocation: true\n", "")
    recognized.write_text(original_generated)
    customized = skills / "methods-clinic/SKILL.md"
    custom_text = (
        customized.read_text().replace("disable-model-invocation: true\n", "")
        + "\nMy custom notes\n"
    )
    customized.write_text(custom_text)
    settings_path = project / ".claude/settings.json"
    settings = json.loads(settings_path.read_text())
    unrelated = {"matcher": "", "hooks": [{"type": "command", "command": "my-other-hook"}]}
    settings["hooks"]["SessionStart"].append(unrelated)
    settings_path.write_text(json.dumps(settings))
    capsys.readouterr()

    assert main(["init", "--yes"]) == 0
    output = capsys.readouterr().out
    notice = next(
        line
        for line in output.splitlines()
        if line.startswith("Updated legacy Benchside commands to explicit invocation only:")
    )
    assert "/pi" in notice
    assert "methods-clinic" not in notice
    assert f"Preserved custom skill at {customized}" in output

    assert recognized.read_text() == original_generated.replace(
        "---\n", "---\ndisable-model-invocation: true\n", 1
    )
    assert customized.read_text() == custom_text
    assert journal.read_bytes() == original_journal
    assert not (memory / "app-projects").exists()
    assert (skills / "benchside/runtime/source.json").is_file()
    remaining_hooks = json.loads(settings_path.read_text())["hooks"]
    assert remaining_hooks["SessionStart"] == [unrelated]
    assert remaining_hooks["SessionEnd"] == []
    assert main(["init", "--yes"]) == 0
    assert "Updated legacy Benchside commands" not in capsys.readouterr().out
