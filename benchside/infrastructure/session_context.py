"""Which Claude session is this?

Claude Code does not export the session id to Bash subprocesses, so `bench`
cannot see it directly. The SessionStart hook — which does receive it —
registers it in a per-project file; everything bench writes is stamped from
there. CLAUDE_SESSION_ID still wins when set (tests, scripted use).

The registered id is also what links a journal entry to its conversation:
the archived transcript is `transcripts/<stamp>-<session_id>.jsonl`, and the
same id names Claude Code's own record in ~/.claude/projects/.
"""

import json
import math
import os
import re
import shlex
import time
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from benchside.config import Paths
from benchside.domain.shared.error import InvalidStateError
from benchside.domain.shared.model.ids import ProjectId
from benchside.domain.shared.model.provenance import AppProvenance
from benchside.infrastructure.files import atomic_json, file_lock

_recording_context: ContextVar[tuple[str | None, AppProvenance] | None] = ContextVar(
    "benchside_recording_context", default=None
)

# Anonymous fallback expires after 24 hours without explicit activity.
# Explicit activity refreshes only a known registration, never an ended one.
_REGISTRATION_LIFETIME_SECONDS = 24 * 60 * 60


@contextmanager
def recording_context(*, provenance: AppProvenance, session_id: str | None = None):
    """Bind one caller's context without changing another thread's environment."""
    if session_id is not None:
        validate_session_id(session_id)
    token = _recording_context.set((session_id, provenance))
    try:
        yield
    finally:
        _recording_context.reset(token)


def current_provenance() -> AppProvenance | None:
    context = _recording_context.get()
    return context[1] if context else None


def validate_session_id(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,127}", value):
        raise InvalidStateError("Invalid session identifier")
    return value


def _session_file(paths: Paths, project_id: ProjectId):
    return paths.home / "projects" / project_id.root / "current-session"


def register_session(paths: Paths, project_id: ProjectId, session_id: str) -> None:
    validate_session_id(session_id)
    # Each Claude session has its own environment file. This avoids the
    # last-started-session race of a shared per-project current-session file.
    env_file = os.environ.get("CLAUDE_ENV_FILE")
    if env_file:
        with Path(env_file).open("a", encoding="utf-8") as handle:
            handle.write(f"\nexport CLAUDE_SESSION_ID={shlex.quote(session_id)}\n")
    # The registry is only a fallback. A damaged registry must not prevent
    # Claude from giving this conversation its explicit, authoritative ID.
    path = _session_file(paths, project_id)
    with file_lock(path.with_suffix(".lock")):
        sessions = _registered(path)
        sessions[session_id] = time.time()
        _prune_expired(paths, project_id, sessions)
        _save_registered(path, sessions)


def clear_session(paths: Paths, project_id: ProjectId, session_id: str) -> None:
    """Retire only this project's named conversation; preserve its journal."""
    validate_session_id(session_id)
    path = _session_file(paths, project_id)
    with file_lock(path.with_suffix(".lock")):
        sessions = _registered(path)
        retire_session_pointer(paths, session_id, project_id=project_id)
        sessions.pop(session_id, None)
        _save_registered(path, sessions)


def clear_project_sessions(paths: Paths, project_id: ProjectId) -> None:
    """Remove fallback registrations, preserving explicitly addressed conversations."""
    path = _session_file(paths, project_id)
    with file_lock(path.with_suffix(".lock")):
        path.unlink(missing_ok=True)


def retire_session_pointer(
    paths: Paths, session_id: str, *, project_id: ProjectId | None = None
) -> dict | None:
    """Keep unfinished work available for explicit resumption, never adoption."""
    validate_session_id(session_id)
    path = paths.home / "sessions" / f"{session_id}.json"
    with file_lock(path.with_suffix(".lock")):
        if not path.is_file():
            return None
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            record = {}
        if not isinstance(record, dict):
            record = {}
        if project_id is not None and record.get("project_id") != project_id.root:
            return None
        path.replace(path.with_suffix(".ended"))
        return record


def current_session(paths: Paths, project_id: ProjectId) -> str | None:
    context = _recording_context.get()
    if context and context[0] is not None:
        _refresh_registered(paths, project_id, context[0])
        return context[0]
    env = os.environ.get("BENCHSIDE_SESSION_ID") or os.environ.get("CLAUDE_SESSION_ID")
    if env:
        session_id = validate_session_id(env)
        _refresh_registered(paths, project_id, session_id)
        return session_id
    path = _session_file(paths, project_id)
    with file_lock(path.with_suffix(".lock")):
        sessions = _registered(path)
        if _prune_expired(paths, project_id, sessions):
            _save_registered(path, sessions)
    if len(sessions) > 1:
        raise InvalidStateError(
            "Several conversations are active; a session identifier is required to record safely",
            hint=(
                "Use this conversation's CLAUDE_SESSION_ID or BENCHSIDE_SESSION_ID. "
                f"Registered IDs: {', '.join(sorted(sessions))}. If one has ended, ask your agent "
                f"to run `bench session clear --project {shlex.quote(project_id.root)} "
                "--session <ended-session-id>`. This preserves its research records."
            ),
        )
    return next(iter(sessions), None)


def _refresh_registered(paths: Paths, project_id: ProjectId, session_id: str) -> None:
    """Keep explicit activity alive without enrolling another project/session."""
    path = _session_file(paths, project_id)
    if not path.is_file():
        return
    with file_lock(path.with_suffix(".lock")):
        try:
            sessions = _registered(path)
        except InvalidStateError:
            # Explicit identity still works while a damaged registry awaits
            # repair. Never overwrite it or infer missing registrations.
            return
        if session_id in sessions:
            sessions[session_id] = time.time()
            _save_registered(path, sessions)


def _registered(path: Path) -> dict[str, float]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise TypeError("expected a registration object")
        names_raw = data.get("sessions", [])
        if not isinstance(names_raw, list):
            raise TypeError("sessions must be a list of conversation IDs")
        # Older registrations had no timestamps. Their last file write is a
        # bounded migration fallback, never renewed merely by reading them.
        legacy_timestamp = path.stat().st_mtime
        names = {validate_session_id(s) for s in names_raw} | (
            {validate_session_id(data["session_id"])} if "session_id" in data else set()
        )
        timestamps = data.get("registered_at", {name: legacy_timestamp for name in names})
        if not isinstance(timestamps, dict) or set(timestamps) != names:
            raise ValueError("timestamps must match the registered conversation IDs")
        result = {}
        now = time.time()
        for name in names:
            timestamp = timestamps[name]
            if (
                isinstance(timestamp, bool)
                or not isinstance(timestamp, (int, float))
                or timestamp < 0
                or timestamp > now + 300
                or not math.isfinite(timestamp)
            ):
                raise ValueError("timestamps must be finite Unix times with at most 5 minutes skew")
            result[name] = min(float(timestamp), now)
        return result
    except FileNotFoundError:
        return {}
    except (TypeError, ValueError, InvalidStateError) as error:
        raise InvalidStateError(
            "Invalid Benchside conversation registrations; recording is paused",
            hint=(
                f"Ask your agent to inspect and repair {path}, preserving active conversation "
                "IDs and their original timestamps. Do not delete scientific journals. "
                "An explicit conversation ID can still identify the current conversation."
            ),
        ) from error


def _save_registered(path: Path, sessions: dict[str, float]) -> None:
    if sessions:
        atomic_json(path, {"sessions": sorted(sessions), "registered_at": sessions})
    else:
        path.unlink(missing_ok=True)


def _prune_expired(paths: Paths, project_id: ProjectId, sessions: dict[str, float]) -> bool:
    cutoff = time.time() - _REGISTRATION_LIFETIME_SECONDS
    expired = [name for name, timestamp in sessions.items() if timestamp <= cutoff]
    for name in expired:
        # Expiry makes anonymous fallback unsafe; it does not mean the actual
        # conversation ended. Its pointer remains accessible only by its ID.
        del sessions[name]
    return bool(expired)
