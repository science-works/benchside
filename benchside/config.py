"""Typed settings and path resolution.

State lives on the scientist's machine, never in the repo. BENCHSIDE_HOME
overrides the root, which is what tests and the eval harness use to stay
hermetic.
"""

import os
from pathlib import Path

from pydantic import BaseModel


class Paths(BaseModel):
    """Everywhere benchside reads or writes."""

    home: Path
    repo_root: Path

    @property
    def journal_dir(self) -> Path:
        """One append-only stream per project."""
        return self.home / "projects"

    @property
    def content_dir(self) -> Path:
        return self.repo_root / "content"

    @property
    def personas_dir(self) -> Path:
        return self.content_dir / "personas"

    @property
    def templates_dir(self) -> Path:
        return self.content_dir / "templates"

    @property
    def skills_dir(self) -> Path:
        return self.repo_root / "skills"

    def journal_file(self, project_id: str) -> Path:
        return self.journal_dir / project_id / "journal.jsonl"


def resolve_paths() -> Paths:
    home = Path(os.environ.get("BENCHSIDE_HOME", Path.home() / ".benchside")).expanduser()
    repo_root = Path(os.environ.get("BENCHSIDE_REPO", Path(__file__).resolve().parent.parent))
    return Paths(home=home, repo_root=repo_root)
