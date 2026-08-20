"""Loading persona records and templates from content/.

Personas are authored as YAML. Adding a specialist means adding a file here --
never touching orchestration code.
"""

import logging
from pathlib import Path
from typing import Any

import yaml

from benchside.domain.authoring.model.flow import Flow, Phase
from benchside.domain.authoring.model.persona import Persona
from benchside.domain.authoring.model.value import FailureMode, ForcingQuestion
from benchside.domain.shared.error import ValidationError
from benchside.domain.shared.model.ids import PersonaId

logger = logging.getLogger(__name__)


class YamlPersonaRepository:
    def __init__(self, personas_dir: Path) -> None:
        self._dir = personas_dir

    def get(self, persona_id: PersonaId) -> Persona | None:
        path = self._dir / f"{persona_id.root}.yaml"
        if not path.exists():
            return None
        return self._parse(path)

    def list_all(self) -> list[Persona]:
        if not self._dir.exists():
            return []
        return [self._parse(p) for p in sorted(self._dir.glob("*.yaml"))]

    def _parse(self, path: Path) -> Persona:
        raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        try:
            return Persona(
                id=PersonaId(raw.get("id", path.stem)),
                stance=raw["stance"],
                expertise=tuple(raw.get("expertise", ())),
                voice=raw["voice"],
                forcing_questions=tuple(
                    ForcingQuestion(
                        ask=q["ask"],
                        push_until=q["push_until"],
                        red_flags=tuple(q.get("red_flags", ())),
                    )
                    for q in raw.get("forcing_questions", ())
                ),
                failure_modes=tuple(
                    FailureMode(name=f["name"], description=f["description"])
                    for f in raw.get("failure_modes", ())
                ),
                escalation_rules=tuple(raw.get("escalation_rules", ())),
                flow=_parse_flow(raw.get("flow", {})),
            )
        except (KeyError, TypeError, ValueError) as err:
            raise ValidationError(f"Malformed persona record at {path}: {err}") from err


def _parse_flow(raw: dict[str, Any]) -> Flow:
    from benchside.domain.shared.model.capture import CaptureKind, CloseRequirement

    return Flow(
        phases=tuple(
            Phase(
                id=p["id"],
                goal=p["goal"],
                guidance=p.get("guidance", ""),
                captures=tuple(CaptureKind(c) for c in p.get("captures", ())),
                exit_when=p.get("exit_when", ""),
            )
            for p in raw.get("phases", ())
        ),
        close_requires=tuple(
            CloseRequirement(kind=CaptureKind(r["kind"]), minimum=int(r.get("minimum", 1)))
            for r in raw.get("close_requires", ())
        ),
    )


class FileTemplateRepository:
    def __init__(self, templates_dir: Path) -> None:
        self._dir = templates_dir

    def skill_template(self) -> str:
        path = self._dir / "skill.md.tmpl"
        if not path.exists():
            raise ValidationError(f"Missing skill template at {path}")
        return path.read_text(encoding="utf-8")

    def block(self, name: str) -> str | None:
        path = self._dir / "blocks" / f"{name}.md"
        return path.read_text(encoding="utf-8") if path.exists() else None
