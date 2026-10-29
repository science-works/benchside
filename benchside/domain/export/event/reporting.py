from benchside.domain.export.model.reporting import Channel, FailureCode, Feedback
from benchside.domain.shared.event import Event


class ReportingConsentChanged(Event):
    channel: Channel
    enabled: bool


class FeedbackRecorded(Event):
    feedback: Feedback


class UsageFailureRecorded(Event):
    code: FailureCode


class ReportSubmitted(Event):
    channel: Channel
    grant_id: str
    submission_id: str
    payload_sha256: str
    destination: str
    received_at: str
