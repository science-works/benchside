"""CLI users can resume and explicitly replace a project report without sending."""

import json
import re
from pathlib import Path

from benchside.application.sharing import SharingFlow
from benchside.cli.runtime import current_paths
from tests.unit.cli.test_bench_cli import env as env  # noqa: PLC0414


def test_cli_lists_and_replaces_pending_report(env):
    run, _, _ = env
    run("sitting", "open", "--persona", "pi")
    assert run("gap", "missing_index", "--question", "Booking information")[0] == 0
    flow = SharingFlow(current_paths())
    flow.set_consent("gaps", True, scope="all_workflow")
    assert run("share", "preview")[0] == 0
    draft = flow.drafts()[0]
    code, output = run("share", "drafts")
    assert code == 0
    assert json.loads(output)[0]["preview"] == draft["preview"]
    assert run("gap", "missing_index", "--question", "Reagent ordering information")[0] == 0
    code, output = run("share", "preview")
    assert code != 0 and "--replace-draft" in output
    assert run("share", "preview", "--replace-draft", draft["id"])[0] == 0
    assert len(flow.drafts()) == 1 and len(flow.drafts()[0]["preview"]["observation_ids"]) == 2
    assert flow.history() == []


def test_cli_limited_consent_previews_permitted_item_and_displays_withheld_ids(env, monkeypatch):
    monkeypatch.setenv("BENCHSIDE_GAPS_ENDPOINT", "")
    run, _, _ = env
    assert run("sitting", "open", "--persona", "pi")[0] == 0
    assert run("gap", "missing_index", "--question", "Synthetic booking information")[0] == 0
    assert run("gap", "workflow_problem", "--description", "Synthetic booking delay")[0] == 0
    assert run("share", "grant", "--kinds", "missing_index")[0] == 0
    code, output = run("share", "preview")
    assert code == 0
    draft = SharingFlow(current_paths()).drafts()[0]
    assert len(draft["preview"]["observation_ids"]) == 1
    assert len(draft["preview"]["withheld"]) == 1
    assert draft["preview"]["withheld"][0] in output and "Withheld" in output
    assert "Synthetic booking delay" not in output


def test_cli_skill_documents_workflow_consent_and_pending_report_recovery(env, monkeypatch):
    monkeypatch.setenv("BENCHSIDE_GAPS_ENDPOINT", "")
    text = (Path(__file__).resolve().parents[3] / "content/claude/bench-share/SKILL.md").read_text()
    kinds = re.search(r"chosen kinds \(([^)]+)\)", text).group(1)
    kinds = ",".join(kind.strip() for kind in kinds.split(","))
    assert "workflow_problem" in kinds
    for command in ("bench share drafts", "--replace-draft", "--project", "--all-projects"):
        assert command in text
    run, _, _ = env
    assert run("sitting", "open", "--persona", "pi")[0] == 0
    assert run("gap", "workflow_problem", "--description", "Synthetic booking delay")[0] == 0
    assert run("share", "grant", "--kinds", kinds)[0] == 0
    assert run("share", "preview")[0] == 0
    assert len(SharingFlow(current_paths()).drafts()) == 1


def test_missing_rationale_is_clear_in_cli_and_session_context(env):
    from benchside.cli.hooks import _recall_lines
    from benchside.cli.runtime import resolve_project

    run, _, _ = env
    assert run("sitting", "open", "--persona", "pi")[0] == 0
    assert run("decide", "Check the booking")[0] == 0
    for command in (("recall",), ("journal", "show"), ("journal", "decisions")):
        code, output = run(*command)
        assert code == 0 and "Rationale not stated" in output
    assert "Rationale not stated" in "\n".join(_recall_lines(resolve_project()))
