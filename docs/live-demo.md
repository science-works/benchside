# Live Benchside demonstration

The presenter starts a new conversation and responds naturally. This is a
synthetic research consultation, not a replay of the acceptance-test chat.
Use the installed Benchside plugin in ChatGPT for the first rehearsal; the
existing larger Claude notebook currently fails the exact-transfer check.
The evidence and limitations are in [the live test report](live-receiver-check-2026-10-29.md).

## Starting prompt

Paste this into a new chat with Benchside selected, then send it during the demo:

> I'd like to use Benchside to plan an imaging study. This is a fictional demo;
> none of the details are real research. Start a new private project called
> “Paired imaging — live demo” in a separate demo notebook. Explain the available
> storage and optional sharing choices briefly, and let me answer them. If this
> app cannot reliably save records, tell me rather than claiming it has saved.
>
> I have six donors, with control and treatment samples from each donor. Each
> donor-condition has two wells and each well has three images, so my spreadsheet
> has 72 rows. I was going to treat those as 72 independent measurements. Does
> that make sense? Ask a useful follow-up question and take this one step at a
> time; don't complete the whole demonstration for me.

## Possible next turns

These are presenter cues, not instructions to run all steps automatically.

1. Choose a separate private demo store after its limitations are explained.
   For an initial rehearsal, leave sharing off. For the supervised send demo,
   opt into workflow-problem sharing only after its explanation; each exact
   problem still needs review. Skip demographics if desired.
2. Discuss pairing and nested measurements. A useful scientific response should
   distinguish six independent donors from 72 rows without prescribing an
   analysis before checking the design and assumptions.
3. Introduce a workflow obstacle: “In this fictional export, channel labels
   sometimes disappear. I spend about 20 minutes putting them back each week.”
   Do not attribute the invented defect to an actual product.
4. Say: “Let's check donor, condition and channel mapping before analysis.
   Record that decision. Keep open whether to aggregate the wells and images
   or model them hierarchically.” Wait for an actual save confirmation.
5. Optionally start a fresh chat, select the same demo store/project, and ask
   what was decided. A read from saved storage demonstrates continuity;
   repeating the decision from the previous chat does not.
6. Ask to review a workflow-problem report. The candidate should describe the
   export/relabeling friction and frequency, omit donor counts, conditions and
   research questions, and retain an explicit “SYNTHETIC DEMO — not a research
   submission” marker in allowed descriptive text.
7. Inspect the exact preview. Only then approve the synthetic submission if the
   registered marker below is present. Show the receiver receipt and
   automatic GitHub report; a successful chat response alone is not proof.

Do not pre-authorize an unseen payload, invent a submission receipt, or set a
new `test:true` field: the live receiver enforces a strict schema.

## Showing the data flow honestly

The intended full demonstration is:

Research conversation → private saved record → reviewed problem report → HTTPS
receiver → private R2 object → analysis → reviewed report → Vercel preview.

The receiver, R2 readback and local importer have passed synthetic checks. A
separate **GitHub-hosted synthetic demo job now also passes**, without merging:
[verified rehearsal run](https://github.com/LauraRyanSW/tools-science-works/actions/runs/40872156541).
It verified one existing synthetic object, showing one problem, one contributing
store and one exact-description group. The hosted run took 26 seconds. This is
the earlier acceptance record, not a record from the presenter's later live chat.

Today's automatic route has now passed a live rehearsal:
[automatic 0.3.0 run](https://github.com/LauraRyanSW/tools-science-works/actions/runs/40877962796).
The receiver accepted the new synthetic record at 13:04:14 UTC; GitHub completed
its report at 13:04:29 UTC. No receipt was copied to the reporting job. The report
retained optional tool version, impact and workaround fields, while the private
scientific decision remained absent. The artifact contains one observation,
one synthetic contributing store and one exact-description group.

For the colleague demo, use [this separate waiting run](https://github.com/LauraRyanSW/tools-science-works/actions/runs/40881134460).
It is armed until **17:00 UK/UTC on 29 October 2026** and finishes after the first
matching batch. The exact problem marker for this run is:

`SYNTHETIC-DEMO-d653ecd34c032c939fd2e8c8:`

Keep that marker at the beginning of every submitted gap's primary description
(task, approach, sought or question). Use a separate demo store and only preview
synthetic observations. The marker was registered before collection and is
permanently excluded from research reporting, including late submissions.
Generic words such as “demo” do not qualify other records for this report.

After the researcher approves the exact preview, the client sends normally.
The GitHub job checks Cloudflare every 15 seconds; refresh its summary page after
the receipt arrives. Its JSON/Markdown artifact is available to repository
members for seven days. This updates a GitHub run/artifact, not a committed raw
record or a Vercel page. The job has no GitHub write, R2 write or delete permission.
It reads the named dates with fixed limits, never outputs unrelated records, and
refuses mixed demo/research batches. The production import remains unmerged and
disabled. Nothing is merged as part of this demonstration.

See [the colleague quick-start](demo-start-here.md) for the install steps and
copyable prompts. The runtime version is 0.3.0; the receiver supports the new
optional fields. Claude's uploaded plugin shows 0.3.0, but the known larger
cloud-notebook transfer problem remains. Do not demonstrate a successful cloud
save or fresh-chat restoration unless the host actually verifies it.

## Reporting structure for the first rollout

Keep raw submissions in private Cloudflare R2. Run validation and aggregation in
the private GitHub repository using its scoped read-only key. Keep the internal
analysis in short-lived private job artifacts. Commit only reviewed public-safe
report snapshots; Vercel deploys the approved code/data together. GitHub is not
the raw participant database, and no receiving or storage credential is shipped
to users or to the browser.

This fits the existing static Bugbear site and the already prepared reporting
PR. Vercel does not require data in GitHub: if frequent updates later justify it,
store approved report snapshots in Cloudflare and fetch those through a Vercel
server route. Retain an explicit review/publish step in either design.

The updated reporting PR retains each complete gap observation alongside summary
statistics. It deduplicates retries without combining matching descriptions.
LLM theme discovery and mapping into Bugbear tool tiles are later analysis and
display tasks. A problem report is not automatically a vote to rebuild a
tool. Keep source-specific report counts and participating-store counts distinct
from Bugbear's existing hackathon scientist/demand counts.

Useful optional problem context includes the public tool/dataset name, relevant
version, generic task, frequency, practical impact, workaround and desired
improvement. These now have dedicated optional fields in 0.3.0. Their missing values do not
block recording or sharing; the assistant may ask one useful follow-up at a
natural pause. The actual version used is recorded, not a guessed latest release.
Do not collect unpublished findings, detailed protocols or sample identifiers
to fill the Bugbear page. Its tool mapping and hardware alternatives can be
curated after collection.
