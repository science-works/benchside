"""One random contributor identifier per private store; no account identifiers."""

import json
import re
import uuid
from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from benchside.domain.export.model.reporting import StrictValue
from benchside.domain.shared.error import ValidationError
from benchside.infrastructure.files import atomic_json

POLICY = "pseudonymous-contributions-1"


class ContributionPolicy(StrictValue):
    policy: Literal["pseudonymous-contributions-1"] = POLICY
    grants: dict[
        Literal["gaps", "feedback", "usage"],
        Annotated[str, StringConstraints(min_length=1, max_length=100)],
    ] = Field(default_factory=dict)


def contributor_id(paths):
    path = paths.home / "reporting/installation.json"
    if path.exists():
        value = json.loads(path.read_text())["id"]
        if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{32}", value):
            raise ValidationError("Invalid contributor identifier; preserve and repair this store")
        return value
    value = uuid.uuid4().hex
    atomic_json(path, {"id": value})
    return value
