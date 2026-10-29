import hashlib
import json
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from benchside.application.app import App
from benchside.application.metascience import Metascience
from benchside.application.native import run_native
from benchside.application.sharing import SharingFlow
from benchside.domain.export.event.reporting import UsageFailureRecorded
from benchside.domain.export.model.metascience import StudyCatalog
from benchside.domain.export.model.value import DeliveryReceipt
from benchside.domain.export.service.reporting import REPORTING_PROJECT, ReportingService
from benchside.domain.shared.error import BenchsideError, InfrastructureError


class Collector:
    def __init__(self, channel):
        self.destination = f"https://synthetic.invalid/v1/{channel}"
        self.sent = []
        self.error = None
        self.missing_receipt = False

    def send(self, payload):
        self.sent.append(payload)
        if self.error:
            raise self.error
        if self.missing_receipt:
            return None
        return DeliveryReceipt(
            status="stored",
            sha256=hashlib.sha256(payload.encode()).hexdigest(),
            received_at=datetime.now(UTC).isoformat(),
            observations=len(json.loads(payload).get("observations", [None])),
        )


def prepare(paths, channel, *, usage_enabled=True):
    sinks = {c: Collector(c) for c in ("gaps", "feedback", "usage", "surveys", "activity")}
    sharing = SharingFlow(paths, sinks=sinks)
    sharing.set_consent("usage", usage_enabled)
    if channel in {"surveys", "activity"}:
        flow = Metascience(paths, sinks=sinks, today=date(2026, 10, 22))
        if channel == "surveys":

            class Catalog:
                def fetch(self):
                    fixture = Path(__file__).parents[2] / "fixtures/metascience/catalog.json"
                    return StudyCatalog.model_validate_json(fixture.read_text())

            flow.catalog = Catalog()
            flow.consent("invitations", True)
            study = flow.invitations()["invitation"]
            question = study["questions"][0]
            draft = flow.survey(
                f"{study['id']}@{study['version']}",
                {question["id"]: question["options"][0]["id"]},
            )
        else:
            flow.consent("analysis", True)
            flow.consent("sharing", True)
            scope = {"host": "claude", "source_id": "synthetic-source"}
            flow.scopes([scope])
            sample = flow.sample([{"scope": scope, "session_ref": "synthetic-session"}])
            token = next(iter(sample["selected"]))
            flow.record(
                sample["week"],
                token,
                {
                    "benchside_role": "none",
                    "activity": {"value": "unknown", "basis": "unknown"},
                    "obstacle": {"value": "unknown", "basis": "unknown"},
                    "verification": {"value": "unknown", "basis": "unknown"},
                    "outcome": {"value": "not_reported", "basis": "unknown"},
                },
            )
            draft = flow.preview_activity(sample["week"])
        return sharing, flow, sinks[channel], draft["id"], draft["sha256"]
    flow = sharing
    if channel == "gaps":
        app = App(paths)
        setup = app.run({"action": "setup", "project_key": "synthetic-project"})
        context = {k: setup[k] for k in ("project_id", "session_id")}
        sitting = app.run({"action": "start", **context, "role": "methods-clinic"})
        app.run(
            {
                "action": "gap",
                **context,
                "sitting_id": sitting["sitting"]["id"],
                "gap": {"kind": "missing_index", "question": "Synthetic workflow need"},
            }
        )
        flow.set_consent("gaps", True, kinds=["missing_index"])
        draft = flow.prepare("gaps")[0]
    elif channel == "feedback":
        flow.set_consent("feedback", True)
        feedback = flow.feedback(ease=4, would_use_again="yes", comment="Synthetic feedback")
        draft = flow.prepare("feedback", feedback_id=feedback.id)[0]
    else:
        draft = flow.prepare("usage")[0]
    return sharing, flow, sinks[channel], draft.id, draft.preview.payload_sha256


def counts(sharing):
    return Counter(
        event.code
        for event in sharing.journal.read(REPORTING_PROJECT)
        if isinstance(event, UsageFailureRecorded)
    )


@pytest.mark.parametrize("channel", ["gaps", "feedback", "usage", "surveys", "activity"])
def test_invalid_approval_counts_once_without_sending(paths, channel):
    sharing, flow, sink, identifier, _ = prepare(paths, channel)
    with pytest.raises(BenchsideError):
        flow.send(identifier, "0" * 64)
    assert counts(sharing) == {"submission_invalid": 1}
    assert sink.sent == []


@pytest.mark.parametrize("channel", ["gaps", "feedback", "usage", "surveys", "activity"])
def test_network_failure_keeps_standard_code_and_original_exception(paths, channel):
    sharing, flow, sink, identifier, approval = prepare(paths, channel)
    sink.error = InfrastructureError("DO_NOT_REPORT_RAW_RESEARCH", code="submission_rate_limited")
    with pytest.raises(InfrastructureError) as caught:
        flow.send(identifier, approval)
    assert caught.value is sink.error
    assert counts(sharing) == {"submission_rate_limited": 1}
    assert len(sink.sent) == 1
    assert "DO_NOT_REPORT_RAW_RESEARCH" not in sharing.prepare("usage")[0].preview.payload


@pytest.mark.parametrize("channel", ["feedback", "surveys", "activity"])
def test_failure_counting_requires_separate_usage_consent(paths, channel):
    sharing, flow, sink, identifier, _ = prepare(paths, channel, usage_enabled=False)
    with pytest.raises(BenchsideError):
        flow.send(identifier, "0" * 64)
    assert counts(sharing) == {}
    assert sink.sent == []
    # Linked feedback/activity can create the contributor ID independently of usage.
    assert not sharing.reporting.active_grant("usage")
    assert not list((paths.home / "reporting").glob("usage-*.json"))


@pytest.mark.parametrize("channel", ["gaps", "feedback", "usage", "surveys", "activity"])
def test_withdrawal_is_not_a_submission_failure(paths, channel):
    sharing, flow, sink, identifier, approval = prepare(paths, channel)
    if channel in {"surveys", "activity"}:
        flow.consent("invitations" if channel == "surveys" else "sharing", False)
    else:
        flow.set_consent(channel, False)
    with pytest.raises(BenchsideError):
        flow.send(identifier, approval)
    assert counts(sharing) == {}
    assert sink.sent == []


def test_demographic_withdrawal_is_not_a_submission_failure(paths):
    sharing, flow, sink, identifier, approval = prepare(paths, "usage")
    flow.set_profile({}, False)
    with pytest.raises(BenchsideError):
        flow.send(identifier, approval)
    assert counts(sharing) == {}
    assert sink.sent == []


def test_dismissing_a_survey_is_not_a_submission_failure(paths):
    sharing, flow, sink, identifier, approval = prepare(paths, "surveys")
    flow.dismiss(next(iter(flow.state.studies)))
    with pytest.raises(BenchsideError):
        flow.send(identifier, approval)
    assert counts(sharing) == {}
    assert sink.sent == []


@pytest.mark.parametrize("channel", ["surveys", "activity"])
def test_missing_metascience_receipt_uses_receipt_failure_code(paths, channel):
    sharing, flow, sink, identifier, approval = prepare(paths, channel)
    sink.missing_receipt = True
    with pytest.raises(InfrastructureError):
        flow.send(identifier, approval)
    assert counts(sharing) == {"submission_receipt_invalid": 1}
    assert flow.state.receipts == {}


def test_counter_storage_failure_does_not_mask_send_failure(paths, monkeypatch):
    _, flow, sink, identifier, approval = prepare(paths, "surveys")
    sink.error = InfrastructureError("Original failure", code="submission_unavailable")

    def unavailable(*_args):
        raise OSError("Synthetic local counter failure")

    monkeypatch.setattr(ReportingService, "failure", unavailable)
    with pytest.raises(InfrastructureError) as caught:
        flow.send(identifier, approval)
    assert caught.value is sink.error


def test_native_notebook_restores_metascience_failure_count():
    snapshot = run_native({"action": "native.create"})["snapshot"]

    def run(request):
        nonlocal snapshot
        result = run_native(
            {
                "action": "native.run",
                "workspace_id": snapshot["workspace_id"],
                "document": snapshot,
                "request": request,
            }
        )
        snapshot = result["snapshot"]
        return result

    run({"action": "sharing.consent", "channel": "usage", "enabled": True})
    for choice in ("analysis", "sharing"):
        run({"action": "metascience.consent", "choice": choice, "enabled": True})
    scope = {"host": "claude", "source_id": "synthetic-source"}
    run({"action": "metascience.scopes", "scopes": [scope]})
    sample = run(
        {
            "action": "metascience.sample",
            "candidates": [{"scope": scope, "session_ref": "synthetic-session"}],
        }
    )["result"]
    run(
        {
            "action": "metascience.record",
            "week": sample["week"],
            "token": next(iter(sample["selected"])),
            "classification": {
                "benchside_role": "none",
                "activity": {"value": "unknown", "basis": "unknown"},
                "obstacle": {"value": "unknown", "basis": "unknown"},
                "verification": {"value": "unknown", "basis": "unknown"},
                "outcome": {"value": "not_reported", "basis": "unknown"},
            },
        }
    )
    draft = run({"action": "metascience.preview", "week": sample["week"]})["result"]
    rejected = run(
        {
            "action": "metascience.send",
            "draft_id": draft["id"],
            "approved_sha256": "0" * 64,
        }
    )
    assert not rejected["ok"] and rejected["changed"]
    usage = run({"action": "sharing.preview", "channel": "usage"})
    assert usage["ok"]
    errors = json.loads(usage["result"][0]["preview"]["payload"])["errors"]
    assert errors["submission_invalid"] == 1
    assert sum(errors.values()) == 1
