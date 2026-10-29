"""Generate the app skill/plugin from the same persona records and core wheel."""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from benchside import __version__
from benchside.application.packaging import build_agent_skill

ROOT = Path(__file__).resolve().parents[1]

# Standard CPython on the supported desktop and cloud execution platforms.
# Resolution happens at build time; installed plugins never contact a package index.
PLATFORMS = (
    "manylinux2014_x86_64",
    "manylinux2014_aarch64",
    "macosx_11_0_arm64",
    "macosx_10_13_x86_64",
)


def bundle_dependencies(requirements: Path, runtime: Path):
    with tempfile.TemporaryDirectory(prefix="benchside-wheels-") as temporary:
        for version in ("311", "312", "313", "314"):
            for platform in PLATFORMS:
                subprocess.run(
                    [
                        sys.executable, "-m", "pip", "download",
                        "--disable-pip-version-check", "--quiet", "--require-hashes",
                        "--only-binary=:all:", "--no-deps", "--implementation", "cp",
                        "--python-version", version, "--abi", f"cp{version}",
                        "--platform", platform, "--dest", temporary,
                        "-r", str(requirements),
                    ],
                    check=True,
                    timeout=180,
                )
        destination = runtime / "wheels"
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(temporary, destination)
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(destination.glob("*.whl"))
    }


def build(wheel: Path, output: Path):
    plugin = ROOT / "plugins/benchside"
    skill = plugin / "skills/benchside"
    build_agent_skill(skill)
    runtime = skill / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / "source.json").unlink(missing_ok=True)  # Never ship a local source launcher target.
    for stale in runtime.glob("*.whl"):
        stale.unlink()
    shutil.copyfile(wheel, runtime / wheel.name)
    requirements = ROOT / "content/app-requirements.txt"
    shutil.copyfile(requirements, runtime / "requirements.txt")
    dependencies = bundle_dependencies(requirements, runtime)
    (runtime / "manifest.json").write_text(
        json.dumps(
            {
                "version": __version__,
                "wheel": wheel.name,
                "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
                "requirements_sha256": hashlib.sha256(requirements.read_bytes()).hexdigest(),
                "dependency_wheels": dependencies,
            },
            indent=2,
        )
        + "\n"
    )
    output.mkdir(parents=True, exist_ok=True)
    for name, folder, parent in (
        (f"benchside-claude-{__version__}.zip", skill, skill.parent),
        (f"benchside-plugin-{__version__}.zip", plugin, plugin.parent),
        (f"benchside-claude-plugin-{__version__}.zip", plugin, plugin),
    ):
        with zipfile.ZipFile(output / name, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(folder.rglob("*")):
                if path.is_file() and "__pycache__" not in path.parts:
                    archive.write(path, path.relative_to(parent))
        print(output / name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--wheel", type=Path, default=ROOT / f"dist/benchside-{__version__}-py3-none-any.whl"
    )
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    build(args.wheel.resolve(), args.output.resolve())
