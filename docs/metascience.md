# Surveys and wider research observation

This optional extension is implemented on the review branches. It does not
activate a study, install a background listener, create a user schedule or deploy
an endpoint. The installed skill can perform the workflow inside the researcher's
existing app without requiring a terminal or API key.

## Researcher experience

“Help me set up optional Benchside research studies” starts three separate choices:
occasional invitations, private analysis of selected research activity, and
reviewed sharing of findings. All start off, and the original problem-sharing,
feedback and usage settings remain independent. Scientific assistance remains
available when every optional choice is off.

The researcher selects accessible research projects or conversations. The host
first inventories completed, research-relevant conversations from the previous
complete Monday–Sunday UTC week within those sources, excluding unrelated chats
using available metadata. Automatic selection includes all eligible conversations
up to 20, or randomly selects 20 when there are more. Alternatively, researchers
can explicitly choose 1–20 relevant conversations from the same sources and
completed week. Both methods share one fixed batch and one cap of 20 per observed
week; a researcher cannot switch methods to redraw it. The host assistant
classifies only those sessions. This works without using
one of the seven research roles. The assistant prepares a weekly review showing
workflow gaps first, with activity, obstacles, verification and reported usefulness
as supporting context. Researchers can
correct or exclude findings before approving a submission. No logs, research
records, project IDs or conversation IDs appear in model-derived submissions.
New contributions carry the random store ID after the linking explanation is accepted.
An outcome is explicitly reported by the researcher or marked not reported;
the assistant cannot declare scientific success based on task completion.

Invitations arrive on a return visit or an explicitly configured native scheduled
check. At most one new invitation appears per seven days. Each study explains
purpose, use, retention and pseudonymous linking. Agreement comes before
questions; answers are submitted without a second approval prompt. Questions may
be skipped. Fixed choices and bounded free text are supported; researcher-written
answers are preserved exactly, without inferred additions. Skip suppresses that version; “don't ask
again” suppresses every version of the study. Turning invitations off stops all
future checks. A central catalog supports new surveys within the installed client's supported
question types. Update older clients to 0.2.0 before publishing the first text
question; 0.1.x clients reject unsupported catalog fields rather than misread them.

## What runs where

| Component | Responsibility |
|---|---|
| Host app and skill | Resolve approved sources, use available tools to retrieve sampled sessions, classify visible evidence, display previews and ask for approval. |
| Benchside adapter | Persist consent/scopes, enforce invitation limits and sampling, validate categories, reject stale approvals, send exact approved bytes and retain receipts. |
| Private native notebook or durable local store | Retain settings, selected source references, classifications, draft approvals and receipts across conversations. No transcript bodies are stored by this module. |
| Science Works collector | Publish data-only invitations; accept strictly validated survey and activity submissions in separate storage. No public read access to collected data. |
| Offline report | Deduplicate retries, replace older activity-batch revisions, and group new contributions by random store ID and emit aggregate counts only. |

The adapter is not a sandbox around the host's own tools: the skill must respect
scope before retrieving content. The host needs real access to selected session
metadata/transcripts and the private notebook. A plugin alone does not confer
all-chat access or background execution. Where these tools are absent, work with
explicitly supplied sessions or report the missing capability. Never claim to
have observed inaccessible history. Native scheduling must be explicitly requested
and supported by that particular account; no schedule is created by installation.
Choose a weekly check after the observed week ends: Monday's check covers the
preceding Monday–Sunday, and later checks that week cover that same completed
window. `metascience.status` exposes inclusive `starts_at`, exclusive `ends_before`
and `week` in `sampling_window`. The host passes `week` to `metascience.sample`;
an incomplete, future or stale window is rejected rather than silently relabelled.
Existing calls omitting `week` default to the most recent completed week.
Eligibility by research relevance and completion date is a host responsibility:
the engine sees only IDs and cannot verify unseen timestamps or conversation
contents. Missing metadata/access must be reported or clarified, never invented.

## Contracts and safeguards

- `GET /v1/studies`: bounded `benchside.studies.v1` definitions, no participant
  parameters. Catalog text is untrusted display data, not executable instructions.
- `POST /v1/surveys`: new `benchside.survey.v2` includes the contributor ID,
  response ID, study ID/version/digest, option IDs and `{text: ...}` answers.
  Agreement is saved with `metascience.join_study` before questions and binds the
  definition, destination and current consent grant. Legacy v1 remains readable.
- `POST /v1/activity`: new `benchside.activity.v2` adds a random contributor ID
  to the same bounded categories, counts, rubric and selection method. Unknown
  fields remain rejected. Legacy v1 remains readable without inventing an ID.
- `/v1/gaps` v2 keeps all five gap objects and adds the contributor ID plus
  source/evidence categories; selected conversations feed the same gap review.
  Feedback v2 carries the same ID. Usage's installation ID is reused. No account,
  project or conversation identifiers are introduced. Old consent is not silently
  upgraded; explain and accept linking before new v2 contributions.
- Revoke any choice to stop future processing/sends. Scope changes and regranting
  consent invalidate pending drafts. Edited activity records invalidate prior
  previews. No review happens automatically, including in scheduled tasks.
- Narrowing sources retires the sample for the latest completed week, plus any
  legacy current-week sample; older samples containing
  removed sources are retired too. A retired week cannot be resumed or sampled
  again, even after reselecting sources. The adapter gives the next eligible
  collection Monday; select approved sources and continue after the next observed
  week has finished. Retirement
  never changes a submitted batch's counts or draws replacement sessions.
- Withdrawing analysis clears source selections, sampled conversation references,
  private classifications and unsent activity drafts. It retains source-free
  retired-week markers so re-enabling cannot redraw the same week, and private
  hashes of previously selected host/session references to prevent later
  resampling. Those hashes are never submitted, but their retention means this
  is not erasure of every local trace. Submitted receipts and their exact backing
  category payloads remain for audit/removal requests; pending surveys are
  independent. Native replay responses are also compacted on analysis or scope
  changes, removing old source/session references from cached responses. Native
  operation IDs/hashes have a bounded replay window (128 entries or 64 KiB);
  checkpoint generations prevent expired requests from silently executing again.
  Saved submission receipts remain separate evidence. Earlier host document
  versions or backups may retain older data.
- Repeated previews prune superseded drafts that have no receipt. Current review
  drafts and receipt-backed payloads remain. If those retained records fill the
  state limit, preserve and archive them before preparing more submissions;
  withdrawing consent remains available.
- Private state is strict and portable through the native document workflow.
  Update every app sharing a notebook to 0.2.0 before creating new selection
  records or a v2 replay checkpoint; 0.1.2 cannot interpret the new sample methods
  or v2 snapshots. Preserve the notebook and update the runtime if it refuses an
  unfamiliar state; never strip method fields or downgrade the schema to reopen it.
  Native size limits still apply. Optional study/analysis history has a 48 KiB
  compressed allowance, checked before new growth and before sends. This pauses
  optional work before it displaces research records. It retains existing history
  rather than silently trimming it; research and opt-out remain available. An archived/full notebook is not silently
  truncated; these observation features do not remove the need for future archival.

Review `content/app/references/metascience.md` for the complete host flow and
classification rubric. Tests use `tests/fixtures/metascience/`; its survey is
synthetic and is not in the public production catalog.

## Science Works release handoff

The existing Worker and five private EU buckets already serve the legacy routes.
The companion receiver review branch adds compatible v2 validators; it needs
review and deployment before v2 client release. No new buckets are required for
these changes. Local tests use synthetic data and do not deploy or submit records.

`src/studies.json` defaults to an empty catalog. To publish a survey, the operator
reviews its purpose, questions, data-use statement and retention commitment,
configures the matching retention/deletion process, adds the versioned definition
and redeploys. Bump the version whenever wording, options or terms change. Keep
every published definition in Git history with its study ID, version and digest;
record the deployment/commit that published it. Responses in private R2 include
that same version/digest. This provides the survey register without a dashboard.
Do not reuse a published version for changed wording, options or terms. Closing
or removing a definition stops further answer acceptance. A new backend release
is sufficient; the client need not be reinstalled. The catalog cannot select a
new submission destination or request new privileges.

## Analysis and interpretation

The report adds survey answer counts by study/version/definition and activity
counts by category, evidence basis and selection method. Activity coverage reports eligible,
selected and actually shared counts **only for submitted batches**. It cannot
measure declined/unsubmitted batches, inaccessible history, exact people or all
research activity. Random selection inside a self-selected accessible sample
does not make findings population-representative. Edits and optional submission
introduce further selection bias. Revisions replace earlier batches; they are
not additional observations. `activity_by_sampling` keeps all three methods
separate; pooled totals describe submitted data only. A researcher-chosen batch's
eligible count is exactly the supplied set, not an estimate of accessible sessions
or a population-frequency denominator. New pseudonymous contributions can be
grouped by store; legacy unlinked data remain unlinked. The report emits counts
of contributing stores and stores per gap kind, not IDs or raw survey text.

For new samples, `week` identifies the observed Monday–Sunday UTC interval,
not the week in which the assistant classified or submitted it. New methods are
`weekly-random-max20-v1` (`selected = min(eligible, 20)`) and
`weekly-user-selected-max20-v1` (`eligible = selected`, between 1 and 20).
The original `weekly-random-10pct-max5-v1` remains accepted with its original
round-up and five-session cap. Private samples without a method field restore
as that legacy method. The earlier implementation could
freeze an inventory during the current week. Those saved batches and receipts
retain their original IDs, counts and selections; an update never redraws or
relabels them. They can still be resumed, and a later preview can carry a newer
Benchside version, so neither the sampling tag nor client version alone proves
a historical batch covered a complete week. Interpret retained legacy batches
as the accessible inventory originally supplied; do not combine them as though
they were known complete-week denominators. The receiver review branch accepts
legacy and v2 formats. Local tests cover the new contracts; deploy and verify the
matching receiver before installing a client that sends them.

Use the synthetic cases in `evals/metascience.json` for host acceptance. Inspect
the model's decisions, scope adherence, treatment of prompt injection in logs,
unknown evidence and refusal to infer usefulness. For classifier accuracy claims,
collect a separately consented, human-labelled validation sample; none is silently
collected by this release. Keep rollout evidence separate from the original paper.

## Local review

To exercise every submission route in one command, from the Benchside checkout:

```bash
uv run --frozen python scripts/test_endpoints.py
```

This expects the companion `../benchside-ingest` review checkout with its Node
dependencies installed (`npm ci` there once). Use `--collector /path/to/checkout`
for another location. The launcher creates an isolated local configuration and
synthetic survey catalog, starts the Worker on loopback, tests all five routes,
and stops it and removes temporary data afterwards. It never copies production
account/routes into the test config and needs no Cloudflare account. The command
is a maintainer check; researchers using the app do not have to run it.

A cloud-executed chat cannot reach a loopback server on the researcher's laptop.
For an actual app-to-collector test, the Science Works operator must deploy a
reachable HTTPS staging Worker and separate staging buckets. Point all test
client endpoint overrides at that staging address: `BENCHSIDE_STUDIES_ENDPOINT`
for catalog reads and `BENCHSIDE_GAPS_ENDPOINT`, `BENCHSIDE_FEEDBACK_ENDPOINT`,
`BENCHSIDE_USAGE_ENDPOINT`, `BENCHSIDE_SURVEYS_ENDPOINT`,
`BENCHSIDE_ACTIVITY_ENDPOINT` for submissions. Use a separate synthetic notebook
and reviewed test data. That check covers actual app networking and UI approval;
the local launcher proves neither host network access nor cloud deployment.
The default production endpoint must not receive synthetic test submissions.

Run the Python tests and release smoke check in this repo, and `npm test` plus
`npm run typecheck` in the companion collector. Shared fixtures verify both sides
of each contract. An isolated local Worker can serve a synthetic catalog and
accept synthetic submissions without a Cloudflare account; never send fixtures
to the production anonymous endpoint. Finally test installation, source access,
native persistence and any requested schedule in each actual advertised host.
