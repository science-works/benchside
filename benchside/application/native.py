"""Portable native-document memory, independent of an execution sandbox.

The host reads/writes the private document with its own authorized tools. This
module validates and runs a transaction in a disposable directory and returns a
candidate snapshot. Only guarded host save + readback confirms persistence.
Compression is for document size, not encryption or anonymisation.
"""

import base64
import copy
import hashlib
import json
import re
import tempfile
import uuid
import zlib
from pathlib import Path

from benchside.application.app import READ_ACTIONS, App
from benchside.application.sharing import ParticipationChoice, SharingFlow, SubmissionDraft
from benchside.config import Paths
from benchside.domain.export.model.metascience import MetaState
from benchside.domain.export.model.reporting import ResearchProfile, UsagePayload
from benchside.domain.shared.error import BenchsideError, ValidationError
from benchside.domain.shared.event import Event
from benchside.infrastructure.journal.registry import ensure_events_registered
from benchside.infrastructure.session_context import validate_session_id

SCHEMA = "benchside.native.v1"
CHECKPOINT_SCHEMA = "benchside.native.v2"
CONTEXT_SCHEMA = "benchside.native.v3"
MAX_DOCUMENT_BYTES = 190_000  # Fits one native Pages edit with room for transport metadata.
MAX_METASCIENCE_DOCUMENT_BYTES = 48 * 1024
MAX_STATE_BYTES = 8 * 1024 * 1024
# Ordinary writes leave room to withdraw consent even when recording is full.
DOCUMENT_CONTROL_RESERVE = 16 * 1024
STATE_CONTROL_RESERVE = 64 * 1024
MAX_REPLAY_CACHE_BYTES = 32 * 1024
MAX_COMPACT_RESULT_BYTES = 4 * 1024
MAX_OPERATION_RECEIPTS = 128
MAX_OPERATION_INDEX_BYTES = 64 * 1024
RETAIN_OPERATION_RECEIPTS = 64
PROJECT = r"p-[a-f0-9]{32}"
FILE = re.compile(
    rf"(?:app-projects/{PROJECT}\.json|app-sessions/[a-f0-9]{{32}}\.json|"
    rf"projects/(?:{PROJECT}|consent-ledger|reporting-ledger)/journal\.jsonl|"
    r"sharing/drafts/[a-f0-9]{32}\.json|"
    r"reporting/(?:installation|profile|participation|contributions|usage-\d{4}-\d{2}-\d{2})\.json|metascience/state\.json)"
)
HEX = re.compile(r"[a-f0-9]{32}")
OPERATION = re.compile(r"(?:g([1-9][0-9]{0,9})-)?[a-f0-9]{32}")


def _json(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def _digest(value):
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _loads(text):
    return json.loads(text, object_pairs_hook=_pairs)


def _fail(message):
    raise ValidationError(message, code="native_storage_invalid")


def _update_required():
    raise ValidationError(
        "This notebook contains records from a newer Benchside version. Update the installed "
        "Benchside package, then reread this same notebook; do not delete, replace or skip records.",
        code="native_update_required",
    )


def _capacity_error():
    raise ValidationError(
        "Native notebook capacity is exhausted; nothing new should be submitted. "
        "Preserve this notebook and arrange archival or larger storage. Consent withdrawal "
        "can use reserved space; do not truncate scientific history.",
        code="native_capacity",
    )


def _check_files(files):
    ensure_events_registered()
    if not isinstance(files, dict):
        _fail("Native memory files must be an object")
    for name, text in files.items():
        if not FILE.fullmatch(name) or not isinstance(text, str):
            _fail("Native memory contains an unsupported file")
        if name.endswith("journal.jsonl"):
            project = name.split("/")[1]
            for line in text.splitlines():
                if not line.strip():
                    continue
                envelope = _loads(line)
                if set(envelope) != {"type", "session", "data"}:
                    _fail("Native journal envelope is incomplete")
                if envelope["session"] is not None:
                    validate_session_id(envelope["session"])
                try:
                    event_type = Event.resolve(envelope["type"])
                except KeyError:
                    _update_required()
                if set(envelope["data"]) - set(event_type.model_fields):
                    _update_required()
                event_type.model_validate(envelope["data"])
                if "project_id" in envelope["data"] and envelope["data"]["project_id"] != project:
                    _fail("Native journal event belongs to another project")
        elif name == "reporting/profile.json":
            ResearchProfile.model_validate_json(text)
        elif name == "reporting/participation.json":
            ParticipationChoice.model_validate_json(text)
        elif name == "reporting/contributions.json":
            from benchside.application.contributions import ContributionPolicy

            ContributionPolicy.model_validate_json(text)
        elif name == "metascience/state.json":
            MetaState.model_validate_json(text)
        elif name.startswith("sharing/"):
            draft = SubmissionDraft.model_validate_json(text)
            if Path(name).stem != draft.id:
                _fail("Native draft identifier does not match its filename")
        elif name.startswith("reporting/usage-"):
            usage = UsagePayload.model_validate_json(text)
            if name != f"reporting/usage-{usage.week}.json":
                _fail("Native usage week does not match its filename")
        else:
            data = _loads(text)
            if name == "reporting/installation.json":
                if set(data) != {"id"} or not HEX.fullmatch(data["id"]):
                    _fail("Invalid native installation identity")
            elif (
                (set(data) - ({"title"} if name.startswith("app-projects/") else set()))
                != (
                    {"host", "app_version", "surface", "project_id"}
                    if name.startswith("app-sessions/")
                    else {"host", "app_version", "surface"}
                )
                or data["host"] not in {"claude", "chatgpt", "unknown"}
                or data["surface"] not in {"web", "desktop", "cli", "unknown"}
                or not isinstance(data["app_version"], str)
            ):
                _fail("Invalid native project configuration")
            if "title" in data and (
                not isinstance(data["title"], str)
                or not 1 <= len(data["title"]) <= 160
                or any(ord(char) < 32 for char in data["title"])
            ):
                _fail("Invalid native project title")
            if name.startswith("app-sessions/") and (
                not isinstance(data.get("project_id"), str)
                or not re.fullmatch(PROJECT, data["project_id"])
                or f"app-projects/{data['project_id']}.json" not in files
            ):
                _fail("Native session references a missing project")


def _validate_body(body):
    if (
        not isinstance(body, dict)
        or not {"files", "projects", "operations"} <= set(body)
        or set(body) - {"files", "projects", "operations", "replay"}
    ):
        _fail("Invalid native memory contents")
    if "replay" in body and (
        not isinstance(body["replay"], dict)
        or set(body["replay"]) != {"generation"}
        or type(body["replay"]["generation"]) is not int
        or not 1 <= body["replay"]["generation"] <= 2**32 - 1
    ):
        _fail("Invalid native replay generation")
    _check_files(body["files"])
    if not isinstance(body["projects"], dict) or not isinstance(body["operations"], dict):
        _fail("Invalid native project or operation index")
    for identifier, project in body["projects"].items():
        if not re.fullmatch(PROJECT, identifier):
            _fail("Invalid native project identity")
        if f"app-projects/{identifier}.json" not in body["files"]:
            _fail("Native project configuration is missing")
        _validate_project(project)
        config = _loads(body["files"][f"app-projects/{identifier}.json"])
        key = f"{config['host']}:{project['document_id']}"
        if identifier != "p-" + hashlib.sha256(key.encode()).hexdigest()[:32]:
            _fail("Native project document does not match its stable identity")
    for identifier, operation in body["operations"].items():
        if not isinstance(operation, dict) or _operation_generation(identifier) > _generation(body):
            _fail("Invalid native operation identity")
        if not {"request_sha256", "result"} <= set(operation) or set(operation) - {
            "request_sha256",
            "result",
            "revision",
            "result_compacted",
        }:
            _update_required()
        if not re.fullmatch(r"[a-f0-9]{64}", operation["request_sha256"]):
            _fail("Invalid native operation receipt")
        if "revision" in operation and (
            type(operation["revision"]) is not int or operation["revision"] < 0
        ):
            _fail("Invalid native operation revision")
        if "result_compacted" in operation and type(operation["result_compacted"]) is not bool:
            _fail("Invalid native operation result marker")


def _validate_project(project):
    if not isinstance(project, dict) or set(project) != {"document_id", "title"}:
        _fail("Provide the native project document ID and title")
    if any(
        not isinstance(project[key], str)
        or not 1 <= len(project[key]) <= limit
        or any(ord(char) < 32 for char in project[key])
        for key, limit in (("document_id", 256), ("title", 160))
    ):
        _fail("Invalid native project document ID or title")


def _has_gap_context(value):
    """Include JSONL journals, frozen draft JSON and operation results in the gate.

    Older packages must refuse a context-bearing notebook instead of silently
    discarding nested fields when replaying their older event models.
    """
    if isinstance(value, dict):
        if value.get("schema") == "benchside.gaps.v3" or ("kind" in value and "context" in value):
            return True
        return any(_has_gap_context(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_gap_context(item) for item in value)
    if isinstance(value, str) and ("context" in value or "benchside.gaps.v3" in value):
        for line in [value, *value.splitlines()]:
            try:
                decoded = json.loads(line)
            except (ValueError, TypeError):
                continue
            if not isinstance(decoded, str) and _has_gap_context(decoded):
                return True
    return False


def _document_limit(request):
    # A host store may hold less than one Pages edit: Claude Docs caps a code block
    # at 65,536 characters. Omitted means the original limit for every other host.
    limit = request.get("document_limit_bytes")
    if limit is None:
        return MAX_DOCUMENT_BYTES
    if type(limit) is not int or not 2 * DOCUMENT_CONTROL_RESERVE <= limit <= MAX_DOCUMENT_BYTES:
        _fail(f"document_limit_bytes must be an integer from 32768 to {MAX_DOCUMENT_BYTES}")
    return limit


def pack(body, workspace_id, revision, *, limit=MAX_DOCUMENT_BYTES):
    _validate_body(body)
    raw = _json(body).encode("utf-8")
    if len(raw) > MAX_STATE_BYTES:
        _capacity_error()
    snapshot = {
        "schema": CONTEXT_SCHEMA
        if _has_gap_context(body)
        else (CHECKPOINT_SCHEMA if "replay" in body else SCHEMA),
        "workspace_id": workspace_id,
        "revision": revision,
        "payload": base64.b64encode(zlib.compress(raw)).decode("ascii"),
    }
    snapshot["sha256"] = _digest(snapshot)
    if len(_json(snapshot).encode("utf-8")) > limit:
        _capacity_error()
    return snapshot


def unpack(document, expected_workspace_id=None):
    """Reject damaged/foreign memory before restoring anything to a filesystem."""
    try:
        if isinstance(document, str):
            if len(document.encode("utf-8")) > MAX_DOCUMENT_BYTES + 4096:
                _fail("Native memory document is too large")
            if document.strip().startswith("{"):
                snapshot = _loads(document)
            else:
                blocks = re.findall(
                    r"^```json\s*\n(.*?)\n```\s*$", document, re.MULTILINE | re.DOTALL
                )
                if len(blocks) != 1:
                    _fail("Read the complete, single Benchside state block")
                snapshot = _loads(blocks[0])
        else:
            snapshot = document
        if not isinstance(snapshot, dict) or set(snapshot) != {
            "schema",
            "workspace_id",
            "revision",
            "payload",
            "sha256",
        }:
            _fail("Invalid native memory envelope")
        if snapshot["schema"] not in {SCHEMA, CHECKPOINT_SCHEMA, CONTEXT_SCHEMA}:
            _update_required()
        if (
            not HEX.fullmatch(snapshot["workspace_id"])
            or type(snapshot["revision"]) is not int
            or snapshot["revision"] < 0
            or len(_json(snapshot).encode("utf-8")) > MAX_DOCUMENT_BYTES
        ):
            _fail("Unsupported native memory version or identity")
        if expected_workspace_id and snapshot["workspace_id"] != expected_workspace_id:
            _fail("This document belongs to another Benchside notebook")
        unsigned = {key: value for key, value in snapshot.items() if key != "sha256"}
        if snapshot["sha256"] != _digest(unsigned):
            _fail(
                "Native memory checksum failed; keep the document and recover its last good version"
            )
        compressed = base64.b64decode(snapshot["payload"], validate=True)
        decoder = zlib.decompressobj()
        raw = decoder.decompress(compressed, MAX_STATE_BYTES + 1)
        if len(raw) > MAX_STATE_BYTES or not decoder.eof or decoder.unused_data:
            _fail("Invalid or oversized compressed native memory")
        body = _loads(raw.decode("utf-8"))
        _validate_body(body)
        contextual = _has_gap_context(body)
        if (snapshot["schema"] == CONTEXT_SCHEMA) != contextual:
            _fail("Native workflow context does not match its snapshot schema")
        if not contextual and (snapshot["schema"] == CHECKPOINT_SCHEMA) != ("replay" in body):
            _fail("Native replay generation does not match its snapshot schema")
        return snapshot, body
    except (ValueError, KeyError, TypeError, AttributeError, zlib.error) as error:
        raise ValidationError(
            "Native memory could not be validated", code="native_storage_invalid"
        ) from error


def markdown(snapshot):
    return "```json\n" + _json(snapshot) + "\n```"


def reference(snapshot):
    return {key: snapshot[key] for key in ("workspace_id", "revision", "sha256")}


def _generation(body):
    return body.get("replay", {}).get("generation", 0)


def _operation_generation(identifier):
    match = OPERATION.fullmatch(identifier) if isinstance(identifier, str) else None
    if not match:
        _fail("Use a UUID for generation 0, or g<operation_generation>-<UUID> after a checkpoint")
    return int(match.group(1) or 0)


def _new_operation_id(body):
    generation = _generation(body)
    return (f"g{generation}-" if generation else "") + uuid.uuid4().hex


def _bound_operations(body, *, current=None):
    """Expire a whole ID generation before forgetting any replay receipt."""
    operations = body["operations"]
    if (
        len(operations) <= MAX_OPERATION_RECEIPTS
        and len(_json(operations).encode("utf-8")) <= MAX_OPERATION_INDEX_BYTES
    ):
        return
    generation = _generation(body) + 1
    if generation > 2**32 - 1:
        _capacity_error()
    retained = {}
    ordered = sorted(
        operations,
        key=lambda key: (key == current, operations[key].get("revision", 0)),
        reverse=True,
    )
    # Leave half the index budget for new work so concurrent requests do not
    # expire on every subsequent write. Keep the current result even when its
    # exact response alone occupies the bounded 32 KiB response cache.
    for identifier in ordered:
        candidate = {**retained, identifier: operations[identifier]}
        if len(candidate) > RETAIN_OPERATION_RECEIPTS or (
            identifier != current
            and len(_json(candidate).encode("utf-8")) > MAX_OPERATION_INDEX_BYTES // 2
        ):
            break
        retained = candidate
    body["operations"] = retained
    body["replay"] = {"generation": generation}


def _checkpoint_sampling_format(body, original_body):
    """Use the v2 envelope before persisting sampling fields old readers reject."""
    if _generation(body):
        return
    path = "metascience/state.json"
    saved = body["files"].get(path)
    if saved is None or saved == original_body["files"].get(path):
        return
    state = _loads(saved)
    if any("sampling" in sample for sample in state.get("samples", {}).values()):
        # Even a newly serialized legacy sampling tag is an unknown field to
        # pre-0.1.3 readers. A compatibility checkpoint fences pending old IDs,
        # while every retained receipt still replays; no receipts are evicted here.
        body["replay"] = {"generation": 1}


def _capacity(body, snapshot, limit=MAX_DOCUMENT_BYTES):
    state_bytes = len(_json(body).encode("utf-8"))
    document_bytes = len(_json(snapshot).encode("utf-8"))
    return {
        "state_bytes": state_bytes,
        "document_bytes": document_bytes,
        "document_limit_bytes": limit,
        "ordinary_state_bytes_remaining": max(
            0, MAX_STATE_BYTES - STATE_CONTROL_RESERVE - state_bytes
        ),
        "ordinary_document_bytes_remaining": max(
            0, limit - DOCUMENT_CONTROL_RESERVE - document_bytes
        ),
        "control_reserve_document_bytes": DOCUMENT_CONTROL_RESERVE,
        "optional_history_document_bytes": _metascience_size(body),
        "optional_history_limit_bytes": MAX_METASCIENCE_DOCUMENT_BYTES,
    }


def _metascience_size(body):
    text = body["files"].get("metascience/state.json", "")
    return len(base64.b64encode(zlib.compress(text.encode("utf-8")))) if text else 0


def _require_metascience_headroom(body, original=None, *, additional=0):
    size = _metascience_size(body)
    if original is not None and size <= _metascience_size(original):
        return  # Reads, research records, withdrawal and shrinking state remain available.
    if size + (additional * 4 + 2) // 3 > MAX_METASCIENCE_DOCUMENT_BYTES:
        raise ValidationError(
            "Optional analysis and study history has reached its cloud notebook allowance. "
            "No new analysis or submission was saved. Existing records and receipts remain "
            "intact; research work and consent withdrawal can continue. Preserve this notebook "
            "and move to larger private storage before extending optional history.",
            code="native_capacity",
        )


def _require_headroom(body, snapshot, *, additional=0, limit=MAX_DOCUMENT_BYTES):
    capacity = _capacity(body, snapshot, limit)
    # Base64 and conservative compression/framing allowance. Collector receipts
    # are bounded separately; reserve their worst-case metadata before any POST.
    encoded_growth = (additional * 4 + 2) // 3 + (1024 if additional else 0)
    if (
        capacity["state_bytes"] + additional > MAX_STATE_BYTES - STATE_CONTROL_RESERVE
        or capacity["document_bytes"] + encoded_growth > limit - DOCUMENT_CONTROL_RESERVE
    ):
        _capacity_error()


def _result_identity(value):
    """Keep replay identities, never duplicate scientific text or growing recall."""
    if isinstance(value, list):
        return [_result_identity(item) for item in value]
    if not isinstance(value, dict):
        return None
    identifiers = {
        "id",
        "recorded",
        "project_id",
        "session_id",
        "draft_id",
        "batch_id",
        "week",
        "token",
        "channel",
        "payload_sha256",
        "sha256",
        "received_at",
    }
    result = {
        key: item
        for key, item in value.items()
        if key in identifiers and isinstance(item, str) and len(item) <= 128
    }
    for key in ("sitting", "preview", "invitation"):
        if key in value:
            result[key] = _result_identity(value[key])
    if isinstance(value.get("steps"), dict):
        result["steps"] = {key: _result_identity(item) for key, item in value["steps"].items()}
    return result


def _compact_operations(body, *, current=None, all_results=False):
    """Bound the response cache while retaining every operation ID and input hash."""
    remaining = 0 if all_results else MAX_REPLAY_CACHE_BYTES
    ordered = sorted(
        body["operations"],
        key=lambda key: (key == current, body["operations"][key].get("revision", 0)),
        reverse=True,
    )
    for identifier in ordered:
        operation = body["operations"][identifier]
        if operation.get("result_compacted"):
            continue
        size = len(_json(operation["result"]).encode("utf-8"))
        if size <= remaining:
            remaining -= size
        else:
            summary = _result_identity(operation["result"])
            if len(_json(summary).encode("utf-8")) > MAX_COMPACT_RESULT_BYTES:
                # An unusually large read nested inside a batch is not another
                # unbounded cache. The durable operation/hash still proves it
                # completed; obtain current data with a separate read.
                summary = {"completed": True}
            body["operations"][identifier] = {
                **operation,
                "result": summary,
                "result_compacted": True,
            }


def _privacy_controls(app):
    flow = SharingFlow(app.paths)
    status = flow.status()
    profile = flow.profile()
    enabled = {f"sharing.{key}" for key in ("gaps", "feedback", "usage") if status[key]["enabled"]}
    meta_path = app.paths.home / "metascience/state.json"
    scopes = []
    if meta_path.exists():
        state = MetaState.model_validate_json(meta_path.read_text())
        enabled.update(f"metascience.{key}" for key in state.grants)
        scopes = state.scopes
    if profile.include_in_usage:
        enabled.add("profile.include_in_usage")
    return {"enabled": enabled, "demographics": profile.demographics.model_dump(), "scopes": scopes}


def _commands(command):
    return (
        [step["request"] for step in command["steps"]]
        if command["action"] == "batch"
        else [command]
    )


def _withdrawal(command, before, after):
    """Reserve capacity for actual opt-outs, never repeated off/preference writes."""
    for item in _commands(command):
        action = item["action"]
        if action in READ_ACTIONS:
            continue
        if action in {"sharing.consent", "metascience.consent"} and item.get("enabled") is False:
            continue
        if action == "participation.set" and item.get("response") in ("declined", "deferred"):
            continue
        if action == "profile.set" and item.get("include_in_usage") is False:
            demographics = item.get("demographics")
            if (
                isinstance(demographics, dict)
                and {
                    "discipline": None,
                    "career_stage": None,
                    **demographics,
                }
                == before["demographics"]
            ):
                continue
        # A batch may use the reserve only for literal opt-outs and reads.
        # Unrelated profile changes and unresolved references use ordinary space.
        return False
    return bool(before["enabled"] - after["enabled"]) and not (after["enabled"] - before["enabled"])


def _retired_analysis(command, before, after):
    # Repeated analysis opt-outs also remove cached references left by older
    # versions. Retain replay IDs/hashes, not withdrawn source/session details.
    return (
        before["scopes"] != after["scopes"]
        or "metascience.analysis" in (before["enabled"] ^ after["enabled"])
        or any(
            item["action"] == "metascience.consent" and item.get("choice") == "analysis"
            for item in _commands(command)
        )
    )


def _compact_control_history(body):
    """Emergency consent checkpoint only; never drop science, receipts or operation IDs."""
    name = "projects/consent-ledger/journal.jsonl"
    if name not in body["files"]:
        return
    rows = [_loads(line) for line in body["files"][name].splitlines() if line.strip()]
    revoked = {row["data"]["grant_id"] for row in rows if row["type"] == "ConsentRevoked"}
    active = [
        row
        for row in rows
        if row["type"] == "ConsentGranted" and row["data"]["grant_id"] not in revoked
    ]
    latest = {}
    for row in rows:
        if row["type"] == "ReportingConsentChanged":
            latest[row["data"]["channel"]] = row
    retained = [
        row
        for row in rows
        if row["type"] not in {"ConsentGranted", "ConsentRevoked", "ReportingConsentChanged"}
    ]
    retained += active[-1:]
    retained += [row for row in latest.values() if row["data"]["enabled"]]
    body["files"][name] = "".join(_json(row) + "\n" for row in retained)


def _preflight_submission(body, snapshot, command, limit=MAX_DOCUMENT_BYTES):
    if command["action"] not in {"sharing.send", "metascience.send"}:
        return
    # Duplicate destination/ID metadata can appear in both the durable receipt
    # and its cached result. Include the entire bounded HTTP receipt (8 KiB)
    # twice and framing, even though normal server receipts are much smaller.
    if command["action"] == "sharing.send":
        text = body["files"].get(f"sharing/drafts/{command.get('draft_id')}.json")
        if text is None:
            return  # The ordinary validation rejects an unknown draft without network.
        preview = SubmissionDraft.model_validate_json(text).preview
        metadata = _json(
            {
                "destination": preview.destination,
                "observation_ids": preview.observation_ids,
                "grant_id": preview.grant_id,
            }
        )
    else:
        text = body["files"].get("metascience/state.json")
        if text is None:
            return  # Let the ordinary unknown-draft validation supply recovery guidance.
        state = MetaState.model_validate_json(text)
        draft = state.drafts.get(command.get("draft_id"))
        if draft is None:
            return
        metadata = _json({"destination": draft.destination, "draft_id": draft.id})
        if draft.id not in state.receipts:
            _require_metascience_headroom(
                body, additional=10 * 1024 + len(metadata.encode("utf-8"))
            )
    _require_headroom(
        body, snapshot, additional=18 * 1024 + 2 * len(metadata.encode("utf-8")), limit=limit
    )


def _restore(files, home):
    for name, content in files.items():
        path = home / name  # All paths have been allowlisted by unpack.
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        path.write_text(content, encoding="utf-8")
        path.chmod(0o600)


def _capture(home):
    return {
        path.relative_to(home).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(home.rglob("*"))
        if path.is_file() and FILE.fullmatch(path.relative_to(home).as_posix())
    }


def _quote(text):
    # Scientific text stays quoted content, never executable Page/agent instructions.
    return "\n".join("> " + line for line in str(text).splitlines())


def journal_view(app, project_id, projects, revision, history="recent"):
    recall = app.run({"action": "recall", "project_id": project_id, "history": history})
    lines = [
        f"Snapshot revision: {revision}.",
        (
            "This page is a readable view of that snapshot, not a live save status. "
            "Benchside checks the private notebook for the current saved revision; "
            "ask Benchside to record corrections so history is preserved."
        ),
        (
            f"Showing {len(recall['recent_decisions'])} of {recall['total_decisions']} decisions "
            f"and {len(recall['recent_records'])} of {recall['total_records']} research records. "
            + ("Ask Benchside for all history to see older entries." if history == "recent" else "")
        ).strip(),
        "## Current hypothesis",
        _quote(recall["current_hypothesis"]) if recall["current_hypothesis"] else "None recorded.",
        "## Unresolved questions",
        *[_quote(question) for question in recall["open_questions"]],
    ]
    if not recall["open_questions"]:
        lines.append("None recorded.")
    label = "All" if history == "all" else "Recent"
    lines.append(f"## {label} decisions")
    for decision in recall["recent_decisions"]:
        lines.extend([_quote(decision["decision"]), _quote(decision["rationale"])])
    lines.append(f"## {label} research records")
    for record in recall["recent_records"]:
        lines.append(_quote(record["summary"]))
        lines.extend(_quote(detail) for detail in record["details"])
        lines.extend(_quote("Source: " + source) for source in record["sources"])
    lines.append("## Open discussions")
    lines.extend(
        _quote(sitting["persona"] + ": " + sitting["id"]) for sitting in recall["open_sittings"]
    )
    if not recall["open_sittings"]:
        lines.append("None open.")
    return {
        "project_id": project_id,
        **projects.get(project_id, {}),
        "markdown": "\n\n".join(lines),
    }


BATCH_ACTIONS = {
    "setup",
    "roles",
    "projects",
    "recall",
    "start",
    "hypothesis",
    "record",
    "critique",
    "resolve",
    "decide",
    "gap",
    "close",
    "profile.status",
    "profile.set",
    "participation.status",
    "participation.set",
    "sharing.status",
    "sharing.consent",
    "metascience.status",
    "metascience.consent",
    "metascience.scopes",
}


def _references(value, results):
    if isinstance(value, dict):
        if set(value) == {"$ref"}:
            path = value["$ref"]
            if not isinstance(path, str):
                _fail("A batch reference must name an earlier step result")
            resolved = results
            for key in path.split("."):
                if not isinstance(resolved, dict) or key not in resolved:
                    _fail("A batch reference must name an earlier step result")
                resolved = resolved[key]
            return copy.deepcopy(resolved)
        return {key: _references(item, results) for key, item in value.items()}
    if isinstance(value, list):
        return [_references(item, results) for item in value]
    return value


def _checked_command(body, command, project):
    if not isinstance(command, dict) or not isinstance(command.get("action"), str):
        _fail("Provide an app request inside native.run")
    if command["action"].startswith(("native.", "storage.")):
        _fail("Native documents replace the local storage probe")
    if command["action"] == "setup":
        _validate_project(project)
        selected = command.get("project_id")
        if selected:
            existing = body["projects"].get(selected)
            if not existing or existing["document_id"] != project["document_id"]:
                _fail("Select the existing project and its registered journal document")
        elif command.get("project_key") != project["document_id"]:
            _fail("Use the observed native project document ID as project_key")
        else:
            registered = [
                identifier
                for identifier, saved in body["projects"].items()
                if saved["document_id"] == project["document_id"]
            ]
            if len(registered) > 1:
                _fail("Several projects use this journal document; select an existing project_id")
            if registered:
                # The native document identifies the project across host apps.
                # Keep its original creation identity instead of hashing a new host.
                command = {**command, "project_id": registered[0]}
        command = {**command, "title": project["title"]}
    elif project is not None:
        _fail("Project document registration is only supported during setup")
    return command


def _execute(app, body, command, project):
    command = _checked_command(body, command, project)
    result = app.run(command)
    if project is not None:
        body["projects"][result["project_id"]] = project
    # Older notebooks can have the friendly title only in the native index.
    project_id = command.get("project_id")
    if project_id in body["projects"] and isinstance(result, dict):
        recalled = result if command["action"] == "recall" else result.get("recall")
        if isinstance(recalled, dict):
            recalled["title"] = body["projects"][project_id]["title"]
    return result


def _execute_batch(app, body, steps):
    if not isinstance(steps, list) or not 1 <= len(steps) <= 16:
        _fail("A native batch needs 1–16 private steps")
    identifiers = set()
    # Validate the whole action list before executing any step. Network and
    # preview/approval actions must remain separate from these private saves.
    for step in steps:
        if not isinstance(step, dict) or set(step) - {"id", "request", "project_document"}:
            _fail("Invalid native batch step")
        identifier = step.get("id")
        if not isinstance(identifier, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,31}", identifier):
            _fail("Use a short unique batch step ID")
        if identifier in identifiers:
            _fail("Use a short unique batch step ID")
        identifiers.add(identifier)
        command = step.get("request")
        if (
            not isinstance(command, dict)
            or not isinstance(command.get("action"), str)
            or command["action"] not in BATCH_ACTIONS
        ):
            _fail("Batches support private actions only; keep network and previews separate")
    results = {}
    project_id = None
    for step in steps:
        command = _references(step["request"], results)
        result = _execute(app, body, command, step.get("project_document"))
        results[step["id"]] = result
        project_id = command.get("project_id", project_id)
        if command["action"] == "setup":
            project_id = result["project_id"]
    return {"steps": results, "project_id": project_id}


def run_native(request):
    """Host-neutral entry point used by the bundled app script."""
    if not isinstance(request, dict) or not isinstance(request.get("action"), str):
        _fail("Provide a native memory action")
    action = request["action"]
    if action == "native.create":
        snapshot = pack({"files": {}, "projects": {}, "operations": {}}, uuid.uuid4().hex, 0)
        return {
            "snapshot": snapshot,
            "markdown": markdown(snapshot),
            "operation_generation": 0,
            "saved": False,
        }
    if action not in {"native.inspect", "native.run", "native.batch", "native.confirm"}:
        _fail("Unknown native memory action")
    limit = _document_limit(request)
    expected = request.get("workspace_id")
    if not isinstance(expected, str) or not HEX.fullmatch(expected):
        _fail("Use the notebook workspace ID returned by native.create")
    if request.get("document") is None:
        _fail("Read and provide the complete saved native document before continuing")
    snapshot, body = unpack(request["document"], expected)
    if action == "native.confirm":
        if reference(snapshot) != request.get("expected"):
            raise ValidationError(
                "Native save was not confirmed; reread and reconcile before retrying",
                code="native_save_conflict",
            )
        return {"saved": True, **reference(snapshot)}
    if action == "native.inspect":
        return {
            **reference(snapshot),
            "projects": body["projects"],
            "capacity": _capacity(body, snapshot, limit),
            "operation_generation": _generation(body),
        }

    batch = action == "native.batch"
    command = (
        {"action": "batch", "steps": request.get("steps")} if batch else request.get("request")
    )
    if not isinstance(command, dict) or not isinstance(command.get("action"), str):
        _fail("Provide an app request inside native.run")
    project = request.get("project_document")
    if batch and project is not None:
        _fail("Put project_document on the batch setup step")
    if not batch:
        _checked_command(body, command, project)
    operation_id = request.get("operation_id", _new_operation_id(body))
    operation_generation = _operation_generation(operation_id)
    request_hash = _digest({"request": command, "project_document": project})
    previous = body["operations"].get(operation_id)
    if previous and previous["request_sha256"] != request_hash:
        _fail("This operation ID was already used for a different request")
    if not previous and operation_generation != _generation(body):
        raise ValidationError(
            "This operation is outside the notebook's active replay generation. It cannot be "
            "safely replayed. Preserve the original request and reconcile saved scientific "
            "records or submission receipts before deciding what to do. Do not automatically "
            "retry with a new operation ID. Read native.inspect for the current generation.",
            code="native_operation_expired",
        )

    original_body = copy.deepcopy(body)
    with tempfile.TemporaryDirectory(prefix="benchside-native-") as temporary:
        home = Path(temporary)
        _restore(body["files"], home)
        app = App(Paths(home=home, repo_root=home))
        outcome = {"ok": True}
        withdrawal = False
        if previous:
            result = previous["result"]
        else:
            try:
                original_controls = _privacy_controls(app)
                if command["action"] in {"sharing.send", "metascience.send"}:
                    # Capacity checks may migrate an old, oversized replay index.
                    # Do that only on a copy: a failed send must keep its original
                    # generation so the same operation can be retried safely.
                    preflight = copy.deepcopy(body)
                    _compact_operations(preflight)
                    _bound_operations(preflight)
                    _preflight_submission(
                        preflight,
                        pack(preflight, expected, snapshot["revision"], limit=limit),
                        command,
                        limit,
                    )
                result = (
                    _execute_batch(app, body, command["steps"])
                    if batch
                    else _execute(app, body, command, project)
                )
                mutates = (
                    any(step["request"]["action"] not in READ_ACTIONS for step in command["steps"])
                    if batch
                    else command["action"] not in READ_ACTIONS
                )
                if mutates:
                    current_controls = _privacy_controls(app)
                    withdrawal = _withdrawal(command, original_controls, current_controls)
                    body["operations"][operation_id] = {
                        "request_sha256": request_hash,
                        "result": result,
                        "revision": snapshot["revision"] + 1,
                    }
                    _compact_operations(
                        body,
                        current=operation_id,
                        all_results=_retired_analysis(command, original_controls, current_controls),
                    )
                    _bound_operations(body, current=operation_id)
            except BenchsideError as error:
                result = None
                outcome = {"ok": False, "error": str(error), "code": error.code}
                if batch:
                    # No partial setup, preferences, events or failure counters
                    # escape a failed private transaction.
                    body = original_body
        if not batch or outcome["ok"]:
            body["files"] = _capture(home)
        _checkpoint_sampling_format(body, original_body)
        # Compression bytes can differ across runtimes without a state change.
        # Preserve the original envelope for reads, replays and rolled-back
        # batches so a different zlib representation cannot trigger a save.
        changed = _json(body) != _json(original_body)
        control_history_compacted = False
        candidate_failed = False
        delivery_confirmed = False
        try:
            if changed and not withdrawal:
                _require_metascience_headroom(body, original_body)
            try:
                candidate = (
                    pack(body, expected, snapshot["revision"] + 1, limit=limit)
                    if changed
                    else snapshot
                )
            except ValidationError as error:
                if error.code != "native_capacity" or not outcome["ok"] or not withdrawal:
                    raise
                _compact_operations(body, all_results=True)
                _compact_control_history(body)
                candidate = pack(body, expected, snapshot["revision"] + 1, limit=limit)
                control_history_compacted = True
            if changed and not withdrawal:
                _require_headroom(body, candidate, limit=limit)
        except ValidationError as error:
            if error.code != "native_capacity":
                raise
            # No private transaction is committed if its candidate cannot fit.
            # A collector receipt, if already obtained despite the conservative
            # preflight, must still be returned and described as unsaved.
            delivery_confirmed = outcome["ok"] and command["action"] in {
                "sharing.send",
                "metascience.send",
            }
            outcome = {"ok": False, "error": str(error), "code": error.code}
            if delivery_confirmed:
                outcome["error"] = (
                    "Collector delivery was confirmed but its native receipt could not be saved. "
                    "Preserve the returned receipt and original notebook; retry only the same "
                    "approved draft after recovering capacity."
                )
            else:
                result = None
                if withdrawal:
                    outcome["error"] = (
                        "Consent withdrawal could not fit in this legacy notebook, even after "
                        "compacting replay responses and consent history. It has not been saved. "
                        "Stop sharing, preserve the notebook, and recover capacity or move to "
                        "larger private storage before continuing."
                    )
            candidate, body = snapshot, original_body
            changed, candidate_failed = False, True
        project_id = (result or {}).get("project_id") if isinstance(result, dict) else None
        project_id = project_id or command.get("project_id")
        view = (
            journal_view(
                app,
                project_id,
                body["projects"],
                candidate["revision"],
                command.get("history", "recent") if command["action"] == "recall" else "recent",
            )
            if not candidate_failed and project_id in body["projects"]
            else None
        )
    return {
        **outcome,
        "result": result,
        "operation_id": operation_id,
        "operation_generation": _generation(body),
        "replay_checkpointed": _generation(body) != _generation(original_body),
        "replayed": bool(previous),
        "result_compacted": bool(previous and previous.get("result_compacted")),
        "control_history_compacted": control_history_compacted,
        **({"delivery_confirmed": True} if delivery_confirmed else {}),
        "base": reference(snapshot),
        "snapshot": candidate,
        "markdown": markdown(candidate),
        "changed": changed,
        "saved": False,
        "project_journal": view,
        "capacity": _capacity(body, candidate, limit),
    }
