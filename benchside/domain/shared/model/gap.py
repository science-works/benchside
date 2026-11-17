"""Workflow observations, with legacy types and an open-ended description format.

General reports retain optional descriptive labels and reviewed, de-identified
excerpts. Labels are analytical hints, never a topic allowlist or consent gate.
Private scientific findings and identifiers do not belong in shared text.
"""

from typing import Literal

from pydantic import ConfigDict, Field, field_validator, model_serializer, model_validator

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


# Suggested analytical labels, not an allowlist or consent boundary.
WORKFLOW_LABELS = (
    "software_data", "equipment_access", "materials_procurement",
    "coordination", "methods_training", "other",
)


def has_workflow_text(value: str) -> bool:
    # ECMAScript trim (the receiver) also treats U+FEFF as whitespace.
    # Check presence without changing any stored/reviewed payload bytes.
    return any(not c.isspace() and c != "\ufeff" for c in value)


class WorkflowProblem(ContextualGap):
    """Any workflow problem, including ones outside suggested labels."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    kind: Literal["workflow_problem"] = "workflow_problem"
    description: str
    labels: tuple[str, ...] = Field(default=(), max_length=20)
    deidentified_excerpt: str | None = None
    workaround_status: Literal[
        "model_suggested", "researcher_tried", "researcher_reported_helpful"
    ] | None = None

    @field_validator("description", "deidentified_excerpt")
    @classmethod
    def useful_text(cls, value):
        if value is not None and (not has_workflow_text(value) or len(value.encode("utf-16-le")) // 2 > 2000):
            raise ValueError("Workflow text needs 1–2000 UTF-16 characters")
        return value

    @field_validator("labels")
    @classmethod
    def descriptive_labels(cls, values):
        if len(set(values)) != len(values) or any(
            not has_workflow_text(v) or len(v.encode("utf-16-le")) // 2 > 100 for v in values
        ):
            raise ValueError("Labels must be distinct text of 1–100 UTF-16 characters")
        return values

    @model_validator(mode="after")
    def status_needs_workaround(self):
        if self.workaround_status and not (self.context and self.context.workaround and has_workflow_text(self.context.workaround)):
            raise ValueError("A workaround status needs a described workaround")
        return self

    @model_serializer(mode="wrap")
    def optional_fields(self, handler):
        return {k: v for k, v in handler(self).items() if v is not None and (k != "context" or v)}


Gap = MissingTool | UnfindableData | ManualToil | DeadEnd | MissingIndex | WorkflowProblem

GAP_KINDS: frozenset[str] = frozenset(
    {"missing_tool", "unfindable_data", "manual_toil", "dead_end", "missing_index", "workflow_problem"}
)
