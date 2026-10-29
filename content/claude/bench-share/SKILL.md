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
missing_index). Disable choices with `bench share revoke --channel <channel>`;
`--channel all` stops all future reporting. Revocation does not delete past submissions.

For feedback, ask for ease of use (1–5), whether they would use it again
(yes/no/unsure), and an optional comment. Save using `bench share feedback --ease
<rating> --again <answer> --comment "<their text>"`, with `--role`, `--host` and
`--surface` if known. Never invent ratings.

Use `bench share preview --channel <channel>`; feedback also needs
`--feedback-id <returned ID>`. Gaps can select `--only <observation ID>` repeatedly
and use `--edits <JSON file>` mapping selected IDs to complete reviewed gap objects.
Feedback previews can use `--comment "<reviewed replacement>"`.

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
