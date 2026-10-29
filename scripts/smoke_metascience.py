"""Synthetic HTTP integration check; refuses every non-loopback destination.

Run against an isolated local Worker with the synthetic fixture catalog. Never
publish that catalog to staging/production just to run this development check.
"""

import argparse
import json
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

from benchside.application.metascience import Metascience, StudyClient
from benchside.application.sharing import SharingFlow
from benchside.config import Paths
from benchside.domain.shared.error import BenchsideError, InfrastructureError
from benchside.infrastructure.http_sink import HttpExportSink


def smoke(endpoint):
    url = urlsplit(endpoint)
    if (
        url.scheme != "http"
        or url.hostname not in {"localhost", "127.0.0.1", "::1"}
        or url.username
        or url.password
        or url.query
        or url.fragment
        or url.path not in {"", "/"}
    ):
        raise ValueError("This synthetic check only permits a local loopback Worker")
    endpoint = endpoint.rstrip("/")
    with tempfile.TemporaryDirectory(prefix="benchside-meta-review-") as temporary:
        root = Path(temporary)
        flow = Metascience(
            Paths(home=root / "private", repo_root=root),
            catalog=StudyClient(f"{endpoint}/v1/studies", allow_local=True),
            sinks={
                c: HttpExportSink(f"{endpoint}/v1/{c}", allow_local=True)
                for c in ("surveys", "activity")
            },
        )
        flow.consent("invitations", True)
        offered = flow.invitations()
        invitation = offered["invitation"]
        assert invitation and invitation["id"] == "synthetic-verification", (
            "Use the isolated synthetic catalog"
        )
        flow.join_study("synthetic-verification@1", offered["study_sha256"])
        text_answer = "Synthetic test only: Fiji channel labels need manual restoration."
        survey = flow.survey("synthetic-verification@1", {
            "checked": "yes", "comment": {"text": text_answer}
        })
        assert json.loads(survey["payload"])["answers"]["comment"]["text"] == text_answer
        survey_receipt = flow.send(survey["id"], survey["sha256"])
        assert survey_receipt["status"] == "stored"
        assert flow.sinks["surveys"].send(survey["payload"]).status == "duplicate"
        flow.consent("analysis", True)
        scope = {"host": "claude", "source_id": "synthetic-project"}
        flow.scopes([scope])
        sample = flow.sample([{"scope": scope, "session_ref": f"synthetic-{i}"} for i in range(21)])
        assert len(sample["selected"]) == 20, "The automatic sample must respect the 20-session cap"
        for token in sample["selected"]:
            flow.record(
                sample["week"],
                token,
                {
                    "benchside_role": "none",
                    "activity": {"value": "analysis", "basis": "model_inferred"},
                    "obstacle": {"value": "unknown", "basis": "unknown"},
                    "verification": {"value": "none_visible", "basis": "model_inferred"},
                    "outcome": {"value": "not_reported", "basis": "unknown"},
                },
            )
        token = next(iter(sample["selected"]))
        gap = flow.record_gap(sample["week"], token,
                              {"kind": "manual_toil", "task": text_answer,
                               "frequency": "Synthetic only"}, "researcher_reported")
        sharing = SharingFlow(flow.paths, sinks={
            "gaps": HttpExportSink(f"{endpoint}/v1/gaps", allow_local=True)
        })
        sharing.set_consent("gaps", True, kinds=["manual_toil"])
        gap_draft = sharing.prepare("gaps")[0]
        gap_payload = json.loads(gap_draft.preview.payload)
        assert gap_payload["observations"][0]["id"] == gap["recorded"]
        assert gap_payload["observations"][0]["origin"] == "selected_conversation"
        sharing.send(gap_draft.id, gap_draft.preview.payload_sha256)
        assert sharing.sinks["gaps"].send(gap_draft.preview.payload).status == "duplicate"
        flow.consent("sharing", True)
        activity = flow.preview_activity(sample["week"])
        activity_receipt = flow.send(activity["id"], activity["sha256"])
        assert activity_receipt["status"] == "stored" and activity_receipt["observations"] == 20
        assert flow.sinks["activity"].send(activity["payload"]).status == "duplicate"
        invalid = json.loads(activity["payload"])
        invalid["transcript"] = "Synthetic forbidden field"
        try:
            flow.sinks["activity"].send(json.dumps(invalid))
        except InfrastructureError as error:
            assert error.code == "submission_rejected" and "422" in str(error)
        else:
            raise AssertionError("Collector accepted forbidden text")
        flow.consent("sharing", False)
        try:
            flow.send(activity["id"], activity["sha256"])
        except BenchsideError:
            pass
        else:
            raise AssertionError("Revocation did not block submission")
        identity = json.loads((flow.path.parent.parent / "reporting/installation.json").read_text())
        assert identity["id"] == gap_payload["contributor_id"]
        assert identity["id"] == json.loads(survey["payload"])["contributor_id"]
        assert identity["id"] == json.loads(activity["payload"])["contributor_id"]
        print(
            json.dumps(
                {
                    "catalog": "synthetic invitation retrieved",
                    "surveys": "agreed before answering; exact free text stored; retry verified",
                    "selected_conversation_gap": "reviewed v2 gap stored; retry verified",
                    "pseudonymous_linkage": "same store ID across the three opted-in channels",
                    "activity": "20 selected sessions stored; duplicate retry verified",
                    "forbidden_transcript": "HTTP 422",
                    "revoked_sharing": "blocked before HTTP",
                    "production_requests": 0,
                },
                indent=2,
            )
        )

        return {"surveys": survey["payload"], "activity": activity["payload"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://127.0.0.1:8880")
    smoke(parser.parse_args().endpoint)
