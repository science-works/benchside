"""Journal envelopes carry the Claude session id that produced them.

The id comes from CLAUDE_SESSION_ID when set (tests, direct use), else from
the per-project current-session file the SessionStart hook maintains —
because Claude Code does NOT export the session id to Bash subprocesses.
"""

import json
import pytest

from benchside.domain.consultation.event.opened import ConsultationOpened
from benchside.domain.shared.model.ids import PersonaId, ProjectId
from benchside.infrastructure.journal.store import JsonlJournal
from benchside.infrastructure.session_context import current_session, register_session

PID = ProjectId("stamped")


def open_event() -> ConsultationOpened:
    return ConsultationOpened(
        id="e1", consultation_id="c-1", project_id=PID, persona_id=PersonaId("pi")
    )


class TestSessionResolution:
    def test_parallel_sessions_require_their_own_identity(self, paths, monkeypatch, tmp_path):
        from benchside.domain.shared.error import InvalidStateError
        from benchside.infrastructure.session_context import clear_session

        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        first_env = tmp_path / "first.env"
        second_env = tmp_path / "second.env"
        monkeypatch.setenv("CLAUDE_ENV_FILE", str(first_env))
        register_session(paths, PID, "first")
        monkeypatch.setenv("CLAUDE_ENV_FILE", str(second_env))
        register_session(paths, PID, "second")
        assert "first" in first_env.read_text()
        assert "second" not in first_env.read_text()
        assert "second" in second_env.read_text()
        with pytest.raises(InvalidStateError, match="Several"):
            current_session(paths, PID)
        monkeypatch.setenv("CLAUDE_SESSION_ID", "first")
        assert current_session(paths, PID) == "first"
        clear_session(paths, PID, "second")
        monkeypatch.delenv("CLAUDE_SESSION_ID")
        assert current_session(paths, PID) == "first"

    def test_env_var_wins(self, paths, monkeypatch):
        monkeypatch.setenv("CLAUDE_SESSION_ID", "env-session")
        register_session(paths, PID, "file-session")
        assert current_session(paths, PID) == "env-session"

    def test_falls_back_to_registered_file(self, paths, monkeypatch):
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        register_session(paths, PID, "de21b135-19f1-494a-b72c-f6292368ed7c")
        assert current_session(paths, PID) == "de21b135-19f1-494a-b72c-f6292368ed7c"

    def test_none_when_nothing_known(self, paths, monkeypatch):
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        assert current_session(paths, PID) is None


class TestEnvelopeStamping:
    def test_appended_line_carries_session(self, paths, journal, monkeypatch):
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        register_session(paths, PID, "sess-abc")
        journal.append(PID, open_event())
        line = json.loads(paths.journal_file(PID.root).read_text().splitlines()[0])
        assert line["session"] == "sess-abc"

    def test_session_null_when_unknown(self, paths, journal, monkeypatch):
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        journal.append(PID, open_event())
        line = json.loads(paths.journal_file(PID.root).read_text().splitlines()[0])
        assert line["session"] is None

    def test_old_lines_without_session_still_parse(self, paths, journal):
        path = paths.journal_file(PID.root)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "type": "ConsultationOpened",
            "data": open_event().model_dump(mode="json"),
        }
        path.write_text(json.dumps(record) + "\n")
        events = list(journal.read(PID))
        assert len(events) == 1, "pre-stamping journals must remain readable"

    def test_read_envelopes_exposes_session(self, paths, journal, monkeypatch):
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        register_session(paths, PID, "sess-xyz")
        journal.append(PID, open_event())
        envelopes = list(journal.read_envelopes(PID))
        assert envelopes[0]["session"] == "sess-xyz"
        assert envelopes[0]["type"] == "ConsultationOpened"
