import hashlib
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from benchside.application.metascience import Metascience
from benchside.domain.export.model.metascience import MetaState, StudyCatalog
from benchside.domain.export.model.value import DeliveryReceipt
from benchside.domain.shared.error import BenchsideError

TODAY = date(2026, 10, 27)
SCOPES = [
    {"host": "claude", "source_id": "private-source-A"},
    {"host": "claude", "source_id": "private-source-B"},
]
CANDIDATES = [
    {"scope": scope, "session_ref": f"private-conversation-{index}"}
    for index, scope in enumerate(SCOPES)
]


class Sink:
    def __init__(self, channel):
        self.destination = f"https://synthetic.invalid/v1/{channel}"
        self.sent = []

    def send(self, payload):
        self.sent.append(payload)
        return DeliveryReceipt(
            status="stored",
            sha256=hashlib.sha256(payload.encode()).hexdigest(),
            received_at=datetime.now(UTC).isoformat(),
            observations=len(json.loads(payload).get("observations", [None])),
        )


class Catalog:
    def fetch(self):
        path = Path(__file__).parents[2] / "fixtures/metascience/catalog.json"
        return StudyCatalog.model_validate_json(path.read_text())


def classification(activity="coding"):
    return {
        "benchside_role": "none",
        "activity": {"value": activity, "basis": "model_inferred"},
        "obstacle": {"value": "unknown", "basis": "unknown"},
        "verification": {"value": "unknown", "basis": "unknown"},
        "outcome": {"value": "not_reported", "basis": "unknown"},
    }


def sampled_flow(paths):
    flow = Metascience(
        paths,
        today=TODAY,
        catalog=Catalog(),
        sinks={channel: Sink(channel) for channel in ("surveys", "activity")},
    )
    flow.consent("analysis", True)
    flow.consent("sharing", True)
    flow.scopes(SCOPES)
    batch = flow.sample(CANDIDATES)
    token = next(iter(batch["selected"]))
    flow.record(batch["week"], token, classification())
    return flow, batch, token


def test_narrowing_scopes_retires_week_with_one_clear_recovery(paths):
    flow, batch, _ = sampled_flow(paths)
    first = flow.preview_activity(batch["week"])
    removed = next(iter(batch["selected"].values()))["scope"]
    remaining = [scope for scope in SCOPES if scope != removed]
    current_candidates = [c for c in CANDIDATES if c["scope"] in remaining]
    status = flow.scopes(remaining)
    assert status["weeks"] == []
    assert status["retired_weeks"] == [batch["week"]]
    for call in (
        lambda: flow.sample(current_candidates),
        lambda: flow.batch(batch["week"]),
        lambda: flow.preview_activity(batch["week"]),
    ):
        with pytest.raises(BenchsideError, match="was retired.*2026-11-02"):
            call()
    with pytest.raises(BenchsideError):
        flow.send(first["id"], first["sha256"])
    assert not flow.sinks["activity"].sent
    assert first["id"] not in flow.state.drafts
    assert flow.state.samples[batch["week"]].selected == {}
    assert flow.state.samples[batch["week"]].records == {}
    assert removed["source_id"] not in flow.path.read_text()
    # Re-adding a removed scope does not restore the old sample or create a redraw.
    flow.scopes(SCOPES)
    with pytest.raises(BenchsideError, match="was retired"):
        flow.sample(CANDIDATES)
    flow.today += timedelta(days=7)
    next_batch = flow.sample(CANDIDATES)
    assert next_batch["eligible"] == 0  # Both prior candidates were selected under the cap of 20.
    assert next_batch["week"] == "2026-10-26"
    assert next_batch["id"] != batch["id"]


def test_analysis_withdrawal_erases_private_selections_but_keeps_receipt_evidence(paths):
    flow, batch, token = sampled_flow(paths)
    submitted = flow.preview_activity(batch["week"])
    receipt = flow.send(submitted["id"], submitted["sha256"])
    flow.record(batch["week"], token, classification("writing"))
    unsubmitted = flow.preview_activity(batch["week"])
    flow.consent("invitations", True)
    study = flow.invitations()["invitation"]
    survey = flow.survey(f"{study['id']}@{study['version']}", {"checked": "yes"})
    seen = list(flow.state.seen)
    before = flow.path.read_text()
    assert "private-source-" in before and "private-conversation-" in before

    status = flow.consent("analysis", False)
    saved = flow.path.read_text()
    assert "private-source-" not in saved and "private-conversation-" not in saved
    assert "writing" not in saved
    assert status["scopes"] == [] and status["weeks"] == []
    assert status["retired_weeks"] == [batch["week"]]
    assert flow.state.seen == seen  # Private anti-resampling hashes; no source references.
    assert flow.state.samples[batch["week"]].selected == {}
    assert flow.state.samples[batch["week"]].records == {}
    assert flow.state.drafts[submitted["id"]].payload == submitted["payload"]
    assert unsubmitted["id"] not in flow.state.drafts
    assert not any(key.startswith("activity:") for key in flow.state.latest)
    assert survey["id"] in flow.state.latest.values()
    assert flow.dispatch({"action": "metascience.history"}) == [receipt]
    MetaState.model_validate_json(saved)
    flow.send(survey["id"], survey["sha256"])  # Independent survey consent still works.


def fill_obsolete_drafts(flow, draft, count=1000):
    source = flow.state.drafts[draft["id"]]
    drafts = {f"{i:032x}": source.model_copy(update={"id": f"{i:032x}"}) for i in range(count)}
    flow._save(drafts=drafts, latest={source.key: f"{count - 1:032x}"})


def test_valid_draft_ceiling_does_not_prevent_consent_withdrawal(paths):
    flow, batch, _ = sampled_flow(paths)
    draft = flow.preview_activity(batch["week"])
    fill_obsolete_drafts(flow, draft)
    assert len(flow.state.drafts) == 1000
    # The review's claimed >1000 validation failure does not occur at the valid cap.
    flow.consent("sharing", False)
    assert "sharing" not in flow.state.grants
    assert len(flow.state.drafts) == 1000
    flow.consent("analysis", False)
    assert flow.state.drafts == {}
    assert flow.state.latest == {}


@pytest.mark.parametrize("edited", [False, True])
def test_preview_prunes_obsolete_receipt_free_drafts_at_capacity(paths, edited):
    flow, batch, token = sampled_flow(paths)
    draft = flow.preview_activity(batch["week"])
    fill_obsolete_drafts(flow, draft)
    if edited:
        flow.record(batch["week"], token, classification("writing"))
    refreshed = flow.preview_activity(batch["week"])
    assert set(flow.state.drafts) == {refreshed["id"]}
    assert flow.state.latest[f"activity:{batch['week']}"] == refreshed["id"]
    assert json.loads(refreshed["payload"])["revision"] == (2 if edited else 1)


def test_pruning_preserves_submitted_payload_and_repeat_receipt(paths):
    flow, batch, token = sampled_flow(paths)
    first = flow.preview_activity(batch["week"])
    first_receipt = flow.send(first["id"], first["sha256"])
    flow.record(batch["week"], token, classification("writing"))
    second = flow.preview_activity(batch["week"])
    assert set(flow.state.drafts) == {first["id"], second["id"]}
    second_receipt = flow.send(second["id"], second["sha256"])
    assert flow.send(second["id"], second["sha256"]) == second_receipt
    assert flow.preview_activity(batch["week"])["id"] == second["id"]
    assert len(flow.sinks["activity"].sent) == 2
    assert flow.dispatch({"action": "metascience.history"}) == [first_receipt, second_receipt]
    flow.consent("sharing", False)
    flow.consent("sharing", True)
    with pytest.raises(BenchsideError, match="Consent changed"):
        flow.send(second["id"], second["sha256"])


def test_survey_edits_prune_old_approval_without_changing_response_identity(paths):
    flow, batch, _ = sampled_flow(paths)
    activity = flow.preview_activity(batch["week"])
    flow.consent("invitations", True)
    study = flow.invitations()["invitation"]
    key = f"{study['id']}@{study['version']}"
    first = flow.survey(key, {"checked": "yes"})
    second = flow.survey(key, {"checked": "no"})
    assert first["id"] not in flow.state.drafts
    assert set(flow.state.drafts) == {activity["id"], second["id"]}
    assert (
        json.loads(first["payload"])["response_id"] == json.loads(second["payload"])["response_id"]
    )
    with pytest.raises(BenchsideError):
        flow.send(first["id"], first["sha256"])
    assert flow.sinks["surveys"].sent == []
    receipt = flow.send(second["id"], second["sha256"])
    assert flow.send(second["id"], second["sha256"]) == receipt
    assert len(flow.sinks["surveys"].sent) == 1
