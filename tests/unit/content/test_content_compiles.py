"""The shipped content must always load and compile (tier-1 static gate).

These tests run against the real content/ tree — no fixtures. A persona that
fails here is unshippable, whatever its prose reads like.
"""

import yaml

from benchside.config import resolve_content_root
from benchside.domain.authoring.model.persona import Persona
from benchside.domain.authoring.service.authoring import AuthoringService
from benchside.domain.shared.model.capture import CaptureKind
from benchside.domain.shared.model.ids import PersonaId
from benchside.infrastructure.content.loader import (
    FileTemplateRepository,
    YamlPersonaRepository,
)
from benchside.infrastructure.content.renderer import PlaceholderRenderer


def load_pi() -> Persona:
    persona = YamlPersonaRepository(resolve_content_root() / "personas").get(PersonaId("pi"))
    assert persona is not None, "content/personas/pi.yaml must exist"
    return persona


def compile_pi() -> str:
    templates = FileTemplateRepository(resolve_content_root() / "templates")
    persona = load_pi()
    return PlaceholderRenderer(templates).render(templates.skill_template(), persona)


class TestPiPersona:
    def test_pi_declares_a_complete_flow(self):
        persona = load_pi()
        assert len(persona.flow.phases) >= 3
        assert any(
            CaptureKind.HYPOTHESIS in phase.captures for phase in persona.flow.phases
        ), "some phase must capture a hypothesis"
        kinds = {r.kind for r in persona.flow.close_requires}
        assert CaptureKind.HYPOTHESIS in kinds

    def test_pi_is_evaluable(self):
        """No failure modes -> no rubric -> unverifiable persona."""
        rubric = load_pi().rubric()
        assert len(rubric.criteria) >= 3

    def test_pi_has_forcing_questions_with_red_flags(self):
        persona = load_pi()
        assert len(persona.forcing_questions) >= 3
        assert all(q.push_until for q in persona.forcing_questions)

    def test_skill_compiles_with_valid_frontmatter(self):
        text = compile_pi()
        assert text.lstrip().startswith("---")
        _, frontmatter, body = text.split("---", 2)
        meta = yaml.safe_load(frontmatter)
        assert meta["name"] == "pi"
        assert "bench" in meta["allowed-tools"], "bench calls must be pre-approved"
        assert "description" in meta

    def test_skill_body_carries_the_contract(self):
        body = compile_pi()
        assert "bench hypothesis" in body, "capture obligations must be explicit"
        assert "bench close" in body
        assert "bench gap" in body, "gap capture must be instructed"
        assert "recommend" in body.lower(), "user sovereignty must be stated"
