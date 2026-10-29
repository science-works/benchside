"""The `bench` entry point.

Two faces, one binary: runtime commands called from skill bash blocks
(open/hypothesis/critique/.../close, recall, consent, export) and dev commands
(compile, init, hook). Each subcommand parses argv into a typed DTO, resolves
the matching handler inside a UOW scope, and prints the result — one
human-readable line by default, JSON with --json.

Invariants live here and below, never in the model: ids, timestamps, enum
validation, referential integrity, close enforcement.
"""

import argparse
import json
import sys
from contextlib import nullcontext

from pydantic import ValidationError as PydanticValidationError

from benchside.application.di import create_container
from benchside.cli import runtime
from benchside.cli.ui import UI
from benchside.domain.consultation.model.value import MethodFlaw, Resolution
from benchside.domain.shared.error import BenchsideError
from benchside.domain.shared.model.capture import CaptureKind
from benchside.domain.shared.model.gap import GAP_KINDS
from benchside.domain.shared.model.ids import PersonaId
from benchside.util.di import Scope


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_:  # argparse prints its own message (incl. choices)
        return int(exit_.code or 0)
    if not hasattr(args, "run"):
        parser.print_help()
        return 2
    # Hooks own their short per-project/session locks and always-zero error
    # boundary. They must not wait behind sharing/network transactions or fail
    # while resolving optional storage/provenance before reaching that boundary.
    if args.command == "hook":
        return args.run(args)
    args.ui = UI.create()
    try:
        from benchside.infrastructure.files import file_lock
        from benchside.infrastructure.session_context import recording_context

        transaction = (
            nullcontext()
            if args.command in {"compile", "setup", "project", "init", "app"}
            else file_lock(runtime.current_paths().home / ".transaction.lock")
        )
        context = (
            nullcontext()
            if args.command == "app"
            else recording_context(provenance=runtime.recording_provenance())
        )
        with transaction, context:
            return args.run(args)
    except BenchsideError as err:
        _record_failure(args.command, err)
        args.ui.error(err.message, hint=err.hint)
        return 1
    except (PydanticValidationError, ValueError, OSError) as err:
        _record_failure(args.command, err)
        args.ui.error(str(err))
        return 1


def _record_failure(command, error):
    if command not in {"sitting", "hypothesis", "record", "critique", "resolve", "decide", "gap"}:
        return
    from benchside.domain.export.service.reporting import ReportingService
    from benchside.domain.shared.error import StorageUnavailableError
    from benchside.infrastructure.files import file_lock
    from benchside.infrastructure.journal.store import JsonlJournal

    code = (
        "recording_unavailable"
        if isinstance(error, (OSError, StorageUnavailableError))
        else "recording_invalid"
    )
    try:
        paths = runtime.current_paths()
        with file_lock(paths.home / ".transaction.lock"):
            ReportingService(journal=JsonlJournal(paths)).failure(code)
    except (BenchsideError, ValueError, OSError):
        pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bench",
        description="benchside: an AI workspace for doing science",
        epilog=(
            "command groups:\n"
            "  setup, init, project, compile   get set up (machine, then per project)\n"
            "  sitting open|status|close       manage the current sitting\n"
            "  hypothesis, critique, resolve,\n"
            "  decide, gap                     record what happened (used mid-sitting)\n"
            "  journal <view>                  query the project record\n"
            "  share <action>                  consent, preview, and export\n"
            "  recall                          what a persona reads on arrival"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # --- lifecycle (root) ---
    p = sub.add_parser("setup", help="one-time machine setup: install the /bench-init skill")
    p.add_argument("--agent", choices=["claude", "codex", "generic"], default="claude")
    p.add_argument("--skills-dir", type=str, help="skill discovery directory used by this agent")
    p.add_argument("--storage", type=str, help="explicit durable local directory outside Git")
    p.set_defaults(run=cmd_setup_dispatch)

    p = sub.add_parser("init", help="initialize this directory as a benchside project")
    p.add_argument("--yes", action="store_true", help="consent non-interactively")
    p.add_argument("--project", default=None)
    p.add_argument("--agent", choices=["claude", "codex", "generic"], default="claude")
    p.add_argument("--skills-dir", type=str, help="skill discovery directory used by this agent")
    p.add_argument("--storage", type=str, help="explicit durable local directory outside Git")
    p.add_argument(
        "--legacy-cli",
        action="store_true",
        help="explicit Claude Code CLI role skills and hooks instead of the shared app skill",
    )
    p.set_defaults(run=cmd_init_dispatch)

    p = sub.add_parser("app", help="agent API: one structured JSON request on stdin")
    p.set_defaults(run=cmd_app_dispatch)

    p = sub.add_parser("project", help="print the resolved project id")
    p.add_argument("--project", default=None)
    p.add_argument("--json", action="store_true")
    p.set_defaults(run=cmd_project)

    p = sub.add_parser("compile", help="compile personas into skills")
    p.add_argument("--check", action="store_true", help="dry-run freshness check")
    p.set_defaults(run=cmd_compile)

    p = sub.add_parser("recall", help="what a persona reads at the start of a sitting")
    p.add_argument("--project", default=None)
    p.add_argument("--json", action="store_true")
    p.add_argument(
        "--all", action="store_true", help="include all saved decisions and research records"
    )
    p.set_defaults(run=cmd_recall)

    p = sub.add_parser("session", help="recover a conversation that ended without cleanup")
    session = p.add_subparsers(dest="action", required=True, metavar="<action>")
    a = session.add_parser("clear", help="retire one ended conversation, keeping its research")
    a.add_argument("--project", default=None)
    a.add_argument("--session", required=True, dest="session_id")
    a.set_defaults(run=cmd_clear_session)

    # --- sitting management ---
    p = sub.add_parser("sitting", help="manage the current sitting: open, status, close")
    sitting = p.add_subparsers(dest="action", required=True, metavar="<action>")

    a = sitting.add_parser("open", help="open a sitting with a persona")
    a.add_argument("--persona", required=True)
    a.add_argument("--project", default=None)
    a.set_defaults(run=cmd_open)

    a = sitting.add_parser("resume", help="resume an open sitting in this project")
    a.add_argument("sitting_id")
    a.set_defaults(run=cmd_resume)

    a = sitting.add_parser("status", help="state, captures, and close requirements")
    a.add_argument("--json", action="store_true")
    a.set_defaults(run=cmd_status)

    a = sitting.add_parser("close", help="close the sitting")
    group = a.add_mutually_exclusive_group(required=True)
    group.add_argument("--converged", action="store_true")
    group.add_argument("--abandoned", action="store_true")
    a.add_argument("--outcome", default="", help="agreed next step (or abandonment reason)")
    a.set_defaults(run=cmd_close)

    # --- capture verbs (the mid-sitting hot path; deliberately flat) ---
    p = sub.add_parser("hypothesis", help="record a hypothesis")
    p.add_argument("statement")
    p.add_argument("--supersedes", default=None)
    p.set_defaults(run=cmd_hypothesis)

    p = sub.add_parser("critique", help="record a critique against the project")
    p.add_argument("--target", required=True, choices=["claim", "method", "interpretation"])
    p.add_argument("--claim"), p.add_argument("--ground")
    p.add_argument("--step"), p.add_argument("--flaw", choices=[f.value for f in MethodFlaw])
    p.add_argument("--result"), p.add_argument("--alternative")
    p.set_defaults(run=cmd_critique)

    p = sub.add_parser("resolve", help="settle an open critique")
    p.add_argument("critique_id")
    p.add_argument("--as", dest="resolution", required=True, choices=[r.value for r in Resolution])
    p.set_defaults(run=cmd_resolve)

    p = sub.add_parser("decide", help="record a durable decision")
    p.add_argument("decision")
    p.add_argument("--because", required=True)
    p.add_argument("--supersedes", default=None)
    p.set_defaults(run=cmd_decide)

    p = sub.add_parser("record", help="save a scientific output for the current research role")
    p.add_argument(
        "--kind",
        required=True,
        choices=[
            "study-design",
            "methods",
            "results",
            "reproducibility",
            "literature",
            "review",
        ],
    )
    p.add_argument("--summary", required=True)
    p.add_argument("--detail", action="append", required=True)
    p.add_argument("--source", action="append", default=[])
    p.set_defaults(run=cmd_record)

    p = sub.add_parser("gap", help="record a workflow breakdown (local until consented)")
    gap_sub = p.add_subparsers(dest="kind", required=True, metavar="<kind>")
    g = gap_sub.add_parser("missing_tool")
    g.add_argument("--task", required=True)
    g.add_argument("--reached-for", required=True)
    g.add_argument("--why-failed", required=True)
    g = gap_sub.add_parser("unfindable_data")
    g.add_argument("--sought", required=True)
    g.add_argument("--where-searched", required=True, help="comma-separated")
    g = gap_sub.add_parser("manual_toil")
    g.add_argument("--task", required=True)
    g.add_argument("--frequency", required=True)
    g = gap_sub.add_parser("dead_end")
    g.add_argument("--approach", required=True)
    g.add_argument("--cost", required=True)
    g = gap_sub.add_parser("missing_index")
    g.add_argument("--question", required=True)
    p.set_defaults(run=cmd_gap)

    # --- journal views ---
    p = sub.add_parser("journal", help="query the project record")
    views = p.add_subparsers(dest="view", required=True, metavar="<view>")
    v = views.add_parser("show", help="summary of the whole record")
    v.add_argument("--project", default=None)
    v = views.add_parser("sittings", help="past sittings and their end states")
    v.add_argument("--project", default=None)
    v = views.add_parser("hypotheses", help="the supersession chain")
    v.add_argument("--project", default=None)
    v = views.add_parser("records", help="research outputs with evidence and sources")
    v.add_argument("--project", default=None)
    v = views.add_parser("critiques", help="critiques and their resolutions")
    v.add_argument("--open", action="store_true", help="only open critiques")
    v.add_argument("--project", default=None)
    v = views.add_parser("decisions", help="durable decisions with rationale")
    v.add_argument("--project", default=None)
    v = views.add_parser("gaps", help="recorded workflow breakdowns")
    v.add_argument("--project", default=None)
    v = views.add_parser("events", help="the raw event stream")
    v.add_argument("--json", action="store_true")
    v.add_argument("--project", default=None)
    p.set_defaults(run=cmd_journal_dispatch)

    # --- sharing (consent + export in one place) ---
    p = sub.add_parser("share", help="review optional workflow observations, feedback and usage")
    p.set_defaults(run=cmd_share_dispatch)
    share = p.add_subparsers(dest="action", required=True, metavar="<action>")
    a = share.add_parser("status", help="grant state")
    a.add_argument("--json", action="store_true")
    a = share.add_parser("grant", help="consent to sharing listed gap kinds")
    a.add_argument("--kinds", help=f"comma-separated from: {sorted(GAP_KINDS)}")
    a.add_argument("--channel", choices=["gaps", "feedback", "usage"], default="gaps")
    a = share.add_parser("revoke", help="withdraw consent")
    a.add_argument("--channel", choices=["gaps", "feedback", "usage", "all"], default="gaps")
    a = share.add_parser("preview", help="the exact bytes an export would send; sends nothing")
    a.add_argument("--channel", choices=["gaps", "feedback", "usage"], default="gaps")
    a.add_argument("--only", action="append")
    a.add_argument(
        "--edits", help="path to a JSON file mapping observation IDs to reviewed gap objects"
    )
    a.add_argument("--feedback-id")
    a.add_argument("--comment", help="reviewed replacement feedback comment")
    a.add_argument("--week", help="Monday of the reporting week, YYYY-MM-DD")
    a = share.add_parser("send", help="export consented observations")
    a.add_argument("--draft")
    a.add_argument("--approve-sha256")
    a = share.add_parser("history", help="receipts for submitted data and removal requests")
    a = share.add_parser("feedback", help="save optional usability feedback locally")
    a.add_argument("--role", default="unknown")
    a.add_argument("--host", choices=["chatgpt", "claude", "unknown"], default="unknown")
    a.add_argument("--surface", choices=["web", "desktop", "cli", "unknown"], default="unknown")
    a.add_argument("--ease", required=True, type=int, choices=range(1, 6))
    a.add_argument("--again", required=True, choices=["yes", "no", "unsure"])
    a.add_argument("--comment", default="")

    # --- machine plumbing (no help= -> hidden from the listing) ---
    p = sub.add_parser("hook")
    p.add_argument("event", choices=["session-start", "session-end"])
    p.set_defaults(run=cmd_hook_dispatch)

    return parser


def _guard_initialized() -> None:
    """Skip the guard only for explicit BENCH_SITTING cleanup."""
    import os

    if not os.environ.get("BENCH_SITTING"):
        runtime.require_initialized()


def _uow():
    container = create_container()
    return container, container(scope=Scope.UOW)


def cmd_project(args) -> int:
    project_id = runtime.resolve_project(args.project)
    if args.json:
        print(json.dumps({"project_id": project_id.root}))
    else:
        args.ui.info(f"project: {project_id.root}")
    return 0


def cmd_clear_session(args) -> int:
    from benchside.infrastructure.session_context import clear_session

    if not args.project:
        runtime.require_initialized()
    project_id = runtime.resolve_project(args.project)
    clear_session(runtime.current_paths(), project_id, args.session_id)
    args.ui.info(
        f"Cleared conversation '{args.session_id}' for project '{project_id.root}'; "
        "research records and unfinished sittings are preserved."
    )
    return 0


def cmd_open(args) -> int:
    from benchside.domain.authoring.service.authoring import AuthoringService
    from benchside.domain.consultation.service.consultation import ConsultationService

    runtime.require_initialized()
    paths = runtime.current_paths()
    project_id = runtime.resolve_project(args.project)
    for record in runtime.live_pointers(paths):
        if (
            record.get("session") == runtime.session_name(paths, project_id)
            and record.get("project_id") == project_id.root
        ):
            raise BenchsideError(
                f"A sitting is already open for this project: {record['sitting_id']}. "
                f"Resume it (it is this session's active sitting) or close it first "
                f"with `bench sitting close`."
            )
    container, uow = _uow()
    with container, uow:
        persona = uow.get(AuthoringService).get(PersonaId(args.persona))
        sitting_id = runtime.short_id("c")
        uow.get(ConsultationService).open(
            consultation_id=sitting_id,
            project_id=project_id,
            persona_id=persona.id,
            close_requires=persona.flow.close_requires,
            critique_requires_hypothesis=persona.critique_requires_hypothesis,
            record_kind=persona.record_kind,
            persona_version=persona.version,
            **runtime.recording_provenance().model_dump(),
        )
    runtime.write_pointer(
        paths, sitting_id=sitting_id, project_id=project_id, persona_id=persona.id.root
    )
    args.ui.success(f"Sitting open with /{persona.id.root} on project '{project_id.root}'")
    print(f"<bench-sitting:{sitting_id}>")  # stdout: machine-recoverable marker
    return 0


def cmd_resume(args) -> int:
    from benchside.domain.consultation.service.consultation import ConsultationService

    runtime.require_initialized()
    paths = runtime.current_paths()
    project_id = runtime.resolve_project()
    container, uow = _uow()
    with container, uow:
        sitting = uow.get(ConsultationService).get(args.sitting_id)
        if sitting.project_id != project_id:
            raise BenchsideError("This sitting belongs to another project")
        sitting._require_live()
        own = runtime.read_pointer(paths, project_id)
        if own and own["sitting_id"] != sitting.id:
            raise BenchsideError("Finish or pause the current sitting before resuming another")
    runtime.clear_pointer(paths, sitting.id)
    runtime.write_pointer(
        paths,
        sitting_id=sitting.id,
        project_id=project_id,
        persona_id=sitting.persona_id.root,
    )
    args.ui.success(f"Resumed {sitting.id} with /{sitting.persona_id.root}")
    return 0


def cmd_record(args) -> int:
    from benchside.domain.consultation.model.value import ResearchRecord
    from benchside.domain.consultation.service.consultation import ConsultationService

    _guard_initialized()
    pointer = runtime.require_pointer(runtime.current_paths(), runtime.resolve_project())
    record = ResearchRecord(
        id=runtime.short_id("r"),
        kind=args.kind,
        summary=args.summary,
        details=tuple(args.detail),
        sources=tuple(args.source),
    )
    container, uow = _uow()
    with container, uow:
        uow.get(ConsultationService).record_research(
            consultation_id=pointer["sitting_id"],
            record=record,
        )
    args.ui.success(f"research record saved: {record.id}")
    return 0


def cmd_hypothesis(args) -> int:
    from benchside.domain.consultation.service.consultation import ConsultationService

    _guard_initialized()
    pointer = runtime.require_pointer(runtime.current_paths(), runtime.resolve_project(None))
    hypothesis_id = runtime.short_id("h")
    container, uow = _uow()
    with container, uow:
        uow.get(ConsultationService).state_hypothesis(
            consultation_id=pointer["sitting_id"],
            hypothesis_id=hypothesis_id,
            statement=args.statement,
            supersedes=args.supersedes,
        )
    args.ui.success(f"hypothesis recorded: {hypothesis_id}")
    return 0


def cmd_critique(args) -> int:
    from benchside.domain.consultation.model.value import (
        TargetsClaim,
        TargetsInterpretation,
        TargetsMethod,
    )
    from benchside.domain.consultation.service.consultation import ConsultationService

    target = _build_target(args, TargetsClaim, TargetsMethod, TargetsInterpretation)
    _guard_initialized()
    pointer = runtime.require_pointer(runtime.current_paths(), runtime.resolve_project(None))
    critique_id = runtime.short_id("k")
    container, uow = _uow()
    with container, uow:
        project = uow.get(ConsultationService).raise_critique(
            consultation_id=pointer["sitting_id"], critique_id=critique_id, target=target
        )
    args.ui.success(f"critique recorded: {critique_id} ({len(project.open_critiques)} open)")
    return 0


def _build_target(args, claim_cls, method_cls, interp_cls):
    if args.target == "claim":
        _require(args, "claim", "ground")
        return claim_cls(claim=args.claim, ground=args.ground)
    if args.target == "method":
        _require(args, "step", "flaw")
        return method_cls(step=args.step, flaw=MethodFlaw(args.flaw))
    _require(args, "result", "alternative")
    return interp_cls(result=args.result, alternative=args.alternative)


def _require(args, *names: str) -> None:
    missing = [f"--{n}" for n in names if getattr(args, n) is None]
    if missing:
        raise BenchsideError(f"--target {args.target} requires {' and '.join(missing)}")


def cmd_resolve(args) -> int:
    from benchside.domain.consultation.service.consultation import ConsultationService

    _guard_initialized()
    pointer = runtime.require_pointer(runtime.current_paths(), runtime.resolve_project(None))
    container, uow = _uow()
    with container, uow:
        project = uow.get(ConsultationService).resolve_critique(
            consultation_id=pointer["sitting_id"],
            critique_id=args.critique_id,
            resolution=Resolution(args.resolution),
        )
    args.ui.success(f"critique {args.critique_id} settled ({len(project.open_critiques)} open)")
    return 0


def cmd_decide(args) -> int:
    from benchside.domain.consultation.service.consultation import ConsultationService

    _guard_initialized()
    pointer = runtime.require_pointer(runtime.current_paths(), runtime.resolve_project(None))
    decision_id = runtime.short_id("d")
    container, uow = _uow()
    with container, uow:
        uow.get(ConsultationService).record_decision(
            consultation_id=pointer["sitting_id"],
            decision_id=decision_id,
            decision=args.decision,
            rationale=args.because,
            supersedes=args.supersedes,
        )
    args.ui.success(f"decision recorded: {decision_id}")
    return 0


def cmd_gap(args) -> int:
    from benchside.domain.consultation.service.consultation import ConsultationService
    from benchside.domain.shared.model.gap import (
        DeadEnd,
        ManualToil,
        MissingIndex,
        MissingTool,
        UnfindableData,
    )

    gap = {
        "missing_tool": lambda: MissingTool(
            task=args.task, reached_for=args.reached_for, why_failed=args.why_failed
        ),
        "unfindable_data": lambda: UnfindableData(
            sought=args.sought,
            where_searched=tuple(s.strip() for s in args.where_searched.split(",")),
        ),
        "manual_toil": lambda: ManualToil(task=args.task, frequency=args.frequency),
        "dead_end": lambda: DeadEnd(approach=args.approach, cost=args.cost),
        "missing_index": lambda: MissingIndex(question=args.question),
    }[args.kind]()
    _guard_initialized()
    pointer = runtime.require_pointer(runtime.current_paths(), runtime.resolve_project(None))
    observation_id = runtime.short_id("o")
    container, uow = _uow()
    with container, uow:
        uow.get(ConsultationService).capture_gap(
            consultation_id=pointer["sitting_id"], observation_id=observation_id, gap=gap
        )
    args.ui.success(f"gap recorded locally: {observation_id} ({args.kind})")
    args.ui.detail("stays on this machine; shared only via bench share grant")
    return 0


def cmd_status(args) -> int:
    from benchside.domain.consultation.service.consultation import ConsultationService

    _guard_initialized()
    pointer = runtime.require_pointer(runtime.current_paths(), runtime.resolve_project(None))
    container, uow = _uow()
    with container, uow:
        service = uow.get(ConsultationService)
        sitting = service.get(pointer["sitting_id"])
        project = service.get_project(sitting.project_id)
        counts = service.capture_counts(sitting)
    payload = {
        "sitting_id": sitting.id,
        "state": sitting.state.kind,
        "captured": {k.value: v for k, v in counts.items()},
        "requirements": [
            {"kind": r.kind.value, "minimum": r.minimum, "met": counts.get(r.kind, 0) >= r.minimum}
            for r in sitting.close_requires
        ],
        "open_critiques": [c.id for c in project.critiques if c.is_open],
    }
    if args.json:
        print(json.dumps(payload))
    else:
        args.ui.info(f"sitting {sitting.id}: {sitting.state.kind}")
        for r in payload["requirements"]:
            have = counts.get(CaptureKind(r["kind"]), 0)
            line = f"{r['kind']} ({have}/{r['minimum']})"
            if r["met"]:
                args.ui.success(f"requirement met: {line}")
            else:
                args.ui.warn(f"requirement unmet: {line}")
        open_ids = payload["open_critiques"]
        if open_ids:
            args.ui.warn(f"{len(open_ids)} critique(s) still open")
            for cid in open_ids:
                args.ui.detail(cid)
        else:
            args.ui.detail("no open critiques")
    return 0


def cmd_close(args) -> int:
    from benchside.domain.consultation.service.consultation import ConsultationService

    _guard_initialized()
    paths = runtime.current_paths()
    pointer = runtime.require_pointer(paths, runtime.resolve_project(None))
    container, uow = _uow()
    with container, uow:
        sitting = uow.get(ConsultationService).close(
            consultation_id=pointer["sitting_id"],
            converged=args.converged,
            detail=args.outcome,
        )
    runtime.clear_pointer(paths, sitting.id)
    args.ui.success(f"sitting {sitting.id} closed: {sitting.state.kind}")
    return 0


def cmd_recall(args) -> int:
    from benchside.domain.consultation.query.recall_project import (
        RecallProject,
        RecallProjectHandler,
    )

    runtime.require_initialized()
    project_id = runtime.resolve_project(args.project)
    container, uow = _uow()
    with container, uow:
        recall = uow.get(RecallProjectHandler).run(
            RecallProject(project_id=project_id, history="all" if args.all else "recent")
        )
    if args.json:
        print(recall.model_dump_json())
        return 0
    if (
        not recall.current_hypothesis
        and not recall.open_questions
        and not recall.last_sitting_state
    ):
        args.ui.info(f"project '{project_id.root}': no recorded history yet")
        return 0
    args.ui.info(f"project '{recall.title}'")
    if recall.history == "recent":
        args.ui.detail(
            f"showing {len(recall.recent_decisions)}/{recall.total_decisions} decisions and "
            f"{len(recall.recent_records)}/{recall.total_records} research records; "
            "use recall --all for older entries"
        )
    if recall.current_hypothesis:
        args.ui.detail(f"current hypothesis: {recall.current_hypothesis}")
    for q in recall.open_questions:
        args.ui.warn(f"open: {q}")
    for d in recall.recent_decisions:
        args.ui.detail(f"decided: {d.decision} — {d.rationale}")
    for record in recall.recent_records:
        args.ui.detail(f"{record.kind}: {record.summary}")
        for detail in record.details:
            args.ui.detail(detail)
    for sitting in recall.open_sittings:
        args.ui.detail(f"open sitting: {sitting['id']} (/{sitting['persona']})")
    if recall.last_sitting_state:
        args.ui.detail(f"last sitting: {recall.last_sitting_state}")
    return 0


def cmd_journal_dispatch(args) -> int:
    from benchside.cli.journal import cmd_journal

    return cmd_journal(args)


def cmd_share_dispatch(args) -> int:
    from benchside.cli.sharing import cmd_sharing

    return cmd_sharing(args)


def cmd_compile(args) -> int:
    from benchside.domain.authoring.command.compile import CompileSkills, CompileSkillsHandler

    container, uow = _uow()
    with container, uow:
        result = uow.get(CompileSkillsHandler).run(CompileSkills(dry_run=args.check))
    for name in result.written:
        args.ui.success(f"wrote {name}")
    for name in result.stale:
        args.ui.warn(f"STALE {name}")
    summary = f"compile: {len(result.written)} written, {len(result.unchanged)} unchanged"
    if result.is_fresh:
        args.ui.info(summary)
    else:
        args.ui.error(summary, hint="run `bench compile` and commit the result")
    return 0 if result.is_fresh or not args.check else 1


def cmd_init_dispatch(args) -> int:
    from benchside.cli.install import cmd_init

    return cmd_init(args)


def cmd_setup_dispatch(args) -> int:
    from benchside.cli.install import cmd_setup

    return cmd_setup(args)


def cmd_hook_dispatch(args) -> int:
    from benchside.cli.hooks import cmd_hook

    return cmd_hook(args)


def cmd_app_dispatch(args) -> int:
    from benchside.application.bridge import main as app_main

    return app_main()


if __name__ == "__main__":
    sys.exit(main())
