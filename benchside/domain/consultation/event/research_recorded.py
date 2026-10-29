from benchside.domain.consultation.model.value import ResearchRecord
from benchside.domain.shared.event import Event
from benchside.domain.shared.model.ids import ConsultationId, ProjectId


class ResearchRecorded(Event):
    project_id: ProjectId
    consultation_id: ConsultationId
    record: ResearchRecord
