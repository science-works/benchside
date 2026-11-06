"""Executable reproductions for the 6 November review, using private fixtures."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from benchside.application.app import App
from benchside.application.contributions import contributor_id
from benchside.application.native import _digest, pack, unpack
from benchside.config import Paths
from benchside.domain.export.model.reporting import ResearchProfile
from benchside.domain.export.model.metascience import MetaDraft, MetaState
from benchside.domain.shared.error import BenchsideError
from benchside.infrastructure import readable_records, storage_layout
from tests.unit.application.test_linked_contributions import join_text_study
from tests.unit.application.test_metascience import flow as flow  # noqa: PLC0414


@pytest.mark.parametrize("invalid", ["{", "[]", "null", "{}", '{"id": 7}', '{"id": "wrong"}'])
def test_malformed_contributor_identity_is_preserved_for_repair(paths, invalid):
    path = paths.home / "reporting/installation.json"
    path.parent.mkdir(parents=True)
    path.write_text(invalid)
    with pytest.raises(BenchsideError, match="preserve and repair"):
        contributor_id(paths)
    assert path.read_text() == invalid


@pytest.mark.parametrize("answer", ["", " ", "\n\t"])
def test_blank_survey_answer_is_rejected_before_creating_draft(flow, answer):
    key = join_text_study(flow)
    before = flow.path.read_bytes()
    with pytest.raises(ValueError):
        flow.survey(key, {"comment": {"text": answer}})
    assert flow.path.read_bytes() == before
    assert not flow.sinks["surveys"].sent


@pytest.mark.parametrize("answer", ["Contact synthetic@example.org", "My token is sk-" + "x" * 40])
def test_sensitive_survey_answer_requires_edit_before_draft(flow, answer):
    key = join_text_study(flow)
    before = flow.path.read_bytes()
    with pytest.raises(BenchsideError, match="[Ee]dit"):
        flow.survey(key, {"comment": {"text": answer}})
    assert flow.path.read_bytes() == before
    assert not flow.sinks["surveys"].sent


@pytest.mark.parametrize("answer", ["synthetic@example.org", " \n\t"])
def test_older_pending_survey_draft_restores_but_cannot_send_flagged_or_blank_text(flow, answer):
    key = join_text_study(flow)
    draft = flow.survey(key, {"comment": {"text": "Clean synthetic answer"}})
    payload = json.loads(draft["payload"])
    payload["answers"]["comment"]["text"] = answer
    draft["payload"] = json.dumps(payload)
    draft["sha256"] = hashlib.sha256(draft["payload"].encode()).hexdigest()
    old = MetaDraft.model_validate(draft)
    flow._save(drafts={old.id: old})
    # Old persisted records must remain readable, including their exact payload.
    assert MetaState.model_validate_json(flow.path.read_text()).drafts[old.id] == old
    with pytest.raises((BenchsideError, ValueError)):
        flow.send(old.id, old.sha256)
    assert not flow.sinks["surveys"].sent
    assert flow.state.drafts[old.id] == old


def test_app_refreshes_once_after_all_events(tmp_path, monkeypatch):
    root = tmp_path / "private"
    app = App(Paths(home=root, store_root=root, repo_root=tmp_path))
    setup = app.run({"action": "setup", "project_key": "synthetic"})
    context = {k: setup[k] for k in ("project_id", "session_id")}
    context["sitting_id"] = app.run({"action": "start", "role": "pi", **context})["sitting"]["id"]
    dispatch = app._dispatch

    def two_events(action, request):
        result = dispatch(action, request)
        dispatch(action, {**request, "decision": "Second decision"})
        return result

    monkeypatch.setattr(app, "_dispatch", two_events)
    with patch.object(readable_records, "export_project", wraps=readable_records.export_project) as export:
        app.run({"action": "decide", **context, "decision": "First decision", "rationale": "Synthetic"})
    assert export.call_count == 1


def body_with_profile(discipline):
    profile = ResearchProfile(demographics={"discipline": discipline})
    return {"files": {"reporting/profile.json": profile.model_dump_json()}, "projects": {}, "operations": {}}


def relabel(snapshot, schema):
    unsigned = {**snapshot, "schema": schema}
    unsigned.pop("sha256")
    return {**unsigned, "sha256": _digest(unsigned)}


def test_multidiscipline_snapshot_requests_new_runtime():
    body = body_with_profile(["life_sciences", "computer_information_sciences"])
    snapshot = pack(body, "a" * 32, 1)
    assert snapshot["schema"] == "benchside.native.v4"
    assert unpack(snapshot)[1] == body
    # Released 0.4.0 already wrote these under v1-v3: preserve those notebooks
    # and upgrade their label on the next save rather than calling them corrupt.
    old_body = unpack(relabel(snapshot, "benchside.native.v1"))[1]
    assert pack(old_body, "a" * 32, 2)["schema"] == "benchside.native.v4"


def test_legacy_profile_keeps_legacy_native_schema():
    assert pack(body_with_profile("life_sciences"), "a" * 32, 1)["schema"] == "benchside.native.v1"


def test_hypothesis_role_usage_requires_new_schema():
    fixture = Path(__file__).resolve().parents[2] / "fixtures/reporting/benchside-usage.json"
    usage = json.loads(fixture.read_text())
    usage["sessions"][0]["role"] = "pi-hypothesis"
    body = {"files": {f"reporting/usage-{usage['week']}.json": json.dumps(usage)}, "projects": {}, "operations": {}}
    snapshot = pack(body, "a" * 32, 1)
    assert snapshot["schema"] == "benchside.native.v4"
    assert unpack(snapshot)[1] == body


@pytest.mark.parametrize("schema", ["benchside.native.v1", "benchside.native.v2"])
def test_context_cannot_be_hidden_under_older_schema(schema):
    body = {"files": {}, "projects": {}, "operations": {
        "b" * 32: {"request_sha256": "c" * 64, "result": {"kind": "missing_index", "context": {"tool_name": "Synthetic"}}}
    }}
    snapshot = pack(body, "a" * 32, 1)
    assert snapshot["schema"] == "benchside.native.v3"
    with pytest.raises(BenchsideError, match="schema"):
        unpack(relabel(snapshot, schema))


def test_checkpoint_cannot_be_hidden_under_v1():
    body = {"files": {}, "projects": {}, "operations": {}, "replay": {"generation": 1}}
    snapshot = pack(body, "a" * 32, 1)
    with pytest.raises(BenchsideError, match="schema"):
        unpack(relabel(snapshot, "benchside.native.v1"))


@pytest.mark.parametrize("schema", ["benchside.native.v2", "benchside.native.v3", "benchside.native.v4"])
def test_newer_schema_with_no_optional_feature_still_restores(schema):
    body = {"files": {}, "projects": {}, "operations": {}}
    snapshot = relabel(pack(body, "a" * 32, 0), schema)
    assert unpack(snapshot)[1] == body


def test_migration_detects_write_to_already_copied_directory(tmp_path, monkeypatch):
    root = tmp_path / "legacy"
    (root / "projects/synthetic").mkdir(parents=True)
    original = root / "projects/synthetic/journal.jsonl"
    original.write_text("original")
    settings = root / "records-preferences.json"
    settings.write_text(json.dumps({"format": "odt"}))
    copy = storage_layout.shutil.copy2

    def concurrent_write(source, destination, *args, **kwargs):
        result = copy(source, destination, *args, **kwargs)
        if source == settings:
            original.write_text("original plus hook update")
        return result

    monkeypatch.setattr(storage_layout.shutil, "copy2", concurrent_write)
    with pytest.raises((BenchsideError, OSError)):
        storage_layout.organise(root, True)
    assert original.read_text() == "original plus hook update"
    assert not (root / "agent").exists()
    assert not (root / storage_layout.MARKER).exists()


def test_hook_holds_layout_lock_without_global_transaction_lock(tmp_path, monkeypatch):
    import fcntl
    import io
    from types import SimpleNamespace

    from benchside.cli import hooks

    root = tmp_path / "private"
    root.mkdir()
    config = tmp_path / "project/.bench/config.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("project: synthetic\n")
    monkeypatch.setenv("BENCHSIDE_HOME", str(root))
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"cwd": str(config.parent.parent)})))
    held = []

    def inspect_lock(payload):
        with (root / ".layout.lock").open("a") as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                held.append(True)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)

    monkeypatch.setattr(hooks, "_session_start", inspect_lock)
    assert hooks.cmd_hook(SimpleNamespace(event="session-start")) == 0
    assert held == [True]
