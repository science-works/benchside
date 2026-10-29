"""Optional analysis history must not consume the research notebook's capacity."""

import json
import uuid

from benchside.application import native
from tests.unit.application.test_metascience import flow as flow  # noqa: PLC0414
from tests.unit.application.test_metascience import record_batch
from tests.unit.application.test_native_capacity import Notebook, fake_receipts


def test_optional_history_limit_leaves_research_and_opt_out_working(monkeypatch):
    book = Notebook()
    context = book.setup()
    context["sitting_id"] = book.run({"action": "start", "role": "methods-clinic", **context})[
        "result"
    ]["sitting"]["id"]
    book.run({"action": "metascience.consent", "choice": "analysis", "enabled": True})
    scope = {"host": "claude", "source_id": "synthetic-source"}
    book.run({"action": "metascience.scopes", "scopes": [scope]})
    before = book.document
    monkeypatch.setattr(native, "MAX_METASCIENCE_DOCUMENT_BYTES", 1500, raising=False)
    result = book.run(
        {
            "action": "metascience.sample",
            "candidates": [
                {"scope": scope, "session_ref": uuid.uuid4().hex + uuid.uuid4().hex}
                for _ in range(20)
            ],
        }
    )
    assert not result["ok"] and not result["changed"]
    assert "optional" in result["error"].lower() and book.document == before
    saved = book.run(
        {
            "action": "decide",
            "decision": "Keep paired synthetic controls",
            "rationale": "Synthetic test",
            **context,
        }
    )
    assert saved["ok"] and saved["changed"]
    assert book.run({"action": "metascience.consent", "choice": "analysis", "enabled": False})["ok"]


def test_optional_capacity_check_happens_before_delivery(flow, monkeypatch):
    batch = record_batch(flow, 1)
    flow.consent("sharing", True)
    draft = flow.preview_activity(batch["week"])
    book = Notebook()
    snapshot, body = native.unpack(book.document)
    body["files"]["metascience/state.json"] = flow.path.read_text()
    body["files"]["reporting/installation.json"] = (
        flow.paths.home / "reporting/installation.json"
    ).read_text()
    book.document = native.markdown(
        native.pack(body, snapshot["workspace_id"], snapshot["revision"])
    )
    before = book.document
    sent = fake_receipts(monkeypatch)
    monkeypatch.setenv("BENCHSIDE_ACTIVITY_ENDPOINT", flow.sinks["activity"].destination)
    monkeypatch.setattr(native, "MAX_METASCIENCE_DOCUMENT_BYTES", 1000, raising=False)
    result = book.run(
        {"action": "metascience.send", "draft_id": draft["id"], "approved_sha256": draft["sha256"]}
    )
    assert not result["ok"] and not result["changed"] and not sent
    assert book.document == before
    assert json.loads(native.unpack(book.document)[1]["files"]["metascience/state.json"])["drafts"]
