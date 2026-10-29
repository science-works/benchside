"""Run the installed source or packaged runtime with one JSON request on stdin."""

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def private_cache_directory(identity):
    """A shared temporary parent must not let another account substitute our code."""
    base = Path(tempfile.gettempdir()).resolve()
    for parent in (base, *base.parents):
        info = parent.lstat()
        if (
            not stat.S_ISDIR(info.st_mode)
            or info.st_uid not in {0, os.getuid()}
            or (info.st_mode & 0o022 and not info.st_mode & stat.S_ISVTX)
        ):
            raise RuntimeError("Unsafe ancestor for the Benchside runtime cache")
    directory = base
    for name in (f"benchside-runtime-v2-{os.getuid()}", identity):
        directory /= name
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            pass
        info = directory.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise RuntimeError("Runtime cache must be a private, owned directory without symlinks")
    return directory


def cache_file(path, flags, *, private=False):
    """Never follow a lock/manifest symlink or open a special file."""
    descriptor = os.open(path, flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    info = os.fstat(descriptor)
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_uid != os.getuid()
        or info.st_nlink != 1
        or info.st_mode & (0o077 if private else 0o022)
    ):
        os.close(descriptor)
        raise RuntimeError("Unsafe file in the Benchside runtime cache")
    return descriptor


def cache_inventory(directory):
    """Detect changed, injected or missing executable content before import."""
    if not stat.S_ISDIR(directory.lstat().st_mode):
        raise RuntimeError("Runtime cache must not contain links or special files")
    inventory = {}
    for path in (directory, *sorted(directory.rglob("*"))):
        info = path.lstat()
        if info.st_uid != os.getuid() or info.st_mode & 0o022:
            raise RuntimeError("Unsafe ownership or permissions in the runtime cache")
        if stat.S_ISDIR(info.st_mode):
            continue
        if not stat.S_ISREG(info.st_mode):
            raise RuntimeError("Runtime cache must not contain links or special files")
        with os.fdopen(cache_file(path, os.O_RDONLY), "rb") as handle:
            inventory[str(path.relative_to(directory))] = hashlib.file_digest(
                handle, "sha256"
            ).hexdigest()
    return inventory


def seal_cache(directory):
    """Installers may create permissive bookkeeping files inside our private tree."""
    if not stat.S_ISDIR(directory.lstat().st_mode):
        raise RuntimeError("Runtime cache must not contain links or special files")
    for path in (directory, *sorted(directory.rglob("*"))):
        info = path.lstat()
        if info.st_uid != os.getuid() or not (
            stat.S_ISDIR(info.st_mode) or (stat.S_ISREG(info.st_mode) and info.st_nlink == 1)
        ):
            raise RuntimeError("Unsafe file produced by the offline runtime installer")
        path.chmod(stat.S_IMODE(info.st_mode) & 0o700, follow_symlinks=False)


def run_source(request, source):
    repair = (
        "Restore or reinstall the Benchside source environment, then have your agent "
        "rerun bench setup for this skill location. Keep using the existing research-record storage."
    )
    try:
        settings = json.loads(source.read_text())
        if set(settings) != {"schema", "python", "package_root"} or (
            settings["schema"] != "benchside.source.v1"
        ):
            raise ValueError("Invalid source runtime configuration")
        interpreter = Path(settings["python"])
        package_root = Path(settings["package_root"])
        if not interpreter.is_absolute() or not package_root.is_absolute():
            raise ValueError("Source runtime paths must be absolute")
        if not interpreter.is_file() or not os.access(interpreter, os.X_OK):
            raise ValueError("The saved Python interpreter is unavailable")
        if not (package_root / "benchside/application/bridge.py").is_file():
            raise ValueError("The saved Benchside source is unavailable")
        response = subprocess.run(
            [
                str(interpreter),
                "-I",
                "-B",
                "-c",
                (
                    "import sys; sys.path.insert(0, sys.argv[1]); "
                    "from benchside.application.bridge import main; raise SystemExit(main())"
                ),
                str(package_root),
            ],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            check=False,
            timeout=240,
        )
        result = json.loads(response.stdout)
        if not isinstance(result, dict) or type(result.get("ok")) is not bool:
            raise ValueError("The installed runtime did not return a valid response")
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise RuntimeError(
            f"Benchside's source runtime could not start: {error}. {repair}"
        ) from error
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(
            "Benchside's source runtime timed out. Check the saved records before retrying; "
            "the action may already have completed."
        ) from error
    return result


def bootstrap():
    if sys.version_info < (3, 11):  # noqa: UP036 - this bootstrap runs before package installation.
        raise RuntimeError("Benchside needs Python 3.11 or later in this app")
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "runtime/manifest.json").read_text())
    wheel = root / "runtime" / manifest["wheel"]
    requirements = root / "runtime/requirements.txt"
    if hashlib.sha256(wheel.read_bytes()).hexdigest() != manifest["wheel_sha256"]:
        raise RuntimeError("Packaged runtime checksum does not match")
    if hashlib.sha256(requirements.read_bytes()).hexdigest() != manifest["requirements_sha256"]:
        raise RuntimeError("Dependency lock checksum does not match")
    dependencies = manifest.get("dependency_wheels")
    if not dependencies:
        raise RuntimeError("This package has no offline dependencies; install a rebuilt release")
    wheelhouse = root / "runtime/wheels"
    for name, digest in dependencies.items():
        if Path(name).name != name or not name.endswith(".whl"):
            raise RuntimeError("Invalid dependency wheel name")
        if hashlib.sha256((wheelhouse / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"Packaged dependency checksum does not match: {name}")
    identity = hashlib.sha256(
        (json.dumps(manifest, sort_keys=True) + sys.version).encode(),
    ).hexdigest()
    directory = private_cache_directory(identity)
    site = directory / "site"
    # First-use setup is isolated and locked. It never installs into the project.
    import fcntl

    descriptor = cache_file(directory / ".install.lock", os.O_RDWR | os.O_CREAT, private=True)
    with os.fdopen(descriptor, "r+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        marker = directory / ".ready.json"
        if marker.exists() or marker.is_symlink():
            with os.fdopen(cache_file(marker, os.O_RDONLY, private=True)) as handle:
                receipt = json.load(handle)
            if (
                receipt.get("identity") != identity
                or not receipt.get("files")
                or receipt["files"] != cache_inventory(site)
            ):
                raise RuntimeError(
                    "Runtime cache integrity check failed. Have your agent verify ownership "
                    f"and move aside only this generated cache directory: {directory}. "
                    "Then rerun the installed skill to rebuild the runtime offline from its "
                    "verified bundle. Keep the installed package and research-record storage "
                    "in place; do not edit the cache contents or its integrity receipt."
                )
        else:
            if site.exists() or site.is_symlink():
                seal_cache(site)  # Validate incomplete installer output before discarding it.
                shutil.rmtree(site)
            site.mkdir(mode=0o700)
            if importlib.util.find_spec("pip"):
                installer = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check"]
            elif shutil.which("uv"):
                installer = ["uv", "pip", "install", "--python", sys.executable]
            else:
                raise RuntimeError("The app needs pip or uv to install the bundled runtime")
            # Host installer settings must not add remote find-links or indexes.
            environment = {
                key: value
                for key, value in os.environ.items()
                if not key.startswith(("PIP_", "UV_")) or key == "UV_CACHE_DIR"
            }
            environment.update(
                PIP_CONFIG_FILE=os.devnull,
                UV_OFFLINE="true",
                UV_NO_CONFIG="true",
                UV_LINK_MODE="copy",
            )
            subprocess.run(
                installer
                + [
                    "--target",
                    str(site),
                    "--no-index",
                    "--no-deps",
                    "--find-links",
                    str(wheelhouse),
                    "--only-binary=:all:",
                    "--require-hashes",
                    "-r",
                    str(requirements),
                ],
                check=True,
                env=environment,
                stdout=sys.stderr,
                timeout=180,
            )
            with zipfile.ZipFile(wheel) as archive:
                for name in archive.namelist():
                    target = (site / name).resolve()
                    if not target.is_relative_to(site.resolve()):
                        raise RuntimeError("Unsafe runtime archive path")
                archive.extractall(site)
            seal_cache(site)
            receipt = {"identity": identity, "files": cache_inventory(site)}
            with os.fdopen(
                cache_file(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, private=True), "w"
            ) as handle:
                json.dump(receipt, handle)
                handle.flush()
                os.fsync(handle.fileno())
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(site))


def response_summary(response, path):
    """Keep opaque native state in the file, not in the model's copy buffer."""
    summary = {**response, "response_file": str(path)}
    result = response.get("result")
    if isinstance(result, dict) and "snapshot" in result and "markdown" in result:
        summary["result"] = {k: v for k, v in result.items() if k not in {"snapshot", "markdown"}}
        summary["result"]["candidate"] = {
            key: result["snapshot"][key] for key in ("workspace_id", "revision", "sha256")
        }
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--response-file", type=Path, help="new private file for the complete response"
    )
    args = parser.parse_args(argv or [])
    output = None
    try:
        if args.response_file:
            if not args.response_file.is_absolute():
                raise ValueError(
                    "Use an absolute response-file path in a private working directory"
                )
            # Reserve before running anything: a bad destination must not trigger
            # a submission, and retries must never overwrite an unsaved candidate.
            descriptor = os.open(args.response_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            output = os.fdopen(descriptor, "w", encoding="utf-8")
        request = json.load(sys.stdin)
        if not isinstance(request, dict) or not isinstance(request.get("action"), str):
            raise TypeError("Provide a JSON object with an action")
        source = Path(__file__).resolve().parents[1] / "runtime/source.json"
        if source.is_file():
            response = run_source(request, source)
        else:
            bootstrap()
            from benchside.application.bridge import run

            response = {"ok": True, "result": run(request)}
    except Exception as error:  # noqa: BLE001 - the process boundary must return a JSON error.
        response = {
            "ok": False,
            "error": str(error),
            "code": getattr(error, "code", "setup_failed"),
        }
    displayed = response
    if output is not None:
        try:
            with output:
                json.dump(response, output, ensure_ascii=False)
                output.flush()
                os.fsync(output.fileno())
            displayed = response_summary(response, args.response_file)
        except OSError as error:
            # The action may have completed; preserve its full result/receipt on
            # stdout rather than implying it failed and inviting a duplicate send.
            displayed = {**response, "response_file_error": str(error)}
    print(json.dumps(displayed, ensure_ascii=False))
    return 0 if response["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
