"""The Consultation aggregate: one sitting with a persona.

Episodic. Owns only the state machine; the science it discusses belongs to the
Project. The service supplies the project's open-critique set, and this
aggregate decides whether a transition is legal.
"""

from benchside.domain.consultation.model.value import (
    TERMINAL,
    Abandoned,
    Challenged,
    Converged,
    Framing,
    Probing,
    State,
)
from benchside.domain.shared.error import InvalidStateError
from benchside.domain.shared.model.aggregate import Aggregate
from benchside.domain.shared.model.capture import CloseRequirement
from benchside.domain.shared.model.ids import ConsultationId, CritiqueId, PersonaId, ProjectId


class Consultation(Aggregate):
    id: ConsultationId
    project_id: ProjectId
    persona_id: PersonaId
    state: State = Framing()
    close_requires: tuple[CloseRequirement, ...] = ()

    def _require_live(self) -> None:
        if self.state.kind in TERMINAL:
            raise InvalidStateError(f"Consultation is already {self.state.kind}")

    def probe(self) -> None:
        """A hypothesis landed; the persona starts pressing."""
        self._require_live()
        if self.state.kind == "framing":
            self.state = Probing()

    def settle(self, open_critiques: tuple[CritiqueId, ...]) -> None:
        """Reconcile with the project's open-critique set after any change."""
        self._require_live()
        self.state = Challenged(open_critiques=open_critiques) if open_critiques else Probing()

    def converge(self, outcome: str) -> None:
        self._require_live()
        if self.state.kind == "challenged":
            raise InvalidStateError("Cannot converge while critiques are open")
        self.state = Converged(outcome=outcome)

    def abandon(self, reason: str) -> None:
        self._require_live()
        self.state = Abandoned(reason=reason)
