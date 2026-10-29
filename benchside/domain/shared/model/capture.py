"""The capture vocabulary.

Shared kernel: authoring declares requirements over these kinds; consultation
enforces them at close. Each kind names a `bench` call and maps 1:1 to a
journal event type.
"""

from enum import StrEnum
from typing import Literal

from benchside.domain.shared.model.value import ValueObject

RecordKind = Literal[
    "study-design", "methods", "results", "reproducibility", "literature", "review"
]


class CaptureKind(StrEnum):
    HYPOTHESIS = "hypothesis"
    CRITIQUE = "critique"
    RESOLUTION = "resolution"
    DECISION = "decision"
    GAP = "gap"
    RECORD = "record"


class CloseRequirement(ValueObject):
    """A minimum capture count a sitting must reach to close converged."""

    kind: CaptureKind
    minimum: int = 1
