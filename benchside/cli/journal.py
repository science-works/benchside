"""Read-only journal views: the scientist's window into the record.

This is the human surface, so it gets the full UI treatment — headers,
glyphed state columns, warnings for what needs attention. Everything is a
fold over the project's event stream; no mutations, no new domain surface.
`journal events --json` is the one machine channel here and stays pure stdout.
"""

import json

from benchside.application.di import create_container
from benchside.cli import runtime
from benchside.cli.ui import UI, default_glyphs
from benchside.domain.consultation.port.repository import (
    ConsultationRepository,
    ProjectRepository,
)
from benchside.domain.shared.port.journal import Journal
from benchside.util.di import Scope

_G = default_glyphs()


def cmd_journal(args) -> int:
    runtime.require_initialized()
    ui: UI = args.ui
    project_id = runtime.resolve_project(getattr(args, "project", None))
    container = create_container()
    with container, container(scope=Scope.UOW) as uow:
        project = uow.get(ProjectRepository).get(project_id)
        if project is None and args.view != "events":
            ui.info(f"project '{project_id.root}': no recorded history yet")
            return 0
        match args.view:
            case "show":
                _show(ui, project, uow.get(ConsultationRepository).list_for_project(project_id))
            case "sittings":
                _sittings(ui, uow.get(ConsultationRepository).list_for_project(project_id))
            case "hypotheses":
                _hypotheses(ui, project)
            case "critiques":
                _critiques(ui, project, only_open=args.open)
            case "decisions":
                _decisions(ui, project)
            case "gaps":
                _gaps(ui, uow.get(Journal), project_id)
            case "events":
                _events(uow.get(Journal), project_id, as_json=args.json)
    return 0


def _plural(n: int, word: str, plural: str | None = None) -> str:
    return f"{n} {word if n == 1 else (plural or word + 's')}"


def _show(ui: UI, project, sittings) -> None:
    """The dashboard: what is claimed, what stands against it, what was decided."""
    ui.header(project.title)

    open_critiques = [c for c in project.critiques if c.is_open]
    ui.detail(
        "  ·  ".join(
            [
                _plural(len(project.hypotheses), "hypothesis", "hypotheses"),
                f"{_plural(len(project.critiques), 'critique')} ({len(open_critiques)} open)",
                _plural(len(project.decisions), "decision"),
                _plural(len(sittings), "sitting"),
            ]
        )
    )
    ui.info("")

    current = project.current_hypothesis
    if current:
        ui.section("hypothesis", meta=current.id)
        ui.block(current.statement)
    else:
        ui.warn("no hypothesis on the table yet")

    live = [s for s in sittings if s.state.kind not in ("converged", "abandoned")]
    if open_critiques or live:
        ui.section("needs attention")
        for critique in open_critiques:
            ui.warn(f"{critique.id}  {_target_line(critique.target)}")
        for sitting in live:
            ui.warn(f"sitting {sitting.id} is still open ({sitting.state.kind})")
    else:
        ui.section("standing")
        ui.success("all critiques settled; no sitting left open")

    if project.decisions:
        decision = project.decisions[-1]
        ui.section("latest decision", meta=decision.id)
        ui.block(decision.decision)
        ui.block(f"because — {decision.rationale}", dim=True)
        if len(project.decisions) > 1:
            ui.detail(f"({len(project.decisions) - 1} earlier — bench journal decisions)")


def _sittings(ui: UI, sittings) -> None:
    if not sittings:
        ui.info("no sittings yet")
        return
    state_glyph = {"converged": _G.check, "abandoned": _G.dot}
    ui.table(
        ["", "ID", "PERSONA", "STATE"],
        [
            [state_glyph.get(s.state.kind, _G.warn), s.id, s.persona_id.root, s.state.kind]
            for s in sittings
        ],
    )


def _hypotheses(ui: UI, project) -> None:
    if not project.hypotheses:
        ui.info("no hypotheses yet")
        return
    superseded = {h.supersedes for h in project.hypotheses if h.supersedes is not None}
    rows = []
    for hypothesis in project.hypotheses:
        old = hypothesis.id in superseded
        glyph = "−" if old else _G.check
        note = f"supersedes {hypothesis.supersedes}" if hypothesis.supersedes else ""
        rows.append([glyph, hypothesis.id, hypothesis.statement, note])
    ui.table(["", "ID", "HYPOTHESIS", "NOTES"], rows)


def _critiques(ui: UI, project, *, only_open: bool) -> None:
    critiques = [c for c in project.critiques if c.is_open or not only_open]
    if not critiques:
        ui.info("no open critiques" if only_open else "no critiques yet")
        return
    rows = [
        [
            _G.warn if c.is_open else _G.check,
            c.id,
            _target_line(c.target),
            "open" if c.is_open else c.resolution.value,
        ]
        for c in critiques
    ]
    ui.table(["", "ID", "TARGET", "RESOLUTION"], rows)


def _decisions(ui: UI, project) -> None:
    if not project.decisions:
        ui.info("no decisions yet")
        return
    rows = [
        [d.id, d.decision, d.rationale, f"supersedes {d.supersedes}" if d.supersedes else ""]
        for d in project.decisions
    ]
    ui.table(["ID", "DECISION", "BECAUSE", "NOTES"], rows)


def _gaps(ui: UI, journal, project_id) -> None:
    from benchside.domain.consultation.event.gap_observed import GapObserved

    found = [e for e in journal.read(project_id) if isinstance(e, GapObserved)]
    if not found:
        ui.info("no gaps recorded yet")
        return
    rows = []
    for event in found:
        gap = event.gap
        detail = getattr(gap, "question", None) or getattr(gap, "task", None) or gap.kind
        rows.append([event.observation_id, gap.kind, detail])
    ui.table(["ID", "KIND", "DETAIL"], rows)


def _events(journal, project_id, *, as_json: bool) -> None:
    """The raw stream: data, so stdout — pipeable either way."""
    for event in journal.read(project_id):
        if as_json:
            print(json.dumps({"type": type(event).__name__, "data": event.model_dump(mode="json")}))
        else:
            data = event.model_dump(mode="json")
            keys = [k for k in ("statement", "detail", "decision", "resolution") if data.get(k)]
            extra = f" | {data[keys[0]][:60]}" if keys else ""
            print(f"{data['recorded_at'][:19]} {type(event).__name__}{extra}")


def _target_line(target) -> str:
    match target.kind:
        case "claim":
            return f"claim: {target.claim}"
        case "method":
            return f"method ({target.flaw}): {target.step}"
        case _:
            return f"interpretation: {target.result}"
