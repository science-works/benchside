"""The JSONL journal: benchside's source of truth.

One append-only file per project. Every line is one event, tagged with its
class name so it can be parsed back into its concrete type. History is never
rewritten -- corrections are new events that supersede old ones.

Writes are atomic-ish by construction: a single `write()` of one line in append
mode under the POSIX small-write guarantee. Good enough for a single-user CLI;
if this ever goes concurrent it needs a lock.
"""

import json
import logging
from collections.abc import Iterable
from pathlib import Path

from benchside.config import Paths
from benchside.domain.shared.error import StorageUnavailableError
from benchside.domain.shared.event import Event
from benchside.domain.shared.model.ids import ProjectId
from benchside.infrastructure.journal.registry import ensure_events_registered

logger = logging.getLogger(__name__)


class JsonlJournal:
    def __init__(self, paths: Paths) -> None:
        self._paths = paths
        ensure_events_registered()

    def append(self, project_id: ProjectId, event: Event) -> None:
        path = self._paths.journal_file(project_id.root)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            line = json.dumps(
                {"type": type(event).__name__, "data": event.model_dump(mode="json")},
                ensure_ascii=False,
            )
            with path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        except OSError as err:
            raise StorageUnavailableError(f"Could not append to journal at {path}: {err}") from err

    def read(self, project_id: ProjectId) -> Iterable[Event]:
        path = self._paths.journal_file(project_id.root)
        if not path.exists():
            return []
        return list(self._parse(path))

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
                    event_type = Event.resolve(record["type"])
                    yield event_type.model_validate(record["data"])
                except (json.JSONDecodeError, KeyError, ValueError) as err:
                    logger.warning("Skipping unreadable journal line %s:%d (%s)", path, number, err)
