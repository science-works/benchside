"""Crashed or cross-project conversations must not poison later CLI recording."""

import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from benchside.cli import runtime
from benchside.cli.main import main
from benchside.config import Paths
from benchside.domain.shared.error import InvalidStateError
from benchside.domain.shared.model.ids import ProjectId
from benchside.infrastructure.files import file_lock
from benchside.infrastructure.session_context import current_session, register_session


@pytest.fixture
def session_project(tmp_path, monkeypatch):
    project = tmp_path / "research"
    (project / ".bench").mkdir(parents=True)
    (project / ".bench/config.yaml").write_text("project: research\n")
    paths = Paths(home=tmp_path / "records", repo_root=Path(__file__).resolve().parents[3])
    monkeypatch.chdir(project)
    monkeypatch.setenv("BENCHSIDE_HOME", str(paths.home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    for name in (
        "CLAUDE_SESSION_ID",
        "BENCHSIDE_SESSION_ID",
        "CLAUDE_ENV_FILE",
        "BENCH_SITTING",
        "BENCHSIDE_REPO",
    ):
        monkeypatch.delenv(name, raising=False)
    return paths, ProjectId("research"), project


def _hook(monkeypatch, event, project, **payload):
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"cwd": str(project), **payload})))
    return main(["hook", event])


def test_expired_registration_is_not_adopted_but_explicit_pointer_survives(
    session_project, monkeypatch
):
    paths, project_id, _ = session_project
    now = time.time()
    register_session(paths, project_id, "crashed")
    runtime.write_pointer(paths, sitting_id="unfinished", project_id=project_id, persona_id="pi")
    journal = paths.journal_file(project_id.root)
    journal.write_text("private scientific records remain here\n")
    monkeypatch.setattr(time, "time", lambda: now + 48 * 3600)

    assert runtime.read_pointer(paths, project_id) is None
    assert current_session(paths, project_id) is None
    assert not (paths.home / "projects/research/current-session").exists()
    assert (paths.home / "sessions/crashed.json").is_file()
    assert journal.read_text() == "private scientific records remain here\n"


def test_new_registration_prunes_expired_peer(session_project, monkeypatch):
    paths, project_id, _ = session_project
    now = time.time()
    register_session(paths, project_id, "crashed")
    monkeypatch.setattr(time, "time", lambda: now + 48 * 3600)

    register_session(paths, project_id, "current")

    assert current_session(paths, project_id) == "current"
    assert json.loads((paths.home / "projects/research/current-session").read_text())[
        "sessions"
    ] == ["current"]


def test_new_cli_record_after_expiry_does_not_use_the_crashed_conversation(
    session_project, monkeypatch
):
    paths, project_id, _ = session_project
    now = time.time()
    register_session(paths, project_id, "crashed")
    assert main(["sitting", "open", "--persona", "methods-clinic"]) == 0
    original = json.loads((paths.home / "sessions/crashed.json").read_text())
    monkeypatch.setattr(time, "time", lambda: now + 48 * 3600)

    assert main(["sitting", "open", "--persona", "methods-clinic"]) == 0

    events = [
        json.loads(line) for line in paths.journal_file(project_id.root).read_text().splitlines()
    ]
    assert len(events) == 2
    assert events[0]["session"] == "crashed"
    assert events[1]["session"] is None
    assert all(event["type"] == "ConsultationOpened" for event in events)
    assert json.loads((paths.home / "sessions/crashed.json").read_text()) == original
    assert (
        json.loads((paths.home / "sessions/local.json").read_text())["sitting_id"]
        != original["sitting_id"]
    )


@pytest.mark.parametrize("legacy", [{"session_id": "old"}, {"sessions": ["old"]}])
def test_untimestamped_registration_uses_original_file_age(session_project, legacy):
    paths, project_id, _ = session_project
    path = paths.home / "projects/research/current-session"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(legacy))
    old = time.time() - 48 * 3600
    os.utime(path, (old, old))

    assert current_session(paths, project_id) is None
    assert not path.exists()


def test_explicit_session_identity_remains_authoritative_after_expiry(session_project, monkeypatch):
    paths, project_id, _ = session_project
    now = time.time()
    register_session(paths, project_id, "long-conversation")
    runtime.write_pointer(paths, sitting_id="unfinished", project_id=project_id, persona_id="pi")
    monkeypatch.setattr(time, "time", lambda: now + 48 * 3600)
    monkeypatch.setenv("CLAUDE_SESSION_ID", "long-conversation")

    assert current_session(paths, project_id) == "long-conversation"
    assert runtime.read_pointer(paths, project_id)["sitting_id"] == "unfinished"


@pytest.mark.parametrize(
    "registry",
    [
        None,
        [],
        {"sessions": "active"},
        {"sessions": [False]},
        {"session_id": 7},
        {"sessions": ["active"], "registered_at": []},
        {"sessions": ["active"], "registered_at": {"active": True}},
        {"sessions": ["active"], "registered_at": {"active": "yesterday"}},
        {"sessions": ["active"], "registered_at": {"active": float("nan")}},
        {"sessions": ["active"], "registered_at": {"active": time.time() + 86400}},
        {"sessions": ["active"], "registered_at": {}},
        {"sessions": ["active"], "registered_at": {"different": 1}},
    ],
)
def test_invalid_registry_fails_with_repair_path_without_rewriting_state(session_project, registry):
    paths, project_id, _ = session_project
    path = paths.home / "projects/research/current-session"
    path.parent.mkdir(parents=True)
    original = json.dumps(registry)
    path.write_text(original)

    with pytest.raises(InvalidStateError) as captured:
        current_session(paths, project_id)

    assert str(path) in captured.value.hint
    assert "repair" in captured.value.hint.lower()
    assert path.read_text() == original


def test_ambiguity_names_targeted_recovery_that_preserves_other_sessions(
    session_project, monkeypatch
):
    paths, project_id, _ = session_project
    register_session(paths, project_id, "crashed")
    runtime.write_pointer(paths, sitting_id="unfinished", project_id=project_id, persona_id="pi")
    register_session(paths, project_id, "current")
    with pytest.raises(InvalidStateError) as captured:
        current_session(paths, project_id)
    assert "bench session clear" in captured.value.hint
    assert "--session" in captured.value.hint

    assert main(["session", "clear", "--project", "research", "--session", "crashed"]) == 0

    assert current_session(paths, project_id) == "current"
    assert (paths.home / "sessions/crashed.ended").is_file()
    assert not (paths.home / "sessions/crashed.json").exists()


def test_session_end_clears_cwd_and_pointer_projects(session_project, monkeypatch):
    paths, project_id, project = session_project
    other = ProjectId("another-project")
    register_session(paths, project_id, "cross-project")
    register_session(paths, other, "cross-project")
    monkeypatch.setenv("CLAUDE_SESSION_ID", "cross-project")
    runtime.write_pointer(paths, sitting_id="unfinished", project_id=other, persona_id="pi")
    monkeypatch.delenv("CLAUDE_SESSION_ID")

    assert _hook(monkeypatch, "session-end", project, session_id="cross-project") == 0

    assert current_session(paths, project_id) is None
    assert current_session(paths, other) is None
    assert (paths.home / "sessions/cross-project.ended").is_file()


def test_targeted_recovery_does_not_retire_another_project_pointer(session_project, monkeypatch):
    paths, project_id, _ = session_project
    other = ProjectId("another-project")
    register_session(paths, project_id, "cross-project")
    register_session(paths, other, "cross-project")
    monkeypatch.setenv("CLAUDE_SESSION_ID", "cross-project")
    runtime.write_pointer(paths, sitting_id="keep-open", project_id=other, persona_id="pi")
    monkeypatch.delenv("CLAUDE_SESSION_ID")

    assert main(["session", "clear", "--project", "research", "--session", "cross-project"]) == 0

    assert current_session(paths, project_id) is None
    assert current_session(paths, other) == "cross-project"
    assert runtime.read_pointer(paths, other)["sitting_id"] == "keep-open"


def test_shared_setup_clears_registrations_only_for_its_project(session_project):
    paths, project_id, _ = session_project
    assert main(["init", "--yes", "--legacy-cli"]) == 0
    register_session(paths, project_id, "abandoned-hook-session")
    runtime.write_pointer(paths, sitting_id="unfinished", project_id=project_id, persona_id="pi")
    other = ProjectId("other")
    register_session(paths, other, "keep-other")
    journal = paths.journal_file(project_id.root)
    journal.write_text("private scientific records remain here\n")

    assert main(["init", "--yes"]) == 0

    assert current_session(paths, project_id) is None
    assert current_session(paths, other) == "keep-other"
    assert (paths.home / "sessions/abandoned-hook-session.json").is_file()
    assert journal.read_text() == "private scientific records remain here\n"


@pytest.mark.parametrize("event", ["session-start", "session-end"])
def test_hooks_do_not_wait_for_global_transaction_lock(session_project, event):
    paths, _, project = session_project
    code = "from benchside.cli.main import main; raise SystemExit(main())"
    environment = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[3])}
    with file_lock(paths.home / ".transaction.lock"):
        try:
            result = subprocess.run(
                [sys.executable, "-c", code, "hook", event],
                input=json.dumps({"cwd": str(project), "session_id": "unblocked"}),
                text=True,
                capture_output=True,
                env=environment,
                timeout=2,
                check=False,
            )
        except subprocess.TimeoutExpired:
            pytest.fail("Lifecycle hook blocked behind the global transaction lock")
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("event", ["session-start", "session-end"])
def test_hook_invalid_storage_preference_still_returns_zero(
    session_project, monkeypatch, event, tmp_path
):
    _, _, project = session_project
    monkeypatch.delenv("BENCHSIDE_HOME")
    preference = tmp_path / "config/benchside/storage.json"
    preference.parent.mkdir(parents=True)
    preference.write_text('{"local_directory":"relative/path"}')

    assert _hook(monkeypatch, event, project, session_id="invalid-storage") == 0
