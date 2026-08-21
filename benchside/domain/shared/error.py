"""Domain error hierarchy.

Raise typed errors; never return None to signal failure. None means "not
found" at a repository boundary and nothing else.
"""


class BenchsideError(Exception):
    """Root of every error benchside raises deliberately."""

    def __init__(self, message: str, *, code: str | None = None, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or type(self).__name__
        self.hint = hint


class DomainError(BenchsideError):
    """A business-rule violation. The caller asked for something invalid."""


class NotFoundError(DomainError):
    """The referenced aggregate does not exist."""


class ValidationError(DomainError):
    """Input failed validation."""

    def __init__(self, message: str, *, field: str | None = None, code: str | None = None) -> None:
        super().__init__(message, code=code)
        self.field = field


class InvalidStateError(DomainError):
    """The aggregate cannot make this transition from its current state."""


class ConsentRequiredError(DomainError):
    """An export was attempted without an active consent grant covering it."""


class InfrastructureError(BenchsideError):
    """A system failure: disk, network, external process."""


class StorageUnavailableError(InfrastructureError):
    """The journal or content store could not be read or written."""


class ConfigurationError(InfrastructureError):
    """The installation is misconfigured; fail fast at startup."""
