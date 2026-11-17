from typing import Literal

from pydantic import model_serializer

from benchside.domain.shared.event import Event
from benchside.domain.shared.model.gap import Gap
from benchside.domain.shared.model.ids import ConsultationId, ObservationId, ProjectId


class GapObserved(Event):
    """The scientific workflow broke down. Local until export is consented to.

    Recorded here because gaps surface during meetings; read by the export
    domain, which governs whether they ever leave the machine.
    """

    project_id: ProjectId
    consultation_id: ConsultationId | None
    observation_id: ObservationId
    gap: Gap
    basis: Literal["researcher_reported", "model_inferred", "unknown"] = "unknown"

    @model_serializer(mode="wrap")
    def legacy_observation_shape(self, handler):
        value = handler(self)
        if self.basis == "unknown":
            value.pop("basis", None)
        return value
