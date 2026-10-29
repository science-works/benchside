# Acceptance checks — 28 October 2026

Status: acceptance run completed, with the usability findings below and
permanent test-record cleanup awaiting confirmation. Synthetic data only. Will
authorised testing the existing live endpoint before release. No PR was merged.

## Baseline

- Client: `codex/research-roles-rollout`, `ca77133`, version 0.1.3.
- Receiver: `codex/feedback-usage-rollout`, `39df659`.
- Existing Worker: `benchside-ingest`, active version starting `401226cb`.
- Existing EU bucket: `benchside-gaps`, dashboard listed zero objects before tests.
- Workers Admin and R2 Admin verified in the dashboard.

## Results

| Check | Result | Evidence / fix |
| --- | --- | --- |
| Client regressions | Pass | 435 tests on local Python 3.14. |
| Receiver regressions and types | Pass | 56 tests; TypeScript check passed. |
| Local five-route integration | Failed, fixed, passed | Smoke assertion still expected 3 observations under the old sampling design. It now checks that 21 candidates produce exactly 20 selected conversations and 20 stored observations. All five routes, duplicate receipts, forbidden transcript rejection and revoked consent passed on rerun. |
| Deployment CLI authentication | Not available | Wrangler is not signed in. Current granular roles require an account-owned API token for Wrangler; dashboard deployment is being used instead. No token was created or exposed. |
| Live Python client | Failed, fixed, passed | Cloudflare returned HTTP 403 / error 1010 for Python's default user agent. Both catalogue GET and submission POST now send `Benchside/<version>`. Regression assertions failed before the fix and pass afterwards. Actual `StudyClient` and `HttpExportSink` verified against the live endpoint. Released privately for testing as 0.1.4. |
| Production deployment | Pass | Four missing EU buckets created and all five bound to the existing Worker. Deployed receiver `39df659` with a separately authored, temporary synthetic catalogue. No PR merged. |
| Live five-route receipts | Pass | Each channel returned 201 with the correct SHA-256 and observation count. Exact retries returned 200/duplicate with the original receipt timestamp; actual Benchside clients also verified the retries. |
| Public read protection | Pass | GET on each submission route returns 405/Allow POST. Buckets remain private. |
| Live validation | Pass | Raw transcript in activity and installation ID in gaps rejected (422); changed survey definition rejected (422); malformed JSON and invalid UTF-8 rejected (400); wrong content type rejected (415); oversized body rejected (413). |
| Live rate limiting | Pass with documented limit | Initial new-connection bursts did not demonstrate throttling. A bounded persistent-connection test returned 429 on request 12, with `Retry-After: 60`. Live binding verified at 10 requests/60 seconds. This demonstrates throttling, not a strict global ten-request quota; Cloudflare counters are approximate and per location. |
| R2 storage readback | Pass | All five objects independently opened in the Cloudflare dashboard; parsed JSON matched submitted content, with matching object keys and receipt digests. The five indented test bodies also matched the formatted preview bytes, but this preview is not a raw object download. Each remains in its separate private EU bucket. |
| Aggregate report | Pass | Generated from dashboard readbacks of all seven records: one workflow observation, one feedback submission, one participating installation, three survey answers and one activity batch. Zero invalid/conflicting files. Repeating the complete input set twice leaves the report unchanged. Entire report is synthetic and must not be counted as research evidence. |
| Rebuilt 0.1.4 packages | Pass | All three archives pass extracted-runtime checks: seven roles, local/native save and restore, selected-activity state, batched onboarding, consent defaults, exact replay and damaged dependency rejection. A sandbox-only installer failure was resolved by rerunning outside the sandbox, with package-index access still disabled. |
| Updated regression suite | Pass | 435 tests, lint check passed after the fix. |
| Installed package update | Pass | Claude visibly shows 0.1.4 after Will's upload. Existing private OpenAI plugin updated through Plugin Creator and source readback verified; obsolete 0.1.1 wheel removed. No audience/permission change. |
| Automated browser upload | Blocked | Chrome's file chooser reports missing file-URL access. Will uploaded the Claude ZIP; OpenAI used its supported plugin-update tool. |
| GitHub package checks | Failed, fixed, passed | Workflow still named 0.1.3 ZIPs after building 0.1.4. Commit `3924b13` derives filenames from the runtime version and runs archive checks using the matrix interpreter. Both Python 3.11 and 3.14 jobs passed in run `40675057102`, including all three archives. |
| ChatGPT installed native workflow | Pass | 0.1.4 wheel digest verified. All seven roles saved a record, decision and question. Guarded saves, exact readback and stale-write rejection passed. Project A recall excludes B. Real runtime fetched the synthetic catalogue; stopped before submission for exact-payload review. |
| Claude installed native workflow | Pass with recovered host error | 0.1.4 verified; guarded saves and exact readbacks passed. Seven decisions and six non-supervisor records saved. Supervisor critique correctly refused the first test's missing hypothesis; supplying an explicitly synthetic hypothesis then saved it and the seventh open question at revision 4. Other six roles required no hypothesis. |
| Claude shared Google update | Pass | Existing notebook revision 10 → 11 using the Google Docs revision guard and exact old state. Complete readback confirmed; only the generated journal section refreshed. Existing project/sitting IDs and history retained, consent unchanged/off. |
| Fresh ChatGPT native and shared Google restore | Pass | A new chat found the native notebook by title, restored its marker/question and all seven saved recommendations, and verified project separation. Independently restored the Claude-updated Google notebook at revision 11 with the new decision and unchanged IDs. Both Google documents reported owner-only permissions. Both recalls returned changed:false. |
| Fresh Claude native restore | Pass | A new chat restored the saved marker, methods question and seven decisions through the installed 0.1.4 runtime; changed:false and no writes. Read-only inspection with bytecode disabled preserved the sealed cache fingerprint. All seven sittings remained open. |
| Installed ChatGPT survey round trip | Pass | Runtime catalogue fetch → displayed purpose/question → exact JSON preview → separate digest approval → stored receipt → guarded native save/readback. R2 JSON independently matches the approved answer; object size 291 bytes, key/digest and receipt agree. Repeating under a new operation ID returned the same local receipt with zero HTTP calls. Invitations then revoked; a new check raised ConsentRequiredError with zero HTTP calls. Final native revision 10, all sharing off. |
| Claude catalogue network access | Failed, configuration fixed, passed | Runtime proxy initially refused the collector. Settings → Capabilities showed Allow network egress off. With Will's explicit approval, temporarily enabled it and added only the collector domain alongside the existing package-manager allowlist. The real runtime fetch then succeeded with the expected study digest. After verified delivery, removed the added domain and restored network egress to off. |
| Installed Claude survey round trip | Pass with earlier recovered save error | Exact JSON preview and separate digest approval, then one runtime POST. R2 readback matches the approved JSON, with matching key/digest and 291-byte stored size. Receipt saved at revision 6; invitations withdrawn at revision 7. Both readbacks confirmed on the first attempt. A subsequent invitation check raised ConsentRequiredError with no network connections; all sharing is off. No answer sent during the earlier copy-error recovery. |
| Temporary catalogue closure | Pass | Final deployment `2288bbdd` contains the reviewed receiver with an empty catalogue. Actual StudyClient returned zero studies; a new answer to the removed test definition returned 422. All five receiving routes/bindings remain deployed. |

## Usability findings and proposed fixes

- **Before wider use: make large native saves reliable and quicker.** Claude's
  invitation save contained a single-character transcription error; readback
  validation caught it. It corrected the copy,
  repeated the guarded write and confirmed revision 3 before continuing; the
  supervisor batch then confirmed revision 4. The runtime detected the mismatch
  and no answer was sent during recovery. The bad intermediate remains in the
  document's version history; the current verified state is corrected. Avoid manually retranscribing large
  compressed state strings through model context: use an authorised tool-to-file
  or document operation that transfers the exact generated bytes, retaining the
  revision guard and final hash/readback. Test again with populated notebooks.
- Claude's first full seven-role/native run took roughly 20 minutes; this is a
  multi-case acceptance scenario, not a controlled onboarding benchmark. Both
  apps needed several guarded document operations. Claude's subsequent single
  send, receipt save and withdrawal took about 12 minutes even without copy errors.
  Reduce redundant reads and
  batch recording; measure a normal single-role first-use task separately.
- Direct diagnostic imports wrote bytecode into the sealed runtime cache in two
  Claude runs. Integrity validation correctly refused the changed cache; offline
  rebuild recovered. Version inspection should use `python -B` or a supported
  read-only runtime version action. Do not relax the integrity check.
- A failed catalogue fetch consumes the daily check cooldown by design, covered
  by a regression test. After a network-setting repair, the UI should explain the
  wait; a future explicit, bounded manual retry could improve recovery while
  retaining automatic polling and weekly invitation limits. No cooldown bypass
  or consent relaxation was added.
- In the first failed Claude fetch, the host explicitly discarded the changed
  candidate containing that cooldown. This conflicts with the native-memory
  save protocol even though the inner action failed. Add an installed-host
  acceptance case that persists error candidates, and make that instruction
  prominent before outreach. The later network retry used the actual saved
  revision; it did not edit or reset stored cooldown fields.
- Normal recall and journal views include only the latest five decisions/records.
  Older items remain in the notebook. A complete-history/pagination affordance
  would make this clearer; missing recent-view items must not be called lost data.
- `/pi` requires a hypothesis before critique. Its acceptance case must supply an
  explicitly synthetic hypothesis; the other roles correctly start without one.
- ChatGPT's surrounding notebook reference prose retained revision 6 after the
  authoritative state advanced. The runtime correctly restored revision 7 in a
  fresh chat. Derive displayed revision metadata from the confirmed snapshot or
  refresh it after saves; do not rely on handwritten reference prose.
- Scientific spot checks supported paired controls, biological units, cautious
  confidence-interval interpretation and association rather than causal claims.
  Claude still offered a donor random effect with only three donors; the fresh
  check identified this limitation. Prefer donor summaries for that tiny example
  and qualify variance estimation. These synthetic checks are not a scientific
  quality evaluation or evidence from the original paper.

Cloudflare's [1010 guidance](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/)
recommends a descriptive application User-Agent. Its
[rate-limit documentation](https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/)
describes asynchronous approximate counters, not a strict global quota.

## Resources and versions changed in this run

- Kept Ben's existing `benchside-gaps` bucket.
- Created `benchside-feedback`, `benchside-usage`, `benchside-surveys` and
  `benchside-activity`, all EU, Standard, public access disabled.
- Existing production Worker `benchside-ingest`, same custom domain and five
  R2 bindings. Original code version remains in deployment history (`401226cb`);
  last original-code version with all five bindings was `1375829b`.
- Temporary catalogue deployment: `05411b56`; final reviewed receiver with an
  empty catalogue: `2288bbdd`. Final source bundle SHA-256:
  `271a83d4721a860f842245e8774cf0f693d2e220162bc2aa1e23ecb02768a5bc`.
- Client package 0.1.4 includes the descriptive User-Agent fix. The existing
  0.1.3 sampling/native format is unchanged. Dependency versions are unchanged.
- Runtime/smoke fixes pushed to PR #5 as `8bfd70a`; CI filename fix as `3924b13`.
  PR #5 remains a draft against main, backed by Will's fork. No merge performed.
- OpenAI private plugin release: `pluginrel_6ae1c6a30c848191aabad6c8fd54e0ac`.
  [Plugin](https://chatgpt.com/plugins/Plugin_a5f12a7a3860819195a9308479e22ad2).

## Test-data handling

The test survey was newly authored and explicitly synthetic, not a research
study. It is now removed from the live catalogue. All seven successful test
submissions are registered by channel, payload digest, receipt and object key.
Permanent R2 deletion awaits Will's confirmation under the browser confirmation
policy; local evidence is retained. Do not include these registered objects in
research reports while cleanup is pending. The five buckets are retained.

Working evidence: `/private/tmp/benchside-acceptance-20261028/`; a private local
copy is preserved outside Git in the task's `benchside-acceptance-20261028`
artifact directory. No raw research conversations or participant data were used.

## Outstanding

- Complete approved cleanup of the seven registered synthetic objects.
- Review the installed 0.1.5 results below, particularly Claude's save latency,
  before outreach. The optional failed-invitation save has local regression
  coverage but was not repeated in the installed apps in the focused check.
- A Vercel viewer, real research catalogue, validated activity classifier and
  scheduled invitations have not been deployed or evaluated in this test.

## Focused usability changes after acceptance — 0.1.5

The source and release packages now address the findings without changing storage
formats, consent, endpoints or survey frequency:

- The existing launcher can save its complete response to a new private file,
  while printing only the native candidate's revision/digest and useful results.
  A host with a file-to-tool bridge can pass the exact generated Markdown to its
  guarded document update. This removes a transcription step where supported;
  it does not grant connector access or make literal-only tools read files.
- Guidance batches justified private records, reuses a confirmed readback/guard
  for the next private update in the same chat, and avoids journal refreshes for
  consent-only changes. Fresh reads before submissions and conflict checks remain.
- Failed actions with changed state must still be saved and confirmed. A regression
  exercises a failed invitation fetch, saves its candidate and restores the daily
  cooldown with no second network call. Cooldown responses now include the next
  permitted check time. No manual bypass or background retry was added.
- Recall offers all saved decisions/research records for the selected project;
  the ordinary recent view gives counts and explains how to retrieve older entries.
  The terminal route supports `recall --all`; complete history is read-only.
- Readable journals label a snapshot revision rather than claiming a live save
  status. Host guidance uses confirmed state for current revision numbers and
  keeps changing revision numbers out of the document index.
- A supported `version` action avoids direct cache imports and opening research
  storage. The source launcher also disables bytecode writes.
- Study design, methods and results guidance starts the three-donor example with
  donor summaries and appropriate paired comparisons, qualifies variance estimation
  and avoids a blanket minimum-group rule. This distinction follows the scope of
  [Gomes's simulation study](https://doi.org/10.7717/peerj.12794); it is guidance,
  not a claim that every small-sample mixed model is invalid. An additional synthetic
  role-evaluation case records the expected behaviour; it has not been model-scored.

Local checks cover exact transfer and restoration of a populated synthetic notebook,
owner-only response-file permissions, refusal to overwrite an earlier candidate,
complete-history project separation, read-only recall and error-state recovery.
The archive smoke check now exercises version inspection and response-file transfer
in fresh processes as well as the existing role, memory and consent checks.
All three 0.1.5 archive smoke checks passed with submission endpoints disabled;
the 443-test client suite, lint and generated-role freshness checks passed.

## Installed 0.1.5 focused check

Both installed packages were updated to 0.1.5 and their runtime version actions
verified. The OpenAI plugin remains private to the existing account; its new
release is `pluginrel_6ae1fb51270c8191b18d497fbf2df344`. Claude's plugin UI also
confirmed the update. The wheel SHA-256 is
`3df678e939e755028d99f82248bac667f6555ba7cbb62184c896f0986d611ac2`.
GitHub CI passed on source commit `45ee18b` for Python 3.11 and 3.14
([run 40696113213](https://github.com/WilliamBolton/benchside/actions/runs/40696113213)).

Each app resumed its existing populated synthetic notebook, recorded one methods
summary and one decision in one batch, saved the notebook once with guards and
readback, and refreshed its readable journal once. The scenario used three donors
with paired treatments and technical repeats. Both responses kept three donors
as the independent units and recommended paired pre-/post-extraction controls.
These are bounded acceptance checks, not scientific-quality evaluation results.

| Check | ChatGPT | Claude |
| --- | --- | --- |
| Save and readback | Passed; native revision 11 | Passed; native revision 8 (host document revision 13) |
| Exact response-file transfer | Installed test reported a working code-to-document bridge | Unsupported by the literal-text document update tool; guarded copy/readback passed |
| Full-history recall | Retrieved an older decision outside the last-five view | Retrieved an older decision outside the last-five view |
| Fresh-chat restoration | Passed; new decision and rationale recovered | Passed; new decision and rationale recovered |
| Preserved history | 8 decisions, 7 records, 7 unresolved questions | 8 decisions, 7 records, 7 unresolved questions |
| Other project | Project B retained its marker and single record, with no A records | This focused check used one project; earlier isolation evidence remains separate |
| Consent | All sharing and metascience choices off | All sharing and metascience choices off; no scopes or pending drafts |
| Save workflow duration | UI: 4m 13s | Runtime-reported: 724s from version check through full-history recall; approximately 13 minutes overall |

Fresh-chat checks read the saved documents rather than using the earlier chats as
evidence. ChatGPT's read-only check took 2m 14s; Claude's took approximately three
minutes. No collector submissions, survey catalogue changes, network-setting
changes or PR merges were made. These runs used different models and populated
notebooks and are not controlled performance comparisons. Claude's literal-text
transfer remains a material usability limitation; the new optional file route
does not remove it in that host.

Evidence: [ChatGPT save](https://chatgpt.com/c/6ae1fe97-49f8-83eb-944d-43efcdd8fdb5),
[ChatGPT fresh chat](https://chatgpt.com/c/6ae200be-fabc-83eb-82a1-426897d5985a),
[Claude save](https://claude.ai/chat/1ad70b65-7cac-4432-ae34-25b309938ee7),
[Claude fresh chat](https://claude.ai/chat/93efc22c-9a35-4677-a9ad-a7e7efe5f4ec).
These are account-scoped synthetic test chats, not public research data.

Claude's fresh check also found historical prose outside the state block still
claiming revision 7 and describing the 0.1.4 test. A separate guarded edit removed
those stale labels and identified the fenced snapshot as authoritative. Complete
readback confirmed the state block was byte-identical and native revision remained
8; only the host document revision advanced to 14. No data loss was found.
No failed-invitation test was sent
to the live endpoint during this check; the local regression covers preservation
of its changed state and cooldown, as described above.
