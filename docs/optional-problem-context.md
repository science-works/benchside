# Optional problem context (Benchside 0.3.0)

Gap records can carry an optional context object with public tool/dataset names,
versions actually used, workflow area, frequency, impact, workaround and desired
improvement. Missing fields are fine. The assistant captures what is already in
the conversation and may ask one useful follow-up at a natural pause.

Context stays inside the exact reviewed gap payload. Existing consent, redaction,
preview, approval, receipt and retry controls apply. It never permits scientific
findings, private dataset identifiers or project-specific research details.

The client emits benchside.gaps.v3 only when context is present. Legacy v1/v2
payloads retain their format. The receiver independently allowlists every context
field, applies the same 2000 UTF-16 character limit and stores the exact bytes.
Reporting preserves context in its private analysis bundle; public reports still
contain aggregate counts only. The updated reporting PR preserves each complete
observation separately, including its wording, context and evidence basis. It
deduplicates retries, but does not merge independent matching descriptions.
Thematic grouping through an LLM remains a later analysis step.

Native notebooks containing these new records or pending drafts use
benchside.native.v3. Older clients refuse these notebooks and request an update,
rather than silently dropping context. Update every app sharing such a notebook.
The new reader continues to accept v1/v2 notebooks, including replay checkpoints.
This schema change does not fix the known Claude exact-transfer limitation.

Validation: 473 client tests passed; 71 receiver tests and TypeScript checks
passed. Hosted reporting and live receipt evidence are recorded in the demo
report after the end-to-end rehearsal. No PR is merged by this update.
