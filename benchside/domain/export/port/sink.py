"""The one way observations leave the machine.

Every implementation must be reachable only through ExportService.export,
which requires an active grant. A static test enforces that no other module
imports this port.
"""

from abc import abstractmethod
from typing import Protocol

from benchside.domain.export.model.value import DeliveryReceipt
from benchside.domain.shared.port.base import Port


class ExportSink(Port, Protocol):
    destination: str

    @abstractmethod
    def send(self, payload: str) -> DeliveryReceipt | None: ...
