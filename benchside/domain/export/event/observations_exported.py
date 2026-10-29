from benchside.domain.shared.event import Event
from benchside.domain.shared.model.ids import GrantId, ObservationId


class ObservationsExported(Event):
    """Proof of what left the machine. Content-free: ids and a digest only."""

    grant_id: GrantId
    observation_ids: tuple[ObservationId, ...]
    payload_sha256: str
    destination: str = ""
    received_at: str | None = None
