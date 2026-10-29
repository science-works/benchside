"""Failed pre-checks must not expire the operation they are trying to execute."""

import hashlib
import uuid

from benchside.application import native


def test_failed_send_from_legacy_full_replay_index_can_retry_same_operation():
    created = native.run_native({"action": "native.create"})
    workspace = created["snapshot"]["workspace_id"]
    _, body = native.unpack(created["markdown"], workspace)
    for i in range(130):
        body["operations"][uuid.uuid4().hex] = {
            "request_sha256": hashlib.sha256(str(i).encode()).hexdigest(),
            "result": {"ok": True},
            "revision": i + 1,
        }
    document = native.markdown(native.pack(body, workspace, 130))
    request = {
        "action": "native.run",
        "workspace_id": workspace,
        "document": document,
        "operation_id": uuid.uuid4().hex,
        "request": {"action": "sharing.send", "draft_id": "missing", "approved_sha256": "0" * 64},
    }
    failed = native.run_native(request)
    assert not failed["ok"]
    retry = native.run_native({**request, "document": failed["markdown"]})
    assert not retry["ok"]
    assert retry["code"] != "native_operation_expired"
    assert retry["operation_generation"] == 0
