"""Consent and approval are checked against the exact frozen bytes at send time."""

import hashlib
import json
from dataclasses import field
from datetime import UTC, datetime

from benchside.domain.export.event.observations_exported import ObservationsExported
from benchside.domain.export.model.value import ExportPreview, ExportRecord
from benchside.domain.export.model.wire import (
    MAX_BYTES,
    MAX_OBSERVATIONS,
    validate_gap,
    validate_payload,
)
from benchside.domain.export.port.redactor import Redactor
from benchside.domain.export.port.repository import ConsentRepository, ObservationReader
from benchside.domain.export.port.sink import ExportSink
from benchside.domain.export.service.consent import CONSENT_LEDGER_PROJECT, ConsentService
from benchside.domain.shared.error import ConsentRequiredError, ValidationError
from benchside.domain.shared.event import new_event_id
from benchside.domain.shared.port.journal import Journal
from benchside.domain.shared.service import Service


class ExportService(Service):
    observations: ObservationReader
    consent: ConsentService
    redactor: Redactor
    sink: ExportSink
    ledger: ConsentRepository
    journal: Journal
    # Set by the sharing adapter only after the linked-sharing policy is accepted.
    # This is configuration, not a dependency for the legacy CLI composition root.
    contributor_id: str | None = field(default=None, init=False)

    def preview(self, *, only=None, edits=None) -> ExportPreview:
        previews = self.previews(only=only, edits=edits)
        if len(previews) > 1:
            raise ValidationError(
                "Several batches are needed; review each batch using share preview"
            )
        return previews[0]

    def previews(self, *, only=None, edits=None) -> tuple[ExportPreview, ...]:
        grant = self.consent.active_grant()
        unshared = self.observations.list_unshared()
        covered = [
            o
            for o in unshared
            if grant is not None and grant.covers(o.gap) and (only is None or o.id in only)
        ]
        if only is not None and set(only) - {o.id for o in covered}:
            raise ValidationError("Selection includes unknown, shared or unconsented observations")
        edits = edits or {}
        if set(edits) - {o.id for o in covered}:
            raise ValidationError("Edits must refer to selected observations")
        withheld = tuple(o.id for o in unshared if o not in covered)
        batches, batch = [], []
        for observation in covered:
            gap = edits.get(observation.id, observation.gap.model_dump(mode="json"))
            validate_gap(gap)
            if gap["kind"] != observation.gap.kind:
                raise ValidationError("An edit cannot change an observation's kind")
            item = {"id": observation.id, "gap": gap}
            if self.contributor_id:
                item.update(origin=observation.origin, basis=observation.basis)
            candidate = self.redactor.apply(self._payload(batch + [item]))
            if batch and (
                len(batch) == MAX_OBSERVATIONS or len(candidate.encode("utf-8")) > MAX_BYTES
            ):
                batches.append(batch)
                batch = []
            batch.append(item)
        batches.append(batch)
        result = []
        for items in batches:
            payload = self.redactor.apply(self._payload(items))
            if items:
                validate_payload(payload)
            result.append(
                ExportPreview(
                    payload=payload,
                    observation_ids=tuple(o["id"] for o in items),
                    withheld=withheld,
                    grant_id=grant.id if grant else None,
                    payload_sha256=self._digest(payload),
                    destination=self.sink.destination,
                    redaction_findings=tuple(
                        f"{f.tier}:{f.category} in {f.field}" for f in self.redactor.scan(payload)
                    ),
                )
            )
        return tuple(result)

    def export(
        self, *, preview: ExportPreview | None = None, approved_sha256: str | None = None
    ) -> ExportRecord:
        grant = self.consent.active_grant()
        if grant is None:
            raise ConsentRequiredError("No active consent grant; nothing was shared")
        if preview is None:
            if not any(grant.covers(o.gap) for o in self.observations.list_unshared()):
                return ExportRecord(
                    grant_id=grant.id,
                    observation_ids=(),
                    payload_sha256="",
                    exported_at=datetime.now(UTC),
                )
            raise ConsentRequiredError("An exact reviewed preview and its approval are required")
        if preview.grant_id != grant.id:
            raise ConsentRequiredError("The consent changed; review the export again")
        digest = self._digest(preview.payload)
        if digest != preview.payload_sha256 or digest != approved_sha256:
            raise ConsentRequiredError("The reviewed payload changed or has not been approved")
        if preview.destination != self.sink.destination:
            raise ConsentRequiredError("The destination changed; review the export again")
        for previous in self.ledger.load().exports:
            if previous.payload_sha256 == digest and previous.destination == preview.destination:
                return previous
        data = validate_payload(preview.payload)
        ids = tuple(o["id"] for o in data["observations"])
        if ids != preview.observation_ids:
            raise ValidationError("Preview identifiers do not match its payload")
        current = {o.id: o for o in self.observations.list_unshared()}
        for item in data["observations"]:
            original = current.get(item["id"])
            if (
                original is None
                or not grant.covers(original.gap)
                or original.gap.kind != item["gap"]["kind"]
            ):
                raise ConsentRequiredError("Observation selection changed; review the export again")
        if any(f.tier == "HIGH" for f in self.redactor.scan(preview.payload)):
            raise ValidationError("Sensitive content remains; edit and review before sending")
        receipt = self.sink.send(preview.payload)
        event = ObservationsExported(
            id=new_event_id(),
            grant_id=grant.id,
            observation_ids=ids,
            payload_sha256=digest,
            destination=preview.destination,
            received_at=receipt.received_at if receipt else None,
        )
        self.journal.append(CONSENT_LEDGER_PROJECT, event)
        return ExportRecord(
            grant_id=grant.id,
            observation_ids=ids,
            payload_sha256=digest,
            exported_at=event.recorded_at,
            destination=event.destination,
            received_at=event.received_at,
        )

    def _payload(self, observations: list[dict]) -> str:
        schema = "benchside.gaps.v2" if self.contributor_id else "benchside.gaps.v1"
        if any("context" in item["gap"] for item in observations):
            schema = "benchside.gaps.v3"
        return json.dumps(
            {
                "schema": schema,
                **({"contributor_id": self.contributor_id} if self.contributor_id else {}),
                "observations": observations,
            },
            ensure_ascii=False,
            indent=2,
        )

    @staticmethod
    def _digest(payload: str) -> str:
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
