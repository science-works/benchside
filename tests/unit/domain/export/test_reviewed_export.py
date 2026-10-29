import json

import pytest

from benchside.domain.shared.error import BenchsideError
from tests.unit.domain.export.test_export_service import export_service, observe  # noqa: F401


def consent_and_observe(service, consent, journal):
    consent.grant(grant_id="g1", gap_kinds=frozenset({"missing_index"}))
    observe(journal, "o1", "Find reusable protocols")
    return service.preview()


def test_send_requires_the_reviewed_digest(export_service, journal):
    service, consent = export_service
    consent_and_observe(service, consent, journal)
    with pytest.raises(BenchsideError, match="review"):
        service.export()
    assert not service.sink.sent


def test_send_uses_reviewed_bytes_not_new_observations(export_service, journal):
    service, consent = export_service
    preview = consent_and_observe(service, consent, journal)
    observe(journal, "o2", "New private observation")
    service.export(preview=preview, approved_sha256=preview.payload_sha256)
    assert service.sink.sent == [preview.payload]
    assert "New private observation" not in service.sink.sent[0]
    assert service.observations.list_unshared()[0].id == "o2"


def test_changed_preview_cannot_use_old_approval(export_service, journal):
    service, consent = export_service
    preview = consent_and_observe(service, consent, journal)
    tampered = preview.model_copy(
        update={"payload": preview.payload.replace("protocols", "assays")}
    )
    with pytest.raises(BenchsideError):
        service.export(preview=tampered, approved_sha256=preview.payload_sha256)
    assert not service.sink.sent


def test_regrant_invalidates_old_review(export_service, journal):
    service, consent = export_service
    preview = consent_and_observe(service, consent, journal)
    consent.revoke()
    consent.grant(grant_id="g2", gap_kinds=frozenset({"missing_index"}))
    with pytest.raises(BenchsideError, match="consent"):
        service.export(preview=preview, approved_sha256=preview.payload_sha256)
    assert not service.sink.sent


def test_successful_retry_does_not_send_again(export_service, journal):
    service, consent = export_service
    preview = consent_and_observe(service, consent, journal)
    first = service.export(preview=preview, approved_sha256=preview.payload_sha256)
    second = service.export(preview=preview, approved_sha256=preview.payload_sha256)
    assert first == second
    assert len(service.sink.sent) == 1


def test_review_can_edit_or_exclude_observations(export_service, journal):
    service, consent = export_service
    consent_and_observe(service, consent, journal)
    observe(journal, "o2", "Exclude this")
    preview = service.preview(
        only=["o1"],
        edits={"o1": {"kind": "missing_index", "question": "Reviewed wording"}},
    )
    assert json.loads(preview.payload)["observations"] == [
        {"id": "o1", "gap": {"kind": "missing_index", "question": "Reviewed wording"}},
    ]
    assert service.observations.list_all()[0].gap.question == "Find reusable protocols"


def test_batches_respect_collector_limit(export_service, journal):
    service, consent = export_service
    consent.grant(grant_id="g1", gap_kinds=frozenset({"missing_index"}))
    for index in range(300):
        observe(journal, f"o{index}", "🧬" * 900)  # UTF-8 byte limit is reached before item limit.
    previews = service.previews()
    assert len(previews) > 1
    assert sum(len(p.observation_ids) for p in previews) == 300
    assert all(len(p.payload.encode("utf-8")) <= 512 * 1024 for p in previews)
