# Final-review follow-up — 17 November 2026

Follow-up to Claude's review of client PR #19 at `4a6a788`, receiver PR #4 at
`3dc54b3`, and reporting PR #5 at `5dc1cfe`. Nothing in this follow-up authorizes
a merge, deployment, production submission or public release.

## Changes

- **Project separation:** pending workflow reports are scoped by their original
  observations' project ownership, without changing their payload or approval
  digest. A pending report in B no longer blocks a new report in A. Preparing a
  replacement deletes only the explicitly agreed replacement drafts; B remains
  byte-for-byte intact. A repeated identical preview retains its original ID.
- **Scoped app API:** `sharing.drafts` and gap `sharing.preview` require the
  current `project_id`, or `all_projects:true` for an explicitly requested broader
  review. Omitting scope refuses instead of displaying another project's report.
  An older mixed-project draft stays intact and requires an explicit all-project
  review. Feedback and usage remain store-wide channels. Selected-conversation
  candidates use `project_id:"reporting-ledger"` plus explicit candidate IDs.
- **CLI recovery:** `bench share drafts` redisplays exact pending reports;
  `bench share preview --replace-draft <id>` supports an explicitly agreed
  replacement (repeat for each batch). Both default to the current project and
  accept `--project` or `--all-projects`.
- **Rationale:** role and notebook decisions accept omitted/null reasons without
  inventing one. CLI `--because` is optional. CLI views and the session hook say
  “Rationale not stated” when no reason was supplied; non-text reasons still fail.
- **Read-only batches:** `sharing.drafts`, `sharing.status` and `sharing.history`
  can run together in `native.batch` without changing the notebook. Previews and
  sends remain excluded from batches, and all existing approval/consent checks
  still apply.
- **Blank workflow text:** BOM/whitespace-only descriptions, excerpts, labels and
  status-bearing workarounds are refused before submission, matching the
  receiver's nonblank check. Valid text is not rewritten by this validation.
- **Update guidance:** every app sharing local storage must update and restart,
  as well as apps sharing cloud notebooks. Older 0.4.2 apps may omit new
  notebook-only records from their views even though the records remain intact.
- **Reporting regression:** companion tests now assert `custom_label` grouping,
  no custom label text in aggregate JSON/Markdown, preservation of full reviewed
  wording in private evidence rows, and exclusion of legacy gaps from the
  unlabelled-workflow count. Both new checks fail against the old `b60c0a2` pin.

## Verification

- Client: **673 tests pass** on Python 3.14; lint passes using CI's command;
  `bench compile --check` reports eight unchanged roles. New regressions were
  reproduced before the fixes. The full run uses a loopback-only HTTP mock;
  no Science Works submission is made.
- Reporting: **67 tests pass** against this client. Against the old pin, the two
  new grouping/count checks fail as expected. The receiver was not modified;
  its prior 96-test/typecheck result is not a new deployment or live-storage test.
- Native integration: two projects can retain separate pending reports; a fresh
  read-only batch returns only A's exact report without modifying the notebook.
  B's report survives A's replacement. An older mixed draft is preserved and
  cannot be exposed through A's scoped list.
- Private package wrapper: `0.4.3-review.6`; bundled source version remains
  `0.4.2`, so identify this candidate by the wheel hash below. All 150 packaged
  Python source files and 19 generated skill files match source; dependency
  hashes verify against the unchanged dependency manifest.
- All three ZIP layouts pass offline cold-install checks: all eight roles save,
  restore and conclude in fresh local/native processes; ODT/Markdown exports,
  selected-conversation state, setup replay and damaged-dependency rejection
  pass. All submission endpoints are disabled during these checks.

Wheel SHA-256: `0d54b38dc3e0a69c271b7dcdd511a343c49e20146c679149509856c407eb08df`.
Private artifacts and local logs are in `/tmp/benchside-pr19-review6/`.

## Remaining release sequence

The reporting PR must use the corrected immutable client, then be pinned to the
final merged `main` commit after #19 merges (particularly if squash merging).
The old reporting importer aborts on v4 objects, so merge/run the updated
reporting path before deploying the receiver that accepts them. Then perform
one registered synthetic production submission plus a reporting run, and only
then publish matching client packages.

The review.5 installed Claude, ChatGPT and OpenCode evidence remains in the
acceptance documents. It is not a live-app test of review.6: this follow-up's new
project-scope instructions still need a focused installed-app check before beta
invitations. No receiver deployment or real-bucket import was performed here.
