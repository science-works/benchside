"""Packaged runtime cache safety without installing or executing external code."""

import hashlib
import importlib.util
import io
import json
import os
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def packaged_runtime(tmp_path, monkeypatch):
    script = Path(__file__).resolve().parents[3] / "content/app/scripts/benchside_app.py"
    spec = importlib.util.spec_from_file_location("benchside_cache_test_entry", script)
    entry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entry)
    skill = tmp_path / "skill"
    runtime = skill / "runtime"
    (runtime / "wheels").mkdir(parents=True)
    (skill / "scripts").mkdir()
    monkeypatch.setattr(entry, "__file__", str(skill / "scripts/benchside_app.py"))
    temporary = tmp_path / "cache-parent"
    temporary.mkdir(mode=0o700)
    monkeypatch.setattr(entry.tempfile, "gettempdir", lambda: str(temporary))
    monkeypatch.setattr(sys, "path", sys.path.copy())
    monkeypatch.setattr(sys, "dont_write_bytecode", sys.dont_write_bytecode)
    wheel = runtime / "benchside-test.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("benchside/__init__.py", "# synthetic test module\n")
    requirement = runtime / "requirements.txt"
    requirement.write_text("synthetic==1\n")
    dependency = runtime / "wheels/synthetic.whl"
    dependency.write_bytes(b"synthetic dependency archive")
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {
        "wheel": wheel.name,
        "wheel_sha256": digest(wheel),
        "requirements_sha256": digest(requirement),
        "dependency_wheels": {dependency.name: digest(dependency)},
    }
    (runtime / "manifest.json").write_text(json.dumps(manifest))
    identity = hashlib.sha256((json.dumps(manifest, sort_keys=True) + sys.version).encode()).hexdigest()
    calls = []

    def install(command, **kwargs):
        assert "--no-index" in command
        assert kwargs["env"]["UV_OFFLINE"] == "true"
        assert kwargs["env"]["UV_LINK_MODE"] == "copy"
        destination = Path(command[command.index("--target") + 1])
        (destination / "synthetic.py").write_text("# synthetic dependency\n")
        bookkeeping = destination / ".lock"
        bookkeeping.write_text("")
        bookkeeping.chmod(0o777)  # uv's target-install bookkeeping uses this mode.
        calls.append(command)

    monkeypatch.setattr(entry.subprocess, "run", install)
    monkeypatch.setattr(entry.shutil, "which", lambda name: "/synthetic/uv" if name == "uv" else None)
    return entry, temporary, identity, calls


def test_private_cache_reuses_verified_offline_install(packaged_runtime):
    entry, temporary, identity, calls = packaged_runtime
    entry.bootstrap()
    entry.bootstrap()
    assert len(calls) == 1
    directory = temporary / f"benchside-runtime-v2-{os.getuid()}" / identity
    assert directory.stat().st_mode & 0o077 == 0
    assert directory.parent.stat().st_mode & 0o077 == 0
    assert sys.path[0] == str(directory / "site")


def test_response_file_failure_preserves_completed_action_receipt(
    packaged_runtime, monkeypatch, capsys, tmp_path
):
    from benchside.application import bridge

    entry, _, _, _ = packaged_runtime
    calls = []

    def completed(request):
        calls.append(request)
        return {"status": "stored", "sha256": "a" * 64}

    def full_disk(descriptor):
        raise OSError("Synthetic disk full")

    monkeypatch.setattr(entry, "bootstrap", lambda: None)
    monkeypatch.setattr(bridge, "run", completed)
    monkeypatch.setattr(entry.os, "fsync", full_disk)
    monkeypatch.setattr(sys, "stdin", io.StringIO('{"action":"synthetic.send"}'))
    assert entry.main(["--response-file", str(tmp_path / "receipt.json")]) == 0
    response = json.loads(capsys.readouterr().out)
    assert response["ok"] and response["result"]["status"] == "stored"
    assert response["result"]["sha256"] == "a" * 64
    assert response["response_file_error"] == "Synthetic disk full"
    assert len(calls) == 1


def test_interrupted_install_recovers_without_trusting_partial_cache(packaged_runtime, monkeypatch):
    entry, temporary, identity, calls = packaged_runtime
    install = entry.subprocess.run

    def interrupted(*args, **kwargs):
        install(*args, **kwargs)
        raise RuntimeError("synthetic installer interruption")

    monkeypatch.setattr(entry.subprocess, "run", interrupted)
    with pytest.raises(RuntimeError, match="interruption"):
        entry.bootstrap()
    directory = temporary / f"benchside-runtime-v2-{os.getuid()}" / identity
    assert not (directory / ".ready.json").exists()
    monkeypatch.setattr(entry.subprocess, "run", install)
    entry.bootstrap()
    assert len(calls) == 2
    assert (directory / ".ready.json").is_file()


@pytest.mark.parametrize("attack", ["modify", "inject", "remove", "symlink"])
def test_cached_code_changes_are_rejected(packaged_runtime, attack):
    entry, temporary, identity, calls = packaged_runtime
    entry.bootstrap()
    site = temporary / f"benchside-runtime-v2-{os.getuid()}" / identity / "site"
    module = site / "synthetic.py"
    if attack == "modify":
        module.write_text("raise RuntimeError('must never execute')\n")
    elif attack == "inject":
        (site / "injected.py").write_text("# unexpected executable content\n")
    elif attack == "remove":
        module.unlink()
    else:
        module.unlink()
        module.symlink_to(temporary / "external.py")
    # Linux symlinks expose writable mode bits, so the permission check can
    # reject them before the link-type check. Both must stop cache reuse.
    with pytest.raises(RuntimeError, match="integrity|links|ownership or permissions"):
        entry.bootstrap()
    assert len(calls) == 1


def test_integrity_failure_identifies_cache_without_rewriting_it(
    packaged_runtime, monkeypatch, capsys
):
    entry, temporary, identity, calls = packaged_runtime
    entry.bootstrap()
    directory = temporary / f"benchside-runtime-v2-{os.getuid()}" / identity
    module = directory / "site/synthetic.py"
    changed_code = "raise RuntimeError('must never execute')\n"
    module.write_text(changed_code)
    receipt = directory / ".ready.json"
    original_receipt = receipt.read_bytes()
    monkeypatch.setattr(sys, "stdin", io.StringIO('{"action":"roles"}'))

    assert entry.main() == 1

    response = json.loads(capsys.readouterr().out)
    assert response["code"] == "setup_failed"
    assert str(directory) in response["error"]
    assert "verify ownership" in response["error"]
    assert "move aside only this generated cache directory" in response["error"]
    assert "rebuild the runtime offline" in response["error"]
    assert module.read_text() == changed_code
    assert receipt.read_bytes() == original_receipt
    assert len(calls) == 1


@pytest.mark.parametrize("attack", ["symlink", "writable", "foreign-owner"])
def test_precreated_cache_root_is_rejected(packaged_runtime, monkeypatch, attack):
    entry, temporary, identity, calls = packaged_runtime
    root = temporary / f"benchside-runtime-v2-{os.getuid()}"
    if attack == "symlink":
        target = temporary / "attacker-directory"
        target.mkdir(mode=0o700)
        root.symlink_to(target, target_is_directory=True)
    else:
        root.mkdir(mode=0o700)
        if attack == "writable":
            root.chmod(0o777)
        else:
            original = Path.lstat

            def lstat(path, *args, **kwargs):
                value = original(path, *args, **kwargs)
                if path == root:
                    return SimpleNamespace(st_uid=os.getuid() + 1, st_mode=value.st_mode)
                return value

            monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(RuntimeError, match="private, owned"):
        entry.bootstrap()
    assert not calls
    assert not (root / identity).exists()


def test_lock_symlink_does_not_truncate_target(packaged_runtime):
    entry, temporary, identity, calls = packaged_runtime
    directory = entry.private_cache_directory(identity)
    target = temporary / "unrelated-file"
    target.write_text("preserve this content")
    (directory / ".install.lock").symlink_to(target)
    with pytest.raises(OSError):
        entry.bootstrap()
    assert target.read_text() == "preserve this content"
    assert not calls


def test_ready_symlink_is_rejected(packaged_runtime):
    entry, temporary, identity, calls = packaged_runtime
    directory = entry.private_cache_directory(identity)
    target = temporary / "fake-ready"
    target.write_text("{}")
    (directory / ".ready.json").symlink_to(target)
    with pytest.raises(OSError):
        entry.bootstrap()
    assert target.read_text() == "{}"
    assert not calls
