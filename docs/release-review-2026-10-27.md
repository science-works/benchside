# Review preparation — 27 October 2026

This report records the earlier 0.1.2 review and the 0.1.3 follow-up below.
Historical endpoint tests used synthetic records and isolated storage; the current
review does not deploy or exercise the receiver.
The paper, workshop evaluation and graph output directories are outside the PR.

## Review map

The Benchside PR includes the existing session-stamping commit from Rory's PR #4,
preserving its authorship. The follow-up ports the session safety fixes to PR #4
before merging that dependency; no message to its author is required. The new
client and receiver changes are reviewed together against the same JSON contracts.

Draft PRs: [Benchside #5](https://github.com/science-works/benchside/pull/5)
and [receiver #1](https://github.com/science-works/benchside-ingest/pull/1).

| Area examined | Checks and boundary |
| --- | --- |
| Consent and exact submission | Off by default; separate grants; draft digest and destination checked at send time; withdrawal/regrant invalidates approvals; verified receipt required; retries retain approved bytes. |
| Data separation | Original workflow-observation format preserved. Feedback and activity omit installation/project/session IDs. Usage has its own random installation ID and optional categorical demographics. Reports combine aggregates without joining participants across channels. Free text still requires human review. |
| Native memory | Allowlisted files, bounded decompression, checksums, stable project identity, atomic private batches, operation replay, project isolation and guarded host writes/readback. No network actions or approval steps in batches. |
| Metascience | Separate invitation/analysis/sharing choices, selected accessible sources, fixed bounded weekly sample, categorical outputs and evidence labels, no inferred scientific outcomes, empty public study catalog. |
| Receiver and deployment | Strict per-route validation, capped UTF-8 bodies, separate storage bindings, outcome-only logging, unchanged original gaps contract, separate staging buckets and rate-limit namespace. No public collected-data read route. |
| Packaging | Version 0.1.2 across wheel and manifests; bundled hashed dependencies; offline bootstrap; all seven compiled role definitions; no journal or credentials in the package. |

This records code review and executable checks performed in this working session;
it is not a human reviewer approval or a scientific validation study.

## Independent review and fixes

Three Codex review agents examined memory/consent, metascience/reporting and
packaging/onboarding. A separate Claude Opus review read client commit `4992880`
against base `eb9c039`; its environment blocked running PR code, so its findings
were static analysis. Local executable regressions substantiate the fixes below.
The browser reviewer could not fetch the private receiver source. A later
read-only Claude Code review used the local receiver checkout at `8aad0f5`, and
a separate Claude Code follow-up examined client `ca762ae`. Neither executed
code. Proposed defects were checked against the implementation and test results.

- Native memory bounds cached response bodies. Version 0.1.2 retained all operation
  IDs and request hashes; 0.1.3 bounds that index with generation checkpoints that
  refuse expired retries before execution. Submissions check capacity before networking, and ordinary
  writes leave room for consent withdrawal. Emergency control-history compaction
  preserves scientific records and submitted receipts. A physically full legacy
  notebook can still need larger storage; no guarantee of infinite memory is made.
- Runtime caches require trusted ownership, private directories, safe locks and
  verified contents before importing code. Cold install, reuse, tamper rejection
  and interrupted-install recovery have executable coverage.
- Reopening the same journal from another app reuses its project. Scientific
  events record the app that actually wrote them, including when a sitting is
  resumed elsewhere. Global consent/collection ledgers omit that provenance.
- Generated role instructions use the real adapter actions. Missing sessions fail
  with a resume instruction. Source installs have a durable launcher; default
  Claude setup uses the shared app entry, with legacy CLI skills explicit-only.
- Analysis withdrawal clears old selected sources. Invalid optional destinations
  do not block private work. Empty observations cannot produce an empty draft.
  Optional usage tolerates legacy/custom metadata, standardises failure counts
  and omits research text. Aggregate observations deduplicate stable IDs and
  exclude conflicting duplicates.
- Newer native records produce update guidance. **Update every app writing a
  shared notebook to 0.1.2 before continuing:** older 0.1.1 readers cannot read
  newly added provenance fields or compacted replay entries. Keep the notebook;
  do not create a replacement or discard unfamiliar records.

The follow-up led to narrower withdrawal-reserve rules, actionable malformed
request errors, superseded-preview cleanup, removal of empty usage rows, safe
cache-recovery guidance and reporting of migrated source commands. Analysis
withdrawal removes unsubmitted source selections/classifications; changing sources
retires an affected weekly sample rather than silently drawing another one.
Submitted receipts and private no-resampling hashes remain, as documented.

Receiver follow-up fixes duplicate receipts for restored objects lacking their
original metadata, using R2's actual upload time. A shared non-ASCII fixture
confirms the Python/TypeScript study digest contract, and shuffled receiver tests
pass. The suggested Unicode mismatch and test-order dependency were not confirmed.
The claimed Linux cache-install blocker was contradicted by actual Linux 3.11 and
3.14 CI, including cold package execution. Public write access, an empty study
catalog and separately gated staging deployment remain explicit design choices.

## Earlier 0.1.2 verification

- All 327 Python tests passed on Python 3.11 and Python 3.14.
- Lint, all seven compiled-role checks, Codex/portable manifest, Claude manifest
  and shared skill validation passed.
- All three rebuilt 0.1.2 archives passed extracted-runtime checks: all seven roles across
  fresh processes, native restore, batches, remembered choices, replay and
  rejection of a damaged dependency even with an existing cache.
- All 43 receiver tests passed, including restored receipts, the shared Unicode
  study digest and the feedback UTF-16 boundary. Shuffled execution and type
  checking passed.
- The local integration check passed all five channels: stored and duplicate
  receipts, a synthetic study invitation, three sampled activity records, rejected
  transcript content and consent withdrawal before networking. Production requests: 0.
- The staging deployment dry run built successfully and listed only the five
  separate `-staging` EU buckets. It did not create those buckets or deploy a Worker.
- The CI action tags were checked against their upstream GitHub repositories.
- Previous GitHub CI passed for both Python versions, including all three archive checks,
  on [client commit 894cc42](https://github.com/WilliamBolton/benchside/actions/runs/40506017287).
  This run is on the contributor fork; the upstream PR currently has no check run.
  [Receiver CI](https://github.com/science-works/benchside-ingest/actions/runs/40509010527)
  also passed for commit 6f18f2a, including the restored-object fix. Historical
  client runs do not certify later edits.

## Installed-app Google storage check

ChatGPT's installed 0.1.0 plugin restored the existing private synthetic Google
notebook in a fresh conversation, continued the same project and methods sitting,
and saved a new decision in one guarded batch. The notebook advanced from revision
8 to 9. The readable journal was updated and read back. An independent connector
read and runtime restore verified the digest, decision, project identity and
remembered participation deferral. No submission endpoints were called.

The earlier Claude check exercised **Google Drive only**, with specific-file
access. It did not test the separate Google Docs connector and must not be used
to claim that Claude cannot edit Google Docs. Anthropic documents the separate
connector for document edits. On 27 October the user explicitly approved its
broader Google Docs scope. The installed Claude 0.1.1 plugin then read both complete
documents, restored the same project and methods sitting, and saved the requested
synthetic decision. The notebook advanced from revision 9 to 10. `update_doc`
used the exact old state text plus Google's required revision; the journal used
its own revision guard. Full readback and `native.confirm` succeeded. A deliberately
invalid revision was rejected; this test did not separately exercise a stale
revision of the same document.

An independent Google connector read and local runtime restore confirmed revision
10, the checksum, the new decision and its readable-journal entry. Earlier
decisions and deferred participation remain. Independent metadata showed both
documents `shared:false`, with only owner permission. Claude's Docs connector
itself did not expose sharing metadata. No unrelated documents, sharing settings
or collection endpoints were used. This establishes cross-app continuity for
these accounts and connectors, not every Google integration. The connector's
literal-text update requires the model to carry the state payload; checksum and
readback validation remain essential.

Sources: [Anthropic Workspace connectors](https://support.claude.com/en/articles/10166901-use-google-workspace-connectors),
[Google Docs scope](https://developers.google.com/workspace/docs/api/auth).

## Installed 0.1.1 update checks

Both app UIs showed version 0.1.1. Each test verified the loaded runtime and the
bundled wheel SHA-256 `0e774f9de94c81b26496ac83b8138f991ca0ffea991ece968838fdf46cfc117a`.
Claude restored BATCH-O3 in its existing sitting and advanced the notebook from
revision 11 to 12. ChatGPT restored GPT-O3 in its existing sitting and advanced
revision 8 to 9. Both guarded writes passed full readback and `native.confirm`.
Decisions, unresolved questions, other projects, deferred participation, empty
demographics and disabled sharing were preserved. Neither test called a collector.

Both response-only reproducibility checks distinguished the user's unsupplied
README claim from inspected evidence; neither claimed to have read or run it.
Claude also discovered a read-only false revision change. A local reproduction
confirmed that comparing recompressed bytes misidentifies a different valid zlib
representation as changed state. Version 0.1.2 compares decoded state and preserves
the original envelope for unchanged reads, replay and rollback.

These are installed **0.1.1** results; they do not establish installed 0.1.2 behavior.

## Host and release gates

The [23 October report](acceptance-2026-10-23.md) remains the evidence for the
broader seven-role installed tests. The new 0.1.3 ZIPs contain review fixes and need
a further installed update check. Package validation alone is not app installation.

Cloudflare access checks confirmed an active token and a successful signed HEAD
request to the existing EU `benchside-gaps` bucket. After accepting the Science
Works invitation, the dashboard confirmed Individual Workers Editor access limited
to the existing `benchside-ingest` Worker. That permits editing/deploying that
Worker, but does not grant creation of other Workers or R2 bucket management;
the EU bucket object view remained inaccessible. The original production gaps
receiver already exists. Additional access/setup for the new routes is pending,
and the user has deferred receiver and live analysis testing. No production
objects were read or written.

Before outreach:

1. Install the 0.1.3 review update and repeat native resumption in both apps.
2. Repeat shared Google memory after both installed apps are updated to 0.1.3;
   preserve the successful 0.1.1 continuity result as separate evidence.
3. Provision Science Works staging after access is granted, deploy the receiver
   there and obtain real receipts from Claude and ChatGPT. Diagnose any gateway
   or edge HTTP 403 without weakening unrelated network protections.
4. Exercise preview/approval, retry and withdrawal against staging; verify stored
   objects and produce a report from those synthetic exports.
5. Review the PRs with Will before merging and releasing. Public survey definitions
   and their data-handling commitments need review before activating any study.

Remaining limits: Claude setup latency, broader scientific quality evaluation,
host-dependent sharing metadata and eventual native-notebook archival. Nothing
here establishes cross-account automatic synchronization or background access to
all research conversations.

## 0.1.3 follow-up to Claude's eleven findings

This follow-up addresses the review of client `4ef0eaf`, session PR #4 `6e8e444`
and receiver `6f18f2a`. Will has requested pushed updates and review comments,
with **no merges**. The receiver and installed-app checks above are historical;
this follow-up uses synthetic client records and does not deploy anything.

| Finding | Problem and disposition |
| --- | --- |
| 1 | Native replay IDs/hashes grew without bound. The index now has a 128-receipt / 64 KiB limit. Generation checkpoints reject expired requests before execution, preserving scientific history and durable submission receipts. |
| 2 | Crashed registrations could mislabel or block later writes. The anonymous fallback expires after 24 hours without explicit activity; ended pointers remain available for explicit resumption. A targeted recovery command preserves journals. Removing legacy hooks clears that project's registrations. |
| 3 | Cross-project SessionEnd cleared the wrong registration. Cleanup now covers the hook's origin project and its pointer project. |
| 4 | PR #4 alone used last-started-session identity and could adopt another conversation's pointer. A separate fix branch ports the relevant identity, lifecycle and journal fixes before that PR is merged. The original commit and authorship remain intact. |
| 5 | An early-week sample excluded conversations later in that week. New selection uses the previous complete UTC week. Will additionally requested a cap of 20 instead of 10%, with automatic random selection from relevant research conversations or explicit user selection. Methods are labelled and reported separately; existing legacy samples keep their meaning. |
| 6 | Non-object journal lines crashed both readers. They now skip and log the line location/error category, preserve valid records and never rewrite the source journal. |
| 7 | Lifecycle hooks waited on the global transaction lock and could exit nonzero before their error boundary. They now dispatch through their own always-zero boundary and use narrow registration/pointer locks. |
| 8 | Quoting recalled journal text as recorded data remains an optional suggestion awaiting Will's answer. No quoting change is included yet. |
| 9 | Failure accounting repeated invalid storage resolution and produced a traceback. It now preserves the actionable original error; malformed profile shapes are validated too. |
| 10 | Atomic Claude settings replacement remains an optional suggestion awaiting Will's answer. No settings-write change is included yet. |
| 11 | The edit option described inline JSON although it reads a file. Help now explicitly requests a JSON file path. |

Follow-up review also found and fixed active-session expiry: explicit activity
refreshes only an existing registration in that project. It never recreates an
ended session or enrolls an unrelated project. A separate regression fixes the
Python module entry point calling command handlers before they were defined.

The new activity selection tags require the matching receiver validation update.
Gaps, feedback, usage and survey wire contracts remain unchanged. Receiver code
and regression fixtures are prepared separately; live receipt/storage checks
remain deferred. Automatic relevance and date filtering rely on the host's
accessible metadata within approved sources. The engine cannot inspect unseen
conversation history or independently establish that a conversation is research.

Update all apps writing a shared notebook to 0.1.3 before creating new selection
records or replay checkpoints. The new state uses a v2 envelope so older runtimes
request an update. Scientific history still has a finite document capacity; this
change does not implement notebook archival. Installed 0.1.3 acceptance and live
staging delivery remain release gates.

Follow-up verification: all 435 client tests pass on Python 3.11 and Python 3.14;
source lint, all seven compiled-role checks, both plugin manifest validators and
shared-skill validation pass. The PR #4 fix branch passes all 126 tests on Python
3.14 and source lint. Separate agents reviewed the session port, replay-generation
design and new selection/reporting behavior; the additional session and native
compatibility findings were reproduced and fixed before pushing.

All three rebuilt 0.1.3 archives pass offline extracted-runtime checks: all seven
roles save and resume through local and native storage; batches, replay, remembered
choices and corrupted-dependency rejection work. A separate upgrade check using
the actual 0.1.1 and 0.1.3 archives preserves all seven projects/sittings, decisions,
unresolved questions and participation choices in both storage modes. It made
227 fresh-process calls with endpoints disabled, no collection requests and no
metascience actions. The 0.1.3 wheel SHA-256 is
`ce9781e4b5183e847be0163e75a535be20b6d13238febc8bbc82fb913b3ec12b`.
This verifies packaged upgrades, not an installation into a live app account.
