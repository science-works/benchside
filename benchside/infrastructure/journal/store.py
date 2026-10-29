"""The JSONL journal: benchside's source of truth.

One append-only file per project. Every line is one event, tagged with its
class name so it can be parsed back into its concrete type. History is never
rewritten -- corrections are new events that supersede old ones.

Each append holds a per-journal file lock, flushes and syncs the write, and
restricts the file to its owner. App and CLI commands also hold an installation
transaction lock around read/validate/write operations.
"""

import json
import logging
import os
from collections.abc import Iterable
from pathlib import Path

from benchside.config import Paths
from benchside.domain.shared.error import ConfigurationError, StorageUnavailableError
from benchside.domain.shared.event import Event
from benchside.domain.shared.model.ids import ProjectId
from benchside.infrastructure.files import file_lock
from benchside.infrastructure.journal.registry import ensure_events_registered
from benchside.infrastructure.session_context import current_provenance, current_session

logger = logging.getLogger(__name__)


class JsonlJournal:
    def __init__(self, paths: Paths) -> None:
        root = paths.home.resolve()
        if any((directory / ".git").exists() for directory in (root, *root.parents)):
            raise ConfigurationError("Benchside journals must be stored outside Git")
        self._paths = paths
        ensure_events_registered()

    def append(self, project_id: ProjectId, event: Event) -> None:
        path = self._paths.journal_file(project_id.root)
        try:
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            provenance = current_provenance()
            if provenance is not None and hasattr(event, "consultation_id"):
                event = event.model_copy(update={"provenance": provenance})
            data = event.model_dump(mode="json")
            if not hasattr(event, "consultation_id") or event.provenance is None:
                data.pop("provenance", None)
            line = json.dumps(
                {
                    "type": type(event).__name__,
                    "session": current_session(self._paths, project_id),
                    "data": data,
                },
                ensure_ascii=False,
            )
            with file_lock(path.with_suffix(".lock")), path.open("a", encoding="utf-8") as handle:
                os.chmod(path, 0o600)
                handle.write(line + "\n")
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as err:
            raise StorageUnavailableError(f"Could not append to journal at {path}: {err}") from err

    def read(self, project_id: ProjectId) -> Iterable[Event]:
        path = self._paths.journal_file(project_id.root)
        if not path.exists():
            return []
        return list(self._parse(path))

    def read_envelopes(self, project_id: ProjectId) -> Iterable[dict]:
        """Raw journal lines as dicts — type, session, data. For views and
        analysis that need the session linkage the domain Event doesn't carry."""
        path = self._paths.journal_file(project_id.root)
        if not path.exists():
            return []
        envelopes = []
        for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                record = json.loads(raw)
                if not isinstance(record, dict):
                    raise TypeError("Journal envelope must be an object")
                record.setdefault("session", None)
                envelopes.append(record)
            except (ValueError, TypeError, AttributeError) as err:
                self._log_unreadable(path, number, err)
        return envelopes

    def projects(self) -> Iterable[ProjectId]:
        root = self._paths.journal_dir
        if not root.exists():
            return []
        return [ProjectId(d.name) for d in sorted(root.iterdir()) if (d / "journal.jsonl").exists()]

    def _parse(self, path: Path) -> Iterable[Event]:
        """Skip unparseable lines rather than failing the whole read.

        A single corrupt line must not make a scientist's entire project
        unreadable. Skips are logged so they are not silent.
        """
        with path.open(encoding="utf-8") as handle:
            for number, raw in enumerate(handle, start=1):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    record = json.loads(raw)
                    if not isinstance(record, dict):
                        raise TypeError("Journal envelope must be an object")
                    event_type = Event.resolve(record["type"])
                    yield event_type.model_validate(record["data"])
                except (KeyError, ValueError, TypeError, AttributeError) as err:
                    self._log_unreadable(path, number, err)

    @staticmethod
    def _log_unreadable(path: Path, number: int, error: Exception) -> None:
        # Validation errors can contain research text. Log location and category only.
        logger.warning(
            "Skipping unreadable journal line %s:%d (%s)", path, number, type(error).__name__
        )
