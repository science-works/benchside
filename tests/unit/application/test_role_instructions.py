"""Execute the action names agents actually see in generated role references."""

import re

import pytest

from benchside.application.app import App
from benchside.application.packaging import build_agent_skill
from benchside.domain.shared.error import BenchsideError


def test_generated_role_capture_instructions_dispatch(paths, tmp_path):
    skill = tmp_path / "skill"
    build_agent_skill(skill)
    app = App(paths)
    for role in app.run({"action": "roles"}):
        reference = (skill / "references/roles" / f"{role['id']}.md").read_text()
        actions = re.findall(r"run `([a-z]+) adapter action`", reference)
        setup = app.run({"action": "setup", "project_key": role["id"]})
        context = {key: setup[key] for key in ("project_id", "session_id")}
        start = app.run({"action": "start", "role": role["id"], **context})
        context["sitting_id"] = start["sitting"]["id"]
        payloads = {
            "hypothesis": {"statement": "Synthetic controls explain measurement loss"},
            "critique": {
                "target": {"kind": "method", "step": "Synthetic assay", "flaw": "missing_control"}
            },
            "record": {
                "record": {
                    "kind": start["sitting"]["record_kind"],
                    "summary": "Synthetic role check",
                    "details": ["An independent control is required for comparison."],
                    "sources": ["Supplied synthetic excerpt, page 1"],
                }
            },
            "decide": {"decision": "Run paired controls", "rationale": "Test both stages"},
        }
        assert actions
        for action in actions:
            # An unknown name must fail here, rather than being corrected by a
            # test-only translation that the researcher never sees.
            result = app.run({"action": action, **context, **payloads.get(action, {})})
            assert result["recorded"]
        assert app.run({"action": "recall", **context})["recent_decisions"]


@pytest.mark.parametrize("missing", ["fabricated", "removed"])
def test_recording_rejects_missing_session_without_changing_scientific_records(paths, missing):
    app = App(paths)
    setup = app.run({"action": "setup", "project_key": "synthetic"})
    context = {key: setup[key] for key in ("project_id", "session_id")}
    start = app.run({"action": "start", "role": "methods-clinic", **context})
    context["sitting_id"] = start["sitting"]["id"]
    before = app.run({"action": "recall", **context})
    if missing == "removed":
        (paths.home / "app-sessions" / f"{context['session_id']}.json").unlink()
    else:
        context["session_id"] = "f" * 32
    with pytest.raises(BenchsideError, match="session is missing"):
        app.run({"action": "decide", **context, "decision": "Must not save", "rationale": "Test"})
    assert app.run({"action": "recall", **context}) == before
