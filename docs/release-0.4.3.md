# Benchside 0.4.3

Benchside can help in ordinary research conversations, save useful project
checkpoints without starting a role, and capture scientific workflow problems
beyond software. All eight roles use the selected project's shared memory.

## Changes

- A short first-use introduction explains private records and optional sharing.
  Skill-discovery guidance covers Codex, Claude, OpenCode and other capable hosts;
  implicit suggestions depend on the host and model, not installation alone.
- Record decisions, evidence and open questions without a role consultation.
  Decision rationale is optional; unstated reasons are never invented.
- Explore practical bottlenecks with a relevant follow-up at a natural pause.
  Reviewed workflow reports accept optional multiple labels, including `other`
  and custom labels, a de-identified excerpt, and supported workaround context.
  Suggested, tried and researcher-reported helpful workarounds remain distinct.
- Sharing reminders respect project scope, prior offers and existing consent.
  Pending reports can be redisplayed and retried exactly. Replacing changed
  content requires agreement; changes only to withheld metadata reuse the draft.
  Obsolete combined drafts can be identified without exposing another project.
- Claude private file-artifact notebooks use exact transfers and guarded saves.
  Concurrent chats must reread and reconcile conflicts rather than overwrite
  newer decisions. Older Claude Docs remain read-only; no automatic migration.
- Invalid scrubbed observations are withheld individually, with actionable
  diagnostics. Aggregate reports count custom labels without printing their text.
  Exported Markdown journals include their project title.

## Updating

**Update every app and agent sharing a Benchside store to 0.4.3 together.** This
applies to shared local folders as well as cloud notebooks. Older cloud runtimes
refuse the new native format; older local clients may omit new notebook-only
records from their views even though those records are intact.

For uv installs, run `uv tool upgrade benchside`. For pip installs, run
`python -m pip install --upgrade benchside` in the existing environment. Then
rerun the matching `bench setup` command to refresh the installed skill. An agent
can do this for the researcher. Source installs should update to tag `v0.4.3`,
refresh dependencies, and rerun setup.

For hosted apps, update the existing plugin or skill with the complete matching
0.4.3 archive. Do not overlay it on a source installation. Preserve the existing
private storage, projects and sharing preferences. Restart long-running hosts,
reopen the same project and verify recall before recording more work.

## Scope and verification

The runtime supports native notebook formats v5/v6 and `benchside.gaps.v4`.
The compatible receiver and reporting changes must be live before publication.
Local tests, clean distribution installs and all three archive layouts are
checked in CI. Earlier live Claude, ChatGPT and OpenCode acceptance evidence is
documented in the dated review reports; it is not a new live run of this release.

Private scientific records are not sent to Science Works. Workflow sharing
requires applicable consent and approval of the exact de-identified report.
Solution discovery remains a separate prototype and is not included. This is
a GitHub/PyPI release, not a new public plugin-directory listing.

### Production acceptance — 17 November 2026

- Receiver main `df150dd` deployed as Worker version
  `379dec95-29ee-4949-bf09-f9eaaa461465`, after 96 receiver tests and TypeScript
  validation passed. Existing EU bucket bindings and rate limits were retained.
- A fresh 0.4.3 wheel generated two explicitly synthetic v4 workflow observations.
  The preview excluded a separate private notebook decision. The report hash was
  registered in the reporting exclusion ledger before sending.
- The normal approved-send path received a matching production receipt; retrying
  the identical bytes returned `duplicate` with two observations and the same
  receipt timestamp.
- [Exact receipt verification](https://github.com/LauraRyanSW/tools-science-works/actions/runs/44167579511)
  read the stored object and checked its complete SHA-256. The synthetic GitHub
  report retained both complete gap objects, including labels, de-identified
  excerpt, workaround status and context. Access requires repository membership.
- [Normal reporting import](https://github.com/LauraRyanSW/tools-science-works/actions/runs/44167587923)
  succeeded against production storage using its incremental checkpoint. The
  synthetic report was absent from normal analysis. Daily reporting remains
  enabled at 06:17 UTC; aggregate updates still require review before publication.

The receipt SHA-256 is
`c75c751947dd0d24cdb44bb8f1f0901bab08271c64ceedaec2842503876c583b`.
No real research content was submitted for this test.
