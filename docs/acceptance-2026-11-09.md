# Release verification — 9 November 2026

Benchside **0.4.2** is published on [GitHub](https://github.com/science-works/benchside/releases/tag/v0.4.2)
and [PyPI](https://pypi.org/project/benchside/0.4.2/). This report separates release,
deployment and reporting checks from the remaining installed-app acceptance.

## Reviewed fixes and release

- [Client PR #15](https://github.com/science-works/benchside/pull/15) merged as
  `d7528dbe53fec43f883de26c3750250552b79b97`. The tag has the same tree as the
  reviewed PR head. An independent review found Markdown punctuation around
  URLs was being treated as part of the link; regression tests reproduced it,
  and the corrected extraction passed re-review.
- **610 client tests passed**, including exact public-link confirmation,
  unchanged answer text, sensitive-text refusal, consent withdrawal, duplicate
  receipt handling and invalid answers. Release CI passed on Python 3.11 and 3.14.
- All three plugin/skill archives passed extracted-runtime checks across all
  eight roles: local and native snapshot save/restore, readable ODT/Markdown
  records, offline bootstrap, damaged dependency refusal and consent replay.
  Native storage in these package tests is simulated.
- [Trusted publishing completed](https://github.com/science-works/benchside/actions/runs/42611642629).
  A fresh installation of `benchside==0.4.2` from public PyPI passed the
  distribution smoke check: CLI, eight-role generic setup, private save/restore,
  readable records and sharing-off defaults. It sent no submissions.
- Public PyPI wheel and source archive SHA-256 values exactly match the GitHub
  release assets. Wheel: `b27a19756bf25021401d70de175955345a495a9f268bccdadcf2ed6c12b81dad`.

## Receiver and reporting

- [Receiver PR #3](https://github.com/science-works/benchside-ingest/pull/3)
  merged and deployed to the existing production Worker and storage bindings.
  Worker version: `982b42f6-b9c6-418a-af24-8876fd4f5555`.
- Type checking and **78 receiver tests passed**. The blank-answer regressions
  exercise HTTP rejection and verify that no object is stored, including Unicode
  whitespace cases.
- The live study catalog returned HTTP 200 with no active studies. Malformed
  synthetic submissions were refused with HTTP 422. The live blank-survey probe
  was refused at the unavailable-study check; it did **not** exercise the later
  blank-answer branch. No live study was created for that probe.
- A manual run of the ordinary incremental import
  [completed successfully](https://github.com/LauraRyanSW/tools-science-works/actions/runs/42612227907):
  18 listed objects, 17 excluded test objects, one accepted object, zero newly
  downloaded objects and three reused checkpoint objects. These are storage
  object counts, not researcher or gap counts. This verifies access and checkpoint
  reuse; it does not establish receipt of a new 0.4.2 app submission.
- The daily import remains scheduled. Private full gap records and aggregate
  outputs remain separate. Registered synthetic markers stay excluded from
  research reporting. No Vercel view or LLM grouping was added in this patch.

## Installed apps — still pending

The existing private ChatGPT plugin was updated to 0.4.2 and its stored package
metadata and bundled wheel hash were verified. Claude accepted a replacement
plugin upload; its final installed version and execution still need confirmation.

The final live sequence remains: PI discussion without requiring a hypothesis,
private saved decision and open question, restoration in a fresh chat, then an
explicitly reviewed synthetic gap submission with a verified receipt. Browser
control currently cannot reliably enter or send the test prompt. These checks
must not be counted as passed from package tests or earlier release results.

No real researcher notebooks were changed and no new synthetic gap submission
was sent during this verification so far. Test notebooks and submissions, when
created, must be clearly synthetic and use a registered reporting exclusion.
