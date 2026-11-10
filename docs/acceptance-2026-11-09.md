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

## Installed apps

The existing private ChatGPT plugin was updated to 0.4.2 and its stored package
metadata and bundled wheel hash were verified. Claude accepted a replacement
plugin upload and its settings show the installed, enabled Benchside 0.4.2.

**ChatGPT Work, synthetic PI project.** The installed plugin reported runtime
0.4.2, accepted a study without an initial hypothesis, and asked what the
researcher wanted the repeated images to reveal about the paired treatments.
It reported a verified save at revision 1 with participation off. In a separate
read, the stored personal Page had no direct or inherited shares. The published
0.4.2 runtime validated that Page's snapshot in a new process and recovered the
project and its actual open question. The stored settings had all participation
off, no installation ID and no demographics. This is independent evidence of persistence;
it does not stand in for a second ChatGPT conversation restoring the Page.

**Claude web, synthetic PI project.** Claude ran 0.4.2, saved a decision and
an unresolved question in a separate notebook, and returned a readable journal.
The agent reported checking the hash, using a revision guard, exporting the
result and confirming Benchside revision 1 by readback (Claude Doc revision 3).
It kept all five participation choices off and left the hypothesis unset.
The notebook card in Claude showed **Only you**; Claude Docs did not expose a
collaborator roster to the agent.

In a fresh Claude chat, the only pointer supplied for recall was the saved
notebook link. Claude recovered the exact PI decision and open question, the
revision and the initial sharing settings. The test then opted into the manual
toil category for that synthetic notebook only. Claude saved a fictional
DemoScope export problem at revision 2 and a pending preview at revision 3.
The approved preview contained only the fictional software problem, version,
frequency, impact and generated IDs. Its primary task began with a registered
test marker; the normal importer's marker check classified the whole batch as
synthetic. The digest computed from the displayed payload matched the approval
digest. No notebook decisions, questions or project names appeared in it.

One reporting detail for follow-up: the preview used `basis: unknown` for this
explicitly reported problem; the analysis must not count it as a report
explicitly attributed to the researcher on that field alone.

**Production send and import.** After approval of the exact preview, Claude
received a matching receipt for one observation at 13:21:23 UTC (digest
`9cb0f95f…8504282`). Claude saved the receipt at notebook revision 4, switched
workflow sharing off at revision 5 and confirmed both saves by readback. No
network settings were changed. The [next incremental import](https://github.com/LauraRyanSW/tools-science-works/actions/runs/42625110688)
downloaded one new object. Against the baseline above, listed objects increased
from 18 to 19 and excluded test objects from 17 to 18; accepted research objects
remained at one. The importer validates downloaded bytes against their storage
digest. Its audit exposes counts, not individual keys. A separate attempt to
download that exact object with the local Worker deployment login returned 403:
that login has no R2 object-read scope. No broader permissions were requested.

**Remaining ChatGPT-specific check.** The web composer showed **Send** disabled
for a follow-up and for the read-only recall prompt in a new Work chat. Neither
prompt was submitted at the time of this check. The first save, independent
readback and local runtime recall passed; fresh-chat recall and an approved send
from ChatGPT itself remain unverified. No real researcher notebooks were changed.
