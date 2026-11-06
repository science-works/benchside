"""Refresh derived reading copies once per changed project at a command boundary."""

import logging
from contextlib import contextmanager
from contextvars import ContextVar

logger = logging.getLogger(__name__)
_active = ContextVar("benchside_readable_refresh", default=None)
WARNING = (
    "The scientific record was saved, but its readable ODT/Markdown copy could not be "
    "refreshed. Retry records.export; do not repeat the recording action."
)


class RefreshBatch:
    def __init__(self):
        self.pending = {}
        self.results = {}
        self.warning = None

    def mark(self, paths, journal, project_id):
        if paths.store_root and project_id not in {"consent-ledger", "reporting-ledger"}:
            self.pending[(paths.home.resolve(), project_id)] = (paths, journal)

    def flush(self):
        from benchside.infrastructure.readable_records import export_project

        for key, (paths, journal) in self.pending.items():
            try:
                self.results[key] = export_project(paths, journal, key[1])
            except Exception as error:  # noqa: BLE001 - the authoritative save already succeeded
                self.warning = journal.readable_records_warning = WARNING
                logger.warning("Readable record refresh failed (%s)", type(error).__name__)
        self.pending.clear()


def mark_readable(paths, journal, project_id):
    batch = _active.get()
    if batch is not None:
        batch.mark(paths, journal, project_id)
    else:
        # Direct journal callers have no command boundary; retain their refresh.
        batch = RefreshBatch()
        batch.mark(paths, journal, project_id)
        batch.flush()


@contextmanager
def readable_refresh():
    batch = RefreshBatch()
    token = _active.set(batch)
    try:
        yield batch
    finally:
        try:
            batch.flush()  # Refresh even if a later step fails after durable appends.
        finally:
            _active.reset(token)
