"""Sitting pointers must be project-scoped (regression: cross-project bleed).

The reproduced field bug: /pi run in the wrong directory left a live pointer;
a new session in the right directory adopted it via the single-live-pointer
fallback, reporting "a sitting is already open" for a different project — and
captures would have landed in the wrong project's journal.
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
    wrong = tmp_path / "wrong-dir"
    right = tmp_path / "right-project"
    wrong.mkdir()
    right.mkdir()
    for directory in (wrong, right):
        (directory / ".bench").mkdir()
        (directory / ".bench" / "config.yaml").write_text(f"project: {directory.name}\n")
    content = tmp_path / "repo" / "content"
    (content / "personas").mkdir(parents=True)
    (content / "templates").mkdir(parents=True)
    (content / "personas" / "pi.yaml").write_text(MINIMAL_PI)
    monkeypatch.setenv("BENCHSIDE_HOME", str(home))
    monkeypatch.setenv("BENCHSIDE_REPO", str(tmp_path / "repo"))
    monkeypatch.delenv("BENCH_SITTING", raising=False)

    def run(*argv: str) -> tuple[int, str]:
        code = main(list(argv))
        out = capsys.readouterr()
        return code, out.out + out.err

    return run, home, wrong, right, monkeypatch


def open_in_wrong_dir_then_move(run, wrong, right, monkeypatch):
    """The field scenario: open in session-1/wrong dir, exit without hooks,
    reopen Claude (new session id) in the right dir."""
    monkeypatch.setenv("CLAUDE_SESSION_ID", "session-1")
    monkeypatch.chdir(wrong)
    code, _ = run("sitting", "open", "--persona", "pi")
    assert code == 0
    monkeypatch.setenv("CLAUDE_SESSION_ID", "session-2")
    monkeypatch.chdir(right)


class TestProjectScopedPointers:
    def test_foreign_project_pointer_is_not_adopted(self, env):
        run, _, wrong, right, monkeypatch = env
        open_in_wrong_dir_then_move(run, wrong, right, monkeypatch)

        code, out = run("sitting", "status")
        assert code != 0, "another project's sitting must not be adopted"
        assert "No open sitting" in out

    def test_open_succeeds_in_the_right_project(self, env):
        run, _, wrong, right, monkeypatch = env
        open_in_wrong_dir_then_move(run, wrong, right, monkeypatch)

        code, out = run("sitting", "open", "--persona", "pi")
        assert code == 0

    def test_captures_never_bleed_into_the_foreign_journal(self, env):
        run, home, wrong, right, monkeypatch = env
        open_in_wrong_dir_then_move(run, wrong, right, monkeypatch)
        run("sitting", "open", "--persona", "pi")
        code, _ = run("hypothesis", "recorded in the right project")
        assert code == 0

        wrong_journal = home / "projects" / "wrong-dir" / "journal.jsonl"
        right_journal = home / "projects" / "right-project" / "journal.jsonl"
        assert "recorded in the right project" in right_journal.read_text()
        assert "recorded in the right project" not in wrong_journal.read_text()

    def test_same_session_same_project_double_open_is_refused(self, env):
        run, _, _, right, monkeypatch = env
        monkeypatch.setenv("CLAUDE_SESSION_ID", "session-1")
        monkeypatch.chdir(right)
        run("sitting", "open", "--persona", "pi")
        code, out = run("sitting", "open", "--persona", "pi")
        assert code != 0
        assert "already open" in out and ("close" in out or "resume" in out)

    def test_env_override_still_reaches_a_foreign_sitting_for_cleanup(self, env):
        run, home, wrong, right, monkeypatch = env
        open_in_wrong_dir_then_move(run, wrong, right, monkeypatch)
        pointer = json.loads(
            next((home / "sessions").glob("session-1.json")).read_text()
        )
        monkeypatch.setenv("BENCH_SITTING", pointer["sitting_id"])
        code, out = run("sitting", "close", "--abandoned", "--outcome", "opened in wrong directory")
        assert code == 0, "explicit BENCH_SITTING must allow cross-project cleanup"
