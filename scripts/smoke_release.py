"""Exercise the extracted app package in fresh processes using synthetic records."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path


def smoke(archive_path: Path):
    with tempfile.TemporaryDirectory(prefix="benchside-release-") as temporary:
        root = Path(temporary)
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(root)
        entries = [
            root / "benchside/scripts/benchside_app.py",  # standalone skill
            root / "benchside/skills/benchside/scripts/benchside_app.py",  # portable plugin
            root / "skills/benchside/scripts/benchside_app.py",  # Claude plugin upload
        ]
        found = [path for path in entries if path.is_file()]
        assert len(found) == 1, "Archive must contain one recognized runtime entry"
        entry = found[0]
        env = {
            **os.environ,
            "TMPDIR": str(root),  # Require a cold runtime install for every archive.
            "PIP_NO_INDEX": "1",
            "UV_OFFLINE": "1",
            "UV_CACHE_DIR": str(root / "uv-cache"),
            "XDG_CONFIG_HOME": str(root / "config"),
            "XDG_DATA_HOME": str(root / "default-data"),
            "BENCHSIDE_GAPS_ENDPOINT": "",
            "BENCHSIDE_FEEDBACK_ENDPOINT": "",
            "BENCHSIDE_USAGE_ENDPOINT": "",
            "BENCHSIDE_STUDIES_ENDPOINT": "",
            "BENCHSIDE_SURVEYS_ENDPOINT": "",
            "BENCHSIDE_ACTIVITY_ENDPOINT": "",
        }
        env.pop("BENCHSIDE_HOME", None)
        env.pop("BENCHSIDE_REPO", None)
        env.pop("PYTHONPATH", None)

        def run(request, *options):
            result = subprocess.run(
                [sys.executable, str(entry), *options],
                cwd=root,
                env=env,
                input=json.dumps(request),
                capture_output=True,
                text=True,
                timeout=240,
                check=False,
            )
            if result.returncode:
                raise RuntimeError(result.stdout + result.stderr)
            response = json.loads(result.stdout)
            assert response["ok"], response
            return response["result"]

        manifest = json.loads((entry.parent.parent / "runtime/manifest.json").read_text())
        assert run({"action": "version"}) == {"version": manifest["version"]}
        assert run({"action": "version"}) == {"version": manifest["version"]}
        assert not (root / "default-data").exists()
        transfer = root / "native-response.json"
        summary = run({"action": "native.create"}, "--response-file", str(transfer))
        complete = json.loads(transfer.read_text())["result"]
        assert "snapshot" not in summary and "markdown" not in summary
        assert not complete["saved"]
        assert transfer.stat().st_mode & 0o077 == 0
        assert run(
            {
                "action": "native.confirm",
                "workspace_id": summary["candidate"]["workspace_id"],
                "document": complete["markdown"],
                "expected": summary["candidate"],
            }
        )["saved"]
        print("Read-only version checks and exact native response-file transfer passed.")

        probe = run({"action": "storage.configure", "directory": str(root / "private-records")})
        assert (
            Path(run({"action": "storage.location"})["storage"])
            == (root / "private-records").resolve()
        )
        assert run({"action": "storage.check", "token": probe["token"]})["matched"]
        roles = run({"action": "roles"})
        assert len(roles) == 7
        for role in roles:
            setup = run(
                {
                    "action": "setup",
                    "project_key": f"synthetic-{role['id']}",
                    "host": "chatgpt",
                    "surface": "desktop",
                }
            )
            context = {k: setup[k] for k in ("project_id", "session_id")}
            started = run({"action": "start", "role": role["id"], **context})
            context["sitting_id"] = started["sitting"]["id"]
            if role["id"] == "pi":
                run(
                    {
                        "action": "hypothesis",
                        "statement": "The supplied comparison can distinguish the two explanations.",
                        **context,
                    }
                )
            else:
                run(
                    {
                        "action": "record",
                        "record": {
                            "kind": role["record_kind"],
                            "summary": "Synthetic smoke-test scientific record",
                            "details": ["Compare independent samples before generalising."],
                            "sources": ["Synthetic smoke-test excerpt, methods paragraph"],
                        },
                        **context,
                    }
                )
            shared_setup = run(
                {"action": "setup", "host": "claude", "project_id": context["project_id"]}
            )
            context["session_id"] = shared_setup["session_id"]
            assert context["project_id"] in {p["project_id"] for p in run({"action": "projects"})}
            resumed = run({"action": "start", "role": role["id"], **context})
            assert resumed["sitting"]["id"] == context["sitting_id"]
            run(
                {
                    "action": "decide",
                    "decision": "Check the independent comparison",
                    "rationale": "Resolve the stated uncertainty",
                    **context,
                }
            )
            closed = run(
                {"action": "close", "converged": True, "detail": "Agreed next check", **context}
            )
            assert closed["recall"]["last_sitting_state"] == "converged"
        status = run({"action": "sharing.status"})
        assert all(not status[channel]["enabled"] for channel in ("gaps", "feedback", "usage"))
        print(
            "Packaged runtime: all seven roles saved, resumed and concluded across fresh processes."
        )
        print("Private storage persisted locally. All submission endpoints were disabled.")
        print(
            "This checks the package, not ChatGPT/Claude cloud account persistence or scientific advice quality."
        )

        snapshot = run({"action": "native.create"})["snapshot"]

        def native(command, project=None):
            nonlocal snapshot
            request = {
                "action": "native.run",
                "workspace_id": snapshot["workspace_id"],
                "document": snapshot,
                "request": command,
            }
            if project:
                request["project_document"] = {"document_id": project, "title": "Synthetic test"}
            candidate = run(request)
            assert candidate["ok"], candidate
            assert not candidate["saved"]
            snapshot = candidate["snapshot"]
            confirmed = run(
                {
                    "action": "native.confirm",
                    "workspace_id": snapshot["workspace_id"],
                    "document": candidate["markdown"],
                    "expected": {k: snapshot[k] for k in ("workspace_id", "revision", "sha256")},
                }
            )
            assert confirmed["saved"]
            return candidate["result"]

        for role in roles:
            page = f"synthetic-page-{role['id']}"
            setup = native({"action": "setup", "host": "chatgpt", "project_key": page}, page)
            context = {key: setup[key] for key in ("project_id", "session_id")}
            context["sitting_id"] = native({"action": "start", "role": role["id"], **context})[
                "sitting"
            ]["id"]
            if role["id"] == "pi":
                native(
                    {
                        "action": "hypothesis",
                        "statement": "Synthetic comparison distinguishes causes",
                        **context,
                    }
                )
            else:
                native(
                    {
                        "action": "record",
                        "record": {
                            "kind": role["record_kind"],
                            "summary": "Synthetic native record",
                            "details": ["Check independent controls"],
                            "sources": ["Synthetic methods, page 2"],
                        },
                        **context,
                    }
                )
            native(
                {
                    "action": "decide",
                    "decision": "Check independent controls",
                    "rationale": "Resolve uncertainty",
                    **context,
                }
            )
            shared_setup = native(
                {"action": "setup", "host": "claude", "project_id": context["project_id"]}, page
            )
            context["session_id"] = shared_setup["session_id"]
            resumed = native({"action": "start", "role": role["id"], **context})
            assert resumed["sitting"]["id"] == context["sitting_id"]
            assert (
                resumed["recall"]["recent_decisions"][0]["decision"] == "Check independent controls"
            )
            native({"action": "close", "converged": True, "detail": "Agreed next step", **context})
        print(
            "Native snapshots: all seven roles saved, restored and concluded across fresh processes."
        )
        print(
            "This simulates document transport; live native tool checks are a separate release gate."
        )
        for adapter in (run, native):
            assert not any(adapter({"action": "metascience.status"})["choices"].values())
            adapter({"action": "metascience.consent", "choice": "analysis", "enabled": True})
            scope = {"host": "chatgpt", "source_id": "synthetic-external-research"}
            adapter({"action": "metascience.scopes", "scopes": [scope]})
            batch = adapter(
                {
                    "action": "metascience.sample",
                    "candidates": [{"scope": scope, "session_ref": "synthetic-no-persona-session"}],
                }
            )
            token = next(iter(batch["selected"]))
            adapter(
                {
                    "action": "metascience.record",
                    "week": batch["week"],
                    "token": token,
                    "classification": {
                        "benchside_role": "none",
                        "activity": {"value": "coding", "basis": "model_inferred"},
                        "obstacle": {"value": "unknown", "basis": "unknown"},
                        "verification": {"value": "none_visible", "basis": "model_inferred"},
                        "outcome": {"value": "not_reported", "basis": "unknown"},
                    },
                }
            )
            restored = adapter({"action": "metascience.batch", "week": batch["week"]})
            assert restored["records"][token]["benchside_role"] == "none"
            assert not adapter({"action": "metascience.status"})["choices"]["sharing"]
            adapter({"action": "metascience.consent", "choice": "analysis", "enabled": False})
        print(
            "Metascience: private sampled activity restored across fresh local/native processes; no sends."
        )
        # One confirmed native save must retain a whole setup turn. Replay must
        # neither create another session nor change the previously chosen answer.
        empty = run({"action": "native.create"})["snapshot"]
        batched_request = {
            "action": "native.batch",
            "document": empty,
            "workspace_id": empty["workspace_id"],
            "operation_id": uuid.uuid4().hex,
            "steps": [
                {
                    "id": "setup",
                    "project_document": {
                        "document_id": "batch-project",
                        "title": "Batched project",
                    },
                    "request": {
                        "action": "setup",
                        "host": "claude",
                        "project_key": "batch-project",
                    },
                },
                {
                    "id": "choice",
                    "request": {"action": "participation.set", "response": "deferred"},
                },
                {
                    "id": "start",
                    "request": {
                        "action": "start",
                        "role": "methods-clinic",
                        "project_id": {"$ref": "setup.project_id"},
                        "session_id": {"$ref": "setup.session_id"},
                    },
                },
            ],
        }
        batched = run(batched_request)
        assert batched["ok"] and batched["snapshot"]["revision"] == 1
        assert batched["result"]["steps"]["start"]["recall"]["title"] == "Batched project"
        assert run(
            {
                "action": "native.confirm",
                "document": batched["markdown"],
                "workspace_id": empty["workspace_id"],
                "expected": {
                    k: batched["snapshot"][k] for k in ("workspace_id", "revision", "sha256")
                },
            }
        )["saved"]
        replay = run({**batched_request, "document": batched["markdown"]})
        assert replay["replayed"] and not replay["changed"]
        assert replay["result"] == batched["result"]
        status = run(
            {
                "action": "native.batch",
                "document": batched["markdown"],
                "workspace_id": empty["workspace_id"],
                "steps": [{"id": "choice", "request": {"action": "participation.status"}}],
            }
        )
        assert not status["changed"]
        assert status["result"]["steps"]["choice"]["response"] == "deferred"
        print(
            "Batched setup: one save, friendly title, remembered deferral and exact replay verified."
        )
        # A ready cache must not conceal a damaged bundled dependency.
        dependency = next((entry.parents[1] / "runtime/wheels").glob("*.whl"))
        dependency.write_bytes(dependency.read_bytes() + b"corrupt-test-only")
        damaged = subprocess.run(
            [sys.executable, str(entry)],
            cwd=root,
            env=env,
            input=json.dumps({"action": "roles"}),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert damaged.returncode == 1
        assert "dependency checksum" in json.loads(damaged.stdout)["error"]
        print("Damaged dependency rejected even after a successful cached install.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    smoke(parser.parse_args().archive.resolve())
