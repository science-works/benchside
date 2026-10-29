"""What a persona reads at the start of a sitting.

The cross-session continuity surface: computed from the project's accumulated
record, never re-summarised from conversation prose.
"""

from typing import Literal

from pydantic import Field

from benchside.domain.consultation.model.value import Decision, ResearchRecord, Target
from benchside.domain.consultation.service.consultation import ConsultationService
from benchside.domain.shared.command import Result
from benchside.domain.shared.error import NotFoundError
from benchside.domain.shared.model.ids import ProjectId
from benchside.domain.shared.query import Query, QueryHandler


class RecallProject(Query):
    project_id: ProjectId
    history: Literal["recent", "all"] = "recent"


class ProjectRecall(Result):
    project_id: ProjectId
    title: str
    history: Literal["recent", "all"] = "recent"
    total_decisions: int = 0
    total_records: int = 0
    current_hypothesis: str | None = None
    open_questions: list[str] = Field(default_factory=list)
    recent_decisions: list[Decision] = Field(default_factory=list)
    last_sitting_state: str | None = None
    recent_records: list[ResearchRecord] = Field(default_factory=list)
    open_sittings: list[dict[str, str]] = Field(default_factory=list)


class RecallProjectHandler(QueryHandler[RecallProject, ProjectRecall]):
    consultation_service: ConsultationService

    def run(self, query: RecallProject) -> ProjectRecall:
        try:
            project = self.consultation_service.get_project(query.project_id)
        except NotFoundError:
            # A fresh project has no journal yet. That is an empty recall,
            # not an error -- SessionStart injection must survive it.
            return ProjectRecall(
                project_id=query.project_id, title=query.project_id.root, history=query.history
            )
        latest = self.consultation_service.latest_for_project(query.project_id)
        current = project.current_hypothesis
        return ProjectRecall(
            project_id=project.id,
            title=project.title,
            history=query.history,
            total_decisions=len(project.decisions),
            total_records=len(project.research_records),
            current_hypothesis=current.statement if current else None,
            open_questions=[describe_target(c.target) for c in project.critiques if c.is_open],
            recent_decisions=project.decisions
            if query.history == "all"
            else project.decisions[-5:],
            last_sitting_state=latest.state.kind if latest else None,
            recent_records=(
                project.research_records
                if query.history == "all"
                else project.research_records[-5:]
            ),
            open_sittings=[
                {"id": c.id, "persona": c.persona_id.root}
                for c in self.consultation_service.consultations.list_for_project(project.id)
                if c.state.kind not in {"converged", "abandoned"}
            ],
        )


def describe_target(target: Target) -> str:
    """Render a critique target as one line for the persona to read back."""
    match target.kind:
        case "claim":
            return f"claim: {target.claim}; concern: {target.ground}"
        case "method":
            return f"method ({target.flaw}): {target.step}"
        case _:
            return f"interpretation: {target.result}; alternative: {target.alternative}"
