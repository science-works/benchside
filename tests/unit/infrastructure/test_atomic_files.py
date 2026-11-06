"""Shared durability contract for JSON state and human-readable documents."""

import json
import stat

import pytest

from benchside.domain.shared.error import BenchsideError
from benchside.infrastructure import files


@pytest.mark.parametrize("writer,value", [(files.atomic_bytes, b"new bytes"), (files.atomic_json, {"text": "α"})])
def test_atomic_writers_keep_original_when_replace_fails(tmp_path, monkeypatch, writer, value):
    target = tmp_path / "private"
    target.write_bytes(b"original")

    def fail(*args):
        raise OSError("Synthetic disk error")

    monkeypatch.setattr(files.os, "replace", fail)
    with pytest.raises(OSError):
        writer(target, value)
    assert target.read_bytes() == b"original"
    assert list(tmp_path.iterdir()) == [target]


@pytest.mark.parametrize("writer,value", [(files.atomic_bytes, b"new bytes"), (files.atomic_json, {"text": "α"})])
def test_atomic_writers_refuse_symlinks_and_keep_destination(tmp_path, writer, value):
    target = tmp_path / "target"
    target.write_bytes(b"original")
    link = tmp_path / "link"
    link.symlink_to(target)
    with pytest.raises(BenchsideError, match="symlink"):
        writer(link, value)
    assert link.is_symlink() and target.read_bytes() == b"original"


def test_atomic_writers_create_private_files_and_preserve_json_encoding(tmp_path):
    target = tmp_path / "nested/record.json"
    files.atomic_json(target, {"text": "α"})
    assert target.read_text() == json.dumps({"text": "α"}, ensure_ascii=False, indent=2) + "\n"
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
