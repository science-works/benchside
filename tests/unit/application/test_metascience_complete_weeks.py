import json
from datetime import date, timedelta

import pytest

from benchside.application.metascience import Metascience
from benchside.domain.export.model.metascience import (
    Sample,
    digest,
    parse_activity,
)
from benchside.domain.shared.error import ValidationError

SCOPE = {"host": "claude", "source_id": "synthetic-selected-source"}
CANDIDATES = [{"scope": SCOPE, "session_ref": "synthetic-completed-conversation"}]
CLASSIFICATION = {
    "benchside_role": "none",
    "activity": {"value": "coding", "basis": "model_inferred"},
    "obstacle": {"value": "unknown", "basis": "unknown"},
    "verification": {"value": "unknown", "basis": "unknown"},
    "outcome": {"value": "not_reported", "basis": "unknown"},
}


def enabled_flow(paths, today=date(2026, 10, 27)):
    flow = Metascience(paths, today=today)
    flow.consent("analysis", True)
    flow.scopes([SCOPE])
    return flow


@pytest.mark.parametrize(
    "today,expected",
    [
        (date(2026, 10, 25), "2026-10-12"),  # Sunday has not ended yet.
        (date(2026, 10, 26), "2026-10-19"),  # Monday starts a new collection window.
        (date(2026, 10, 27), "2026-10-19"),
        (date(2026, 11, 1), "2026-10-19"),
        (date(2026, 11, 2), "2026-10-26"),
        (date(2027, 1, 1), "2026-12-21"),  # Across the year boundary.
    ],
)
def test_new_sample_covers_previous_complete_utc_week(paths, today, expected):
    flow = enabled_flow(paths, today)
    window = flow.status()["sampling_window"]
    assert window == {
        "week": expected,
        "starts_at": f"{expected}T00:00:00Z",
        "ends_before": f"{date.fromisoformat(expected) + timedelta(days=7)}T00:00:00Z",
    }
    batch = flow.sample(CANDIDATES)
    assert batch["week"] == expected
    assert set(flow.state.samples) == {expected}
    assert flow.sample(CANDIDATES) == batch


@pytest.mark.parametrize("week", ["2026-10-26", "2026-11-02", "2026-10-12"])
def test_sample_rejects_incomplete_future_or_stale_inventory_window(paths, week):
    flow = enabled_flow(paths)
    before = flow.path.read_bytes()
    with pytest.raises(ValidationError, match="completed UTC week 2026-10-19"):
        flow.dispatch({"action": "metascience.sample", "week": week, "candidates": CANDIDATES})
    assert flow.path.read_bytes() == before


def test_inventory_window_cannot_be_silently_relabelled_after_monday_rollover(paths):
    flow = enabled_flow(paths, date(2026, 11, 1))
    window = flow.status()["sampling_window"]
    flow.today = date(2026, 11, 2)
    with pytest.raises(ValidationError, match="completed UTC week 2026-10-26"):
        flow.dispatch(
            {"action": "metascience.sample", "week": window["week"], "candidates": CANDIDATES}
        )
    assert flow.state.samples == {}


def test_legacy_partial_week_sample_is_preserved_without_redraw_or_relabelling(paths):
    flow = enabled_flow(paths)
    week = "2026-10-26"
    token = "b" * 32
    legacy = Sample(
        id="a" * 32,
        inventory_sha256=digest([digest([SCOPE["host"], CANDIDATES[0]["session_ref"]])]),
        eligible=1,
        selected={token: CANDIDATES[0]},
        records={token: CLASSIFICATION},
        revision=3,
    )
    flow._save(samples={week: legacy}, seen=[digest([SCOPE["host"], CANDIDATES[0]["session_ref"]])])
    before = flow.state.samples[week].model_dump()
    assert flow.batch(week) == {"week": week, **before}
    new = flow.sample([])
    assert new["week"] == "2026-10-19"
    assert flow.state.samples[week].model_dump() == before
    flow.today = date(2026, 11, 2)
    assert flow.sample(CANDIDATES) == {"week": week, **before}
    with pytest.raises(ValidationError, match="sample is fixed"):
        flow.sample([])
    assert flow.state.samples[week].model_dump() == before


def test_scope_narrowing_retires_completed_week_even_if_removed_source_was_not_selected(paths):
    flow = enabled_flow(paths)
    other = {"host": "claude", "source_id": "synthetic-unselected-source"}
    flow.scopes([SCOPE, other])
    batch = flow.sample(CANDIDATES)
    flow.scopes([SCOPE])
    assert flow.status()["retired_weeks"] == ["2026-10-19"]
    with pytest.raises(ValidationError, match="available from 2026-11-02"):
        flow.batch(batch["week"])
    flow.today = date(2026, 11, 2)
    assert flow.sample([])["week"] == "2026-10-26"


def test_completed_week_preview_preserves_wire_contract_without_source_ids(paths):
    class Sink:
        destination = "https://synthetic.invalid/v1/activity"

    flow = enabled_flow(paths)
    flow.sinks = {"activity": Sink()}
    flow.consent("sharing", True)
    batch = flow.dispatch(
        {"action": "metascience.sample", "week": "2026-10-19", "candidates": CANDIDATES}
    )
    flow.record(batch["week"], next(iter(batch["selected"])), CLASSIFICATION)
    preview = flow.preview_activity(batch["week"])
    payload = parse_activity(preview["payload"])
    assert payload.week == "2026-10-19"
    assert payload.sampling == "weekly-random-max20-v1"
    assert payload.eligible == payload.selected == 1
    assert payload.observations[0].benchside_role == "none"
    assert set(json.loads(preview["payload"])) == {
        "contributor_id",
        "schema",
        "benchside_version",
        "batch_id",
        "revision",
        "week",
        "sampling",
        "coverage",
        "eligible",
        "selected",
        "observations",
    }
    assert "synthetic-selected-source" not in preview["payload"]
    assert "synthetic-completed-conversation" not in preview["payload"]
