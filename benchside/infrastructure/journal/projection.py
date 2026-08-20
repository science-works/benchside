"""Journal projections: folding the event stream back into aggregates.

This is where event-sourcing actually happens. The domain's repository ports
hide it entirely -- a service asks for a Project and gets one, without knowing
it was rebuilt from a file of events.

Folds are cheap at this scale (a project accumulates hundreds of events, not
millions). If that stops being true, the answer is a snapshot cache behind the
same ports, not a change to the domain.
"""


from benchside.domain.consultation.event.closed import ConsultationClosed
from benchside.domain.consultation.event.critique_raised import CritiqueRaised
from benchside.domain.consultation.event.critique_resolved import CritiqueResolved
from benchside.domain.consultation.event.decision_recorded import DecisionRecorded
from benchside.domain.consultation.event.gap_observed import GapObserved
from benchside.domain.consultation.event.hypothesis_stated import HypothesisStated
from benchside.domain.consultation.event.opened import ConsultationOpened
from benchside.domain.consultation.model.consultation import Consultation
from benchside.domain.consultation.model.project import Project
from benchside.domain.consultation.model.value import (
    Abandoned,
    Converged,
    Critique,
    Decision,
    Hypothesis,
)
from benchside.domain.export.event.consent_granted import ConsentGranted
from benchside.domain.export.event.consent_revoked import ConsentRevoked
from benchside.domain.export.event.observations_exported import ObservationsExported
from benchside.domain.export.model.ledger import ConsentLedger
from benchside.domain.export.model.value import ExportRecord, Grant, Observation
from benchside.domain.shared.model.ids import (
    CONSENT_LEDGER_PROJECT,
    ConsultationId,
    ObservationId,
    ProjectId,
)
from benchside.domain.shared.port.journal import Journal


class JournalProjectRepository:
    """Rebuilds Projects from their journals.

    A project's title is not yet carried by any event, so it falls back to the
    id until a ProjectNamed event exists.
    """

    def __init__(self, journal: Journal) -> None:
        self._journal = journal

    def get(self, project_id: ProjectId) -> Project | None:
        events = list(self._journal.read(project_id))
        if not events:
            return None
        project = Project(id=project_id, title=project_id.root)
        for event in events:
            match event:
                case HypothesisStated():
                    project.hypotheses.append(
                        Hypothesis(
                            id=event.hypothesis_id,
                            statement=event.statement,
                            supersedes=event.supersedes,
                        )
                    )
                case CritiqueRaised():
                    project.critiques.append(Critique(id=event.critique_id, target=event.target))
                case CritiqueResolved():
                    for i, critique in enumerate(project.critiques):
                        if critique.id == event.critique_id:
                            project.critiques[i] = critique.model_copy(
                                update={"resolution": event.resolution}
                            )
                            break
                case DecisionRecorded():
                    project.decisions.append(
                        Decision(
                            id=event.decision_id,
                            decision=event.decision,
                            rationale=event.rationale,
                            decided_at=event.recorded_at,
                            supersedes=event.supersedes,
                        )
                    )
        return project

    def list_all(self) -> list[Project]:
        found = [self.get(pid) for pid in self._journal.projects()]
        return [p for p in found if p is not None]


class JournalConsultationRepository:
    """Rebuilds Consultations, including their state machine, from journals.

    State is replayed rather than stored: open critiques at the time of the
    last event determine whether a live sitting is probing or challenged.
    """

    def __init__(self, journal: Journal) -> None:
        self._journal = journal

    def get(self, consultation_id: ConsultationId) -> Consultation | None:
        for project_id in self._journal.projects():
            for consultation in self.list_for_project(project_id):
                if consultation.id == consultation_id:
                    return consultation
        return None

    def list_for_project(self, project_id: ProjectId) -> list[Consultation]:
        sittings: dict[str, Consultation] = {}
        open_critiques: list[str] = []
        for event in self._journal.read(project_id):
            match event:
                case ConsultationOpened():
                    # Ignore duplicate opens: replaying one must never replace
                    # (and thereby reset) an existing sitting (bug B3).
                    if event.consultation_id not in sittings:
                        sittings[event.consultation_id] = Consultation(
                            id=event.consultation_id,
                            project_id=event.project_id,
                            persona_id=event.persona_id,
                            close_requires=event.close_requires,
                        )
                case HypothesisStated() if event.consultation_id in sittings:
                    sittings[event.consultation_id].probe()
                case CritiqueRaised() if event.consultation_id in sittings:
                    open_critiques.append(event.critique_id)
                    sittings[event.consultation_id].settle(tuple(open_critiques))
                case CritiqueResolved() if event.consultation_id in sittings:
                    if event.critique_id in open_critiques:
                        open_critiques.remove(event.critique_id)
                    sittings[event.consultation_id].settle(tuple(open_critiques))
                case ConsultationClosed() if event.consultation_id in sittings:
                    sitting = sittings[event.consultation_id]
                    sitting.state = (
                        Converged(outcome=event.detail)
                        if event.state == "converged"
                        else Abandoned(reason=event.detail)
                    )
        return list(sittings.values())

    def latest_for_project(self, project_id: ProjectId) -> Consultation | None:
        found = self.list_for_project(project_id)
        return found[-1] if found else None


class JournalObservationReader:
    """Reads captured gaps across every project.

    Read-only cross-domain access: export never reaches into consultation's
    aggregates, it folds the same events out of the shared journal.
    """

    def __init__(self, journal: Journal) -> None:
        self._journal = journal

    def list_all(self) -> list[Observation]:
        found: list[Observation] = []
        for project_id in self._journal.projects():
            if project_id.root == CONSENT_LEDGER_PROJECT.root:
                continue
            for event in self._journal.read(project_id):
                if isinstance(event, GapObserved):
                    found.append(
                        Observation(
                            id=event.observation_id,
                            project_id=event.project_id,
                            gap=event.gap,
                        )
                    )
        return found

    def list_unshared(self) -> list[Observation]:
        return [o for o in self.list_all() if o.id not in self._already_shared()]

    def _already_shared(self) -> set[ObservationId]:
        shared: set[ObservationId] = set()
        for event in self._journal.read(CONSENT_LEDGER_PROJECT):
            if isinstance(event, ObservationsExported):
                shared.update(event.observation_ids)
        return shared


class JournalConsentRepository:
    """Rebuilds the consent ledger from its own stream.

    Consent is machine-wide rather than per project, so it lives under a
    reserved project id.
    """

    def __init__(self, journal: Journal) -> None:
        self._journal = journal

    def load(self) -> ConsentLedger:
        ledger = ConsentLedger()
        for event in self._journal.read(CONSENT_LEDGER_PROJECT):
            match event:
                case ConsentGranted():
                    ledger.grants.append(
                        Grant(
                            id=event.grant_id,
                            gap_kinds=event.gap_kinds,
                            granted_at=event.recorded_at,
                        )
                    )
                case ConsentRevoked():
                    for i, grant in enumerate(ledger.grants):
                        if grant.id == event.grant_id and grant.revoked_at is None:
                            ledger.grants[i] = grant.model_copy(
                                update={"revoked_at": event.recorded_at}
                            )
                            break
                case ObservationsExported():
                    ledger.exports.append(
                        ExportRecord(
                            grant_id=event.grant_id,
                            observation_ids=event.observation_ids,
                            payload_sha256=event.payload_sha256,
                            exported_at=event.recorded_at,
                        )
                    )
        return ledger


