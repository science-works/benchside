import hashlib
import json
from datetime import UTC, datetime

import pytest

from benchside.application.native import run_native, unpack
from benchside.application.sharing import SharingFlow
from benchside.domain.consultation.event import ConsultationOpened
from benchside.domain.export.model.value import DeliveryReceipt
from benchside.domain.export.service.reporting import ReportingService
from benchside.domain.shared.error import BenchsideError
from benchside.domain.shared.model.ids import PersonaId, ProjectId
from benchside.infrastructure.journal.store import JsonlJournal


class Collector:
    destination = "https://collector.example/v1/feedback"

    def __init__(self):
        self.sent = []

    def send(self, payload):
        self.sent.append(payload)
        return DeliveryReceipt(
            status="stored", sha256=hashlib.sha256(payload.encode()).hexdigest(),
            received_at="2026-10-27T12:00:00Z", observations=1,
        )


def test_replacement_previews_preserve_other_channels_records_and_receipts(paths):
    collector = Collector()
    flow = SharingFlow(paths, sinks={"feedback": collector, "usage": collector})
    flow.set_consent("feedback", True)
    flow.set_consent("usage", True)
    usage = flow.prepare("usage")[0]
    feedback = flow.feedback(ease=4, would_use_again="yes", comment="Original synthetic feedback")
    first = flow.prepare("feedback", feedback_id=feedback.id)[0]
    flow.send(first.id, first.preview.payload_sha256)
    editable = flow.feedback(ease=3, would_use_again="yes", comment="Second synthetic feedback")
    for number in range(20):
        current = flow.prepare("feedback", feedback_id=editable.id, comment=f"Edit {number}")[0]
        identical = flow.prepare("feedback", feedback_id=editable.id, comment=f"Edit {number}")[0]
        assert current.id == identical.id
    assert len(list((paths.home / "sharing/drafts").glob("*.json"))) == 2
    assert flow.load(usage.id) == usage
    assert len(flow.history()) == 1
    assert "Original synthetic feedback" in flow.reporting.feedback_payload(feedback.id, "0.1.2")
    with pytest.raises(BenchsideError, match="superseded"):
        flow.send(first.id, first.preview.payload_sha256)
    assert collector.sent == [first.preview.payload]
    flow.send(current.id, current.preview.payload_sha256)
    flow.send(current.id, current.preview.payload_sha256)
    assert collector.sent == [first.preview.payload, current.preview.payload]
    assert len(flow.history()) == 2


def test_native_preview_edits_do_not_retain_superseded_payloads(monkeypatch):
    monkeypatch.setenv("BENCHSIDE_FEEDBACK_ENDPOINT", "")
    document = run_native({"action": "native.create"})["markdown"]

    def run(command):
        nonlocal document
        result = run_native({
            "action": "native.run", "document": document,
            "workspace_id": unpack(document)[0]["workspace_id"], "request": command,
        })
        assert result["ok"]
        document = result["markdown"]
        return result["result"]

    run({"action": "sharing.consent", "channel": "feedback", "enabled": True})
    feedback = run({"action": "sharing.feedback", "feedback": {
        "ease": 4, "would_use_again": "yes", "comment": "Synthetic feedback",
    }})
    for number in range(12):
        current = run({"action": "sharing.preview", "channel": "feedback",
                       "feedback_id": feedback["id"], "comment": f"Synthetic edit {number}"})[0]
    drafts = {name: text for name, text in unpack(document)[1]["files"].items()
              if name.startswith("sharing/drafts/")}
    assert set(drafts) == {f"sharing/drafts/{current['id']}.json"}
    assert json.loads(next(iter(drafts.values())))["preview"]["payload"] == current["preview"]["payload"]


def test_duplicate_open_in_later_week_does_not_create_an_empty_usage_row(paths):
    journal = JsonlJournal(paths)
    project = ProjectId("synthetic-private-project")
    for identifier, recorded_at in [
        ("first", datetime(2026, 10, 12, tzinfo=UTC)),
        ("duplicate", datetime(2026, 10, 20, tzinfo=UTC)),
    ]:
        journal.append(project, ConsultationOpened(
            id=identifier, recorded_at=recorded_at, project_id=project,
            consultation_id="same-sitting", persona_id=PersonaId("pi"),
            host="chatgpt", surface="web",
        ))
    payload = ReportingService(journal=journal).usage_payload(
        installation_id="a" * 32, report_id="b" * 32, week="2026-10-19",
        revision=1, version="0.1.2",
    )
    assert payload.sessions == []
