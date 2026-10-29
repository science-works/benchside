"""File-backed bindings: the production port seam.

Everything durable routes through the JSONL journal; content comes from the
resolved content root (checkout or packaged data).
"""

import os

from dishka import provide

from benchside.config import Paths, resolve_content_root, resolve_paths
from benchside.domain.authoring.port.renderer import TemplateRenderer
from benchside.domain.authoring.port.repository import PersonaRepository, TemplateRepository
from benchside.domain.authoring.port.skill_writer import SkillWriter
from benchside.domain.consultation.port.repository import (
    ConsultationRepository,
    ProjectRepository,
)
from benchside.domain.export.port.redactor import Redactor
from benchside.domain.export.port.repository import ConsentRepository, ObservationReader
from benchside.domain.export.port.sink import ExportSink
from benchside.domain.shared.port.journal import Journal
from benchside.infrastructure.content.loader import FileTemplateRepository, YamlPersonaRepository
from benchside.infrastructure.content.renderer import PlaceholderRenderer
from benchside.infrastructure.content.writer import FileSkillWriter
from benchside.infrastructure.http_sink import COLLECTOR, HttpExportSink
from benchside.infrastructure.journal.projection import (
    JournalConsentRepository,
    JournalConsultationRepository,
    JournalObservationReader,
    JournalProjectRepository,
)
from benchside.infrastructure.journal.store import JsonlJournal
from benchside.infrastructure.placeholders import RefusingExportSink
from benchside.infrastructure.redaction import TextRedactor
from benchside.util.di import Provider, Scope


class FileProvider(Provider):
    @provide(scope=Scope.APP)
    def get_paths(self) -> Paths:
        return resolve_paths()

    @provide(scope=Scope.APP)
    def get_journal(self, paths: Paths) -> Journal:
        return JsonlJournal(paths)

    @provide(scope=Scope.UOW)
    def get_projects(self, journal: Journal) -> ProjectRepository:
        return JournalProjectRepository(journal)

    @provide(scope=Scope.UOW)
    def get_consultations(self, journal: Journal) -> ConsultationRepository:
        return JournalConsultationRepository(journal)

    @provide(scope=Scope.UOW)
    def get_observations(self, journal: Journal) -> ObservationReader:
        return JournalObservationReader(journal)

    @provide(scope=Scope.UOW)
    def get_consent_repo(self, journal: Journal) -> ConsentRepository:
        return JournalConsentRepository(journal)

    @provide(scope=Scope.APP)
    def get_personas(self) -> PersonaRepository:
        return YamlPersonaRepository(resolve_content_root() / "personas")

    @provide(scope=Scope.APP)
    def get_templates(self) -> TemplateRepository:
        return FileTemplateRepository(resolve_content_root() / "templates")

    @provide(scope=Scope.APP)
    def get_renderer(self, templates: TemplateRepository) -> TemplateRenderer:
        return PlaceholderRenderer(templates)

    @provide(scope=Scope.APP)
    def get_skill_writer(self, paths: Paths) -> SkillWriter:
        return FileSkillWriter(paths.skills_dir)

    redactor = provide(TextRedactor, scope=Scope.APP, provides=Redactor)

    @provide(scope=Scope.APP)
    def get_sink(self) -> ExportSink:
        endpoint = os.environ.get("BENCHSIDE_GAPS_ENDPOINT", f"{COLLECTOR}/v1/gaps")
        return HttpExportSink(endpoint) if endpoint else RefusingExportSink()
