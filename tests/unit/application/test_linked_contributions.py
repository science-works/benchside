"""Researcher choices, exact text and backwards-compatible contribution formats."""

import json

import pytest

from benchside.application.sharing import SharingFlow
from benchside.domain.consultation.event import GapObserved
from benchside.domain.export.model.metascience import parse_survey
from benchside.domain.shared.error import BenchsideError
from benchside.domain.shared.model.gap import MissingIndex
from benchside.domain.shared.model.ids import ProjectId
from benchside.reporting import summarise
from tests.unit.application.test_metascience import flow as flow  # noqa: PLC0414
from tests.unit.application.test_metascience import record_batch
from tests.unit.application.test_sharing import Collector


def test_selected_conversation_problems_use_reviewed_gap_flow(flow, paths):
    batch = record_batch(flow, 1)
    token = next(iter(batch["selected"]))
    gap = {
        "kind": "missing_tool",
        "task": "Retain channel names",
        "reached_for": "Fiji 2.16",
        "why_failed": "Names lost on export",
    }
    problem = flow.record_gap(batch["week"], token, gap, "researcher_reported")
    assert (
        flow.record_gap(batch["week"], token, gap, "researcher_reported")["recorded"]
        == problem["recorded"]
    )
    sink = Collector("gaps")
    sharing = SharingFlow(paths, sinks={"gaps": sink})
    with pytest.raises(BenchsideError):
        sharing.prepare("gaps")
    sharing.set_consent("gaps", True, kinds=["missing_tool"])
    draft = sharing.prepare("gaps")[0]
    data = json.loads(draft.preview.payload)
    assert data["observations"] == [
        {
            "id": problem["recorded"],
            "gap": gap,
            "origin": "selected_conversation",
            "basis": "researcher_reported",
        }
    ]
    assert token not in draft.preview.payload and "private-" not in draft.preview.payload
    assert "analysis" in flow.state.grants and "sharing" not in flow.state.grants
    sharing.send(draft.id, draft.preview.payload_sha256)
    with pytest.raises(BenchsideError, match="No selected"):
        sharing.prepare("gaps")


def test_withdrawn_analysis_prevents_pending_selected_problem_send(flow, paths):
    batch = record_batch(flow, 1)
    token = next(iter(batch["selected"]))
    flow.record_gap(
        batch["week"],
        token,
        {"kind": "missing_index", "question": "Which public tool supports this format?"},
        "model_inferred",
    )
    sharing = SharingFlow(paths, sinks={"gaps": Collector("gaps")})
    sharing.set_consent("gaps", True, kinds=["missing_index"])
    draft = sharing.prepare("gaps")[0]
    flow.consent("analysis", False)
    with pytest.raises(BenchsideError, match="selection changed"):
        sharing.send(draft.id, draft.preview.payload_sha256)


def test_old_analysis_and_sharing_choices_require_updated_explanation(flow):
    batch = record_batch(flow, 1)
    flow.consent("sharing", True)
    draft = flow.preview_activity(batch["week"])
    original_grants = dict(flow.state.grants)
    flow._save(analysis_policy=None, sharing_policy=None)
    with pytest.raises(BenchsideError, match="up to 20"):
        flow.batch(batch["week"])
    flow.consent("analysis", True)
    with pytest.raises(BenchsideError, match="pseudonymous"):
        flow.preview_activity(batch["week"])
    flow.consent("sharing", True)
    assert flow.state.grants != original_grants
    with pytest.raises(BenchsideError):
        flow.send(draft["id"], draft["sha256"])
    assert len(flow.batch(batch["week"])["selected"]) == 1


def test_new_sharing_links_contributions_without_research_identifiers(paths, tmp_path):
    sharing = SharingFlow(paths, sinks={c: Collector(c) for c in ("gaps", "feedback", "usage")})
    sharing.set_consent("gaps", True, kinds=["missing_index"])
    sharing.set_consent("feedback", True)
    sharing.set_consent("usage", True)
    sharing.journal.append(
        ProjectId("synthetic-private"),
        GapObserved(
            id="event",
            project_id=ProjectId("synthetic-private"),
            consultation_id="private-session",
            observation_id="problem",
            gap=MissingIndex(question="Public software compatibility index"),
        ),
    )
    feedback = sharing.feedback(ease=4, would_use_again="yes", comment="Synthetic feedback")
    drafts = [
        sharing.prepare("gaps")[0],
        sharing.prepare("feedback", feedback_id=feedback.id)[0],
        sharing.prepare("usage")[0],
    ]
    payloads = [json.loads(d.preview.payload) for d in drafts]
    assert (
        payloads[0]["contributor_id"]
        == payloads[1]["contributor_id"]
        == payloads[2]["installation_id"]
    )
    assert "synthetic-private" not in drafts[0].preview.payload
    assert "private-session" not in drafts[0].preview.payload
    files = []
    for draft in drafts:
        sharing.send(draft.id, draft.preview.payload_sha256)
        path = tmp_path / f"{draft.channel}.json"
        path.write_text(draft.preview.payload)
        files.append(path)
    report = summarise(files)
    assert report["invalid_files"] == 0
    assert report["workflow_observations"] == 1
    assert report["feedback_submissions"] == 1
    assert report["contributing_stores"] == 1
    assert report["stores_contributing_multiple_channels"] == 1
    assert report["contributing_stores_by_workflow_kind"] == {"missing_index": 1}
    assert payloads[0]["contributor_id"] not in json.dumps(report)


def test_old_sharing_grant_is_not_silently_converted_to_linked_sharing(paths):
    sharing = SharingFlow(paths)
    sharing.consent.grant(grant_id="old-grant", gap_kinds=frozenset(["missing_index"]))
    with pytest.raises(BenchsideError, match="renew"):
        sharing.prepare("gaps")
    assert not (paths.home / "reporting/installation.json").exists()
    sharing.set_consent("gaps", True, kinds=["missing_index"])
    assert sharing.consent.active_grant().id != "old-grant"


def join_text_study(flow):
    flow.catalog.studies[0]["questions"].append(
        {
            "id": "comment",
            "type": "text",
            "prompt": "What would improve the workflow?",
            "max_length": 2000,
        }
    )
    flow.consent("invitations", True)
    invitation = flow.invitations()
    key = "synthetic-verification@1"
    flow.join_study(key, invitation["study_sha256"])
    return key


def test_survey_answers_are_preserved_and_sent_under_prior_study_agreement(flow, tmp_path):
    key = join_text_study(flow)
    text = "Fiji 2.16: I couldn't retain channel names.\nPlease improve its documentation."
    draft = flow.survey(key, {"checked": "yes", "comment": {"text": text}})
    assert json.loads(draft["payload"])["answers"]["comment"]["text"] == text
    receipt = flow.send(draft["id"], draft["sha256"])
    assert flow.send(draft["id"], draft["sha256"]) == receipt
    assert len(flow.sinks["surveys"].sent) == 1
    parsed = parse_survey(draft["payload"])
    assert parsed.contributor_id == flow.state.participation[key].contributor_id
    path = tmp_path / "survey.json"
    path.write_text(draft["payload"])
    report = summarise([path])
    assert report["invalid_files"] == 0
    assert sum(report["survey_free_text_responses"].values()) == 1
    assert text not in json.dumps(report)  # Aggregate exports never copy raw survey answers.


@pytest.mark.parametrize("change", ["withdraw", "destination", "definition"])
def test_survey_agreement_cannot_be_reused_for_changed_terms(flow, change):
    key = join_text_study(flow)
    draft = flow.survey(key, {"comment": {"text": "Synthetic answer"}})
    if change == "withdraw":
        flow.consent("invitations", False)
        flow.consent("invitations", True)
    elif change == "destination":
        flow.sinks["surveys"].destination = "https://other.example/v1/surveys"
    else:
        study = flow.state.studies[key].model_copy(update={"purpose": "Different study"})
        flow._save(studies={key: study})
    with pytest.raises((BenchsideError, ValueError)):
        flow.send(draft["id"], draft["sha256"])
    assert not flow.sinks["surveys"].sent


def test_unaccepted_free_text_and_unknown_answers_are_rejected(flow):
    flow.consent("invitations", True)
    flow.invitations()
    with pytest.raises(ValueError):
        flow.survey("synthetic-verification@1", {"checked": {"text": "not an option"}})
    with pytest.raises(BenchsideError):
        flow.join_study("synthetic-verification@1", "0" * 64)
