"""The journal event base.

Every durable fact benchside records is an Event appended to a research line's
journal. The journal is append-only and is the source of truth: consultation
state, the lab notebook, and the eval assertions are all derived from it.
"""

from datetime import UTC, datetime
from typing import ClassVar, NewType, Self
from uuid import uuid4

from pydantic import BaseModel, Field

EventId = NewType("EventId", str)


def new_event_id() -> EventId:
    """Opaque unique event id. Always generated here, never by the model."""
    return EventId(str(uuid4()))


class Event(BaseModel):
    """A recorded fact. Immutable once appended.

    Subclasses register themselves by class name so a journal line can be
    parsed back into its concrete type.
    """

    _registry: ClassVar[dict[str, type["Event"]]] = {}

    id: EventId
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        Event._registry[cls.__name__] = cls

    @classmethod
    def resolve(cls, name: str) -> type[Self]:
        """Look up a concrete Event subclass by its class name."""
        return Event._registry[name]  # type: ignore[return-value]
