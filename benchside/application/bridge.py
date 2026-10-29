"""One JSON protocol for source installs and packaged app runtimes."""

import json
import sys

from benchside.application.app import App
from benchside.config import configure_local_storage, resolve_paths


def run(request):
    if not isinstance(request, dict) or not isinstance(request.get("action"), str):
        raise TypeError("Provide a JSON object with an action")
    if request["action"] == "version":
        from benchside import __version__

        return {"version": __version__}
    if request["action"].startswith("native."):
        from benchside.application.native import run_native

        return run_native(request)
    if request["action"] == "storage.configure":
        return configure_local_storage(request["directory"])
    if request["action"] == "storage.location":
        return {"storage": str(resolve_paths().home)}
    return App(resolve_paths()).run(request)


def main():
    try:
        result = run(json.load(sys.stdin))
        print(json.dumps({"ok": True, "result": result}, ensure_ascii=False))
        return 0
    except Exception as error:  # noqa: BLE001 - JSON process boundary, including IO failures.
        print(
            json.dumps(
                {"ok": False, "error": str(error), "code": getattr(error, "code", "setup_failed")}
            )
        )
        return 1
