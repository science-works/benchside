"""Close requirements: snapshotted at open, enforced at close.

The snapshot lives in the ConsultationOpened event so replay determinism never
depends on a mutable persona YAML outside the journal.
"""

import pytest

from benchside.domain.consultation.service.consultation import ConsultationService
from benchside.domain.shared.error import InvalidStateError
from benchside.domain.shared.model.capture import CaptureKind, CloseRequirement
from benchside.domain.shared.model.ids import ConsultationId, PersonaId, ProjectId
from benchside.infrastructure.journal.projection import (
    JournalConsultationRepository,
    JournalProjectRepository,
)

PID = ProjectId("test-project")
CID = ConsultationId("c-1")
REQUIRES = (CloseRequirement(kind=CaptureKind.HYPOTHESIS, minimum=1),)


def make_service(journal) -> ConsultationService:
    return ConsultationService(
        projects=JournalProjectRepository(journal),
        consultations=JournalConsultationRepository(journal),
        journal=journal,
    )


class TestCloseRequirementSnapshot:
    def test_converged_close_refused_when_requirements_unmet(self, journal):
        service = make_service(journal)
        service.open(
            consultation_id=CID,
            project_id=PID,
            persona_id=PersonaId("pi"),
            close_requires=REQUIRES,
        )
        with pytest.raises(InvalidStateError, match="hypothesis"):
            service.close(consultation_id=CID, converged=True, detail="all done")

    def test_converged_close_allowed_once_met(self, journal):
        service = make_service(journal)
        service.open(
            consultation_id=CID,
            project_id=PID,
            persona_id=PersonaId("pi"),
            close_requires=REQUIRES,
        )
        service.state_hypothesis(
            consultation_id=CID, hypothesis_id="h1", statement="X causes Y"
        )
        closed = service.close(consultation_id=CID, converged=True, detail="next step agreed")
        assert closed.state.kind == "converged"

    def test_abandoned_close_never_blocked_by_requirements(self, journal):
        service = make_service(journal)
        service.open(
            consultation_id=CID,
            project_id=PID,
            persona_id=PersonaId("pi"),
            close_requires=REQUIRES,
        )
        closed = service.close(consultation_id=CID, converged=False, detail="ran out of time")
        assert closed.state.kind == "abandoned"

    def test_snapshot_survives_replay(self, journal):
        """The requirement must be enforced from the journal, not from any
        live persona lookup: a fresh repository fold must carry it."""
        service = make_service(journal)
        service.open(
            consultation_id=CID,
            project_id=PID,
            persona_id=PersonaId("pi"),
            close_requires=REQUIRES,
        )
        fresh = make_service(journal)  # new repos, same journal
        with pytest.raises(InvalidStateError, match="hypothesis"):
            fresh.close(consultation_id=CID, converged=True, detail="done")
