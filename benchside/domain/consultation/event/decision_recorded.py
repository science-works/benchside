from benchside.domain.shared.event import Event
from benchside.domain.shared.model.ids import ConsultationId, DecisionId, ProjectId


class DecisionRecorded(Event):
    """A durable call was made, with its rationale, so it is not re-litigated."""

    project_id: ProjectId
    consultation_id: ConsultationId | None
    decision_id: DecisionId
    decision: str
    rationale: str
    supersedes: DecisionId | None = None
