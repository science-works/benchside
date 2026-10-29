import pytest

from benchside.application.app import App
from benchside.domain.shared.error import BenchsideError

ROLES = {
    "study-design": "study-design",
    "methods-clinic": "methods",
    "results-meeting": "results",
    "repro-check": "reproducibility",
    "journal-club": "literature",
    "peer-review": "review",
}


def test_complete_recall_keeps_older_records_and_project_separation(paths):
    app = App(paths)
    setup = app.run({"action": "setup", "project_key": "history"})
    other = app.run({"action": "setup", "project_key": "other"})
    context = {key: setup[key] for key in ("project_id", "session_id")}
    context["sitting_id"] = app.run({"action": "start", "role": "methods-clinic", **context})[
        "sitting"
    ]["id"]
    for i in range(7):
        app.run({"action": "decide", **context, "decision": f"Decision {i}", "rationale": "Test"})
        app.run(
            {
                "action": "record",
                **context,
                "record": {
                    "kind": "methods",
                    "summary": f"Record {i}",
                    "details": ["Synthetic check"],
                    "sources": [],
                },
            }
        )
    recent = app.run({"action": "recall", "project_id": setup["project_id"]})
    assert len(recent["recent_decisions"]) == len(recent["recent_records"]) == 5
    assert recent["total_decisions"] == recent["total_records"] == 7
    complete = app.run({"action": "recall", "project_id": setup["project_id"], "history": "all"})
    assert [d["decision"] for d in complete["recent_decisions"]] == [
        f"Decision {i}" for i in range(7)
    ]
    assert [r["summary"] for r in complete["recent_records"]] == [f"Record {i}" for i in range(7)]
    assert complete["history"] == "all"
    isolated = app.run({"action": "recall", "project_id": other["project_id"], "history": "all"})
    assert isolated["recent_decisions"] == isolated["recent_records"] == []
    with pytest.raises(BenchsideError):
        app.run({"action": "recall", "project_id": setup["project_id"], "history": "everything"})


@pytest.mark.parametrize("role,kind", ROLES.items())
def test_each_role_records_resumes_and_concludes(paths, role, kind):
    app = App(paths)
    setup = app.run(
        {
            "action": "setup",
            "host": "claude",
            "surface": "desktop",
            "project_key": "research-project",
        }
    )
    context = {key: setup[key] for key in ("project_id", "session_id")}
    start = app.run({"action": "start", "role": role, **context})
    context["sitting_id"] = start["sitting"]["id"]
    app.run(
        {
            "action": "record",
            **context,
            "record": {
                "kind": kind,
                "summary": "Comparison needs an independent control",
                "details": [
                    "Technical measurements repeat the same biological sample.",
                    "Use independent samples.",
                ],
                "sources": ["supplied-methods.pdf, page 2"],
            },
        }
    )
    resumed = App(paths).run({"action": "start", "role": role, **context})
    assert resumed["sitting"]["id"] == context["sitting_id"]
    assert resumed["recall"]["recent_records"][0]["kind"] == kind
    assert resumed["recall"]["current_hypothesis"] is None
    app.run(
        {
            "action": "decide",
            **context,
            "decision": "Check independent controls",
            "rationale": "Supports the intended comparison",
        }
    )
    result = app.run(
        {"action": "close", **context, "converged": True, "detail": "Agreed next check"}
    )
    assert result["recall"]["last_sitting_state"] == "converged"
    assert result["recall"]["open_sittings"] == []


def test_pi_and_project_isolation(paths):
    app = App(paths)
    first = app.run({"action": "setup", "project_key": "one"})
    second = app.run({"action": "setup", "project_key": "two"})
    context = {key: first[key] for key in ("project_id", "session_id")}
    sitting = app.run({"action": "start", "role": "pi", **context})["sitting"]["id"]
    context["sitting_id"] = sitting
    app.run({"action": "hypothesis", **context, "statement": "A private hypothesis"})
    with pytest.raises(BenchsideError, match="another project"):
        app.run(
            {
                "action": "decide",
                **context,
                "project_id": second["project_id"],
                "decision": "Cross project",
                "rationale": "Should fail",
            }
        )
    assert (
        app.run({"action": "recall", "project_id": second["project_id"]})["current_hypothesis"]
        is None
    )


def test_storage_probe_survives_a_new_adapter(paths):
    probe = App(paths).run({"action": "storage.probe"})
    assert App(paths).run({"action": "storage.check", "token": probe["token"]})["matched"]
    assert not App(paths).run({"action": "storage.check", "token": "wrong"})["matched"]


def test_git_journal_storage_is_refused(paths):
    paths.home.mkdir(parents=True)
    (paths.home / ".git").mkdir()
    with pytest.raises(BenchsideError, match="outside Git"):
        App(paths).run({"action": "storage.probe"})


def test_role_metadata_is_specific(paths):
    roles = App(paths).run({"action": "roles"})
    assert len(roles) == 7
    assert len({r["title"] for r in roles}) == 7


def test_app_release_version_is_preserved_in_optional_usage(paths):
    app = App(paths)
    setup = app.run(
        {
            "action": "setup",
            "project_key": "versioned-project",
            "host": "claude",
            "app_version": "1.2.3",
        }
    )
    context = {key: setup[key] for key in ("project_id", "session_id")}
    app.run({"action": "start", "role": "methods-clinic", **context})
    app.run({"action": "sharing.consent", "channel": "usage", "enabled": True})
    drafts = app.run({"action": "sharing.preview", "channel": "usage"})
    import json

    row = json.loads(drafts[0]["preview"]["payload"])["sessions"][0]
    assert row["app_version"] == "1.2.3"
    with pytest.raises(BenchsideError):
        app.run(
            {
                "action": "setup",
                "project_key": "versioned-project",
                "app_version": "account@example.org",
            }
        )
