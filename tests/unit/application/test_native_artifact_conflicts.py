"""Executable host protocol: artifact-wide versions must stay paired with state.

The fake models Claude's observed whole-artifact compare-and-swap, not its API.
All scientific operations and readback checks use the real Benchside runtime.
"""

from uuid import uuid4

import pytest

from benchside.application.native import reference, run_native
from benchside.domain.shared.error import BenchsideError
from tests.unit.application.test_native import Notebook


class Conflict(Exception):
    pass


class Artifact:
    def __init__(self, state):
        self.files = {"state": state, "journal": ""}
        self.version = 1

    def read(self):
        return self.files["state"], self.version

    def patch(self, version, **files):
        if version != self.version:
            raise Conflict("Nothing was published")
        self.files.update(files)
        self.version += 1
        return self.version


@pytest.mark.parametrize("interleave", ["before_readback", "before_journal", "after_journal"])
def test_two_writers_preserve_decisions_across_journal_refresh(interleave):
    notebook = Notebook()
    a, b = notebook.setup(), notebook.setup()
    artifact = Artifact(notebook.document)

    def run(document, request, operation_id=None):
        result = run_native({
            "action": "native.run", "workspace_id": notebook.workspace_id,
            "document": document, "operation_id": operation_id or uuid4().hex,
            "request": request,
        })
        assert result["ok"]
        return result

    def decision(ctx, text):
        return {"action": "notebook.decide", "project_id": ctx["project_id"],
                "session_id": ctx["session_id"], "decision": text, "rationale": "Synthetic"}

    def writer_b():
        document, version = artifact.read()
        candidate = run(document, decision(b, "B1"))
        artifact.patch(version, state=candidate["markdown"])

    document, version = artifact.read()
    candidate = run(document, decision(a, "A1"))
    version = artifact.patch(version, state=candidate["markdown"])
    if interleave == "before_readback":
        writer_b()
    document, read_version = artifact.read()
    confirmation = {"action": "native.confirm", "workspace_id": notebook.workspace_id,
                    "document": document, "expected": reference(candidate["snapshot"])}
    if interleave == "before_readback":
        with pytest.raises(BenchsideError):
            run_native(confirmation)
        # Reread and validate newer state; never roll back to the older candidate.
        run_native({"action": "native.inspect", "workspace_id": notebook.workspace_id,
                    "document": document})
    else:
        assert run_native(confirmation)["saved"]
    version = read_version  # This version came with these exact state bytes.

    if interleave == "before_journal":
        writer_b()
    try:
        journal = run(document, {"action": "recall", "project_id": a["project_id"]})
        version = artifact.patch(version, journal=journal["project_journal"]["markdown"])
    except Conflict:
        assert interleave == "before_journal"
        document, version = artifact.read()
        journal = run(document, {"action": "recall", "project_id": a["project_id"]})
        version = artifact.patch(version, journal=journal["project_journal"]["markdown"])
    # Carrying the successful patch version is safe ONLY because its base was
    # bound to document, and the patch did not change the notebook state file.
    assert document == artifact.files["state"]

    if interleave == "after_journal":
        writer_b()
    operation = uuid4().hex
    request = decision(a, "A2")
    candidate = run(document, request, operation)
    try:
        artifact.patch(version, state=candidate["markdown"])
    except Conflict:
        assert interleave == "after_journal"
        document, version = artifact.read()
        candidate = run(document, request, operation)  # Same intended operation.
        artifact.patch(version, state=candidate["markdown"])
    document, _ = artifact.read()
    assert run_native({"action": "native.confirm", "workspace_id": notebook.workspace_id,
                       "document": document, "expected": reference(candidate["snapshot"])})["saved"]
    decisions = run(document, {"action": "recall", "project_id": a["project_id"],
                               "history": "all"})["result"]["recent_decisions"]
    assert sorted(d["decision"] for d in decisions) == ["A1", "A2", "B1"]
