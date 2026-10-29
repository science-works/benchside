# Build and rollout

This implementation is the week 1–2 build. Share with researchers from week 3
after the release checks below, and improve onboarding and the roles as feedback
arrives. The rollout is informal; no fixed cohort or required follow-up session.

## Current verification

**0.2.0 review update:** the branch adds pseudonymous contributions, researcher-written
survey answers under prior study agreement, selected-conversation gaps and supporting
activity categories with definitions. New tests cover consent renewal, exact survey
text, shared gap review and a cloud capacity safeguard. Session review fixes also
apply to PR #6. These changes have not been deployed or installed in the live apps;
the 0.1.5 installed results below remain the latest live-app evidence.


**28 October update:** [live acceptance results](acceptance-2026-10-28.md)
supersede the deployment and 0.1.3 update blockers in the historical notes below.
All five routes now have private EU storage and verified synthetic receipts.
The client is 0.1.5 (443 passing tests), and the receiver has 56 passing tests plus
its type check. Both installed 0.1.5 apps passed a focused methods save and
fresh-chat restoration check. ChatGPT used the direct file-transfer route;
Claude's literal-text tool still makes populated notebook updates slow. The
installed results and limits are recorded in that report. No PR has been merged
and no research rollout has begun.

See the [27 October release review](release-review-2026-10-27.md) for the current
0.1.3 review package, executable checks, independent review findings and remaining
release gates. Installed 0.1.1 passed fresh-chat native restoration and guarded
save/readback in both apps; the 0.1.3 fixes require a further installed update check.
Coverage includes native
memory cases covering all seven roles, project isolation, consent/draft recovery,
ambiguous saves, operation replay and invalid state. The companion
collector passes its type check and 43 Worker tests. The extracted app package
also saves, resumes and concludes all seven roles across fresh processes using
both local files and portable native-document snapshots. All three archive formats
(standalone skill, Claude plugin and portable/OpenAI plugin) pass the extracted
runtime checks. These include remembering a chosen directory and continuing each
role through a second app identity in the same local store/native notebook.
All test records are synthetic, and the package smoke test disables submission
endpoints. All three rebuilt archives also pass batched setup, friendly project
names, remembered participation deferral, exact replay and read-only restore.

The [23 October acceptance report](acceptance-2026-10-23.md) records the four
follow-up checks, live evidence, fixes and remaining blockers. The rebuilt runtime
saved all seven roles in one guarded transaction to real Google Docs and ChatGPT
Pages notebooks, with fresh-process confirmation and readable-journal readback.
The installed Claude plugin was exercised on all seven scientific scenarios.
Three corrected overclaims did not recur in a fresh installed-plugin check.
The final reproducibility wording check passed in both installed 0.1.1 plugins.
Both installed apps passed batched native setup, fresh-chat resumption, feedback
preview, failed submission, retry and consent withdrawal.

Optional metascience adds 28 client cases covering invitation limits, scoped
sampling, private analysis outside the roles, consent withdrawal, exact approval,
native recovery and aggregate deduplication. A real local HTTP check verified
catalog retrieval, survey/activity storage and duplicate receipts, rejection of
a transcript field (422), and revocation before sending. It used only a temporary
local Worker and synthetic records; the review branch's public catalog is empty.

This is not yet an outreach-ready cloud release. The final small package update,
broader scientific response quality and successful in-app staging delivery remain
checks below. On 27 October, the installed ChatGPT plugin restored and updated the
existing Google notebook; independent readback confirmed the saved decision and
unchanged project identity. After explicit approval of the separate Google Docs
connector, Claude's installed 0.1.1 plugin resumed that same project and saved a
synthetic decision at revision 10 using a guarded update and complete readback.
Independent restoration confirmed the decision; Google metadata showed both test
documents unshared. This establishes cross-app continuity for the tested accounts.
The Drive-only check had not tested this separate editing connector. Claude's
native Docs tools cannot verify sharing permissions; private native state was
checked in the UI. No hosted journal service has been added, and deployment
of the new collector routes remains outstanding.

On 22 October, read-only requests from this environment to the public `/v1/gaps`,
`/v1/feedback` and `/v1/studies` addresses returned HTTP 403 / Cloudflare error 1010
(browser signature blocked), before the Worker could be verified. The collector
repository documents the original gaps route as deployed on 20 October; these
checks do not confirm current storage receipt or establish whether other clients
can reach it. The operator needs to check API-client access as well as deployment.
No production test submissions were sent.

On 23 October, an isolated temporary HTTPS Quick Tunnel also passed all five
submission routes: stored receipts and exact duplicate retries. It served the
same disposable local Worker and synthetic-only storage, without a Cloudflare
account or deployment. Initial attempts failed DNS lookup; allowing the new name
time to resolve succeeded. This demonstrates HTTPS client-to-receiver delivery,
not provisioning or deployment in the Science Works account. See
[endpoint testing](endpoint-testing.md) to reproduce it.

Claude's execution gateway refused the temporary HTTPS domain with a 403. A later
ChatGPT installed-plugin test also received 403 before reaching the Worker, as
checked against receiver logs and stored objects. Both preserved reviewed drafts
after two failed sends and blocked another send before networking once consent
was withdrawn. This verifies failure recovery, not successful cloud-app delivery.
A reachable approved staging address is still required; no network restrictions
were changed. Both temporary receivers were stopped and their storage removed.

## What is implemented

- General agent onboarding asks where records should live, discovers existing
  projects, and can reuse their IDs across apps. Local directory choices persist
  in the OS account configuration. Source installs expose the same `bench app`
  protocol as the bundles, with Claude, Codex and custom skill-directory installers.
- Claude plugin packaging now includes its validated manifest and upload archive;
  portable/OpenAI packaging includes an onboarding entry. Custom installation and
  fresh-chat discovery passed in the tested Claude account; public distribution
  and other hosts/account configurations still require checks.
- Seven scientific roles, generated from one set of persona records for the CLI
  and app package. New roles record appropriate scientific outputs and decisions
  without requiring a hypothesis or invented criticism.
- A structured app adapter, guided setup, private project journals, automatic
  recall and resumption, and Rory's PR #4 session stamping with per-session shell
  identity to avoid attributing concurrent conversations to the last one opened.
- One optional review flow for workflow observations, feedback and usage.
  Independent consent, identifier scrubbing, editable drafts, exact-content
  approval, bounded batches, verified receipts and retry recovery.
- Separate feedback and usage contracts and an offline aggregate report.
  The companion `benchside-ingest` repository has matching routes, validators,
  separate R2 bindings and synthetic contract tests.
- Optional discipline and career-stage categories, with an independent choice to
  include them in reviewed usage reports. The private profile persists in local
  and native storage; changing it invalidates prepared usage drafts. Aggregate
  buckets use each installation's latest accepted report. In the earlier format, other channels never
  contain these fields, and setup does not infer demographic answers.
- Optional study invitations and wider observation, with independent consent,
  bounded random samples, categorical records, weekly batch review and aggregate
  reporting. See [metascience](metascience.md) for the host workflow and limitations.

## App availability and persistence

The packaged runtime supports Python 3.11+ on macOS/Linux with a persistent
user-owned directory. The assistant performs setup; the researcher does not
need developer commands or an API key. Release bundles include hash-locked
dependency wheels for standard CPython 3.11–3.14 on macOS (Intel/Apple Silicon)
and glibc Linux (x86-64/ARM64). Setup uses pip or uv offline, without first-use
access to Python package repositories. Release building requires network access.

**Native document memory is implemented.** The host uses its own authorized
document tools to read a private notebook, pass it to `native.run`, conditionally
save the candidate, and read it back through `native.confirm`. The runtime restores
into a fresh temporary directory on every call. It requires no cloud-mounted
filesystem and provides no hosted journal service.

One private state Page holds validated journal events, project mappings, consent,
prepared submissions, usage identity and receipts. Per-project readable Pages
are derived views. A single guarded state write avoids partially saving those
dependent records. Checksums detect damage; operation IDs prevent committed
actions being repeated after ambiguous saves. The compressed state is private
research data, not encryption. State documents are bounded at 190,000 bytes and
8 MiB uncompressed. Replay responses are bounded, and the operation ID/hash index
is limited to 128 entries or 64 KiB. Checkpoint generations fence expired requests
so forgetting an old ID cannot silently replay its action. Saved submission
receipts remain available separately. Ordinary writes leave capacity for consent withdrawal;
submission receipt space is checked before networking. A full notebook preserves
scientific history and needs archival/larger storage. Update all apps sharing a
notebook to 0.1.3 before new activity selection records or a v2 replay checkpoint;
0.1.2 cannot read the new sample methods or v2 snapshots. Preserve refused state
and update the runtime; never remove method fields or downgrade its schema.

On 22 October, native ChatGPT Page creation, read, guarded update and readback
were verified with synthetic records. Will independently opened a new ChatGPT
conversation and recovered revision 2's decision and unresolved question. This
proves cross-chat retrieval of a native Page. The rebuilt package subsequently
created a synthetic methods record, unresolved critique and decision, saved each
through real native Pages tools, verified readback, and restored the structured
recall in a new execution process. The readable project journal was generated
from that saved state. The subsequent installed-plugin setup and fresh-chat
discovery/resumption passed on 23 October, reaching confirmed notebook revision 8.

On 23 October, the connected Google Drive/Docs tools saved a private synthetic
notebook and readable project journal in the account's private ChatGPT folder.
Complete reads restored the structured decision, unresolved question and open
discussion in a fresh runtime. Google rejected a deliberately outdated revision.
A second app identity then resumed the same project; revision 7 restored both
decisions and the readable view matched. This tests live Google storage plus
runtime portability, not an actual Claude-to-Google session.

After Will signed in to Claude on 23 October, a separate native Claude Doc test
passed private creation, complete readback and guarded update. The visible UI
showed “Only you”. An update from revision 1 to 2 used the full block ID plus
`ifHash`/`ifRev`; a second update using the old guard returned `guard_mismatch`.
A fresh conversation, given only the document title, found the same Doc through
the Artifact listing and read revision 2, the synthetic marker, decision and open
question through Claude Docs. No chat-history lookup was used. Evidence is in
the [write/conflict test](https://claude.ai/chat/61d00e51-6ee3-45aa-b7ce-9caae0ceffd2)
and [fresh-conversation lookup](https://claude.ai/chat/e829e605-c9dc-48a7-8f66-119ce7428be2).
This established the native storage prerequisites in that account, followed by
the installed-plugin checks below. The shared native-memory guide maps the
observed Claude operations and guards explicitly.

The Benchside 0.1.0 review plugin was then installed in Claude with Will's
approval. Its first complete workflow attempt stopped before creating records:
the host blocked PyPI downloads, so the pinned runtime dependencies could not
be installed. No notebook or project was created, and no collector request was
made. The release builder now bundles the locked wheels, verifies their checksums,
and installs with package indexes disabled. All three archives passed cold-cache
offline smoke checks through pip/uv on macOS, covering every role and simulated
native restoration. The offline build was then uploaded and replaced the initial
installed plugin. In a new Claude conversation it bootstrapped on Linux x86-64 /
Python 3.13 and saved a synthetic methods project through revisions 0–6, each
confirmed after guarded native writes and readback. The notebook and journal UI
both showed "Only you". All participation choices stayed off, demographics were
skipped and no submissions were made. The
[installed workflow test](https://claude.ai/chat/7ec0ea1d-31e7-4368-96c7-74b4d2edd85d)
exposed a recall defect: open questions omitted claim grounds/alternative
interpretations. This was fixed and covered by a native restore/journal regression
test, then rebuilt and installed for the fresh-conversation check.

The [fresh conversation](https://claude.ai/chat/8b8672bf-8cc4-4ebd-ae6d-87e9c7d094a7)
discovered the notebook from native Docs metadata, without a supplied locator,
decision, project/sitting ID, chat-history lookup or saved conversational memory.
It restored the decision and full unresolved question, reused project
`p-9fd0e30e5814400552dd92f947cbd292` and sitting
`c-017370d040274e3b866c353e2267879b`, and created a new session. Guarded saves and
`native.confirm` passed for revisions 7 and 8. A second private project, M9-B,
was registered in the same notebook at confirmed revision 9; its recall had no
records, decisions, questions or sittings, while M9 retained its own records.
All sharing/metascience preferences remained off and the demographic profile
remained empty. The readable M9 journal was refreshed with the full question.
This establishes the installed methods-role storage/resumption path in that
account, not every role's scientific quality, all account types, or a live
collector submission from Claude. The review plugin remains installed; no main
merge or backend deployment was performed.

The live test identified three usability problems: internal project IDs instead
of friendly titles, no explicit memory of declining/deferring participation, and
slow serial saves (about 12 minutes for the earlier Claude setup). The review build
now returns friendly titles, stores a private participation response independently
of consent, and supports an atomic batch of up to 16 private actions followed by one
guarded save/readback. Batches exclude networking, previews and submissions. A failed
step rolls back the entire batch; exact replay cannot create duplicate sessions.
The package and live Google/Pages connector checks pass. The installed Claude
batched setup took about 7½ minutes, including recovery from an incorrect batch
reference; its fresh-chat resume confirmed revision 11. Installed ChatGPT setup
took 2m 21s, with fresh-chat resume at 2m 11s. These individual runs are not a
controlled speed comparison. Both returning stores preserved their choices
without renewed participation prompts. On 27 October both apps showed installed 0.1.1, verified the bundled wheel,
restored those existing projects and saved a resumed session with guarded
readback. The final reproducibility wording check passed in both apps.

See `content/app/references/native-memory.md` for the host workflow, conflict
recovery and separation between a network receipt and a successful native save.

Official sources checked during implementation:

- [ChatGPT skills](https://learn.chatgpt.com/docs/build-skills) and
  [plugin packaging](https://learn.chatgpt.com/docs/build-plugins): installation
  and available tools depend on the workspace and surface.
- [ChatGPT projects](https://learn.chatgpt.com/docs/projects): shared project
  context alone does not establish writable journal persistence.
- [Claude custom skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills):
  skills can bundle scripts and install Python dependencies; the Claude archive
  contains one root skill folder.
- [Claude session environment](https://code.claude.com/docs/en/hooks#persist-environment-variables):
  the session-start hook can pass session identity to subsequent shell commands.

## Before outreach

1. Run the Python tests, linter, compiled-skill check and packaged-runtime smoke
   test. Run the companion collector's type check and Worker tests.
   The package check is `python scripts/smoke_release.py dist/benchside-claude-0.1.3.zip`
   after building the release; repeat it for the two plugin ZIPs. It exercises
   local continuity and simulated native transport, not live cloud persistence.
   Validate the Claude manifest with `claude plugin validate plugins/benchside`.
2. In each advertised app/account type, install the package, save a native
   notebook with readback, move to a new conversation, reset execution, and recover the same
   project, open sitting, decision and research record. Confirm another project
   does not see that scientific content. Test the storage-choice prompt with local,
   native and installed connector options. A read-only connector must not be offered
   as working journal storage. If two apps share a location, select the same existing
   project and verify continuation and conflicting-write recovery.
3. Try every case in `evals/research-roles.json` in the actual AI host. The
   deterministic tests verify recording and resumption; they do not establish
   that a model provides good scientific advice. Inspect source attribution,
   invented objections, uncertainty and respect for the scientist's choices.
4. Have the Science Works endpoint operator provision the new feedback, usage,
   survey and activity
   buckets and deploy the companion Worker, first to staging. Ben's integration
   note explicitly says app developers need no Science Works Cloudflare account
   access; they can use the anonymous endpoint and test a local Worker without it.
   Will has now created a Cloudflare account with his Science Works email and is
   waiting for Ben's Science Works invitation. Direct deployment needs that
   organisation access; alternatively Ben can deploy staging and provide the address.
   The code/config changes alone do not create cloud resources.
   No production submissions are used as development fixtures.
5. Test each consent choice, edit and re-review, failures, retries and revocation
   against staging. Shared cloud egress may encounter the existing per-IP rate
   limit; verify expected concurrent use before advertising a cloud route.
6. Distribute the full seven-role release through contacts and communities.
   Offer feedback and usage choices in the same flow as workflow observations.
7. For metascience, try `evals/metascience.json` in each host. Verify selected
   session access, scope boundaries, private state restoration and honest evidence
   labels. Keep the catalog empty until a study definition and its data-use/retention
   process are reviewed. Configure native scheduled checks only on explicit request;
   a weekly check inventories the previous complete Monday–Sunday UTC week from
   the selected sources. Filter for research relevance using available metadata
   before selection, including work without a Benchside role; report missing
   date/relevance information or source access. Pass the status sampling window's
   week when creating the sample so a Monday rollover cannot relabel an inventory.
   Automatic selection includes all relevant eligible conversations up to 20,
   or randomly selects 20 above that cap. A researcher may instead explicitly
   choose up to 20; record the method. Both share one fixed batch per observed
   week, so switching methods cannot redraw it. A scheduled run must leave
   submissions awaiting researcher review.

## Collecting and interpreting data

Usage reports are cumulative snapshots for a Monday–Sunday UTC week. A stable
installation/week report ID and increasing revision allow analysis to replace
earlier snapshots, even when uploads arrive out of order. Started, concluded and
explicitly abandoned consultations are counted by the week of each event.
They are not a cohort completion-rate denominator. Reopening the same sitting
does not count as another start; closing an app does not count as abandonment.
Role, Benchside and app versions accompany the counts. App release versions are
`unknown` when the host does not expose one; a model name is not an app version.

Demographic buckets are optional self-reports attached only to reviewed usage.
The aggregate report uses each installation's latest accepted weekly snapshot
once for these buckets; an omitted current profile is not backfilled from older
weeks. They describe opted-in installations, not exact people or the research
population. Shared multi-person stores should skip demographic reporting.

New contributions use one random pseudonymous ID per private store, including
workflow observations, feedback, surveys, activity and usage. New v2 envelopes
keep research project/conversation identifiers out. Existing participants must
accept the new linking explanation; received unlinked records remain unlinked.
Public tool/dataset names and versions may explain gaps; model-derived reports
exclude private findings and research details. Survey text supplied by the
researcher is preserved as written under the study agreement.

Download authorised copies of the collector datasets to a private
directory, then run `python -m benchside.reporting <directory>` for Markdown or
add `--json`. The report deduplicates retries, uses the highest weekly usage
revision, excludes conflicting snapshots, and combines aggregate findings
with distinct contributing-store counts across channels and per gap kind. No
contributor IDs or raw survey text appear in the aggregate export.

Survey answers are grouped by study version and definition digest. Activity
reports use the highest revision of each independent weekly batch, distinguish
model inference from researcher reports, separate selection methods, and show coverage only for submitted
batches. They do not estimate a population or establish classifier accuracy.
For new samples, the activity `week` is the previous complete observed UTC week,
not the submission week. `weekly-random-max20-v1` includes all relevant eligible
sessions up to 20 or randomly selects 20 from a larger supplied inventory.
`weekly-user-selected-max20-v1` records an explicit chosen set; its eligible count
means that set only, never all accessible research or a population denominator.
The report's `activity_by_sampling` separates both methods and the preserved
`weekly-random-10pct-max5-v1` legacy rule. Older saved samples may have been fixed before their
week ended and are preserved without redrawing or changing counts. They can be
resumed after an update, so a newer preview's client version does not establish
complete-week coverage. Treat those historical batches as their original supplied
inventory, and do not assume a complete research-activity denominator. The host
filters relevance and dates; the engine cannot independently validate that from IDs.
The v2 receiver validators have local tests; deployment and installed-app checks
remain necessary before the updated client is released.

Only opt-in installations are counted. Reinstallation or multiple apps may
represent the same person more than once. Use feedback and the examples people
choose to discuss to interpret counts; activity and completion do not establish
scientific benefit.

## Original paper

Keep the original workshop evaluation separate. Its source baseline is
`eb9c039d270d8c4e2cb5a38a2049533ceff10e05`; the existing local
`neurips_workshop_eval/` and `paper/` directories are not modified by this build.
The revised `/pi` is version 2. Do not attribute new role or rollout results to
the original paper conditions.
