"""Claude Code hook handlers.

Contract (gstack lessons, kept verbatim): always exit 0 — a failing hook must
never damage the user's session; errors go to ~/.local/share/benchside/hook-errors.log;
bail out fast outside benchside projects. Hooks are plumbing, never meaning —
all semantic capture stays in the explicit bench commands.
"""

import json
import shutil
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path

from benchside.cli import runtime


def cmd_hook(args) -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        payload = {}
    try:
        if args.event == "session-start":
            _session_start(payload)
        elif args.event == "session-end":
            _session_end(payload)
    except Exception:  # noqa: BLE001 — hooks must never fail the session
        _log_error(traceback.format_exc())
    return 0


def _bench_project_dir(payload: dict) -> Path | None:
    cwd = Path(payload.get("cwd") or Path.cwd())
    config = runtime.find_bench_config(cwd)
    return config.parent.parent if config else None


def _session_start(payload: dict) -> None:
    """Inject recall into the session's context (stdout lands in context)."""
    project_dir = _bench_project_dir(payload)
    if project_dir is None:
        return  # not a benchside project; <10ms bail
    paths = runtime.current_paths()
    project_id = runtime.resolve_project(cwd=project_dir)

    lines = [f"benchside: project '{project_id.root}'."]
    recall = _recall_lines(project_id)
    lines += recall if recall else ["No recorded history yet."]

    for record in _retired_pointers(paths):
        if record.get("project_id") != project_id.root:
            continue  # another project's business; never surface it here
        lines.append(
            f"A sitting from an earlier session is still open: {record['sitting_id']} "
            f"(persona {record.get('persona_id', '?')}). Resume it by exporting "
            f"BENCH_SITTING={record['sitting_id']}, or close it with bench sitting close."
        )
    print("\n".join(lines))


def _recall_lines(project_id) -> list[str]:
    from benchside.application.di import create_container
    from benchside.domain.consultation.query.recall_project import (
        RecallProject,
        RecallProjectHandler,
    )
    from benchside.util.di import Scope

    container = create_container()
    with container, container(scope=Scope.UOW) as uow:
        recall = uow.get(RecallProjectHandler).run(RecallProject(project_id=project_id))
    lines = []
    if recall.current_hypothesis:
        lines.append(f"Current hypothesis: {recall.current_hypothesis}")
    lines += [f"Open question: {q}" for q in recall.open_questions]
    lines += [f"Decided: {d.decision} — {d.rationale}" for d in recall.recent_decisions]
    if recall.last_sitting_state:
        lines.append(f"Last sitting ended: {recall.last_sitting_state}.")
    return lines


def _session_end(payload: dict) -> None:
    """Archive the transcript; retire (never auto-close) this session's pointer."""
    project_dir = _bench_project_dir(payload)
    if project_dir is None:
        return
    paths = runtime.current_paths()
    session_id = payload.get("session_id") or "local"

    pointer_path = runtime.pointer_dir(paths) / f"{session_id}.json"
    project_root = None
    if pointer_path.is_file():
        try:
            project_root = json.loads(pointer_path.read_text(encoding="utf-8")).get("project_id")
        except (OSError, json.JSONDecodeError):
            pass
        # Retire: rename off the *.json namespace so it can never hijack
        # sitting resolution, but keep it for the next session's recall.
        pointer_path.rename(pointer_path.with_suffix(".ended"))

    if project_root is None:
        project_root = runtime.resolve_project(cwd=project_dir).root

    transcript = payload.get("transcript_path") or ""
    if transcript and Path(transcript).is_file():
        target = paths.home / "projects" / project_root / "transcripts"
        target.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        shutil.copyfile(transcript, target / f"{stamp}-{session_id}.jsonl")


def _retired_pointers(paths) -> list[dict]:
    directory = runtime.pointer_dir(paths)
    if not directory.is_dir():
        return []
    records = []
    for path in sorted(directory.glob("*.ended")):
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return records


def _log_error(text: str) -> None:
    try:
        log = runtime.current_paths().home / "hook-errors.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as handle:
            handle.write(f"--- {datetime.now(UTC).isoformat()} ---\n{text}\n")
    except OSError:
        pass  # last resort: a broken log must not break the hook
