"""bench init (the installer) and the session lifecycle hooks."""

import json

import pytest

from benchside.cli.main import main

MINIMAL_TEMPLATE = """---
name: {{PERSONA_ID}}
description: "{{PERSONA_STANCE}}"
---

{{FLOW}}
"""

MINIMAL_PI = """
id: pi
stance: A rigorous but caring PI.
voice: Direct.
expertise: [experimental design]
flow:
  phases:
    - id: actual-question
      goal: Find the actual question
      guidance: Press for a falsifiable statement.
      captures: [hypothesis]
      exit_when: A hypothesis is recorded.
  close_requires:
    - kind: hypothesis
      minimum: 1
"""


@pytest.fixture
def env(tmp_path, monkeypatch, capsys):
    home = tmp_path / "home"
    project_dir = tmp_path / "lab" / "chd7-study"
    project_dir.mkdir(parents=True)
    content = tmp_path / "repo" / "content"
    (content / "personas").mkdir(parents=True)
    (content / "templates").mkdir(parents=True)
    (content / "personas" / "pi.yaml").write_text(MINIMAL_PI)
    (content / "templates" / "skill.md.tmpl").write_text(MINIMAL_TEMPLATE)
    monkeypatch.setenv("BENCHSIDE_HOME", str(home))
    monkeypatch.setenv("BENCHSIDE_REPO", str(tmp_path / "repo"))
    monkeypatch.setenv("CLAUDE_SESSION_ID", "sess-1")
    monkeypatch.delenv("BENCH_SITTING", raising=False)
    monkeypatch.chdir(project_dir)

    def run(*argv: str, stdin: str = "") -> tuple[int, str]:
        import io
        import sys

        monkeypatch.setattr(sys, "stdin", io.StringIO(stdin))
        code = main(list(argv))
        out = capsys.readouterr()
        return code, out.out + out.err

    return run, home, project_dir


class TestInit:
    def test_init_materializes_config_skill_and_hooks(self, env):
        run, home, project_dir = env
        code, out = run("init", "--yes")
        assert code == 0

        config = project_dir / ".bench" / "config.yaml"
        assert config.is_file() and "chd7-study" in config.read_text()

        skill = project_dir / ".claude" / "skills" / "pi" / "SKILL.md"
        assert skill.is_file() and "Find the actual question" in skill.read_text()

        settings = json.loads((project_dir / ".claude" / "settings.json").read_text())
        assert "SessionStart" in settings["hooks"] and "SessionEnd" in settings["hooks"]
        assert "local" in out.lower(), "init must state that data stays local"

    def test_init_is_idempotent(self, env):
        run, _, project_dir = env
        run("init", "--yes")
        run("init", "--yes")
        settings = json.loads((project_dir / ".claude" / "settings.json").read_text())
        assert len(settings["hooks"]["SessionStart"]) == 1
        assert len(settings["hooks"]["SessionEnd"]) == 1


class TestHooks:
    def hook_stdin(self, project_dir, **extra) -> str:
        return json.dumps(
            {
                "session_id": "sess-1",
                "cwd": str(project_dir),
                "transcript_path": extra.pop("transcript_path", ""),
                **extra,
            }
        )

    def test_session_start_bails_silently_outside_benchside_projects(self, env, tmp_path):
        run, _, _ = env
        outside = tmp_path / "elsewhere"
        outside.mkdir()
        code, out = run(
            "hook", "session-start", stdin=self.hook_stdin(outside, source="startup")
        )
        assert code == 0
        assert out.strip() == ""

    def test_session_start_injects_recall(self, env):
        run, _, project_dir = env
        run("init", "--yes")
        run("sitting", "open", "--persona", "pi")
        run("hypothesis", "CHD7 loss reduces migration")
        code, out = run(
            "hook", "session-start", stdin=self.hook_stdin(project_dir, source="startup")
        )
        assert code == 0
        assert "CHD7 loss reduces migration" in out

    def test_session_end_archives_transcript_and_retires_pointer(self, env, tmp_path):
        run, home, project_dir = env
        run("init", "--yes")
        run("sitting", "open", "--persona", "pi")

        transcript = tmp_path / "transcript.jsonl"
        transcript.write_text('{"role":"user"}\n')
        code, out = run(
            "hook",
            "session-end",
            stdin=self.hook_stdin(
                project_dir, transcript_path=str(transcript), session_end_reason="clear"
            ),
        )
        assert code == 0
        archived = list((home / "projects" / "chd7-study" / "transcripts").glob("*.jsonl"))
        assert len(archived) == 1, "transcript must be archived under the project"

        # The pointer is retired: a capture command no longer finds a sitting.
        code, out = run("hypothesis", "another idea")
        assert code != 0

        # But the sitting was NOT auto-closed; the next session hears about it.
        code, out = run(
            "hook", "session-start", stdin=self.hook_stdin(project_dir, source="startup")
        )
        assert code == 0
        assert "still open" in out.lower()

    def test_hooks_always_exit_zero_on_garbage_stdin(self, env):
        run, _, _ = env
        code, _ = run("hook", "session-start", stdin="not json{{{")
        assert code == 0
        code, _ = run("hook", "session-end", stdin="")
        assert code == 0
