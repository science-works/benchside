"""Strict legacy and linked gap contracts, including UTF-16 text limits."""

import json
import re

from benchside.domain.shared.error import ValidationError
from benchside.domain.shared.model.gap import GapContext

MAX_BYTES = 512 * 1024
MAX_OBSERVATIONS = 1000
GAP_FIELDS = {
    "missing_tool": {"task", "reached_for", "why_failed"},
    "unfindable_data": {"sought", "where_searched"},
    "manual_toil": {"task", "frequency"},
    "dead_end": {"approach", "cost"},
    "missing_index": {"question"},
}


def validate_gap(gap: dict, *, allow_context: bool = True) -> None:
    if (
        not isinstance(gap, dict)
        or not isinstance(gap.get("kind"), str)
        or gap["kind"] not in GAP_FIELDS
    ):
        raise ValidationError("Unknown workflow observation kind")
    context_fields = {"context"} if allow_context and "context" in gap else set()
    if set(gap) != GAP_FIELDS[gap["kind"]] | {"kind"} | context_fields:
        raise ValidationError("Workflow observations contain missing or unknown fields")
    for key, value in gap.items():
        if key == "context":
            if (
                not isinstance(value, dict)
                or not value
                or set(value) - set(GapContext.model_fields)
            ):
                raise ValidationError("Invalid optional workflow context")
            for item in value.values():
                _text(item, 2000)
        elif key == "where_searched":
            if not isinstance(value, list) or len(value) > 50:
                raise ValidationError("where_searched must have at most 50 entries")
            for item in value:
                _text(item, 500)
        else:
            _text(value, 2000)


def _text(value, maximum):
    if not isinstance(value, str) or len(value.encode("utf-16-le")) // 2 > maximum:
        raise ValidationError(f"Shared text must be a string of at most {maximum} characters")


def validate_payload(payload: str) -> dict:
    if len(payload.encode("utf-8")) > MAX_BYTES:
        raise ValidationError("Batch exceeds the collector's 512 KiB limit")
    try:
        data = json.loads(payload)
    except (TypeError, json.JSONDecodeError) as err:
        raise ValidationError("Invalid export JSON") from err
    contextual = isinstance(data, dict) and data.get("schema") == "benchside.gaps.v3"
    linked = isinstance(data, dict) and (
        data.get("schema") == "benchside.gaps.v2" or (contextual and "contributor_id" in data)
    )
    fields = {"schema", "observations"} | ({"contributor_id"} if linked else set())
    if not isinstance(data, dict) or set(data) != fields:
        raise ValidationError("Invalid export fields")
    if linked and (
        not isinstance(data["contributor_id"], str)
        or not re.fullmatch(r"[a-f0-9]{32}", data["contributor_id"])
    ):
        raise ValidationError("Invalid contributor identifier")
    observations = data["observations"]
    if data["schema"] not in {
        "benchside.gaps.v1",
        "benchside.gaps.v2",
        "benchside.gaps.v3",
    } or not isinstance(observations, list):
        raise ValidationError("Invalid export schema")
    if not 1 <= len(observations) <= MAX_OBSERVATIONS:
        raise ValidationError("An export needs 1–1000 observations")
    seen = set()
    for observation in observations:
        provenance = linked and isinstance(observation, dict) and "origin" in observation
        fields = {"id", "gap"} | ({"origin", "basis"} if provenance else set())
        if not isinstance(observation, dict) or set(observation) != fields:
            raise ValidationError("Invalid observation fields")
        if provenance and (
            not isinstance(observation["origin"], str)
            or not isinstance(observation["basis"], str)
            or observation["origin"] not in {"benchside", "selected_conversation"}
            or observation["basis"] not in {"model_inferred", "researcher_reported", "unknown"}
        ):
            raise ValidationError("Invalid observation origin or evidence basis")
        identifier = observation["id"]
        if not isinstance(identifier, str) or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", identifier
        ):
            raise ValidationError("Invalid observation identifier")
        if identifier in seen:
            raise ValidationError("Repeated observation identifier")
        seen.add(identifier)
        validate_gap(observation["gap"], allow_context=contextual)
    return data
