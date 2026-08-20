"""Export business logic -- the disclosure chokepoint.

The only path from a local observation to anywhere else. The order is not
negotiable: ask consent, filter to what the grant covers, redact, preview the
exact bytes, then send those same bytes. Never scan a string and re-render it,
which would reopen a scan-versus-send gap.
"""

import hashlib
import json
import logging

from benchside.domain.export.event.observations_exported import ObservationsExported
from benchside.domain.export.model.value import ExportPreview, ExportRecord, Observation
from benchside.domain.export.port.redactor import Redactor
from benchside.domain.export.port.repository import ConsentRepository, ObservationReader
from benchside.domain.export.port.sink import ExportSink
from benchside.domain.export.service.consent import CONSENT_LEDGER_PROJECT, ConsentService
from benchside.domain.shared.error import ConsentRequiredError
from benchside.domain.shared.model.ids import GrantId
from benchside.domain.shared.port.journal import Journal
from benchside.domain.shared.service import Service

logger = logging.getLogger(__name__)


class ExportService(Service):
    observations: ObservationReader
    consent: ConsentService
    redactor: Redactor
    sink: ExportSink
    ledger: ConsentRepository
    journal: Journal

    def preview(self) -> ExportPreview:
        """Render exactly what an export would send.

        Safe without a grant: it exists so the scientist can see what sharing
        would mean before deciding. Nothing leaves the machine here. With no
        grant, every observation is listed as withheld.
        """
        grant = self.consent.active_grant()
        unshared = self.observations.list_unshared()
        covered = [o for o in unshared if grant is not None and grant.covers(o.gap)]
        withheld = [o.id for o in unshared if o not in covered]

        payload = self._payload(covered)
        findings = self.redactor.scan(payload)
        return ExportPreview(
            payload=self.redactor.apply(payload),
            observation_ids=tuple(o.id for o in covered),
            withheld=tuple(withheld),
            redaction_findings=tuple(f"{f.tier}:{f.category} in {f.field}" for f in findings),
        )

    def export(self) -> ExportRecord:
        grant = self.consent.active_grant()
        if grant is None:
            raise ConsentRequiredError("No active consent grant; nothing was shared")

        covered = [o for o in self.observations.list_unshared() if grant.covers(o.gap)]
        payload = self.redactor.apply(self._payload(covered))
        digest = self._digest(payload)

        # Send before recording: a failed send must not leave a record claiming
        # the data left. A duplicate send on retry is the safer failure.
        self.sink.send(payload)

        observation_ids = tuple(o.id for o in covered)
        self.journal.append(
            CONSENT_LEDGER_PROJECT,
            ObservationsExported(
                id=f"export:{digest[:12]}",
                grant_id=GrantId(grant.id),
                observation_ids=observation_ids,
                payload_sha256=digest,
            ),
        )
        logger.info("Exported %d observations under grant %s", len(covered), grant.id)
        return ExportRecord(
            grant_id=grant.id,
            observation_ids=observation_ids,
            payload_sha256=digest,
            exported_at=self.ledger.load().grants[-1].granted_at,
        )

    @staticmethod
    def _payload(observations: list[Observation]) -> str:
        """The wire format: one JSON object, gap shapes only.

        Project ids are deliberately omitted -- the nonprofit needs the shape
        of a breakdown, never which piece of work produced it.
        """
        return json.dumps(
            {
                "schema": "benchside.gaps.v1",
                "observations": [
                    {"id": o.id, "gap": o.gap.model_dump(mode="json")} for o in observations
                ],
            },
            indent=2,
            ensure_ascii=False,
        )

    @staticmethod
    def _digest(payload: str) -> str:
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
