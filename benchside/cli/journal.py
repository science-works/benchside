"""Read-only journal views: the scientist's ways of querying the record.

Everything here is a fold over the project's event stream — no mutations, no
new domain surface. `journal show` is the human's counterpart to what
`recall` is for the persona.
"""

import json

from benchside.application.di import create_container
from benchside.cli import runtime
from benchside.domain.consultation.port.repository import (
    ConsultationRepository,
    ProjectRepository,
)
from benchside.domain.shared.port.journal import Journal
from benchside.util.di import Scope


def cmd_journal(args) -> int:
    runtime.require_initialized()
    project_id = runtime.resolve_project(getattr(args, "project", None))
    container = create_container()
    with container, container(scope=Scope.UOW) as uow:
        project = uow.get(ProjectRepository).get(project_id)
        if project is None and args.view != "events":
            print(f"project '{project_id.root}': no recorded history yet")
            return 0
        match args.view:
            case "show":
                _show(project, uow.get(ConsultationRepository).list_for_project(project_id))
            case "sittings":
                _sittings(uow.get(ConsultationRepository).list_for_project(project_id))
            case "hypotheses":
                _hypotheses(project)
            case "critiques":
                _critiques(project, only_open=args.open)
            case "decisions":
                _decisions(project)
            case "gaps":
                _gaps(uow.get(Journal), project_id)
            case "events":
                _events(uow.get(Journal), project_id, as_json=args.json)
    return 0


def _show(project, sittings) -> None:
    print(f"project '{project.title}'")
    current = project.current_hypothesis
    if current:
        print(f"\ncurrent hypothesis: {current.statement}")
    open_count = len(project.open_critiques)
    print(
        f"\n{len(project.hypotheses)} hypothesis(es), {len(project.critiques)} critique(s) "
        f"({open_count} open), {len(project.decisions)} decision(s), {len(sittings)} sitting(s)"
    )
    for decision in project.decisions[-3:]:
        print(f"  decided: {decision.decision} — {decision.rationale}")
    for critique in project.critiques:
        if critique.is_open:
            print(f"  OPEN: {_target_line(critique.target)}")


def _sittings(sittings) -> None:
    if not sittings:
        print("no sittings yet")
        return
    for sitting in sittings:
        print(f"{sitting.id}  persona={sitting.persona_id.root}  state={sitting.state.kind}")


def _hypotheses(project) -> None:
    if not project.hypotheses:
        print("no hypotheses yet")
        return
    superseded = {h.supersedes for h in project.hypotheses if h.supersedes is not None}
    for hypothesis in project.hypotheses:
        tag = "superseded" if hypothesis.id in superseded else "current"
        via = f" (supersedes {hypothesis.supersedes})" if hypothesis.supersedes else ""
        print(f"[{tag}] {hypothesis.id}: {hypothesis.statement}{via}")


def _critiques(project, *, only_open: bool) -> None:
    critiques = [c for c in project.critiques if c.is_open or not only_open]
    if not critiques:
        print("no open critiques" if only_open else "no critiques yet")
        return
    for critique in critiques:
        state = "open" if critique.is_open else critique.resolution.value
        print(f"[{state}] {critique.id}: {_target_line(critique.target)}")


def _decisions(project) -> None:
    if not project.decisions:
        print("no decisions yet")
        return
    for decision in project.decisions:
        via = f" (supersedes {decision.supersedes})" if decision.supersedes else ""
        print(f"{decision.id}: {decision.decision} — {decision.rationale}{via}")


def _gaps(journal, project_id) -> None:
    from benchside.domain.consultation.event.gap_observed import GapObserved

    found = [e for e in journal.read(project_id) if isinstance(e, GapObserved)]
    if not found:
        print("no gaps recorded yet")
        return
    for event in found:
        gap = event.gap
        detail = getattr(gap, "question", None) or getattr(gap, "task", None) or gap.kind
        print(f"{event.observation_id} [{gap.kind}] {detail}")


def _events(journal, project_id, *, as_json: bool) -> None:
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
