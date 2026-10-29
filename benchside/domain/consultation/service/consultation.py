"""Consultation business logic.

Every mutation follows the same shape: load the aggregates, let them enforce
the transition, append the corresponding event to the journal. The journal is
the store, so there is no separate save step.

Cross-aggregate coordination lives here: the Project owns the critique set,
the Consultation owns the state machine, and this service keeps them in step.
"""

import logging
from datetime import UTC, datetime

from benchside.domain.consultation.event.closed import ConsultationClosed
from benchside.domain.consultation.event.critique_raised import CritiqueRaised
from benchside.domain.consultation.event.critique_resolved import CritiqueResolved
from benchside.domain.consultation.event.decision_recorded import DecisionRecorded
from benchside.domain.consultation.event.gap_observed import GapObserved
from benchside.domain.consultation.event.hypothesis_stated import HypothesisStated
from benchside.domain.consultation.event.opened import ConsultationOpened
from benchside.domain.consultation.event.research_recorded import ResearchRecorded
from benchside.domain.consultation.model.consultation import Consultation
from benchside.domain.consultation.model.project import Project
from benchside.domain.consultation.model.value import (
    Critique,
    Decision,
    Hypothesis,
    RecordKind,
    ResearchRecord,
    Resolution,
    Target,
)
from benchside.domain.consultation.port.repository import (
    ConsultationRepository,
    ProjectRepository,
)
from benchside.domain.shared.error import InvalidStateError, NotFoundError
from benchside.domain.shared.event import new_event_id
from benchside.domain.shared.model.capture import CaptureKind, CloseRequirement
from benchside.domain.shared.model.gap import Gap
from benchside.domain.shared.model.ids import (
    ConsultationId,
    CritiqueId,
    DecisionId,
    HypothesisId,
    ObservationId,
    PersonaId,
    ProjectId,
)
from benchside.domain.shared.port.journal import Journal
from benchside.domain.shared.service import Service

logger = logging.getLogger(__name__)


class ConsultationService(Service):
    projects: ProjectRepository
    consultations: ConsultationRepository
    journal: Journal

    def open(
        self,
        *,
        consultation_id: ConsultationId,
        project_id: ProjectId,
        persona_id: PersonaId,
        close_requires: tuple[CloseRequirement, ...] = (),
        critique_requires_hypothesis: bool = True,
        record_kind: RecordKind | None = None,
        persona_version: str = "1",
        host: str = "unknown",
        app_version: str = "unknown",
        surface: str = "unknown",
    ) -> Consultation:
        if self.consultations.get(consultation_id) is not None:
            raise InvalidStateError(f"Consultation already exists: {consultation_id}")
        consultation = Consultation(
            id=consultation_id,
            project_id=project_id,
            persona_id=persona_id,
            close_requires=close_requires,
            critique_requires_hypothesis=critique_requires_hypothesis,
            record_kind=record_kind,
            persona_version=persona_version,
            host=host,
            app_version=app_version,
            surface=surface,
        )
        self.journal.append(
            project_id,
            ConsultationOpened(
                id=new_event_id(),
                consultation_id=consultation_id,
                project_id=project_id,
                persona_id=persona_id,
                close_requires=close_requires,
                critique_requires_hypothesis=critique_requires_hypothesis,
                record_kind=record_kind,
                persona_version=persona_version,
                host=host,
                app_version=app_version,
                surface=surface,
            ),
        )
        return consultation

    def state_hypothesis(
        self,
        *,
        consultation_id: ConsultationId,
        hypothesis_id: HypothesisId,
        statement: str,
        supersedes: HypothesisId | None = None,
    ) -> Project:
        consultation, project = self._load_pair(consultation_id)
        project.state_hypothesis(
            Hypothesis(id=hypothesis_id, statement=statement, supersedes=supersedes)
        )
        consultation.probe()
        self.journal.append(
            project.id,
            HypothesisStated(
                id=new_event_id(),
                project_id=project.id,
                consultation_id=consultation_id,
                hypothesis_id=hypothesis_id,
                statement=statement,
                supersedes=supersedes,
            ),
        )
        return project

    def raise_critique(
        self,
        *,
        consultation_id: ConsultationId,
        critique_id: CritiqueId,
        target: Target,
    ) -> Project:
        consultation, project = self._load_pair(consultation_id)
        project.raise_critique(
            Critique(id=critique_id, target=target),
            requires_hypothesis=consultation.critique_requires_hypothesis,
        )
        consultation.settle(project.open_critiques)
        self.journal.append(
            project.id,
            CritiqueRaised(
                id=new_event_id(),
                project_id=project.id,
                consultation_id=consultation_id,
                critique_id=critique_id,
                target=target,
            ),
        )
        return project

    def resolve_critique(
        self,
        *,
        consultation_id: ConsultationId,
        critique_id: CritiqueId,
        resolution: Resolution,
    ) -> Project:
        consultation, project = self._load_pair(consultation_id)
        project.resolve_critique(critique_id, resolution)
        consultation.settle(project.open_critiques)
        self.journal.append(
            project.id,
            CritiqueResolved(
                id=new_event_id(),
                project_id=project.id,
                consultation_id=consultation_id,
                critique_id=critique_id,
                resolution=resolution,
            ),
        )
        return project

    def record_decision(
        self,
        *,
        consultation_id: ConsultationId,
        decision_id: DecisionId,
        decision: str,
        rationale: str,
        supersedes: DecisionId | None = None,
    ) -> Project:
        consultation, project = self._load_pair(consultation_id)
        consultation._require_live()
        project.record_decision(
            Decision(
                id=decision_id,
                decision=decision,
                rationale=rationale,
                decided_at=datetime.now(UTC),
                supersedes=supersedes,
            )
        )
        self.journal.append(
            project.id,
            DecisionRecorded(
                id=new_event_id(),
                project_id=project.id,
                consultation_id=consultation_id,
                decision_id=decision_id,
                decision=decision,
                rationale=rationale,
                supersedes=supersedes,
            ),
        )
        return project

    def capture_gap(
        self,
        *,
        consultation_id: ConsultationId,
        observation_id: ObservationId,
        gap: Gap,
    ) -> None:
        """Record where the workflow broke down.

        Journal-only: a gap is not part of the Project's scientific record and
        does not touch its invariants. The export domain reads these.
        """
        consultation = self._load_consultation(consultation_id)
        consultation._require_live()
        self.journal.append(
            consultation.project_id,
            GapObserved(
                id=new_event_id(),
                project_id=consultation.project_id,
                consultation_id=consultation_id,
                observation_id=observation_id,
                gap=gap,
            ),
        )

    def record_research(self, *, consultation_id: ConsultationId, record: ResearchRecord) -> None:
        consultation, project = self._load_pair(consultation_id)
        consultation._require_live()
        if consultation.record_kind != record.kind:
            raise InvalidStateError(
                f"This role records {consultation.record_kind}, not {record.kind}"
            )
        if record.kind == "literature" and not record.sources:
            raise InvalidStateError("A literature record needs a supplied or retrieved source")
        if any(r.id == record.id for r in project.research_records):
            raise InvalidStateError(f"Research record already exists: {record.id}")
        self.journal.append(
            consultation.project_id,
            ResearchRecorded(
                id=new_event_id(),
                project_id=consultation.project_id,
                consultation_id=consultation_id,
                record=record,
            ),
        )

    def close(
        self,
        *,
        consultation_id: ConsultationId,
        converged: bool,
        detail: str,
    ) -> Consultation:
        consultation = self._load_consultation(consultation_id)
        if converged:
            # A different sitting may have raised a concern since this one last wrote.
            consultation.settle(self.get_project(consultation.project_id).open_critiques)
            self._enforce_close_requirements(consultation)
            consultation.converge(detail)
        else:
            consultation.abandon(detail)
        self.journal.append(
            consultation.project_id,
            ConsultationClosed(
                id=new_event_id(),
                project_id=consultation.project_id,
                consultation_id=consultation_id,
                state="converged" if converged else "abandoned",
                detail=detail,
            ),
        )
        return consultation

    def get(self, consultation_id: ConsultationId) -> Consultation:
        return self._load_consultation(consultation_id)

    def get_project(self, project_id: ProjectId) -> Project:
        project = self.projects.get(project_id)
        if project is None:
            raise NotFoundError(f"Project not found: {project_id}")
        return project

    def latest_for_project(self, project_id: ProjectId) -> Consultation | None:
        return self.consultations.latest_for_project(project_id)

    def _load_consultation(self, consultation_id: ConsultationId) -> Consultation:
        consultation = self.consultations.get(consultation_id)
        if consultation is None:
            raise NotFoundError(f"Consultation not found: {consultation_id}")
        return consultation

    def _enforce_close_requirements(self, consultation: Consultation) -> None:
        """A converged close must meet the requirements snapshotted at open.

        Counts are derived from the sitting's own journal events, so this is
        the mechanism that prevents empty journals: you cannot cleanly finish
        a sitting you never recorded.
        """
        if not consultation.close_requires:
            return
        counts = self.capture_counts(consultation)
        missing = [
            f"{req.kind.value} (have {counts.get(req.kind, 0)}, need {req.minimum})"
            for req in consultation.close_requires
            if counts.get(req.kind, 0) < req.minimum
        ]
        if missing:
            raise InvalidStateError(
                "Cannot close converged; requirements unmet: " + ", ".join(missing)
            )

    def capture_counts(self, consultation: Consultation) -> dict[CaptureKind, int]:
        """What this sitting has recorded, by capture kind (drives status/close)."""
        counts: dict[CaptureKind, int] = {}
        kind_by_event = {
            HypothesisStated: CaptureKind.HYPOTHESIS,
            CritiqueRaised: CaptureKind.CRITIQUE,
            CritiqueResolved: CaptureKind.RESOLUTION,
            DecisionRecorded: CaptureKind.DECISION,
            GapObserved: CaptureKind.GAP,
            ResearchRecorded: CaptureKind.RECORD,
        }
        for event in self.journal.read(consultation.project_id):
            kind = kind_by_event.get(type(event))
            if kind is not None and event.consultation_id == consultation.id:
                counts[kind] = counts.get(kind, 0) + 1
        return counts

    def _load_pair(self, consultation_id: ConsultationId) -> tuple[Consultation, Project]:
        consultation = self._load_consultation(consultation_id)
        return consultation, self.get_project(consultation.project_id)
