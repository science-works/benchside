"""The Persona aggregate: a collaborator archetype.

Read-only at runtime. Personas change by editing content/personas/ and
recompiling, never by a command from a consultation.
"""

from benchside.domain.authoring.model.flow import Flow
from benchside.domain.authoring.model.value import (
    FailureMode,
    ForcingQuestion,
    Rubric,
    RubricCriterion,
)
from benchside.domain.shared.error import ValidationError
from benchside.domain.shared.model.aggregate import Aggregate
from benchside.domain.shared.model.capture import RecordKind
from benchside.domain.shared.model.ids import PersonaId


class Persona(Aggregate):
    id: PersonaId
    title: str = "Research supervisor"
    description: str = "Discuss research direction, hypotheses, priorities and next experiments."
    version: str = "1"
    critique_requires_hypothesis: bool = True
    record_kind: RecordKind | None = None
    stance: str
    expertise: tuple[str, ...]
    voice: str
    forcing_questions: tuple[ForcingQuestion, ...] = ()
    failure_modes: tuple[FailureMode, ...] = ()
    escalation_rules: tuple[str, ...] = ()
    flow: Flow = Flow()

    def rubric(self) -> Rubric:
        """Derive the judge rubric from this persona's failure modes.

        Generated rather than authored so a persona can never have a rubric
        that tests something it was not built to do.
        """
        if not self.failure_modes:
            raise ValidationError(
                f"Persona {self.id.root} declares no failure modes, so it cannot be evaluated",
                field="failure_modes",
            )
        return Rubric(
            persona_id=self.id.root,
            criteria=tuple(
                RubricCriterion(
                    name=mode.name,
                    question=f"Did the response avoid this failure: {mode.description}",
                    derived_from=mode.name,
                )
                for mode in self.failure_modes
            ),
        )
