"""Broad workflow capture and notebook-only work must preserve review boundaries."""

import json

import pytest

from benchside.application.app import App
from benchside.application.sharing import SharingFlow
from benchside.domain.export.model.wire import validate_payload
from benchside.domain.shared.error import BenchsideError
from benchside.reporting import summarise
from tests.unit.application.test_native import Notebook
from tests.unit.application.test_sharing import Collector


def setup(app, key="synthetic"):
    result = app.run({"action": "setup", "project_key": key})
    return {k: result[k] for k in ("project_id", "session_id")}


def problem(**extra):
    return {
        "kind": "workflow_problem",
        "description": "Shared equipment bookings are cancelled.",
        **extra,
    }


def test_notebook_records_restore_without_role_or_consultation_counts(paths):
    app = App(paths)
    ctx = setup(app)
    saved = app.run(
        {
            "action": "notebook.decide",
            **ctx,
            "decision": "Check bookings first.",
            "rationale": "Avoid wasted preparation.",
        }
    )
    app.run(
        {
            "action": "notebook.record",
            **ctx,
            "record": {
                "kind": "evidence",
                "summary": "Two cancellations reported.",
                "details": ["Researcher report; cause unknown."],
                "sources": ["Researcher report in this conversation"],
            },
        }
    )
    q = app.run({"action": "notebook.question", **ctx, "question": "Why were bookings cancelled?"})
    fresh = App(paths)
    fresh.run(
        {
            "action": "notebook.answer",
            **ctx,
            "question_id": q["recorded"],
            "answer": "Maintenance was rescheduled.",
        }
    )
    result = fresh.run({"action": "recall", **ctx})
    assert result["recent_decisions"][0]["id"] == saved["recorded"]
    assert result["recent_records"][0]["kind"] == "evidence"
    assert result["open_sittings"] == []
    flow = SharingFlow(paths)
    flow.set_consent("usage", True)
    payload = json.loads(flow.prepare("usage")[0].preview.payload)
    assert payload["sessions"] == []
    assert "Check bookings" not in json.dumps(payload)


def test_notebook_project_boundaries_and_decision_corrections(paths):
    app = App(paths)
    first, second = setup(app), setup(app, "other")
    saved = app.run(
        {"action": "notebook.decide", **first, "decision": "Original", "rationale": "Reason"}
    )
    for ctx in (second, {**first, "session_id": second["session_id"]}):
        with pytest.raises(BenchsideError):
            app.run(
                {
                    "action": "notebook.decide",
                    **ctx,
                    "decision": "Replacement",
                    "rationale": "Reason",
                    "supersedes": saved["recorded"],
                }
            )
    app.run(
        {
            "action": "notebook.decide",
            **first,
            "decision": "Replacement",
            "rationale": "New evidence",
            "supersedes": saved["recorded"],
        }
    )
    assert app.run({"action": "recall", **second})["recent_decisions"] == []


@pytest.mark.parametrize(
    "labels", [[], ["other"], ["equipment_access", "coordination"], ["unexpected new topic"]]
)
def test_uncategorised_other_and_unfamiliar_labels_survive_review_and_reporting(
    paths, tmp_path, labels
):
    app = App(paths)
    ctx = setup(app)
    gap = problem(
        labels=labels,
        deidentified_excerpt="The booking for [redacted] was cancelled twice.",
        workaround_status="researcher_tried",
        context={"workaround": "Check availability before preparation."},
    )
    saved = app.run({"action": "notebook.gap", **ctx, "gap": gap, "basis": "researcher_reported"})
    flow = SharingFlow(paths, sinks={"gaps": Collector("gaps")})
    flow.set_consent("gaps", True, scope="all_workflow")
    draft = flow.prepare("gaps")[0]
    data = validate_payload(draft.preview.payload)
    assert data["schema"] == "benchside.gaps.v4"
    assert data["observations"][0]["gap"] == gap
    assert data["observations"][0]["id"] == saved["recorded"]
    assert data["observations"][0]["basis"] == "researcher_reported"
    with pytest.raises(BenchsideError):
        flow.send(draft.id, "0" * 64)
    assert not flow.sinks["gaps"].sent
    flow.send(draft.id, draft.preview.payload_sha256)
    flow.send(draft.id, draft.preview.payload_sha256)
    assert len(flow.sinks["gaps"].sent) == 1
    path = tmp_path / "received.json"
    path.write_text(draft.preview.payload)
    report = summarise([path])
    assert report["workflow_observations"] == 1
    assert report["workflow_labels"] == {label: 1 for label in labels}
    assert report["workflow_unlabelled"] == (not labels)


def test_old_consent_is_not_silently_expanded(paths):
    app = App(paths)
    ctx = setup(app)
    app.run({"action": "notebook.gap", **ctx, "gap": problem()})
    flow = SharingFlow(paths, sinks={"gaps": Collector("gaps")})
    flow.set_consent("gaps", True, kinds=["missing_index"])
    assert flow.status()["gaps"]["scope"] == "kinds"
    with pytest.raises(BenchsideError):
        flow.prepare("gaps")
    flow.set_consent("gaps", True, scope="all_workflow")
    draft = flow.prepare("gaps")[0]
    flow.set_consent("gaps", False)
    with pytest.raises(BenchsideError):
        flow.send(draft.id, draft.preview.payload_sha256)


def test_native_notebook_and_workflow_features_are_version_gated():
    notebook = Notebook()
    ctx = {k: v for k, v in notebook.setup().items() if k in {"project_id", "session_id"}}
    result = notebook.run(
        {
            "action": "notebook.decide",
            **ctx,
            "decision": "Private decision",
            "rationale": "Private reason",
        }
    )
    assert result["ok"]
    assert result["snapshot"]["schema"] == "benchside.native.v5"
    fresh = Notebook()
    fresh.document, fresh.workspace_id = notebook.document, notebook.workspace_id
    result = fresh.run({"action": "recall", **ctx})
    assert result["result"]["recent_decisions"][0]["decision"] == "Private decision"
    assert result["result"]["open_sittings"] == []


def test_workflow_excerpt_has_same_sensitive_content_checks(paths):
    app = App(paths)
    ctx = setup(app)
    app.run(
        {
            "action": "notebook.gap",
            **ctx,
            "gap": problem(deidentified_excerpt="Contact person@example.org about [redacted]."),
        }
    )
    flow = SharingFlow(paths, sinks={"gaps": Collector("gaps")})
    flow.set_consent("gaps", True, scope="all_workflow")
    draft = flow.prepare("gaps")[0]
    assert "person@example.org" not in draft.preview.payload
    assert not flow.sinks["gaps"].sent


def test_sharing_check_in_only_offers_new_consented_material_once_per_chat(paths):
    app = App(paths)
    ctx = setup(app)
    call = {"action": "sharing.check_in", **ctx}
    assert not app.run(call)["offer"]
    app.run({"action": "notebook.gap", **ctx, "gap": problem()})
    assert not app.run(call)["offer"]
    app.run(
        {"action": "sharing.consent", "channel": "gaps", "enabled": True, "scope": "all_workflow"}
    )
    assert app.run(call) == {"offer": True, "channel": "gaps", "pending": 1}
    assert not app.run(call)["offer"]
    fresh = setup(app)
    # A declined/deferred offer isn't repeated just because the chat changed.
    assert not app.run({"action": "sharing.check_in", **fresh})["offer"]
    app.run(
        {
            "action": "notebook.gap",
            **fresh,
            "gap": problem(description="Reagent deliveries are unpredictable."),
        }
    )
    assert app.run({"action": "sharing.check_in", **fresh})["pending"] == 2
    assert not app.run({"action": "sharing.check_in", **fresh})["offer"]


@pytest.mark.parametrize(
    "change",
    [
        {"description": " "},
        {"labels": ["a", "a"]},
        {"labels": ["a"] * 21},
        {"deidentified_excerpt": " "},
        {"workaround_status": "researcher_reported_helpful"},
        {"scientific_results": "private"},
    ],
)
def test_new_problem_rejects_bad_structure_without_restricting_topics(paths, change):
    app = App(paths)
    ctx = setup(app)
    with pytest.raises(BenchsideError):
        app.run({"action": "notebook.gap", **ctx, "gap": problem(**change)})


@pytest.mark.parametrize(
    "role",
    [
        "pi",
        "pi-hypothesis",
        "study-design",
        "methods-clinic",
        "results-meeting",
        "repro-check",
        "journal-club",
        "peer-review",
    ],
)
def test_every_role_sees_shared_notebook_and_can_capture_broad_problem(paths, role):
    app = App(paths)
    ctx = setup(app)
    original = "Check equipment availability first."
    app.run(
        {
            "action": "notebook.decide",
            **ctx,
            "decision": original,
            "rationale": "Researcher chose this order.",
        }
    )
    started = app.run({"action": "start", **ctx, "role": role})
    assert started["recall"]["recent_decisions"][0]["decision"] == original
    saved = app.run(
        {
            "action": "gap",
            **ctx,
            "sitting_id": started["sitting"]["id"],
            "gap": problem(labels=["other"]),
            "basis": "researcher_reported",
        }
    )
    assert saved["recorded"]
    assert saved["recall"]["recent_decisions"][0]["decision"] == original


def test_native_check_in_survives_restore_and_schema_downgrade_is_refused():
    from benchside.application.native import _digest, unpack

    notebook = Notebook()
    ctx = {k: v for k, v in notebook.setup().items() if k in {"project_id", "session_id"}}
    assert notebook.run({"action": "notebook.gap", **ctx, "gap": problem()})["ok"]
    assert notebook.run(
        {"action": "sharing.consent", "channel": "gaps", "enabled": True, "scope": "all_workflow"}
    )["ok"]
    offered = notebook.run({"action": "sharing.check_in", **ctx})
    assert offered["ok"] and offered["result"]["offer"]
    fresh = notebook.setup()
    assert not notebook.run(
        {"action": "sharing.check_in", **{k: fresh[k] for k in ("project_id", "session_id")}}
    )["result"]["offer"]
    tampered = dict(offered["snapshot"], schema="benchside.native.v4")
    tampered["sha256"] = _digest({k: v for k, v in tampered.items() if k != "sha256"})
    with pytest.raises(BenchsideError, match="newer snapshot schema"):
        unpack(tampered)


def test_notebook_evidence_needs_source_and_failed_save_preserves_other_records(paths):
    app = App(paths)
    ctx = setup(app)
    with pytest.raises(BenchsideError, match="source"):
        app.run(
            {
                "action": "notebook.record",
                **ctx,
                "record": {
                    "kind": "evidence",
                    "summary": "Unverified",
                    "details": ["A proposed result"],
                },
            }
        )
    assert app.run({"action": "recall", **ctx})["recent_records"] == []


def test_shared_client_receiver_contract_fixture_is_valid():
    from pathlib import Path

    data = validate_payload((Path(__file__).parents[2] / "fixtures/workflow-v4.json").read_text())
    gap = data["observations"][0]["gap"]
    assert gap["labels"] == ["equipment_access", "other", "new analytical label"]
    assert gap["deidentified_excerpt"] == "The booking for [redacted] was cancelled twice."
