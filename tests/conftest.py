"""Shared fixtures. Every test runs against a temp BENCHSIDE_HOME."""

import pytest

from benchside.config import Paths
from benchside.infrastructure.journal.store import JsonlJournal


@pytest.fixture
def paths(tmp_path) -> Paths:
    return Paths(home=tmp_path / "home", repo_root=tmp_path / "repo")


@pytest.fixture
def journal(paths) -> JsonlJournal:
    return JsonlJournal(paths)
