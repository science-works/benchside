"""Writing compiled skills to skills/<persona>/SKILL.md."""

from pathlib import Path

from benchside.domain.authoring.model.skill import SkillDocument
from benchside.domain.shared.error import StorageUnavailableError


class FileSkillWriter:
    def __init__(self, target_dir: Path) -> None:
        self._dir = target_dir

    def write(self, document: SkillDocument) -> None:
        path = self._path(document.filename)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(document.render(), encoding="utf-8")
        except OSError as err:
            raise StorageUnavailableError(f"Could not write skill to {path}: {err}") from err

    def read_existing(self, filename: str) -> str | None:
        path = self._path(filename)
        return path.read_text(encoding="utf-8") if path.exists() else None

    def _path(self, filename: str):
        return self._dir / filename
