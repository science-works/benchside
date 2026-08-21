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

from benchside.application.di import create_container
from benchside.cli import runtime
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
    try:
        return args.run(args)
    except BenchsideError as err:
        print(f"error: {err.message}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bench", description="benchside: science workspace CLI")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("project", help="print the resolved project id")
    p.add_argument("--project", default=None)
    p.add_argument("--json", action="store_true")
    p.set_defaults(run=cmd_project)

    p = sub.add_parser("open", help="open a sitting with a persona")
    p.add_argument("--persona", required=True)
    p.add_argument("--project", default=None)
    p.set_defaults(run=cmd_open)

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

    p = sub.add_parser("gap", help="record a workflow breakdown (local until consented)")
    gap_sub = p.add_subparsers(dest="kind", required=True)
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

    p = sub.add_parser("status", help="sitting state, captures, and requirements")
    p.add_argument("--json", action="store_true")
    p.set_defaults(run=cmd_status)

    p = sub.add_parser("close", help="close the sitting")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--converged", action="store_true")
    group.add_argument("--abandoned", action="store_true")
    p.add_argument("--outcome", default="", help="agreed next step (or abandonment reason)")
    p.set_defaults(run=cmd_close)

    p = sub.add_parser("recall", help="what a persona reads at the start of a sitting")
    p.add_argument("--project", default=None)
    p.add_argument("--json", action="store_true")
    p.set_defaults(run=cmd_recall)

    p = sub.add_parser("consent", help="govern sharing of gap observations")
    consent_sub = p.add_subparsers(dest="action", required=True)
    c = consent_sub.add_parser("grant")
    c.add_argument("--kinds", required=True, help=f"comma-separated from: {sorted(GAP_KINDS)}")
    consent_sub.add_parser("revoke")
    consent_sub.add_parser("status")
    p.set_defaults(run=cmd_consent)

    p = sub.add_parser("export", help="share consented gap observations")
    p.add_argument(
        "--preview",
        action="store_true",
        help="show the exact bytes an export would send; sends nothing",
    )
    p.set_defaults(run=cmd_export)

    p = sub.add_parser("init", help="initialize this directory as a benchside project")
    p.add_argument("--yes", action="store_true", help="consent non-interactively")
    p.add_argument("--project", default=None)
    p.set_defaults(run=cmd_init_dispatch)

    p = sub.add_parser("hook", help="Claude Code hook entry points (stdin JSON)")
    p.add_argument("event", choices=["session-start", "session-end"])
    p.set_defaults(run=cmd_hook_dispatch)

    p = sub.add_parser("compile", help="compile personas into skills")
    p.add_argument("--check", action="store_true", help="dry-run freshness check")
    p.set_defaults(run=cmd_compile)

    return parser


def _uow():
    container = create_container()
    return container, container(scope=Scope.UOW)


def cmd_project(args) -> int:
    project_id = runtime.resolve_project(args.project)
    if args.json:
        print(json.dumps({"project_id": project_id.root}))
    else:
        print(f"project: {project_id.root}")
    return 0


def cmd_open(args) -> int:
    from benchside.domain.authoring.service.authoring import AuthoringService
    from benchside.domain.consultation.service.consultation import ConsultationService

    paths = runtime.current_paths()
    project_id = runtime.resolve_project(args.project)
    for record in runtime.live_pointers(paths):
        if (
            record.get("session") == runtime.session_name()
            and record.get("project_id") == project_id.root
        ):
            raise BenchsideError(
                f"A sitting is already open for this project: {record['sitting_id']}. "
                f"Resume it (it is this session's active sitting) or close it first "
                f"with `bench close`."
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
        )
    runtime.write_pointer(
        paths, sitting_id=sitting_id, project_id=project_id, persona_id=persona.id.root
    )
    print(f"Sitting open with /{persona.id.root} on project '{project_id.root}'.")
    print(f"<bench-sitting:{sitting_id}>")
    return 0


def cmd_hypothesis(args) -> int:
    from benchside.domain.consultation.service.consultation import ConsultationService

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
    print(f"hypothesis recorded: {hypothesis_id}")
    return 0


def cmd_critique(args) -> int:
    from benchside.domain.consultation.model.value import (
        TargetsClaim,
        TargetsInterpretation,
        TargetsMethod,
    )
    from benchside.domain.consultation.service.consultation import ConsultationService

    target = _build_target(args, TargetsClaim, TargetsMethod, TargetsInterpretation)
    pointer = runtime.require_pointer(runtime.current_paths(), runtime.resolve_project(None))
    critique_id = runtime.short_id("k")
    container, uow = _uow()
    with container, uow:
        project = uow.get(ConsultationService).raise_critique(
            consultation_id=pointer["sitting_id"], critique_id=critique_id, target=target
        )
    print(f"critique recorded: {critique_id} ({len(project.open_critiques)} open)")
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

    pointer = runtime.require_pointer(runtime.current_paths(), runtime.resolve_project(None))
    container, uow = _uow()
    with container, uow:
        project = uow.get(ConsultationService).resolve_critique(
            consultation_id=pointer["sitting_id"],
            critique_id=args.critique_id,
            resolution=Resolution(args.resolution),
        )
    print(f"critique {args.critique_id} settled ({len(project.open_critiques)} open)")
    return 0


def cmd_decide(args) -> int:
    from benchside.domain.consultation.service.consultation import ConsultationService

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
    print(f"decision recorded: {decision_id}")
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
    pointer = runtime.require_pointer(runtime.current_paths(), runtime.resolve_project(None))
    observation_id = runtime.short_id("o")
    container, uow = _uow()
    with container, uow:
        uow.get(ConsultationService).capture_gap(
            consultation_id=pointer["sitting_id"], observation_id=observation_id, gap=gap
        )
    print(f"gap recorded locally: {observation_id} ({args.kind}). Shared only via bench consent.")
    return 0


def cmd_status(args) -> int:
    from benchside.domain.consultation.service.consultation import ConsultationService

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
        parts = []
        for r in payload["requirements"]:
            have = counts.get(CaptureKind(r["kind"]), 0)
            parts.append(f"{r['kind']} ✓" if r["met"] else f"{r['kind']} {have}/{r['minimum']}")
        reqs = ", ".join(parts) or "none"
        print(
            f"sitting {sitting.id}: {sitting.state.kind}; requirements: {reqs}; "
            f"open critiques: {len(payload['open_critiques'])}"
        )
    return 0


def cmd_close(args) -> int:
    from benchside.domain.consultation.service.consultation import ConsultationService

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
    print(f"sitting {sitting.id} closed: {sitting.state.kind}")
    return 0


def cmd_recall(args) -> int:
    from benchside.domain.consultation.query.recall_project import (
        RecallProject,
        RecallProjectHandler,
    )

    project_id = runtime.resolve_project(args.project)
    container, uow = _uow()
    with container, uow:
        recall = uow.get(RecallProjectHandler).run(RecallProject(project_id=project_id))
    if args.json:
        print(recall.model_dump_json())
        return 0
    if (
        not recall.current_hypothesis
        and not recall.open_questions
        and not recall.last_sitting_state
    ):
        print(f"project '{project_id.root}': no recorded history yet")
        return 0
    print(f"project '{recall.title}':")
    if recall.current_hypothesis:
        print(f"  current hypothesis: {recall.current_hypothesis}")
    for q in recall.open_questions:
        print(f"  open: {q}")
    for d in recall.recent_decisions:
        print(f"  decided: {d.decision} — {d.rationale}")
    if recall.last_sitting_state:
        print(f"  last sitting: {recall.last_sitting_state}")
    return 0


def cmd_consent(args) -> int:
    from benchside.domain.export.service.consent import ConsentService

    container, uow = _uow()
    with container, uow:
        service = uow.get(ConsentService)
        if args.action == "grant":
            kinds = frozenset(k.strip() for k in args.kinds.split(","))
            grant = service.grant(grant_id=runtime.short_id("g"), gap_kinds=kinds)
            print(f"consent granted ({grant.id}) for: {', '.join(sorted(grant.gap_kinds))}")
        elif args.action == "revoke":
            revoked = service.revoke()
            print(f"consent revoked ({revoked.id}); nothing further will be shared")
        else:
            grant = service.active_grant()
            if grant is None:
                print("consent: none granted; all observations stay local")
            else:
                print(f"consent: active ({grant.id}) for {', '.join(sorted(grant.gap_kinds))}")
    return 0


def cmd_export(args) -> int:
    from benchside.domain.export.service.export import ExportService

    container, uow = _uow()
    with container, uow:
        service = uow.get(ExportService)
        if args.preview:
            preview = service.preview()
            print("=== export preview: the EXACT bytes an export would send ===")
            print(preview.payload)
            print(
                f"=== observations included: {len(preview.observation_ids)}; "
                f"withheld (not covered by consent): {len(preview.withheld)} ==="
            )
            findings = "; ".join(preview.redaction_findings) or "none flagged"
            print(f"=== redaction: passthrough engine (v0 placeholder); findings: {findings} ===")
            return 0
        record = service.export()
        print(
            f"exported {len(record.observation_ids)} observations "
            f"(sha256 {record.payload_sha256[:12]})"
        )
    return 0


def cmd_compile(args) -> int:
    from benchside.domain.authoring.command.compile import CompileSkills, CompileSkillsHandler

    container, uow = _uow()
    with container, uow:
        result = uow.get(CompileSkillsHandler).run(CompileSkills(dry_run=args.check))
    for name in result.written:
        print(f"wrote {name}")
    for name in result.stale:
        print(f"STALE {name}")
    print(
        f"compile: {len(result.written)} written, {len(result.unchanged)} unchanged"
        + ("" if result.is_fresh else "; STALE OUTPUT — run bench compile")
    )
    return 0 if result.is_fresh or not args.check else 1


def cmd_init_dispatch(args) -> int:
    from benchside.cli.install import cmd_init

    return cmd_init(args)


def cmd_hook_dispatch(args) -> int:
    from benchside.cli.hooks import cmd_hook

    return cmd_hook(args)


if __name__ == "__main__":
    sys.exit(main())
