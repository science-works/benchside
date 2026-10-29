import hashlib
import json
from datetime import date

import pytest
from pydantic import ValidationError as SchemaError

from benchside.application.metascience import Metascience
from benchside.application.native import pack, run_native, unpack
from benchside.domain.export.model.metascience import (
    ActivityPayload,
    Sample,
    digest,
    parse_activity,
)
from benchside.domain.export.model.value import DeliveryReceipt
from benchside.domain.shared.error import ValidationError

RANDOM = "weekly-random-max20-v1"
MANUAL = "weekly-user-selected-max20-v1"
LEGACY = "weekly-random-10pct-max5-v1"
SCOPE = {"host": "claude", "source_id": "synthetic-selected-source"}
CLASSIFICATION = {
    "benchside_role": "none",
    "activity": {"value": "coding", "basis": "model_inferred"},
    "obstacle": {"value": "unknown", "basis": "unknown"},
    "verification": {"value": "unknown", "basis": "unknown"},
    "outcome": {"value": "not_reported", "basis": "unknown"},
}


def candidates(count):
    return [{"scope": SCOPE, "session_ref": f"synthetic-conversation-{n}"} for n in range(count)]


def enabled_flow(paths):
    flow = Metascience(paths, today=date(2026, 10, 27))
    flow.consent("analysis", True)
    flow.scopes([SCOPE])
    return flow


@pytest.mark.parametrize("count,selected", [(0, 0), (1, 1), (8, 8), (20, 20), (21, 20), (500, 20)])
def test_automatic_selection_uses_all_relevant_sessions_up_to_twenty(paths, count, selected):
    flow = enabled_flow(paths)
    batch = flow.sample(candidates(count))
    assert batch["sampling"] == RANDOM
    assert batch["eligible"] == count
    assert len(batch["selected"]) == selected
    assert flow.sample(list(reversed(candidates(count)))) == batch
    assert flow.status()["limits"]["sessions_per_week"] == 20
    assert "sample_percent" not in flow.status()["limits"]


def test_manual_selection_is_exact_and_not_an_estimate_of_all_research(paths):
    flow = enabled_flow(paths)
    chosen = candidates(8)
    batch = flow.dispatch(
        {"action": "metascience.sample", "selection": "user_selected", "candidates": chosen}
    )
    assert batch["sampling"] == MANUAL
    assert batch["eligible"] == len(batch["selected"]) == 8
    assert {c["session_ref"] for c in batch["selected"].values()} == {
        c["session_ref"] for c in chosen
    }
    assert flow.sample(list(reversed(chosen)), selection="user_selected") == batch


@pytest.mark.parametrize("count", [0, 21])
def test_manual_selection_rejects_empty_or_oversized_set_without_sampling(paths, count):
    flow = enabled_flow(paths)
    before = flow.path.read_bytes()
    with pytest.raises(ValidationError, match="between 1 and 20"):
        flow.sample(candidates(count), selection="user_selected")
    assert flow.path.read_bytes() == before


@pytest.mark.parametrize("selection", [[], {}, 20, True, "unknown-method"])
def test_malformed_selection_has_actionable_error_without_state_change(paths, selection):
    flow = enabled_flow(paths)
    before = flow.path.read_bytes()
    with pytest.raises(ValidationError, match="Choose random or user_selected"):
        flow.sample(candidates(1), selection=selection)
    assert flow.path.read_bytes() == before


@pytest.mark.parametrize("first,second", [("random", "user_selected"), ("user_selected", "random")])
def test_modes_share_one_fixed_weekly_cap_without_switching_or_redraw(paths, first, second):
    flow = enabled_flow(paths)
    batch = flow.sample(candidates(20), selection=first)
    before = flow.path.read_bytes()
    with pytest.raises(ValidationError, match="selection method is fixed"):
        flow.sample(candidates(20), selection=second)
    with pytest.raises(ValidationError, match="sample is fixed"):
        flow.sample(candidates(19), selection=first)
    assert flow.path.read_bytes() == before
    assert flow.batch(batch["week"]) == batch


def test_manual_selection_cannot_resample_previous_week_conversations(paths):
    flow = enabled_flow(paths)
    flow.sample(candidates(2), selection="random")
    flow.today = date(2026, 11, 2)
    with pytest.raises(ValidationError, match="already selected"):
        flow.sample(candidates(2), selection="user_selected")
    assert set(flow.state.samples) == {"2026-10-19"}


def test_legacy_sample_keeps_original_policy_and_cannot_be_upgraded_mid_week(paths):
    flow = enabled_flow(paths)
    items = candidates(100)
    inventory = sorted(digest([SCOPE["host"], c["session_ref"]]) for c in items)
    legacy = Sample(
        id="a" * 32,
        inventory_sha256=digest(inventory),
        eligible=100,
        selected={f"{index:032x}": candidate for index, candidate in enumerate(items[:5])},
    )
    flow._save(samples={"2026-10-19": legacy})
    assert flow.sample(items)["sampling"] == LEGACY
    before = flow.path.read_bytes()
    for method in ("random", "user_selected"):
        with pytest.raises(ValidationError):
            flow.sample(items, selection=method)
    assert flow.path.read_bytes() == before
    assert flow.state.samples["2026-10-19"].eligible == 100
    assert len(flow.state.samples["2026-10-19"].selected) == 5


@pytest.mark.parametrize("method,tag", [("random", RANDOM), ("user_selected", MANUAL)])
def test_twenty_classifications_round_trip_and_receipts_preserve_method(paths, method, tag):
    class Sink:
        destination = "https://synthetic.invalid/v1/activity"

        def __init__(self):
            self.sent = []

        def send(self, payload):
            self.sent.append(payload)
            return DeliveryReceipt(
                status="stored",
                sha256=hashlib.sha256(payload.encode()).hexdigest(),
                received_at="2026-10-27T00:00:00+00:00",
                observations=20,
            )

    flow = enabled_flow(paths)
    flow.sinks = {"activity": Sink()}
    flow.consent("sharing", True)
    batch = flow.sample(candidates(20), selection=method)
    for token in batch["selected"]:
        flow.record(batch["week"], token, CLASSIFICATION)
    draft = flow.preview_activity(batch["week"])
    payload = parse_activity(draft["payload"])
    assert payload.sampling == tag
    assert payload.eligible == payload.selected == len(payload.observations) == 20
    assert "synthetic-conversation" not in draft["payload"]
    receipt = flow.send(draft["id"], draft["sha256"])
    assert receipt["observations"] == 20
    assert flow.send(draft["id"], draft["sha256"]) == receipt
    assert flow.sinks["activity"].sent == [draft["payload"]]
    restored = Metascience(paths, today=flow.today, sinks=flow.sinks)
    assert restored.state.samples[batch["week"]].sampling == tag
    assert restored.dispatch({"action": "metascience.history"}) == [receipt]


@pytest.mark.parametrize(
    "tag,eligible,selected,valid",
    [
        (LEGACY, 100, 5, True),
        (LEGACY, 20, 20, False),
        (RANDOM, 100, 20, True),
        (RANDOM, 8, 8, True),
        (RANDOM, 20, 2, False),
        (MANUAL, 8, 8, True),
        (MANUAL, 100, 20, False),
        (MANUAL, 21, 21, False),
    ],
)
def test_wire_counts_are_specific_to_selection_method(tag, eligible, selected, valid):
    payload = {
        "benchside_version": "0.1.3",
        "batch_id": "c" * 32,
        "revision": 1,
        "week": "2026-10-19",
        "sampling": tag,
        "eligible": eligible,
        "selected": selected,
        "observations": [{**CLASSIFICATION, "host": "claude"}],
    }
    if valid:
        assert ActivityPayload.model_validate(payload).sampling == tag
    else:
        with pytest.raises(SchemaError):
            ActivityPayload.model_validate(payload)


@pytest.mark.parametrize("selection,tag", [("random", RANDOM), ("user_selected", MANUAL)])
def test_native_state_round_trips_twenty_selected_sessions(selection, tag):
    snapshot = run_native({"action": "native.create"})["snapshot"]

    def run(request):
        nonlocal snapshot
        outcome = run_native(
            {
                "action": "native.run",
                "workspace_id": snapshot["workspace_id"],
                "document": snapshot,
                "request": request,
            }
        )
        assert outcome["ok"], outcome
        snapshot = outcome["snapshot"]
        return outcome["result"]

    run({"action": "metascience.consent", "choice": "analysis", "enabled": True})
    run({"action": "metascience.scopes", "scopes": [SCOPE]})
    week = run({"action": "metascience.status"})["sampling_window"]["week"]
    batch = run(
        {
            "action": "metascience.sample",
            "week": week,
            "selection": selection,
            "candidates": candidates(20),
        }
    )
    assert snapshot["schema"] == "benchside.native.v2"
    assert unpack(snapshot)[1]["replay"]["generation"] == 1
    token = next(iter(batch["selected"]))
    run(
        {
            "action": "metascience.record",
            "week": week,
            "token": token,
            "classification": CLASSIFICATION,
        }
    )
    restored = run({"action": "metascience.batch", "week": week})
    assert restored["sampling"] == tag and len(restored["selected"]) == 20
    assert restored["records"][token]["benchside_role"] == "none"
    saved = json.loads(unpack(snapshot)[1]["files"]["metascience/state.json"])
    assert saved["samples"][week]["sampling"] == tag


def test_legacy_native_sample_without_method_restores_without_rewriting_bytes(paths):
    flow = enabled_flow(paths)
    legacy = Sample(
        id="f" * 32,
        inventory_sha256=digest([]),
        eligible=21,
        selected={f"{index:032x}": item for index, item in enumerate(candidates(3))},
    )
    flow._save(samples={"2026-10-19": legacy})
    state = flow.state.model_dump(mode="json")
    state["samples"]["2026-10-19"].pop("sampling")
    original = json.dumps(state)
    initial = run_native({"action": "native.create"})["snapshot"]
    body = unpack(initial)[1]
    body["files"]["metascience/state.json"] = original
    snapshot = pack(body, initial["workspace_id"], initial["revision"])
    outcome = run_native(
        {
            "action": "native.run",
            "workspace_id": snapshot["workspace_id"],
            "document": snapshot,
            "request": {"action": "metascience.batch", "week": "2026-10-19"},
        }
    )
    assert outcome["ok"], outcome
    assert outcome["result"]["sampling"] == LEGACY
    assert len(outcome["result"]["selected"]) == 3
    assert unpack(outcome["snapshot"])[1]["files"]["metascience/state.json"] == original


def test_shared_new_selection_fixtures_keep_bounded_method_contract():
    from pathlib import Path

    directory = Path(__file__).parents[2] / "fixtures/metascience"
    for name, method in [
        ("activity-random-max20.json", RANDOM),
        ("activity-user-selected-max20.json", MANUAL),
    ]:
        payload = ActivityPayload.model_validate_json((directory / name).read_text())
        assert payload.sampling == method and len(payload.observations) == 20
