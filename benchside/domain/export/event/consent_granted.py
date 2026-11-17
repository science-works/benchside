from typing import Literal

from pydantic import model_serializer

from benchside.domain.shared.event import Event
from benchside.domain.shared.model.ids import GrantId


class ConsentGranted(Event):
    """The scientist authorised sharing for the listed gap kinds."""

    grant_id: GrantId
    gap_kinds: frozenset[str]
    scope: Literal["kinds", "all_workflow"] = "kinds"

    @model_serializer(mode="wrap")
    def legacy_grant_shape(self, handler):
        value = handler(self)
        if self.scope == "kinds":
            value.pop("scope", None)
        return value
