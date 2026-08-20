"""Authoring business logic: personas in, skills and rubrics out.

Compilation is deliberately pure of I/O beyond its ports, so `bench check` can
run it in dry-run mode and compare against what is on disk.
"""

import logging

from benchside.domain.authoring.model.persona import Persona
from benchside.domain.authoring.model.skill import CompileReport, SkillDocument
from benchside.domain.authoring.model.value import Rubric
from benchside.domain.authoring.port.renderer import TemplateRenderer
from benchside.domain.authoring.port.repository import PersonaRepository, TemplateRepository
from benchside.domain.authoring.port.skill_writer import SkillWriter
from benchside.domain.shared.error import NotFoundError, ValidationError
from benchside.domain.shared.model.ids import PersonaId
from benchside.domain.shared.service import Service

logger = logging.getLogger(__name__)

_FENCE = "---"


def _split_frontmatter(text: str, persona_id: str) -> tuple[str, str]:
    stripped = text.lstrip()
    if not stripped.startswith(_FENCE):
        raise ValidationError(
            f"Rendered skill for {persona_id} has no frontmatter fence", field="template"
        )
    rest = stripped[len(_FENCE) :]
    end = rest.find(f"\n{_FENCE}")
    if end == -1:
        raise ValidationError(
            f"Rendered skill for {persona_id} has an unterminated frontmatter fence",
            field="template",
        )
    return rest[:end].strip("\n"), rest[end + len(_FENCE) + 1 :].lstrip("\n")


class AuthoringService(Service):
    personas: PersonaRepository
    templates: TemplateRepository
    renderer: TemplateRenderer
    writer: SkillWriter

    def get(self, persona_id: PersonaId) -> Persona:
        persona = self.personas.get(persona_id)
        if persona is None:
            raise NotFoundError(f"Persona not found: {persona_id.root}")
        return persona

    def list_all(self) -> list[Persona]:
        return self.personas.list_all()

    def rubric(self, persona_id: PersonaId) -> Rubric:
        return self.get(persona_id).rubric()

    def compile(self, *, dry_run: bool = False) -> CompileReport:
        """Render every persona into a skill document.

        With dry_run, nothing is written and the report's `stale` list names
        the files that would change -- the CI freshness gate.
        """
        template = self.templates.skill_template()
        written: list[str] = []
        unchanged: list[str] = []
        stale: list[str] = []

        for persona in self.personas.list_all():
            document = self._render(persona, template)
            existing = self.writer.read_existing(document.filename)
            if existing == document.render():
                unchanged.append(document.filename)
                continue
            stale.append(document.filename)
            if not dry_run:
                self.writer.write(document)
                written.append(document.filename)

        return CompileReport(
            written=tuple(written),
            unchanged=tuple(unchanged),
            stale=tuple(stale) if dry_run else (),
        )

    def _render(self, persona: Persona, template: str) -> SkillDocument:
        """Render a persona into a skill document.

        The template carries its own YAML frontmatter fence; splitting here
        rather than in the renderer keeps the renderer a pure text expander.
        """
        text = self.renderer.render(template, persona)
        frontmatter, body = _split_frontmatter(text, persona.id.root)
        return SkillDocument(
            persona_id=persona.id.root,
            filename=f"{persona.id.root}/SKILL.md",
            frontmatter=frontmatter,
            body=body,
        )
