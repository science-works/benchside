"""Exploratory supervision must not manufacture a hypothesis to save progress."""

import json

import pytest

from benchside.application.app import App
from benchside.domain.consultation.event.opened import ConsultationOpened
from benchside.domain.shared.error import BenchsideError
from benchside.domain.shared.event import new_event_id
from benchside.domain.shared.model.capture import CaptureKind, CloseRequirement
from benchside.domain.shared.model.ids import PersonaId, ProjectId
from tests.unit.application.test_native import Notebook


def context(app, project="exploratory", role="pi"):
    setup = app.run({"action": "setup", "project_key": project})
    ctx = {k: setup[k] for k in ("project_id", "session_id")}
    ctx["sitting_id"] = app.run({"action": "start", "role": role, **ctx})["sitting"]["id"]
    return ctx


def test_exploratory_supervisor_saves_question_and_finishes_without_hypothesis(paths):
    app = App(paths)
    ctx = context(app)
    question = "Which mix of disciplines and career stages should we include?"
    saved = app.run({"action": "question", **ctx, "question": question})
    decision = "Start with six semi-structured interviews about analysis-software selection."
    app.run({"action": "decide", **ctx, "decision": decision, "rationale": "Two weeks available."})
    app.run({"action": "close", **ctx, "converged": True, "detail": "Plan interviews; sampling is open."})
    recall = App(paths).run({"action": "recall", "project_id": ctx["project_id"]})
    assert recall["current_hypothesis"] is None
    assert recall["recent_decisions"][0]["decision"] == decision
    assert recall["open_questions"] == [question]
    assert recall["open_research_questions"][0]["id"] == saved["recorded"]
    assert recall["open_sittings"] == []
    from benchside.infrastructure.journal.projection import JournalObservationReader
    assert JournalObservationReader(app.journal).list_all() == []


def test_question_answer_is_project_scoped_and_survives_replay(paths):
    app = App(paths)
    first, other = context(app), context(app, "other")
    saved = app.run({"action": "question", **first, "question": "Which fields?"})
    with pytest.raises(BenchsideError, match="not found"):
        app.run({"action": "answer", **other, "question_id": saved["recorded"], "answer": "Must fail"})
    assert app.run({"action": "recall", **other})["open_questions"] == []
    app.run({"action": "answer", **first, "question_id": saved["recorded"], "answer": "CS and life sciences."})
    recall = App(paths).run({"action": "recall", **first, "history": "all"})
    assert recall["open_questions"] == []
    assert recall["recent_questions"][0]["answer"] == "CS and life sciences."
    with pytest.raises(BenchsideError, match="already answered"):
        app.run({"action": "answer", **first, "question_id": saved["recorded"], "answer": "Overwrite"})


@pytest.mark.parametrize("value", ["", "   ", None, 12])
def test_question_rejects_invalid_text_without_recording(paths, value):
    app = App(paths)
    ctx = context(app)
    with pytest.raises(BenchsideError):
        app.run({"action": "question", **ctx, "question": value})
    assert app.run({"action": "recall", **ctx})["open_questions"] == []


def test_questions_and_answers_require_live_sitting(paths):
    app = App(paths)
    ctx = context(app)
    saved = app.run({"action": "question", **ctx, "question": "Which fields?"})
    app.run({"action": "close", **ctx, "converged": False, "detail": "Paused test ended."})
    for request in ({"action": "question", "question": "New question?"},
                    {"action": "answer", "question_id": saved["recorded"], "answer": "CS"}):
        with pytest.raises(BenchsideError):
            app.run({**request, **ctx})


def test_general_supervisor_can_critique_without_hypothesis_but_focused_role_cannot(paths):
    app = App(paths)
    target = {"kind": "method", "step": "Recruit only colleagues", "flaw": "selection_bias"}
    broad = context(app)
    app.run({"action": "critique", **broad, "target": target})
    strict = context(app, "focused", "pi-hypothesis")
    with pytest.raises(BenchsideError, match="hypothesis"):
        app.run({"action": "critique", **strict, "target": target})
    app.run({"action": "hypothesis", **strict, "statement": "Prior tool familiarity predicts choice."})
    app.run({"action": "critique", **strict, "target": target})


def test_legacy_pi_contract_is_preserved_and_new_sitting_is_explicit(paths):
    app = App(paths)
    setup = app.run({"action": "setup", "project_key": "legacy"})
    ctx = {k: setup[k] for k in ("project_id", "session_id")}
    app.journal.append(ProjectId(ctx["project_id"]), ConsultationOpened(
        id=new_event_id(), consultation_id="legacy-pi", project_id=ProjectId(ctx["project_id"]),
        persona_id=PersonaId("pi"), persona_version="3", critique_requires_hypothesis=True,
        close_requires=(CloseRequirement(kind=CaptureKind.HYPOTHESIS, minimum=1),),
    ))
    resumed = app.run({"action": "start", **ctx, "role": "pi"})
    assert resumed["sitting"]["id"] == "legacy-pi"
    assert resumed["sitting"]["critique_requires_hypothesis"]
    assert resumed["role_update_available"]
    new = app.run({"action": "start", **ctx, "role": "pi", "new_sitting": True})
    assert new["sitting"]["id"] != "legacy-pi"
    assert not new["sitting"]["critique_requires_hypothesis"]
    assert len(new["recall"]["open_sittings"]) == 2
    with pytest.raises(BenchsideError):
        app.run({"action": "start", **ctx, "role": "pi", "new_sitting": "yes"})
    with pytest.raises(BenchsideError):
        app.run({"action": "start", **ctx, "role": "pi", "new_sitting": True, "sitting_id": "legacy-pi"})


def test_questions_survive_native_transfer_and_do_not_enter_usage_text():
    notebook = Notebook()
    setup = notebook.setup()
    ctx = {k: setup[k] for k in ("project_id", "session_id")}
    ctx["sitting_id"] = notebook.run({"action": "start", **ctx, "role": "pi"})["result"]["sitting"]["id"]
    private = "Which unpublished compound should be studied next?"
    question = notebook.run({"action": "question", **ctx, "question": private})["result"]["recorded"]
    restored = Notebook()
    restored.document, restored.workspace_id = notebook.document, notebook.workspace_id
    fresh = restored.setup()
    recall = restored.run({"action": "recall", **fresh})
    assert recall["result"]["open_research_questions"][0]["id"] == question
    assert private in recall["project_journal"]["markdown"]
    restored.run({"action": "sharing.consent", "channel": "usage", "enabled": True})
    drafts = restored.run({"action": "sharing.preview", "channel": "usage"})["result"]
    payload = json.loads(drafts[0]["preview"]["payload"])
    assert private not in json.dumps(payload)
    assert payload["sessions"][0]["records"]["record"] == 1


@pytest.mark.parametrize("answer", ["", "   ", None, 12])
def test_invalid_answer_leaves_question_open(paths, answer):
    app = App(paths)
    ctx = context(app)
    saved = app.run({"action": "question", **ctx, "question": "Which fields?"})
    with pytest.raises(BenchsideError):
        app.run({"action": "answer", **ctx, "question_id": saved["recorded"], "answer": answer})
    assert app.run({"action": "recall", **ctx})["open_questions"] == ["Which fields?"]
