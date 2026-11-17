# Installed review.4 acceptance checks — 17 November 2026

Client under test: PR #19, `1127d1e6147b8dcaf1dbb92251508540e6c6219f`.
Private plugin wrapper: `0.4.3-review.4`; bundled runtime reports `0.4.2`.
Wheel SHA-256:
`f83d28da9b4e0e4bd21aabd4647173b91a93b673e79021e646522f9354c4636b`.

These are synthetic installed-app checks. No production submission, receiver
deployment, merge or public release was performed. Existing research notebooks
and the separate solution-discovery worktree were not modified.

## OpenCode / OpenRouter

Two independent OpenCode sessions used `openrouter/deepseek/deepseek-v4.1-flash`
and the review.4 portable skill in an isolated temporary directory. The first
run verified the bundled wheel hash, created an organised local store with a
Markdown researcher view, and saved a verbatim decision and open question
without starting a research role. It recorded two researcher-reported workflow
problems (instrument access and purchase approval), preserving the limited
evidence that a cancellation list had helped once. Only broad workflow sharing
was enabled; all other participation choices remained off.

`sharing.check_in` offered exactly those two IDs; `sharing.preview` used `only`
with that set. The second fresh session restored the same records and consent.
Its first check-in returned `offer:false`. After recording one new booking-calendar
problem, check-in offered only the new ID, and the preview contained that item
alone. Earlier observations remained in the journal. The newer preview replaced
the earlier draft, as documented; it did not delete the underlying observations.

Independent file checks found one decision, one question and three observations,
a matching preview digest, and no receipt. The new preview SHA-256 was
`80b87fa3c4c4b596a70529d819cf38930b9e5d21949d2ff0e9b0464dbdbfcd6d`.
The researcher Markdown view contained the saved decision and question.

Sessions: `ses_e16af85c4ffeaRjvgBpl9zxWON` and
`ses_e16acffe1ffeDnfW1CHE89R0Vy`. Local evidence and response exports are in
`/tmp/benchside-app-review-20261117/`; the temporary store is a test fixture, not
a recommended durable research location. The agent's test wrapper isolated the
remembered-store configuration as well as the journal.

One recoverable interaction was observed: an initial decision call without a
rationale was refused. The agent retried with an explicit “not supplied” marker
instead of inventing a researcher motive. This is a usability consideration,
not a failed save or a new regression established by this test.

## ChatGPT Work

The existing private plugin was updated in place from review.2 to review.4,
preserving identity, metadata and permissions. The installed runtime hash matched.
The [creation chat](https://chatgpt.com/c/6afc3e78-7598-83eb-a44b-0b79e1105171)
created a new private notebook and registered project, saved the decision
“Book the synthetic microscope one week ahead.” with its supplied reason, and
kept the cancellation-list question open. It saved one broad workflow problem,
offered exactly its ID and prepared a preview restricted to that ID. Nothing
was approved or sent.

An independent Pages read found the actual saved `benchside.native.v6` notebook
at revision 3, and an independent bundled-runtime `native.inspect` and read-only
recall validated it and restored the exact decision, rationale and question.
The sharing roster had no shares or inherited access. Snapshot SHA-256:
`5fe286fe2a62369b6d09cff0e82ffd90718f53f59fdd213919cafedef19b6a13`.

The [fresh installed chat](https://chatgpt.com/c/6afc4006-41b0-83eb-a085-0865ba0f6182)
found the notebook by name, without a supplied URL or past chat transcript. It
restored the exact decision, rationale and question. Opening its session and
performing the check-in advanced private bookkeeping to revision 5; the check-in
returned `offer:false`. Consent remained unchanged and nothing was approved or
sent. An independent Pages read and snapshot comparison confirmed that the
research journal, consent ledger and existing draft were byte-identical to
revision 3. Final snapshot SHA-256:
`cd406f9ff8dbb6338d2e5d907a42417ded699789bfcc5fcce619072a93834ade`.

One usability limitation remains: the fresh agent could not redisplay the saved
preview through the documented read-only runtime actions. It correctly reported
that limitation and did not create a replacement preview. Independent inspection
confirmed the draft was still present and unchanged; this is a draft-discovery
gap, not lost content. A read-only pending-draft view is a possible follow-up.

## Claude

The uploaded plugin displayed review.4. A fresh chat automatically loaded the
installed skill and confirmed the wheel hash. Given only the synthetic notebook
and project names, it searched owner-scoped artifacts, found the correct file
artifact, checked privacy and file hashes, and restored the decision and open
question from `memory/state.md`. No prior chat transcript or artifact URL was
provided. The old notebook's state and artifact version remained unchanged.

The [first writer](https://claude.ai/chat/f39887cf-601d-4620-a7a4-642cd87ed2ba)
then created a separate owner-only two-chat fixture, saved A1 and refreshed its
journal with the paired version. A2 was prepared but deliberately not published.
A [second independent writer](https://claude.ai/chat/342e3d83-f7b0-4d64-9a0d-4431594c5555)
found that notebook by name, opened its own session,
saved B1 and refreshed the journal. It verified both A1 and B1. The first writer
then attempted its held A2 against the original version and received an actual
host HTTP 409. The expanded tool result explicitly said nothing was published
and identified `memory/state.md` as a would-overwrite conflict. The agent fetched
the current state, reran the original request with the same operation ID, saved
and confirmed the result, then refreshed the journal against its own save's
version. Final readback contained A1, B1 and A2 exactly once. Both chats used the
review.4 wheel. All participation remained off.

| Stale-state recovery step | Artifact version |
| --- | --- |
| A1 plus journal; A2 prepared and held | `1794915964-6600` |
| B1 authoritative save | `1794916442-5c2e` |
| B1 journal refresh / state reread after conflict | `1794916479-fc2c` |
| A2 save after rerun | `1794916745-8365` |
| A2 journal refresh and verified final read | `1794916758-ceb2` |

The narrower journal-interleaving check also passed. A saved and confirmed A3,
then deliberately held its journal refresh. B reread the notebook, saved B2 and
refreshed the journal. A attempted its held journal patch using its own earlier
state/version pair and received a second actual HTTP 409; this time the host
identified the journal as would-overwrite and also listed the changed state file.
A fetched the current state and version together and regenerated the journal.
B's current journal already matched that generated view, so A discarded the
obsolete journal rather than writing it. A then saved A4 from the fresh state,
confirmed the fetched readback, and refreshed the journal against that save's
version. This exercises the specific lost-update sequence from the review,
using separate chats and the installed guidance rather than a two-cache simulation.

| Journal-interleaving step | Artifact version |
| --- | --- |
| A3 confirmed; its journal deliberately held | `1794916860-5480` |
| B2 state save | `1794916977-0247` |
| B2 journal / fresh pair after A's journal conflict | `1794917008-f96e` |
| A4 save from the fresh state | `1794917138-0dab` |
| Final journal and readback | `1794917152-fc97` |

The final authoritative notebook was revision 6 and held these six decisions
exactly once, with no duplicate IDs:

1. Reserve the synthetic microscope on Tuesday.
2. Ask the synthetic core facility about spare slots.
3. Use the synthetic cancellation list for spare slots.
4. Keep a synthetic backup booking.
5. Confirm the synthetic equipment handover.
6. Review the synthetic booking plan on Friday.

The final journal is a recent-history view: it explicitly says “Showing 5 of 6
decisions”. The oldest decision remains in authoritative storage and full recall;
it was not lost. One local journal-comparison command exited with code 1 during
reconciliation; regenerating the standard view then matched the stored journal,
and the subsequent state save and readback passed. Neither conflict caused an
unguarded overwrite or a submission. The original discovery fixture remained
unchanged. Both stale-write rejections were inspected in the expanded host tool
results, not inferred solely from the assistant's summary.

These checks use ordinary private file artifacts. They do not establish that
the older Claude Docs exact-export route has recovered.

## Scope and next review

The memory and sharing-reminder checks passed on the installed review.4 build.
No runtime or instruction changes were needed during these tests. The prior
649-test client suite remains the automated baseline; it was not rerun for this
documentation-only update. This check did not deploy or exercise the production
receiver or reporting pipeline.

The app checks used the existing paid ChatGPT Work and Claude accounts. They do
not establish free-tier capabilities or reliability across every model. OpenCode
used a local agent/runtime with hosted OpenRouter inference, not inference on the
Mac. The Claude version-pair discipline is host/agent guidance enforced through
the host's conditional-write mechanism; passing these interleavings is not a
guarantee that every possible agent will always follow it.

Follow-up usability candidates are a read-only pending-draft view and allowing
an explicitly unknown decision rationale without requiring a placeholder. Older
Claude Docs notebooks still need a working exact-transfer route or a separately
verified migration; these tests did not migrate them. The branch remains for
review, with no merge or public release.
