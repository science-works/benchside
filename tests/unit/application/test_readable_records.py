import json
import stat
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from benchside.application.app import App
from benchside.config import Paths, configure_local_storage, resolve_paths
from benchside.domain.shared.error import BenchsideError
from tests.unit.application.test_supervisor_questions import context


def test_named_odt_and_markdown_include_all_history_and_preserve_private_journal(tmp_path, monkeypatch):
    root = tmp_path / "My research"
    monkeypatch.delenv("BENCHSIDE_HOME", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    configure_local_storage(str(root))
    paths = resolve_paths()
    assert paths.home == root / "agent"
    app = App(paths)
    app.run({"action": "records.configure", "format": "both"})
    setup = app.run({"action": "setup", "project_key": "test", "title": "Software selection interviews"})
    ctx = {k: setup[k] for k in ("project_id", "session_id")}
    ctx["sitting_id"] = app.run({"action": "start", **ctx, "role": "pi"})["sitting"]["id"]
    for i in range(7):
        app.run({"action": "decide", **ctx, "decision": f"Decision {i}: α < β & γ", "rationale": "Two  spaces\nand a new line"})
    question = app.run({"action": "question", **ctx, "question": "Which disciplines?"})["recorded"]
    app.run({"action": "answer", **ctx, "question_id": question, "answer": "CS and life sciences."})
    files = app.run({"action": "records.export", "project_id": ctx["project_id"]})
    odt, md = Path(files["odt"]), Path(files["markdown"])
    assert odt.parent.parent == root / "researcher" / "projects"
    assert "Software selection interviews" in odt.parent.name
    assert "Decision 0" in md.read_text() and "Decision 6" in md.read_text()
    assert "Which disciplines?" in md.read_text() and "CS and life sciences." in md.read_text()
    assert "Two  spaces" in md.read_text()
    assert stat.S_IMODE(odt.stat().st_mode) == 0o600
    with zipfile.ZipFile(odt) as archive:
        assert archive.namelist()[0] == "mimetype"
        assert archive.getinfo("mimetype").compress_type == zipfile.ZIP_STORED
        assert archive.read("mimetype") == b"application/vnd.oasis.opendocument.text"
        doc = ET.fromstring(archive.read("content.xml"))
        text = "".join(doc.itertext())
        assert "Decision 0: α < β & γ" in text
        assert "Decision 6" in text and "CS and life sciences." in text
        ET.fromstring(archive.read("META-INF/manifest.xml"))
    # Editing the readable copy never rewrites the journal.
    md.write_text("My edits")
    fresh = App(resolve_paths()).run({"action": "recall", **ctx, "history": "all"})
    assert len(fresh["recent_decisions"]) == 7
    assert fresh["recent_decisions"][0]["decision"] == "Decision 0: α < β & γ"
    assert not App(resolve_paths()).run({"action": "sharing.status"})["gaps"]["enabled"]


def test_legacy_move_preserves_every_private_file_and_identity(tmp_path, monkeypatch):
    root = tmp_path / "legacy"
    monkeypatch.setenv("BENCHSIDE_HOME", str(root))
    app = App(resolve_paths())
    app.run({"action": "records.configure", "format": "markdown"})
    ctx = context(app)
    app.run({"action": "decide", **ctx, "decision": "Use interviews", "rationale": "Explore choices"})
    app.run({"action": "profile.set", "demographics": {"discipline": ["life_sciences", "computer_information_sciences"]}, "include_in_usage": False})
    prior = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file() and p.suffix in {".json", ".jsonl"}}
    with pytest.raises(BenchsideError):
        app.run({"action": "storage.organise"})
    result = app.run({"action": "storage.organise", "confirm_idle": True})
    assert result["agent"] == str(root / "agent")
    for name, data in prior.items():
        assert (root / "agent" / name).read_bytes() == data
    fresh = App(resolve_paths())
    assert fresh.run({"action": "records.preferences"}) == {"format": "markdown", "configured": True}
    assert fresh.run({"action": "recall", **ctx})["recent_decisions"][0]["decision"] == "Use interviews"
    assert fresh.run({"action": "profile.status"})["demographics"]["discipline"] == ["life_sciences", "computer_information_sciences"]
    assert fresh.run({"action": "storage.organise", "confirm_idle": True})["migrated"] is False
    with pytest.raises(BenchsideError):
        app.run({"action": "decide", **ctx, "decision": "Stale path", "rationale": "Must refuse"})


def test_export_failure_does_not_lose_or_duplicate_saved_decision(tmp_path, monkeypatch):
    from benchside.infrastructure import readable_records
    root = tmp_path / "store"
    paths = Paths(home=root, store_root=root, repo_root=tmp_path)
    app = App(paths)
    ctx = context(app)
    def fail(*args, **kwargs):
        raise OSError("Synthetic export failure")
    monkeypatch.setattr(readable_records, "export_project", fail)
    result = app.run({"action": "decide", **ctx, "decision": "Keep this", "rationale": "Saved before export"})
    assert result["recorded"]
    assert result["readable_records_warning"]
    assert len(app.run({"action": "recall", **ctx})["recent_decisions"]) == 1


def test_path_titles_cannot_escape_researcher_directory(tmp_path):
    root = tmp_path / "store"
    app = App(Paths(home=root, store_root=root, repo_root=tmp_path))
    setup = app.run({"action": "setup", "project_key": "test", "title": "../../private: / beta"})
    result = app.run({"action": "records.export", "project_id": setup["project_id"]})
    assert Path(result["odt"]).is_relative_to(root / "researcher/projects")


def test_native_store_does_not_export_temporary_paths():
    from tests.unit.application.test_native import Notebook
    book = Notebook()
    setup = book.setup()
    result = book.run({"action": "records.export", "project_id": setup["project_id"]})
    assert not result["ok"]
    assert "local" in json.dumps(result["error"]).lower()


def test_migration_copy_failure_keeps_originals_and_does_not_switch_store(tmp_path, monkeypatch):
    from benchside.infrastructure import storage_layout
    root = tmp_path / "old"
    monkeypatch.setenv("BENCHSIDE_HOME", str(root))
    app = App(resolve_paths())
    ctx = context(app)
    journal = app.paths.journal_file(ctx["project_id"])
    original = journal.read_bytes()
    def fail(*args, **kwargs):
        raise OSError("Synthetic disk failure")
    monkeypatch.setattr(storage_layout.shutil, "copytree", fail)
    with pytest.raises(OSError):
        app.run({"action": "storage.organise", "confirm_idle": True})
    assert journal.read_bytes() == original
    assert resolve_paths().home == root
    assert not (root / "agent").exists()
    assert not list(root.glob(".benchside-layout-*"))


def test_renamed_project_updates_readable_folder_without_losing_extra_files(tmp_path):
    root = tmp_path / "store"
    app = App(Paths(home=root, store_root=root, repo_root=tmp_path))
    setup = app.run({"action": "setup", "project_key": "test", "title": "Original title"})
    before = Path(setup["readable_records"]["odt"]).parent
    (before / "my notes.txt").write_text("Keep this")
    renamed = app.run({"action": "setup", "project_id": setup["project_id"], "title": "Updated title"})
    after = Path(renamed["readable_records"]["odt"]).parent
    assert "Updated title" in after.name
    assert not before.exists()
    assert (after / "my notes.txt").read_text() == "Keep this"


def test_symlinked_readable_folder_is_refused_without_writing_outside_store(tmp_path):
    root = tmp_path / "store"
    app = App(Paths(home=root, store_root=root, repo_root=tmp_path))
    setup = app.run({"action": "setup", "project_key": "test", "title": "Test"})
    folder = Path(setup["readable_records"]["odt"]).parent
    outside = tmp_path / "outside"
    folder.rename(outside)
    folder.symlink_to(outside, target_is_directory=True)
    before = (outside / "Research record.odt").read_bytes()
    with pytest.raises(BenchsideError, match="symlink"):
        app.run({"action": "records.export", "project_id": setup["project_id"]})
    assert (outside / "Research record.odt").read_bytes() == before


def test_readable_exports_refuse_git_inside_the_storage_root(tmp_path):
    root = tmp_path / "store"
    (root / "researcher/projects/.git").mkdir(parents=True)
    app = App(Paths(home=root / "agent", store_root=root, repo_root=tmp_path))
    setup = app.run({"action": "setup", "project_key": "test", "title": "Private project"})
    assert setup["readable_records_warning"]
    with pytest.raises(BenchsideError, match="outside Git"):
        app.run({"action": "records.export", "project_id": setup["project_id"]})
    assert not list((root / "researcher").rglob("*.odt"))
    assert not list((root / "researcher").rglob("*.md"))


def test_malformed_readable_index_warns_after_save_instead_of_inviting_duplicate(tmp_path):
    root = tmp_path / "store"
    paths = Paths(home=root, store_root=root, repo_root=tmp_path)
    app = App(paths)
    ctx = context(app)
    (root / "readable-index.json").write_text("[]")
    result = app.run({"action": "decide", **ctx, "decision": "Saved once", "rationale": "Even if export fails"})
    assert result["recorded"]
    assert result["readable_records_warning"]
    assert len(app.run({"action": "recall", **ctx})["recent_decisions"]) == 1


def test_odt_replaces_xml_forbidden_characters_only_in_reading_copy():
    import io

    from benchside.infrastructure.readable_records import odt_bytes
    with zipfile.ZipFile(io.BytesIO(odt_bytes([(0, "α\ufffe\uffff\x01β")])) ) as archive:
        text = "".join(ET.fromstring(archive.read("content.xml")).itertext())
        assert text == "α���β"


def test_long_unicode_title_stays_within_filesystem_name_limit(tmp_path):
    root = tmp_path / "store"
    app = App(Paths(home=root, store_root=root, repo_root=tmp_path))
    setup = app.run({"action": "setup", "project_key": "unicode", "title": "🧪" * 100})
    folder = Path(setup["readable_records"]["odt"]).parent
    assert len(folder.name.encode()) <= 255
    assert folder.exists()


def test_readable_format_default_and_preference_persist_across_projects(tmp_path):
    root = tmp_path / "store"
    paths = Paths(home=root, store_root=root, repo_root=tmp_path)
    app = App(paths)
    assert app.run({"action": "records.preferences"}) == {"format": "odt", "configured": False}
    first = app.run({"action": "setup", "project_key": "one", "title": "First"})
    assert "odt" in first["readable_records"] and "markdown" not in first["readable_records"]
    original = Path(first["readable_records"]["odt"]).read_bytes()
    app.run({"action": "records.configure", "format": "markdown"})
    fresh = App(paths)
    assert fresh.run({"action": "records.preferences"}) == {"format": "markdown", "configured": True}
    exported = fresh.run({"action": "records.export", "project_id": first["project_id"]})
    assert "markdown" in exported and "odt" not in exported
    assert Path(first["readable_records"]["odt"]).read_bytes() == original
    assert exported["previous_copies_not_refreshed"] == [first["readable_records"]["odt"]]
    second = fresh.run({"action": "setup", "project_key": "two", "title": "Second"})
    assert "markdown" in second["readable_records"] and "odt" not in second["readable_records"]


@pytest.mark.parametrize("invalid", ["pdf", "", None, [], True])
def test_invalid_format_does_not_change_preference_or_research_records(tmp_path, invalid):
    root = tmp_path / "store"
    app = App(Paths(home=root, store_root=root, repo_root=tmp_path))
    app.run({"action": "records.configure", "format": "both"})
    with pytest.raises(BenchsideError, match="format"):
        app.run({"action": "records.configure", "format": invalid})
    assert app.run({"action": "records.preferences"})["format"] == "both"
    assert not list(root.rglob("journal.jsonl"))


def test_native_format_preferences_do_not_claim_local_file_support():
    from tests.unit.application.test_native import Notebook
    book = Notebook()
    result = book.run({"action": "records.configure", "format": "odt"})
    assert not result["ok"]
    assert "local" in str(result["error"]).lower()
