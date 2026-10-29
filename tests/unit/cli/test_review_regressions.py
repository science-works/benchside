"""Claude review regressions using synthetic records and isolated storage."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from benchside.cli.main import main
from benchside.domain.consultation.event.opened import ConsultationOpened
from benchside.domain.shared.model.ids import PersonaId, ProjectId


@pytest.mark.parametrize("reader", ["read", "read_envelopes"])
def test_non_object_journal_lines_are_skipped_and_logged(paths, journal, caplog, reader):
    project = ProjectId("synthetic")
    event = ConsultationOpened(
        id="event-1", consultation_id="consultation-1", project_id=project,
        persona_id=PersonaId("pi"),
    )
    journal.append(project, event)
    path = paths.journal_file(project.root)
    original = path.read_text()
    path.write_text(original + 'null\n123\n["private text must not enter a log"]\n' + original)
    before = path.read_bytes()

    records = list(getattr(journal, reader)(project))

    assert len(records) == 2
    assert path.read_bytes() == before
    assert len(caplog.records) == 3
    assert all("Skipping unreadable journal line" in record.message for record in caplog.records)
    assert "private text" not in caplog.text


@pytest.mark.parametrize("profile", [
    {"local_directory": "relative/path"}, None, ["local_directory"],
    {"local_directory": None}, {"local_directory": 42},
])
def test_invalid_storage_preference_reports_original_error(
    tmp_path, monkeypatch, capsys, profile
):
    monkeypatch.delenv("BENCHSIDE_HOME", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    config = tmp_path / "config/benchside/storage.json"
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps(profile))

    assert main(["hypothesis", "Synthetic hypothesis"]) == 1

    output = capsys.readouterr()
    assert "choose the local directory again" in output.err
    assert "Traceback" not in output.err
    assert "Synthetic hypothesis" not in output.err


def test_review_edits_help_requires_a_file_path(capsys):
    assert main(["share", "preview", "--help"]) == 0
    help_text = " ".join(capsys.readouterr().out.split())
    assert "path to a JSON file mapping observation IDs to reviewed gap objects" in help_text


def test_python_module_entrypoint_loads_all_command_handlers(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "benchside.cli.main", "--help"],
        cwd=Path(__file__).resolve().parents[3],
        env={**os.environ, "BENCHSIDE_HOME": str(tmp_path / "records")},
        capture_output=True, text=True, timeout=5, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "benchside" in result.stdout
    assert "Traceback" not in result.stderr
