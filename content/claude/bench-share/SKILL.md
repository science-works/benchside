---
name: bench-share
description: Review optional Benchside workflow observations, usability feedback and usage counts, control each consent choice, and send only explicitly approved drafts. Use when the researcher wants to share or review sharing preferences.
---

# Optional Benchside sharing

Use `bench share status` to read existing choices. Offer workflow observations,
usability feedback and weekly usage counts together, each optional. Private
scientific records and source documents are never part of these submissions.

After the researcher chooses, enable only those channels with
`bench share grant --channel gaps|feedback|usage`. Gaps also need `--kinds`
with their chosen kinds (missing_tool, unfindable_data, manual_toil, dead_end,
missing_index, workflow_problem). `workflow_problem` covers broad scientific
workflow obstacles, including equipment, materials, coordination and software/data.
Enable it only if the researcher chooses it; do not expand an older grant automatically.
Disable choices with `bench share revoke --channel <channel>`;
`--channel all` stops all future reporting. Revocation does not delete past submissions.

For feedback, ask for ease of use (1–5), whether they would use it again
(yes/no/unsure), and an optional comment. Save using `bench share feedback --ease
<rating> --again <answer> --comment "<their text>"`, with `--role`, `--host` and
`--surface` if known. Never invent ratings.

Use `bench share preview --channel <channel>`; feedback also needs
`--feedback-id <returned ID>`. Gaps can select `--only <observation ID>` repeatedly
and use `--edits <JSON file>` mapping selected IDs to complete reviewed gap objects.
Feedback previews can use `--comment "<reviewed replacement>"`.

Workflow previews and `bench share drafts` default to the current project. Use
`--project <project ID>` to select another project, or `--all-projects` only for
an explicitly requested review across projects. The preview includes only
consented items and lists withheld IDs locally; withheld content is not sent.
New withheld items alone refresh that local list without replacing an otherwise
identical pending report.

Use `bench share drafts` to redisplay the exact pending payload, destination,
digest and current send readiness. If a new preview would replace a pending
report, ask whether to keep, send, combine or replace it. Only after agreement,
run `bench share preview --replace-draft <id>`; repeat `--replace-draft` for each
draft being replaced, with `--only`/`--edits` if needed. Replacement is not approval
to send. Other projects' reports must remain unchanged.

An older combined-project draft's refusal names its draft ID without showing
another project's content. If its original consent has been revoked or superseded,
use that ID for an agreed replacement while preparing a report for one project;
no all-project payload review is required just to find the ID. Explain that the
old combined preview is being retired; the original observations in every project
remain private and can be reviewed separately. A combined draft with current
consent stays protected. Use `bench share drafts --all-projects` only if the
researcher explicitly requests to view or resume the combined report.

Show the complete prepared content, recipient and any redaction findings.
Usage includes a random installation ID, weekly counts, role/app/version
information and standard failure counts, with no research text. Installation
counts are not exact people. New feedback and workflow observations share that random contributor ID so
Science Works can group contributions over time. Explain this before consent;
old unlinked grants need a renewed choice. It identifies a store, not a person.
Public software/dataset names and versions can explain a problem, but private
scientific findings and source passages must be removed from model-derived gaps.

After the researcher explicitly approves a displayed batch, send that exact
batch with `bench share send --draft <returned draft ID> --approve-sha256
<displayed digest>`. Any edits need a new preview and approval. Retry an uncertain
send with the same draft. No automatic retries, broad approvals, or unattended
uploads. Each batch needs review.

`bench share history` returns receipts for review and operator-assisted removal.
Never claim a send succeeded unless the command confirms a verified receipt.
