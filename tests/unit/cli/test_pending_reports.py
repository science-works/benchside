"""CLI users can resume and explicitly replace a project report without sending."""

import json

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
    assert run("share", "preview")[0] != 0
    assert run("share", "preview", "--replace-draft", draft["id"])[0] == 0
    assert len(flow.drafts()) == 1 and len(flow.drafts()[0]["preview"]["observation_ids"]) == 2
    assert flow.history() == []


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
