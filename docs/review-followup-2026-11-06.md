# Follow-up to Claude's 6 November review

Candidate: **0.4.1**, on `codex/review-fixes-17-27`, based on PR #11 at
`09bccb2`. PR #11 was still open when this work started; no merge, public release
or receiver deployment was performed as part of these fixes.

The review covered released 0.4.0 code and found no defect in PR #11's role-quality
changes. The fixes below preserve consent, exact approval, redaction, destination,
receipt, replay and guarded-write protections.

## Findings and changes

| Finding | Disposition |
| --- | --- |
| 17: CLI export crashes unless both formats are selected | Fixed. Print only refreshed files, and explicitly identify older reading copies that were retained but not refreshed. ODT, Markdown and both formats are covered. |
| 18: survey text bypasses sensitive-text checks | Will chose **require an edited answer**. Scan exact text before drafting and immediately before sending, including old pending drafts. Flagged answers cannot be overridden by another approval. No automatic rewriting; ordinary answers still use the original study agreement. |
| 19: uppercase question IDs cannot be answered | Fixed. Display the original ID in the question heading's metadata; `bench answer` now says an answer was saved. |
| 20: old readers misdiagnose newer research values as damage | New saves containing discipline lists or `pi-hypothesis` use native schema v4. Current readers accept v4. Existing 0.4.0 notebooks that already put those values under v1-v3 remain readable and upgrade on their next save. |
| 21: hooks can write during folder migration | New hooks and migration share a dedicated layout lock, independent of long sharing transactions. Migration also fingerprints the source before and after copying and refuses a detected concurrent change. The stop-other-agents requirement remains, particularly for older clients without this lock. |
| 22: optional history eventually fills its 48 KiB allowance | Will chose **retain history**. No automatic weekly compaction or summary. The host guidance and capacity error explain the pause and offer larger private storage or discussion of an explicitly approved archive/summary plan. Automated safe archival is not implemented. |
| 23: repeated readable-copy regeneration | Derived copies refresh once per changed project at the end of each app/CLI command, including after a later step fails. Direct journal callers retain their immediate refresh. A failed refresh still leaves the durable research save successful and reports a warning. |
| 24: exact optional-feature/schema equality is brittle | Readers accept a supported newer envelope without requiring every optional feature to be present. Context under v1/v2 and replay checkpoints under v1 remain refused. |
| 25: malformed contributor identity raises raw exceptions | Invalid JSON/types/missing keys and read errors produce the preserve-and-repair domain error. The identity file is never silently replaced. |
| 26: blank survey text counts as an answer | Client checks reject empty/whitespace-only answers before creating a draft or sending an old draft; skipped questions must be omitted. Historical drafts remain readable. Matching receiver enforcement is a separate future deployment. |
| 27: duplicated atomic writer | JSON and readable files use one durable byte writer, retaining restrictive file permissions, symlink refusal, fsync, atomic replacement and temporary-file cleanup. |

## Verification

- Added failing regression cases before the confirmed fixes, and reproduced the
  migration race, malformed identity, blank/sensitive survey and schema concerns
  with temporary synthetic state. The multi-event app and CLI reproductions
  each called export twice before the batching fix and once afterward.
- **577 tests passed on Python 3.11 and 3.14**, including all metascience tests.
- Ruff and compiled-role freshness checks passed.
- Executed the actual native-reader source from the v0.3.1 tag against a new v4
  snapshot: it returns `native_update_required`, not a corruption error.
- Regression checks cover preserving older stored survey drafts while refusing
  unsafe/blank sends, readable-export failure after a successful save, migration
  changes after an earlier directory was copied, layout-lock ownership, and
  atomic-write failure/symlink handling.
- Rebuilt the Python wheel and all three app archives from source and pinned
  dependency wheels. All three archives passed cold-install smoke checks on
  Python 3.11 and 3.14: all eight roles save/resume/conclude using both local
  storage and native snapshots, readable ODT/Markdown views, metascience restore,
  batched setup/replay, and damaged dependency refusal. Collector endpoints were
  disabled throughout.
- An independent agent review found no actionable new correctness, privacy,
  compatibility or concurrency regression; its 194 targeted tests passed.

All records and test submissions here were synthetic and local. No production
collector request or live account installation was part of this regression run.

## Follow-up: linked Claude Code settings

The shared atomic writer already refused symlinks, but legacy `bench init` could
create `.bench/config.yaml` or change the storage preference before reaching that
refusal. It now checks the settings shortcut before those writes. The error names
the file and its destination and explains default setup and manual hook options;
it does not write through or replace the link. Default setup leaves unrelated
linked settings alone, and also checks early when it must remove old Benchside
hooks. Five regression cases cover absolute/relative/dangling links, old-hook
removal, and successful default shared-skill installation with unrelated settings.
The existing general atomic-writer symlink refusal remains unchanged.
The four refusal cases reproduced the partial-setup problem before the fix; all
**582 tests now pass on Python 3.11 and 3.14**. Ruff and compiled-role checks pass.

## Limits and remaining work

- Batching avoids repeated exports within a command. A single-event command
  still regenerates the complete reading copy once; this does not make very
  large journals constant-time. Incremental rendering/archival remains future
  work, rather than adding a cache with another consistency contract now.
- The text scanner is conservative: it flags email/credential/path/URL patterns,
  including harmless public URLs, and cannot recognise all names, sample IDs or
  private findings. Researcher-facing guidance must retain that limitation.
- A new package cannot stop an older package from misreading an already-saved
  0.4.0 notebook before that notebook is upgraded. Update all apps that share it;
  v4 protects subsequent saves from silent use by older readers.
- Receiver blank-text validation needs its own review/deployment. Wire formats
  and production infrastructure are unchanged by this client patch.
- Merge/release and installed-host acceptance remain separate steps. PyPI/uv and
  public-directory publishing are recorded in [future distribution](distribution-roadmap.md).
