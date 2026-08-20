"""The persona-as-program flow model and its rendering."""

from benchside.domain.authoring.model.flow import Flow, Phase
from benchside.domain.shared.model.capture import CaptureKind, CloseRequirement


def make_flow() -> Flow:
    return Flow(
        phases=(
            Phase(
                id="context",
                goal="Understand where the work stands",
                guidance="Open with what you know from recall.",
                exit_when="You can restate their situation in one sentence.",
            ),
            Phase(
                id="actual-question",
                goal="Find the actual question",
                guidance="Press until a falsifiable statement lands.",
                captures=(CaptureKind.HYPOTHESIS,),
                exit_when="A hypothesis is recorded.",
            ),
        ),
        close_requires=(CloseRequirement(kind=CaptureKind.HYPOTHESIS, minimum=1),),
    )


class TestFlowRendering:
    def test_flow_placeholder_renders_phases_in_order(self, paths):
        from benchside.domain.authoring.model.persona import Persona
        from benchside.domain.shared.model.ids import PersonaId
        from benchside.infrastructure.content.renderer import PlaceholderRenderer

        class NoBlocks:
            def skill_template(self) -> str:
                return ""

            def block(self, name: str) -> str | None:
                return None

        persona = Persona(
            id=PersonaId("pi"),
            stance="supervisor",
            expertise=("supervision",),
            voice="direct",
            flow=make_flow(),
        )
        text = PlaceholderRenderer(NoBlocks()).render("{{FLOW}}", persona)
        assert text.index("context") < text.index("actual-question")
        assert "bench hypothesis" in text, "captures must render as explicit bench calls"
        assert "You can restate their situation" in text
