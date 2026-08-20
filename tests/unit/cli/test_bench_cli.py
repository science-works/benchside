"""The bench CLI: dispatch, sitting lifecycle, invariants at the boundary.

These tests drive main(argv) exactly as a skill's bash block would, against a
temp BENCHSIDE_HOME, and assert on exit codes, output, and journal effects.
"""

import json

import pytest

from benchside.cli.main import main


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
    monkeypatch.setenv("BENCHSIDE_HOME", str(home))
    monkeypatch.setenv("BENCHSIDE_REPO", str(tmp_path / "repo"))
    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
    monkeypatch.delenv("BENCH_SITTING", raising=False)
    monkeypatch.chdir(project_dir)

    def run(*argv: str) -> tuple[int, str]:
        code = main(list(argv))
        out = capsys.readouterr()
        return code, out.out + out.err

    return run, home, project_dir


class TestProjectResolution:
    def test_project_falls_back_to_directory_name(self, env):
        run, _, _ = env
        code, out = run("project")
        assert code == 0
        assert "chd7-study" in out

    def test_config_file_wins(self, env):
        run, _, project_dir = env
        (project_dir / ".bench").mkdir()
        (project_dir / ".bench" / "config.yaml").write_text("project: my-real-line\n")
        code, out = run("project")
        assert code == 0
        assert "my-real-line" in out


class TestSittingLifecycle:
    def test_open_prints_marker_and_creates_pointer(self, env):
        run, home, _ = env
        code, out = run("open", "--persona", "pi")
        assert code == 0
        assert "<bench-sitting:" in out
        pointers = list((home / "sessions").glob("*.json"))
        assert len(pointers) == 1

    def test_capture_without_open_sitting_fails_helpfully(self, env):
        run, _, _ = env
        code, out = run("hypothesis", "CHD7 loss reduces migration")
        assert code != 0
        assert "bench open" in out, "error must tell the model what to do next"

    def test_full_sitting_flow_with_close_enforcement(self, env):
        run, _, _ = env
        run("open", "--persona", "pi")

        code, out = run("close", "--converged", "--outcome", "done")
        assert code != 0, "converged close with no hypothesis must be refused"
        assert "hypothesis" in out

        code, out = run("hypothesis", "CHD7 loss reduces migration speed")
        assert code == 0

        code, out = run(
            "critique", "--target", "method", "--step", "qPCR", "--flaw", "confound"
        )
        assert code == 0
        critique_id = json.loads(run("status", "--json")[1])["open_critiques"][0]

        code, out = run("close", "--converged", "--outcome", "done")
        assert code != 0, "cannot converge with an open critique"

        code, out = run("resolve", critique_id, "--as", "design_revised")
        assert code == 0

        code, out = run("close", "--converged", "--outcome", "add batch control")
        assert code == 0

        code, out = run("recall")
        assert code == 0
        assert "CHD7 loss reduces migration speed" in out

    def test_invalid_flaw_lists_the_taxonomy(self, env):
        run, _, _ = env
        run("open", "--persona", "pi")
        run("hypothesis", "H")
        code, out = run(
            "critique", "--target", "method", "--step", "s", "--flaw", "confund"
        )
        assert code != 0
        assert "missing_control" in out, "error must list valid flaws"


class TestGapAndConsent:
    def test_gap_capture_and_consent_gated_export(self, env):
        run, _, _ = env
        run("open", "--persona", "pi")
        code, _ = run(
            "gap", "missing_index", "--question", "has this assay been run on this organism?"
        )
        assert code == 0

        code, out = run("export")
        assert code != 0
        assert "consent" in out.lower()

        code, _ = run("consent", "grant", "--kinds", "missing_index")
        assert code == 0
        code, out = run("export", "--preview")
        assert code == 0
        assert "has this assay been run" in out
        assert "redaction" in out.lower(), "preview must label redaction status"
