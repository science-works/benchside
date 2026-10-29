from benchside.domain.consultation.model.value import RecordKind
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
    critique_requires_hypothesis: bool = True
    record_kind: RecordKind | None = None
    persona_version: str = "1"
    host: str = "unknown"
    app_version: str = "unknown"
    surface: str = "unknown"
