"""journal views are the human surface: structured, glyphed, testable in plain.

Chrome goes to stderr via the UI layer; `journal events --json` stays pure
stdout. Plain rendering is exact-shape testable (non-TTY => plain).
"""

import json

import pytest

from benchside.cli.main import main

MINIMAL_PI = """
id: pi
stance: s
voice: v
expertise: [x]
flow:
  close_requires:
    - kind: hypothesis
      minimum: 1
"""


@pytest.fixture
def env(tmp_path, monkeypatch, capsys):
    home = tmp_path / "home"
    project_dir = tmp_path / "lab"
    project_dir.mkdir()
    (project_dir / ".bench").mkdir()
    (project_dir / ".bench" / "config.yaml").write_text("project: lab\n")
    content = tmp_path / "repo" / "content"
    (content / "personas").mkdir(parents=True)
    (content / "templates").mkdir(parents=True)
    (content / "personas" / "pi.yaml").write_text(MINIMAL_PI)
    monkeypatch.setenv("BENCHSIDE_HOME", str(home))
    monkeypatch.setenv("BENCHSIDE_REPO", str(tmp_path / "repo"))
    monkeypatch.setenv("CLAUDE_SESSION_ID", "s1")
    monkeypatch.delenv("BENCH_SITTING", raising=False)
    monkeypatch.chdir(project_dir)

    def run(*argv: str) -> tuple[int, str, str]:
        code = main(list(argv))
        captured = capsys.readouterr()
        return code, captured.out, captured.err

    # seed a small record
    run("sitting", "open", "--persona", "pi")
    _, _, err = run("hypothesis", "H1 original")
    h1 = err.split("recorded: ")[1].splitlines()[0].strip()
    run("hypothesis", "H2 refined", "--supersedes", h1)
    run("critique", "--target", "method", "--step", "qPCR", "--flaw", "confound")
    run("decide", "run known-answer test", "--because", "cheapest discriminating step")
    return run


class TestJournalShow:
    def test_show_is_structured_with_header_and_sections(self, env):
        code, out, err = env("journal", "show")
        assert code == 0
        assert out == "", "journal chrome belongs on stderr"
        assert "── lab" in err, "view opens with a project header rule"
        assert "HYPOTHESIS" in err, "sections carry uppercase labels"
        assert "│ " in err, "long text renders in a guttered block"
        assert "H2 refined" in err
        assert "2 hypotheses" in err and "1 open" in err
        assert "run known-answer test" in err

    def test_show_pluralizes_correctly(self, env):
        _, _, err = env("journal", "show")
        assert "1 decision" in err and "1 decisions" not in err
        assert "1 sitting" in err and "1 sittings" not in err

    def test_show_never_wraps_mid_word_in_plain(self, env):
        _, _, err = env("journal", "show")
        for line in err.splitlines():
            assert len(line) <= 100, f"overlong plain line: {line!r}"

    def test_show_flags_open_critiques_as_warnings(self, env):
        _, _, err = env("journal", "show")
        assert "⚠" in err and "qPCR" in err


class TestJournalTables:
    def test_hypotheses_view_is_a_table_with_supersession_glyphs(self, env):
        code, _, err = env("journal", "hypotheses")
        assert code == 0
        lines = [l for l in err.splitlines() if l.strip()]
        header = next(l for l in lines if "HYPOTHESIS" in l)
        assert "ID" in header
        superseded_row = next(l for l in lines if "H1 original" in l)
        current_row = next(l for l in lines if "H2 refined" in l)
        assert "−" in superseded_row or "superseded" in superseded_row
        assert "✓" in current_row

    def test_critiques_view_shows_state_column(self, env):
        code, _, err = env("journal", "critiques")
        assert code == 0
        assert "⚠" in err and "confound" in err and "qPCR" in err

    def test_sittings_view_tabulates(self, env):
        code, _, err = env("journal", "sittings")
        assert code == 0
        assert "PERSONA" in err and "pi" in err


class TestJournalEvents:
    def test_events_json_is_pure_stdout(self, env):
        code, out, err = env("journal", "events", "--json")
        assert code == 0
        for line in out.strip().splitlines():
            json.loads(line)


def test_recall_all_exposes_older_decisions_without_rewriting_journal(env):
    for i in range(6):
        assert env("decide", f"Later decision {i}", "--because", "Synthetic follow-up")[0] == 0
    _, before, _ = env("journal", "events", "--json")
    code, recent, _ = env("recall", "--json")
    assert code == 0 and len(json.loads(recent)["recent_decisions"]) == 5
    code, full, _ = env("recall", "--all", "--json")
    assert code == 0
    assert json.loads(full)["recent_decisions"][0]["decision"] == "run known-answer test"
    assert len(json.loads(full)["recent_decisions"]) == 7
    _, after, _ = env("journal", "events", "--json")
    assert before == after
