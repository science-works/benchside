"""Verify a separately installed wheel/sdist outside the source checkout; no sends."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def smoke(python: Path, expected_version: str):
    python = python.absolute()  # Preserve the virtual environment's interpreter link.
    with tempfile.TemporaryDirectory(prefix="benchside-python-install-") as temporary:
        root = Path(temporary)
        env = {
            **os.environ,
            "XDG_CONFIG_HOME": str(root / "config"),
            "XDG_DATA_HOME": str(root / "data"),
            "PYTHONNOUSERSITE": "1",
        }
        for key in ("BENCHSIDE_HOME", "BENCHSIDE_REPO", "PYTHONPATH"):
            env.pop(key, None)
        for channel in ("GAPS", "FEEDBACK", "USAGE", "STUDIES", "SURVEYS", "ACTIVITY"):
            env[f"BENCHSIDE_{channel}_ENDPOINT"] = ""

        def execute(command, request=None):
            result = subprocess.run(
                [str(part) for part in command], cwd=root, env=env,
                input=None if request is None else json.dumps(request),
                text=True, capture_output=True, timeout=90, check=False,
            )
            if result.returncode:
                raise RuntimeError(result.stdout + result.stderr)
            return result.stdout

        installed = json.loads(execute([
            python, "-c", ("import json, benchside; "
            "print(json.dumps({'path':benchside.__file__, 'version':benchside.__version__}))"),
        ]))
        assert installed["version"] == expected_version, installed
        assert "site-packages" in Path(installed["path"]).parts, installed
        bench = python.parent / "bench"
        assert "setup" in execute([bench, "--help"])
        skills = root / "host-skills"
        execute([bench, "setup", "--agent", "generic", "--skills-dir", skills])
        entry = skills / "benchside/scripts/benchside_app.py"
        assert entry.is_file()
        assert len(list((skills / "benchside/references/roles").glob("*.md"))) == 8

        def run(request):
            response = json.loads(execute([python, entry], request))
            assert response["ok"], response
            return response["result"]

        assert run({"action": "version"}) == {"version": expected_version}
        assert not (root / "data").exists(), "Setup/version must not create research records"
        probe = run({"action": "storage.configure", "directory": str(root / "private")})
        assert run({"action": "storage.check", "token": probe["token"]})["matched"]
        setup = run({"action": "setup", "project_key": "SYNTHETIC-PYPI-INSTALL", "host": "unknown"})
        context = {key: setup[key] for key in ("project_id", "session_id")}
        started = run({"action": "start", "role": "pi", **context})
        context["sitting_id"] = started["sitting"]["id"]
        run({"action": "question", "question": "Which synthetic comparison?", **context})
        decision = "Check the independent synthetic comparison"
        run({"action": "decide", "decision": decision, "rationale": "Resolve uncertainty", **context})
        restored = run({"action": "setup", "project_id": context["project_id"], "host": "unknown"})
        context["session_id"] = restored["session_id"]
        resumed = run({"action": "start", "role": "pi", **context})
        assert resumed["sitting"]["id"] == context["sitting_id"]
        run({"action": "records.configure", "format": "both"})
        exported = run({"action": "records.export", "project_id": context["project_id"]})
        assert decision in Path(exported["markdown"]).read_text()
        assert Path(exported["odt"]).is_file()
        status = run({"action": "sharing.status"})
        assert all(not status[channel]["enabled"] for channel in ("gaps", "feedback", "usage"))
        print(f"Installed {expected_version}: CLI, eight-role generic setup, private save/restore, "
              "reading copies and sharing-off defaults passed. No submissions.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    smoke(args.python, args.version)
