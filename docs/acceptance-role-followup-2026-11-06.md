# Role-quality follow-up — 6 November 2026

This review branch implements the small changes proposed in the
[0.4.0 evaluation](acceptance-role-evaluation-2026-11-06.md). The package version
is **0.4.1**, prepared for review, not published by this change. The public
release links remain on 0.4.0 until a separate release is approved.

## What changed

- All roles check the distinction between supplied evidence, inference and
  proposals before saving. Scientific uncertainty must survive into the journal.
- Corrections use the existing append-only `record` action: name the earlier
  record ID, mistaken claim, replacement and reason. Recall checks later
  corrections. No new event schema or automatic supersession is claimed.
- Decisions preserve researcher wording separately from rationale. Advice is
  not agreement; the generated decision-recording step now explicitly waits for
  the researcher to choose. Unknown answers remain open questions.
- The hypothesis reviewer challenges reasoning respectfully and distinguishes
  probabilistic predictions from universal claims. The shared generator's old
  accusation of “dodging” was also removed for every role.
- Role-specific guidance addresses control coverage, small-sample assumptions,
  unknown effect scales, recruitment versus allocation, source provenance and
  proportionate peer review. Named reporting taxonomy labels require verification.
- Shared setup examples use neutral host metadata. A Claude-named ZIP does not
  make OpenCode a Claude session. Skipping demographics has an executable JSON
  example; confirmation should be brief and use ordinary language.
- Shared and legacy instructions, generated role references, wheel and all three
  package formats were rebuilt together. No collector, consent or private-storage
  format changed.

## Automated and independent checks

- **540 tests passed** on Python 3.14; Ruff and `bench compile --check` passed.
- New checks execute the documented correction example through local and native
  adapters, replay it beyond the five-record recent window, retain the original,
  and verify both ODT/Markdown or native journal output. They also exercise the
  demographics-skip example and guard both generated instruction formats against
  the old accusatory wording and unconditional decision-recording step.
- Package smoke checks exercise all eight roles, fresh-process local/native
  restore, readable copies, offline dependency bootstrap and damaged-dependency
  refusal. Native transport is simulated, not a new live cloud-account test.
  All three final archives passed these checks.
- An independent reviewer found the remaining accusatory generator wording and
  outdated “seven colleagues” manifests. Both were corrected; the follow-up
  review found no further actionable contradictions or consent regressions.

The initial sandboxed suite could not start its loopback HTTP proxy fixture;
rerunning with permission passed. A sandbox restriction on macOS system access
also interrupted offline `uv` bootstrap; the ordinary-permission package checks
passed. These were environment failures, not hidden passing tests.

## Live OpenCode checks

OpenCode **2.2.5**, `openrouter/z-ai/glm-5.3-flash`, using the existing connection.
The prompts are in [role-quality-followups.json](../evals/role-quality-followups.json).
All data and projects are synthetic. Participation was declined and all submission
endpoint environment variables were disabled. The hosted model processed these
conversations remotely; this is not on-device inference. Existing researcher
stores were untouched.

There were three successive candidate builds, all labelled 0.4.1 within this
unpublished review branch:

1. Eight roles, each with an initial task, challenge, explicit decision/question
   and fresh recall. These ran before the reviewer's generator-label correction.
2. After that correction: a new hypothesis-review discussion and a deliberately
   seeded historical literature mistake, each followed by fresh recall.
3. After the premature-decision fix discovered in run 1: a new peer-review case
   using the final package, followed by fresh recall.

In total: **11 consultations and 11 fresh-recall chats**, with approximately
**US$0.36** reported by OpenCode (not a billing reconciliation).

The corresponding bundled wheel SHA-256 values are, in that order:

```text
8ff6761bb8200f58dac36c850d22a3f759a34681f7299bcdd8cd1c88c0d7a102
20dc1077e9eb4988875d3166cdc3e56688a96bc07863f15a20854d750798beda
05cfdff4eec269801306f2d16e394eeb6cc5bc98dac565826a03cf7fd0759743
```

Local evidence is kept separately under:

- `/Users/will/Code/Benchside Role Followup 2026-11-06/`
- `/Users/will/Code/Benchside Role Followup Final 2026-11-06/`
- `/Users/will/Code/Benchside Role Followup Decision 2026-11-06/`

Each contains isolated stores, installed package files and exported session
evidence. Readable transcripts omit reasoning blocks. These localhost sessions
and paths are maintainer evidence, not publicly accessible attachments.

### Observed improvements

- In the eight-role pass, every exact requested decision was saved and retrieved
  through the runtime in a fresh chat, and both readable formats contained it.
  Every recorded host was `unknown`, as required for OpenCode by the current
  reporting schema. No malformed demographics-skip request was observed.
- The PI's fresh recall quoted the exact decision and labelled additional
  rationale as assistant suggestions, rather than expanding the researcher's plan.
- Both hypothesis-review runs correctly rejected treating one counterexample
  as disproving a probabilistic prediction. Neither used the old “name the dodge”
  accusation, though the model still sometimes sounded overly categorical.
- The methods follow-up correctly rejected eliminating three possible causes
  after a failed run in which all three were changed simultaneously.
- Journal club correctly distinguished recruitment from allocation. In the
  seeded-error case, the model appended a same-kind correction naming the old
  record and evidence. A fresh chat retrieved full history and clearly identified
  “allocation unknown” as the current interpretation, retaining the original.
- The reproducibility audit stopped inferring a stale README from a script with
  no command-line arguments. It inspected the fixtures and checked arithmetic
  without executing or editing the analysis script.
- The final peer-review rerun saved its recommendations as research records,
  waited for the researcher to choose, and recorded exactly one decision. That
  exact decision and the requested unresolved question survived fresh recall and
  appeared in both readable formats. This is one successful retest, not a
  guarantee that every model always follows the instruction.

### Remaining failures and limits

This is a small maintainer check, not a benchmark or a claim of validated
scientific advice. Instruction improvements did **not** eliminate model errors:

- Results discussion still called an unknown scale's values practically
  important, inferred underpowering, and overgeneralised interval behaviour.
  Study design still supplied unjustified precision claims and insufficiently
  qualified small-sample analysis guidance. Methods still offered an unsupported
  replicate minimum and overconfident outcome-to-cause mappings.
- The first journal-club run speculated about deliberate overstatement from a
  fictional marginal annotation. The seeded-correction run avoided that inference.
  This variability is a reason to keep paper-specific claims tied to inspected text.
- The first peer-review run saved assistant recommendations as decisions before
  any researcher choice. This triggered the explicit decision-capture fix above.
  It also represented the requested unresolved question as a critique rather than
  a `QuestionRecorded` event: only **7/8** cases in that first pass met the exact
  open-question check, although its text remained visible in open concerns.
- Some agents still narrated internal IDs and setup steps at length. Three
  consultations initially omitted the required decision rationale and recovered
  after validation refused the request. The validation was not relaxed.

A synthetic audit form required the test researcher to choose a next action
(provenance first). The harness initially supplied the wrong form shape and
retried with the documented string shape. A large transcript export was truncated
through the CLI's pipe; writing CLI output to a temporary file recovered complete
JSON. These harness issues are separate from Benchside's runtime.

Use researcher review for scientific conclusions and saved interpretations.
Further model comparisons and realistic colleague-led discussions are more
informative than adding an ever-longer list of prompt prohibitions. Cloud-account
storage, optional sends and receiver behaviour were not retested in this work.
