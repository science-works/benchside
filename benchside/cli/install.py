"""Install shared agent instructions and optional legacy Claude Code project hooks."""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

from benchside.application.di import create_container
from benchside.cli import runtime
from benchside.domain.authoring.port.renderer import TemplateRenderer
from benchside.domain.authoring.port.repository import PersonaRepository, TemplateRepository
from benchside.domain.authoring.service.authoring import AuthoringService
from benchside.infrastructure.content.writer import FileSkillWriter
from benchside.infrastructure.files import atomic_json
from benchside.util.di import Scope

_TAG = "_benchside"
_HOOK_TIMEOUTS = {"SessionStart": 10, "SessionEnd": 15}


def _skill_directory(args, root: Path) -> Path:
    if args.skills_dir:
        return Path(args.skills_dir).expanduser().resolve()
    return root / (".claude" if args.agent == "claude" else ".agents") / "skills"


def _configure_storage(args):
    if args.storage:
        from benchside.config import configure_local_storage

        configure_local_storage(args.storage)


def _install_app_skill(target: Path):
    from benchside.application.packaging import build_agent_skill
    from benchside.config import resolve_content_root
    from benchside.infrastructure.files import atomic_json

    if (resolve_content_root() / "app").is_dir():
        _retire_legacy_skills(target)
        skill = target / "benchside"
        build_agent_skill(skill)
        # Preserve the venv executable path: resolving its symlink would lose
        # the environment's dependencies in a later conversation.
        atomic_json(
            skill / "runtime/source.json",
            {
                "schema": "benchside.source.v1",
                "python": str(Path(sys.executable).absolute()),
                "package_root": str(Path(__file__).resolve().parents[2]),
            },
        )


def cmd_init(args) -> int:
    project_dir = Path.cwd()
    project_id = runtime.resolve_project(args.project)
    target = _skill_directory(args, project_dir)
    legacy = args.legacy_cli
    if legacy and args.agent != "claude":
        raise ValueError("--legacy-cli is only available with --agent claude")
    hooks = legacy
    details = " and register Claude Code session hooks" if hooks else ""
    if not args.yes and not _confirm(
        f"Create .bench/config.yaml, install Benchside into {target}{details}?"
    ):
        print("init cancelled; nothing written")
        return 1
    _configure_storage(args)
    config = project_dir / ".bench" / "config.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    if not config.is_file():
        config.write_text(f"project: {project_id.root}\n", encoding="utf-8")
    if hooks:
        _register_hooks(project_dir / ".claude" / "settings.json")
        _compile_skills(target, explicit=True)
    else:
        if args.agent == "claude":
            _remove_hooks(project_dir / ".claude" / "settings.json")
            from benchside.infrastructure.session_context import clear_project_sessions

            clear_project_sessions(runtime.current_paths(), runtime.resolve_project(cwd=project_dir))
        _install_app_skill(target)
    print(f"initialized benchside project '{project_id.root}'")
    print(f"  skills: {target}")
    print(f"  local record directory: {runtime.current_paths().home}")
    print("Optional submissions require separate consent and an approved preview.")
    if legacy:
        print("Legacy role commands are explicit-invocation-only and keep their existing CLI journal.")
    else:
        print("Ask Benchside to select existing app records before creating a new research project.")
        print("Legacy CLI journals are preserved separately; choose continuation or migration explicitly.")
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
    atomic_json(settings_path, settings)


def _remove_hooks(settings_path: Path) -> None:
    """Remove only Benchside-tagged lifecycle hooks when selecting the shared route."""
    if not settings_path.is_file():
        return
    settings = json.loads(settings_path.read_text(encoding="utf-8") or "{}")
    changed = False
    for event, groups in settings.get("hooks", {}).items():
        retained = [group for group in groups if group.get(_TAG) != "v1"]
        if len(retained) != len(groups):
            settings["hooks"][event] = retained
            changed = True
    if changed:
        atomic_json(settings_path, settings)


def _explicit_skill(text: str) -> str:
    return text.replace("---\n", "---\ndisable-model-invocation: true\n", 1)


def _retire_legacy_skills(target: Path) -> None:
    """Only recognize exact generated content, including known earlier release digests."""
    from benchside.config import resolve_content_root

    known = resolve_content_root() / "legacy-skill-digests.json"
    historical = json.loads(known.read_text()) if known.is_file() else {}
    changed = []
    with tempfile.TemporaryDirectory(prefix="benchside-legacy-check-") as temporary:
        expected = Path(temporary)
        _compile_skills(expected)
        for original in expected.glob("*/SKILL.md"):
            installed = target / original.relative_to(expected)
            if (
                not installed.is_file()
                or installed.is_symlink()
                or installed.parent.is_symlink()
            ):
                continue
            text = installed.read_text(encoding="utf-8")
            if text == original.read_text(encoding="utf-8") or (
                hashlib.sha256(text.encode()).hexdigest() in historical.get(original.parent.name, [])
            ):
                installed.write_text(_explicit_skill(text), encoding="utf-8")
                changed.append(original.parent.name)
            elif not text.startswith("---\ndisable-model-invocation: true\n"):
                print(
                    f"Preserved custom skill at {installed}; "
                    "review its invocation before using both routes."
                )
    if changed:
        names = ", ".join(f"/{name}" for name in sorted(changed))
        print(f"Updated legacy Benchside commands to explicit invocation only: {names}.")
        print("Their saved research records remain in the existing CLI journal.")


def _compile_skills(target_dir: Path, *, explicit: bool = False) -> None:
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
    import shutil

    from benchside.config import resolve_content_root
    from benchside.infrastructure.content.loader import YamlPersonaRepository

    sharing_skill = resolve_content_root() / "claude" / "bench-share"
    if sharing_skill.is_dir():  # Custom authoring roots may contain only personas.
        shutil.copytree(sharing_skill, target_dir / "bench-share", dirs_exist_ok=True)
    if explicit:
        names = {
            persona.id.root
            for persona in YamlPersonaRepository(resolve_content_root() / "personas").list_all()
        } | {"bench-share"}
        for path in target_dir.glob("*/SKILL.md"):
            if path.parent.name in names:
                path.write_text(_explicit_skill(path.read_text(encoding="utf-8")), encoding="utf-8")


def cmd_setup(args) -> int:
    """Install agent instructions without assuming a particular model or storage provider."""
    from benchside.config import resolve_content_root

    _configure_storage(args)
    target = _skill_directory(args, Path.home())
    _install_app_skill(target)
    if args.agent == "claude":
        source = resolve_content_root() / "claude" / "bench-init" / "SKILL.md"
        destination = target / "bench-init" / "SKILL.md"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"installed /bench-init skill -> {destination}")
    print(f"Benchside instructions installed in {target}.")
    print("Ask your agent to set up Benchside; it will ask where to store your records.")
    print(
        "Other agents can read benchside/SKILL.md explicitly if they do not discover skills here."
    )
    return 0
