"""Typed settings and path resolution.

State lives on the scientist's machine, never in the repo. BENCHSIDE_HOME
overrides the root, which is what tests and the eval harness use to stay
hermetic.
"""

import json
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
        return resolve_content_root()

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


def resolve_content_root() -> Path:
    """Locate authored content (personas, templates).

    Order: BENCHSIDE_REPO env override -> the repo checkout this module sits
    in (development) -> content packaged into the wheel (installed users).
    The packaged copy exists because pyproject force-includes content/ as
    benchside/_content/ (bug B4: installed users have no checkout).
    """
    override = os.environ.get("BENCHSIDE_REPO")
    if override:
        return Path(override).expanduser() / "content"
    checkout = Path(__file__).resolve().parent.parent / "content"
    if checkout.is_dir():
        return checkout
    return Path(__file__).resolve().parent / "_content"


def resolve_paths() -> Paths:
    """Explicit environment override, remembered local choice, then XDG/default data home."""
    override = os.environ.get("BENCHSIDE_HOME")
    if override:
        home = Path(override).expanduser()
    elif storage_profile_path().is_file():
        profile = json.loads(storage_profile_path().read_text())
        if (
            not isinstance(profile, dict)
            or set(profile) != {"local_directory"}
            or not isinstance(profile["local_directory"], str)
            or not Path(profile["local_directory"]).is_absolute()
        ):
            raise ValueError(
                "Invalid Benchside storage preference; choose the local directory again"
            )
        home = Path(profile["local_directory"])
    else:
        xdg_data = os.environ.get("XDG_DATA_HOME")
        data_root = Path(xdg_data).expanduser() if xdg_data else Path.home() / ".local" / "share"
        home = data_root / "benchside"
    repo_root = Path(os.environ.get("BENCHSIDE_REPO", Path(__file__).resolve().parent.parent))
    return Paths(home=home, repo_root=repo_root)


def storage_profile_path() -> Path:
    root = os.environ.get("XDG_CONFIG_HOME")
    return (Path(root).expanduser() if root else Path.home() / ".config") / "benchside/storage.json"


def configure_local_storage(directory: str) -> dict:
    """Remember an explicit local choice for all agents on this OS account. Never migrate data."""
    from benchside.application.app import App
    from benchside.infrastructure.files import atomic_json

    home = Path(directory).expanduser()
    if not home.is_absolute():
        raise ValueError("Choose an absolute local storage directory")
    home = home.resolve()
    override = os.environ.get("BENCHSIDE_HOME")
    if override and Path(override).expanduser().resolve() != home:
        raise ValueError(
            "BENCHSIDE_HOME overrides this choice; remove it or choose the same directory"
        )
    paths = Paths(home=home, repo_root=Path(__file__).resolve().parent.parent)
    probe = App(paths).run({"action": "storage.probe"})
    atomic_json(storage_profile_path(), {"local_directory": str(home)})
    return {**probe, "preference": str(storage_profile_path()), "migrated": False}
