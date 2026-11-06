"""Reproductions from Claude's 6 November review (17, 19 and 23)."""

import re
from unittest.mock import patch

import pytest

from benchside.cli import runtime
from benchside.infrastructure import readable_records
from tests.unit.cli.test_bench_cli import env as env  # noqa: PLC0414


@pytest.mark.parametrize("format", ["odt", "markdown", "both"])
def test_export_prints_only_refreshed_formats(env, format):
    run, _, _ = env
    readable_records.configure(runtime.current_paths(), format)
    assert run("sitting", "open", "--persona", "pi")[0] == 0
    code, text = run("journal", "export")
    assert code == 0
    assert ("Research record.odt" in text) == (format in {"odt", "both"})
    assert ("Research record.md" in text) == (format in {"markdown", "both"})


def test_export_reports_copies_not_refreshed(env):
    run, _, _ = env
    run("sitting", "open", "--persona", "pi")
    readable_records.configure(runtime.current_paths(), "markdown")
    code, text = run("journal", "export")
    assert code == 0
    assert "not refreshed" in text and "Research record.odt" in text


def test_displayed_question_id_can_be_used_to_answer(env):
    run, _, _ = env
    run("sitting", "open", "--persona", "pi")
    run("question", "Does the synthetic effect replicate?")
    code, text = run("journal", "questions")
    assert code == 0
    identifier = re.search(r"[qQ]-[a-fA-F0-9]{32}", text).group()
    code, text = run("answer", identifier, "Not yet known")
    assert code == 0
    assert "answer saved" in text


def test_cli_refreshes_readable_record_once_for_multi_event_command(env, monkeypatch):
    from benchside.cli import main as cli

    run, _, _ = env
    run("sitting", "open", "--persona", "pi")
    decide = cli.cmd_decide

    def two_events(args):
        decide(args)
        return decide(args)

    monkeypatch.setattr(cli, "cmd_decide", two_events)
    with patch.object(readable_records, "export_project", wraps=readable_records.export_project) as export:
        assert run("decide", "Two events", "--because", "Synthetic command")[0] == 0
    assert export.call_count == 1


def test_cli_export_failure_keeps_save_successful_and_warns(env):
    run, _, _ = env
    run("sitting", "open", "--persona", "pi")
    with patch.object(readable_records, "export_project", side_effect=OSError("Synthetic failure")):
        code, text = run("decide", "Keep this", "--because", "Synthetic decision")
    assert code == 0
    assert "saved" in text and "readable" in text and "do not repeat" in text
    assert "Keep this" in run("journal", "decisions")[1]
