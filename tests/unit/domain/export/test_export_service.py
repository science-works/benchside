"""Regression tests for ExportService (bugs B1, B2, B7)."""

from datetime import UTC, datetime, timedelta

import pytest

from benchside.domain.export.model.value import Observation
from benchside.domain.export.port.redactor import Finding
from benchside.domain.export.service.consent import ConsentService
from benchside.domain.export.service.export import ExportService
from benchside.domain.shared.model.gap import MissingIndex
from benchside.domain.shared.model.ids import GrantId, ObservationId, ProjectId
from benchside.infrastructure.journal.projection import (
    JournalConsentRepository,
    JournalObservationReader,
)


class RecordingSink:
    def __init__(self) -> None:
        self.sent: list[str] = []

    def send(self, payload: str) -> None:
        self.sent.append(payload)


class MarkingRedactor:
    """apply() visibly changes the payload; scan() reports per-payload."""

    def scan(self, payload: str) -> list[Finding]:
        if "SECRET" in payload:
            return [Finding(tier="HIGH", category="secret", field="gap")]
        return []

    def apply(self, payload: str) -> str:
        return payload.replace("SECRET", "[REDACTED]")


@pytest.fixture
def export_service(journal):
    ledger = JournalConsentRepository(journal)
    consent = ConsentService(repository=ledger, journal=journal)
    return ExportService(
        observations=JournalObservationReader(journal),
        consent=consent,
        redactor=MarkingRedactor(),
        sink=RecordingSink(),
        ledger=ledger,
        journal=journal,
    ), consent


def observe(journal, obs_id: str, question: str) -> None:
    """Plant a GapObserved event directly in a project journal."""
    from benchside.domain.consultation.event.gap_observed import GapObserved

    journal.append(
        ProjectId("proj-a"),
        GapObserved(
            id=f"e-{obs_id}",
            project_id=ProjectId("proj-a"),
            consultation_id="c-1",
            observation_id=ObservationId(obs_id),
            gap=MissingIndex(question=question),
        ),
    )


def grant_in_the_past(journal, hours: float) -> None:
    """Plant a ConsentGranted event whose timestamp is `hours` ago."""
    from benchside.domain.export.event.consent_granted import ConsentGranted
    from benchside.domain.export.service.consent import CONSENT_LEDGER_PROJECT

    journal.append(
        CONSENT_LEDGER_PROJECT,
        ConsentGranted(
            id="e-grant",
            grant_id=GrantId("g1"),
            gap_kinds=frozenset({"missing_index"}),
            recorded_at=datetime.now(UTC) - timedelta(hours=hours),
        ),
    )


class TestB1ExportedAt:
    def test_exported_at_is_export_time_not_grant_time(self, export_service, journal):
        service, consent = export_service
        grant_in_the_past(journal, hours=1)
        observe(journal, "o1", "any index?")

        before = datetime.now(UTC)
        record = service.export()
        after = datetime.now(UTC)

        assert before - timedelta(seconds=5) <= record.exported_at <= after, (
            f"exported_at={record.exported_at} is the grant time, not the export time"
        )


class TestB2EmptyExport:
    def test_export_with_nothing_covered_does_not_touch_sink(self, export_service):
        service, consent = export_service
        consent.grant(grant_id=GrantId("g1"), gap_kinds=frozenset({"missing_index"}))
        # No observations at all.
        record = service.export()
        assert record.observation_ids == ()
        assert service.sink.sent == [], "empty export must not send anything"


class TestB7PreviewScansSentBytes:
    def test_preview_findings_describe_the_payload_shown(self, export_service, journal):
        service, consent = export_service
        consent.grant(grant_id=GrantId("g1"), gap_kinds=frozenset({"missing_index"}))
        observe(journal, "o1", "where is the SECRET assay index?")

        preview = service.preview()
        # The shown payload is post-redaction...
        assert "SECRET" not in preview.payload
        # ...so findings must describe those bytes: the redactor already
        # cleaned them, hence nothing left to report on the sent bytes.
        assert preview.redaction_findings == (), (
            "findings describe pre-redaction bytes, not what is shown/sent"
        )
