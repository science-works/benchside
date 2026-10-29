"""Build the same agent instructions from source installs and release packaging."""

import shutil
from pathlib import Path

from benchside.config import resolve_content_root
from benchside.infrastructure.content.loader import FileTemplateRepository, YamlPersonaRepository
from benchside.infrastructure.content.renderer import PlaceholderRenderer


def build_agent_skill(target: Path):
    content = resolve_content_root()
    shutil.copytree(content / "app", target, dirs_exist_ok=True)
    renderer = PlaceholderRenderer(FileTemplateRepository(content / "templates"), app=True)
    template = (content / "templates/app-role.md.tmpl").read_text()
    roles = target / "references/roles"
    roles.mkdir(parents=True, exist_ok=True)
    for persona in YamlPersonaRepository(content / "personas").list_all():
        (roles / f"{persona.id.root}.md").write_text(renderer.render(template, persona))
