"""bench init: the installer for a research project.

Everything an external scientist needs, one command: project identity pinned
in .bench/config.yaml, lifecycle hooks registered (with consent — Claude Code
executes project hooks without prompting, so the consent moment is ours), and
the /pi skill compiled into the project's .claude/skills/ where Claude Code
auto-discovers it.
"""

import json
import sys
from pathlib import Path

from benchside.application.di import create_container
from benchside.cli import runtime
from benchside.domain.authoring.port.renderer import TemplateRenderer
from benchside.domain.authoring.port.repository import PersonaRepository, TemplateRepository
from benchside.domain.authoring.service.authoring import AuthoringService
from benchside.infrastructure.content.writer import FileSkillWriter
from benchside.util.di import Scope

_TAG = "_benchside"
_HOOK_TIMEOUTS = {"SessionStart": 10, "SessionEnd": 15}

LOCAL_DATA_NOTE = """\
Your data stays local. Sittings, hypotheses, critiques, and transcripts are
written only to ~/.benchside/ on this machine. Nothing is shared unless you
explicitly run `bench consent grant` — and `bench export --preview` always
shows you the exact bytes before anything leaves."""


def cmd_init(args) -> int:
    project_dir = Path.cwd()
    project_id = runtime.resolve_project(args.project)

    if not args.yes and not _confirm(
        "bench init will write .bench/config.yaml, register two session hooks in "
        ".claude/settings.json, and compile the /pi skill into .claude/skills/. Proceed?"
    ):
        print("init cancelled; nothing written")
        return 1

    config = project_dir / ".bench" / "config.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    if not config.is_file():
        config.write_text(f"project: {project_id.root}\n", encoding="utf-8")

    _register_hooks(project_dir / ".claude" / "settings.json")
    _compile_skills(project_dir / ".claude" / "skills")

    print(f"initialized benchside project '{project_id.root}'")
    print("  .bench/config.yaml — project identity")
    print("  .claude/settings.json — SessionStart/SessionEnd hooks (tagged, idempotent)")
    print("  .claude/skills/pi/SKILL.md — the /pi supervisor persona")
    print()
    print(LOCAL_DATA_NOTE)
    return 0


def _confirm(prompt: str) -> bool:
    if not sys.stdin.isatty():
        print("non-interactive session: pass --yes to consent to init", file=sys.stderr)
        return False
    return input(f"{prompt} [y/N] ").strip().lower() in {"y", "yes"}


def _register_hooks(settings_path: Path) -> None:
    """Idempotent under the _benchside tag; never clobbers other hooks."""
    settings: dict = {}
    if settings_path.is_file():
        settings = json.loads(settings_path.read_text(encoding="utf-8") or "{}")
    hooks = settings.setdefault("hooks", {})
    for event, subcommand in (("SessionStart", "session-start"), ("SessionEnd", "session-end")):
        groups = hooks.setdefault(event, [])
        if any(group.get(_TAG) for group in groups):
            continue
        groups.append(
            {
                _TAG: "v1",
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"bench hook {subcommand}",
                        "timeout": _HOOK_TIMEOUTS[event],
                    }
                ],
            }
        )
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")


def _compile_skills(target_dir: Path) -> None:
    """Compile personas straight into the project's skill directory."""
    container = create_container()
    with container, container(scope=Scope.UOW) as uow:
        service = AuthoringService(
            personas=uow.get(PersonaRepository),
            templates=uow.get(TemplateRepository),
            renderer=uow.get(TemplateRenderer),
            writer=FileSkillWriter(target_dir),
        )
        service.compile()


def cmd_setup(args) -> int:
    """One-time machine setup: install the user-level /bench-init skill.

    This is the only skill that lives at user level — it must exist BEFORE any
    project is inited, because it is how init happens from inside Claude.
    Everything else is per-project, installed by bench init.
    """
    from benchside.config import resolve_content_root

    source = resolve_content_root() / "claude" / "bench-init" / "SKILL.md"
    target = Path.home() / ".claude" / "skills" / "bench-init" / "SKILL.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"installed /bench-init skill -> {target}")
    print("In any project directory, a Claude session can now run /bench-init.")
    return 0
