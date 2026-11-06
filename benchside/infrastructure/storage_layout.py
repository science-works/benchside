"""An explicit local-store upgrade; native notebooks keep their existing format."""

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from benchside.domain.shared.error import ValidationError
from benchside.infrastructure.files import atomic_json, file_lock

MARKER = ".benchside-layout.json"
STATE_NAMES = ("projects", "sessions", "app-projects", "app-sessions", "reporting", "sharing", "metascience", "app-probe.json", "readable-index.json", "records-preferences.json")


def _state_fingerprint(root):
    """Detect legacy/uncoordinated writers as well as cooperating lifecycle hooks."""
    state = {}
    for name in STATE_NAMES:
        source = root / name
        if not source.exists() and not source.is_symlink():
            continue
        for path in [source, *source.rglob("*")] if source.is_dir() else [source]:
            if path.is_symlink():
                raise ValidationError("Resolve symlinks in private state before organising storage")
            state[str(path.relative_to(root))] = (
                hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
            )
    return state


def organised(root):
    marker = root / MARKER
    if not marker.exists():
        return False
    if marker.is_symlink() or json.loads(marker.read_text()) != {"version": 1, "agent": "agent", "researcher": "researcher"}:
        raise ValidationError("Invalid Benchside folder layout marker")
    if (root / "agent").is_symlink():
        raise ValidationError("Benchside agent storage must not be a symlink")
    return True


def initialise(root):
    root = root.resolve()
    if any((p / ".git").exists() for p in (root, *root.parents)):
        raise ValidationError("Benchside storage must be outside Git")
    if organised(root):
        return
    if (root / "agent").exists():
        raise ValidationError("An agent folder already exists without a Benchside layout marker")
    (root / "agent").mkdir(parents=True, mode=0o700)
    atomic_json(root / MARKER, {"version": 1, "agent": "agent", "researcher": "researcher"})


def organise(root, confirm_idle):
    root = root.resolve()
    if type(confirm_idle) is not bool or not confirm_idle:
        raise ValidationError("Stop other agents using this store, then confirm_idle:true to organise it")
    if any((p / ".git").exists() for p in (root, *root.parents)):
        raise ValidationError("Benchside storage must be outside Git")
    with file_lock(root / ".transaction.lock"), file_lock(root / ".layout.lock"):
        if organised(root):
            return {"agent": str(root / "agent"), "researcher": str(root / "researcher"), "migrated": False}
        if (root / "agent").exists():
            raise ValidationError("An agent folder already exists; preserve it and resolve the conflict before organising")
        sources = [root / name for name in STATE_NAMES if (root / name).exists()]
        original_state = _state_fingerprint(root)
        for source in sources:
            if source.is_symlink() or (source.is_dir() and any(p.is_symlink() for p in source.rglob("*"))):
                raise ValidationError("Resolve symlinks in private state before organising storage")
        # Copy and verify before switching paths. Originals remain as a private backup.
        temporary = Path(tempfile.mkdtemp(prefix=".benchside-layout-", dir=root))
        try:
            for source in sources:
                target = temporary / source.name
                if source.is_dir():
                    shutil.copytree(source, target)
                    for file in source.rglob("*"):
                        if file.is_file() and file.read_bytes() != (target / file.relative_to(source)).read_bytes():
                            raise OSError("Storage copy verification failed")
                else:
                    shutil.copy2(source, target)
                    if source.read_bytes() != target.read_bytes():
                        raise OSError("Storage copy verification failed")
            if _state_fingerprint(root) != original_state:
                raise ValidationError(
                    "Private state changed during folder organisation; originals are intact. "
                    "Stop other agents and retry."
                )
            os.rename(temporary, root / "agent")
            try:
                atomic_json(root / MARKER, {"version": 1, "agent": "agent", "researcher": "researcher"})
            except OSError:
                os.rename(root / "agent", temporary)
                raise
            backup = root / "agent" / "legacy-backup"
            backup.mkdir(mode=0o700)
            for source in sources:
                os.rename(source, backup / source.name)
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)
    return {"agent": str(root / "agent"), "researcher": str(root / "researcher"), "migrated": True, "backup": str(backup)}
