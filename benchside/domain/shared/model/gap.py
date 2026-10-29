"""The gap taxonomy.

Kernel rather than domain-owned: consultation records gaps as they occur,
export reads them. A gap is the *shape* of a workflow breakdown, captured as a
closed sum at the moment it happens rather than distilled from prose later.

Free text describes tooling and process only -- never a hypothesis, a result,
or data. Redaction and consent are enforced by the export domain.
"""

from typing import Literal

from pydantic import ConfigDict, field_validator, model_serializer

from benchside.domain.shared.model.value import ValueObject


class GapContext(ValueObject):
    """Optional public tooling/process context, never private scientific details."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    tool_name: str | None = None
    tool_version: str | None = None
    dataset_name: str | None = None
    dataset_version: str | None = None
    workflow_area: str | None = None
    frequency: str | None = None
    impact: str | None = None
    workaround: str | None = None
    desired_improvement: str | None = None

    @field_validator("*")
    @classmethod
    def bounded_text(cls, value):
        if value is not None and len(value.encode("utf-16-le")) // 2 > 2000:
            raise ValueError("Context text must be at most 2000 UTF-16 characters")
        return value

    @model_serializer(mode="wrap")
    def omit_unknown(self, handler):
        return {key: value for key, value in handler(self).items() if value is not None}


class ContextualGap(ValueObject):
    context: GapContext | None = None

    @model_serializer(mode="wrap")
    def preserve_legacy_shape(self, handler):
        value = handler(self)
        if not value.get("context"):
            value.pop("context", None)
        return value


class MissingTool(ContextualGap):
    task: str
    reached_for: str
    why_failed: str
    kind: Literal["missing_tool"] = "missing_tool"


class UnfindableData(ContextualGap):
    sought: str
    where_searched: tuple[str, ...]
    kind: Literal["unfindable_data"] = "unfindable_data"


class ManualToil(ContextualGap):
    task: str
    frequency: str
    kind: Literal["manual_toil"] = "manual_toil"


class DeadEnd(ContextualGap):
    approach: str
    cost: str
    kind: Literal["dead_end"] = "dead_end"


class MissingIndex(ContextualGap):
    question: str
    kind: Literal["missing_index"] = "missing_index"


Gap = MissingTool | UnfindableData | ManualToil | DeadEnd | MissingIndex

GAP_KINDS: frozenset[str] = frozenset(
    {"missing_tool", "unfindable_data", "manual_toil", "dead_end", "missing_index"}
)
