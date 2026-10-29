"""CLI runtime context: project resolution, sitting pointers, container access.

The CLI is the only writer to on-disk state and the layer where the model's
prose becomes typed records — or gets refused. Ids and timestamps are
generated here, never supplied by the model.
"""

import json
import os
import re
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path

import yaml
from pydantic import ValidationError as SchemaError

from benchside.config import Paths, resolve_paths
from benchside.domain.shared.error import DomainError
from benchside.domain.shared.model.ids import ProjectId, user_project_id
from benchside.domain.shared.model.provenance import AppProvenance

_NON_SLUG = re.compile(r"[^a-z0-9]+")


class NoOpenSittingError(DomainError):
    """Raised when a capture command runs with no resolvable open sitting."""


class NotInitializedError(DomainError):
    """Raised when a project-bound command runs outside an inited project."""


def require_initialized(cwd: Path | None = None) -> Path:
    """Project-bound commands refuse to run outside a `bench init`-ed project.

    Prevents accidental projects: /pi can load from a parent directory and
    bench runs anywhere, so without this guard a sitting could be opened in a
    directory that was never set up (and whose hooks therefore never fire).
    Explicit BENCH_SITTING cleanup paths bypass this at the call site.
    """
    cwd = cwd or Path.cwd()
    config = find_bench_config(cwd)
    if config is None:
        raise NotInitializedError(
            f"'{cwd}' is not part of a benchside project",
            hint="Run `bench init` here first — it sets up the project id, "
            "session hooks, and the /pi skill.",
        )
    return config.parent.parent


def slugify(raw: str) -> str:
    slug = _NON_SLUG.sub("-", raw.strip().lower()).strip("-")
    return slug or "unnamed"


def short_id(prefix: str) -> str:
    """Human-quotable unique id, generated CLI-side (never by the model)."""
    return f"{prefix}-{uuid.uuid4().hex}"


# --- Project resolution (issue #2: config file > git remote > dirname) ---


def find_bench_config(start: Path) -> Path | None:
    for directory in (start, *start.parents):
        candidate = directory / ".bench" / "config.yaml"
        if candidate.is_file():
            return candidate
    return None


def resolve_project(explicit: str | None = None, cwd: Path | None = None) -> ProjectId:
    if explicit:
        return user_project_id(slugify(explicit))
    cwd = cwd or Path.cwd()

    config = find_bench_config(cwd)
    if config is not None:
        raw = (yaml.safe_load(config.read_text(encoding="utf-8")) or {}).get("project")
        if raw:
            return user_project_id(slugify(str(raw)))

    remote = _git_remote_slug(cwd)
    if remote is not None:
        return user_project_id(remote)

    return user_project_id(slugify(cwd.name))


def _git_remote_slug(cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,  # non-repo dirs are an expected, handled case
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    url = result.stdout.strip()
    # git@host:owner/repo.git or https://host/owner/repo(.git)
    match = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?/?$", url)
    if not match:
        return None
    return slugify(f"{match.group(1)}-{match.group(2)}")


# --- Sitting pointers (per session; parallel sessions never fight) ---


def session_name(paths: Paths | None = None, project_id: ProjectId | None = None) -> str:
    """The session this bench invocation belongs to. Env wins; else the id
    the SessionStart hook registered for this project; else 'local'."""
    if paths is not None and project_id is not None:
        from benchside.infrastructure.session_context import current_session

        registered = current_session(paths, project_id)
        return registered or "local"
    env = os.environ.get("BENCHSIDE_SESSION_ID") or os.environ.get("CLAUDE_SESSION_ID")
    if env:
        from benchside.infrastructure.session_context import validate_session_id

        return validate_session_id(env)
    return "local"


def pointer_dir(paths: Paths) -> Path:
    return paths.home / "sessions"


def write_pointer(paths: Paths, *, sitting_id: str, project_id: ProjectId, persona_id: str) -> None:
    directory = pointer_dir(paths)
    directory.mkdir(parents=True, exist_ok=True)
    session = session_name(paths, project_id)
    from benchside.infrastructure.files import atomic_json, file_lock

    with file_lock(directory / f"{session}.lock"):
        atomic_json(
            directory / f"{session}.json",
            {
                "sitting_id": sitting_id,
                "project_id": project_id.root,
                "persona_id": persona_id,
                "session": session,
                "opened_at": datetime.now(UTC).isoformat(),
            },
        )


def clear_pointer(paths: Paths, sitting_id: str) -> None:
    """Remove whichever live pointer references the sitting — not blindly this
    session's, so cross-project cleanup via BENCH_SITTING clears the right one."""
    from benchside.infrastructure.files import file_lock

    directory = pointer_dir(paths)
    for path in sorted(directory.iterdir()) if directory.is_dir() else []:
        if path.suffix not in {".json", ".ended"}:
            continue
        try:
            with file_lock(path.with_suffix(".lock")):
                if json.loads(path.read_text(encoding="utf-8")).get("sitting_id") == sitting_id:
                    path.unlink(missing_ok=True)
        except (OSError, json.JSONDecodeError):
            continue


def live_pointers(paths: Paths) -> list[dict]:
    directory = pointer_dir(paths)
    records = []
    for path in sorted(directory.glob("*.json")) if directory.is_dir() else []:
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return records


def read_pointer(paths: Paths, project_id: ProjectId | None = None) -> dict | None:
    """Resolve the active sitting FOR THIS PROJECT.

    Sittings belong to projects; a pointer left behind by another project must
    never be adopted (regression: /pi opened in the wrong directory bled into
    the next project's session). Order: BENCH_SITTING env override (explicit,
    allowed cross-project so stranded sittings can be cleaned up), then this
    session's pointer (including the local terminal pointer), only when it
    matches the current project. A missing ID never adopts another conversation.
    """
    override = os.environ.get("BENCH_SITTING")
    if override:
        for record in live_pointers(paths):
            if record.get("sitting_id") == override:
                return record
        return {"sitting_id": override, "project_id": None}
    # Expired fallback registrations do not retire explicit conversation pointers.
    # Those pointers must not be adopted merely because only one remains.
    mine = session_name(paths, project_id)
    records = live_pointers(paths)
    if project_id is not None:
        records = [r for r in records if r.get("project_id") == project_id.root]
    for record in records:
        if record.get("session") == mine:
            return record
    return None


def require_pointer(paths: Paths, project_id: ProjectId | None = None) -> dict:
    record = read_pointer(paths, project_id)
    if record is None:
        where = f" for project '{project_id.root}'" if project_id is not None else ""
        raise NoOpenSittingError(
            f"No open sitting{where}",
            hint="Start one with `bench sitting open --persona <id>` "
            "(or set BENCH_SITTING to an existing sitting id).",
        )
    return record


def current_paths() -> Paths:
    return resolve_paths()


def recording_provenance() -> AppProvenance:
    """Use only reported CLI metadata; never infer a release version."""
    values = {
        "host": os.environ.get(
            "BENCHSIDE_HOST", "claude" if os.environ.get("CLAUDE_SESSION_ID") else "unknown"
        ),
        "app_version": os.environ.get("BENCHSIDE_APP_VERSION", "unknown"),
        "surface": os.environ.get("BENCHSIDE_SURFACE", "cli"),
    }
    try:
        return AppProvenance.model_validate(values)
    except SchemaError as error:
        # Optional host metadata cannot prevent a valid scientific record.
        # Keep valid fields and replace unsupported labels with the wire sentinel.
        for field in {issue["loc"][0] for issue in error.errors()}:
            values[field] = "unknown"
        return AppProvenance.model_validate(values)
