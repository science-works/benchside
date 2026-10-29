"""Usage follows the recording app while scientific sitting identity stays stable."""

import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from benchside.application.app import App
from benchside.application.native import markdown, pack, run_native, unpack
from benchside.cli.main import main
from benchside.config import Paths
from benchside.domain.consultation.event import ConsultationOpened
from benchside.domain.export.event.reporting import ReportingConsentChanged
from benchside.domain.export.service.reporting import ReportingService, week_start
from benchside.domain.shared.model.ids import CONSENT_LEDGER_PROJECT, PersonaId, ProjectId
from benchside.domain.shared.model.provenance import AppProvenance
from benchside.infrastructure.journal.store import JsonlJournal
from benchside.infrastructure.session_context import recording_context


def usage(journal):
    return ReportingService(journal=journal).usage_payload(
        installation_id="0" * 32,
        report_id="1" * 32,
        week=week_start(),
        revision=1,
        version="0.1.1",
    )


def assert_attribution(payload, second_host, second_version, *, surface="desktop"):
    rows = {(r.host, r.app_version, r.surface): r for r in payload.sessions}
    assert set(rows) == {("chatgpt", "1.0", "web"), (second_host, second_version, surface)}
    original = rows[("chatgpt", "1.0", "web")]
    resumed = rows[(second_host, second_version, surface)]
    assert original.started == 1 and original.records.decision == 0 and original.abandoned == 0
    assert resumed.started == 0 and resumed.records.decision == 1 and resumed.abandoned == 1
    assert sum(row.started for row in rows.values()) == 1


@pytest.mark.parametrize("second_host,second_version", [("claude", "2.0"), ("chatgpt", "1.1")])
def test_app_resume_and_upgrade_use_current_context(paths, second_host, second_version):
    app = App(paths)
    first = app.run(
        {
            "action": "setup",
            "project_key": "private synthetic project",
            "host": "chatgpt",
            "app_version": "1.0",
            "surface": "web",
        }
    )
    started = app.run({"action": "start", "role": "methods-clinic", **first})
    second = app.run(
        {
            "action": "setup",
            "project_id": first["project_id"],
            "host": second_host,
            "app_version": second_version,
            "surface": "desktop",
        }
    )
    resumed = app.run({"action": "start", "role": "methods-clinic", **second})
    assert resumed["sitting"]["id"] == started["sitting"]["id"]
    context = {**second, "sitting_id": resumed["sitting"]["id"]}
    app.run(
        {
            "action": "decide",
            "decision": "Private synthetic decision",
            "rationale": "Private",
            **context,
        }
    )
    app.run({"action": "close", "converged": False, "detail": "Private reason", **context})
    payload = usage(app.journal)
    assert_attribution(payload, second_host, second_version)
    exported = payload.model_dump_json()
    for private in (
        "Private",
        first["project_id"],
        first["session_id"],
        second["session_id"],
        context["sitting_id"],
        "provenance",
    ):
        assert private not in exported


def test_native_restore_preserves_legacy_and_new_provenance():
    document = run_native({"action": "native.create"})["markdown"]

    def run(command, project=None):
        nonlocal document
        result = run_native(
            {
                "action": "native.run",
                "document": document,
                "workspace_id": unpack(document)[0]["workspace_id"],
                "request": command,
                "operation_id": uuid.uuid4().hex,
                **({"project_document": project} if project else {}),
            }
        )
        assert result["ok"]
        document = result["markdown"]
        return result["result"]

    project = {"document_id": "synthetic-native-journal", "title": "Synthetic"}
    first = run(
        {
            "action": "setup",
            "project_key": project["document_id"],
            "host": "chatgpt",
            "app_version": "1.0",
            "surface": "web",
        },
        project,
    )
    start = run({"action": "start", "role": "methods-clinic", **first})
    # Simulate a notebook from the release preceding per-event provenance.
    snapshot, body = unpack(document)
    journal_path = f"projects/{first['project_id']}/journal.jsonl"
    envelopes = [json.loads(line) for line in body["files"][journal_path].splitlines()]
    for envelope in envelopes:
        envelope["data"].pop("provenance", None)
    body["files"][journal_path] = "".join(json.dumps(e) + "\n" for e in envelopes)
    document = markdown(pack(body, snapshot["workspace_id"], snapshot["revision"]))

    second = run(
        {
            "action": "setup",
            "project_id": first["project_id"],
            "host": "claude",
            "app_version": "2.0",
            "surface": "desktop",
        },
        project,
    )
    resumed = run({"action": "start", "role": "methods-clinic", **second})
    assert resumed["sitting"]["id"] == start["sitting"]["id"]
    context = {**second, "sitting_id": resumed["sitting"]["id"]}
    run({"action": "decide", "decision": "Synthetic", "rationale": "Synthetic", **context})
    run({"action": "close", "converged": False, "detail": "Synthetic", **context})
    run({"action": "sharing.consent", "channel": "usage", "enabled": True})
    draft = run({"action": "sharing.preview", "channel": "usage"})[0]
    from benchside.domain.export.model.reporting import UsagePayload

    assert_attribution(
        UsagePayload.model_validate_json(draft["preview"]["payload"]), "claude", "2.0"
    )
    # Native unpack and later calls retain the legacy journal entry unchanged.
    saved = [json.loads(line) for line in unpack(document)[1]["files"][journal_path].splitlines()]
    assert "provenance" not in saved[0]["data"]
    assert saved[-1]["data"]["provenance"]["host"] == "claude"


def test_cli_records_and_closes_under_current_app_context(tmp_path, monkeypatch):
    home, project = tmp_path / "home", tmp_path / "project"
    (project / ".bench").mkdir(parents=True)
    (project / ".bench/config.yaml").write_text("project: synthetic\n")
    monkeypatch.setenv("BENCHSIDE_HOME", str(home))
    monkeypatch.delenv("BENCH_SITTING", raising=False)
    monkeypatch.setenv("CLAUDE_SESSION_ID", "first-session")
    monkeypatch.setenv("BENCHSIDE_HOST", "chatgpt")
    monkeypatch.setenv("BENCHSIDE_APP_VERSION", "1.0")
    monkeypatch.setenv("BENCHSIDE_SURFACE", "web")
    monkeypatch.chdir(project)
    assert main(["sitting", "open", "--persona", "methods-clinic"]) == 0
    journal = JsonlJournal(Paths(home=home, repo_root=project))
    first = next(iter(journal.read(ProjectId("synthetic"))))
    monkeypatch.setenv("CLAUDE_SESSION_ID", "second-session")
    monkeypatch.setenv("BENCHSIDE_HOST", "claude")
    monkeypatch.setenv("BENCHSIDE_APP_VERSION", "2.0")
    monkeypatch.setenv("BENCHSIDE_SURFACE", "cli")
    assert main(["sitting", "resume", first.consultation_id]) == 0
    assert main(["decide", "Synthetic", "--because", "Synthetic"]) == 0
    assert main(["sitting", "close", "--abandoned", "--outcome", "Synthetic"]) == 0
    assert_attribution(usage(journal), "claude", "2.0", surface="cli")


def test_parallel_recording_contexts_do_not_share_session_or_host(paths):
    barrier = Barrier(2)
    journal = JsonlJournal(paths)

    def record(host):
        pid = ProjectId(host)
        with recording_context(session_id=f"session-{host}", provenance=AppProvenance(host=host)):
            barrier.wait(timeout=5)
            journal.append(
                pid,
                ConsultationOpened(
                    id=f"event-{host}",
                    consultation_id=f"sitting-{host}",
                    project_id=pid,
                    persona_id=PersonaId("pi"),
                ),
            )
        return next(iter(journal.read_envelopes(pid)))

    with ThreadPoolExecutor(max_workers=2) as pool:
        records = list(pool.map(record, ["chatgpt", "claude"]))
    for host, record in zip(["chatgpt", "claude"], records, strict=True):
        assert record["session"] == f"session-{host}"
        assert record["data"]["provenance"]["host"] == host


def test_provenance_is_not_added_to_the_global_consent_ledger(journal):
    with recording_context(session_id="private-session", provenance=AppProvenance(host="claude")):
        journal.append(
            CONSENT_LEDGER_PROJECT,
            ReportingConsentChanged(id="consent", channel="usage", enabled=True),
        )
    envelope = next(iter(journal.read_envelopes(CONSENT_LEDGER_PROJECT)))
    assert "provenance" not in envelope["data"]
