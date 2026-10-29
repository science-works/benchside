"""Data-only study definitions and bounded, pseudonymous metascience submissions."""

import hashlib
import json
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, field_validator, model_validator

from benchside.domain.export.model.reporting import Host, Identifier, Role, StrictValue, Version
from benchside.domain.shared.model.gap import Gap

Key = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9-]{0,47}$")]
Digest = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
Day = Annotated[str, StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}$")]
Basis = Literal["model_inferred", "researcher_reported", "unknown"]
Choice = Literal["invitations", "analysis", "sharing"]
LEGACY_SAMPLING = "weekly-random-10pct-max5-v1"
RANDOM_SAMPLING = "weekly-random-max20-v1"
MANUAL_SAMPLING = "weekly-user-selected-max20-v1"
Sampling = Literal[
    "weekly-random-10pct-max5-v1", "weekly-random-max20-v1", "weekly-user-selected-max20-v1"
]


def selection_size(sampling: Sampling, eligible: int) -> int:
    if sampling == LEGACY_SAMPLING:
        return min(5, (eligible + 9) // 10)
    if sampling == RANDOM_SAMPLING:
        return min(20, eligible)
    return eligible  # The manual frame is exactly the supplied chosen set, capped separately.


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class Option(StrictValue):
    id: Key
    label: str = Field(min_length=1, max_length=160)


class Question(StrictValue):
    id: Key
    prompt: str = Field(min_length=1, max_length=500)
    options: list[Option] = Field(min_length=2, max_length=10)

    @model_validator(mode="after")
    def unique_options(self):
        if len({o.id for o in self.options}) != len(self.options):
            raise ValueError("Duplicate question option")
        return self


class TextQuestion(StrictValue):
    id: Key
    prompt: str = Field(min_length=1, max_length=500)
    type: Literal["text"] = "text"
    max_length: int = Field(ge=1, le=2000)


class Study(StrictValue):
    id: Key
    version: int = Field(ge=1, le=1_000_000)
    title: str = Field(min_length=1, max_length=160)
    purpose: str = Field(min_length=1, max_length=1000)
    data_use: str = Field(min_length=1, max_length=1000)
    retention_days: int = Field(ge=1, le=3650)
    opens: Day
    closes: Day
    questions: list[Question | TextQuestion] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def valid_study(self):
        if date.fromisoformat(self.opens) > date.fromisoformat(self.closes):
            raise ValueError("Study closes before opening")
        if len({q.id for q in self.questions}) != len(self.questions):
            raise ValueError("Duplicate study question")
        return self

    @property
    def key(self):
        return f"{self.id}@{self.version}"

    def active(self, today):
        return self.opens <= today <= self.closes


class StudyCatalog(StrictValue):
    schema_version: Literal["benchside.studies.v1"] = Field(
        default="benchside.studies.v1", alias="schema"
    )
    studies: list[Study] = Field(max_length=50)

    @model_validator(mode="after")
    def unique_studies(self):
        if len({s.id for s in self.studies}) != len(self.studies):
            raise ValueError("Only one version of each study may be active")
        return self


class SurveyPayload(StrictValue):
    schema_version: Literal["benchside.survey.v1"] = Field(
        default="benchside.survey.v1", alias="schema"
    )
    benchside_version: Version
    response_id: Identifier
    study_id: Key
    study_version: int = Field(ge=1, le=1_000_000)
    study_sha256: Digest
    answers: dict[Key, Key] = Field(min_length=1, max_length=10)

    def check_study(self, study):
        if (
            self.study_id != study.id
            or self.study_version != study.version
            or self.study_sha256 != digest(study.model_dump())
            or set(self.answers) - {q.id for q in study.questions}
        ):
            raise ValueError("Survey does not match the reviewed study definition")
        for question in study.questions:
            if isinstance(question, TextQuestion) and question.id in self.answers:
                raise ValueError("Free text needs the current survey format")
            if question.id in self.answers and self.answers[question.id] not in {
                o.id for o in question.options
            }:
                raise ValueError("Unknown survey answer")


class TextAnswer(StrictValue):
    text: str = Field(max_length=2000)


class LinkedSurveyPayload(SurveyPayload):
    schema_version: Literal["benchside.survey.v2"] = Field(
        default="benchside.survey.v2", alias="schema"
    )
    contributor_id: Identifier
    answers: dict[Key, Key | TextAnswer] = Field(min_length=1, max_length=10)

    def check_study(self, study):
        if (
            self.study_id != study.id
            or self.study_version != study.version
            or self.study_sha256 != digest(study.model_dump())
        ):
            raise ValueError("Survey does not match the accepted study definition")
        questions = {q.id: q for q in study.questions}
        for identifier, answer in self.answers.items():
            question = questions.get(identifier)
            if isinstance(question, TextQuestion):
                if (
                    not isinstance(answer, TextAnswer)
                    or len(answer.text.encode("utf-16-le")) // 2 > question.max_length
                ):
                    raise ValueError("Invalid or overlong text answer")
            elif (
                not isinstance(question, Question)
                or not isinstance(answer, str)
                or answer not in {o.id for o in question.options}
            ):
                raise ValueError("Unknown survey answer")


def parse_survey(payload):
    from pydantic import TypeAdapter

    return TypeAdapter(SurveyPayload | LinkedSurveyPayload).validate_json(payload)


class StudyParticipation(StrictValue):
    study_sha256: Digest
    invitation_grant: Identifier
    destination: str
    contributor_id: Identifier


class Activity(StrictValue):
    value: Literal[
        "literature",
        "study_design",
        "data_collection",
        "analysis",
        "coding",
        "interpretation",
        "writing",
        "review",
        "other",
        "unknown",
    ]
    basis: Basis


class Obstacle(StrictValue):
    value: Literal[
        "access",
        "tool_failure",
        "missing_context",
        "unreliable_answer",
        "workflow_friction",
        "none_reported",
        "other",
        "unknown",
    ]
    basis: Basis


class Verification(StrictValue):
    value: Literal[
        "checked_sources",
        "ran_test",
        "compared_methods",
        "expert_review",
        "none_visible",
        "other",
        "unknown",
    ]
    basis: Basis


class Outcome(StrictValue):
    value: Literal["helpful", "unhelpful", "mixed", "not_reported"]
    basis: Literal["researcher_reported", "unknown"]


class Classification(StrictValue):
    rubric: Literal["research-activity-1"] = "research-activity-1"
    benchside_role: Role | Literal["none", "unknown"]
    activity: Activity
    obstacle: Obstacle
    verification: Verification
    outcome: Outcome

    @model_validator(mode="after")
    def evidence(self):
        for field in (self.activity, self.obstacle, self.verification, self.outcome):
            unknown = field.value in {"unknown", "not_reported"}
            if unknown != (field.basis == "unknown"):
                raise ValueError(
                    "Unknown findings need unknown evidence; other findings need a basis"
                )
        return self


class ActivityObservation(Classification):
    host: Host


class ActivityPayload(StrictValue):
    schema_version: Literal["benchside.activity.v1"] = Field(
        default="benchside.activity.v1", alias="schema"
    )
    benchside_version: Version
    batch_id: Identifier
    revision: int = Field(ge=1, le=1_000_000)
    week: Day
    sampling: Sampling = LEGACY_SAMPLING
    coverage: Literal["user_selected_accessible_sessions"] = "user_selected_accessible_sessions"
    eligible: int = Field(ge=1, le=500)
    selected: int = Field(ge=1, le=20)
    observations: list[ActivityObservation] = Field(min_length=1, max_length=20)

    @field_validator("week")
    @classmethod
    def monday(cls, value):
        if date.fromisoformat(value).weekday() != 0:
            raise ValueError("Activity week must start on Monday")
        return value

    @model_validator(mode="after")
    def coverage_counts(self):
        if self.selected != selection_size(self.sampling, self.eligible):
            raise ValueError("Selection count does not match the sampling policy")
        if len(self.observations) > self.selected:
            raise ValueError("Reviewed count exceeds selected count")
        return self


class LinkedActivityPayload(ActivityPayload):
    schema_version: Literal["benchside.activity.v2"] = Field(
        default="benchside.activity.v2", alias="schema"
    )
    contributor_id: Identifier


def parse_activity(payload):
    from pydantic import TypeAdapter

    return TypeAdapter(ActivityPayload | LinkedActivityPayload).validate_json(payload)


class Scope(StrictValue):
    host: Host
    source_id: str = Field(min_length=1, max_length=256)


class Candidate(StrictValue):
    scope: Scope
    session_ref: str = Field(min_length=1, max_length=256)


class SelectedProblem(StrictValue):
    id: Identifier
    gap: Gap
    basis: Basis


class Sample(StrictValue):
    id: Identifier
    inventory_sha256: Digest
    eligible: int = Field(ge=0, le=500)
    # Missing in saved pre-0.1.3 samples; never reinterpret their original counts.
    sampling: Sampling = LEGACY_SAMPLING
    selected: dict[Identifier, Candidate] = Field(max_length=20)
    records: dict[Identifier, Classification] = Field(default_factory=dict, max_length=20)
    problems: dict[Identifier, list[SelectedProblem]] = Field(default_factory=dict, max_length=20)
    revision: int = Field(default=0, ge=0, le=1_000_000)

    @model_validator(mode="after")
    def consistent_sample(self):
        if len(self.selected) != selection_size(self.sampling, self.eligible):
            raise ValueError("Invalid private sample size")
        if set(self.records) - set(self.selected):
            raise ValueError("Classification is not part of this sample")
        if set(self.problems) - set(self.selected) or any(
            len(p) > 5 for p in self.problems.values()
        ):
            raise ValueError(
                "Problems need a selected conversation, with at most five per conversation"
            )
        return self


class MetaDraft(StrictValue):
    id: Identifier
    channel: Literal["surveys", "activity"]
    key: str
    grants: dict[Choice, Identifier]
    payload: str
    sha256: Digest
    destination: str

    @model_validator(mode="after")
    def valid_payload(self):
        if self.channel == "surveys":
            parse_survey(self.payload)
        else:
            parse_activity(self.payload)
        if hashlib.sha256(self.payload.encode()).hexdigest() != self.sha256:
            raise ValueError("Metascience draft digest mismatch")
        expected = {"invitations"} if self.channel == "surveys" else {"analysis", "sharing"}
        if set(self.grants) != expected:
            raise ValueError("Metascience draft needs the relevant consent grants")
        return self


class MetaReceipt(StrictValue):
    channel: Literal["surveys", "activity"]
    destination: str
    status: Literal["stored", "duplicate"]
    sha256: Digest
    received_at: str
    observations: int = Field(ge=1, le=20)

    @field_validator("received_at")
    @classmethod
    def timestamp(cls, value):
        if datetime.fromisoformat(value).tzinfo is None:
            raise ValueError("Receipt needs a timezone")
        return value


class MetaState(StrictValue):
    schema_version: Literal["benchside.metascience-state.v1"] = "benchside.metascience-state.v1"
    grants: dict[Choice, Identifier] = Field(default_factory=dict, max_length=3)
    scopes: list[Scope] = Field(default_factory=list, max_length=50)
    seed: Identifier
    last_check: Day | None = None
    last_invitation: Day | None = None
    studies: dict[str, Study] = Field(default_factory=dict, max_length=500)
    dismissed: list[Key] = Field(default_factory=list, max_length=500)
    completed: list[str] = Field(default_factory=list, max_length=500)
    seen: list[Digest] = Field(default_factory=list, max_length=10000)
    samples: dict[Day, Sample] = Field(default_factory=dict, max_length=520)
    drafts: dict[Identifier, MetaDraft] = Field(default_factory=dict, max_length=1000)
    latest: dict[str, Identifier] = Field(default_factory=dict, max_length=1000)
    receipts: dict[Identifier, MetaReceipt] = Field(default_factory=dict, max_length=1000)
    participation: dict[str, StudyParticipation] = Field(default_factory=dict, max_length=500)
    analysis_policy: Literal["selected-research-max20-1"] | None = None
    sharing_policy: Literal["pseudonymous-contributions-1"] | None = None

    @model_validator(mode="after")
    def consistent_state(self):
        if any(key != study.key for key, study in self.studies.items()):
            raise ValueError("Invalid study index")
        for week in self.samples:
            if date.fromisoformat(week).weekday() != 0:
                raise ValueError("Invalid private sample week")
        for key, draft in self.drafts.items():
            if key != draft.id:
                raise ValueError("Invalid draft index")
        for key, identifier in self.latest.items():
            if identifier not in self.drafts or self.drafts[identifier].key != key:
                raise ValueError("Invalid latest draft index")
        for key, receipt in self.receipts.items():
            draft = self.drafts.get(key)
            if not draft or (receipt.sha256, receipt.channel, receipt.destination) != (
                draft.sha256,
                draft.channel,
                draft.destination,
            ):
                raise ValueError("Receipt does not match a private draft")
        return self
