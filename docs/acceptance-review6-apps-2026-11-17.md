# Installed-app acceptance — review.6, 17 November 2026

Focused follow-up to the project-scope, replacement, optional-rationale and
read-only-batch fixes in PR #19. Tested code: `f1421964accab19265e1adda57b345cd384cc678`.
No merge, receiver deployment, public package publication or Science Works
submission is part of this test. Every record and problem below is synthetic.

## Candidate and isolation

- Private wrapper version: **0.4.3-review.6**. The bundled source package still
  reports **0.4.2**; its identity is the wheel SHA-256
  `0d54b38dc3e0a69c271b7dcdd511a343c49e20146c679149509856c407eb08df`.
- Claude was updated by the user. ChatGPT was updated in place, preserving the
  existing private plugin identity and account metadata. Both installed apps
  measured the expected wheel hash before testing.
- Each host used a new notebook/store containing separate projects A and B.
  Only workflow sharing, with `all_workflow` scope, was enabled in these stores.
  Other participation stayed off. Reports remained unapproved and unsent.
- OpenCode used an isolated installed skill and local store at
  `/tmp/benchside-pr19-review6/opencode`, with visible session output. The model
  was `openrouter/deepseek/deepseek-v4.1-flash`; this tests an OpenRouter-hosted
  model with local execution/storage, not inference on the Mac.
- Existing notebooks and the solution-discovery worktree were not modified.

## Focused scenario

1. In B, record a three-day reagent delivery delay and prepare an unsent report.
2. In A, save “Book the synthetic microscope on Tuesday.” without a rationale;
   record a two-day microscope-access delay and an explicitly researcher-reported
   workaround that helped once. Prepare A's report while B remains pending.
3. Confirm A's scoped draft list contains only A's report.
4. Add a second A problem: manually copying booking emails each week. Attempt
   a new preview without replacement permission. Expect `pending_draft_exists`
   and preservation of the original A draft.
5. Explicitly authorize replacing only A's draft with both A problems. Confirm
   B's ID, destination, payload bytes and digest are unchanged.
6. Restore stored records and inspect pending reports/history. In cloud apps,
   run scoped draft/status/history calls in a read-only native batch and check
   that the saved notebook is unchanged. Do not perform a connection check/send.

## Results

| Check | ChatGPT Work | Claude web | OpenCode |
| --- | --- | --- | --- |
| Correct installed runtime hash | Pass | Pass | Pass |
| Both projects can hold separate pending reports | Pass | Pass | Pass |
| A-scoped list excludes B's report | Pass | Pass | Pass |
| Unapproved replacement refused; A retained | Pass | Pass | Pass |
| Explicit replacement changes only A; B byte-identical | Pass | Pass | Pass |
| Decision restored verbatim; rationale empty | Pass | Pass | Pass |
| Read-only native batch leaves notebook unchanged | Pass | Pass | Not applicable to local storage |
| Empty submission history | Pass | Pass | Pass |
| Fresh chat discovers notebook from name alone | Pass | Pass | Not the local-storage discovery route |

These are project-scoped application views within one private store, not
separate host-account permission boundaries.

### ChatGPT

- [Creation and replacement test](https://chatgpt.com/c/6afc8624-5868-83ed-9d17-f285e33b54bb)
- [Independent fresh-chat restore](https://chatgpt.com/c/6afc879a-43bc-83ed-ad3d-6f55c5d65e38)
- [Synthetic notebook](https://chatgpt.com/space/page_0788de720fa481918bc4307dfed232e9)
- Model: GPT-6.1 Sol, Light; ChatGPT Work.
- Workspace `15339f968e7f48818ba65c7e1ce89df7`; notebook revision **6**, schema v5.
- Snapshot SHA: `2b7f961e0f2f45fd68f13017c659ed314059de7d58a4d771060c243da50f5e49`.
- A draft `751938c24b604245b16166d499e52e4d`, payload SHA
  `5ee4a12258286ec64078c1e84e672086ecd753c44b129ec0261b7651fc5df57d`.
- B draft `7dcd753ada4a48699cb798275d2dfa17`, payload SHA
  `2849c34b914c2704df37f56222de139bd868afa43e44571fc3c08ecaca72a0b0`.

The second chat received only the notebook/project names, not a URL, ID, saved
decision or expected draft digest. It found the notebook, restored the decision
and redisplayed A's exact two-item pending payload. It did not display B's report.
An independent Pages connector read was validated locally with `native.unpack`:
the envelope checksum, both payload digests, exact decision and empty rationale
were confirmed. A second connector read after restore matched the first complete
notebook Markdown byte-for-byte; Page sequence remained 6. No receipt exists.

### Claude

- [Creation and replacement test](https://claude.ai/chat/8bdbb804-c690-4f8c-a4e5-73f720151d2d)
- [Independent fresh-chat restore](https://claude.ai/chat/549a1ab8-32ab-47f0-b86e-6612678a5224)
- Model: Opus 5.5, Extra.
- Private file artifact `a44ac3fb-8901-4b2d-acab-fc68f09781af`, owner-only.
- Workspace `91ad6cc6bdf848989b251e30f5e6223c`; final notebook revision **6**, v5.
- Snapshot SHA: `3fc73a84b6694c5d26a66bc0924c01d216787294b74ed65499d6402a28c68c77`.
- State file SHA: `df1326cfa8adc32df0ee9f11bb8a19a9719d22a3b5632c6668f946b617c45e99`.
- Artifact version after notebook and readable-journal writes: `1794934708-87a5`.
- A draft `dd6a132e0807420db13fb7905be0ca58`, payload SHA
  `a7df35dc0a9a3a640f0e434706c23fdea46bf364e94998f87e09d3fe889989df`.
- B draft `98bbc21d15d94f4883d847baead1af24`, payload SHA
  `f3581e54dc9aec5d3ab10936a3f67bde2bd2b78098f239ffa5885ce4706a612e`.

The installed agent used guarded artifact writes and file readback for revisions
0–6. Journal refreshes used the version paired with the saved notebook; the state
file was unchanged by journal refresh. Final read-only batching reported unchanged
state/artifact version and empty history. These observations are from the live
agent's tool execution and results, not an independent connector download here.
The earlier two-writer conflict test is not repeated by this focused test.

The second chat searched the exact notebook name and found one match, without
being given the artifact URL, workspace/project IDs, decision or expected hashes.
It downloaded the 4,336-byte state file and checked its host-provided hash, then
restored A and redisplayed only A's two-item report. The pending payload digest
matched the creation test. Its read-only batch returned `changed:false`; a second
artifact read retained version `1794934708-87a5`, all four file hashes and identical
state bytes. It inspected only registered metadata for B, without recalling B's
records or opening its journal. The fresh chat did not read unrelated notebooks
for duplicate-workspace detection because it performed no write.

### OpenCode

- Visible session: `ses_e1592b559ffeGe6Qy5KCdqSwRq`, titled
  **Benchside review.6 project separation**.
- A project `p-739644335808dc4827ca2b95d99d5fd2`; B project
  `p-508f658669eb48ffd6d54569d5097e8c`.
- A draft `1b05491cbb80425e8ade01aca518a023`, payload SHA
  `55014309d689d10b5f2b6fadfadef6e82e880dead2c9429f5cb8edca31e8b953`.
- B draft `3d845e70ff9b4f18b5cd137ee6eda7a3`, payload SHA
  `ad2b0a311f94e2771a498eab58bf26735403fe88215313feb5de3b92aff5cfbc`.

New runtime sessions restored both projects. A's list returned only its combined
draft and the decision had an empty rationale. Independent filesystem inspection
confirmed exactly two draft files, their computed digests, the absence of the old
A draft, B's original payload bytes, and the exact decision event. Evidence and
full tool logs are `opencode/evidence.json` and `opencode/run.jsonl` under the
private test directory. This was not a second fresh model conversation.

## Minor usability observations and follow-up fixes

- The Markdown returned by `native.journal_view` has no project title inside the
  content. Native Pages can supply it as a page title, but a standalone Markdown
  file is less clear. Add the escaped/quoted project title to the readable view.
- Batch IDs accept `[a-z][a-z0-9_]{0,31}`. Claude initially tried camelCase, received
  the vague “Use a short unique batch step ID” refusal, then corrected it without
  a saved mutation. State the allowed format in the guide/error. The guard worked.

Both observations were fixed after the installed-app acceptance run. Readable
journals now start with “Benchside project journal” and the project title as
quoted, escaped text. The ID error and source/generated guide state the accepted
format and give `review_a` as an example; duplicate IDs have a distinct message.
Validation rules, saved notebook state and consent behavior are unchanged.

Five new regression cases failed before the fixes and now pass. The targeted
native-memory/batching/conflict/replay run passed 64 tests. The full suite passed
677 tests in the sandbox; its one loopback-server test could not bind there and
passed separately with local-port access, covering all 678 tests. Lint, role
compilation and whitespace checks pass. The generated app guide is current.
These small follow-up edits are tested locally; the installed review.6 ZIPs
remain the exact candidate documented above, not a live test of the polish edits.

## Limits and next gate

- Current client CI passes on Python 3.11 and 3.14. Reporting PR #5's 67-test job
  and Vercel preview are green. No extra unit-test rerun is claimed here.
- Legacy Claude Docs storage is not retested; this evidence covers the working
  private file-artifact route. Free-account capability/usage limits are not tested.
- Automatic role suggestion, role quality and every sharing channel were not
  rerun; this is a focused regression check of the latest fixes.
- Receiver PR #4 remains undeployed. Production submission/real-bucket import
  and the coordinated release order remain separate gates. No public release
  readiness is inferred from these private installed-app tests alone.
- Source files and package bytes were not changed during the installed-app
  acceptance run. The subsequent small source/guide fixes are distinguished above.

Local screenshots/transcripts and machine-readable evidence are retained at
`/tmp/benchside-pr19-review6/`. Private chat links require the test account.
