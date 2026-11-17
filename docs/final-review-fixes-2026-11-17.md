# Final review fixes — 17 November 2026

Follow-up to Claude's final review of client PR #19 at `8bfc344`, receiver PR #4
at `3dc54b3`, and reporting PR #5 at `81470f7`. All changes here are on the client
review branch. Nothing was merged, deployed, published or sent to Science Works.

## Confirmed findings and fixes

1. **Limited consent and project previews.** Reproduced the refusal when a project
   contained both a consented legacy observation and an uncovered workflow problem.
   Automatic project selection now includes only observations covered by the active
   grant. Uncovered current-project IDs appear in local `withheld` metadata, never
   in the outgoing payload. Other projects' IDs/content stay absent. An explicit
   selection of unconsented, unknown, shared or other-project IDs remains refused.
   CLI previews now display withheld IDs as well as existing redaction findings.

2. **Obsolete combined-project drafts.** Reproduced the blocked recovery after
   upgrading consent from a legacy grant to `all_workflow`. A replacement may now
   retire a combined draft only if its grant is no longer current, its exact ID is
   explicitly named, and the review scope overlaps its projects. This permits a
   new per-project report without copying another project's material into it.
   Original observations and unrelated drafts remain intact. No replacement is
   implicit, and replacement is never send approval. Combined drafts under the
   current grant remain protected, including when some other check (destination
   or payload digest) makes them unsendable.

3. **CLI sharing instructions.** The legacy CLI skill includes `workflow_problem`
   among choices and explains the broader scientific workflow scope. It documents
   `bench share drafts`, repeatable `--replace-draft`, default project scope,
   `--project`, `--all-projects`, withheld items and obsolete-draft recovery. It
   explicitly forbids silently expanding an older grant. The replacement error
   now names both the app field and the actual CLI flag.

No consent rule, send-approval check, destination guard, redaction rule, storage
format or wire format changed. Receiver/reporting code did not need modification.

## Verification

- Ran both embedded review reproductions before fixing. They produced the stated
  limited-consent refusal and the three combined-draft refusals.
- Added regression coverage first: seven cases failed before the fixes. Added
  negative checks preserve active-grant combined drafts even when their destination
  or digest is invalid, reject incorrect replacement IDs, and prevent cross-project
  IDs/content entering preview or withheld output.
- Focused application/CLI pending-report tests: **33 pass**.
- Full suite: **687 pass on Python 3.14.0** and **687 pass on Python 3.11.14**.
  Tests use temporary stores; network behavior uses mocks or a loopback server.
- CI-style lint, `bench compile --check` (eight roles unchanged), generated app
  source comparison and `git diff --check` pass.
- Rebuilt private candidate **0.4.3-review.7**. Its bundled Python source version
  remains 0.4.2; identify it by wheel SHA-256
  `9e2b4f65f127cd04e3b387c47c609be1a1b41f27dd4c4db21dc965ff9ab3e416`.
  All Python sources and the CLI sharing skill in that wheel match source.
  App guides were regenerated from source, not edited as generated copies.
- All three archive layouts pass offline cold-install smoke checks: eight roles
  save, restore and conclude in local and native-memory processes; ODT/Markdown
  exports, sampled-activity restoration, batched setup/replay and damaged-dependency
  rejection pass. All collector endpoints were disabled. The initial sandboxed
  archive runs hit a macOS uv system-configuration error; the same offline checks
  passed outside that sandbox without changing packages or downloading dependencies.

The original CLI reproduction contains only an uncovered workflow problem and
explicitly grants the five old kinds. That exact grant still cannot preview the
problem: it now explains that one observation is withheld by current consent.
Automatically adding permission would be incorrect. The mixed-consent CLI
regression previews its permitted item, and the updated guide's opt-in list
successfully previews a workflow problem when the researcher chooses that kind.

Local logs/reproductions: `/tmp/benchside-final-review-fixes-20261117/`.
Private packages and archive check logs: `/tmp/benchside-pr19-review7/`.

## Release boundary

These are local runtime/instruction fixes; no host storage protocol changed.
The existing review.6 live Claude/ChatGPT/OpenCode evidence is retained as evidence
for that candidate, not relabelled as a live review.7 run. No new account upload
or live submission occurred here. The final reviewed candidate still needs the
registered synthetic production submission after the receiver/reporting rollout.

Merge order remains: reviewed client; repin reporting to the final merged main
SHA, merge and verify its import; merge/deploy receiver; register and send the
approved synthetic test and verify its reporting exclusion; publish packages.
Those steps are not authorized by this fixes-only follow-up.

## Small follow-up after the `3197894` re-review

Both remaining usability findings were reproduced with regression tests before
fixing them (three new cases failed):

- Re-previewing after recording a new unconsented item now reuses the existing
  draft ID and refreshes its local withheld list. The payload, digest, destination,
  grant, included observation IDs and redaction findings must still match exactly.
  Changed outgoing content still requires an explicit replacement; consent is not
  expanded and another project's withheld items remain invisible.
- A combined-report refusal now gives just the blocking draft ID, without project
  IDs, observation IDs or report content. When its grant is obsolete, the message
  explains exact-ID replacement after agreement; no all-project payload review is
  needed just to discover that ID. A combined draft with current consent remains
  protected. App and CLI instructions describe both cases consistently.

Verification: **36 focused pending-report tests** and **690 full-suite tests**
pass on Python 3.14.0. CI-style lint, role compilation (eight unchanged), generated
app instructions and whitespace checks pass. Tests use temporary stores and mock
collectors; no production data was sent. No cloud app was reinstalled or newly
tested for these two local runtime/message changes. Earlier live acceptance and
review.7 archive evidence above retain their original scope. Nothing was merged,
deployed or published, and the solution-discovery worktree was left untouched.
