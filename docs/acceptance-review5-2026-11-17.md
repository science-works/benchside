# Review follow-up and beta checks — 17 November 2026

This follows Claude's review of PR #19 at `c45e757`. Nobody is using the new
features in production yet. The beta route is private Claude file-artifact memory,
ChatGPT Pages, or an explicitly chosen durable local/connected store. This work
does not merge, deploy or publicly release anything, and sends no contributions
to Science Works. The solution-discovery worktree is untouched.

## Findings and changes

| Claude finding | Resolution |
| --- | --- |
| 1. Pending reports cannot be recovered read-only | Add `sharing.drafts`, with the exact stored preview, ID, destination and digest. Current `sendable`/`problems` come from the same validation used by send. Reads neither create consent/identity nor send or save a notebook. Drafts with receipts are excluded. |
| 2. Docs recovery can create two active copies | Remove automatic migration and ongoing Docs recording from the beta instructions. Duplicate workspace IDs are copies; two unretired copies require reconciliation. A future explicit move must verify the destination and mark the source outside its encoded state. |
| 3. A new offer silently deletes a pending draft | Require an explicit choice before replacing a pending gaps draft. The runtime enforces the exact `replace_draft_ids`; a fresh offered preview cannot silently replace earlier work. Combining requires an explicitly selected union of observation IDs. |
| 4. Exact older-Docs recovery is not documented | Document exact-export read-only inspection, without claiming a completed migration or a verified export route in every account. Full migration is deferred: no real beta user needs it now. Old synthetic Docs remain intact. |
| 5. Guides disagree on fallback | Both now pause recording for an inaccessible existing project. Only an explicitly separate new project may start in a new store. |
| 6. Discovery can overlook old Docs | List blocked Docs candidates before registering a new project; never silently replace an inaccessible notebook. |
| 7. Main skill omits offered-ID selection | Add the `only=observation_ids` rule and the pending-draft check to the main skill. |
| 8. Withheld IDs expose unrelated projects | A scoped preview's omissions include only its selected IDs. |
| 9. Missing rationale requires a placeholder | `notebook.decide` accepts an omitted rationale, stores empty text and renders “Rationale not stated”. It does not invent a reason. Role-specific decision actions are unchanged. |
| 10. Duplicated schema walkers | Share one nested JSON/JSONL walker, including the offer-state gate. |

Existing consent, exact-content approval, redaction, destination and stale-state
checks remain enforced. A readiness result is not permission to send and does
not promise network connectivity. A failed or uncertain send must resume the
original draft before choosing a different selection; otherwise an altered
payload would not be an identical retry. No receiver wire format changes are
introduced by this follow-up.

## Automated checks

- Client: **661 tests passed**, including new tests first run against the missing
  behaviour. Coverage includes fresh native reads without writes, an uncertain
  receipt followed by an identical retry, invalid approval, changed consent,
  policy and destination, corrupt/sensitive payloads, changed usage demographics,
  pending-draft protection, project-scoped omissions, omitted rationale and JSONL
  feature detection.
- Lint, whitespace and generated-role checks passed.
- Companion receiver at `3dc54b3`: **96 tests passed** in its local Cloudflare
  emulator; TypeScript checking passed. No deployment.
- Companion reporting at `5dc1cfe`, importing this client checkout: **66 tests
  passed**. Its committed immutable client pin still needs updating to the final
  reviewed client commit before rollout.
- The actual pending payload produced by the installed OpenCode package was
  passed twice to the reporting importer locally. It produced one observation,
  preserved the entire gap/workaround/evidence in the private analysis, omitted
  contributor IDs there and kept problem text out of the public summary.

## Private package verification

Wrapper version: `0.4.3-review.5`. The bundled source version remains `0.4.2`;
identify this review build by its wheel hash, not that version string alone:

`752d52ffb066c5692eb36728e287eafe4f7b1d6f0b186d68eab1dd2f776772d1`

Wheel code and content match the working source exactly. All three ZIPs match
the generated skill and references; all bundled dependency hashes verify. A
clean launcher cache installed the bundled runtime offline and returned its
version successfully. The source-tree runtime manifest remains the published
main manifest; these private review packages carry their own verified wheel.

| Archive | SHA-256 |
| --- | --- |
| Portable plugin | `80f890e221375f018db034616f34dac6a45b5e6618ce958fededf79af928c2e5` |
| Claude plugin | `f82d74d5ddb9a46ba7f6d04124210dfaaf49beb135a50fa0408d420e2c6f9800` |
| Existing ChatGPT plugin update | `18bd2fe76c2dce9a624789938538b302c2d2a6b6000695427a05eac812d076e1` |

Archives and local synthetic evidence: `/tmp/benchside-pr19-review5/`.

## Installed OpenCode / OpenRouter

A fresh isolated local agent used `openrouter/deepseek/deepseek-v4.1-flash` with
the review.5 portable skill. It verified the runtime wheel, configured local
storage with a Markdown researcher view, and enabled workflow sharing only.
It saved “Book the synthetic microscope on Tuesday.” with no supplied reason;
the stored rationale is empty. It recorded a two-day microscope-access delay
and a cancellation list that helped once, then prepared a report for that item.

After recording a second reagent-delivery problem, a preview selecting only the
new item returned `pending_draft_exists`. The first draft remained unchanged.
The agent used `sharing.drafts` to recover it. A separate process independently
verified the exact digest, the empty rationale, no receipts and byte-identical
store files across the read-only checks. A shell JSON-display attempt initially
failed because of `echo` escaping; the agent corrected the display command.
That error did not change the stored payload.

- Draft: `9a447c80efbb48d597ad52051a2a61c2`
- Payload: `73412c599a5e78950e753527540f245965604bf6435ec32000f6637211a7ae70`
- No replacement, combining or send was approved or performed.

## Installed ChatGPT Work

The existing private plugin was updated in place to review.5, retaining its
identity, metadata and permissions. Manifest/reference readback confirmed the
update. A [fresh installed chat](https://chatgpt.com/c/6afc5fba-fa78-83eb-ac2b-241a7c9a5c42)
found the earlier synthetic notebook by title, without a supplied Page URL.
It verified the wheel hash, used `sharing.drafts`, displayed the full original
payload and recalled the saved decision. It opened no session and wrote no Page.

An independent Pages read was byte-identical to the previously saved review.4
notebook. Running the packaged runtime over that downloaded content confirmed
`changed:false`, revision 5 and the same pending report:

- Draft: `7070a0a761ac486f82b1149bbd5bd0ed`
- Payload: `8dfb14a5acd97bec3288dec6fd44a3af5e61fba1f6a94eb752951213b6e86cda`
- Notebook: `cd406f9ff8dbb6338d2e5d907a42417ded699789bfcc5fcce619072a93834ade`
- Readiness: `sendable:true`, no local problems. No approval or send.

## Claude and release gates

The review.5 Claude ZIP is prepared. Its installed check is **pending upload**:
Chrome's automated uploader reports missing file-URL permission, and the user
has been asked to upload it in the open update dialog. Claude still showed
review.4 at the last check. Do not describe review.5 as tested in Claude yet.

The earlier [review.4 live checks](acceptance-review4-apps-2026-11-17.md) proved
file-artifact discovery and both two-chat conflict cases, with all six decisions
retained. They are historical evidence for the unchanged version-pair protocol,
not a substitute for the updated-package check. Older Claude Docs export and
migration are not supported beta routes. No existing test notebook was migrated.

Before inviting beta testers: finish that Claude package check, review this
client and both companion PRs, update the reporting client pin, deploy compatible
receiver/reporting support, and verify one clearly synthetic production flow
under the agreed test-data exclusion. Then publish matching client packages.
All apps sharing one notebook must update together. These app checks use the
existing paid accounts and an OpenRouter-backed local agent; they do not establish
capabilities for every free account or model.
