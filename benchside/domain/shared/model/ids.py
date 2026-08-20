"""Typed identifiers.

No bare primitives across boundaries: a PersonaId can never be passed where a
ProjectId is expected.
"""

import re
from typing import ClassVar, NewType

from pydantic import field_validator

from benchside.domain.shared.model.value import RootValueObject

ConsultationId = NewType("ConsultationId", str)
HypothesisId = NewType("HypothesisId", str)
CritiqueId = NewType("CritiqueId", str)
DecisionId = NewType("DecisionId", str)
ObservationId = NewType("ObservationId", str)
GrantId = NewType("GrantId", str)

_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ProjectId(RootValueObject[str]):
    """The unit of continuity: one line of work, journalled together.

    Slug-shaped so it is safe as a directory name under the state root.
    """

    _re: ClassVar[re.Pattern[str]] = _SLUG

    @field_validator("root")
    @classmethod
    def _validate(cls, v: str) -> str:
        v = v.strip().lower()
        if not _SLUG.match(v):
            raise ValueError("invalid ProjectId (expected a lowercase slug)")
        return v


class PersonaId(RootValueObject[str]):
    """Identifies a persona record in content/personas/."""

    _re: ClassVar[re.Pattern[str]] = _SLUG

    @field_validator("root")
    @classmethod
    def _validate(cls, v: str) -> str:
        v = v.strip().lower()
        if not _SLUG.match(v):
            raise ValueError("invalid PersonaId (expected a lowercase slug)")
        return v


CONSENT_LEDGER_PROJECT = ProjectId("consent-ledger")
"""Reserved stream for machine-wide consent events. Not a user project."""


def user_project_id(raw: str) -> ProjectId:
    """Parse a user-supplied project id, rejecting reserved names."""
    project_id = ProjectId(raw)
    if project_id == CONSENT_LEDGER_PROJECT:
        raise ValueError(f"'{raw}' is reserved for the consent ledger")
    return project_id
