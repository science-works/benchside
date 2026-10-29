import base64
import copy
import hashlib
import json
import uuid
import zlib

import pytest

from benchside.application.native import markdown, reference, run_native, unpack
from benchside.domain.shared.error import BenchsideError


def batch(document, steps, operation_id=None):
    return run_native(
        {
            "action": "native.batch",
            "document": document,
            "workspace_id": unpack(document)[0]["workspace_id"],
            "operation_id": operation_id or uuid.uuid4().hex,
            "steps": steps,
        }
    )


def setup_steps():
    context = {
        "project_id": {"$ref": "setup.project_id"},
        "session_id": {"$ref": "setup.session_id"},
    }
    return [
        {
            "id": "setup",
            "project_document": {"document_id": "synthetic-a", "title": "Spike recovery"},
            "request": {"action": "setup", "host": "claude", "project_key": "synthetic-a"},
        },
        {"id": "participation", "request": {"action": "participation.set", "response": "deferred"}},
        {
            "id": "profile",
            "request": {"action": "profile.set", "demographics": {}, "include_in_usage": False},
        },
        {"id": "start", "request": {"action": "start", "role": "methods-clinic", **context}},
        {
            "id": "decision",
            "request": {
                "action": "decide",
                **context,
                "sitting_id": {"$ref": "start.sitting.id"},
                "decision": "Run paired spikes",
                "rationale": "Locate loss",
            },
        },
    ]


def test_one_save_restores_setup_preferences_and_decision_and_replays_once():
    original = run_native({"action": "native.create"})["markdown"]
    operation = uuid.uuid4().hex
    result = batch(original, setup_steps(), operation)
    assert result["ok"] and result["changed"] and not result["saved"]
    assert result["snapshot"]["revision"] == 1
    assert result["result"]["steps"]["start"]["recall"]["title"] == "Spike recovery"
    assert "Run paired spikes" in result["project_journal"]["markdown"]
    confirmed = run_native(
        {
            "action": "native.confirm",
            "document": result["markdown"],
            "workspace_id": result["snapshot"]["workspace_id"],
            "expected": reference(result["snapshot"]),
        }
    )
    assert confirmed["saved"]
    replay = batch(result["markdown"], setup_steps(), operation)
    assert replay["replayed"] and not replay["changed"]
    assert replay["result"] == result["result"]
    state = unpack(result["markdown"])[1]
    assert len([p for p in state["files"] if p.startswith("app-sessions/")]) == 1
    restored = batch(
        result["markdown"],
        [
            {"id": "choice", "request": {"action": "participation.status"}},
            {"id": "consent", "request": {"action": "sharing.status"}},
            {
                "id": "recall",
                "request": {"action": "recall", "project_id": result["result"]["project_id"]},
            },
        ],
    )
    assert restored["result"]["steps"]["choice"]["response"] == "deferred"
    assert not restored["changed"]
    assert not restored["result"]["steps"]["consent"]["usage"]["enabled"]
    assert (
        restored["result"]["steps"]["recall"]["recent_decisions"][0]["decision"]
        == "Run paired spikes"
    )
    changed = setup_steps()
    changed[-1]["request"]["decision"] = "Different choice"
    with pytest.raises(BenchsideError, match="different request"):
        batch(result["markdown"], changed, operation)


def test_failure_rolls_back_every_step_and_does_not_consume_operation_id():
    original = run_native({"action": "native.create"})["markdown"]
    steps = setup_steps()
    steps[-1]["request"]["sitting_id"] = "c-nonexistent"
    result = batch(original, steps)
    assert not result["ok"] and not result["changed"]
    assert result["markdown"] == original
    assert unpack(result["markdown"])[1] == {"files": {}, "projects": {}, "operations": {}}


@pytest.mark.parametrize("operation", ["read_batch", "read_single", "replay", "rollback"])
def test_alternate_compression_does_not_create_a_state_change(operation):
    operation_id = uuid.uuid4().hex
    initial = batch(run_native({"action": "native.create"})["markdown"], setup_steps(), operation_id)
    snapshot = copy.deepcopy(initial["snapshot"])
    # A valid envelope produced with different compressor settings has the
    # same decoded state but a different payload and transport checksum.
    raw = zlib.decompress(base64.b64decode(snapshot["payload"]))
    snapshot["payload"] = base64.b64encode(zlib.compress(raw, level=0)).decode("ascii")
    unsigned = {key: value for key, value in snapshot.items() if key != "sha256"}
    snapshot["sha256"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()
    assert snapshot["sha256"] != initial["snapshot"]["sha256"]
    assert unpack(snapshot)[1] == unpack(initial["snapshot"])[1]
    document = markdown(snapshot)
    recall = {"action": "recall", "project_id": initial["result"]["project_id"]}
    if operation == "read_single":
        result = run_native(
            {
                "action": "native.run",
                "document": document,
                "workspace_id": snapshot["workspace_id"],
                "request": recall,
            }
        )
    elif operation == "read_batch":
        result = batch(document, [{"id": "recall", "request": recall}])
    elif operation == "replay":
        result = batch(document, setup_steps(), operation_id)
        assert result["replayed"]
    else:
        failed_steps = setup_steps()
        failed_steps[-1]["request"]["sitting_id"] = "c-nonexistent"
        result = batch(document, failed_steps)
        assert not result["ok"]
    assert not result["changed"]
    assert result["snapshot"] == snapshot
    assert result["markdown"] == document


@pytest.mark.parametrize(
    "action",
    [
        "sharing.send",
        "sharing.preview",
        "metascience.poll",
        "metascience.send",
        "native.run",
        "storage.configure",
    ],
)
def test_batch_rejects_external_actions_before_setup(action):
    original = run_native({"action": "native.create"})["markdown"]
    steps = setup_steps() + [{"id": "external", "request": {"action": action}}]
    result = batch(original, steps)
    assert not result["ok"] and not result["changed"]
    assert "private actions" in result["error"]
    assert result["markdown"] == original


@pytest.mark.parametrize("change", ["forward_reference", "duplicate_id", "wrong_document"])
def test_invalid_batch_cannot_save_a_partial_project(change):
    original = run_native({"action": "native.create"})["markdown"]
    steps = copy.deepcopy(setup_steps())
    if change == "forward_reference":
        steps[-1]["request"]["sitting_id"] = {"$ref": "not_yet_created.id"}
    elif change == "duplicate_id":
        steps[-1]["id"] = "setup"
    else:
        steps[0]["project_document"]["document_id"] = "wrong"
    result = batch(original, steps)
    assert not result["ok"] and result["markdown"] == original


def test_declining_requires_active_permissions_to_be_revoked():
    original = run_native({"action": "native.create"})["markdown"]
    result = batch(
        original,
        [
            {
                "id": "consent",
                "request": {"action": "sharing.consent", "channel": "usage", "enabled": True},
            },
            {"id": "decline", "request": {"action": "participation.set", "response": "declined"}},
        ],
    )
    assert not result["ok"] and result["markdown"] == original


def test_legacy_notebook_title_is_recovered_from_index():
    initial = batch(run_native({"action": "native.create"})["markdown"], setup_steps())
    from benchside.application.native import markdown, pack

    snapshot, state = unpack(initial["markdown"])
    import json

    name = f"app-projects/{initial['result']['project_id']}.json"
    config = json.loads(state["files"][name])
    del config["title"]
    state["files"][name] = json.dumps(config)
    legacy = markdown(pack(state, snapshot["workspace_id"], snapshot["revision"]))
    result = batch(
        legacy,
        [
            {
                "id": "recall",
                "request": {"action": "recall", "project_id": initial["result"]["project_id"]},
            }
        ],
    )
    assert result["result"]["steps"]["recall"]["title"] == "Spike recovery"
