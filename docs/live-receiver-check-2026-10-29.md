# Live receiver check — 29 October 2026

The production receiver now runs source commit
`e21bedecb93b7506ea5ca688329d4cb0bf2009c6` from
[receiver PR #1](https://github.com/science-works/benchside-ingest/pull/1).
No PR was merged. Cloudflare's active deployment is `2df7e827`.

The existing domain, five EU bucket bindings and rate limits were retained.
This enables the 0.2.0 linked gap, feedback, survey and activity formats,
including researcher-entered survey text. The live catalog is empty again;
no research study is currently offered.

## Results

- Receiver tests: 63 passed; TypeScript check passed.
- Live HTTPS checks: 26 passed. Each of the five channels accepted one synthetic
  record and returned a matching SHA-256 receipt. The actual 0.2.0 Python client
  retried every payload and verified the original receipt with duplicate status.
- All five collection routes refused public reads.
- Invalid contributor IDs, raw transcript fields, changed study definitions,
  overlong answers, malformed JSON, invalid UTF-8, wrong content types and
  oversized requests were rejected.
- A temporary synthetic survey offered one choice question and one text question.
  Its answer was: “TEST ONLY: Fiji channel labels need manual restoration.
  Synthetic example, not a participant report.”
- After removing the temporary catalog, the actual client fetched zero invitations
  and further submissions to that synthetic study were rejected (HTTP 422).
- Reporting tests: 19 passed after adding the five new payload hashes to the
  exclusion manifest in [reporting PR #1](https://github.com/LauraRyanSW/tools-science-works/pull/1).
  Twelve registered synthetic payloads are now excluded. No stored object was deleted.

Successful verified receipts establish that the receiver accepted and acknowledged
storage of the exact submitted bytes. The subsequent reporting check below also
verified those bytes independently in R2.

## Reporting connection and independent readback

With the user's approval, created `benchside-github-reporting-readonly` with Object
Read permissions scoped to the five Benchside EU buckets. Saved its credentials
as encrypted `BENCHSIDE_R2_ACCESS_KEY_ID` and `BENCHSIDE_R2_SECRET_ACCESS_KEY`
Actions secrets in the private `LauraRyanSW/tools-science-works` repository.
Credentials were not printed, committed, or written to local files. They do not
belong in the client package or Vercel browser code.

The reporting importer ran locally against live R2 with this credential:

- Listed 12 objects; excluded all 12 registered synthetic objects; accepted zero
  research objects. The resulting research summary therefore contains no demo data.
- Independently read all 12 known objects and verified their receipt hashes and
  sizes. The newest five also matched the exact sent JSON bytes.
- Ran aggregation separately on the receipt-matched synthetic fixtures: two gap
  observations, two feedback submissions, four survey submissions and two activity
  batches were handled successfully. This fixture output was not published.
- No object was written or deleted; no schedule was enabled or report published.

Evidence: `/private/tmp/benchside-reporting-live-20261029/result.json` and
`synthetic-analysis-check.json`. This establishes the live importer/credential
connection, not a completed GitHub-hosted workflow run. That workflow deliberately
requires reviewed default-branch code and remains unmerged.

Later on 29 October, the user requested a demo that reaches GitHub before merging.
A separate synthetic-only branch job was added in reporting commit `22c42c5`.
[Its hosted run](https://github.com/LauraRyanSW/tools-science-works/actions/runs/40872156541)
passed in 26 seconds, including 29 reporting tests, one exact receipt-matched R2
read and creation of the private `benchside-synthetic-demo` artifact and job summary.
The downloaded artifact contains one synthetic gap, one store and one group,
matching the registered 29 October acceptance receipt. This does not claim to be
the presenter's future live submission or a run of the main production importer.
The original production/default-branch guard and test exclusions remain intact.
This additional demo path has no merge, schedule, R2 mutation or Vercel publication.

## Installed app checks and cloud-memory limitation

Claude's installed plugin and bundled runtime both reported 0.2.0. However,
[the upgrade test](https://claude.ai/chat/2d14f553-0f5e-4856-b678-b1b31154e6b0)
failed to restore the existing synthetic notebook. Its tool returned the state
inline; the model corrupted the long payload while copying it into execution.
`native.inspect` rejected the checksum. No new decision was saved, and the source
notebook remained at Docs revision 14. The unvalidated envelope reported snapshot
revision 8; this is not a successful restore.

A follow-up capability check found no exact document-to-file or file-to-document
bridge in that Claude session. Source guidance now requires an exact-transfer
capability for dependable native storage, labels inline-copy experiments honestly,
and stops automatic manual-copy retries without replacing the saved notebook.
This instruction improvement is not a working cloud-storage adapter, and has not
yet been repackaged into the installed plugin.
After the guidance changes, 100 existing native-storage, onboarding and role
instruction tests passed; the diff whitespace check also passed. These unit tests
do not establish a working host-to-runtime data bridge.

A separate [ChatGPT synthetic rehearsal](https://chatgpt.com/c/6ae32b8c-80d8-83ed-9c6b-893392d082db)
reported a successful native revision-1 save/readback in an owner-only Space, with
one decision and one open question. All sharing remained off; nothing was sent.
Fresh-chat restoration of this new rehearsal was not tested. A small success does
not resolve the larger Claude transfer failure.

Vercel's Science Works team lists the user's account as **Developer**. The production
Bugbear project and the reporting branch preview are visible. Some management
settings require higher permissions; no deployment or settings were changed.

## Deployment evidence

The compiled source was copied into the Cloudflare editor and compared with the
prepared bundle before deployment. The temporary test deployment was `7071025e`;
the final deployment removes only the synthetic catalog.

- Final bundle SHA-256:
  `9cf85e73dbe784c7a7d3330a4f1f6208d3de50b6cbddc87e36ebd2c921d89170`
- Test bundle SHA-256:
  `c1c9619ffcb47758a6908d8749b84fa1c67981a77e69bc6dc71b7c3c4cbd72c0`
- Local evidence: `/private/tmp/benchside-live-020-20261029/test-register.json`
  contains every accepted payload hash, receipt, object key and check result.
  The synthetic sent bodies and compiled bundles are in the same directory.

## Remaining before wider use

1. Resolve Claude's exact-data-transfer limitation before describing its cloud
   notebook route as dependable. Keep existing notebooks intact. A real connector
   bridge or an explicitly chosen durable local store avoids model transcription;
   splitting state into separately saved blocks would require a new atomic protocol.
2. Complete the hosted reporting run and the future Vercel report view after the
   relevant review/merge decisions. Do not relax the default-branch credential
   guard merely to demonstrate the pipeline from an unmerged branch.
3. Review and approve the outstanding PRs before merging/releasing. Reporting
   automation remains disabled, and the Vercel display is still future work.

Use the [interactive demo runbook](live-demo.md) for a fresh user-led demonstration.
The current evidence covers individual components, not a live end-to-end Vercel
display. The OpenAI package remains private, not a public Science Works directory
listing. No PR has been merged.
