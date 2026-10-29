"""Private, synthetic native replay tests; no collector or analysis calls."""

import copy
import json
import uuid

import pytest

from benchside.application import native
from benchside.domain.export.event.reporting import ReportSubmitted
from benchside.domain.export.model.metascience import LEGACY_SAMPLING, MetaState
from benchside.domain.shared.error import BenchsideError

PROFILE = {"action": "profile.set", "demographics": {}, "include_in_usage": False}


class Notebook:
    def __init__(self):
        self.document = native.run_native({"action": "native.create"})["snapshot"]

    def run(self, command, *, operation_id=None, project=None, save=True):
        request = {
            "action": "native.run",
            "workspace_id": self.document["workspace_id"],
            "document": self.document,
            "request": command,
        }
        if operation_id is not None:
            request["operation_id"] = operation_id
        if project is not None:
            request["project_document"] = project
        response = native.run_native(request)
        assert response["ok"], response
        if save:
            self.document = response["snapshot"]
        return response

    def inspect(self):
        return native.run_native(
            {
                "action": "native.inspect",
                "workspace_id": self.document["workspace_id"],
                "document": self.document,
            }
        )


@pytest.fixture
def short_window(monkeypatch):
    monkeypatch.setattr(native, "MAX_OPERATION_RECEIPTS", 4)
    monkeypatch.setattr(native, "RETAIN_OPERATION_RECEIPTS", 2)


def test_replay_index_stays_bounded_across_hundreds_of_private_operations():
    book = Notebook()
    context = book.run(
        {"action": "setup", "host": "claude", "project_key": "synthetic-replay-window"},
        project={"document_id": "synthetic-replay-window", "title": "Synthetic notebook"},
    )["result"]
    started = book.run({"action": "start", "role": "methods-clinic", **context})
    book.run(
        {
            "action": "decide",
            "decision": "Keep the paired synthetic controls",
            "rationale": "Distinguish extraction from detection",
            **context,
            "sitting_id": started["result"]["sitting"]["id"],
        }
    )
    science_path = f"projects/{context['project_id']}/journal.jsonl"
    snapshot, body = native.unpack(book.document)
    science = body["files"][science_path]
    receipt_path = "projects/consent-ledger/journal.jsonl"
    receipt = ReportSubmitted(
        id=str(uuid.uuid4()),
        channel="feedback",
        grant_id="synthetic-grant",
        submission_id="synthetic-receipt",
        payload_sha256="a" * 64,
        destination="https://collector.invalid/v1/feedback",
        received_at="2026-10-27T12:00:00+00:00",
    )
    receipt_line = (
        native._json(
            {"type": "ReportSubmitted", "session": None, "data": receipt.model_dump(mode="json")}
        )
        + "\n"
    )
    body["files"][receipt_path] = receipt_line
    book.document = native.pack(body, snapshot["workspace_id"], snapshot["revision"])
    for _ in range(300):
        recent = book.run(PROFILE)
    body = native.unpack(book.document)[1]
    assert len(body["operations"]) <= 128
    assert len(native._json(body["operations"]).encode()) <= 64 * 1024
    assert body["files"][science_path] == science
    assert body["files"][receipt_path] == receipt_line
    assert json.loads(body["files"]["reporting/profile.json"])["revision"] == 300
    replay = book.run(PROFILE, operation_id=recent["operation_id"])
    assert replay["replayed"] and not replay["changed"]
    assert replay["result"] == recent["result"]


def test_legacy_migration_retains_recent_replay_and_rejects_changed_inputs(short_window):
    book = Notebook()
    assert book.inspect()["operation_generation"] == 0
    legacy_ids = []
    for _ in range(4):
        response = book.run(PROFILE)
        legacy_ids.append(response["operation_id"])
        assert response["snapshot"]["schema"] == "benchside.native.v1"
        assert not response["replay_checkpointed"]
        assert "replay" not in native.unpack(book.document)[1]
    checkpoint = book.run(PROFILE)
    assert checkpoint["replay_checkpointed"]
    assert checkpoint["snapshot"]["schema"] == "benchside.native.v2"
    assert checkpoint["operation_generation"] == book.inspect()["operation_generation"] == 1
    assert len(native.unpack(book.document)[1]["operations"]) == 2
    replay = book.run(PROFILE, operation_id=legacy_ids[-1])
    assert replay["replayed"] and not replay["changed"]
    with pytest.raises(BenchsideError, match="different request"):
        book.run({**PROFILE, "include_in_usage": True}, operation_id=legacy_ids[-1])
    fresh = book.run(PROFILE)
    assert fresh["operation_id"].startswith("g1-")
    assert not fresh["replayed"]
    with pytest.raises(BenchsideError) as caught:
        book.run(PROFILE, operation_id=uuid.uuid4().hex)
    assert caught.value.code == "native_operation_expired"


@pytest.mark.parametrize("action", ["profile.set", "sharing.send", "metascience.send"])
@pytest.mark.parametrize("committed", [False, True])
def test_expired_operation_never_reaches_preflight_or_execution(
    short_window, monkeypatch, action, committed
):
    book = Notebook()
    operation_id = uuid.uuid4().hex
    if committed:
        book.run(PROFILE, operation_id=operation_id)
    while book.inspect()["operation_generation"] == 0:
        book.run(PROFILE)
    before = copy.deepcopy(book.document)

    def refuse(*args, **kwargs):
        raise AssertionError(
            "Expired IDs must be rejected before execution or submission preflight"
        )

    monkeypatch.setattr(native, "_execute", refuse)
    monkeypatch.setattr(native, "_preflight_submission", refuse)
    # Merely name external actions to test the boundary; no collector, draft,
    # consent, activity-analysis or network code is executed in this test.
    command = PROFILE if action == "profile.set" else {"action": action}
    with pytest.raises(BenchsideError) as caught:
        book.run(command, operation_id=operation_id)
    assert caught.value.code == "native_operation_expired"
    assert "reconcile" in str(caught.value)
    assert "Do not automatically retry with a new operation ID" in str(caught.value)
    assert book.document == before


def test_generation_prefixed_operations_also_expire_after_later_checkpoints(short_window):
    book = Notebook()
    while book.inspect()["operation_generation"] == 0:
        book.run(PROFILE)
    old = book.run(PROFILE)
    assert old["operation_id"].startswith("g1-")
    while book.inspect()["operation_generation"] < 3:
        book.run(PROFILE)
    with pytest.raises(BenchsideError) as caught:
        book.run(PROFILE, operation_id=old["operation_id"])
    assert caught.value.code == "native_operation_expired"


def test_batch_auto_ids_use_active_generation_and_expired_batches_do_not_execute(
    short_window, monkeypatch
):
    book = Notebook()
    while book.inspect()["operation_generation"] == 0:
        book.run(PROFILE)
    request = {
        "action": "native.batch",
        "document": book.document,
        "workspace_id": book.document["workspace_id"],
        "steps": [
            {"id": "profile", "request": PROFILE},
            {"id": "status", "request": {"action": "profile.status"}},
        ],
    }
    result = native.run_native(request)
    assert result["ok"] and result["operation_id"].startswith("g1-")
    assert result["result"]["steps"]["status"]["revision"] == 6
    request.update(document=result["snapshot"], operation_id=result["operation_id"])
    replay = native.run_native(request)
    assert replay["replayed"] and not replay["changed"]
    assert replay["result"] == result["result"]

    def refuse(*args, **kwargs):
        raise AssertionError("An expired batch must not execute any step")

    monkeypatch.setattr(native, "_execute_batch", refuse)
    request["operation_id"] = uuid.uuid4().hex
    with pytest.raises(BenchsideError) as caught:
        native.run_native(request)
    assert caught.value.code == "native_operation_expired"


def test_checkpoint_is_only_committed_by_guarded_host_save(short_window):
    book = Notebook()
    for _ in range(4):
        book.run(PROFILE)
    before = copy.deepcopy(book.document)
    operation_id = uuid.uuid4().hex
    pending = book.run(PROFILE, operation_id=operation_id, save=False)
    assert pending["replay_checkpointed"]
    assert not pending["saved"] and book.inspect()["operation_generation"] == 0
    with pytest.raises(BenchsideError, match="not confirmed"):
        native.run_native(
            {
                "action": "native.confirm",
                "document": book.document,
                "workspace_id": book.document["workspace_id"],
                "expected": native.reference(pending["snapshot"]),
            }
        )
    assert book.document == before
    retried = book.run(PROFILE, operation_id=operation_id)
    assert retried["snapshot"] == pending["snapshot"]
    confirmed = native.run_native(
        {
            "action": "native.confirm",
            "document": book.document,
            "workspace_id": book.document["workspace_id"],
            "expected": native.reference(retried["snapshot"]),
        }
    )
    assert confirmed["saved"]
    replay = book.run(PROFILE, operation_id=operation_id)
    assert replay["replayed"] and not replay["changed"]
    assert replay["result"]["revision"] == 5


def test_unsaved_request_cannot_rebase_across_another_chats_checkpoint(short_window):
    book = Notebook()
    for _ in range(4):
        book.run(PROFILE)
    operation_id = uuid.uuid4().hex
    pending = book.run(PROFILE, operation_id=operation_id, save=False)
    other = book.run(PROFILE)
    assert other["replay_checkpointed"]
    assert pending["snapshot"]["sha256"] != other["snapshot"]["sha256"]
    with pytest.raises(BenchsideError) as caught:
        book.run(PROFILE, operation_id=operation_id)
    assert caught.value.code == "native_operation_expired"
    assert (
        json.loads(native.unpack(book.document)[1]["files"]["reporting/profile.json"])["revision"]
        == 5
    )


def test_legacy_large_compacted_results_cannot_exceed_index_byte_budget():
    book = Notebook()
    snapshot, body = native.unpack(book.document)
    old_ids = []
    for revision in range(30):
        identifier = uuid.uuid4().hex
        old_ids.append(identifier)
        body["operations"][identifier] = {
            "request_sha256": native._digest({"request": PROFILE, "project_document": None}),
            "revision": revision,
            "result_compacted": True,
            "result": {
                "steps": {
                    f"step_{index}": {
                        "id": uuid.uuid4().hex,
                        "project_id": "p-" + uuid.uuid4().hex,
                        "session_id": uuid.uuid4().hex,
                    }
                    for index in range(16)
                }
            },
        }
    assert len(native._json(body["operations"]).encode()) > 64 * 1024
    book.document = native.pack(body, snapshot["workspace_id"], 30)
    result = book.run(PROFILE)
    assert result["replay_checkpointed"]
    migrated = native.unpack(book.document)[1]
    assert len(native._json(migrated["operations"]).encode()) <= 64 * 1024
    assert len(migrated["operations"]) < 30
    with pytest.raises(BenchsideError) as caught:
        book.run(PROFILE, operation_id=old_ids[0])
    assert caught.value.code == "native_operation_expired"


@pytest.mark.parametrize("selection", ["random", "user_selected"])
def test_new_sampling_format_checkpoints_before_old_readers_decode_it(selection):
    book = Notebook()
    scope = {"host": "claude", "source_id": "synthetic-source"}
    book.run({"action": "metascience.consent", "choice": "analysis", "enabled": True})
    book.run({"action": "metascience.scopes", "scopes": [scope]})
    before = copy.deepcopy(book.document)
    old_receipts = native.unpack(before)[1]["operations"]
    command = {
        "action": "metascience.sample",
        "selection": selection,
        "candidates": [{"scope": scope, "session_ref": "synthetic-conversation"}],
    }

    pending = book.run(command, save=False)

    assert before["schema"] == "benchside.native.v1"
    assert pending["snapshot"]["schema"] == "benchside.native.v2"
    assert pending["operation_generation"] == 1 and pending["replay_checkpointed"]
    assert book.document == before and not pending["saved"]
    current_receipts = native.unpack(pending["snapshot"])[1]["operations"]
    assert set(current_receipts) == set(old_receipts) | {pending["operation_id"]}
    assert all(current_receipts[key] == value for key, value in old_receipts.items())
    book.document = pending["snapshot"]
    replay = book.run(command, operation_id=pending["operation_id"])
    assert replay["replayed"] and not replay["changed"]
    assert replay["result"] == pending["result"]
    assert book.run(PROFILE)["operation_id"].startswith("g1-")


def _legacy_sample_book():
    book = Notebook()
    book.run(PROFILE)
    snapshot, body = native.unpack(book.document)
    state = MetaState(seed="a" * 32).model_dump(mode="json")
    state["samples"]["2026-10-19"] = {
        "id": "b" * 32,
        "inventory_sha256": "c" * 64,
        "eligible": 0,
        "selected": {},
        "records": {},
        "revision": 0,
    }
    body["files"]["metascience/state.json"] = json.dumps(state)
    book.document = native.pack(body, snapshot["workspace_id"], snapshot["revision"])
    return book


def test_rewriting_legacy_sample_with_explicit_legacy_tag_checkpoints():
    book = _legacy_sample_book()
    before = copy.deepcopy(book.document)
    # A read can expose the default method without changing the old saved bytes.
    read = book.run({"action": "metascience.status"})
    assert not read["changed"] and book.document == before
    assert read["operation_generation"] == 0

    written = book.run({"action": "metascience.consent", "choice": "invitations", "enabled": True})

    assert written["snapshot"]["schema"] == "benchside.native.v2"
    assert written["operation_generation"] == 1 and written["replay_checkpointed"]
    body = native.unpack(book.document)[1]
    sample = json.loads(body["files"]["metascience/state.json"])["samples"]["2026-10-19"]
    assert sample["sampling"] == LEGACY_SAMPLING
    assert set(native.unpack(before)[1]["operations"]) <= set(body["operations"])


def test_failed_batch_does_not_upgrade_legacy_sampling_format():
    book = _legacy_sample_book()
    before = copy.deepcopy(book.document)
    failed = native.run_native(
        {
            "action": "native.batch",
            "workspace_id": before["workspace_id"],
            "document": before,
            "steps": [
                {
                    "id": "write",
                    "request": {
                        "action": "metascience.consent",
                        "choice": "invitations",
                        "enabled": True,
                    },
                },
                {
                    "id": "invalid",
                    "request": {
                        "action": "metascience.consent",
                        "choice": "not-a-choice",
                        "enabled": True,
                    },
                },
            ],
        }
    )
    assert not failed["ok"] and not failed["changed"]
    assert not failed["replay_checkpointed"] and failed["operation_generation"] == 0
    assert failed["snapshot"] == before


def test_failed_single_action_that_retires_sampling_state_still_upgrades_saved_format():
    book = _legacy_sample_book()
    week = book.run({"action": "metascience.status"})["result"]["sampling_window"]["week"]
    snapshot, body = native.unpack(book.document)
    state = json.loads(body["files"]["metascience/state.json"])
    state["grants"] = {"analysis": "d" * 32}
    state["analysis_policy"] = "selected-research-max20-1"
    state["scopes"] = [{"host": "claude", "source_id": "current-source"}]
    sample = state["samples"].pop("2026-10-19")
    sample.update(
        eligible=1,
        selected={
            "e" * 32: {
                "scope": {"host": "claude", "source_id": "removed-source"},
                "session_ref": "synthetic-old-conversation",
            }
        },
    )
    state["samples"][week] = sample
    body["files"]["metascience/state.json"] = json.dumps(state)
    before = native.pack(body, snapshot["workspace_id"], snapshot["revision"])

    failed = native.run_native(
        {
            "action": "native.run",
            "workspace_id": before["workspace_id"],
            "document": before,
            "request": {"action": "metascience.sample", "week": week, "candidates": []},
        }
    )

    assert not failed["ok"] and failed["changed"]
    assert failed["snapshot"]["schema"] == "benchside.native.v2"
    assert failed["operation_generation"] == 1 and failed["replay_checkpointed"]
    retired = json.loads(native.unpack(failed["snapshot"])[1]["files"]["metascience/state.json"])
    assert retired["samples"][week]["selected"] == {}
