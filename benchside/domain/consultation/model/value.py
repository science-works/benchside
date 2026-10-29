"""Consultation value objects.

Illegal combinations are unrepresentable: a sitting is in exactly one state,
and a critique always names its target.
"""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from benchside.domain.shared.model.capture import RecordKind
from benchside.domain.shared.model.ids import CritiqueId, DecisionId, HypothesisId
from benchside.domain.shared.model.value import ValueObject

# --- Sitting state (a sum, not a bag of flags) ---


class Framing(ValueObject):
    """Establishing what the actual question is."""

    kind: Literal["framing"] = "framing"


class Probing(ValueObject):
    """Forcing questions are being asked; nothing challenged yet."""

    kind: Literal["probing"] = "probing"


class Challenged(ValueObject):
    """At least one critique is open against the project."""

    open_critiques: tuple[CritiqueId, ...]
    kind: Literal["challenged"] = "challenged"


class Converged(ValueObject):
    """Agreed next step; no critique left open."""

    outcome: str
    kind: Literal["converged"] = "converged"


class Abandoned(ValueObject):
    """The sitting was dropped."""

    reason: str
    kind: Literal["abandoned"] = "abandoned"


State = Framing | Probing | Challenged | Converged | Abandoned

TERMINAL: frozenset[str] = frozenset({"converged", "abandoned"})


# --- What a critique can target ---


class MethodFlaw(StrEnum):
    """The closed taxonomy the planted-flaw eval fixtures draw from."""

    MISSING_CONTROL = "missing_control"
    CONFOUND = "confound"
    UNDER_POWERED = "under_powered"
    PSEUDOREPLICATION = "pseudoreplication"
    SELECTION_BIAS = "selection_bias"
    UNVALIDATED_INSTRUMENT = "unvalidated_instrument"


class TargetsClaim(ValueObject):
    claim: str
    ground: str
    kind: Literal["claim"] = "claim"


class TargetsMethod(ValueObject):
    step: str
    flaw: MethodFlaw
    kind: Literal["method"] = "method"


class TargetsInterpretation(ValueObject):
    result: str
    alternative: str
    kind: Literal["interpretation"] = "interpretation"


Target = TargetsClaim | TargetsMethod | TargetsInterpretation


class Resolution(StrEnum):
    DESIGN_REVISED = "design_revised"
    REBUTTED = "rebutted"
    ACCEPTED_AS_LIMITATION = "accepted_as_limitation"


# --- The durable record a project accumulates ---


class Hypothesis(ValueObject):
    id: HypothesisId
    statement: str
    supersedes: HypothesisId | None = None


class Critique(ValueObject):
    id: CritiqueId
    target: Target
    resolution: Resolution | None = None

    @property
    def is_open(self) -> bool:
        return self.resolution is None


class Decision(ValueObject):
    """A durable call and why it was made.

    Durable means an architecture or scope choice, or a reversal of one --
    not a turn-level edit. Curated at the source, or the record becomes noise.
    """

    id: DecisionId
    decision: str
    rationale: str
    decided_at: datetime
    supersedes: DecisionId | None = None


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ResearchRecord(ValueObject):
    """A role's scientific output, kept private in the project journal."""

    id: NonEmptyText
    kind: RecordKind
    summary: NonEmptyText
    details: tuple[NonEmptyText, ...] = Field(min_length=1)
    sources: tuple[NonEmptyText, ...] = ()
