# OpenCode and OpenRouter PI check — 5 November 2026

Synthetic compatibility test, separate from the paper's evaluation. This tests
the public 0.3.1 release, not the unpublished 0.3.2 candidate. It is a partial
pass for installation and persistence, with unresolved role and agent issues.

## Configuration and evidence

- Host: OpenCode 2.2.5 on the researcher's Mac, with its browser interface.
- Model: `openrouter/deepseek/deepseek-v4.1-flash-1017`.
- Inference ran remotely through the researcher's connected OpenRouter account;
  tools and records ran locally. This was not locally hosted inference.
- Public release: `v0.3.1`, commit
  `e81b5f25953b3c0bf893406740835ebfa2a82c14`.
- Workspace: `/Users/will/Code/Benchside Local Test`.
- Source/environment: `.benchside/src` and its `.venv`.
- Installed skill: `.opencode/skills/benchside/SKILL.md`.
- Private store: `records`, outside Git, selected with `BENCHSIDE_HOME` for each
  runtime invocation. OpenCode snapshots were disabled for this test folder.
- Project: `SYNTHETIC-OPENROUTER-PI-20261105`, ID
  `p-0102120f9a6e183171115290a7ed2550`.
- Install/recording session: `ses_e536b18c8ffeQK2XUuc5sQEQc3`.
- Fresh restore session: `ses_e535f39a3ffehlRm1gTpL97453`.

Local session exports and tool events are in the workspace's `test-evidence`
directory. OpenCode reported $0.057331728 for installation/recording and
$0.00321959 for fresh restoration, approximately $0.06 total. These are the
host's cost estimates, not a separately checked provider invoice.

## Results

| Check | Result |
|---|---|
| Install public release and project-local skill | Passed technically; the agent used an unnecessarily long source-inspection route. |
| Execute installed runtime | Returned `0.3.1`. |
| Write/readback probe | Passed in the selected store. |
| Separate synthetic setup record | Created in a separate project, not in the PI project. |
| Begin PI discussion without fabricating a hypothesis | Passed for the first question. |
| Preserve the researcher's decision wording | Failed: the agent changed “analysis-software selection” to “analysis-methodology preferences”. |
| Record an unresolved question without a hypothesis | Partial: saved as a study-design record; `open_questions` remained empty. |
| Discover skill in a genuinely fresh conversation | Passed: the new conversation called the `benchside` skill tool and read the app and PI references. |
| Restore from private records in that conversation | Passed: runtime recall returned the stored decision, question-containing record and two open sittings. |
| No invented hypothesis or completed observations | Passed for the inspected journal. |
| Keep optional contributions off | Passed: gaps, feedback, usage, invitations, selected-conversation analysis and analysis sharing were off; participation was declined. |
| Submit to Science Works | Not exercised. |

The fresh conversation was not supplied the decision or question text. It used
the installed launcher and `recall` with `history:all`, rather than earlier chat
logs or test-evidence files. It quoted the stored decision exactly, including
the earlier model's unwanted paraphrase. The scientific journal remained four
events / 2,825 bytes. `setup` created session metadata, so the model's “wrote
nothing” description was too broad even though it added no scientific events.

## Findings and practical fixes

1. **The current PI role assumes hypothesis-led work.** Its open questions are
   unresolved critiques and critiques require a hypothesis. The agent opened a
   second, study-design sitting and saved the sampling question in record
   details. That preserves text, but it is awkward and makes the dedicated
   question list misleading. Before supporting a broader research-supervisor
   role, decide how exploratory questions should be represented without
   weakening the focused hypothesis-review workflow. Do not manufacture a
   hypothesis just to satisfy the schema.
2. **Agent recording fidelity needs checking.** The model changed the agreed
   decision's subject. A follow-up test should require exact decision text and
   compare runtime readback to that text before reporting success. No journal
   was edited to disguise this failure.
3. **Onboarding was technically successful but inefficient.** The initial agent
   inspected source files instead of loading the shared skill, guessed unrelated
   paths, used `/tmp` for public installation material despite the requested
   workspace boundary, and listed an existing global Benchside directory. No
   credential contents or other project journal bodies were observed in the
   tool trace. The fresh conversation stayed on the installed skill/runtime route.
   The candidate's improved installer handoff should be tested separately.
4. **The test driver initially appended its own Python script to the prompts.**
   OpenCode read inherited standard input as additional prompt text. This limits
   the initial run's value as a clean onboarding benchmark. The fresh restore
   used `stdin=DEVNULL`; its exported user message contained only the intended
   prompt. Future command-driven tests must use that setting. Exporting directly
   to a file also avoided truncated piped JSON output.
5. **The browser was initially showing an empty draft while the test ran in a
   different conversation.** The actual conversation was then opened for the
   researcher. Future visible tests should open the target conversation before
   asking the researcher to follow its progress.

No release, runtime, role, consent or collection format was changed for this
test. Installation and fresh-chat persistence are useful evidence; this one
scenario does not establish scientific quality or reliable support for every
model/provider.
