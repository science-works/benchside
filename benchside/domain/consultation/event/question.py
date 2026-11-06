from benchside.domain.consultation.model.value import NonEmptyText, ResearchQuestion
from benchside.domain.shared.event import Event
from benchside.domain.shared.model.ids import ConsultationId, ProjectId


class QuestionRecorded(Event):
    project_id: ProjectId
    consultation_id: ConsultationId
    question: ResearchQuestion


class QuestionAnswered(Event):
    project_id: ProjectId
    consultation_id: ConsultationId
    question_id: NonEmptyText
    answer: NonEmptyText
