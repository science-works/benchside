"""Deliberate production placeholders.

These are not test fakes: they are the safe defaults the container ships with
until the real implementations exist. The refusing sink is a security
property — the default wiring must not be able to leak.
"""

from benchside.domain.export.port.redactor import Finding
from benchside.domain.shared.error import ConfigurationError


class PassthroughRedactor:
    """No redaction yet. The export preview labels this state explicitly."""

    def scan(self, payload: str) -> list[Finding]:
        return []

    def apply(self, payload: str) -> str:
        return payload


class RefusingExportSink:
    """Refuses to send anything until a real sink is configured explicitly."""

    def send(self, payload: str) -> None:
        raise ConfigurationError("No export sink is configured; nothing was sent")
