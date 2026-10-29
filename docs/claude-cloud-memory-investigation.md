# Benchside: investigate Claude memory and sending permissions

Updated 29 October 2026. The installed review package and its running launcher
have both been verified as **0.3.0**. This brief covers two usability issues:
reliable private memory, and sending an approved workflow report from Claude
without unnecessarily broad network access. The memory failure evidence below
comes from 0.2.0; the network probe comes from 0.3.0.

## Task

Investigate and test the smallest dependable way for the installed Benchside
plugin to (A) save and restore private scientific records and (B) send an exact,
researcher-approved problem report to Science Works in Claude. Inspect your actual
tools and capabilities rather than assuming another agent's description is
complete. Prefer a supported native integration if one exists. Avoid a large
redesign: first establish what already works, then propose the smallest fix.
Do not treat another successful tiny notebook as proof that the larger failure
has been fixed.

### Scope: minor Claude compatibility changes only

Will's instruction: **only make minor changes where necessary to make Benchside
work better in Claude.** Diagnose first and leave working behaviour alone.
Prefer a small correction to Claude-specific instructions, packaging or an
existing transport adapter. Preserve behaviour in Codex, ChatGPT and other hosts.
Do not refactor unrelated code, redesign storage, change schemas or the research
design, add a new backend, or build/deploy an MCP service as part of this task.
If a reliable fix needs any of those larger changes, explain the option and stop
at a recommendation for Will to review. Do not expand scope to make a test pass.
Any small code fix should have a focused regression test and a clear diff.

Produce a concrete diagnosis, a tested prototype where feasible, timings and an
implementation handoff within that minor-change scope. Do not merge PRs, deploy
infrastructure or publish a release. Test with synthetic records in separate
test stores. Use mocks for write
requests initially. An HTTPS GET to the public study catalogue is acceptable if
the current host permissions allow it; it contains no research payload. Before
any live submission, show the exact synthetic payload and destination and obtain
the user's approval. Do not change account network settings or install/connect
services without the user's explicit approval. There is no current permission
to turn on Claude's network setting for this investigation.

## Current source and installed version

- Repository: https://github.com/science-works/benchside
- Main rollout PR: https://github.com/science-works/benchside/pull/5
- PR source: `WilliamBolton/benchside`, branch `codex/research-roles-rollout`.
- Current code baseline: `2beea1100ff44e8559b2b21d8d9dd04b28642af3`;
  later commits on the same branch may update documentation. Read the current
  PR head before changing code; do not discard anyone else's work.
- Installed Claude plugin and runtime: **0.3.0**, confirmed in the host.
- Local source, if available: `/Users/will/Code/science-works/benchside`.
- Storage logic: `benchside/application/native.py`.
- Launcher: `content/app/scripts/benchside_app.py`.
- Instructions: `content/app/references/native-memory.md`, `onboarding.md`,
  `app-api.md`, and `content/app/SKILL.md`.
- Source packaging: `benchside/application/packaging.py`, `scripts/build_release.py`.
- Sharing: `benchside/application/sharing.py`,
  `benchside/infrastructure/http_sink.py`, `content/app/references/sharing.md`.
- Built Claude plugin, if local files are accessible:
  `/Users/will/Downloads/benchside-claude-plugin-0.3.0.zip`.

The 0.3.0 instructions warn about inline-copy transport and stop unsafe recovery
attempts. They are guardrails, not a completed transport fix. This version also
adds optional tool/dataset versions, impact and workarounds to shared problems;
do not lose these fields when proposing a different transport.

## A. Private memory: observed failure, 29 October 2026

Test conversation:
https://claude.ai/chat/2d14f553-0f5e-4856-b678-b1b31154e6b0

Existing synthetic notebook (read-only reference; do not change it):
https://claude.ai/artifact/YAqaPuj38DrHxihnRZxwQQ

- Title: **Benchside private notebook — ACCEPT-20261028-A (synthetic)**.
- Document ID: `fc6aeda3-6e4a-4af6-9243-23a7a43d16bd`.
- Observed Docs revision: **14**.
- Envelope reported snapshot revision **8**, workspace
  `379b4b2d707240f1ad9639536e68931b`, but was not validated by the runtime.
- `native.inspect` rejected the copied payload with `native_storage_invalid`
  / checksum failure. The model reported corruption after roughly 3,100 characters
  and a truncated/invented tail. The source notebook was not changed.
- Requested marker `DEMO-020-29` was **not saved**. Do not assume it exists.
- Total attempt about 5.8 minutes. Runtime startup was seconds, so the slow,
  unreliable portion was the host/LLM data transfer rather than Python execution.

A follow-up diagnostic reported:

| Route | Observed limitation in that session |
| --- | --- |
| Claude Docs read | State appeared only as inline tool text in model context |
| Claude Docs export | Inline base64, no directly usable execution file |
| Artifact files/read | Viewer files existed, but no notebook-content file |
| MCP resources | No Claude Docs resources listed |
| Programmatic tool invocation | No available execution tool could directly call Docs |
| Google Drive download | Inline base64; did not provide a bridge for this Claude Doc |

Treat these as observations to verify, not immutable platform facts. A previously
unnoticed export, tool-composition facility, file handle, asset route or supported
native API could change the diagnosis. Do not inspect hidden browser state,
extract session cookies or invent undocumented authenticated endpoints.

Earlier small Claude notebooks saved and resumed successfully, sometimes slowly.
A fresh small ChatGPT 0.2.0 demo also saved/read back successfully on 29 October.
Neither result establishes dependable transfer of growing Claude notebooks.

## How memory currently works

The authoritative private notebook holds a single JSON state block containing
compressed/base64 state and a SHA-256 checksum. Compression is not encryption.
It includes project records, decisions, questions, preferences, consent and
submission/replay state. Project journals are readable derived views.

The host reads the complete block and retains its document revision/block hash.
The bundled Python runtime restores it in a disposable directory, executes a
request or batch and returns a candidate snapshot. The host conditionally writes
that exact candidate, reads it back, and calls `native.confirm`. A runtime result
alone does not establish persistence. The source reads native.v1, v2 and v3;
context-bearing notebooks use v3 to prevent older clients silently dropping fields.
It preserves bounded replay receipts and operation generations, guarded conflict retries and
capacity reserves. Preserve these semantics.

`--response-file` writes the complete runtime response to a private local file.
It only helps when the host can transfer that file's contents directly to a
document tool. Passing the filename to a literal-text field does not read it.
`native.batch` reduces save count, but does not solve byte transfer.

## Investigation priorities

1. Inspect available tools for an **exact bidirectional bridge**. Can document
   content reach execution as bytes without model transcription, and can a saved
   candidate reach a conditional document update the same way? Show the actual
   documented capability and receipts. A downloadable export alone solves only
   half the problem.
2. If a native route exists, prototype it with a new, clearly labelled synthetic
   notebook. Inspect privacy before creation. Keep the existing notebook intact.
3. If there is no exact bridge, compare a minimal connector-based implementation
   with bounded/chunked document transport as recommendations only. Do not presume chunking is sufficient:
   describe how a complete candidate becomes authoritative atomically, how partial
   writes are discarded, and how the last good version remains recoverable.
   Avoid a new multi-document protocol merely to make a single demo pass.
4. Consider durable local storage through Claude Desktop/Code as an immediate
   alternative where actual host filesystem access exists. An ephemeral cloud
   execution directory does not qualify. Do not silently relocate an existing
   user's research records or treat it as a browser-cloud fix.

Do not route private research memory through Science Works' metascience collector.
That endpoint receives optional approved contributions, not private notebooks.
If a proposed connector needs new account access or OAuth scopes, describe the
required permission and stop at that boundary; do not obtain credentials by
scraping another connector. Keep the user's chosen storage and permissions unless
they explicitly choose a change.

## Acceptance evidence

Use synthetic fixtures of increasing, measured size: small (~5 KiB), comparable
to the failing notebook, then ~50 KiB and ~150 KiB if the route supports them.
Sizes refer to the saved encoded envelope; record actual values. Do not fill
the user's existing notebook for this test.

- Exact save/readback and checksum match, including Unicode text.
- Fresh-conversation discovery and restoration using the stable notebook ID.
- A real decision/open question retained after another write and fresh restore.
- Project A/B separation and unchanged optional-sharing settings.
- Deliberately stale revision rejected, followed by safe reconciliation.
- Truncated/corrupted transfer rejected without replacing the last good notebook.
- Interrupted write/retry does not duplicate a decision or submission.
- Time spent reading, transferring, executing, saving and verifying separately.
- No claims based only on chat history or a readable derived journal.

If proposing a code change, add meaningful regression tests for the confirmed
defect and run the affected native tests. Work in an isolated branch/check-out
for experimental code; do not overwrite ongoing PR work. Report host acceptance
results separately from unit-test results. Never weaken consent, source privacy,
checksum checks, conditional writes or replay protections to pass a test.

## Handoff to return

1. The root cause and exact capabilities inspected, including any route that
   worked that the earlier diagnostic missed.
2. A test table with host/version, notebook sizes, timings, outcomes and evidence
   links. Clearly mark untested or failed cases.
3. The smallest proposed patch or prototype, its location/diff, and migration
   implications for existing notebooks, including those written by 0.2.0.
4. What works today, what still requires engineering or account permissions,
   and whether Claude web, Claude desktop and other hosts differ.

If a reliable fix is not available, say so plainly and give the best supported
fallback. Do not claim that prompt wording alone resolves exact data transfer.

## B. Approved sending and Claude's network permission

### Observed state

Verification chat:
https://claude.ai/chat/2cbbcc81-ad86-4696-94d5-fec78edb5a43

- The installed launcher returned 0.3.0 and bootstrapped from bundled wheels.
- A read-only GET to `https://ingest.benchside.science.works/v1/studies`
  was blocked by Claude's egress proxy with HTTP 403, before reaching our Worker.
- The account's **Settings → Capabilities → Allow network egress** switch was off.
  It has been left off. The user's question is whether Claude can instead ask for
  approval to make the particular connection/send.
- The existing receiver is working: an approved synthetic send from the local
  0.3.0 client reached Cloudflare and appeared in the automatic GitHub report
  about 15 seconds later. This does not prove the installed Claude path works.
- No Benchside MCP server is currently provided by this package. The code sends
  HTTPS JSON directly from the host execution environment.

### What to investigate

1. Check the actual Claude tools and current official documentation. Does this
   host support a native one-request network approval or a domain-specific grant?
   Distinguish Claude web, Claude Desktop/Cowork and Claude Code. Do not generalise
   from one surface or assume saying "yes" in chat changes a technical restriction.
2. If a supported per-request option exists, reproduce it with the public GET
   first. Record exactly which user action grants permission and how long it lasts.
   Otherwise identify the smallest supported settings change (ideally just
   `ingest.benchside.science.works`), without enabling it yourself.
3. Check whether a small remote MCP connector is a better route for nontechnical
   users. Official docs say connector connections are separate from code egress;
   verify the actual account behaviour. Establish whether a native approval
   prompt can cover the exact report and destination, which permission mode is
   required, and whether installation/connection adds friction. A design
   recommendation is enough; do not implement or deploy a new service under this
   task. A small reproduction using existing tools is appropriate.
4. Preserve the existing preview → researcher approval → exact-payload send →
   verified receipt flow. If a connector can make approval simpler, explain how
   its tool arguments identify the reviewed immutable draft and how any payload
   or destination change invalidates approval. Neither general sharing consent
   nor a host's automatic approval mode replaces the researcher's content review.
5. Prefer reuse of the existing receiving API and validation. A connector must
   expose narrow contribution/survey operations, never arbitrary URLs, code
   execution or administrative access to buckets. Users must not need Cloudflare
   credentials. Private project notebooks must stay in their chosen private
   store, even if a connector also helps solve memory transport.

### Evidence and acceptance

- A table of supported paths, actual host/tool names, setup steps, permission
  scope and whether each was tested, documented only, or unavailable.
- Read-only connectivity checked separately from a successful write. A GET or
  model statement is not evidence that a report was submitted.
- Mock tests: decline/cancel sends nothing; changed draft/destination requires a
  new review; retries preserve exact bytes; receipt matches payload; network
  denial leaves the report pending and explains the next step simply.
- If a live test is later approved, use only a separate synthetic fixture. Do
  not use the colleague-demo marker or consume its waiting reporting window.
- The smallest proposed implementation, new infrastructure if any, and what the
  user sees during installation and their first approved send.
- Clearly separate this from memory: a working send does not establish durable
  research storage, and working memory does not establish sending permission.

Official references to verify against the actual host:

- https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude
- https://support.claude.com/en/articles/11176164-use-connectors-to-extend-claude-s-capabilities

Return one combined handoff covering A (memory) and B (sending), with confirmed
facts, failed attempts, the smallest fixes, and any decision/permission still
needed from Will. Do not claim that either issue is fixed solely by changing
instructions. Keep minor patches separate from the current demo build; leave
larger proposals unimplemented.
