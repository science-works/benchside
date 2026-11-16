# Workflow support and ordinary-chat notebook actions — review evidence

This is an unreleased change for review. It does not merge branches, deploy a
Worker, change live reporting, or publish a new package. Solution discovery and
community recommendations remain in their separate worktree.

## What changes

- A shared introduction explains Benchside before first setup. Explicit requests
  to install continue without a second approval. Discovery guidance covers
  OpenCode, ChatGPT/Codex, Claude Code and other hosts with skill/instruction support.
- Ordinary research conversations can offer a small Benchside project notebook
  action rather than require a role. Decisions, evidence, notes and questions
  use the same private journal and recall as all eight research roles, without
  inventing or counting a consultation. Evidence needs a source. Existing project
  boundaries, meaningful checkpoints, guarded saves and readable records remain.
- Roles explore relevant practical obstacles with one useful follow-up, including
  materials, equipment, procurement, coordination and methods as well as software.
  They do not turn every research question into a workflow questionnaire.
- `workflow_problem` has a plain-language description and optional multiple
  labels. `other`, no labels and unfamiliar labels all work. Labels are analytical
  suggestions, never a topic or consent filter. Malformed fields and unsafe
  content still have validation/redaction boundaries.
- Optional workaround status distinguishes a model suggestion, something tried,
  and something the researcher explicitly reports helped. An optional short
  excerpt preserves actual wording with identifying/confidential details replaced
  by `[redacted]`; omit it when that would remain revealing or misleading.
- Explicit new workflow consent uses `scope:all_workflow`. Older limited grants
  are not broadened silently. Exact-payload review, digest approval, revocation
  checks, failed-send recovery and idempotent retries remain in place.
- `sharing.check_in` offers review at a natural pause only for opted-in pending
  problems in the selected project. It remembers the offer even after deferral,
  does not repeat the same pending set in a new chat, and offers at most once per
  session. It never sends, prepares a draft, or grants consent. Other sharing
  channels retain their own timing; requested review is always available.
- Historical conversation analysis still needs its separate consent and scoped
  host access. There is no new background listener or account-wide scanner.

## Verification

All tests use synthetic data. No production submissions were made for this work.

| Check | Result |
| --- | --- |
| Client regression suite | 637 passed |
| Receiver Worker emulator suite | 96 passed; TypeScript check passed |
| Private reporting suite against this client | 66 passed |
| Client lint, generated-role consistency and whitespace | Passed |
| Clean Python wheel/source installation smoke checks | Passed |

New regressions cover notebook-only save/restore, project separation, all eight
roles recalling the same decision and capturing a general problem, consent
renewal/revocation, exact preview approval, retry deduplication, excerpt pattern
redaction, reminder suppression and native schema compatibility.

The same client-generated `workflow-v4.json` fixture is checked by the Python
validator, receiver emulator and reporting importer. The receiver stores the
submitted bytes exactly. The private report preserves the complete approved gap
object; the public report excludes excerpts, descriptions, workarounds and free
labels. Private scientific decisions do not enter the payload.

OpenCode 2.2.5 with `opencode/deepseek-v4.1-flash-free` was also exercised in a
temporary project, in read-only plan mode:

- An ordinary microscope-booking question loaded Benchside without naming it in
  the prompt. The first response failed to name Benchside in its offer and treated
  paraphrased wording as exact. The skill was tightened and a fresh retest named
  the Benchside project notebook and preserved the supplied decision wording.
- An unrelated email rewrite did not suggest Benchside.
- After the notebook offer was declined, the same chat gave the requested
  practical advice without another Benchside offer or any writes.
- A discussion-only PI example explored reagent stock, ordering approval and
  consumption as possible causes, ending with “or something else?”.
- A synthetic excerpt removed names, a confidential project and an unpublished
  measurement. It used `other` plus a descriptive label and marked the workaround
  as `researcher_tried`, retaining uncertainty about whether it helped.

These are sampled model behaviours, not guarantees for every model or host.
The changed installed ChatGPT and Claude builds have not been retested live.
Automatic redaction cannot identify every confidential fact; model review and
the researcher's exact-payload review remain necessary.

## Compatibility and rollout after review

1. Review the companion receiver and reporting changes with this client change.
2. Land reporting support and its immutable client pin before allowing v4 traffic;
   deploy the receiver's v4 validator before releasing the client. No additional
   endpoint, bucket, account permission or collection channel is required.
3. Rebuild and release the client/plugins only after those dependencies are ready,
   then perform a synthetic installed-app save/restore and approved submission test.

New features use `benchside.gaps.v4` and, when saved in a native notebook,
`benchside.native.v5`. Every app sharing such a notebook must update together;
older apps refuse the newer schema instead of silently losing records. Existing
notebooks without these features retain their previous format. The source version
is deliberately not bumped or published as part of this review-only change.

An older receiver may reject v4. The report stays pending; never remove fields,
relabel a problem as a software issue, or downgrade its format to force acceptance.
No thematic LLM grouping or public release of submitted prose is added here.
