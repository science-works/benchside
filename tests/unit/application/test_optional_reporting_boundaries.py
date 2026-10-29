from datetime import date

import pytest

from benchside.application.app import App
from benchside.application.metascience import Metascience
from benchside.application.sharing import SharingFlow
from benchside.cli.main import main
from benchside.cli.runtime import recording_provenance
from benchside.config import Paths
from benchside.domain.consultation.event import ConsultationOpened
from benchside.domain.export.event.reporting import UsageFailureRecorded
from benchside.domain.export.model.reporting import UsagePayload
from benchside.domain.export.service.reporting import REPORTING_PROJECT
from benchside.domain.shared.error import BenchsideError, ConfigurationError
from benchside.domain.shared.model.ids import PersonaId, ProjectId
from benchside.infrastructure.http_sink import HttpExportSink
from benchside.infrastructure.journal.store import JsonlJournal


def test_analysis_reenable_requires_explicit_source_reselection(paths):
    flow = Metascience(paths, today=date(2026, 10, 27))
    scope = {"host": "claude", "source_id": "synthetic-source"}
    flow.consent("analysis", True)
    flow.scopes([scope])
    sample = flow.sample([{"scope": scope, "session_ref": "synthetic-session"}])
    flow.consent("analysis", False)
    assert flow.status()["scopes"] == []
    restored = Metascience(paths, today=date(2026, 10, 27))
    restored.consent("analysis", True)
    assert restored.status()["scopes"] == []
    with pytest.raises(BenchsideError, match="Select accessible"):
        restored.sample([{"scope": scope, "session_ref": "synthetic-session"}])
    with pytest.raises(BenchsideError, match="was retired"):
        restored.batch(sample["week"])
    # A fresh choice cannot redraw or restore a withdrawn week's sample.
    restored.scopes([scope])
    with pytest.raises(BenchsideError, match="was retired"):
        restored.batch(sample["week"])


def test_reenable_does_not_restore_scopes_from_a_legacy_revocation(paths):
    flow = Metascience(paths)
    flow.consent("analysis", True)
    scope = {"host": "claude", "source_id": "synthetic-source"}
    flow.scopes([scope])
    # Before this fix revocation removed only the grant, retaining old scopes.
    flow._save(grants={})
    restored = Metascience(paths)
    assert restored.status()["scopes"] == [scope]
    restored.consent("analysis", True)
    assert restored.status()["scopes"] == []
    restored.scopes([scope])
    restored.consent("analysis", True)
    assert restored.status()["scopes"] == [scope]  # Repeating an active choice is idempotent.


def test_bad_optional_endpoints_do_not_block_setup_preferences_or_science(paths, monkeypatch):
    for channel in ("gaps", "feedback", "usage", "studies", "surveys", "activity"):
        monkeypatch.setenv(f"BENCHSIDE_{channel.upper()}_ENDPOINT", "http://unsafe.invalid")

    def no_network(*_args):
        raise AssertionError("Private work must not attempt a submission")

    monkeypatch.setattr(HttpExportSink, "send", no_network)
    app = App(paths)
    setup = app.run({"action": "setup", "project_key": "synthetic-project"})
    context = {key: setup[key] for key in ("project_id", "session_id")}
    assert app.run({"action": "participation.status"})["response"] == "unasked"
    app.run({"action": "participation.set", "response": "declined"})
    app.run({"action": "profile.set", "demographics": {}, "include_in_usage": False})
    assert not any(app.run({"action": "metascience.status"})["choices"].values())
    sitting = app.run({"action": "start", "role": "methods-clinic", **context})
    app.run(
        {
            "action": "decide",
            **context,
            "sitting_id": sitting["sitting"]["id"],
            "decision": "Synthetic private decision",
            "rationale": "Synthetic reason",
        }
    )
    recall = app.run({"action": "recall", "project_id": setup["project_id"]})
    assert recall["recent_decisions"][0]["decision"] == "Synthetic private decision"


def test_only_selected_channel_is_validated_and_invalid_send_stays_local(paths, monkeypatch):
    monkeypatch.setenv("BENCHSIDE_FEEDBACK_ENDPOINT", "http://unsafe.invalid")
    flow = SharingFlow(paths)
    flow.set_consent("usage", True)
    usage = flow.prepare("usage")[0]
    assert usage.preview.destination.endswith("/v1/usage")
    flow.set_consent("feedback", True)
    feedback = flow.feedback(ease=4, would_use_again="yes", comment="Synthetic feedback")
    before = set((paths.home / "sharing/drafts").glob("*.json"))
    with pytest.raises(ConfigurationError):
        flow.prepare("feedback", feedback_id=feedback.id)
    assert set((paths.home / "sharing/drafts").glob("*.json")) == before
    monkeypatch.setenv("BENCHSIDE_USAGE_ENDPOINT", "http://unsafe.invalid")
    with pytest.raises(ConfigurationError):
        flow.send(usage.id, usage.preview.payload_sha256)
    assert flow.history() == []
    assert flow.load(usage.id) == usage


def test_custom_roles_and_legacy_versions_do_not_block_other_usage(paths):
    flow = SharingFlow(paths)
    pid = ProjectId("synthetic-legacy")
    for i, (role, role_version, app_version) in enumerate(
        [
            ("pi", "1", "2.0"),
            ("private-custom-reviewer", "1", "2.0"),
            ("methods-clinic", "legacy-private-label", "2.0"),
            ("study-design", "2", "private legacy app name"),
        ]
    ):
        flow.journal.append(
            pid,
            ConsultationOpened(
                id=f"open-{i}",
                consultation_id=f"sitting-{i}",
                project_id=pid,
                persona_id=PersonaId(role),
                persona_version=role_version,
                host="claude",
                surface="cli",
                app_version=app_version,
            ),
        )
    original = paths.journal_file(pid.root).read_bytes()
    flow.set_consent("usage", True)
    draft = flow.prepare("usage")[0]
    payload = UsagePayload.model_validate_json(draft.preview.payload)
    assert {(r.role, r.role_version, r.app_version) for r in payload.sessions} == {
        ("pi", "1", "2.0"),
        ("study-design", "2", "unknown"),
    }
    assert all(row.started == 1 for row in payload.sessions)
    assert "private" not in draft.preview.payload
    assert paths.journal_file(pid.root).read_bytes() == original


@pytest.mark.parametrize(
    "field,value",
    [
        ("HOST", "local-agent-name"),
        ("APP_VERSION", "Claude Desktop"),
        ("SURFACE", "IDE"),
    ],
)
def test_cli_normalizes_only_invalid_metadata_field(monkeypatch, field, value):
    monkeypatch.setenv("BENCHSIDE_HOST", "claude")
    monkeypatch.setenv("BENCHSIDE_APP_VERSION", "1.2.3")
    monkeypatch.setenv("BENCHSIDE_SURFACE", "cli")
    monkeypatch.setenv(f"BENCHSIDE_{field}", value)
    expected = {"host": "claude", "app_version": "1.2.3", "surface": "cli"}
    expected[field.lower()] = "unknown"
    assert recording_provenance().model_dump() == expected


def test_cli_scientific_record_succeeds_with_malformed_optional_metadata(tmp_path, monkeypatch):
    project, home = tmp_path / "project", tmp_path / "home"
    (project / ".bench").mkdir(parents=True)
    (project / ".bench/config.yaml").write_text("project: synthetic\n")
    monkeypatch.setenv("BENCHSIDE_HOME", str(home))
    monkeypatch.setenv("BENCHSIDE_SESSION_ID", "synthetic-session")
    monkeypatch.delenv("BENCH_SITTING", raising=False)
    monkeypatch.setenv("BENCHSIDE_HOST", "unknown-agent")
    monkeypatch.setenv("BENCHSIDE_APP_VERSION", "private legacy version label")
    monkeypatch.setenv("BENCHSIDE_SURFACE", "IDE")
    monkeypatch.chdir(project)
    assert main(["sitting", "open", "--persona", "methods-clinic"]) == 0
    assert main(["decide", "Synthetic private decision", "--because", "Synthetic reason"]) == 0
    journal = JsonlJournal(Paths(home=home, repo_root=project))
    events = list(journal.read(ProjectId("synthetic")))
    assert len(events) == 2
    assert all(
        event.provenance.model_dump()
        == {
            "host": "unknown",
            "app_version": "unknown",
            "surface": "unknown",
        }
        for event in events
    )


def test_empty_workflow_preview_creates_no_draft_or_failure_count(paths):
    flow = SharingFlow(paths)
    flow.set_consent("gaps", True, kinds=["missing_index"])
    flow.set_consent("usage", True)
    with pytest.raises(BenchsideError, match="No selected, unshared"):
        flow.prepare("gaps")
    assert not (paths.home / "sharing/drafts").exists()
    assert not any(
        isinstance(event, UsageFailureRecorded) for event in flow.journal.read(REPORTING_PROJECT)
    )
