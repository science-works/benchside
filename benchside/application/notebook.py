"""Private checkpoints without opening or counting a role consultation.

The app validates the selected project/session and holds the transaction lock.
Reuse the journal events so role and notebook recall see the same history.
"""

from uuid import uuid4

from pydantic import TypeAdapter

from benchside.domain.consultation.event.decision_recorded import DecisionRecorded
from benchside.domain.consultation.event.gap_observed import GapObserved
from benchside.domain.consultation.event.question import QuestionAnswered, QuestionRecorded
from benchside.domain.consultation.event.research_recorded import ResearchRecorded
from benchside.domain.consultation.model.project import Project
from benchside.domain.consultation.model.value import Decision, ResearchQuestion, ResearchRecord
from benchside.domain.shared.error import ValidationError
from benchside.domain.shared.event import new_event_id
from benchside.domain.shared.model.gap import Gap


def record_checkpoint(app, project_id, action, request):
    if request.get("sitting_id"):
        raise ValidationError("Notebook actions do not take a sitting; use the role action instead")
    project = app.service.projects.get(project_id)
    common = {"id": new_event_id(), "project_id": project_id, "consultation_id": None}
    identifier = uuid4().hex
    match action:
        case "notebook.decide":
            if not isinstance(request.get("decision"), str) or not request["decision"].strip():
                raise ValidationError("A notebook decision needs decision")
            rationale = request.get("rationale", "")
            if not isinstance(rationale, str):
                raise ValidationError("A decision rationale must be text or omitted")
            supersedes = request.get("supersedes")
            identifier = f"d-{identifier}"
            event = DecisionRecorded(
                **common,
                decision_id=identifier,
                decision=request["decision"],
                rationale=rationale if rationale.strip() else "",
                supersedes=supersedes,
            )
            # Setup registers a project before its first scientific journal event.
            project = project or Project(id=project_id, title=project_id.root)
            project.record_decision(Decision(
                id=identifier, decision=event.decision, rationale=event.rationale,
                decided_at=event.recorded_at, supersedes=supersedes,
            ))
        case "notebook.record":
            identifier = f"r-{identifier}"
            record = ResearchRecord(id=identifier, **request["record"])
            if record.kind not in {"note", "evidence"}:
                raise ValidationError(
                    "Notebook records use note or evidence; role records use their role action"
                )
            if record.kind == "evidence" and not record.sources:
                raise ValidationError(
                    "Evidence needs an actual inspected source or explicit researcher report"
                )
            event = ResearchRecorded(**common, record=record)
        case "notebook.question":
            identifier = f"q-{identifier}"
            event = QuestionRecorded(
                **common, question=ResearchQuestion(id=identifier, question=request["question"])
            )
        case "notebook.answer":
            identifier = request["question_id"]
            question = (
                next((q for q in project.questions if q.id == identifier), None)
                if project
                else None
            )
            if question is None or question.answer is not None:
                raise ValidationError("Question not found in this project or already answered")
            event = QuestionAnswered(**common, question_id=identifier, answer=request["answer"])
        case "notebook.gap":
            identifier = f"o-{identifier}"
            event = GapObserved(
                **common,
                observation_id=identifier,
                gap=TypeAdapter(Gap).validate_python(request["gap"]),
                basis=request.get("basis", "unknown"),
            )
        case _:
            raise ValidationError("Unknown notebook action")
    app.journal.append(project_id, event)
    return identifier
