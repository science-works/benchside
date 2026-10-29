"""Synthetic regressions for review findings 13 and 14; no external services."""

import io
import json
import sys
import time
from pathlib import Path

import pytest

from benchside.cli import runtime
from benchside.cli.main import main
from benchside.config import Paths
from benchside.domain.shared.model.ids import ProjectId
from benchside.infrastructure.session_context import clear_project_sessions, register_session


@pytest.fixture
def project(tmp_path, monkeypatch):
    root = tmp_path / "project"
    (root / ".bench").mkdir(parents=True)
    (root / ".bench/config.yaml").write_text("project: synthetic\n")
    paths = Paths(home=tmp_path / "records", repo_root=Path(__file__).resolve().parents[3])
    monkeypatch.chdir(root)
    monkeypatch.setenv("BENCHSIDE_HOME", str(paths.home))
    for name in ("CLAUDE_SESSION_ID", "BENCHSIDE_SESSION_ID", "BENCH_SITTING", "CLAUDE_ENV_FILE"):
        monkeypatch.delenv(name, raising=False)
    return paths, ProjectId("synthetic"), root


@pytest.mark.parametrize("clear", [False, True])
def test_expiring_fallback_never_retires_explicit_open_conversation(project, monkeypatch, clear):
    paths, pid, _ = project
    now = time.time()
    register_session(paths, pid, "still-open")
    monkeypatch.setenv("CLAUDE_SESSION_ID", "still-open")
    runtime.write_pointer(paths, sitting_id="keep-sitting", project_id=pid, persona_id="pi")
    monkeypatch.setattr(time, "time", lambda: now + 25 * 3600)
    if clear:
        clear_project_sessions(paths, pid)
    register_session(paths, pid, "another-chat")
    assert runtime.read_pointer(paths, pid)["sitting_id"] == "keep-sitting"
    assert not (paths.home / "sessions/still-open.ended").exists()
    monkeypatch.setenv("CLAUDE_SESSION_ID", "another-chat")
    assert runtime.read_pointer(paths, pid) is None


@pytest.mark.parametrize("damage", ["malformed", "clock-skew"])
def test_registry_problem_does_not_block_new_identity_or_recall(
    project, monkeypatch, capsys, tmp_path, damage
):
    paths, _pid, root = project
    registry = paths.home / "projects/synthetic/current-session"
    registry.parent.mkdir(parents=True)
    original = (
        "not JSON"
        if damage == "malformed"
        else json.dumps({"sessions": ["old"], "registered_at": {"old": time.time() + 3}})
    )
    registry.write_text(original)
    env_file = tmp_path / "new-chat.env"
    monkeypatch.setenv("CLAUDE_ENV_FILE", str(env_file))
    monkeypatch.setattr(
        sys, "stdin", io.StringIO(json.dumps({"cwd": str(root), "session_id": "new-chat"}))
    )
    assert main(["hook", "session-start"]) == 0
    assert "export CLAUDE_SESSION_ID=new-chat" in env_file.read_text()
    assert "No recorded history yet" in capsys.readouterr().out
    monkeypatch.setenv("CLAUDE_SESSION_ID", "new-chat")
    assert main(["sitting", "open", "--persona", "pi"]) == 0
    assert main(["hypothesis", "Synthetic state continues safely"]) == 0
    if damage == "malformed":
        assert registry.read_text() == original
