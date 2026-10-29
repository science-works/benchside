from benchside.domain.authoring.service.authoring import AuthoringService
from benchside.domain.consultation.service.consultation import ConsultationService
from benchside.domain.shared.command import Command, CommandHandler, Result
from benchside.domain.shared.model.ids import ConsultationId, PersonaId, ProjectId


class OpenConsultation(Command):
    consultation_id: ConsultationId
    project_id: ProjectId
    persona_id: PersonaId


class ConsultationOpened(Result):
    consultation_id: ConsultationId
    state: str


class OpenConsultationHandler(CommandHandler[OpenConsultation, ConsultationOpened]):
    consultation_service: ConsultationService
    authoring_service: AuthoringService

    def run(self, cmd: OpenConsultation) -> ConsultationOpened:
        persona = self.authoring_service.get(cmd.persona_id)
        consultation = self.consultation_service.open(
            consultation_id=cmd.consultation_id,
            project_id=cmd.project_id,
            persona_id=cmd.persona_id,
            close_requires=persona.flow.close_requires,
            critique_requires_hypothesis=persona.critique_requires_hypothesis,
            record_kind=persona.record_kind,
            persona_version=persona.version,
        )
        return ConsultationOpened(
            consultation_id=consultation.id,
            state=consultation.state.kind,
        )
