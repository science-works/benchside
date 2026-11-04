# Portable onboarding checks — 4 November 2026

Candidate: 0.3.2, based on the unmerged installation-documentation work in PR #8.
These are synthetic compatibility checks, separate from the paper's evaluation.
They do not establish scientific accuracy across models or universal account support.

## Changes under test

- Check runtime execution, durable private memory and optional HTTPS separately.
- Stop unsupported setup honestly instead of inventing Markdown journals or
  repeatedly suggesting missing tools.
- Keep the existing generic installer and JSON launcher for other agent hosts.
- Add `connection.check`: a bounded GET of the official public study catalog,
  with no private store, participant IDs, consent changes or submitted records.
- Keep all consent, approved-payload, receipt and journal formats unchanged.

## Automated checks

491 tests passed on macOS arm64 / Python 3.14. Lint and persona compilation passed.
The three release archives passed the package smoke test: every role saves and
restores across fresh processes, native state transfers exactly, preferences
survive, and damaged dependencies are refused. These tests disable submission
endpoints; they are not cloud-account persistence tests.

The new connection test failed before implementation and passes for a valid
catalog, malformed content, HTTP 403, a malformed status line and a truncated
response body. It verifies GET-only transport, no
request body/participant parameters, a fixed official destination even with a
test-endpoint override, and no private/config files created on success or failure.
The first full-suite attempt hit the execution sandbox's localhost-bind limit;
the complete suite passed with the existing proxy test allowed to bind locally.

## Independent host: OpenCode 1.19.5 + hosted DeepSeek V4.1 Flash Free

Used an isolated OpenCode configuration, no inherited provider credentials,
the free model listed by OpenCode, and synthetic inputs only. The source
candidate was provided as a local checkout: this tests candidate installation,
not download/discovery of an unpublished GitHub release.

The agent installed its own environment and generic skill under the test
project's `.opencode/skills`, then invoked the installed launcher. Verified:

- Running version 0.3.2, project discovery and a remembered chosen store.
- A methods-clinic decision, methods record and unresolved question written
  through the actual runtime and returned by `recall`.
- All participation choices off, with the explicit decline remembered.
- Read-only collector reachability, with `submitted:false`.
- A separate agent session discovered the installed skill and restored project A.
  It created project B, verified B had no records, and verified A still had its
  own decision. The journal and preferences were also checked independently.

The test directory is temporary and deliberately synthetic; this does not
endorse a temporary folder as a researcher's permanent store. Normal setup must
choose a durable location outside Git. The host's test permissions initially
rejected some file writes because of path-pattern matching; those harness rules
were corrected for subsequent sessions. The agent completed setup through the
allowed launcher without altering Benchside's implementation or consent checks.

Scientific reasoning was mixed. Its initial response distinguished pre- from
post-extraction controls without inventing results. A follow-up correctly said
that detection interference does not rule out extraction loss, but then gave an
unreliable additional interpretation of discordant controls. This is a technical
compatibility result, not endorsement of this model as a scientific adviser.
No role or consent rule was weakened to make the model pass.

## Host with no execution or writable storage

A separate OpenCode session exposed only read/search/skill tools. The agent read
the packaged instructions, reported that runtime execution was unverified and
setup incomplete, and did not create a substitute journal or save consent. It
distinguished an installed package from a working journal and described further
discussion as unsaved. This controlled capability test does not replace the
recorded free ChatGPT account test.

## Local models

The first test used Qwen3 8B (`500a1f067a9f`) through Ollama 0.40.14, bound to
localhost with cloud features disabled. It failed the setup check: it guessed
nonexistent commands and a substitute JSON record instead of reading SETUP.md.
No Benchside records or submissions were created. This combination is not a
recommended onboarding route on this evidence.

Qwen3.5 9B installed the source runtime and reached the public catalog, but failed
the record-format check in the first run. It guessed `decision` instead of
`decide`, switched to legacy CLI records, and edited a JSONL event to add an
unsupported question field. The app project therefore did not have the requested
validated state. All affected files are isolated synthetic test files. This is
a failed compatibility test, even though parts of setup worked.

That failure prompted two small changes: the source installer now names the
installed SKILL.md and launcher directly, and the skill explicitly forbids
switching to legacy records or manually editing JSON/JSONL after an app error.
A fresh local-model run did not pass either: it tried to clone the public
release instead of using the supplied candidate, hit the harness's intentional
clone restriction, then ended without a usable setup result. It never reached
the new installer handoff or created records, so that run does not validate the
wording fix. These small-model combinations remain unverified for reliable use;
the runtime's portability is not a guarantee of agent instruction-following.

## Claude web: paid account, installed plugin update

Updated the existing private Benchside plugin from 0.3.1 to the 0.3.2 review
archive. This is an update and new-store test in an already configured paid
account, not evidence about a new/free Claude account.

The new synthetic notebook/project passed actual launcher execution, a guarded
file-transfer save, export/readback, and restored decision, methods record and
open critique. The read-only collector check returned `reachable:true` and
`submitted:false`. Participation was saved as declined and all options remained
off. No network settings changed and no contribution was sent.

A fresh Claude chat found the notebook by project name, exported its complete
state and restored it through the installed runtime. It recovered the decision,
question and off preferences. The tool output showed `changed:false`; notebook
state revision 1 and its checksum remained unchanged. Existing artifacts were
not modified by the setup workflow.

Observed limitations:

- Initial setup took about five minutes; fresh-chat restoration about three.
  Exact transfer worked, but document orchestration still needs many tool calls.
- Claude's read/export route attaches a private export blob to the document even
  though it does not change the journal snapshot. It is not literally side-effect
  free at the host's asset layer.
- An agent path typo created a stray directory in its disposable cloud workspace;
  a cleanup attempt was refused. This did not affect the saved notebook.
- Unresolved questions currently use the existing open-critique representation;
  the rendered text includes `claim`/`concern`. No schema change is included here.
- The UI showed the documents as “Only you”; the document tools themselves did
  not expose an access-list verification operation.

The scientific response separated observed facts from proposed checks and
distinguished extraction recovery from detection interference using a clean
reference, including the possibility that both problems coexist. It left the
researcher's exact decision intact and labelled the extra control as a recommendation.

This run tested GET reachability only. Earlier approved production submission
tests remain the evidence for POST delivery; no new production records were
created in this compatibility pass.

## Independent Claude code review and fixes

Claude reviewed the public patch and relevant transport/source files in a
separate chat. It reproduced the standard-library exception behaviour offline;
it did not run Benchside's suite. Its five findings were addressed:

1. Malformed HTTP status lines and truncated bodies escaped the catalog's
   infrastructure-error handler. Two added regressions failed first; catching
   `HTTPException` now preserves the clear no-submission/private-work message.
2. The generic qualification checklist could be mistaken for real-user setup.
   It now requires an isolated synthetic store, preserves real preferences and
   prohibits ordinary onboarding test submissions.
3. The capabilities-first heading obscured when storage writes are allowed.
   Non-writing inspection now comes first, then the researcher's storage choice,
   then an isolated synthetic write/readback probe.
4. The optional connection check now explicitly follows a request or opt-in.
   Guidance names the collector and normal request metadata rather than implying
   that contacting it sends no information.
5. Agents offering local storage with a hosted model must explain that prompts
   still go to that model's provider.

The review also asked to verify packaging, launcher forwarding and versioning
because its packet omitted some generated files. These are covered by the
package smoke tests and live launcher checks. The original failure-path gap in
the separate POST sender was noted as pre-existing and is outside this patch.
The README's unreleased-candidate wording must change when 0.3.2 is published.
