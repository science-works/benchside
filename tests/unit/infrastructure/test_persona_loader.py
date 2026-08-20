"""YAML persona loading, including the flow block."""

import pytest

from benchside.domain.shared.error import ValidationError
from benchside.domain.shared.model.capture import CaptureKind
from benchside.domain.shared.model.ids import PersonaId
from benchside.infrastructure.content.loader import YamlPersonaRepository

PERSONA_YAML = """
id: pi
stance: A rigorous but caring PI.
voice: Direct, warm, allergic to vagueness.
expertise: [experimental design]
forcing_questions:
  - ask: What would change your mind?
    push_until: A concrete observation is named.
    red_flags: ["more data needed"]
failure_modes:
  - name: cheerleading
    description: Praise without a challenge.
flow:
  phases:
    - id: context
      goal: Understand where the work stands
      guidance: Open from recall.
      exit_when: You can restate their situation.
    - id: actual-question
      goal: Find the actual question
      guidance: Press for a falsifiable statement.
      captures: [hypothesis]
      exit_when: A hypothesis is recorded.
  close_requires:
    - kind: hypothesis
      minimum: 1
"""


@pytest.fixture
def repo(tmp_path):
    d = tmp_path / "personas"
    d.mkdir()
    (d / "pi.yaml").write_text(PERSONA_YAML)
    return YamlPersonaRepository(d)


class TestFlowParsing:
    def test_flow_round_trips(self, repo):
        persona = repo.get(PersonaId("pi"))
        assert persona is not None
        assert [p.id for p in persona.flow.phases] == ["context", "actual-question"]
        assert persona.flow.phases[1].captures == (CaptureKind.HYPOTHESIS,)
        req = persona.flow.close_requires[0]
        assert (req.kind, req.minimum) == (CaptureKind.HYPOTHESIS, 1)

    def test_unknown_capture_kind_is_a_validation_error(self, tmp_path):
        d = tmp_path / "personas"
        d.mkdir()
        (d / "bad.yaml").write_text(
            PERSONA_YAML.replace("captures: [hypothesis]", "captures: [vibes]")
        )
        with pytest.raises(ValidationError):
            YamlPersonaRepository(d).get(PersonaId("bad"))
