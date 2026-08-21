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

from benchside.config import Paths, resolve_paths
from benchside.domain.shared.error import DomainError
from benchside.domain.shared.model.ids import ProjectId, user_project_id

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
            f"'{cwd}' is not part of a benchside project. Run `bench init` here "
            "first (it sets up the project id, session hooks, and the /pi skill)."
        )
    return config.parent.parent


def slugify(raw: str) -> str:
    slug = _NON_SLUG.sub("-", raw.strip().lower()).strip("-")
    return slug or "unnamed"


def short_id(prefix: str) -> str:
    """Human-quotable unique id, generated CLI-side (never by the model)."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


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


def session_name() -> str:
    return os.environ.get("CLAUDE_SESSION_ID") or "local"


def pointer_dir(paths: Paths) -> Path:
    return paths.home / "sessions"


def write_pointer(paths: Paths, *, sitting_id: str, project_id: ProjectId, persona_id: str) -> None:
    directory = pointer_dir(paths)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{session_name()}.json").write_text(
        json.dumps(
            {
                "sitting_id": sitting_id,
                "project_id": project_id.root,
                "persona_id": persona_id,
                "session": session_name(),
                "opened_at": datetime.now(UTC).isoformat(),
            }
        ),
        encoding="utf-8",
    )


def clear_pointer(paths: Paths, sitting_id: str) -> None:
    """Remove whichever live pointer references the sitting — not blindly this
    session's, so cross-project cleanup via BENCH_SITTING clears the right one."""
    directory = pointer_dir(paths)
    for path in sorted(directory.glob("*.json")) if directory.is_dir() else []:
        try:
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
    session's pointer, then a single unambiguous live pointer — the latter two
    only when they match the current project.
    """
    override = os.environ.get("BENCH_SITTING")
    records = live_pointers(paths)
    if override:
        for record in records:
            if record.get("sitting_id") == override:
                return record
        return {"sitting_id": override, "project_id": None}
    if project_id is not None:
        records = [r for r in records if r.get("project_id") == project_id.root]
    for record in records:
        if record.get("session") == session_name():
            return record
    if len(records) == 1:
        return records[0]
    return None


def require_pointer(paths: Paths, project_id: ProjectId | None = None) -> dict:
    record = read_pointer(paths, project_id)
    if record is None:
        where = f" for project '{project_id.root}'" if project_id is not None else ""
        raise NoOpenSittingError(
            f"No open sitting{where}. Start one with `bench sitting open --persona <id>` "
            "(or set BENCH_SITTING to an existing sitting id)."
        )
    return record


def current_paths() -> Paths:
    return resolve_paths()
