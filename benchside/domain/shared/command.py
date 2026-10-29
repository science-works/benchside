"""Command side: the write half of CQRS.

One file per use case holds three classes: the Command DTO, the Result DTO,
and the Handler. Handlers are thin -- unpack, call one service, build a result.
"""

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, dataclass_transform

from pydantic import BaseModel


class Command(BaseModel):
    """An intent to change state. Also the CLI argument shape."""


class Result(BaseModel):
    """What a handler returns. Also the CLI output shape."""


@dataclass_transform()
class _CommandHandlerMeta(ABCMeta):
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


C = TypeVar("C", bound=Command)
R = TypeVar("R", bound=Result)


class CommandHandler(Generic[C, R], metaclass=_CommandHandlerMeta):
    """Entry point for a write. Delegates to a service; never touches a port."""

    @abstractmethod
    def run(self, cmd: C) -> R: ...
