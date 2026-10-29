"""Strict, separate feedback and pseudonymous usage contracts."""

from datetime import date
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

Role = Literal[
    "pi",
    "study-design",
    "methods-clinic",
    "results-meeting",
    "repro-check",
    "journal-club",
    "peer-review",
]
Host = Literal["chatgpt", "claude", "unknown"]
Surface = Literal["web", "desktop", "cli", "unknown"]
Channel = Literal["feedback", "usage"]
Identifier = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{32}$")]
Version = Annotated[str, StringConstraints(pattern=r"^[0-9][A-Za-z0-9.-]{0,39}$")]
AppVersion = Version | Literal["unknown"]
Count = Annotated[int, Field(strict=True, ge=0, le=1_000_000_000)]
FailureCode = Literal[
    "recording_invalid",
    "recording_unavailable",
    "submission_invalid",
    "submission_rejected",
    "submission_rate_limited",
    "submission_unavailable",
    "submission_receipt_invalid",
]
FAILURE_CODES = (
    "recording_invalid",
    "recording_unavailable",
    "submission_invalid",
    "submission_rejected",
    "submission_rate_limited",
    "submission_unavailable",
    "submission_receipt_invalid",
)


class StrictValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


Discipline = Literal[
    "life_sciences",
    "medical_health_sciences",
    "physical_sciences",
    "mathematics_statistics",
    "computer_information_sciences",
    "engineering_technology",
    "earth_environmental_sciences",
    "social_sciences",
    "humanities_arts",
    "interdisciplinary",
    "other",
    "prefer_not_to_say",
]
CareerStage = Literal[
    "undergraduate_student",
    "masters_student",
    "doctoral_researcher",
    "postdoctoral_researcher",
    "research_staff",
    "independent_researcher_or_group_leader",
    "other",
    "prefer_not_to_say",
]


class Demographics(StrictValue):
    discipline: Discipline | None = None
    career_stage: CareerStage | None = None


class ResearchProfile(StrictValue):
    demographics: Demographics = Field(default_factory=Demographics)
    include_in_usage: bool = False
    revision: int = Field(default=0, ge=0)


class Feedback(StrictValue):
    id: Identifier
    role: Role | Literal["unknown"] = "unknown"
    host: Host = "unknown"
    surface: Surface = "unknown"
    ease: int = Field(ge=1, le=5)
    would_use_again: Literal["yes", "no", "unsure"]
    comment: str = Field(max_length=2000)

    @field_validator("comment")
    @classmethod
    def utf16_limit(cls, value):
        if len(value.encode("utf-16-le")) // 2 > 2000:
            raise ValueError("Comment is longer than 2000 characters")
        return value


class FeedbackPayload(StrictValue):
    schema_version: Literal["benchside.feedback.v1"] = Field(
        default="benchside.feedback.v1",
        alias="schema",
    )
    benchside_version: Version
    feedback: Feedback


class LinkedFeedbackPayload(FeedbackPayload):
    schema_version: Literal["benchside.feedback.v2"] = Field(
        default="benchside.feedback.v2", alias="schema"
    )
    contributor_id: Identifier


def parse_feedback(payload):
    from pydantic import TypeAdapter

    return TypeAdapter(FeedbackPayload | LinkedFeedbackPayload).validate_json(payload)


class RecordCounts(StrictValue):
    hypothesis: Count = 0
    critique: Count = 0
    resolution: Count = 0
    decision: Count = 0
    gap: Count = 0
    record: Count = 0


class UsageRow(StrictValue):
    role: Role
    role_version: Version
    host: Host
    app_version: AppVersion = "unknown"
    surface: Surface
    started: Count
    concluded: Count
    abandoned: Count
    records: RecordCounts


class UsagePayload(StrictValue):
    schema_version: Literal["benchside.usage.v1"] = Field(
        default="benchside.usage.v1",
        alias="schema",
    )
    installation_id: Identifier
    report_id: Identifier
    week: str
    revision: int = Field(ge=1, le=1_000_000_000)
    benchside_version: Version
    demographics: Demographics | None = None
    sessions: list[UsageRow] = Field(max_length=200)
    errors: dict[FailureCode, Count]

    @field_validator("week")
    @classmethod
    def monday(cls, value):
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value or parsed.weekday() != 0:
            raise ValueError("Usage week must be a Monday in YYYY-MM-DD form")
        return value

    @model_validator(mode="after")
    def unique_rows(self):
        keys = [(r.role, r.role_version, r.host, r.app_version, r.surface) for r in self.sessions]
        if len(set(keys)) != len(keys):
            raise ValueError("Repeated usage row")
        if set(self.errors) != set(FAILURE_CODES):
            raise ValueError("Usage needs all standard failure counts")
        return self
