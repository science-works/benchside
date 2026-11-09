# A live Benchside walkthrough

Use a fresh chat with the latest Benchside package selected. An already installed
account needs no upload during the demonstration. Check the running version with
the agent first; reading the GitHub page is not an installation. For a new user,
give their agent https://github.com/science-works/benchside and follow
[Getting started](getting-started.md). Accounts differ in installation, execution,
durable storage and network access; [host support](host-support.md) records what
has been tested. A local agent with a durable folder is another supported route.

## Prepare

Use invented research and a separate demo notebook/folder. Verify a save and a
fresh-chat restore in that account. The host must be able to send an approved
request to `https://ingest.benchside.science.works`; permission to run Benchside
and permission to access the network are separate. Keep failed sends pending.
No Cloudflare or reporting credentials belong in the user's plugin.

The normal GitHub import runs daily. It is **not** a real-time watcher and excludes
registered synthetic submissions. The 29 October demo watchers have ended.
For an immediate operator check, run the normal **Benchside reporting** workflow
manually after sending, then check its synthetic exclusions. Showing the full
synthetic problem in a separate demo report requires an explicitly started demo
reporting run. Do not remove the test marker or include it in research statistics
to make a demo appear. Colleagues need private repository access to view reports.

## First prompt

> Please use Benchside's research supervisor (/pi) for a fictional imaging study.
> None of this is real research. Set up a new separate private project called
> “Paired imaging — live demo”, explain the available storage and optional sharing
> choices briefly, and let me choose. I have six donors, with control and treatment
> samples from each. Each condition has two wells and each well has three images,
> giving 72 rows. I planned to treat those as 72 independent measurements. Does
> that make sense? Ask one useful follow-up and take this step by step; don't
> complete the demonstration for me.

Discuss the pairing and nested measurements. The supervisor should support this
without inventing a hypothesis or requiring one before giving useful advice.

## Save and restore

> Record our decision to check donor, condition and channel mapping before
> analysis. Keep open whether to aggregate wells/images or model them.

Wait for a verified save. In a fresh chat, select that same demo notebook/project
and ask what was decided and what remains open, without repeating the answer.

## Introduce a workflow problem

> Another fictional issue: DemoScope version 1.4 sometimes drops channel labels
> when I export images. I spend about 20 minutes restoring them manually each
> week. I'd like exports to preserve those labels. Please record this workflow
> problem. When we review it for sharing, start its primary task description with
> this exact registered test marker:
> SYNTHETIC-DEMO-d653ecd34c032c939fd2e8c8:
> Only this invented problem should go into the submission.

Opt into problem sharing after its explanation, leaving other channels off for
this short demo. Review the exact proposed payload and destination. Keep the
marker, public tool version, workaround and impact; omit donor counts, research
questions, hypotheses and sample details. Approve only after reading the preview.
The agent sends it and shows the receipt; no manual receipt transfer is part of
ordinary collection. A generated receipt or a confident chat answer is not proof
of delivery: the operator checks the matching stored bytes/digest.

## Where data appears

Research discussion → private records → reviewed workflow problem → HTTPS
receiver → private Cloudflare storage → daily GitHub import.

In **LauraRyanSW/tools-science-works → Actions**, the reporting run produces
`benchside-private-analysis` (full submitted problems and optional context),
`benchside-public-summary` (aggregate counts), and an encrypted checkpoint for
incremental imports. These are downloadable run artifacts, not raw-data commits.
Registered synthetic submissions are excluded from these research outputs.
The aggregate output may be proposed through a separate review PR; private research
text and raw submissions do not become public repository files.

The reporting code computes counts; it does not use an LLM to group similar
problems. It retains each problem's full submitted wording privately. LLM analysis
and the Vercel display remain later work. Describe them as future steps, not part
of the live demonstration.

For earlier evidence, see [the historical October demo](live-demo.md). Its timed
runs and artifacts are historical and may no longer be downloadable.
