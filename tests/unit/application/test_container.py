"""The composition root wires file-backed adapters by default."""

from benchside.application.di import create_container
from benchside.domain.consultation.command.open import OpenConsultation, OpenConsultationHandler
from benchside.domain.consultation.query.recall_project import RecallProject, RecallProjectHandler
from benchside.domain.shared.model.ids import ConsultationId, PersonaId, ProjectId
from benchside.util.di import Scope


class TestFileBackedContainer:
    def test_command_round_trips_through_jsonl_on_disk(self, tmp_path, monkeypatch):
        monkeypatch.setenv("BENCHSIDE_HOME", str(tmp_path / "home"))
        container = create_container()
        pid = ProjectId("wired-project")
        try:
            with container(scope=Scope.UOW) as uow:
                uow.get(OpenConsultationHandler).run(
                    OpenConsultation(
                        consultation_id=ConsultationId("c-1"),
                        project_id=pid,
                        persona_id=PersonaId("pi"),
                    )
                )
            journal_file = tmp_path / "home" / "projects" / "wired-project" / "journal.jsonl"
            assert journal_file.exists(), "command did not persist to the JSONL journal"

            # A second container (fresh process, same disk) sees the state.
            container2 = create_container()
            try:
                with container2(scope=Scope.UOW) as uow:
                    recall = uow.get(RecallProjectHandler).run(RecallProject(project_id=pid))
                assert recall.last_sitting_state == "framing"
            finally:
                container2.close()
        finally:
            container.close()
