import copy
import hashlib
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError as SchemaError

from benchside import __version__
from benchside.application.app import App
from benchside.application.metascience import Metascience, StudyClient
from benchside.application.native import reference, run_native
from benchside.domain.export.model.metascience import (
    ActivityPayload,
    Classification,
    StudyCatalog,
    SurveyPayload,
)
from benchside.domain.export.model.value import DeliveryReceipt
from benchside.domain.shared.error import BenchsideError, InfrastructureError
from benchside.reporting import summarise

TODAY = date(2026, 10, 22)
SCOPE = {"host": "claude", "source_id": "private-research-project"}
CLASSIFICATION = {
    "benchside_role": "none",
    "activity": {"value": "analysis", "basis": "model_inferred"},
    "obstacle": {"value": "tool_failure", "basis": "researcher_reported"},
    "verification": {"value": "ran_test", "basis": "model_inferred"},
    "outcome": {"value": "not_reported", "basis": "unknown"},
}
STUDY = {
    "id": "synthetic-verification",
    "version": 1,
    "title": "Synthetic test survey",
    "purpose": "Exercise the optional study flow using synthetic answers only.",
    "data_use": "Local development fixture; never published as an active study.",
    "retention_days": 30,
    "opens": "2026-10-01",
    "closes": "2026-12-31",
    "questions": [
        {
            "id": "checked",
            "prompt": "Did you check the answer?",
            "options": [
                {"id": "yes", "label": "Yes"},
                {"id": "no", "label": "No"},
                {"id": "unsure", "label": "Unsure"},
            ],
        }
    ],
}


class Catalog:
    def __init__(self):
        self.calls = 0
        self.studies = [copy.deepcopy(STUDY)]

    def fetch(self):
        self.calls += 1
        return StudyCatalog(studies=self.studies)


class Sink:
    def __init__(self, channel):
        self.destination = f"https://collector.example/v1/{channel}"
        self.sent = []
        self.fail = False

    def send(self, payload):
        self.sent.append(payload)
        if self.fail:
            raise InfrastructureError("Temporary failure")
        data = json.loads(payload)
        return DeliveryReceipt(
            status="stored",
            sha256=hashlib.sha256(payload.encode()).hexdigest(),
            received_at=datetime.now(UTC).isoformat(),
            observations=len(data["observations"]) if "observations" in data else 1,
        )


@pytest.fixture
def flow(paths):
    return Metascience(
        paths, today=TODAY, catalog=Catalog(), sinks={c: Sink(c) for c in ("surveys", "activity")}
    )


def candidates(n=21):
    return [{"scope": SCOPE, "session_ref": f"private-conversation-{i}"} for i in range(n)]


def record_batch(flow, n=21):
    flow.consent("analysis", True)
    flow.scopes([SCOPE])
    batch = flow.sample(candidates(n))
    for token in batch["selected"]:
        flow.record(batch["week"], token, CLASSIFICATION)
    return flow.batch(batch["week"])


def survey(flow):
    flow.consent("invitations", True)
    flow.invitations()
    return flow.survey("synthetic-verification@1", {"checked": "yes"})


def test_all_choices_off_no_background_io_or_identifiers(flow, paths):
    assert not any(flow.status()["choices"].values())
    assert not flow.path.exists()
    for call in (
        flow.invitations,
        lambda: flow.sample(candidates()),
        lambda: flow.scopes([SCOPE]),
        lambda: flow.survey("synthetic-verification@1", {"checked": "yes"}),
        lambda: flow.preview_activity("2026-10-19"),
    ):
        with pytest.raises(BenchsideError):
            call()
    assert flow.catalog.calls == 0
    assert not flow.path.exists()
    assert not (paths.home / "reporting/installation.json").exists()


def test_invitations_once_a_week_skip_and_permanent_opt_out(flow):
    flow.consent("invitations", True)
    first = flow.invitations()
    assert first["invitation"]["id"] == STUDY["id"]
    assert flow.invitations()["reason"] == "weekly_limit"
    flow.dismiss("synthetic-verification@1", permanently=True)
    flow.today += timedelta(days=8)
    flow.catalog.studies[0]["version"] = 2
    assert flow.invitations()["invitation"] is None
    assert flow.catalog.calls == 2
    assert flow.invitations()["reason"] == "already_checked_today"
    flow.consent("invitations", False)
    with pytest.raises(BenchsideError):
        flow.invitations()
    assert flow.catalog.calls == 2


def test_invitation_catalog_failure_does_not_poll_repeatedly(flow):
    flow.consent("invitations", True)
    flow.catalog.studies = [{"not": "a study"}]
    with pytest.raises(ValueError):
        flow.invitations()
    assert flow.invitations()["reason"] == "already_checked_today"


def test_expired_and_future_studies_are_not_offered(flow):
    flow.consent("invitations", True)
    flow.catalog.studies[0]["closes"] = "2026-10-21"
    assert flow.invitations()["invitation"] is None
    flow.today += timedelta(days=1)
    flow.catalog.studies[0].update(opens="2026-11-01", closes="2026-12-31")
    assert flow.invitations()["invitation"] is None


def test_survey_edits_require_new_exact_approval_and_have_no_linkage(flow):
    first = survey(flow)
    second = flow.survey("synthetic-verification@1", {"checked": "no"})
    with pytest.raises(BenchsideError):
        flow.send(first["id"], first["sha256"])
    with pytest.raises(BenchsideError):
        flow.send(second["id"], first["sha256"])
    receipt = flow.send(second["id"], second["sha256"])
    assert flow.send(second["id"], second["sha256"]) == receipt
    assert len(flow.sinks["surveys"].sent) == 1
    assert set(json.loads(second["payload"])) == {
        "schema",
        "benchside_version",
        "response_id",
        "study_id",
        "study_version",
        "study_sha256",
        "answers",
    }
    assert not flow.status()["choices"]["sharing"]  # Answer approval is study-specific.
    assert not flow.status()["choices"]["analysis"]
    with pytest.raises(BenchsideError):
        flow.survey("synthetic-verification@1", {"checked": "yes"})


@pytest.mark.parametrize(
    "answers", [{}, {"secret": "yes"}, {"checked": "unpublished research"}, {"checked": True}]
)
def test_survey_rejects_free_text_and_unknown_fields(flow, answers):
    survey(flow)
    with pytest.raises(ValueError):
        flow.survey("synthetic-verification@1", answers)


@pytest.mark.parametrize("action", ["revoke", "dismiss", "expire"])
def test_pending_survey_cannot_bypass_revocation_or_expiry(flow, action):
    draft = survey(flow)
    if action == "revoke":
        flow.consent("invitations", False)
        flow.consent("invitations", True)
    elif action == "dismiss":
        flow.dismiss("synthetic-verification@1")
    else:
        flow.today = date(2027, 1, 1)
    with pytest.raises(BenchsideError):
        flow.send(draft["id"], draft["sha256"])
    assert not flow.sinks["surveys"].sent


def test_private_sampling_requires_scope_and_bounds_random_selection(flow):
    flow.consent("analysis", True)
    with pytest.raises(BenchsideError):
        flow.sample(candidates())
    flow.scopes([SCOPE])
    outside = candidates(1)
    outside[0]["scope"] = {"host": "claude", "source_id": "not-selected"}
    with pytest.raises(BenchsideError):
        flow.sample(outside)
    with pytest.raises(BenchsideError):
        flow.sample(candidates(1) * 2)
    batch = flow.sample(candidates(100))
    assert batch["eligible"] == 100 and len(batch["selected"]) == 20
    assert flow.sample(list(reversed(candidates(100)))) == batch
    with pytest.raises(BenchsideError):
        flow.sample(candidates(99))
    flow.today += timedelta(days=7)
    later = flow.sample(candidates(100))
    assert later["eligible"] == 80
    assert not {c["session_ref"] for c in batch["selected"].values()} & {
        c["session_ref"] for c in later["selected"].values()
    }
    assert not any(s.sent for s in flow.sinks.values())


def test_empty_sample_is_valid_but_cannot_be_shared(flow):
    flow.consent("analysis", True)
    flow.scopes([SCOPE])
    batch = flow.sample([])
    assert not batch["selected"]
    flow.consent("sharing", True)
    with pytest.raises(BenchsideError):
        flow.preview_activity(batch["week"])


def test_same_conversation_in_two_sources_is_not_counted_twice(flow):
    flow.consent("analysis", True)
    other = {"host": "claude", "source_id": "another-selected-project"}
    flow.scopes([SCOPE, other])
    with pytest.raises(BenchsideError, match="more than once"):
        flow.sample(
            [
                {"scope": SCOPE, "session_ref": "same-conversation"},
                {"scope": other, "session_ref": "same-conversation"},
            ]
        )


def test_broader_observation_works_without_a_benchside_role(flow, paths):
    batch = record_batch(flow)
    assert len(batch["records"]) == 20
    assert all(r["benchside_role"] == "none" for r in batch["records"].values())
    assert not (paths.home / "projects").exists()
    with pytest.raises(BenchsideError):
        flow.preview_activity(batch["week"])
    flow.consent("sharing", True)
    token = next(iter(batch["records"]))
    draft = flow.preview_activity(batch["week"], [token])
    data = json.loads(draft["payload"])
    assert (data["eligible"], data["selected"], len(data["observations"])) == (21, 20, 1)
    assert "private-" not in draft["payload"] and token not in draft["payload"]
    assert not any(
        k in draft["payload"] for k in ("installation_id", "scope", "session_ref", "source_id")
    )
    assert not any(s.sent for s in flow.sinks.values())
    flow.send(draft["id"], draft["sha256"])
    assert flow.sinks["activity"].sent == [draft["payload"]]
    assert not flow.sinks["surveys"].sent
    assert (
        data["contributor_id"]
        == json.loads((paths.home / "reporting/installation.json").read_text())["id"]
    )


def test_activity_edit_revokes_pending_approval_and_revisions_replace(flow):
    batch = record_batch(flow, 1)
    flow.consent("sharing", True)
    first = flow.preview_activity(batch["week"])
    assert flow.preview_activity(batch["week"])["sha256"] == first["sha256"]
    token = next(iter(batch["records"]))
    edited = {**CLASSIFICATION, "activity": {"value": "coding", "basis": "researcher_reported"}}
    flow.record(batch["week"], token, edited)
    with pytest.raises(BenchsideError):
        flow.send(first["id"], first["sha256"])
    second = flow.preview_activity(batch["week"])
    assert json.loads(second["payload"])["revision"] == 2
    assert json.loads(second["payload"])["batch_id"] == json.loads(first["payload"])["batch_id"]
    flow.consent("sharing", False)
    flow.consent("sharing", True)
    with pytest.raises(BenchsideError):
        flow.send(second["id"], second["sha256"])


def test_scope_change_invalidates_pending_approval_and_prevents_reading_removed_scope(flow):
    batch = record_batch(flow, 1)
    flow.consent("sharing", True)
    draft = flow.preview_activity(batch["week"])
    flow.scopes([])
    for call in (
        lambda: flow.batch(batch["week"]),
        lambda: flow.send(draft["id"], draft["sha256"]),
    ):
        with pytest.raises(BenchsideError):
            call()


def test_failed_submission_can_retry_identical_bytes_but_not_changed_destination(flow):
    draft = survey(flow)
    sink = flow.sinks["surveys"]
    sink.fail = True
    with pytest.raises(InfrastructureError):
        flow.send(draft["id"], draft["sha256"])
    assert not flow.state.receipts
    sink.destination = "https://changed.example/v1/surveys"
    with pytest.raises(BenchsideError):
        flow.send(draft["id"], draft["sha256"])
    sink.destination = draft["destination"]
    sink.fail = False
    flow.send(draft["id"], draft["sha256"])
    assert sink.sent == [draft["payload"], draft["payload"]]


@pytest.mark.parametrize(
    "field,value",
    [
        ("outcome", {"value": "helpful", "basis": "model_inferred"}),
        ("outcome", {"value": "helpful", "basis": "unknown"}),
        ("activity", {"value": "unknown", "basis": "model_inferred"}),
        ("transcript", "Private transcript"),
    ],
)
def test_no_raw_text_or_inferred_scientific_success(field, value):
    with pytest.raises(SchemaError):
        Classification.model_validate({**CLASSIFICATION, field: value})


def test_native_state_restores_observer_without_setup_or_persona():
    snapshot = run_native({"action": "native.create"})["snapshot"]

    def run(command):
        nonlocal snapshot
        candidate = run_native(
            {
                "action": "native.run",
                "workspace_id": snapshot["workspace_id"],
                "document": snapshot,
                "request": command,
            }
        )
        assert candidate["ok"], candidate
        snapshot = candidate["snapshot"]
        assert run_native(
            {
                "action": "native.confirm",
                "workspace_id": snapshot["workspace_id"],
                "document": snapshot,
                "expected": reference(snapshot),
            }
        )["saved"]
        return candidate["result"]

    run({"action": "metascience.consent", "choice": "analysis", "enabled": True})
    run({"action": "metascience.scopes", "scopes": [SCOPE]})
    batch = run({"action": "metascience.sample", "candidates": candidates(1)})
    token = next(iter(batch["selected"]))
    run(
        {
            "action": "metascience.record",
            "week": batch["week"],
            "token": token,
            "classification": CLASSIFICATION,
        }
    )
    restored = run({"action": "metascience.batch", "week": batch["week"]})
    assert restored["records"][token]["outcome"]["basis"] == "unknown"
    assert not run({"action": "metascience.status"})["choices"]["sharing"]
    run({"action": "metascience.consent", "choice": "analysis", "enabled": False})
    # A fresh App is used for every native transaction; revoked state is restored too.
    candidate = run_native(
        {
            "action": "native.run",
            "workspace_id": snapshot["workspace_id"],
            "document": snapshot,
            "request": {"action": "metascience.batch", "week": batch["week"]},
        }
    )
    assert not candidate["ok"]


def test_app_adapter_validates_requests_without_creating_research_sessions(paths):
    app = App(paths)
    with pytest.raises(BenchsideError):
        app.run({"action": "metascience.consent", "choice": "analysis", "enabled": "true"})
    app.run({"action": "metascience.consent", "choice": "analysis", "enabled": True})
    assert app.run({"action": "metascience.status"})["choices"]["analysis"]
    assert not (paths.home / "projects").exists()


def test_aggregate_report_deduplicates_revisions_without_linking_people(flow, tmp_path):
    batch = record_batch(flow)
    flow.consent("sharing", True)
    old = flow.preview_activity(batch["week"])
    token = next(iter(batch["records"]))
    new = flow.preview_activity(batch["week"], [token])
    response = survey(flow)
    files = []
    for i, draft in enumerate([old, new, new, response, response]):
        path = tmp_path / f"{i}.json"
        path.write_text(draft["payload"])
        files.append(path)
    report = summarise(files)
    assert report["activity_batches"] == 1
    assert report["activity_coverage"] == {
        "eligible_in_submitted_batches": 21,
        "selected_in_submitted_batches": 20,
        "reviewed_and_shared": 1,
    }
    assert report["survey_submissions"] == 1 and report["active_installations"] == 0
    assert report["activity_findings"]["activity/analysis/model_inferred"] == 1
    conflict = json.loads(new["payload"])
    conflict["observations"][0]["host"] = "chatgpt"
    extra = tmp_path / "conflict.json"
    extra.write_text(json.dumps(conflict))
    report = summarise([*files, extra])
    assert report["conflicting_snapshots"] == 1 and report["activity_batches"] == 0


def test_study_client_sends_no_identifiers_and_rejects_oversized_catalog():
    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def read(self, size):
            assert size == 131073
            return b" " * size

    class Opener:
        def open(self, request, timeout):
            assert request.full_url == "https://collector.example/v1/studies"
            assert request.data is None and request.get_method() == "GET" and timeout == 10
            assert request.get_header("User-agent") == f"Benchside/{__version__}"
            return Response()

    with pytest.raises(InfrastructureError):
        StudyClient("https://collector.example/v1/studies", opener=Opener()).fetch()


def test_shared_metascience_fixtures_match_python_contracts():
    directory = Path(__file__).parents[2] / "fixtures/metascience"
    study = StudyCatalog.model_validate_json((directory / "catalog.json").read_text()).studies[0]
    response = SurveyPayload.model_validate_json((directory / "survey.json").read_text())
    response.check_study(study)
    ActivityPayload.model_validate_json((directory / "activity.json").read_text())
