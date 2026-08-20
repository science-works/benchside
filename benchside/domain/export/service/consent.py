"""Consent business logic.

The sole authority on whether anything may be shared. ExportService asks this
service and nothing else.
"""

import logging
from datetime import UTC, datetime

from benchside.domain.export.event.consent_granted import ConsentGranted
from benchside.domain.export.event.consent_revoked import ConsentRevoked
from benchside.domain.export.model.value import Grant
from benchside.domain.export.port.repository import ConsentRepository
from benchside.domain.shared.event import new_event_id
from benchside.domain.shared.model.gap import GAP_KINDS
from benchside.domain.shared.model.ids import CONSENT_LEDGER_PROJECT, GrantId
from benchside.domain.shared.port.journal import Journal
from benchside.domain.shared.service import Service

logger = logging.getLogger(__name__)


class ConsentService(Service):
    repository: ConsentRepository
    journal: Journal

    def active_grant(self) -> Grant | None:
        return self.repository.load().active_grant

    def has_active_grant(self) -> bool:
        return self.active_grant() is not None

    def grant(self, *, grant_id: GrantId, gap_kinds: frozenset[str]) -> Grant:
        unknown = gap_kinds - GAP_KINDS
        if unknown:
            raise ValueError(f"Unknown gap kinds: {sorted(unknown)}")
        ledger = self.repository.load()
        grant = Grant(id=grant_id, gap_kinds=gap_kinds, granted_at=datetime.now(UTC))
        ledger.grant(grant)
        self.journal.append(
            CONSENT_LEDGER_PROJECT,
            ConsentGranted(id=new_event_id(), grant_id=grant_id, gap_kinds=gap_kinds),
        )
        return grant

    def revoke(self) -> Grant:
        ledger = self.repository.load()
        revoked = ledger.revoke(datetime.now(UTC))
        self.journal.append(
            CONSENT_LEDGER_PROJECT,
            ConsentRevoked(id=new_event_id(), grant_id=revoked.id),
        )
        return revoked
