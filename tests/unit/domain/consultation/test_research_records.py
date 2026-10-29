"""Research roles must work without inventing a hypothesis or an objection."""

import pytest

from benchside.domain.consultation.model.value import ResearchRecord, TargetsClaim
from benchside.domain.shared.error import InvalidStateError
from benchside.domain.shared.model.capture import CaptureKind, CloseRequirement
from benchside.domain.shared.model.ids import PersonaId
from tests.unit.domain.consultation.test_close_requirements import CID, PID, make_service


def open_methods(service):
    return service.open(
        consultation_id=CID,
        project_id=PID,
        persona_id=PersonaId("methods-clinic"),
        critique_requires_hypothesis=False,
        record_kind="methods",
        close_requires=(
            CloseRequirement(kind=CaptureKind.RECORD),
            CloseRequirement(kind=CaptureKind.DECISION),
        ),
    )


def test_methods_records_and_resume_without_hypothesis(journal):
    service = make_service(journal)
    open_methods(service)
    service.record_research(
        consultation_id=CID,
        record=ResearchRecord(
            id="r1",
            kind="methods",
            summary="Low recovery after extraction",
            details=("Expected 80%; observed 20%.", "Test spike recovery before extraction."),
        ),
    )
    service.raise_critique(
        consultation_id=CID,
        critique_id="k1",
        target=TargetsClaim(claim="Extraction is responsible", ground="No recovery control"),
    )
    resumed = make_service(journal)
    assert resumed.get_project(PID).research_records[0].summary == "Low recovery after extraction"
    assert resumed.get(CID).record_kind == "methods"
    with pytest.raises(InvalidStateError):
        resumed.close(consultation_id=CID, converged=True, detail="done")
    resumed.resolve_critique(
        consultation_id=CID,
        critique_id="k1",
        resolution="accepted_as_limitation",
    )
    resumed.record_decision(
        consultation_id=CID,
        decision_id="d1",
        decision="Run spike recovery",
        rationale="Separates extraction from detection",
    )
    assert (
        resumed.close(consultation_id=CID, converged=True, detail="Run control").state.kind
        == "converged"
    )
    assert not resumed.get_project(PID).hypotheses


def test_old_pi_still_requires_hypothesis(journal):
    service = make_service(journal)
    service.open(consultation_id=CID, project_id=PID, persona_id=PersonaId("pi"))
    with pytest.raises(InvalidStateError, match="hypothesis"):
        service.raise_critique(
            consultation_id=CID,
            critique_id="k1",
            target=TargetsClaim(claim="X causes Y", ground="No comparison"),
        )


def test_role_rejects_wrong_record_kind(journal):
    service = make_service(journal)
    open_methods(service)
    with pytest.raises(InvalidStateError, match="methods"):
        service.record_research(
            consultation_id=CID,
            record=ResearchRecord(id="r1", kind="results", summary="A result", details=("Detail",)),
        )


def test_literature_requires_a_source(journal):
    service = make_service(journal)
    service.open(
        consultation_id=CID,
        project_id=PID,
        persona_id=PersonaId("journal-club"),
        critique_requires_hypothesis=False,
        record_kind="literature",
    )
    with pytest.raises(InvalidStateError, match="source"):
        service.record_research(
            consultation_id=CID,
            record=ResearchRecord(id="r1", kind="literature", summary="Paper", details=("Claim",)),
        )


@pytest.mark.parametrize("operation", ["record", "decision", "gap"])
def test_closed_sitting_cannot_keep_recording(journal, operation):
    from benchside.domain.shared.model.gap import MissingIndex

    service = make_service(journal)
    open_methods(service)
    service.close(consultation_id=CID, converged=False, detail="Stopped")
    with pytest.raises(InvalidStateError, match="already"):
        if operation == "record":
            service.record_research(
                consultation_id=CID,
                record=ResearchRecord(id="r1", kind="methods", summary="Late", details=("Late",)),
            )
        elif operation == "decision":
            service.record_decision(
                consultation_id=CID,
                decision_id="d1",
                decision="Late",
                rationale="Late",
            )
        else:
            service.capture_gap(
                consultation_id=CID,
                observation_id="o1",
                gap=MissingIndex(question="Late"),
            )
