"""The capture vocabulary.

Shared kernel: authoring declares requirements over these kinds; consultation
enforces them at close. Each kind names a `bench` call and maps 1:1 to a
journal event type.
"""

from enum import StrEnum

from benchside.domain.shared.model.value import ValueObject


class CaptureKind(StrEnum):
    HYPOTHESIS = "hypothesis"
    CRITIQUE = "critique"
    RESOLUTION = "resolution"
    DECISION = "decision"
    GAP = "gap"


class CloseRequirement(ValueObject):
    """A minimum capture count a sitting must reach to close converged."""

    kind: CaptureKind
    minimum: int = 1
