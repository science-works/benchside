import json

import pytest

from benchside.domain.export.model.wire import validate_payload
from benchside.domain.shared.error import ValidationError
from benchside.infrastructure.redaction import TextRedactor


def payload(question):
    return json.dumps(
        {
            "schema": "benchside.gaps.v1",
            "observations": [
                {"id": "o1", "gap": {"kind": "missing_index", "question": question}},
            ],
        },
        ensure_ascii=False,
    )


def test_utf16_length_matches_the_worker():
    validate_payload(payload("🧬" * 1000))
    with pytest.raises(ValidationError):
        validate_payload(payload("🧬" * 1001))


def test_unknown_private_fields_rejected():
    data = json.loads(payload("a question"))
    data["observations"][0]["installation_id"] = "secret"
    with pytest.raises(ValidationError):
        validate_payload(json.dumps(data))


def test_redaction_preserves_ids_and_scrubs_identifiers():
    result = TextRedactor().apply(
        payload(
            "Find records for scientist@example.org in /Users/alice/unpublished/data.csv at https://private.example/signed?id=secret",
        )
    )
    assert "scientist@example.org" not in result
    assert "/Users/alice" not in result
    assert "private.example" not in result
    assert json.loads(result)["observations"][0]["id"] == "o1"
    assert TextRedactor().scan(result) == []
