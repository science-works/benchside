"""Project-bound commands require `bench init` first.

/pi loading from a parent directory and bench running anywhere meant sittings
could be opened in never-inited directories, creating accidental projects.
Now: no .bench/config.yaml (walking up) -> refuse with guidance.
"""

import pytest

from benchside.cli.main import main

MINIMAL_PI = """
id: pi
stance: s
voice: v
expertise: [x]
flow:
  close_requires: []
"""


@pytest.fixture
def env(tmp_path, monkeypatch, capsys):
    home = tmp_path / "home"
    workdir = tmp_path / "somewhere"
    workdir.mkdir()
    content = tmp_path / "repo" / "content"
    (content / "personas").mkdir(parents=True)
    (content / "templates").mkdir(parents=True)
    (content / "personas" / "pi.yaml").write_text(MINIMAL_PI)
    (content / "templates" / "skill.md.tmpl").write_text(
        "---\nname: {{PERSONA_ID}}\ndescription: d\n---\n\n{{FLOW}}\n"
    )
    monkeypatch.setenv("BENCHSIDE_HOME", str(home))
    monkeypatch.setenv("BENCHSIDE_REPO", str(tmp_path / "repo"))
    monkeypatch.setenv("CLAUDE_SESSION_ID", "s1")
    monkeypatch.delenv("BENCH_SITTING", raising=False)
    monkeypatch.chdir(workdir)

    def run(*argv: str) -> tuple[int, str]:
        code = main(list(argv))
        out = capsys.readouterr()
        return code, out.out + out.err

    return run, workdir, monkeypatch


class TestInitRequired:
    @pytest.mark.parametrize(
        "argv",
        [
            ("open", "--persona", "pi"),
            ("hypothesis", "X causes Y"),
            ("status",),
            ("recall",),
            ("close", "--abandoned", "--outcome", "n/a"),
        ],
    )
    def test_project_commands_refuse_without_init(self, env, argv):
        run, _, _ = env
        code, out = run(*argv)
        assert code != 0
        assert "bench init" in out, f"{argv[0]} must point at bench init"

    def test_open_works_after_init(self, env):
        run, _, _ = env
        assert run("init", "--yes")[0] == 0
        code, _ = run("open", "--persona", "pi")
        assert code == 0

    def test_bench_sitting_override_bypasses_guard_for_cleanup(self, env):
        run, workdir, monkeypatch = env
        run("init", "--yes")
        _, out = run("open", "--persona", "pi")
        sitting_id = out.split("<bench-sitting:")[1].split(">")[0]

        elsewhere = workdir.parent / "uninited"
        elsewhere.mkdir()
        monkeypatch.chdir(elsewhere)
        monkeypatch.setenv("BENCH_SITTING", sitting_id)
        code, _ = run("close", "--abandoned", "--outcome", "cleanup from elsewhere")
        assert code == 0


class TestSetup:
    def test_setup_installs_user_level_init_skill(self, env, tmp_path, monkeypatch):
        run, _, _ = env
        # setup ships a static asset from the real content tree
        monkeypatch.delenv("BENCHSIDE_REPO", raising=False)
        monkeypatch.setenv("HOME", str(tmp_path / "userhome"))
        code, out = run("setup")
        assert code == 0
        skill = tmp_path / "userhome" / ".claude" / "skills" / "bench-init" / "SKILL.md"
        assert skill.is_file()
        assert "bench init" in skill.read_text()
        # idempotent
        assert run("setup")[0] == 0
