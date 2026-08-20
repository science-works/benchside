"""Regression tests for the consultation projection fold (bug B3).

A duplicate ConsultationOpened event must not resurrect a sitting: replaying
open→close→open(dup) was silently resetting the closed sitting to Framing.
"""

import pytest

from benchside.domain.consultation.service.consultation import ConsultationService
from benchside.domain.shared.error import DomainError
from benchside.domain.shared.model.ids import ConsultationId, PersonaId, ProjectId
from benchside.infrastructure.journal.projection import (
    JournalConsultationRepository,
    JournalProjectRepository,
)

PID = ProjectId("test-project")
CID = ConsultationId("c-1")
PERSONA = PersonaId("pi")


def make_service(journal) -> ConsultationService:
    return ConsultationService(
        projects=JournalProjectRepository(journal),
        consultations=JournalConsultationRepository(journal),
        journal=journal,
    )


class TestDuplicateOpen:
    def test_duplicate_open_event_does_not_resurrect_closed_sitting(self, journal):
        """Fold-level: even if a duplicate open lands in the journal, replay
        must keep the closed sitting closed."""
        service = make_service(journal)
        service.open(consultation_id=CID, project_id=PID, persona_id=PERSONA)
        service.close(consultation_id=CID, converged=False, detail="done early")

        # Simulate the duplicate event reaching the journal despite guards.
        from benchside.domain.consultation.event.opened import ConsultationOpened

        journal.append(
            PID,
            ConsultationOpened(
                id="dup-open",
                consultation_id=CID,
                project_id=PID,
                persona_id=PERSONA,
            ),
        )

        sitting = JournalConsultationRepository(journal).get(CID)
        assert sitting is not None
        assert sitting.state.kind == "abandoned", (
            f"duplicate open resurrected the sitting: state={sitting.state.kind}"
        )

    def test_service_rejects_opening_an_existing_sitting_id(self, journal):
        """Service-level: the guard that should prevent the duplicate at all."""
        service = make_service(journal)
        service.open(consultation_id=CID, project_id=PID, persona_id=PERSONA)

        with pytest.raises(DomainError):
            service.open(consultation_id=CID, project_id=PID, persona_id=PERSONA)
