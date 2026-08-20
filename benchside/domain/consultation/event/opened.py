from benchside.domain.shared.event import Event
from benchside.domain.shared.model.capture import CloseRequirement
from benchside.domain.shared.model.ids import ConsultationId, PersonaId, ProjectId


class ConsultationOpened(Event):
    """A scientist started a sitting with a persona.

    `close_requires` is snapshotted from the persona at open time so replay
    determinism never depends on a mutable YAML outside the journal.
    """

    consultation_id: ConsultationId
    project_id: ProjectId
    persona_id: PersonaId
    close_requires: tuple[CloseRequirement, ...] = ()
