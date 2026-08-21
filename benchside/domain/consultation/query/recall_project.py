"""What a persona reads at the start of a sitting.

The cross-session continuity surface: computed from the project's accumulated
record, never re-summarised from conversation prose.
"""

from pydantic import Field

from benchside.domain.consultation.model.value import Decision, Target
from benchside.domain.consultation.service.consultation import ConsultationService
from benchside.domain.shared.error import NotFoundError
from benchside.domain.shared.command import Result
from benchside.domain.shared.model.ids import ProjectId
from benchside.domain.shared.query import Query, QueryHandler


class RecallProject(Query):
    project_id: ProjectId


class ProjectRecall(Result):
    project_id: ProjectId
    title: str
    current_hypothesis: str | None = None
    open_questions: list[str] = Field(default_factory=list)
    recent_decisions: list[Decision] = Field(default_factory=list)
    last_sitting_state: str | None = None


class RecallProjectHandler(QueryHandler[RecallProject, ProjectRecall]):
    consultation_service: ConsultationService

    def run(self, query: RecallProject) -> ProjectRecall:
        try:
            project = self.consultation_service.get_project(query.project_id)
        except NotFoundError:
            # A fresh project has no journal yet. That is an empty recall,
            # not an error -- SessionStart injection must survive it.
            return ProjectRecall(project_id=query.project_id, title=query.project_id.root)
        latest = self.consultation_service.latest_for_project(query.project_id)
        current = project.current_hypothesis
        return ProjectRecall(
            project_id=project.id,
            title=project.title,
            current_hypothesis=current.statement if current else None,
            open_questions=[describe_target(c.target) for c in project.critiques if c.is_open],
            recent_decisions=project.decisions[-5:],
            last_sitting_state=latest.state.kind if latest else None,
        )


def describe_target(target: Target) -> str:
    """Render a critique target as one line for the persona to read back."""
    match target.kind:
        case "claim":
            return f"claim: {target.claim}"
        case "method":
            return f"method ({target.flaw}): {target.step}"
        case _:
            return f"interpretation: {target.result}"
