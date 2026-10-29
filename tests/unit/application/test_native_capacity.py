import base64
import copy
import hashlib
import json
import os
import uuid
import zlib

import pytest

from benchside.application import native
from benchside.domain.export.model.value import DeliveryReceipt
from benchside.domain.shared.error import BenchsideError
from benchside.infrastructure.http_sink import HttpExportSink


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("No real submissions in native capacity tests")

    monkeypatch.setattr(HttpExportSink, "send", refuse)


class Notebook:
    def __init__(self):
        self.document = native.run_native({"action": "native.create"})["markdown"]

    def run(self, command, *, project=None, operation_id=None):
        result = native.run_native(
            {
                "action": "native.run",
                "document": self.document,
                "workspace_id": native.unpack(self.document)[0]["workspace_id"],
                **({"operation_id": operation_id} if operation_id is not None else {}),
                "request": command,
                **({"project_document": project} if project else {}),
            }
        )
        self.document = result["markdown"]
        return result

    def setup(self, host="chatgpt"):
        return self.run(
            {"action": "setup", "host": host, "project_key": "synthetic-journal"},
            project={"document_id": "synthetic-journal", "title": "Synthetic"},
        )["result"]

    def batch(self, commands):
        result = native.run_native(
            {
                "action": "native.batch",
                "document": self.document,
                "workspace_id": native.unpack(self.document)[0]["workspace_id"],
                "steps": [
                    {"id": f"step_{index}", "request": command}
                    for index, command in enumerate(commands)
                ],
            }
        )
        self.document = result["markdown"]
        return result


def feedback_draft(book):
    book.run({"action": "sharing.consent", "channel": "feedback", "enabled": True})
    feedback = book.run(
        {
            "action": "sharing.feedback",
            "feedback": {"ease": 4, "would_use_again": "yes", "comment": "Synthetic"},
        }
    )["result"]
    return book.run(
        {"action": "sharing.preview", "channel": "feedback", "feedback_id": feedback["id"]}
    )["result"][0]


def fake_receipts(monkeypatch):
    submitted = []

    def send(self, payload):
        submitted.append(payload)
        return DeliveryReceipt(
            status="stored",
            sha256=hashlib.sha256(payload.encode()).hexdigest(),
            received_at="2026-10-28T12:00:00+00:00",
            observations=1,
        )

    monkeypatch.setattr(HttpExportSink, "send", send)
    return submitted


def test_response_cache_is_bounded_without_forgetting_committed_operations():
    book = Notebook()
    context = book.setup()
    context["sitting_id"] = book.run({"action": "start", "role": "methods-clinic", **context})[
        "result"
    ]["sitting"]["id"]
    receipts = []
    for index in range(12):
        operation_id = uuid.uuid4().hex
        command = {
            "action": "decide",
            "decision": f"Synthetic {index} " + "a" * 8000,
            "rationale": "Synthetic",
            **context,
        }
        result = book.run(command, operation_id=operation_id)
        assert result["ok"]
        receipts.append((operation_id, command, result["result"]["recorded"]))
    snapshot, body = native.unpack(book.document)
    cached_bytes = sum(
        len(native._json(operation["result"]).encode())
        for operation in body["operations"].values()
        if not operation.get("result_compacted")
    )
    assert cached_bytes <= native.MAX_REPLAY_CACHE_BYTES
    assert all(operation_id in body["operations"] for operation_id, _, _ in receipts)
    compacted = next(
        item for item in receipts if body["operations"][item[0]].get("result_compacted")
    )
    replay = book.run(compacted[1], operation_id=compacted[0])
    assert replay["replayed"] and replay["result_compacted"] and not replay["changed"]
    assert replay["snapshot"] == snapshot
    assert replay["result"]["recorded"] == compacted[2]
    with pytest.raises(BenchsideError, match="different request"):
        book.run({**compacted[1], "decision": "Changed"}, operation_id=compacted[0])
    journal = native.unpack(book.document)[1]["files"][
        f"projects/{context['project_id']}/journal.jsonl"
    ]
    assert (
        sum(json.loads(line)["type"] == "DecisionRecorded" for line in journal.splitlines()) == 12
    )


def test_capacity_preflight_refuses_before_post_and_preserves_approved_draft(monkeypatch):
    book = Notebook()
    draft = feedback_draft(book)
    submitted = fake_receipts(monkeypatch)
    snapshot, before = native.unpack(book.document)
    monkeypatch.setattr(
        native,
        "MAX_DOCUMENT_BYTES",
        len(native._json(snapshot).encode()) + native.DOCUMENT_CONTROL_RESERVE + 1024,
    )
    result = book.run(
        {
            "action": "sharing.send",
            "draft_id": draft["id"],
            "approved_sha256": draft["preview"]["payload_sha256"],
        }
    )
    assert not result["ok"] and result["code"] == "native_capacity"
    assert submitted == []
    assert native.unpack(book.document)[1] == before


def test_claude_docs_limit_refuses_writes_that_would_not_fit_and_keeps_notebook():
    book = Notebook()
    context = book.setup(host="claude")
    sitting = book.run({"action": "start", "role": "methods-clinic", **context})["result"]
    workspace = native.unpack(book.document)[0]["workspace_id"]
    record = {
        "action": "record",
        **context,
        "sitting_id": sitting["sitting"]["id"],
        "record": {
            "kind": "methods",
            "summary": "Synthetic",
            "details": [os.urandom(10_000).hex() for _ in range(5)],  # ~67 KB encoded.
            "sources": [],
        },
    }
    before = book.document
    result = native.run_native(
        {
            "action": "native.run",
            "document": before,
            "workspace_id": workspace,
            "document_limit_bytes": 65_536,
            "request": record,
        }
    )
    assert not result["ok"] and result["code"] == "native_capacity"
    assert not result["changed"] and result["markdown"] == before
    assert result["capacity"]["document_limit_bytes"] == 65_536
    # Without a host limit the same write still fits the original allowance.
    assert book.run(record)["changed"]


@pytest.mark.parametrize("limit", [1024, 190_001, "65536", True])
def test_document_limit_must_be_a_supported_integer(limit):
    book = Notebook()
    with pytest.raises(BenchsideError) as caught:
        native.run_native(
            {
                "action": "native.inspect",
                "document": book.document,
                "workspace_id": native.unpack(book.document)[0]["workspace_id"],
                "document_limit_bytes": limit,
            }
        )
    assert caught.value.code == "native_storage_invalid"


def test_submission_with_headroom_still_saves_its_receipt(monkeypatch):
    book = Notebook()
    draft = feedback_draft(book)
    submitted = fake_receipts(monkeypatch)
    result = book.run(
        {
            "action": "sharing.send",
            "draft_id": draft["id"],
            "approved_sha256": draft["preview"]["payload_sha256"],
        }
    )
    assert result["ok"] and result["changed"]
    assert submitted == [draft["preview"]["payload"]]
    history = book.run({"action": "sharing.history"})["result"]
    assert len(history) == 1 and history[0]["payload_sha256"] == draft["preview"]["payload_sha256"]


def test_unexpected_post_delivery_capacity_failure_returns_the_receipt(monkeypatch):
    book = Notebook()
    draft = feedback_draft(book)
    original = native.unpack(book.document)[1]
    submitted = fake_receipts(monkeypatch)
    send = HttpExportSink.send

    def changed_limit(self, payload):
        receipt = send(self, payload)
        monkeypatch.setattr(native, "MAX_STATE_BYTES", len(native._json(original).encode()) + 1)
        return receipt

    monkeypatch.setattr(HttpExportSink, "send", changed_limit)
    result = book.run(
        {
            "action": "sharing.send",
            "draft_id": draft["id"],
            "approved_sha256": draft["preview"]["payload_sha256"],
        }
    )
    assert len(submitted) == 1
    assert not result["ok"] and result["delivery_confirmed"] and not result["changed"]
    assert result["result"]["payload_sha256"] == draft["preview"]["payload_sha256"]
    assert "receipt could not be saved" in result["error"]
    assert native.unpack(book.document)[1] == original


@pytest.mark.parametrize(
    "action,field,choice",
    [
        ("sharing.consent", "channel", "gaps"),
        ("sharing.consent", "channel", "feedback"),
        ("sharing.consent", "channel", "usage"),
        ("metascience.consent", "choice", "invitations"),
        ("metascience.consent", "choice", "analysis"),
        ("metascience.consent", "choice", "sharing"),
    ],
)
def test_reserved_capacity_allows_every_sharing_choice_to_be_withdrawn(
    monkeypatch, action, field, choice
):
    book = Notebook()
    grant = {"action": action, field: choice, "enabled": True}
    if choice == "gaps":
        grant["kinds"] = ["missing_index"]
    assert book.run(grant)["ok"]
    raw_size = len(native._json(native.unpack(book.document)[1]).encode())
    monkeypatch.setattr(native, "MAX_STATE_BYTES", raw_size + native.STATE_CONTROL_RESERVE - 1)
    refused = book.run(
        {
            "action": "sharing.feedback",
            "feedback": {"ease": 4, "would_use_again": "yes", "comment": "Synthetic"},
        }
    )
    assert not refused["ok"] and refused["code"] == "native_capacity"
    withdrawn = book.run({"action": action, field: choice, "enabled": False})
    assert withdrawn["ok"] and withdrawn["changed"]
    status = book.run(
        {"action": "sharing.status" if action == "sharing.consent" else "metascience.status"}
    )["result"]
    assert not (
        status[choice]["enabled"] if action == "sharing.consent" else status["choices"][choice]
    )


@pytest.mark.parametrize(
    "command",
    [
        {"action": "sharing.consent", "channel": channel, "enabled": False}
        for channel in ("gaps", "feedback", "usage")
    ]
    + [
        {"action": "metascience.consent", "choice": choice, "enabled": False}
        for choice in ("invitations", "analysis", "sharing")
    ]
    + [
        {"action": "profile.set", "demographics": {}, "include_in_usage": False},
        {"action": "participation.set", "response": "declined"},
        {"action": "participation.set", "response": "deferred"},
    ],
)
def test_repeated_off_choices_cannot_consume_control_reserve(monkeypatch, command):
    book = Notebook()
    assert book.run(command)["ok"]
    snapshot, before = native.unpack(book.document)
    native._compact_operations(before, all_results=True)
    snapshot = native.pack(before, snapshot["workspace_id"], snapshot["revision"])
    book.document = native.markdown(snapshot)
    monkeypatch.setattr(
        native,
        "MAX_STATE_BYTES",
        len(native._json(before).encode()) + native.STATE_CONTROL_RESERVE - 1,
    )
    for _ in range(3):
        refused = book.run(command)
        assert not refused["ok"] and refused["code"] == "native_capacity"
        assert not refused["changed"] and not refused["control_history_compacted"]
        assert refused["snapshot"] == snapshot
        assert native.unpack(book.document)[1] == before


def test_profile_opt_out_can_use_reserve_without_changing_demographics(monkeypatch):
    book = Notebook()
    command = {
        "action": "profile.set",
        "demographics": {"discipline": "life_sciences"},
        "include_in_usage": True,
    }
    assert book.run(command)["ok"]
    before = native.unpack(book.document)[1]
    monkeypatch.setattr(
        native,
        "MAX_STATE_BYTES",
        len(native._json(before).encode()) + native.STATE_CONTROL_RESERVE - 1,
    )
    result = book.run({**command, "include_in_usage": False})
    assert result["ok"] and result["changed"]
    assert not result["result"]["include_in_usage"]
    assert result["result"]["demographics"]["discipline"] == "life_sciences"
    repeated = book.run({**command, "include_in_usage": False})
    assert not repeated["ok"] and repeated["code"] == "native_capacity"


@pytest.mark.parametrize("initially_enabled", [False, True])
def test_profile_edits_cannot_trigger_emergency_consent_compaction(monkeypatch, initially_enabled):
    book = Notebook()
    book.run({"action": "sharing.consent", "channel": "feedback", "enabled": True})
    book.run({"action": "sharing.consent", "channel": "feedback", "enabled": False})
    book.run({"action": "profile.set", "demographics": {}, "include_in_usage": initially_enabled})
    snapshot, before = native.unpack(book.document)
    native._compact_operations(before, all_results=True)
    book.document = native.markdown(
        native.pack(before, snapshot["workspace_id"], snapshot["revision"])
    )
    monkeypatch.setattr(native, "MAX_STATE_BYTES", len(native._json(before).encode()) + 64)
    refused = book.run(
        {
            "action": "profile.set",
            "demographics": {"discipline": "life_sciences"},
            "include_in_usage": False,
        }
    )
    assert not refused["ok"] and refused["code"] == "native_capacity"
    assert not refused["changed"] and not refused["control_history_compacted"]
    assert native.unpack(book.document)[1] == before


@pytest.mark.parametrize("unrelated_edit", [False, True])
def test_batch_reserve_requires_a_real_opt_out_without_unrelated_edits(monkeypatch, unrelated_edit):
    book = Notebook()
    book.run({"action": "sharing.consent", "channel": "feedback", "enabled": True})
    book.run({"action": "metascience.consent", "choice": "analysis", "enabled": True})
    before = native.unpack(book.document)[1]
    monkeypatch.setattr(
        native,
        "MAX_STATE_BYTES",
        len(native._json(before).encode()) + native.STATE_CONTROL_RESERVE - 1,
    )
    commands = [
        {"action": "sharing.consent", "channel": "feedback", "enabled": False},
        {"action": "metascience.consent", "choice": "analysis", "enabled": False},
        {"action": "participation.set", "response": "declined"},
        {"action": "sharing.status"},
    ]
    if unrelated_edit:
        commands.append(
            {
                "action": "profile.set",
                "demographics": {"discipline": "life_sciences"},
                "include_in_usage": False,
            }
        )
    result = book.batch(commands)
    if unrelated_edit:
        assert not result["ok"] and result["code"] == "native_capacity"
        assert native.unpack(book.document)[1] == before
    else:
        assert result["ok"] and result["changed"]
        assert not result["result"]["steps"]["step_3"]["feedback"]["enabled"]
        saved = native.unpack(book.document)
        repeated = book.batch(commands)
        assert not repeated["ok"] and repeated["code"] == "native_capacity"
        assert not repeated["changed"]
        assert native.unpack(book.document) == saved


def test_missing_metascience_state_rejects_unknown_draft_without_post():
    book = Notebook()
    result = book.run(
        {
            "action": "metascience.send",
            "draft_id": "a" * 32,
            "approved_sha256": "b" * 64,
        }
    )
    assert not result["ok"]
    assert "Review the current metascience draft first" in result["error"]
    assert "metascience/state.json" not in native.unpack(book.document)[1]["files"]


@pytest.mark.parametrize(
    "missing,message",
    [("document", "complete saved native document"), ("request", "app request inside native.run")],
)
def test_missing_native_inputs_return_recovery_guidance(missing, message):
    created = native.run_native({"action": "native.create"})
    request = {
        "action": "native.run",
        "workspace_id": created["snapshot"]["workspace_id"],
        "document": created["markdown"],
        "request": {"action": "roles"},
    }
    del request[missing]
    with pytest.raises(BenchsideError, match=message) as caught:
        native.run_native(request)
    assert caught.value.code == "native_storage_invalid"


@pytest.mark.parametrize(
    "retirement",
    [
        {"action": "metascience.consent", "choice": "analysis", "enabled": False},
        {"action": "metascience.scopes", "scopes": []},
    ],
)
def test_analysis_retirement_removes_cached_source_references_but_keeps_replay_ids(retirement):
    book = Notebook()
    context = book.setup()
    book.run({"action": "start", "role": "methods-clinic", **context})
    book.run({"action": "metascience.consent", "choice": "analysis", "enabled": True})
    scope = {"host": "claude", "source_id": "synthetic-private-source-retired"}
    book.run({"action": "metascience.scopes", "scopes": [scope]})
    operation_id = uuid.uuid4().hex
    command = {
        "action": "metascience.sample",
        "candidates": [{"scope": scope, "session_ref": "synthetic-private-session-retired"}],
    }
    sampled = book.run(command, operation_id=operation_id)
    assert sampled["ok"]
    before = native.unpack(book.document)[1]
    assert "synthetic-private-session-retired" in native._json(before["operations"])
    science = before["files"][f"projects/{context['project_id']}/journal.jsonl"]
    retired = book.run(retirement)
    assert retired["ok"]
    after = native.unpack(book.document)[1]
    cache = native._json(after["operations"])
    assert "synthetic-private-source-retired" not in cache
    assert "synthetic-private-session-retired" not in cache
    assert after["files"][f"projects/{context['project_id']}/journal.jsonl"] == science
    assert all(
        after["operations"][key]["request_sha256"] == value["request_sha256"]
        for key, value in before["operations"].items()
    )
    replay = book.run(command, operation_id=operation_id)
    assert replay["replayed"] and replay["result_compacted"] and not replay["changed"]
    assert replay["result"]["id"] == sampled["result"]["id"]


def test_emergency_withdrawal_preserves_science_receipts_and_replay_ids(monkeypatch):
    book = Notebook()
    context = book.setup()
    book.run({"action": "start", "role": "methods-clinic", **context})
    draft = feedback_draft(book)
    submitted = fake_receipts(monkeypatch)
    book.run(
        {
            "action": "sharing.send",
            "draft_id": draft["id"],
            "approved_sha256": draft["preview"]["payload_sha256"],
        }
    )
    book.run({"action": "sharing.consent", "channel": "usage", "enabled": True})
    pending = book.run({"action": "sharing.preview", "channel": "usage"})["result"][0]
    snapshot, body = native.unpack(book.document)
    native._compact_operations(body, all_results=True)
    book.document = native.markdown(
        native.pack(body, snapshot["workspace_id"], snapshot["revision"])
    )
    science = body["files"][f"projects/{context['project_id']}/journal.jsonl"]
    receipt = next(
        json.loads(line)
        for line in body["files"]["projects/consent-ledger/journal.jsonl"].splitlines()
        if json.loads(line)["type"] == "ReportSubmitted"
    )
    old_operations = copy.deepcopy(body["operations"])
    original_limit = native.MAX_STATE_BYTES
    monkeypatch.setattr(native, "MAX_STATE_BYTES", len(native._json(body).encode()) + 64)
    result = book.run({"action": "sharing.consent", "channel": "usage", "enabled": False})
    assert result["ok"] and result["control_history_compacted"]
    after = native.unpack(book.document)[1]
    assert after["files"][f"projects/{context['project_id']}/journal.jsonl"] == science
    assert receipt in [
        json.loads(line)
        for line in after["files"]["projects/consent-ledger/journal.jsonl"].splitlines()
    ]
    assert all(
        after["operations"][key]["request_sha256"] == value["request_sha256"]
        for key, value in old_operations.items()
    )
    assert not book.run({"action": "sharing.status"})["result"]["usage"]["enabled"]
    monkeypatch.setattr(native, "MAX_STATE_BYTES", original_limit)
    book.run({"action": "sharing.consent", "channel": "usage", "enabled": True})
    refused = book.run(
        {
            "action": "sharing.send",
            "draft_id": pending["id"],
            "approved_sha256": pending["preview"]["payload_sha256"],
        }
    )
    assert not refused["ok"] and "consent" in refused["error"].lower()
    assert len(submitted) == 1


def test_same_native_document_from_another_app_uses_existing_project():
    book = Notebook()
    first = book.setup("chatgpt")
    second = book.setup("claude")
    assert first["project_id"] == second["project_id"]
    assert first["session_id"] != second["session_id"]
    body = native.unpack(book.document)[1]
    assert len(body["projects"]) == 1
    assert (
        json.loads(body["files"][f"app-sessions/{second['session_id']}.json"])["host"] == "claude"
    )


@pytest.mark.parametrize("future", ["event", "field"])
def test_newer_record_types_require_an_update_without_discarding_data(future):
    book = Notebook()
    context = book.setup()
    book.run({"action": "start", "role": "methods-clinic", **context})
    snapshot, body = native.unpack(book.document)
    name = f"projects/{context['project_id']}/journal.jsonl"
    record = json.loads(body["files"][name])
    if future == "event":
        record["type"] = "FutureScientificRecord"
    else:
        record["data"]["future_context"] = {"preserve": "Synthetic future record"}
    body["files"][name] = json.dumps(record) + "\n"
    snapshot["payload"] = base64.b64encode(zlib.compress(native._json(body).encode())).decode()
    snapshot["sha256"] = native._digest(
        {key: value for key, value in snapshot.items() if key != "sha256"}
    )
    before = copy.deepcopy(snapshot)
    with pytest.raises(BenchsideError) as caught:
        native.unpack(snapshot)
    assert caught.value.code == "native_update_required"
    assert "Update the installed" in str(caught.value)
    assert snapshot == before
