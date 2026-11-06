"""Small durable-file primitives. State is outside project source control."""

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def file_lock(path: Path):
    """Serialize read/validate/write transactions on supported POSIX hosts."""
    import fcntl

    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open("a", encoding="utf-8") as handle:
        os.chmod(path, 0o600)
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def atomic_json(path: Path, value) -> None:
    atomic_bytes(path, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def atomic_bytes(path: Path, data: bytes) -> None:
    from benchside.domain.shared.error import ValidationError

    if path.is_symlink():
        raise ValidationError("Atomic file destination must not be a symlink")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".benchside-")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
