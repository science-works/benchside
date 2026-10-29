"""Export value objects.

Consent is event-sourced: a grant is never mutated, only superseded by a
revocation. That is what makes revocation meaningful -- the ledger records
exactly what left the machine and when.
"""

from datetime import datetime
from enum import StrEnum
from typing import Literal

from benchside.domain.shared.model.gap import Gap
from benchside.domain.shared.model.ids import GrantId, ObservationId, ProjectId
from benchside.domain.shared.model.value import ValueObject


class GrantStatus(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"


class Grant(ValueObject):
    """Permission to share observations of the listed gap kinds."""

    id: GrantId
    gap_kinds: frozenset[str]
    granted_at: datetime
    revoked_at: datetime | None = None

    @property
    def status(self) -> GrantStatus:
        return GrantStatus.ACTIVE if self.revoked_at is None else GrantStatus.REVOKED

    def covers(self, gap: Gap) -> bool:
        return self.revoked_at is None and gap.kind in self.gap_kinds


class Observation(ValueObject):
    """A captured gap, folded from the journal. Local until an export sends it."""

    id: ObservationId
    project_id: ProjectId
    gap: Gap
    origin: Literal["benchside", "selected_conversation"] = "benchside"
    basis: Literal["model_inferred", "researcher_reported", "unknown"] = "unknown"


class ExportRecord(ValueObject):
    """Proof of what one export sent. Content-free.

    Holds ids and a digest of the payload, never the payload itself, so the
    ledger can be audited without re-exposing what it describes.
    """

    grant_id: GrantId
    observation_ids: tuple[ObservationId, ...]
    payload_sha256: str
    exported_at: datetime
    destination: str = ""
    received_at: str | None = None


class ExportPreview(ValueObject):
    """Exactly what would be sent, for the scientist to read before deciding."""

    payload: str
    observation_ids: tuple[ObservationId, ...]
    withheld: tuple[ObservationId, ...] = ()
    redaction_findings: tuple[str, ...] = ()
    grant_id: GrantId | None = None
    payload_sha256: str = ""
    destination: str = ""


class DeliveryReceipt(ValueObject):
    status: str
    sha256: str
    received_at: str
    observations: int
