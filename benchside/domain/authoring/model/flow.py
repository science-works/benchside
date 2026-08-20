"""The persona-as-program flow model.

A persona declares its conversation as ordered phases plus close requirements.
Phases are rendered into the skill at compile time and are conversation
guidance only — the consultation domain's state machine stays the invariant
layer underneath, and only close is enforced by the CLI.
"""

from pydantic import Field

from benchside.domain.shared.model.capture import CaptureKind, CloseRequirement
from benchside.domain.shared.model.value import ValueObject


class Phase(ValueObject):
    id: str
    goal: str
    guidance: str
    captures: tuple[CaptureKind, ...] = ()
    exit_when: str = ""


class Flow(ValueObject):
    """Linear in v0 — no branching until a second persona demands it."""

    phases: tuple[Phase, ...] = ()
    close_requires: tuple[CloseRequirement, ...] = Field(default_factory=tuple)
