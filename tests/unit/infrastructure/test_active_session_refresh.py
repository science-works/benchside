"""Explicit activity keeps only its own existing conversation registration live."""

import json
import time

import pytest

from benchside.cli import runtime
from benchside.domain.shared.model.ids import ProjectId
from benchside.infrastructure.session_context import (
    clear_session,
    current_session,
    register_session,
)

PID = ProjectId("synthetic-active")


@pytest.fixture(autouse=True)
def clean_identity(monkeypatch):
    for name in ("CLAUDE_SESSION_ID", "BENCHSIDE_SESSION_ID", "CLAUDE_ENV_FILE", "BENCH_SITTING"):
        monkeypatch.delenv(name, raising=False)


@pytest.mark.parametrize("variable", ["CLAUDE_SESSION_ID", "BENCHSIDE_SESSION_ID"])
@pytest.mark.parametrize("resolve", [current_session, runtime.session_name])
def test_explicit_activity_survives_another_sessions_later_start(
    paths, monkeypatch, variable, resolve
):
    now = time.time()
    monkeypatch.setattr(time, "time", lambda: now)
    register_session(paths, PID, "active-a")
    monkeypatch.setenv(variable, "active-a")
    runtime.write_pointer(paths, sitting_id="unfinished-a", project_id=PID, persona_id="pi")

    monkeypatch.setattr(time, "time", lambda: now + 23 * 3600)
    assert resolve(paths, PID) == "active-a"
    monkeypatch.setattr(time, "time", lambda: now + 25 * 3600)
    register_session(paths, PID, "new-b")

    assert runtime.read_pointer(paths, PID)["sitting_id"] == "unfinished-a"
    assert not (paths.home / "sessions/active-a.ended").exists()
    assert set(
        json.loads((paths.home / "projects/synthetic-active/current-session").read_text())[
            "sessions"
        ]
    ) == {"active-a", "new-b"}


def test_refresh_changes_only_known_matching_project_registration(paths, monkeypatch):
    now = time.time()
    monkeypatch.setattr(time, "time", lambda: now)
    other = ProjectId("synthetic-other")
    register_session(paths, PID, "active-a")
    register_session(paths, PID, "peer-b")
    register_session(paths, other, "other-c")
    path = paths.home / "projects/synthetic-active/current-session"
    other_path = paths.home / "projects/synthetic-other/current-session"
    original = path.read_text()
    original_other = other_path.read_text()
    monkeypatch.setattr(time, "time", lambda: now + 3600)

    monkeypatch.setenv("CLAUDE_SESSION_ID", "unknown")
    assert runtime.session_name(paths, PID) == "unknown"
    assert path.read_text() == original
    monkeypatch.setenv("CLAUDE_SESSION_ID", "active-a")
    assert current_session(paths, other) == "active-a"
    assert other_path.read_text() == original_other
    assert current_session(paths, PID) == "active-a"
    assert json.loads(path.read_text())["registered_at"] == {"active-a": now + 3600, "peer-b": now}


def test_explicit_identity_does_not_recreate_ended_registration(paths, monkeypatch):
    register_session(paths, PID, "ended-a")
    monkeypatch.setenv("CLAUDE_SESSION_ID", "ended-a")
    runtime.write_pointer(paths, sitting_id="unfinished-a", project_id=PID, persona_id="pi")
    clear_session(paths, PID, "ended-a")

    assert runtime.session_name(paths, PID) == "ended-a"
    assert not (paths.home / "projects/synthetic-active/current-session").exists()
    monkeypatch.delenv("CLAUDE_SESSION_ID")
    assert current_session(paths, PID) is None
    assert runtime.read_pointer(paths, PID) is None
    assert (paths.home / "sessions/ended-a.ended").is_file()


def test_expired_idle_pointer_remains_available_only_to_its_explicit_conversation(
    paths, monkeypatch
):
    now = time.time()
    monkeypatch.setattr(time, "time", lambda: now)
    register_session(paths, PID, "idle-a")
    monkeypatch.setenv("CLAUDE_SESSION_ID", "idle-a")
    runtime.write_pointer(paths, sitting_id="unfinished-a", project_id=PID, persona_id="pi")
    journal = paths.journal_file(PID.root)
    journal.write_text("Synthetic scientific history is preserved.\n")
    monkeypatch.setattr(time, "time", lambda: now + 25 * 3600)
    monkeypatch.setenv("CLAUDE_SESSION_ID", "new-b")
    register_session(paths, PID, "new-b")
    runtime.write_pointer(paths, sitting_id="unfinished-b", project_id=PID, persona_id="pi")
    monkeypatch.setenv("CLAUDE_SESSION_ID", "idle-a")

    assert current_session(paths, PID) == "idle-a"
    assert runtime.read_pointer(paths, PID)["sitting_id"] == "unfinished-a"
    assert json.loads((paths.home / "projects/synthetic-active/current-session").read_text())[
        "sessions"
    ] == ["new-b"]
    assert (paths.home / "sessions/idle-a.json").is_file()
    assert journal.read_text() == "Synthetic scientific history is preserved.\n"


def test_explicit_identity_preserves_malformed_registration_for_repair(paths, monkeypatch):
    path = paths.home / "projects/synthetic-active/current-session"
    path.parent.mkdir(parents=True)
    path.write_text("not valid JSON")
    monkeypatch.setenv("CLAUDE_SESSION_ID", "known-explicit")

    assert current_session(paths, PID) == "known-explicit"
    assert path.read_text() == "not valid JSON"
