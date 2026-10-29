"""The Project aggregate: the durable thread.

Hypotheses, critiques, and decisions outlive any single sitting, so they live
here rather than on Consultation. A project is what the scientist means by
"my work on X"; a consultation is one conversation about it.
"""

from pydantic import Field

from benchside.domain.consultation.model.value import (
    Critique,
    Decision,
    Hypothesis,
    ResearchRecord,
    Resolution,
    Target,
)
from benchside.domain.shared.error import InvalidStateError, NotFoundError
from benchside.domain.shared.model.aggregate import Aggregate
from benchside.domain.shared.model.ids import CritiqueId, HypothesisId, ProjectId


class Project(Aggregate):
    id: ProjectId
    title: str
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    critiques: list[Critique] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    research_records: list[ResearchRecord] = Field(default_factory=list)

    @property
    def open_critiques(self) -> tuple[CritiqueId, ...]:
        return tuple(c.id for c in self.critiques if c.is_open)

    @property
    def current_hypothesis(self) -> Hypothesis | None:
        superseded = {h.supersedes for h in self.hypotheses if h.supersedes is not None}
        live = [h for h in self.hypotheses if h.id not in superseded]
        return live[-1] if live else None

    def state_hypothesis(self, hypothesis: Hypothesis) -> None:
        if hypothesis.supersedes is not None and not self._has_hypothesis(hypothesis.supersedes):
            raise NotFoundError(f"Cannot supersede unknown hypothesis {hypothesis.supersedes}")
        self.hypotheses.append(hypothesis)

    def raise_critique(self, critique: Critique, *, requires_hypothesis: bool = True) -> None:
        if requires_hypothesis and not self.hypotheses:
            raise InvalidStateError("Cannot critique before a hypothesis is on the table")
        self.critiques.append(critique)

    def resolve_critique(self, critique_id: CritiqueId, resolution: Resolution) -> None:
        for i, critique in enumerate(self.critiques):
            if critique.id != critique_id:
                continue
            if not critique.is_open:
                raise InvalidStateError(f"Critique {critique_id} is already resolved")
            self.critiques[i] = critique.model_copy(update={"resolution": resolution})
            return
        raise NotFoundError(f"Critique not found: {critique_id}")

    def record_decision(self, decision: Decision) -> None:
        if decision.supersedes is not None and not self._has_decision(decision.supersedes):
            raise NotFoundError(f"Cannot supersede unknown decision {decision.supersedes}")
        self.decisions.append(decision)

    def critique_target(self, critique_id: CritiqueId) -> Target:
        for critique in self.critiques:
            if critique.id == critique_id:
                return critique.target
        raise NotFoundError(f"Critique not found: {critique_id}")

    def _has_hypothesis(self, hypothesis_id: HypothesisId) -> bool:
        return any(h.id == hypothesis_id for h in self.hypotheses)

    def _has_decision(self, decision_id: str) -> bool:
        return any(d.id == decision_id for d in self.decisions)
