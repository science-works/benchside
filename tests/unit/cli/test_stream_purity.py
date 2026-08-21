"""Machine channels stay pure: JSON and markers on stdout, chrome on stderr."""

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

    return run


class TestStreamPurity:
    def test_status_json_stdout_is_pure_json(self, env):
        env("sitting", "open", "--persona", "pi")
        code, out, _ = env("sitting", "status", "--json")
        assert code == 0
        json.loads(out)  # must parse as-is: chrome may not leak onto stdout

    def test_open_marker_is_on_stdout_chrome_on_stderr(self, env):
        code, out, err = env("sitting", "open", "--persona", "pi")
        assert code == 0
        assert "<bench-sitting:" in out
        assert "Sitting open" in err, "human chrome belongs on stderr"

    def test_errors_go_to_stderr(self, env, tmp_path, monkeypatch):
        outside = tmp_path / "uninited"
        outside.mkdir()
        monkeypatch.chdir(outside)
        code, out, err = env("sitting", "status")
        assert code != 0
        assert out == ""
        assert "bench init" in err
