import json

import pytest
from pydantic import ValidationError as ModelError

from benchside.domain.export.model.wire import validate_payload
from benchside.domain.shared.error import ValidationError
from benchside.domain.shared.model.gap import MissingIndex
from benchside.infrastructure.redaction import TextRedactor
from tests.unit.application.test_native import Notebook
from tests.unit.domain.export.test_export_service import export_service, observe  # noqa: F401


def payload(context=None, schema="benchside.gaps.v3", linked=True):
    gap = {"kind": "missing_index", "question": "Find an image export tool"}
    if context is not None:
        gap["context"] = context
    return {
        "schema": schema,
        **({"contributor_id": "a" * 32} if linked else {}),
        "observations": [{"id": "o1", "gap": gap}],
    }


@pytest.mark.parametrize("linked", [True, False])
def test_context_roundtrips_without_making_any_field_required(linked):
    value = payload(
        {
            "tool_name": "Fiji",
            "tool_version": "2.16.0",
            "workaround": "Rename exported columns manually",
        },
        linked=linked,
    )
    assert validate_payload(json.dumps(value)) == value
    model = MissingIndex.model_validate(value["observations"][0]["gap"])
    assert model.model_dump(mode="json") == value["observations"][0]["gap"]
    assert "context" not in MissingIndex(question="Legacy record").model_dump()


@pytest.mark.parametrize(
    "context", [[], {"hypothesis": "private"}, {"tool_version": 3}, {"workaround": "🧬" * 1001}, {}]
)
def test_invalid_context_is_rejected(context):
    with pytest.raises(ValidationError):
        validate_payload(json.dumps(payload(context)))


def test_old_wire_contract_does_not_silently_accept_new_fields():
    for version in ("v1", "v2"):
        with pytest.raises(ValidationError):
            validate_payload(
                json.dumps(
                    payload(
                        {"workaround": "Manual export"},
                        schema=f"benchside.gaps.{version}",
                        linked=version == "v2",
                    )
                )
            )
    with pytest.raises(ModelError):
        MissingIndex(question="General need", context={"hypothesis": "Private"})


def test_context_is_scrubbed_and_requires_approval_of_exact_bytes(export_service, journal):
    service, consent = export_service
    service.redactor = TextRedactor()
    consent.grant(grant_id="g1", gap_kinds=frozenset({"missing_index"}))
    observe(journal, "o1", "Find an image export tool")
    preview = service.preview(
        edits={
            "o1": payload({"workaround": "Ask person@example.com about /Users/person/private.csv"})[
                "observations"
            ][0]["gap"]
        }
    )
    value = validate_payload(preview.payload)
    assert value["schema"] == "benchside.gaps.v3"
    assert "person@example.com" not in preview.payload
    assert "/Users/person" not in preview.payload
    changed = preview.model_copy(update={"payload": preview.payload.replace("Ask", "Email")})
    with pytest.raises(Exception, match="reviewed payload"):
        service.export(preview=changed, approved_sha256=preview.payload_sha256)
    assert not service.sink.sent
    service.export(preview=preview, approved_sha256=preview.payload_sha256)
    assert service.sink.sent == [preview.payload]
    assert TextRedactor().scan(preview.payload) == []


def test_native_record_retains_context_and_requires_new_reader():
    from benchside.application.native import pack, unpack

    notebook = Notebook()
    setup = notebook.setup()
    context = {key: setup[key] for key in ("project_id", "session_id")}
    started = notebook.run({"action": "start", "role": "methods-clinic", **context})
    context["sitting_id"] = started["result"]["sitting"]["id"]
    saved = notebook.run(
        {
            "action": "gap",
            **context,
            "gap": payload({"workaround": "Manual export"})["observations"][0]["gap"],
        }
    )
    assert saved["ok"]
    snapshot, body = unpack(notebook.document)
    assert snapshot["schema"] == "benchside.native.v3"
    assert "Manual export" in json.dumps(body)
    assert unpack(pack(body, snapshot["workspace_id"], snapshot["revision"]))[1] == body
    recalled = notebook.run({"action": "recall", **context})
    assert recalled["ok"]
