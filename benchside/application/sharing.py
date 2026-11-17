"""One review flow over three independently consented, separately stored channels."""

import json
import os
import uuid
from pathlib import Path
from typing import Literal

from pydantic import Field

from benchside import __version__
from benchside.application.contributions import ContributionPolicy, contributor_id
from benchside.application.submission_failures import record_submission_failure
from benchside.config import Paths
from benchside.domain.export.event.reporting import ReportSubmitted
from benchside.domain.export.model.reporting import (
    Demographics,
    Feedback,
    LinkedFeedbackPayload,
    ResearchProfile,
    StrictValue,
)
from benchside.domain.export.model.value import ExportPreview, Observation
from benchside.domain.export.service.consent import ConsentService
from benchside.domain.export.service.export import ExportService
from benchside.domain.export.service.reporting import ReportingService, week_start
from benchside.domain.shared.error import (
    BenchsideError,
    ConsentRequiredError,
    NotFoundError,
    ValidationError,
)
from benchside.domain.shared.model.ids import CONSENT_LEDGER_PROJECT, ProjectId
from benchside.infrastructure.files import atomic_json
from benchside.infrastructure.http_sink import COLLECTOR, HttpExportSink
from benchside.infrastructure.journal.projection import (
    JournalConsentRepository,
    JournalObservationReader,
)
from benchside.infrastructure.journal.store import JsonlJournal
from benchside.infrastructure.placeholders import RefusingExportSink
from benchside.infrastructure.redaction import TextRedactor


class SubmissionDraft(StrictValue):
    id: str = Field(pattern=r"^[a-f0-9]{32}$")
    channel: Literal["gaps", "feedback", "usage"]
    preview: ExportPreview
    demographics_revision: int | None = None


class ParticipationChoice(StrictValue):
    response: Literal["unasked", "declined", "deferred", "configured"] = "unasked"


class CombinedObservationReader(JournalObservationReader):
    def __init__(self, journal, paths):
        super().__init__(journal)
        self.paths = paths

    def list_all(self):
        from benchside.domain.export.model.metascience import MetaState

        found = super().list_all()
        path = self.paths.home / "metascience/state.json"
        if not path.exists():
            return found
        state = MetaState.model_validate_json(path.read_text())
        if "analysis" not in state.grants:
            return found
        for sample in state.samples.values():
            for token, problems in sample.problems.items():
                if sample.selected[token].scope not in state.scopes:
                    continue
                found.extend(
                    Observation(
                        id=problem.id,
                        project_id=ProjectId("reporting-ledger"),
                        gap=problem.gap,
                        origin="selected_conversation",
                        basis=problem.basis,
                    )
                    for problem in problems
                )
        return found


class SharingFlow:
    """Call under the installation transaction lock (CLI and app adapter do so)."""

    def __init__(self, paths: Paths, *, sinks=None):
        self.paths = paths
        self.journal = JsonlJournal(paths)
        self.reporting = ReportingService(journal=self.journal)
        self.ledger = JournalConsentRepository(self.journal)
        self.consent = ConsentService(repository=self.ledger, journal=self.journal)
        self.redactor = TextRedactor()
        self.sinks = sinks if sinks is not None else {}

    @property
    def export(self):
        service = self._export_service()
        service.contributor_id = contributor_id(self.paths) if self._policy_grant("gaps") else None
        return service

    def _export_service(self):
        """Validation/reads must not create a contributor identity."""
        service = ExportService(
            observations=CombinedObservationReader(self.journal, self.paths),
            consent=self.consent,
            redactor=self.redactor,
            sink=self._get_sink("gaps"),
            ledger=self.ledger,
            journal=self.journal,
        )
        return service

    def _get_sink(self, channel):
        # Optional collection configuration must not block private scientific work.
        # Re-resolve at each preview/send so a changed endpoint needs new approval.
        return self.sinks[channel] if channel in self.sinks else self._sink(channel)

    @staticmethod
    def _sink(channel):
        endpoint = os.environ.get(
            f"BENCHSIDE_{channel.upper()}_ENDPOINT", f"{COLLECTOR}/v1/{channel}"
        )
        return HttpExportSink(endpoint) if endpoint else RefusingExportSink()

    def profile(self):
        path = self.paths.home / "reporting/profile.json"
        return (
            ResearchProfile.model_validate_json(path.read_text())
            if path.exists()
            else ResearchProfile()
        )

    def contribution_policy(self):
        path = self.paths.home / "reporting/contributions.json"
        return (
            ContributionPolicy.model_validate_json(path.read_text())
            if path.exists()
            else ContributionPolicy()
        )

    def _policy_grant(self, channel):
        return self.contribution_policy().grants.get(channel)

    def _accept_policy(self, channel, grant):
        policy = self.contribution_policy()
        grants = dict(policy.grants)
        if grant:
            grants[channel] = grant
        else:
            grants.pop(channel, None)
        atomic_json(
            self.paths.home / "reporting/contributions.json",
            ContributionPolicy(grants=grants).model_dump(),
        )

    def participation(self):
        path = self.paths.home / "reporting/participation.json"
        return (
            ParticipationChoice.model_validate_json(path.read_text())
            if path.exists()
            else ParticipationChoice()
        )

    def set_participation(self, response):
        choice = ParticipationChoice(response=response)
        if choice.response == "unasked":
            raise ValidationError("Record a choice; do not reset an answered invitation")
        if choice.response in {"declined", "deferred"}:
            from benchside.domain.export.model.metascience import MetaState

            meta_path = self.paths.home / "metascience/state.json"
            grants = (
                MetaState.model_validate_json(meta_path.read_text()).grants
                if meta_path.exists()
                else {}
            )
            if any(
                self.status()[channel]["enabled"] for channel in ("gaps", "feedback", "usage")
            ) or any(key in grants for key in ("invitations", "analysis", "sharing")):
                raise ValidationError(
                    "Turn off active participation choices before declining or deferring"
                )
        atomic_json(
            self.paths.home / "reporting/participation.json", choice.model_dump(mode="json")
        )
        return choice.model_dump(mode="json")

    def set_profile(self, demographics, include_in_usage):
        previous = self.profile()
        profile = ResearchProfile(
            demographics=Demographics.model_validate(demographics),
            include_in_usage=include_in_usage,
            revision=previous.revision + 1,
        )
        atomic_json(self.paths.home / "reporting/profile.json", profile.model_dump(mode="json"))
        return profile.model_dump(mode="json")

    def status(self):
        grant = self.consent.active_grant()
        installation = self.paths.home / "reporting" / "installation.json"
        return {
            "gaps": {"enabled": bool(grant), "kinds": sorted(grant.gap_kinds) if grant else [], "scope": grant.scope if grant else None},
            "feedback": {"enabled": bool(self.reporting.active_grant("feedback"))},
            "usage": {"enabled": bool(self.reporting.active_grant("usage"))},
            "linking": "random_contributor_id",
            "needs_policy_renewal": [
                channel
                for channel, active in (
                    ("gaps", grant.id if grant else None),
                    ("feedback", self.reporting.active_grant("feedback")),
                    ("usage", self.reporting.active_grant("usage")),
                )
                if active and self._policy_grant(channel) != active
            ],
            "installation_id": json.loads(installation.read_text())["id"]
            if installation.exists()
            else None,
        }

    def set_consent(self, channel, enabled, *, kinds=None, scope="kinds"):
        if channel == "gaps":
            active = self.consent.active_grant()
            if not enabled:
                if active:
                    self.consent.revoke()
                self._accept_policy(channel, None)
                return
            if scope not in {"kinds", "all_workflow"} or (scope == "all_workflow" and kinds):
                raise ValidationError("Choose all_workflow scope or legacy kinds, not both")
            selected = frozenset(kinds or ())
            if active and active.scope == scope and active.gap_kinds == selected and self._policy_grant(channel) == active.id:
                return
            # Validate before revoking an existing grant.
            from benchside.domain.shared.model.gap import GAP_KINDS

            if scope == "kinds" and (not selected or not selected <= GAP_KINDS):
                raise ValidationError("Choose one or more valid workflow observation kinds")
            if active:
                self.consent.revoke()
            self.consent.grant(grant_id=f"g-{uuid.uuid4().hex}", gap_kinds=selected, scope=scope)
            self._accept_policy(channel, self.consent.active_grant().id)
        elif channel in {"feedback", "usage"}:
            if enabled and self.reporting.active_grant(channel) and not self._policy_grant(channel):
                self.reporting.set_consent(channel, False)
            self.reporting.set_consent(channel, enabled)
            self._accept_policy(channel, self.reporting.active_grant(channel))
        else:
            raise ValidationError("Unknown sharing channel")

    def feedback(self, **values):
        return self.reporting.record_feedback(Feedback(id=uuid.uuid4().hex, **values))

    def check_in(self, project_id, session_id):
        """Offer review at a host-chosen pause; never send or create consent.

        Remember an offer, including one the researcher declines, so reopening a
        chat doesn't repeat it. Only new pending material can produce a new offer.
        """
        from benchside.domain.shared.model.ids import user_project_id
        from benchside.infrastructure.session_context import validate_session_id

        project_id = user_project_id(project_id).root
        validate_session_id(session_id)
        project_path = self.paths.home / "app-projects" / f"{project_id}.json"
        session_path = self.paths.home / "app-sessions" / f"{session_id}.json"
        if not project_path.is_file() or not session_path.is_file():
            raise ValidationError("Select a Benchside project and session before checking in")
        if json.loads(session_path.read_text())["project_id"] != project_id:
            raise ValidationError("This session belongs to another project")
        grant = self.consent.active_grant()
        if grant is None or self._policy_grant("gaps") != grant.id:
            return {"offer": False}
        unshared = [o for o in self.export.observations.list_unshared()
                    if o.project_id.root == project_id]
        pending = {str(o.id) for o in unshared if grant.covers(o.gap)}
        if not pending:
            return {"offer": False}
        config = json.loads(project_path.read_text())
        previous = config.get("sharing_offer", {})
        if previous and "observation_ids" not in previous:
            # Old review builds retained only a whole-set digest. It cannot tell
            # which remaining items were declined after a partial submission.
            # Establish a conservative baseline once; explicit review still works.
            config["sharing_offer"] = {
                "observation_ids": sorted(pending), "session_id": previous["session_id"]
            }
            atomic_json(project_path, config)
            return {"offer": False}
        offered = set(previous.get("observation_ids", [])) & {str(o.id) for o in unshared}
        new = sorted(pending - offered)
        if not new or previous.get("session_id") == session_id:
            return {"offer": False}
        config["sharing_offer"] = {
            "observation_ids": sorted(offered | pending), "session_id": session_id
        }
        atomic_json(project_path, config)
        return {"offer": True, "channel": "gaps", "pending": len(new), "observation_ids": new}

    def prepare(self, channel, *, only=None, edits=None, feedback_id=None, comment=None,
                week=None, replace_draft_ids=None, project_id=None):
        grant = self.consent.active_grant() if channel == "gaps" else None
        active = grant.id if grant else self.reporting.active_grant(channel)
        if active and self._policy_grant(channel) != active:
            raise ConsentRequiredError(
                "Sharing now includes a random contributor ID linking contributions over time. "
                "Explain this change and renew this sharing choice before preparing a new submission."
            )
        if channel == "gaps":
            owners = self._observation_projects()
            if project_id is not None:
                selected = {identifier for identifier, owner in owners.items() if owner == project_id}
                if only is not None and set(only) - selected:
                    raise ValidationError("Selected observations must belong to this Benchside project")
                if only is None:
                    only = [str(o.id) for o in self.export.observations.list_unshared()
                            if str(o.id) in selected]
            previews = self.export.previews(only=only, edits=edits)
            if not any(preview.observation_ids for preview in previews):
                reasons = [reason for preview in previews for reason in preview.redaction_findings]
                raise ValidationError("No selected, unshared workflow observations to preview"
                                      + ("; " + "; ".join(reasons) if reasons else ""))
        else:
            if channel not in {"feedback", "usage"}:
                raise ValidationError("Unknown sharing channel")
            grant = self.reporting.active_grant(channel)
            if not grant:
                raise ConsentRequiredError(
                    f"{channel.title()} reporting is off; nothing was shared"
                )
            sink = self._get_sink(channel)
            if channel == "feedback":
                payload = self.reporting.feedback_payload(feedback_id, __version__)
                if comment is not None:
                    from benchside.domain.export.model.reporting import FeedbackPayload

                    data = json.loads(payload)
                    data["feedback"]["comment"] = comment
                    payload = FeedbackPayload.model_validate(data).model_dump_json(by_alias=True)
                data = json.loads(payload)
                payload = LinkedFeedbackPayload(
                    benchside_version=data["benchside_version"],
                    feedback=data["feedback"],
                    contributor_id=contributor_id(self.paths),
                ).model_dump_json(by_alias=True)
            else:
                payload = self._usage(week or week_start())
            payload = self.redactor.apply(payload)
            previews = (
                ExportPreview(
                    payload=payload,
                    observation_ids=(),
                    grant_id=grant,
                    payload_sha256=ExportService._digest(payload),
                    destination=sink.destination,
                    redaction_findings=tuple(
                        f"{f.tier}:{f.category} in {f.field}" for f in self.redactor.scan(payload)
                    ),
                ),
            )
        existing = [
            SubmissionDraft.model_validate_json(path.read_text())
            for path in (self.paths.home / "sharing/drafts").glob("*.json")
        ]
        drafts = []
        for preview in previews:
            profile_revision = self.profile().revision if channel == "usage" else None
            draft = next(
                (
                    old
                    for old in existing
                    if old.channel == channel
                    and old.preview == preview
                    and old.demographics_revision == profile_revision
                ),
                None,
            )
            if draft is None:
                draft = SubmissionDraft(
                    id=uuid.uuid4().hex,
                    channel=channel,
                    preview=preview,
                    demographics_revision=profile_revision,
                )
            drafts.append(draft)
        retained = {draft.id for draft in drafts}
        if channel == "gaps":
            projects = {project_id} if project_id is not None else {
                owners.get(str(identifier)) for preview in previews for identifier in preview.observation_ids
            }
            pending = set()
            for item in self.drafts(channel="gaps"):
                draft_projects = {owners.get(identifier) for identifier in item["preview"]["observation_ids"]}
                if not projects.intersection(draft_projects):
                    continue
                if draft_projects - projects:
                    raise ValidationError(
                        "An older combined report includes this project and other projects. "
                        "Keep it unchanged; explicitly request an all-project review to resume it.",
                        code="cross_project_draft",
                    )
                pending.add(item["id"])
            replacing = pending - retained
            if replacing and set(replace_draft_ids or ()) != replacing:
                raise ValidationError(
                    "A pending workflow report would be replaced. Read sharing.drafts "
                    "(CLI: bench share drafts) for this project; "
                    "ask whether to keep, send, combine or replace it, then pass the exact "
                    "replace_draft_ids only for an agreed replacement.",
                    code="pending_draft_exists",
                )
            if replace_draft_ids and set(replace_draft_ids) != replacing:
                raise ValidationError("Pending reports changed; read sharing.drafts again")
        for draft in drafts:
            atomic_json(self._draft_path(draft.id), draft.model_dump(mode="json"))
        # One workflow review per project. Save the whole replacement batch first;
        # keep other channels, original observations/feedback and receipt ledgers.
        # Identical previews reuse their ID so failed-send retries keep exact bytes.
        for old in existing:
            if old.channel == channel and old.id not in retained and (
                channel != "gaps" or old.id in replacing
            ):
                self._draft_path(old.id).unlink()
        return drafts

    def _usage(self, week):
        directory = self.paths.home / "reporting"
        identity = contributor_id(self.paths)
        # Validate the week before using it as a filename.
        from datetime import date

        parsed_week = date.fromisoformat(week)
        if parsed_week.isoformat() != week or parsed_week.weekday() != 0:
            raise ValidationError("Choose a Monday in YYYY-MM-DD form")
        path = directory / f"usage-{week}.json"
        previous = json.loads(path.read_text()) if path.exists() else None
        payload = self.reporting.usage_payload(
            installation_id=identity,
            report_id=previous["report_id"] if previous else uuid.uuid4().hex,
            week=week,
            revision=previous["revision"] if previous else 1,
            version=__version__,
        ).model_dump(mode="json", by_alias=True, exclude_none=True)
        profile = self.profile()
        demographics = profile.demographics.model_dump(mode="json", exclude_none=True)
        if profile.include_in_usage and demographics:
            payload["demographics"] = demographics
        if previous and payload != previous:
            payload["revision"] += 1
        atomic_json(path, payload)
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def _draft_path(self, identifier: str) -> Path:
        import re

        if not re.fullmatch(r"[a-f0-9]{32}", identifier):
            raise ValidationError("Invalid draft identifier")
        return self.paths.home / "sharing" / "drafts" / f"{identifier}.json"

    def load(self, identifier):
        path = self._draft_path(identifier)
        if not path.exists():
            raise NotFoundError(
                "Submission draft was not found or was superseded by a newer preview; "
                "prepare and review the current preview"
            )
        return SubmissionDraft.model_validate_json(path.read_text())

    def _observation_projects(self):
        return {str(o.id): o.project_id.root for o in self._export_service().observations.list_all()}

    def drafts(self, *, channel=None, project_id=None):
        """List exact pending reports and current eligibility, without writes or sends."""
        if channel is not None and channel not in {"gaps", "feedback", "usage"}:
            raise ValidationError("Unknown sharing channel")
        received = {(r["channel"], r["payload_sha256"], r["destination"])
                    for r in self.history()}
        owners = self._observation_projects() if project_id is not None else {}
        result = []
        for path in sorted((self.paths.home / "sharing/drafts").glob("*.json")):
            draft = SubmissionDraft.model_validate_json(path.read_text())
            if channel is not None and draft.channel != channel:
                continue
            if project_id is not None and draft.channel == "gaps" and (
                not draft.preview.observation_ids
                or {owners.get(str(i)) for i in draft.preview.observation_ids} != {project_id}
            ):
                continue
            if (draft.channel, draft.preview.payload_sha256, draft.preview.destination) in received:
                continue
            problems = []
            try:
                self._check_draft(draft, draft.preview.payload_sha256)
            except BenchsideError as error:
                problems.append({"code": error.code, "message": error.message})
            except (ValueError, TypeError, KeyError):
                problems.append({"code": "submission_invalid",
                                 "message": "Stored report is invalid; preserve it and review before sending"})
            result.append({**draft.model_dump(mode="json"), "sendable": not problems,
                           "problems": problems})
        return result

    def _check_draft(self, draft, approved_sha256):
        """Shared readiness/send checks. This method never records or transmits."""
        if draft.channel == "gaps":
            active = self.consent.active_grant()
            grant = active.id if active else None
        else:
            grant = self.reporting.active_grant(draft.channel)
        if not grant or grant != draft.preview.grant_id:
            raise ConsentRequiredError("Sharing consent changed; review the submission again")
        if self._policy_grant(draft.channel) != grant:
            raise ConsentRequiredError("Sharing policy changed; renew this choice and review again")
        sink = self._get_sink(draft.channel)
        digest = ExportService._digest(draft.preview.payload)
        if (digest != draft.preview.payload_sha256 or digest != approved_sha256
            or draft.preview.destination != sink.destination):
            raise ValidationError(
                "Approve the exact payload and destination in the current preview",
                code="submission_invalid",
            )
        if draft.channel == "gaps":
            self._export_service().check_preview(
                preview=draft.preview, approved_sha256=approved_sha256,
            )
        else:
            if draft.channel == "usage":
                from benchside.domain.export.model.reporting import UsagePayload

                data = UsagePayload.model_validate_json(draft.preview.payload).model_dump()
                if (draft.demographics_revision or 0) != self.profile().revision:
                    raise ConsentRequiredError(
                        "Demographic preferences changed; review a new usage preview"
                    )
                current = self.paths.home / "reporting" / f"usage-{data['week']}.json"
                if current.exists() and json.loads(current.read_text())["revision"] > data["revision"]:
                    raise ValidationError("A newer usage snapshot exists; review that version")
            self.reporting.check_preview(
                channel=draft.channel, preview=draft.preview, approved_sha256=approved_sha256,
                sink=sink, redactor=self.redactor,
            )
        return sink

    def send(self, identifier, approved_sha256):
        try:
            draft = self.load(identifier)
            sink = self._check_draft(draft, approved_sha256)
            if draft.channel == "gaps":
                return self.export.export(
                    preview=draft.preview,
                    approved_sha256=approved_sha256,
                )
            return self.reporting.send(
                channel=draft.channel,
                preview=draft.preview,
                approved_sha256=approved_sha256,
                sink=sink,
                redactor=self.redactor,
            )
        except Exception as err:
            record_submission_failure(self.paths, err)
            raise

    def history(self):
        entries = [
            {"channel": "gaps", **r.model_dump(mode="json")} for r in self.ledger.load().exports
        ]
        entries += [
            e.model_dump(mode="json")
            for e in self.journal.read(CONSENT_LEDGER_PROJECT)
            if isinstance(e, ReportSubmitted)
        ]
        return entries
