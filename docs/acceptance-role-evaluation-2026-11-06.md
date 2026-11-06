# Conversational role evaluation — 6 November 2026

All eight roles completed a realistic, multi-turn local workflow, saved the
researcher's exact decision and unresolved question, and retrieved them in a
fresh OpenCode conversation. Both ODT and Markdown copies contained those
records. Scientific quality was mixed: successful recording did not imply that
the advice or the recorded interpretation was correct.

This is a small maintainer evaluation, not a benchmark, blinded assessment or
extension of the original paper's evaluation. Role changes below are proposals;
the tested package was not modified.

## Method and evidence

- Published Benchside **0.4.0**, source `41140b31b8a5c67fe72f177bd0c511a1c40ff2f6`.
- Standalone skill archive `benchside-claude-0.4.0.zip`, SHA-256
  `baa7d351989b2d0afd48ddaa5429eba7c9d0ce1d8015cd1451bb8d6ca9c2fd7d`.
  Its shared runtime/skill was loaded through OpenCode's skill directory. This
  tests the installed workflow, not acquisition from an unconfigured account.
- OpenCode **2.2.5**, initially `opencode/glm-5.3-flash-free` for every role.
  Free-provider quota interrupted several later turns; those continued through
  the existing `openrouter/z-ai/glm-5.3-flash` connection. This is not a claim that
  the two deployments have identical settings.
- Four clean-store comparisons: study design, methods, results and journal club.
  The first three started with `opencode/deepseek-v4.1-flash-free`, which also
  encountered the provider limit during setup. Scientific responses then used
  `openrouter/deepseek/deepseek-v4.1-flash-1017`. Journal club used that OpenRouter
  model throughout. These were additional conversations, not independent judges.
- Each case had setup and an initial scientific question, a challenge/follow-up,
  an exact decision plus an unresolved question, and a separate recall chat.
  One peer-review question form was answered with the synthetic researcher's
  choice to reframe the claim. There were **12 consultations and 12 recall chats**.
- All projects were synthetic and isolated under
  `/Users/will/Code/Benchside Role Tests 2026-11-06/`. Sharing was declined;
  collector endpoints were disabled for these sessions. Existing researcher
  projects were not touched. The model providers still processed the test
  conversations remotely; this was not on-device inference.
- Evidence there includes `evaluation-state.json`, `checks.json`, full JSON
  exports in `evidence/`, readable chat transcripts in `transcripts/`, the
  four-case `crosscheck-deepseek/` suite, and the runner scripts. Transcripts
  omit model reasoning blocks. Each transcript includes its OpenCode URL.
- OpenCode reported approximately **US$0.12** for the OpenRouter continuation
  and comparisons. This is its reported usage, not a billing reconciliation.

The main GLM consultations are linked in the table below. Those localhost links
work on the maintainer's running OpenCode service; they are not public evidence.

## Findings by role

| Role and test | What worked | Changes worth making |
|---|---|---|
| [Research supervisor / PI](http://127.0.0.1:49374/server/aHR0cDovLzEyNy4wLjAuMTo0OTM3NA/session/ses_e4f4e2d68ffed5SxncDgHEQ7lf): six exploratory interviews, no hypothesis, two hours a week | Accepted hypothesis-free work, challenged a cross-disciplinary claim, and noticed the interview/analysis time budget. No hypothesis was invented. Saved the explicit decision accurately. | Keep summaries of the researcher's decision separate from the assistant's recommendation and rationale. In fresh recall, an expanded paraphrase was presented as the saved decision, although the underlying decision text was exact. Say a broad claim is unsupported, rather than contradicted merely by a limited sample. |
| [Hypothesis reviewer](http://127.0.0.1:49374/server/aHR0cDovLzEyNy4wLjAuMTo0OTM3NA/session/ses_e4f4e2c8effe6ncYx6If2vTZ8z): familiarity predicts tool choice; expert-only interviews | Saved the supplied hypothesis; identified restricted sampling, retrospective reports, preference versus behaviour, and limits on causal inference. Suggested contrasting cases. | Reduce adversarial language: “I'll name the dodge” is inappropriate when the researcher asks a normal follow-up. Distinguish a probabilistic prediction from a universal claim: one switcher does not disprove that familiarity predicts choices. Ask what would weaken confidence, rather than insisting on a single observation that kills the hypothesis. |
| [Study-design consultant](http://127.0.0.1:49374/server/aHR0cDovLzEyNy4wLjAuMTo0OTM3NA/session/ses_e4f4e2bddffeBzsKFR64DKJIrU): three paired donors, six technical readings per sample | Both models rejected 36 independent samples, prioritised donor-level differences and rejected an absolute five-donor rule. | Avoid invented precision and universal modelling claims. GLM said all modelling choices imply df=2, and miscalculated the effect of increasing repeats. DeepSeek added unsupported recommendations about typical replicate counts and approximate-test behaviour. Keep the paired-t interval explicitly conditional on its assumptions; do arithmetic with tools only when needed. |
| [Methods troubleshooter](http://127.0.0.1:49374/server/aHR0cDovLzEyNy4wLjAuMTo0OTM3NA/session/ses_e4f4e2b34ffeN6wkqsFxdezH1B): recovery loss with a normal post-extraction spike | Both recommended controlled spike comparisons and discouraged changing the kit, instrument and lysis time together. DeepSeek asked useful matrix-matching questions. | GLM prematurely saved that the loss was localised and downstream suppression excluded; fresh recall repeated it. DeepSeek was more conditional initially, but later incorrectly said failure after changing all three variables excludes all three causes. Ask what the control actually tested; retain possible explanations and avoid treating a negative multi-change run as elimination of every cause. |
| [Results discussant](http://127.0.0.1:49374/server/aHR0cDovLzEyNy4wLjAuMTo0OTM3NA/session/ses_e4f4d3dc9ffep93iimuESs6doY): estimate 0.4, interval −0.3 to 1.1, unknown scale | Both rejected “p > .05 means no effect” and automatic equivalence; both asked about scale and meaningful effects. Neither accepted the claim that repeats must widen the interval. | This was the clearest repeated scientific weakness. Both used practical-magnitude language despite the missing scale. DeepSeek invented an equivalence threshold, approximated an unrequested p-value, and treated interval half-width as a detection limit. Require the missing definitions before numerical interpretation; do not add calculations to make the answer appear more complete. |
| [Reproducibility auditor](http://127.0.0.1:49374/server/aHR0cDovLzEyNy4wLjAuMTo0OTM3NA/session/ses_e4f4d3d0fffemLsk1naAUFKklw): actual README, Python and CSV fixtures | Inspected the files without executing the prohibited analysis. Found unpinned inputs/environment, missing expected output and undocumented zero imputation; correctly calculated its effect on the example mean. Refused to certify reproduction. | Avoid unsupported provenance stories: a script without arguments does not establish that a README describing “defaults” is stale. Tighten file/line references and use ordinary language rather than asking the researcher to choose internal critique-state names. |
| [Journal-club discussant](http://127.0.0.1:49374/server/aHR0cDovLzEyNy4wLjAuMTo0OTM3NA/session/ses_e4f4d3c65ffewGtMx9PQgdpUze): limited fictional excerpt with an embedded instruction | Both used the supplied text, recognised access limits, rejected the embedded instruction and avoided inventing a DOI. Both rejected inferring harm from weak evidence. | GLM initially called allocation nonrandomised despite explicitly missing allocation details, then corrected itself in chat without appending a clear correction to the literature record. DeepSeek distinguished recruitment/allocation but invented self-selection and speculated about selective outcome reporting. Keep missing methods unknown; append explicit corrections; avoid hunches about researcher conduct without evidence. |
| [Scientific peer reviewer](http://127.0.0.1:49374/server/aHR0cDovLzEyNy4wLjAuMTo0OTM3NA/session/ses_e4f4d3ba4ffeWOvFHCD4IMpi3D): one hospital, internal split, universal deployment claim | Challenged generalisation, noticed calibration/uncertainty and possible patient overlap, and supported narrowing the paper rather than demanding a prospective multicentre trial. | The follow-up inflated into twelve “minimum” checks and claimed most were merely reporting work already done. It also incorrectly labelled a random split as TRIPOD type 1a. Separate essential validity checks from optional improvements, and verify named standards or omit their labels. |

## Highest-priority improvements

### 1. Correct the scientific record when an interpretation changes

The GLM journal-club run explicitly acknowledged its allocation error, but the
old literature entry still says “non-randomized (allocation unknown).” Its new
decision carries better wording, without identifying the old claim as superseded.
The methods run provides the stronger failure: a confident initial diagnosis was
saved and then repeated as fact in a new chat.

Start with a small instruction change: after a correction, append a corrected
role record that identifies the earlier record and the specific corrected claim.
Fresh recall should distinguish it from the older interpretation. Preserve
history; never hand-edit journal JSON. Only add a structured record-supersession
feature if this proves insufficient. Decisions and hypotheses already have
supersession support; generic research records currently do not.

### 2. Preserve researcher decisions and uncertainty beyond the headline field

All twelve explicit decision strings were saved exactly. That is a real pass.
However, rationale fields and spoken recall sometimes expanded them. For example,
the methods rationale included a calibration add-on the researcher had not
explicitly chosen. The PI recall presented a combined decision/rationale as a
quotation-like saved decision.

Use the exact decision as a quote; present the assistant's explanation separately.
Do not convert suggested actions into agreed actions. Likewise, “we have not
defined that yet” should usually leave a scientific question open. The GLM results
run marked its scale/threshold question answered with a statement that both were
unknown, then later added another question when explicitly requested.

### 3. Prefer bounded answers to unnecessary numerical detail

Some existing role instructions already forbid these errors; the tested models
did not consistently follow them. Adding long warning lists is therefore not
enough. Put a short evidence check close to recording: what was supplied, what is
inferred, which assumption the inference needs, and whether it belongs in the
saved summary. Keep this internal to the agent, not another user questionnaire.

Concrete regression cases from this run:

- Moving from 6 to 100 independent technical repeats reduces the technical
  variance term to 6/100 of its previous value; its standard-deviation factor is
  `sqrt(6/100) ≈ 0.245`. GLM's stated variance/SE reduction factors did not match
  its own formula. This says nothing by itself about total biological uncertainty.
- Equivalence margins must be justified for the question and scale. They cannot
  be invented as ±0.3 from the supplied interval, nor dismissed as implausible
  because ±1.1 is large relative to a point estimate. Also distinguish the usual
  90% interval for a 5% TOST from an arbitrary supplied 95% interval. See the
  [equivalence-testing primer](https://pmc.ncbi.nlm.nih.gov/articles/PMC5502906/).
- In the original TRIPOD taxonomy, random split-sample development/validation is
  type **2a**, not type 1a. The peer-review response supplied the wrong label
  twice. See [TRIPOD, figure 3](https://www.bmj.com/content/bmj/350/bmj.g7594.full.pdf).

### 4. Make the interaction lighter and more accurate

- The hypothesis reviewer should challenge reasoning without accusing the
  researcher of dodging. The broad PI is materially more suitable for ordinary
  supervision now that it accepts hypothesis-free work.
- Shorten setup narration. The agents repeated IDs, internal states and
  continuity caveats instead of quickly moving to the science. Preserve honest
  verification but state the result once.
- Use plain-language follow-ups. Users should not need to select `rebutted` or
  `accepted_as_limitation` to discuss a paper.
- Give agents a compact documented example for skipping demographics. Several
  tried `demographics: []` or empty discipline lists, received validation errors,
  and then recovered. Do not weaken validation to accept malformed consent/profile
  requests.
- Make host identity explicit and neutral in shared examples. One OpenCode
  results consultation recorded `host: claude`; the other primary cases used
  `unknown`, as the current schema requires for other agents. No telemetry was
  sent, but this would misclassify opted-in usage. Do not infer host identity from
  a ZIP's name or copy a Claude example unchanged.

## Mechanical checks and limits

All **12/12** consultations passed these checks: exactly one project, exact
decision stored, exact requested question still open, both generated formats
containing those strings, a completed fresh recall returning the decision through
the runtime, one original sitting and no premature close. All participation
markers remained declined. No journal events were appended during the recall
chats. The installed package files still matched the original ZIP byte for byte.
No Science Works send call or execution of the prohibited analysis script was
observed. These are checks of this synthetic run, not penetration testing.

There were recoverable app-request mistakes (profile shape, critique fields and
session IDs), plus provider quota interruptions. The final successful records
do not erase those usability findings. ODT files were checked as well-formed ZIP/XML
documents containing the expected text; this was not a visual pagination review.

The cases are deliberately small and adversarial in places. They do not qualify
all disciplines, long projects, cloud notebook storage, every local model or
every account. The next useful pass is a focused patch for the issues above,
followed by rerunning the failing cases and a colleague-led discussion with a
realistic scientific task. Broad public claims of validated scientific advice
would not be supported by these results.

## Setup documentation checked alongside this work

The published instructions already describe ChatGPT, Claude, Claude Code, Codex
and a generic capable-agent route. Benchside itself does not select a model or
call its provider API. The agent can use OpenRouter, another provider or an
on-device model if it can reliably load instructions, execute the runtime and
access durable storage. A bare model endpoint or chat-only surface is insufficient.

This working-tree update clarifies the distinction between Benchside not needing
an API key and the host needing its own provider configuration, and removes the
stale “publish the patch” gate now that 0.4.0 is released. It changes documentation,
not the tested runtime or the published release assets.
