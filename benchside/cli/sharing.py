"""Human and agent surfaces for the same three-channel sharing flow."""

import json
from pathlib import Path

from benchside.application.sharing import SharingFlow
from benchside.cli.runtime import current_paths
from benchside.domain.shared.error import ConsentRequiredError


def cmd_sharing(args):
    flow = SharingFlow(current_paths())
    channel = getattr(args, "channel", "gaps")
    if args.action == "status":
        print(json.dumps(flow.status(), indent=2))
    elif args.action == "grant":
        kinds = [k.strip() for k in (args.kinds or "").split(",") if k.strip()]
        flow.set_consent(channel, True, kinds=kinds)
        args.ui.success(f"{channel} consent enabled; review a submission before sending")
    elif args.action == "revoke":
        channels = ("gaps", "feedback", "usage") if channel == "all" else (channel,)
        for name in channels:
            flow.set_consent(name, False)
        args.ui.success(
            f"{channel} reporting stopped; previous submissions are listed in share history"
        )
    elif args.action == "feedback":
        feedback = flow.feedback(
            role=args.role,
            host=args.host,
            surface=args.surface,
            ease=args.ease,
            would_use_again=args.again,
            comment=args.comment,
        )
        print(feedback.model_dump_json())
        args.ui.info("Feedback saved locally; preview and approve it to share")
    elif args.action == "preview":
        edits = json.loads(Path(args.edits).read_text()) if args.edits else None
        drafts = flow.prepare(
            channel,
            only=args.only,
            edits=edits,
            feedback_id=args.feedback_id,
            comment=args.comment,
            week=args.week,
        )
        for draft in drafts:
            print(draft.preview.payload)
            args.ui.info(f"Review {draft.channel} draft {draft.id}")
            args.ui.detail(f"Destination: {draft.preview.destination}")
            args.ui.detail(f"Approval digest: {draft.preview.payload_sha256}")
            for finding in draft.preview.redaction_findings:
                args.ui.warn(finding)
        args.ui.warn("Redaction cannot detect all private research details. Review the full text.")
    elif args.action == "send":
        if not args.draft or not args.approve_sha256:
            raise ConsentRequiredError(
                "Consent, a reviewed draft and its approval digest are required; nothing was shared"
            )
        receipt = flow.send(args.draft, args.approve_sha256)
        print(receipt.model_dump_json())
        args.ui.success("Submission receipt verified")
    elif args.action == "history":
        print(json.dumps(flow.history(), indent=2))
    return 0
