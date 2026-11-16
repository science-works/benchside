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
Automatic redaction cannot identify every confidential fact; model review and
the researcher's exact-payload review remain necessary.

## Installed-app acceptance checks

The user's private ChatGPT and Claude plugins and an isolated OpenCode skill
installation were updated for testing. Review wrappers use `0.4.3-review.2`; the bundled runtime
still reports the unreleased source version `0.4.2`. The final review wheel SHA-256
is `fefea55bdae159b9da5de59d40e1f3f0217bf9162c70969239a06c6bd95446e7`.
This is not a public release or a production receiver deployment.

ChatGPT Work (GPT-6.1 Sol, the existing paid account) saved a synthetic decision,
its exact rationale and an unresolved question without starting a role. The
private Pages notebook was independently read and unpacked, with owner-only
access and no collaborators. A fresh chat, given only the notebook link, restored
the exact records, all-off sharing preferences and absence of an open consultation.
It then opened the supervisor role without requiring a hypothesis and prepared
a general equipment/coordination report with two labels, a verbatim safe excerpt,
`basis:researcher_reported` and `workaround_status:researcher_tried`. The uncertain
benefit remained explicit. The stored v4 preview matched the displayed content;
it was not approved or sent. Deferring in the same chat left the draft pending
without another sharing prompt or an invented decision.

OpenCode executed the bundled skill against a separate synthetic local store,
saved the same decision/question outside a role and produced ODT plus Markdown
reading copies. The free DeepSeek V4.1 Flash model reached its quota before the
fresh-session check, so that check used the user's already-connected OpenRouter
DeepSeek V4.1 Flash provider. Fresh recall recovered the exact records and sharing
state. This is local agent execution with a hosted model, not local model inference.

The first OpenCode supervisor/report run exposed an instruction weakness:
it put `basis` inside `gap`, removed that provenance after validation failed,
and copied an example's unreported impact (repeated preparation). Nothing was
sent. The guide now gives a complete request with top-level `basis`, explains
how to correct its placement without dropping provenance, removes that example
impact and explicitly forbids importing example facts or likely consequences.
A new session and project using the rebuilt package passed: correct provenance
on the first gap call, multiple labels, no invented impact/hypothesis/benefit,
an unapproved preview with a matching digest, and valid ODT/Markdown copies.
The final installed wheel hash and stored draft were independently checked.

ChatGPT also passed a fresh test of the rebuilt package: the manifest hash matched,
a second project saved and restored at native revision 5, and its stored preview
kept the correct provenance and uncertain workaround benefit without adding impact
claims. The earlier project's complete journal was independently compared with
revision 3 and was byte-identical. The app's automatic approval check initially
refused the shared-notebook save, interpreting it as changing the earlier project;
the agent supplied an unchanged-recall comparison and completed the guarded save.
This is a host approval friction point, not a relaxed save or consent guard.

### Claude: research/report behaviour passed; fresh-chat memory blocked

The first attempted upload left the old public 0.4.2 package installed. After the
user uploaded the distinctly named review ZIP, the plugin displayed
`0.4.3-review.2` and its recomputed wheel hash matched the review hash above.
The following checks used that build with Opus 5.5 Extra in the existing paid
Claude account, not the earlier installation.

In a separate synthetic, owner-only Claude Docs notebook, the agent saved the
decision “Check microscope availability before preparing materials.”, rationale
“Two bookings were cancelled after preparation.” and open question “Who can
confirm instrument availability the day before?”. This used notebook actions
outside a role, with every sharing option off. Initial setup took approximately
seven minutes, including tool inspection and the transfer investigation.

The write route uploaded runtime-produced files, checked upload hashes and used
revision/hash-guarded replacements. However, the current
`mcp__claude-artifacts__read_asset` returned inline text, not the file expected by
the earlier guide. The agent reconstructed expected exports from its existing
runtime files and compared their digests with the server export digests before
calling `native.confirm`. Those matches support byte-equivalent writes but are
**not an actual readback into the runtime or proof of fresh-chat restoration**.

A fresh chat received only the notebook link. It found the private document,
revision and state block but could not retrieve the content through an exact
file bridge. It stopped without guessing saved records, changing the document,
or retrying a manual copy. Further inspection of the actual tools found no
programmatic result-to-code bridge or supported asset download-to-file operation
for these Docs. The tool that can save ordinary artifact files refused Docs
created from a type. Upload support alone is therefore insufficient in this
session. This is an outstanding host/storage compatibility issue, not a complete
Claude acceptance pass.

Separately, the original chat continued from its existing runtime files only
after a current server export digest matched them. The research supervisor:

- Started without a hypothesis, preserving the earlier decision/open question.
- Recorded a general microscope-booking problem with `equipment_access` and
  `coordination` labels and `basis:researcher_reported`.
- Replaced the synthetic person and confidential-project names with `[redacted]`
  in the excerpt, omitting them from the general description.
- Marked a newly tried workaround as `researcher_tried`, with benefit explicitly
  unknown, while preserving the earlier private planned-step note.
- Enabled only explicitly chosen `all_workflow` sharing in this synthetic store,
  and prepared only the latest account as an unapproved v4 draft. Other channels
  stayed off. The preview contained no invented impact or successful outcome.
- Asked one relevant cause question ending “or something else?”. After deferral,
  it did not repeat the sharing offer, approve the draft or send anything.

The final notebook was at internal revision 4 / Claude Doc revision 6, with the
same digest-only qualification. The supervisor sitting remained open because a
converged close requires a decision from that sitting; the agent neither invented
one nor labelled a pause as abandonment. This is consistent with current rules,
but the distinction between pausing and concluding remains a usability consideration.

Private evidence is in the
[Claude acceptance chat](https://claude.ai/chat/5ff3b82e-c26d-4869-af2d-8886fdc36834)
and its synthetic notebook. The tests did not change existing research projects,
account permissions or network settings.

The follow-up source guidance now checks the exact read bridge before notebook
creation, describes the observed Claude tool difference, and explicitly refuses
to treat a reconstructed candidate as fetched readback. It also documents native
schema v5. These instruction-only changes were generated into the source plugin
and passed the three role-instruction checks and whitespace checks. They are
**later than the installed review.2 package** and have not been retested as an
installed build; they do not supply the missing host capability. A supported
exact transfer or an independently verified alternative store is needed before
calling this Claude Docs route dependable.

Remaining limits and follow-up:

- Claude Docs fresh-chat restore remains blocked in this account's current tool
  surface. Same-chat writes and previews do not remove that limitation. A revised
  package should retain the new capability check and must pass fresh-chat restore
  on its selected store before being recommended for persistent research records.
- ChatGPT's intermediate progress blocks sometimes displayed “This response
  couldn't load”; both final replies and independent stored-state checks succeeded.
- OpenCode surfaced a stale `0.3.1` label in the parent test project's AGENTS.md.
  The actual manifest and recomputed wheel hash correctly identified the build;
  the parent test setup was not modified.
- These are focused installed-app checks, not a new live evaluation of every role,
  all account tiers or model providers. The eight-role checks remain automated.
- No v4 payload was sent to production. Receipt/storage/import remain covered by
  the receiver/reporting emulator tests until those companion PRs are deployed.

After the documentation fix, 636 client tests passed under the sandbox. The sole
remaining test needed to bind a localhost proxy; it passed when rerun with that
permission (637 total). The three generated-role instruction checks also passed.

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
