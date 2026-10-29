import base64
import copy
import hashlib
import json
import uuid
import zlib

import pytest

from benchside.application.native import markdown, pack, reference, run_native, unpack
from benchside.domain.shared.error import BenchsideError

ROLES = {
    "pi": None,
    "study-design": "study-design",
    "methods-clinic": "methods",
    "results-meeting": "results",
    "repro-check": "reproducibility",
    "journal-club": "literature",
    "peer-review": "review",
}


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    for channel in ("GAPS", "FEEDBACK", "USAGE"):
        monkeypatch.setenv(f"BENCHSIDE_{channel}_ENDPOINT", "")


class Notebook:
    def __init__(self):
        created = run_native({"action": "native.create"})
        assert not created["saved"]
        self.document = created["markdown"]
        self.workspace_id = created["snapshot"]["workspace_id"]

    def run(self, command, *, project=None, operation_id=None, save=True):
        request = {
            "action": "native.run",
            "workspace_id": self.workspace_id,
            "document": self.document,
            "request": command,
            "operation_id": operation_id or uuid.uuid4().hex,
        }
        if project:
            request["project_document"] = {"document_id": project, "title": "Synthetic project"}
        candidate = run_native(request)
        assert not candidate["saved"]
        if save:
            self.document = candidate["markdown"]
            assert self.confirm(candidate)["saved"]
        return candidate

    def confirm(self, candidate):
        return run_native(
            {
                "action": "native.confirm",
                "workspace_id": self.workspace_id,
                "document": self.document,
                "expected": reference(candidate["snapshot"]),
            }
        )

    def setup(self, page="page-a"):
        return self.run({"action": "setup", "host": "chatgpt", "project_key": page}, project=page)[
            "result"
        ]


def test_failed_invitation_candidate_is_saved_and_restored_with_cooldown(monkeypatch):
    from datetime import UTC, datetime, timedelta

    from benchside.application.metascience import StudyClient
    from benchside.domain.shared.error import InfrastructureError

    calls = []

    def unavailable(self):
        calls.append(True)
        raise InfrastructureError("Synthetic connection failure")

    monkeypatch.setattr(StudyClient, "fetch", unavailable)
    notebook = Notebook()
    notebook.run({"action": "metascience.consent", "choice": "invitations", "enabled": True})
    failed = notebook.run({"action": "metascience.invitations"})
    assert not failed["ok"] and failed["changed"]
    assert "Synthetic connection failure" in failed["error"]
    assert notebook.confirm(failed)["revision"] == failed["snapshot"]["revision"]
    restored = notebook.run({"action": "metascience.invitations"})
    assert restored["result"]["reason"] == "already_checked_today"
    tomorrow = datetime.now(UTC).date() + timedelta(days=1)
    assert restored["result"]["retry_at"] == f"{tomorrow}T00:00:00Z"
    assert len(calls) == 1


def test_native_complete_history_is_read_only_and_view_names_its_snapshot_revision():
    notebook = Notebook()
    setup = notebook.setup()
    context = {k: setup[k] for k in ("project_id", "session_id")}
    context["sitting_id"] = notebook.run({"action": "start", "role": "methods-clinic", **context})[
        "result"
    ]["sitting"]["id"]
    for i in range(7):
        notebook.run(
            {"action": "decide", **context, "decision": f"Decision {i}", "rationale": "Test"}
        )
    original = notebook.document
    recent = notebook.run({"action": "recall", "project_id": setup["project_id"]})
    assert "5 of 7 decisions" in recent["project_journal"]["markdown"]
    full = notebook.run({"action": "recall", "project_id": setup["project_id"], "history": "all"})
    assert len(full["result"]["recent_decisions"]) == 7
    assert "Decision 0" in full["project_journal"]["markdown"]
    assert "## All decisions" in full["project_journal"]["markdown"]
    assert (
        f"Snapshot revision: {full['snapshot']['revision']}" in full["project_journal"]["markdown"]
    )
    assert not full["changed"] and notebook.document == original


@pytest.mark.parametrize("role,kind", ROLES.items())
def test_native_roles_restore_without_a_shared_execution_directory(
    role, kind, monkeypatch, tmp_path
):
    monkeypatch.setenv("BENCHSIDE_HOME", str(tmp_path / "must-not-be-used"))
    notebook = Notebook()
    setup = notebook.setup()
    context = {k: setup[k] for k in ("project_id", "session_id")}
    sitting = notebook.run({"action": "start", "role": role, **context})["result"]["sitting"]
    context["sitting_id"] = sitting["id"]
    if role == "pi":
        notebook.run(
            {"action": "hypothesis", "statement": "Synthetic private hypothesis", **context}
        )
    else:
        notebook.run(
            {
                "action": "record",
                "record": {
                    "kind": kind,
                    "summary": "Synthetic private record",
                    "details": ["Compare independent samples"],
                    "sources": ["synthetic.pdf, page 2"],
                },
                **context,
            }
        )
    notebook.run(
        {
            "action": "critique",
            "target": {
                "kind": "claim",
                "claim": "Recovery loss occurs during extraction",
                "ground": "Not yet distinguished from detection loss",
            },
            **context,
        }
    )
    notebook.run(
        {
            "action": "decide",
            "decision": "Run paired spike controls",
            "rationale": "Locate the loss",
            **context,
        }
    )
    resumed_setup = notebook.setup()
    assert resumed_setup["project_id"] == context["project_id"]
    assert resumed_setup["session_id"] != context["session_id"]
    resumed = notebook.run({"action": "start", "role": role, **resumed_setup})["result"]
    assert resumed["sitting"]["id"] == context["sitting_id"]
    assert resumed["recall"]["recent_decisions"][0]["decision"] == "Run paired spike controls"
    assert "Recovery loss" in resumed["recall"]["open_questions"][0]
    assert "Not yet distinguished from detection loss" in resumed["recall"]["open_questions"][0]
    other = notebook.setup("page-b")
    recall = notebook.run({"action": "recall", "project_id": other["project_id"]})["result"]
    assert (
        not recall["recent_records"]
        and not recall["recent_decisions"]
        and not recall["open_questions"]
    )
    assert not (tmp_path / "must-not-be-used").exists()


def test_native_recall_and_readable_journal_preserve_the_unresolved_alternative():
    notebook = Notebook()
    context = notebook.setup()
    started = notebook.run({"action": "start", "role": "methods-clinic", **context})
    context["sitting_id"] = started["result"]["sitting"]["id"]
    question = "Which stage causes the loss: extraction or detection?"
    notebook.run(
        {
            "action": "critique",
            "target": {
                "kind": "interpretation",
                "result": "Recovery is 20%",
                "alternative": question,
            },
            **context,
        }
    )
    # The next runtime restores from the persisted notebook, not the preceding response.
    recalled = notebook.run({"action": "recall", "project_id": context["project_id"]})
    assert question in recalled["result"]["open_questions"][0]
    assert question in recalled["project_journal"]["markdown"]


def test_failed_save_keeps_previous_state_and_retry_does_not_duplicate():
    notebook = Notebook()
    setup = notebook.setup()
    context = {k: setup[k] for k in ("project_id", "session_id")}
    start = notebook.run({"action": "start", "role": "methods-clinic", **context})
    context["sitting_id"] = start["result"]["sitting"]["id"]
    command = {"action": "decide", "decision": "Only once", "rationale": "Synthetic", **context}
    operation_id = uuid.uuid4().hex
    pending = notebook.run(command, operation_id=operation_id, save=False)
    with pytest.raises(BenchsideError, match="not confirmed"):
        notebook.confirm(pending)
    before = notebook.run({"action": "recall", "project_id": setup["project_id"]})
    assert before["result"]["recent_decisions"] == []
    saved = notebook.run(command, operation_id=operation_id)
    repeated = notebook.run(command, operation_id=operation_id)
    assert repeated["replayed"] and not repeated["changed"]
    assert repeated["snapshot"] == saved["snapshot"]
    assert len(repeated["result"]["recall"]["recent_decisions"]) == 1
    with pytest.raises(BenchsideError, match="different request"):
        notebook.run({**command, "decision": "Changed"}, operation_id=operation_id)


def test_stale_candidate_is_detected_and_action_can_rebase():
    notebook = Notebook()
    setup = notebook.setup()
    context = {k: setup[k] for k in ("project_id", "session_id")}
    start = notebook.run({"action": "start", "role": "methods-clinic", **context})
    context["sitting_id"] = start["result"]["sitting"]["id"]
    operation_id = uuid.uuid4().hex
    command = {
        "action": "decide",
        "decision": "Pending decision",
        "rationale": "Synthetic",
        **context,
    }
    pending = notebook.run(command, operation_id=operation_id, save=False)
    notebook.run({**command, "decision": "Other chat's decision"})
    with pytest.raises(BenchsideError, match="not confirmed"):
        notebook.confirm(pending)
    rebased = notebook.run(command, operation_id=operation_id)
    assert [d["decision"] for d in rebased["result"]["recall"]["recent_decisions"]] == [
        "Other chat's decision",
        "Pending decision",
    ]


def test_consent_drafts_and_usage_identity_survive_native_restore():
    notebook = Notebook()
    setup = notebook.setup()
    notebook.run({"action": "start", "role": "methods-clinic", **setup})
    notebook.run({"action": "sharing.consent", "channel": "usage", "enabled": True})
    first = notebook.run({"action": "sharing.preview", "channel": "usage"})["result"][0]
    again = notebook.run({"action": "sharing.preview", "channel": "usage"})["result"][0]
    assert first["preview"]["payload"] == again["preview"]["payload"]
    assert json.loads(first["preview"]["payload"])["sessions"][0]["started"] == 1
    notebook.run({"action": "sharing.consent", "channel": "usage", "enabled": False})
    rejected = notebook.run(
        {
            "action": "sharing.send",
            "draft_id": first["id"],
            "approved_sha256": first["preview"]["payload_sha256"],
        }
    )
    assert not rejected["ok"]
    assert "consent" in rejected["error"].lower()
    assert notebook.run({"action": "sharing.history"})["result"] == []


def test_feedback_preview_and_failed_send_preserve_exact_draft():
    notebook = Notebook()
    notebook.run({"action": "sharing.consent", "channel": "feedback", "enabled": True})
    feedback = notebook.run(
        {
            "action": "sharing.feedback",
            "feedback": {"ease": 4, "would_use_again": "yes", "comment": "Synthetic feedback"},
        }
    )["result"]
    draft = notebook.run(
        {"action": "sharing.preview", "channel": "feedback", "feedback_id": feedback["id"]}
    )["result"][0]
    failed = notebook.run(
        {
            "action": "sharing.send",
            "draft_id": draft["id"],
            "approved_sha256": draft["preview"]["payload_sha256"],
        }
    )
    assert not failed["ok"]
    _, body = unpack(notebook.document)
    saved = json.loads(body["files"][f"sharing/drafts/{draft['id']}.json"])
    assert saved == draft
    assert notebook.run({"action": "sharing.history"})["result"] == []


def test_damage_wrong_notebook_and_incomplete_reads_are_refused():
    snapshot = run_native({"action": "native.create"})["snapshot"]
    damaged = {**snapshot, "revision": 9}
    with pytest.raises(BenchsideError, match="checksum"):
        unpack(damaged)
    with pytest.raises(BenchsideError, match="another Benchside"):
        unpack(snapshot, uuid.uuid4().hex)
    with pytest.raises(BenchsideError):
        unpack(markdown(snapshot)[:-12])
    with pytest.raises(BenchsideError):
        unpack(markdown(snapshot) + "\n\n" + markdown(snapshot))


def test_unknown_files_and_corrupt_events_are_not_silently_dropped():
    notebook = Notebook()
    setup = notebook.setup()
    notebook.run({"action": "start", "role": "pi", **setup})
    snapshot, body = unpack(notebook.document)
    traversal = copy.deepcopy(body)
    traversal["files"]["../../escape"] = "bad"
    with pytest.raises(BenchsideError, match="unsupported file"):
        pack(traversal, snapshot["workspace_id"], 1)
    broken = copy.deepcopy(body)
    name = f"projects/{setup['project_id']}/journal.jsonl"
    broken["files"][name] += '{"invalid":"event"}\n'
    with pytest.raises(BenchsideError, match="envelope"):
        pack(broken, snapshot["workspace_id"], 1)


def test_compression_bomb_is_bounded():
    snapshot = run_native({"action": "native.create"})["snapshot"]
    snapshot["payload"] = base64.b64encode(zlib.compress(b" " * (9 * 1024 * 1024))).decode()
    unsigned = {k: v for k, v in snapshot.items() if k != "sha256"}
    snapshot["sha256"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    with pytest.raises(BenchsideError, match="oversized"):
        unpack(snapshot)


def test_two_apps_continue_the_same_connected_notebook():
    notebook = Notebook()
    first = notebook.setup("shared-document")
    sitting = notebook.run({"action": "start", "role": "methods-clinic", **first})["result"][
        "sitting"
    ]
    notebook.run(
        {
            "action": "decide",
            **first,
            "sitting_id": sitting["id"],
            "decision": "Shared control",
            "rationale": "Synthetic",
        }
    )
    second = notebook.run(
        {"action": "setup", "host": "claude", "project_id": first["project_id"]},
        project="shared-document",
    )["result"]
    resumed = notebook.run({"action": "start", "role": "methods-clinic", **second})["result"]
    assert resumed["sitting"]["id"] == sitting["id"]
    assert resumed["recall"]["recent_decisions"][0]["decision"] == "Shared control"
    assert len(unpack(notebook.document)[1]["projects"]) == 1
    with pytest.raises(BenchsideError, match="registered journal"):
        notebook.run(
            {"action": "setup", "host": "claude", "project_id": first["project_id"]},
            project="different-document",
        )


def test_legacy_notebook_without_session_files_still_restores():
    notebook = Notebook()
    setup = notebook.setup()
    snapshot, body = unpack(notebook.document)
    body["files"] = {
        name: value for name, value in body["files"].items() if not name.startswith("app-sessions/")
    }
    notebook.document = markdown(pack(body, snapshot["workspace_id"], snapshot["revision"]))
    restored_setup = notebook.setup()
    assert restored_setup["project_id"] == setup["project_id"]
    result = notebook.run({"action": "start", "role": "pi", **restored_setup})
    assert result["ok"] and result["result"]["sitting"]["host"] == "chatgpt"


def test_demographic_preferences_restore_and_invalidate_native_usage_draft():
    notebook = Notebook()
    profile = {"discipline": "social_sciences", "career_stage": "research_staff"}
    assert notebook.run(
        {"action": "profile.set", "demographics": profile, "include_in_usage": True}
    )["ok"]
    assert notebook.run({"action": "profile.status"})["result"]["demographics"] == profile
    notebook.run({"action": "sharing.consent", "channel": "usage", "enabled": True})
    draft = notebook.run({"action": "sharing.preview", "channel": "usage"})["result"][0]
    assert json.loads(draft["preview"]["payload"])["demographics"] == profile
    notebook.run({"action": "profile.set", "demographics": {}, "include_in_usage": False})
    rejected = notebook.run(
        {
            "action": "sharing.send",
            "draft_id": draft["id"],
            "approved_sha256": draft["preview"]["payload_sha256"],
        }
    )
    assert not rejected["ok"] and "preferences changed" in rejected["error"]
