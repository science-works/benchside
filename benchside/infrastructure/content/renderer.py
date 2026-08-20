"""Template rendering.

Expands {{PLACEHOLDER}} tokens against a persona and the shared block library.
Two rules, both enforced rather than documented: an unknown placeholder is a
hard error, and any token left unresolved after expansion is a hard error.
Silent empties are how generated prompts rot.
"""

import re
from collections.abc import Callable

from benchside.domain.authoring.model.persona import Persona
from benchside.domain.authoring.port.repository import TemplateRepository
from benchside.domain.shared.error import ValidationError

_TOKEN = re.compile(r"\{\{([A-Z_]+)\}\}")
_MAX_PASSES = 5


class PlaceholderRenderer:
    """Multi-pass so blocks may themselves contain placeholders."""

    def __init__(self, templates: TemplateRepository) -> None:
        self._templates = templates

    def render(self, template: str, persona: Persona) -> str:
        resolvers = self._resolvers(persona)
        text = template
        for _ in range(_MAX_PASSES):
            if not _TOKEN.search(text):
                break
            text = _TOKEN.sub(lambda m: self._resolve(m.group(1), resolvers), text)
        remaining = _TOKEN.findall(text)
        if remaining:
            raise ValidationError(f"Unresolved placeholders after {_MAX_PASSES} passes: {remaining}")
        return text

    def _resolve(self, name: str, resolvers: dict[str, Callable[[], str]]) -> str:
        if name in resolvers:
            return resolvers[name]()
        block = self._templates.block(name.lower().replace("_", "-"))
        if block is not None:
            return block
        raise ValidationError(f"Unknown placeholder: {{{{{name}}}}}")

    def _resolvers(self, persona: Persona) -> dict[str, Callable[[], str]]:
        return {
            "PERSONA_ID": lambda: persona.id.root,
            "PERSONA_STANCE": lambda: persona.stance,
            "PERSONA_VOICE": lambda: persona.voice,
            "PERSONA_EXPERTISE": lambda: ", ".join(persona.expertise),
            "FORCING_QUESTIONS": lambda: _forcing_questions(persona),
            "FAILURE_MODES": lambda: _failure_modes(persona),
            "ESCALATION_RULES": lambda: _escalation_rules(persona),
        }


def _forcing_questions(persona: Persona) -> str:
    if not persona.forcing_questions:
        return "_No forcing questions declared._"
    parts = []
    for i, q in enumerate(persona.forcing_questions, start=1):
        flags = "\n".join(f"  - {flag}" for flag in q.red_flags)
        parts.append(
            f"### Q{i}. {q.ask}\n\n"
            f"**Push until you hear:** {q.push_until}\n\n"
            f"**Red flags — they are dodging if you hear:**\n{flags}"
        )
    return "\n\n".join(parts)


def _failure_modes(persona: Persona) -> str:
    if not persona.failure_modes:
        return "_No failure modes declared._"
    return "\n".join(f"- **{f.name}** — {f.description}" for f in persona.failure_modes)


def _escalation_rules(persona: Persona) -> str:
    if not persona.escalation_rules:
        return "_No escalation rules declared._"
    return "\n".join(f"- {rule}" for rule in persona.escalation_rules)
