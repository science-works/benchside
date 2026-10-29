"""Query side: the read half of CQRS.

Same shape as command.py -- Query DTO, Result DTO, Handler per file -- but
handlers must not mutate state.
"""

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, dataclass_transform

from pydantic import BaseModel

from benchside.domain.shared.command import Result


class Query(BaseModel):
    """A request for state. Also the CLI argument shape."""


@dataclass_transform()
class _QueryHandlerMeta(ABCMeta):
    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
    ) -> type:
        cls = super().__new__(mcs, name, bases, namespace)
        if any(isinstance(b, mcs) for b in bases):
            return dataclass(cls)
        return cls


Q = TypeVar("Q", bound=Query)
R = TypeVar("R", bound=Result)


class QueryHandler(Generic[Q, R], metaclass=_QueryHandlerMeta):
    """Entry point for a read. Delegates to a service; never mutates."""

    @abstractmethod
    def run(self, query: Q) -> R: ...
