"""Count optional submission failures without recording payloads or withdrawal."""

from benchside.domain.export.model.reporting import FAILURE_CODES
from benchside.domain.export.service.reporting import ReportingService
from benchside.domain.shared.error import (
    BenchsideError,
    ConsentRequiredError,
    InfrastructureError,
)
from benchside.infrastructure.journal.store import JsonlJournal


def record_submission_failure(paths, error):
    # Revocation and changes to the researcher's choices are normal controls,
    # not evidence that the product failed. No usage consent means no counter.
    if isinstance(error, ConsentRequiredError):
        return
    code = getattr(error, "code", None)
    if code not in FAILURE_CODES or not code.startswith("submission_"):
        code = (
            "submission_unavailable"
            if isinstance(error, (InfrastructureError, OSError))
            else "submission_invalid"
        )
    try:
        ReportingService(journal=JsonlJournal(paths)).failure(code)
    except (BenchsideError, OSError, ValueError):
        pass  # Failure accounting must never replace the original exception.
