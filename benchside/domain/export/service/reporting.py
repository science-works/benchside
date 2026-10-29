"""Optional reporting, with no shared identifiers in workflow observations."""

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

from pydantic import TypeAdapter
from pydantic import ValidationError as SchemaError

from benchside.domain.consultation.event import (
    ConsultationClosed,
    ConsultationOpened,
    CritiqueRaised,
    CritiqueResolved,
    DecisionRecorded,
    GapObserved,
    HypothesisStated,
    ResearchRecorded,
)
from benchside.domain.export.event.reporting import (
    FeedbackRecorded,
    ReportingConsentChanged,
    ReportSubmitted,
    UsageFailureRecorded,
)
from benchside.domain.export.model.reporting import (
    FAILURE_CODES,
    AppVersion,
    Channel,
    Feedback,
    FeedbackPayload,
    RecordCounts,
    Role,
    UsagePayload,
    UsageRow,
    Version,
    parse_feedback,
)
from benchside.domain.export.model.value import ExportPreview
from benchside.domain.export.port.redactor import Redactor
from benchside.domain.export.port.sink import ExportSink
from benchside.domain.shared.error import ConsentRequiredError, NotFoundError, ValidationError
from benchside.domain.shared.event import new_event_id
from benchside.domain.shared.model.ids import CONSENT_LEDGER_PROJECT, ProjectId
from benchside.domain.shared.port.journal import Journal
from benchside.domain.shared.service import Service

REPORTING_PROJECT = ProjectId("reporting-ledger")
RECORD_EVENTS = {
    HypothesisStated: "hypothesis",
    CritiqueRaised: "critique",
    CritiqueResolved: "resolution",
    DecisionRecorded: "decision",
    GapObserved: "gap",
    ResearchRecorded: "record",
}
_ROLE = TypeAdapter(Role)
_VERSION = TypeAdapter(Version)
_APP_VERSION = TypeAdapter(AppVersion)


def week_start(now: datetime | None = None) -> str:
    day = (now or datetime.now(UTC)).astimezone(UTC).date()
    return (day - timedelta(days=day.weekday())).isoformat()


class ReportingService(Service):
    journal: Journal

    def active_grant(self, channel: Channel) -> str | None:
        found = None
        for event in self.journal.read(CONSENT_LEDGER_PROJECT):
            if isinstance(event, ReportingConsentChanged) and event.channel == channel:
                found = event.id if event.enabled else None
        return found

    def set_consent(self, channel: Channel, enabled: bool) -> str | None:
        current = self.active_grant(channel)
        if bool(current) == enabled:
            return current
        event = ReportingConsentChanged(id=new_event_id(), channel=channel, enabled=enabled)
        self.journal.append(CONSENT_LEDGER_PROJECT, event)
        return event.id if enabled else None

    def record_feedback(self, feedback: Feedback) -> Feedback:
        self.journal.append(
            REPORTING_PROJECT, FeedbackRecorded(id=new_event_id(), feedback=feedback)
        )
        return feedback

    def feedback_payload(self, identifier: str, version: str) -> str:
        for event in self.journal.read(REPORTING_PROJECT):
            if isinstance(event, FeedbackRecorded) and event.feedback.id == identifier:
                return FeedbackPayload(
                    benchside_version=version,
                    feedback=event.feedback,
                ).model_dump_json(by_alias=True, indent=2)
        raise NotFoundError("Feedback was not found")

    def failure(self, code: str) -> None:
        if code in FAILURE_CODES and self.active_grant("usage"):
            self.journal.append(
                REPORTING_PROJECT,
                UsageFailureRecorded(id=new_event_id(), code=code),
            )

    def usage_payload(self, *, installation_id, report_id, week, revision, version) -> UsagePayload:
        start = date.fromisoformat(week)
        end = start + timedelta(days=7)
        groups = {}
        # IDs are used locally to join events, then discarded from the report.
        for project_id in self.journal.projects():
            if project_id in {REPORTING_PROJECT, CONSENT_LEDGER_PROJECT}:
                continue
            events = list(self.journal.read(project_id))
            sittings = {}
            reportable = {}
            for event in events:
                if isinstance(event, ConsultationOpened):
                    sittings.setdefault(event.consultation_id, event)
            for identifier, sitting in sittings.items():
                try:
                    reportable[identifier] = (
                        _ROLE.validate_python(sitting.persona_id.root),
                        _VERSION.validate_python(sitting.persona_version),
                    )
                except SchemaError:
                    # Custom/legacy roles remain valid private science records,
                    # but cannot be represented by the collector's strict schema.
                    continue
            seen = set()
            seen_opens = set()
            seen_closes = set()
            for event in events:
                if event.id in seen:
                    continue
                seen.add(event.id)
                if not start <= event.recorded_at.astimezone(UTC).date() < end:
                    continue
                sitting = sittings.get(getattr(event, "consultation_id", None))
                if sitting is None or sitting.consultation_id not in reportable:
                    continue
                # A scientific sitting can continue across apps and upgrades.
                # Legacy events have no per-event context and retain their
                # original opening attribution rather than inventing metadata.
                context = event.provenance or sitting
                host = context.host if context.host in {"chatgpt", "claude"} else "unknown"
                surface = (
                    context.surface if context.surface in {"web", "desktop", "cli"} else "unknown"
                )
                try:
                    app_version = _APP_VERSION.validate_python(context.app_version)
                except SchemaError:
                    app_version = "unknown"
                role, role_version = reportable[sitting.consultation_id]
                key = (
                    role,
                    role_version,
                    host,
                    surface,
                    app_version,
                )
                row = groups.setdefault(
                    key,
                    {
                        "started": 0,
                        "concluded": 0,
                        "abandoned": 0,
                        "records": defaultdict(int),
                    },
                )
                if (
                    isinstance(event, ConsultationOpened)
                    and event.consultation_id not in seen_opens
                    and event.id == sitting.id
                ):
                    row["started"] += 1
                    seen_opens.add(event.consultation_id)
                elif (
                    isinstance(event, ConsultationClosed)
                    and event.consultation_id not in seen_closes
                ):
                    row["concluded" if event.state == "converged" else "abandoned"] += 1
                    seen_closes.add(event.consultation_id)
                elif type(event) in RECORD_EVENTS:
                    row["records"][RECORD_EVENTS[type(event)]] += 1
        errors = dict.fromkeys(FAILURE_CODES, 0)
        seen_errors = set()
        for event in self.journal.read(REPORTING_PROJECT):
            if (
                isinstance(event, UsageFailureRecorded)
                and event.id not in seen_errors
                and start <= event.recorded_at.astimezone(UTC).date() < end
            ):
                seen_errors.add(event.id)
                errors[event.code] += 1
        return UsagePayload(
            installation_id=installation_id,
            report_id=report_id,
            week=week,
            revision=revision,
            benchside_version=version,
            errors=errors,
            sessions=[
                UsageRow(
                    role=key[0],
                    role_version=key[1],
                    host=key[2],
                    surface=key[3],
                    app_version=key[4],
                    started=value["started"],
                    concluded=value["concluded"],
                    abandoned=value["abandoned"],
                    records=RecordCounts(**value["records"]),
                )
                for key, value in sorted(groups.items())
                if any(value[field] for field in ("started", "concluded", "abandoned"))
                or any(value["records"].values())
            ],
        )

    def send(
        self,
        *,
        channel: Channel,
        preview: ExportPreview,
        approved_sha256: str,
        sink: ExportSink,
        redactor: Redactor,
    ):
        from benchside.domain.export.service.export import ExportService

        grant = self.active_grant(channel)
        if not grant or grant != preview.grant_id:
            raise ConsentRequiredError("Reporting consent changed; review the submission again")
        digest = ExportService._digest(preview.payload)
        if digest != preview.payload_sha256 or digest != approved_sha256:
            raise ConsentRequiredError("The reviewed payload changed or has not been approved")
        if preview.destination != sink.destination:
            raise ConsentRequiredError("The destination changed; review the submission again")
        parsed = (
            parse_feedback(preview.payload)
            if channel == "feedback"
            else UsagePayload.model_validate_json(preview.payload)
        )
        if any(f.tier == "HIGH" for f in redactor.scan(preview.payload)):
            raise ValidationError("Sensitive content remains; edit and review before sending")
        identifier = parsed.feedback.id if channel == "feedback" else parsed.report_id
        for event in self.journal.read(CONSENT_LEDGER_PROJECT):
            if (
                isinstance(event, ReportSubmitted)
                and event.channel == channel
                and event.payload_sha256 == digest
                and event.destination == sink.destination
            ):
                return event
            if (
                isinstance(event, ReportSubmitted)
                and channel == "feedback"
                and event.channel == channel
                and event.submission_id == identifier
            ):
                raise ValidationError(
                    "That feedback has already been shared; record new feedback for a new submission"
                )
        receipt = sink.send(preview.payload)
        if receipt is None:
            raise ValidationError("Reporting requires a verified collector receipt")
        event = ReportSubmitted(
            id=new_event_id(),
            channel=channel,
            grant_id=grant,
            submission_id=identifier,
            payload_sha256=digest,
            destination=sink.destination,
            received_at=receipt.received_at,
        )
        self.journal.append(CONSENT_LEDGER_PROJECT, event)
        return event
