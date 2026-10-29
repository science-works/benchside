import hashlib
import json
from datetime import UTC, datetime

import pytest

from benchside.application.sharing import SharingFlow
from benchside.domain.consultation.event import (
    ConsultationClosed,
    ConsultationOpened,
    HypothesisStated,
)
from benchside.domain.export.model.value import DeliveryReceipt
from benchside.domain.export.service.reporting import week_start
from benchside.domain.shared.error import BenchsideError
from benchside.domain.shared.model.ids import PersonaId, ProjectId


class Collector:
    def __init__(self, channel):
        self.destination = f"https://collector.example/v1/{channel}"
        self.sent = []

    def send(self, payload):
        self.sent.append(payload)
        parsed = json.loads(payload)
        return DeliveryReceipt(
            status="stored",
            sha256=hashlib.sha256(payload.encode()).hexdigest(),
            received_at=datetime.now(UTC).isoformat(),
            observations=len(parsed["observations"]) if "observations" in parsed else 1,
        )


@pytest.fixture
def flow(paths):
    return SharingFlow(paths, sinks={c: Collector(c) for c in ["gaps", "feedback", "usage"]})


def test_each_channel_is_independently_opted_in(flow):
    flow.set_consent("gaps", True, kinds=["missing_index"])
    assert flow.status()["gaps"]["enabled"]
    assert not flow.status()["feedback"]["enabled"]
    assert not flow.status()["usage"]["enabled"]
    with pytest.raises(BenchsideError):
        flow.prepare("usage")
    assert flow.status()["installation_id"] is None


def test_feedback_preview_edit_send_and_revoke(flow):
    feedback = flow.feedback(
        ease=3,
        would_use_again="yes",
        comment="Contact me at scientist@example.org",
    )
    flow.set_consent("feedback", True)
    draft = flow.prepare("feedback", feedback_id=feedback.id)[0]
    assert "scientist@example.org" not in draft.preview.payload
    assert "installation_id" not in draft.preview.payload
    assert "project" not in draft.preview.payload
    reviewed = flow.prepare("feedback", feedback_id=feedback.id, comment="Setup was confusing")[0]
    receipt = flow.send(reviewed.id, reviewed.preview.payload_sha256)
    assert receipt.channel == "feedback"
    assert flow.sinks["feedback"].sent == [reviewed.preview.payload]
    flow.send(reviewed.id, reviewed.preview.payload_sha256)
    assert len(flow.sinks["feedback"].sent) == 1
    flow.set_consent("feedback", False)
    with pytest.raises(BenchsideError):
        flow.send(draft.id, draft.preview.payload_sha256)


def test_usage_is_weekly_revisable_and_content_free(flow):
    pid = ProjectId("private-study")
    flow.journal.append(
        pid,
        ConsultationOpened(
            id="e1",
            consultation_id="c1",
            project_id=pid,
            persona_id=PersonaId("pi"),
            host="claude",
            surface="desktop",
        ),
    )
    flow.journal.append(
        pid,
        HypothesisStated(
            id="e2",
            consultation_id="c1",
            project_id=pid,
            hypothesis_id="h1",
            statement="Unpublished private result",
        ),
    )
    flow.set_consent("usage", True)
    first = flow.prepare("usage", week=week_start())[0]
    data = json.loads(first.preview.payload)
    assert data["sessions"][0]["started"] == 1
    assert data["sessions"][0]["records"]["hypothesis"] == 1
    assert data["sessions"][0]["abandoned"] == 0  # Closing a chat is not abandonment.
    assert "private" not in first.preview.payload.lower()
    assert '"c1"' not in first.preview.payload and '"h1"' not in first.preview.payload
    repeated = flow.prepare("usage")[0]
    assert repeated.preview.payload == first.preview.payload
    flow.journal.append(
        pid,
        ConsultationClosed(
            id="e3",
            consultation_id="c1",
            project_id=pid,
            state="converged",
            detail="Private next step",
        ),
    )
    later = flow.prepare("usage")[0]
    updated = json.loads(later.preview.payload)
    assert updated["report_id"] == data["report_id"]
    assert updated["installation_id"] == data["installation_id"]
    assert updated["revision"] == data["revision"] + 1
    assert updated["sessions"][0]["concluded"] == 1
    with pytest.raises(BenchsideError, match="newer"):
        flow.send(first.id, first.preview.payload_sha256)
    flow.send(later.id, later.preview.payload_sha256)
    assert flow.sinks["usage"].sent == [later.preview.payload]
    assert not flow.sinks["gaps"].sent and not flow.sinks["feedback"].sent


def test_draft_cannot_change_after_approval(flow):
    flow.set_consent("feedback", True)
    feedback = flow.feedback(ease=4, would_use_again="unsure", comment="Original")
    draft = flow.prepare("feedback", feedback_id=feedback.id)[0]
    path = flow._draft_path(draft.id)
    content = json.loads(path.read_text())
    content["preview"]["payload"] = content["preview"]["payload"].replace("Original", "Changed")
    path.write_text(json.dumps(content))
    with pytest.raises(BenchsideError):
        flow.send(draft.id, draft.preview.payload_sha256)
    assert not flow.sinks["feedback"].sent


def test_errors_only_record_controlled_codes_after_usage_opt_in(flow):
    flow.reporting.failure("submission_unavailable")
    flow.set_consent("usage", True)
    flow.reporting.failure("path=/Users/private-name")
    flow.reporting.failure("submission_unavailable")
    payload = json.loads(flow.prepare("usage")[0].preview.payload)
    assert sum(payload["errors"].values()) == 1
    assert payload["errors"]["submission_unavailable"] == 1


def test_failed_send_keeps_draft_and_retries_identical_bytes(flow):
    from benchside.domain.shared.error import InfrastructureError

    class IntermittentCollector(Collector):
        def send(self, payload):
            if not self.sent:
                self.sent.append(payload)
                raise InfrastructureError("Unreachable", code="submission_unavailable")
            return super().send(payload)

    flow.sinks["feedback"] = IntermittentCollector("feedback")
    flow.set_consent("feedback", True)
    flow.set_consent("usage", True)
    feedback = flow.feedback(ease=3, would_use_again="yes", comment="Useful")
    draft = flow.prepare("feedback", feedback_id=feedback.id)[0]
    with pytest.raises(InfrastructureError):
        flow.send(draft.id, draft.preview.payload_sha256)
    assert flow.history() == []
    assert flow.load(draft.id) == draft
    flow.send(draft.id, draft.preview.payload_sha256)
    assert flow.sinks["feedback"].sent == [draft.preview.payload] * 2
    assert len(flow.history()) == 1
    assert (
        json.loads(flow.prepare("usage")[0].preview.payload)["errors"]["submission_unavailable"]
        == 1
    )


def test_usage_keeps_first_open_metadata_and_deduplicates_failure_events(flow):
    from benchside.domain.export.event.reporting import UsageFailureRecorded
    from benchside.domain.export.service.reporting import REPORTING_PROJECT

    pid = ProjectId("deduplicate")
    first = ConsultationOpened(
        id="open-first",
        consultation_id="c1",
        project_id=pid,
        persona_id=PersonaId("pi"),
        app_version="1.2.3",
    )
    flow.journal.append(pid, first)
    flow.journal.append(pid, first.model_copy(update={"id": "open-again", "app_version": "2.0.0"}))
    failure = UsageFailureRecorded(id="failure", code="recording_invalid")
    flow.journal.append(REPORTING_PROJECT, failure)
    flow.journal.append(REPORTING_PROJECT, failure)
    flow.set_consent("usage", True)
    payload = json.loads(flow.prepare("usage")[0].preview.payload)
    assert len(payload["sessions"]) == 1
    assert payload["sessions"][0]["started"] == 1
    assert payload["sessions"][0]["app_version"] == "1.2.3"
    assert payload["errors"]["recording_invalid"] == 1


def test_demographics_are_optional_reviewed_and_revocable(flow):
    categories = {"discipline": "life_sciences", "career_stage": "doctoral_researcher"}
    assert not flow.profile().include_in_usage
    flow.set_profile(categories, False)
    flow.set_consent("usage", True)
    assert "demographics" not in json.loads(flow.prepare("usage")[0].preview.payload)
    flow.set_profile(categories, True)
    draft = flow.prepare("usage")[0]
    assert json.loads(draft.preview.payload)["demographics"] == categories
    flow.set_profile(categories, False)
    with pytest.raises(BenchsideError, match="preferences changed"):
        flow.send(draft.id, draft.preview.payload_sha256)
    assert flow.sinks["usage"].sent == []
    refreshed = flow.prepare("usage")[0]
    assert "demographics" not in json.loads(refreshed.preview.payload)
    flow.send(refreshed.id, refreshed.preview.payload_sha256)
    flow.set_profile(categories, True)
    flow.set_consent("feedback", True)
    feedback = flow.feedback(ease=4, would_use_again="yes", comment="Synthetic feedback")
    assert (
        "demographics" not in flow.prepare("feedback", feedback_id=feedback.id)[0].preview.payload
    )


def test_demographic_labels_do_not_accept_free_text_or_implicit_consent(flow):
    from pydantic import ValidationError

    for profile in [
        {"discipline": "My private dataset"},
        {"career_stage": "Named institute"},
        {"email": "a@example.org"},
    ]:
        with pytest.raises(ValidationError):
            flow.set_profile(profile, True)
    with pytest.raises(ValidationError):
        flow.set_profile({"discipline": "life_sciences"}, "yes")
    assert flow.profile().revision == 0
    flow.set_profile({"career_stage": "prefer_not_to_say"}, True)
    with pytest.raises(BenchsideError, match="off"):
        flow.prepare("usage")  # Profile choice alone never enables usage reporting.
