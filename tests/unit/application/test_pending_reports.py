"""A later chat must resume exact reports without changing or sending them."""

import json

import pytest

from benchside.application.app import App
from benchside.application.native import _has_item_offers
from benchside.application.sharing import SharingFlow
from benchside.domain.shared.error import BenchsideError, InfrastructureError
from tests.unit.application.test_native import Notebook
from tests.unit.application.test_sharing import Collector
from tests.unit.application.test_workflow_notebook import problem, setup


def files(paths):
    return {str(p.relative_to(paths.home)): p.read_bytes()
            for p in paths.home.rglob("*") if p.is_file() and p.name != ".transaction.lock"}


def test_fresh_native_chat_lists_exact_pending_report_without_save(monkeypatch):
    monkeypatch.setenv("BENCHSIDE_FEEDBACK_ENDPOINT", "")
    book = Notebook()
    book.run({"action": "sharing.consent", "channel": "feedback", "enabled": True})
    feedback = book.run({"action": "sharing.feedback", "feedback": {
        "ease": 4, "would_use_again": "yes", "comment": "Synthetic feedback",
    }})["result"]
    draft = book.run({"action": "sharing.preview", "channel": "feedback",
                      "feedback_id": feedback["id"]})["result"][0]
    before = book.document
    fresh = Notebook()
    fresh.document, fresh.workspace_id = before, book.workspace_id
    listed = fresh.run({"action": "sharing.drafts"})
    assert listed["ok"] and not listed["changed"]
    assert fresh.document == before
    assert listed["result"][0]["id"] == draft["id"]
    assert listed["result"][0]["preview"] == draft["preview"]


def test_lost_receipt_restores_same_bytes_and_read_does_not_send(paths):
    class Uncertain(Collector):
        def send(self, payload):
            if not self.sent:
                self.sent.append(payload)
                raise InfrastructureError("Synthetic lost receipt", code="submission_unavailable")
            return super().send(payload)

    collector = Uncertain("feedback")
    flow = SharingFlow(paths, sinks={"feedback": collector})
    flow.set_consent("feedback", True)
    feedback = flow.feedback(ease=4, would_use_again="yes", comment="Synthetic")
    draft = flow.prepare("feedback", feedback_id=feedback.id)[0]
    with pytest.raises(InfrastructureError):
        flow.send(draft.id, draft.preview.payload_sha256)
    before = files(paths)
    fresh = SharingFlow(paths, sinks={"feedback": collector})
    pending = fresh.drafts()[0]
    assert pending["sendable"] and pending["problems"] == []
    assert pending["preview"] == draft.preview.model_dump(mode="json")
    assert files(paths) == before and collector.sent == [draft.preview.payload]
    with pytest.raises(BenchsideError):
        fresh.send(pending["id"], "0" * 64)
    fresh.send(pending["id"], pending["preview"]["payload_sha256"])
    assert collector.sent == [draft.preview.payload] * 2
    assert fresh.drafts() == []


@pytest.mark.parametrize("change", ["revoke", "policy", "destination", "digest", "sensitive", "usage_profile"])
def test_draft_readiness_and_send_share_validation_without_writes(paths, change):
    channel = "usage" if change == "usage_profile" else "feedback"
    collector = Collector(channel)
    flow = SharingFlow(paths, sinks={channel: collector})
    flow.set_consent(channel, True)
    if channel == "feedback":
        feedback = flow.feedback(ease=4, would_use_again="yes", comment="Synthetic")
        draft = flow.prepare(channel, feedback_id=feedback.id)[0]
    else:
        draft = flow.prepare(channel)[0]
    if change == "revoke":
        flow.set_consent(channel, False)
    elif change == "policy":
        flow._accept_policy(channel, None)
    elif change == "destination":
        collector.destination += "-changed"
    elif change in {"digest", "sensitive"}:
        data = draft.model_dump(mode="json")
        data["preview"]["payload"] = draft.preview.payload.replace("Synthetic", "person@example.org")
        if change == "sensitive":
            from benchside.domain.export.service.export import ExportService
            data["preview"]["payload_sha256"] = ExportService._digest(data["preview"]["payload"])
        flow._draft_path(draft.id).write_text(json.dumps(data))
    else:
        flow.set_profile({}, False)
    before = files(paths)
    pending = flow.drafts()[0]
    assert not pending["sendable"] and pending["problems"]
    assert files(paths) == before and not collector.sent
    with pytest.raises(BenchsideError):
        flow.send(draft.id, pending["preview"]["payload_sha256"])
    assert not collector.sent


def test_new_offer_cannot_silently_replace_pending_gap_report(paths):
    app = App(paths)
    ctx = setup(app)
    first = app.run({"action": "notebook.gap", **ctx, "gap": problem()})["recorded"]
    flow = SharingFlow(paths, sinks={"gaps": Collector("gaps")})
    flow.set_consent("gaps", True, scope="all_workflow")
    flow.check_in(**ctx)
    draft = flow.prepare("gaps", only=[first])[0]
    ctx = setup(app)
    new = app.run({"action": "notebook.gap", **ctx, "gap": problem()})["recorded"]
    offer = flow.check_in(**ctx)
    assert offer["observation_ids"] == [new]
    before = files(paths)
    with pytest.raises(BenchsideError, match="pending"):
        flow.prepare("gaps", only=offer["observation_ids"])
    assert files(paths) == before
    assert flow.drafts()[0]["id"] == draft.id
    with pytest.raises(BenchsideError):
        flow.prepare("gaps", only=[new], replace_draft_ids=["0" * 32])
    combined = flow.prepare("gaps", only=[first, new], replace_draft_ids=[draft.id])[0]
    assert set(combined.preview.observation_ids) == {first, new}
    assert [d["id"] for d in flow.drafts()] == [combined.id]
    assert not flow.sinks["gaps"].sent


def test_scoped_preview_does_not_expose_other_projects_withheld_ids(paths):
    app = App(paths)
    a, b = setup(app), setup(app, "different")
    selected = app.run({"action": "notebook.gap", **a, "gap": problem()})["recorded"]
    other = app.run({"action": "notebook.gap", **b, "gap": problem()})["recorded"]
    flow = SharingFlow(paths)
    flow.set_consent("gaps", True, scope="all_workflow")
    draft = flow.prepare("gaps", only=[selected])[0]
    assert other not in json.dumps(draft.model_dump(mode="json"))


def test_notebook_decision_can_omit_reason_without_inventing_one():
    book = Notebook()
    ctx = {k: v for k, v in book.setup().items() if k in {"project_id", "session_id"}}
    result = book.run({"action": "notebook.decide", **ctx, "decision": "Check the booking."})
    assert result["ok"]
    recalled = book.run({"action": "recall", **ctx})
    assert recalled["result"]["recent_decisions"][0]["rationale"] == ""
    assert "Rationale not stated" in recalled["project_journal"]["markdown"]


def test_item_offer_schema_detection_in_jsonl_and_nested_payloads():
    lines = json.dumps({"unrelated": True}) + "\n" + json.dumps({
        "sharing_offer": {"observation_ids": ["synthetic-observation"]},
    }) + "\n"
    assert _has_item_offers({"files": {"test.jsonl": lines}})
