"""Structured app adapter. The assistant calls this; scientists need no terminal.

Storage is a provider/user-owned durable directory, never a Git repository.
Cloud hosts must prove that the same directory survives a new conversation;
an ephemeral execution sandbox is deliberately not certified as durable memory.
"""

import hashlib
import json
import uuid

from pydantic import TypeAdapter

from benchside.application.sharing import SharingFlow
from benchside.config import Paths, resolve_content_root
from benchside.domain.consultation.model.value import ResearchRecord, Resolution, Target
from benchside.domain.consultation.query.recall_project import RecallProject, RecallProjectHandler
from benchside.domain.consultation.service.consultation import ConsultationService
from benchside.domain.export.model.reporting import AppVersion
from benchside.domain.shared.error import BenchsideError, InvalidStateError, ValidationError
from benchside.domain.shared.model.gap import Gap
from benchside.domain.shared.model.ids import PersonaId, user_project_id
from benchside.domain.shared.model.provenance import AppProvenance
from benchside.infrastructure.content.loader import YamlPersonaRepository
from benchside.infrastructure.files import atomic_json, file_lock
from benchside.infrastructure.journal.projection import (
    JournalConsultationRepository,
    JournalProjectRepository,
)
from benchside.infrastructure.journal.store import JsonlJournal
from benchside.infrastructure.session_context import recording_context

READ_ACTIONS = {
    "recall",
    "roles",
    "projects",
    "profile.status",
    "participation.status",
    "sharing.status",
    "sharing.history",
    "storage.check",
    "metascience.status",
    "metascience.history",
    "metascience.batch",
}


class App:
    def __init__(self, paths: Paths):
        self.paths = paths
        self.journal = JsonlJournal(paths)
        self.consultations = JournalConsultationRepository(self.journal)
        self.service = ConsultationService(
            projects=JournalProjectRepository(self.journal),
            consultations=self.consultations,
            journal=self.journal,
        )
        self.personas = YamlPersonaRepository(resolve_content_root() / "personas")

    def run(self, request: dict):
        action = request.get("action")
        if not isinstance(action, str):
            raise ValidationError("An app action is required")
        try:
            self._storage_boundary()
            with file_lock(self.paths.home / ".transaction.lock"):
                return self._dispatch(action, request)
        except BenchsideError as error:
            self._failure(action, error)
            raise
        except (KeyError, TypeError, ValueError) as err:
            self._failure(action, err)
            raise ValidationError(f"Invalid {action} request: {err}") from err

    def _failure(self, action, error):
        if (
            action in READ_ACTIONS
            or action.startswith(
                ("sharing.", "storage.", "metascience.", "profile.", "participation.")
            )
            or action == "setup"
        ):
            return
        from benchside.domain.export.service.reporting import ReportingService
        from benchside.domain.shared.error import StorageUnavailableError

        code = (
            "recording_unavailable"
            if isinstance(error, (StorageUnavailableError, OSError))
            else "recording_invalid"
        )
        try:
            with file_lock(self.paths.home / ".transaction.lock"):
                ReportingService(journal=self.journal).failure(code)
        except (BenchsideError, OSError):
            pass  # A reporting failure must not mask the scientific-record failure.

    def _storage_boundary(self):
        home = self.paths.home.resolve()
        if any((directory / ".git").exists() for directory in (home, *home.parents)):
            raise InvalidStateError("Benchside's journal must be stored outside Git")

    def _dispatch(self, action, request):
        if action.startswith("metascience."):
            from benchside.application.metascience import Metascience

            return Metascience(self.paths).dispatch(request)
        if action == "storage.probe":
            token = uuid.uuid4().hex
            atomic_json(self.paths.home / "app-probe.json", {"token": token})
            return {
                "token": token,
                "storage": str(self.paths.home),
                "status": "written",
                "next": "In a new conversation, call storage.check with this token.",
            }
        if action == "storage.check":
            probe = self.paths.home / "app-probe.json"
            return {
                "matched": probe.exists()
                and json.loads(probe.read_text()).get("token") == request["token"],
                "storage": str(self.paths.home),
                "note": "A same-process or same-sandbox check does not prove cross-chat persistence.",
            }
        if action == "projects":
            return [
                {
                    "project_id": path.stem,
                    "title": json.loads(path.read_text()).get("title", path.stem),
                }
                for path in sorted((self.paths.home / "app-projects").glob("p-*.json"))
            ]
        if action == "roles":
            return [
                {
                    "id": p.id.root,
                    "title": p.title,
                    "description": p.description,
                    "record_kind": p.record_kind,
                    "version": p.version,
                }
                for p in self.personas.list_all()
            ]
        if action == "profile.status":
            return SharingFlow(self.paths).profile().model_dump(mode="json")
        if action == "participation.status":
            return SharingFlow(self.paths).participation().model_dump(mode="json")
        if action == "participation.set":
            return SharingFlow(self.paths).set_participation(request["response"])
        if action == "profile.set":
            return SharingFlow(self.paths).set_profile(
                request["demographics"], request["include_in_usage"]
            )
        if action.startswith("sharing."):
            flow = SharingFlow(self.paths)
            match action:
                case "sharing.status":
                    return flow.status()
                case "sharing.consent":
                    if type(request.get("enabled")) is not bool:
                        raise ValidationError("Consent enabled must be true or false")
                    flow.set_consent(
                        request["channel"], request["enabled"], kinds=request.get("kinds")
                    )
                    return flow.status()
                case "sharing.feedback":
                    return flow.feedback(**request["feedback"]).model_dump(mode="json")
                case "sharing.preview":
                    return [
                        d.model_dump(mode="json")
                        for d in flow.prepare(
                            request["channel"],
                            only=request.get("only"),
                            edits=request.get("edits"),
                            feedback_id=request.get("feedback_id"),
                            comment=request.get("comment"),
                            week=request.get("week"),
                        )
                    ]
                case "sharing.send":
                    return flow.send(request["draft_id"], request["approved_sha256"]).model_dump(
                        mode="json"
                    )
                case "sharing.history":
                    return flow.history()
            raise ValidationError("Unknown sharing action")
        if action == "setup":
            # Stable host project identity, not a title that can be renamed or collide.
            host = request.get("host", "unknown")
            app_version = TypeAdapter(AppVersion).validate_python(
                request.get("app_version", "unknown")
            )
            surface = request.get("surface", "unknown")
            if host not in {"chatgpt", "claude", "unknown"} or surface not in {
                "web",
                "desktop",
                "cli",
                "unknown",
            }:
                raise ValidationError("Unknown app or surface")
            title = request.get("title")
            if title is not None and (
                not isinstance(title, str)
                or not 1 <= len(title) <= 160
                or any(ord(char) < 32 for char in title)
            ):
                raise ValidationError("Use a project title of 1–160 printable characters")
            selected = request.get("project_id")
            if selected:
                project_id = user_project_id(selected).root
                config = self.paths.home / "app-projects" / f"{project_id}.json"
                if not config.is_file():
                    raise InvalidStateError(
                        "Choose an existing project from projects or create a new one"
                    )
            else:
                key = request.get("project_key")
                if not isinstance(key, str) or not key.strip():
                    raise ValidationError("A stable project ID or local folder path is required")
                project_id = "p-" + hashlib.sha256(f"{host}:{key}".encode()).hexdigest()[:32]
                config = self.paths.home / "app-projects" / f"{project_id}.json"
                if not config.exists():
                    identity = {"host": host, "app_version": app_version, "surface": surface}
                    if title is not None:
                        identity["title"] = title
                    atomic_json(config, identity)
            # Creation identity is immutable. Each caller gets its own app context,
            # so another agent opening the same project cannot relabel this session.
            session_id = uuid.uuid4().hex
            atomic_json(
                self.paths.home / "app-sessions" / f"{session_id}.json",
                {
                    "project_id": project_id,
                    "host": host,
                    "app_version": app_version,
                    "surface": surface,
                },
            )
            return {
                "project_id": project_id,
                "session_id": session_id,
                "sharing": SharingFlow(self.paths).status(),
            }

        project_id = user_project_id(request["project_id"])
        project_config = self.paths.home / "app-projects" / f"{project_id.root}.json"
        if not project_config.exists():
            raise InvalidStateError("Set up this app project before recording")
        config = json.loads(project_config.read_text())
        recall = RecallProjectHandler(consultation_service=self.service)
        project_title = config.get("title")

        def recalled():
            result = recall.run(
                RecallProject(
                    project_id=project_id,
                    history=request.get("history", "recent") if action == "recall" else "recent",
                )
            ).model_dump(mode="json")
            if project_title:
                result["title"] = project_title
            return result

        if action == "recall":
            return recalled()
        session = request.get("session_id")
        from benchside.infrastructure.session_context import validate_session_id

        if not session:
            raise ValidationError("Use the session_id returned by setup for recording")
        validate_session_id(session)
        session_file = self.paths.home / "app-sessions" / f"{session}.json"
        if not session_file.is_file():
            raise InvalidStateError("This session is missing; run setup to resume the project")
        config = json.loads(session_file.read_text())
        if config["project_id"] != project_id.root:
            raise InvalidStateError("This session belongs to another project")
        with recording_context(
            session_id=session,
            provenance=AppProvenance(
                host=config["host"],
                app_version=config.get("app_version", "unknown"),
                surface=config["surface"],
            ),
        ):
            if action == "start":
                persona = self.personas.get(PersonaId(request["role"]))
                if persona is None:
                    raise ValidationError("Unknown research role")
                candidates = [
                    sitting
                    for sitting in self.consultations.list_for_project(project_id)
                    if sitting.persona_id == persona.id
                    and sitting.state.kind not in {"converged", "abandoned"}
                ]
                selected = request.get("sitting_id")
                if selected:
                    candidates = [s for s in candidates if s.id == selected]
                    if not candidates:
                        raise ValidationError("That sitting is not open for this project and role")
                if len(candidates) > 1:
                    raise InvalidStateError(
                        "Several sittings are open for this role; choose a sitting_id from recall"
                    )
                sitting = (
                    candidates[0]
                    if candidates
                    else self.service.open(
                        consultation_id=f"c-{uuid.uuid4().hex}",
                        project_id=project_id,
                        persona_id=persona.id,
                        close_requires=persona.flow.close_requires,
                        critique_requires_hypothesis=persona.critique_requires_hypothesis,
                        record_kind=persona.record_kind,
                        persona_version=persona.version,
                        host=config["host"],
                        app_version=config.get("app_version", "unknown"),
                        surface=config["surface"],
                    )
                )
                return {
                    "sitting": sitting.model_dump(mode="json"),
                    "recall": recalled(),
                }
            sitting = self.service.get(request["sitting_id"])
            if sitting.project_id != project_id:
                raise InvalidStateError("A sitting from another project cannot be used here")
            sitting._require_live()
            identifier = uuid.uuid4().hex
            common = {"consultation_id": sitting.id}
            match action:
                case "record":
                    record = ResearchRecord(id=f"r-{identifier}", **request["record"])
                    self.service.record_research(**common, record=record)
                    identifier = record.id
                case "hypothesis":
                    identifier = f"h-{identifier}"
                    self.service.state_hypothesis(
                        **common,
                        hypothesis_id=identifier,
                        statement=request["statement"],
                        supersedes=request.get("supersedes"),
                    )
                case "critique":
                    identifier = f"k-{identifier}"
                    self.service.raise_critique(
                        **common,
                        critique_id=identifier,
                        target=TypeAdapter(Target).validate_python(request["target"]),
                    )
                case "resolve":
                    identifier = request["critique_id"]
                    self.service.resolve_critique(
                        **common,
                        critique_id=identifier,
                        resolution=Resolution(request["resolution"]),
                    )
                case "decide":
                    identifier = f"d-{identifier}"
                    self.service.record_decision(
                        **common,
                        decision_id=identifier,
                        decision=request["decision"],
                        rationale=request["rationale"],
                        supersedes=request.get("supersedes"),
                    )
                case "gap":
                    identifier = f"o-{identifier}"
                    self.service.capture_gap(
                        **common,
                        observation_id=identifier,
                        gap=TypeAdapter(Gap).validate_python(request["gap"]),
                    )
                case "close":
                    if type(request.get("converged")) is not bool:
                        raise ValidationError("converged must be true or false")
                    self.service.close(
                        **common, converged=request["converged"], detail=request["detail"]
                    )
                    identifier = sitting.id
                case _:
                    raise ValidationError("Unknown app action")
            return {
                "recorded": identifier,
                "recall": recalled(),
            }
