# Researcher-run OpenCode check — 6 November 2026

Evidence: a researcher-supplied OpenCode JSON conversation export, inspected
locally. The transcript, scientific content, local paths and contributor IDs are
not included in this repository. This is one observed run, not a guarantee about
every model or account.

## What the export establishes

- The recorded model is `glm-5.3-flash-free`, provider `opencode`, rather than
  OpenRouter. The export's name does not establish where model inference ran;
  this demonstrates a local agent/tool environment, not an on-device model.
- The agent installed the public **0.3.1** tag into a fresh directory, installed
  the generic skill, ran its version check, configured local storage and saved
  and read back a synthetic setup decision. Fresh-chat restore was suggested
  but is not demonstrated by this export.
- The substantive consultation used **study-design**, not the newly broadened
  0.4.0 PI. It saved a role output and a decision.
- The researcher was shown two proposed gap reports and explicitly selected
  approval to send both. `sharing.send` returned success, both observation IDs,
  the approved payload digest and a matching receipt timestamp from
  `https://ingest.benchside.science.works/v1/gaps` at **10:17:52 UTC**.
- The authorised GitHub reporting workflow subsequently read Cloudflare R2
  and produced its private analysis artifact. Both expected observation
  references were present, and their gap descriptions exactly matched the
  approved preview. This independently verifies two observations through the
  collector, storage and reporting pipeline; the report remains internal.
  Feedback, usage, survey and activity submissions were not established by
  this run.

## Findings to carry into testing

- Setup involved several repeated choices. Version 0.4.0 defers conversation
  sources and supporting activity labels and supports multiple disciplines;
  that newer setup still needs a comparable researcher-run check.
- Two gap-recording commands initially contained malformed JSON. The runtime
  rejected them, then accepted the corrected commands. The preview failed while
  no gaps existed; the successful send followed the corrected preview and
  researcher approval. No new retry was made during this review.
- One proposed gap claimed accessible tools could not handle the task without
  an observed attempt or supporting tool lookup in the export. Another described
  anticipated manual work. Delivery success does not establish those claims as
  measured user friction. Shared guidance now explicitly distinguishes observed
  problems, researcher reports, planned work and assistant access limits.
- Scientific advice quality was not independently validated by the receipt or
  code tests. Test reasoning, quantitative assumptions and calibrated claims
  separately during the deeper role evaluation.

No scientific content was changed, resubmitted or newly published during this
review. Do not mark this run synthetic merely because it was used to test the app;
the synthetic setup project and substantive discussion are different.
