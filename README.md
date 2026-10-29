<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/logo-dark.svg">
    <img src="docs/assets/logo-light.svg" alt="benchside" width="100">
  </picture>

  <h1>benchside</h1>

  <p><b>An AI workspace for doing science.</b></p>

  <p>
    <img alt="Python 3.11+" src="https://img.shields.io/badge/python-3.11%2B-4dd0e1?style=flat-square">
    <img alt="License" src="https://img.shields.io/badge/license-Apache--2.0-8b949e?style=flat-square">
    <img alt="Status" src="https://img.shields.io/badge/status-prototype-f0a832?style=flat-square">
  </p>
</div>

Benchside turns research discussions into a private scientific record that you
can return to: decisions, evidence, unresolved questions and next steps.

All seven roles are included:

| Role | Scientific output |
|---|---|
| `/pi` | Hypothesis, challenges and next step |
| `/study-design` | Study outline, comparisons, controls and assumptions |
| `/methods-clinic` | Discrepancy, possible causes and diagnostic checks |
| `/results-meeting` | Evidence-to-claim assessment and follow-up |
| `/repro-check` | Reproducibility and handover checklist |
| `/journal-club` | Source-grounded appraisal of accessible papers |
| `/peer-review` | Major/minor scientific concerns and revision priorities |

## Guided app setup

See [Getting started](docs/getting-started.md) for setup without terminal commands
or API keys. Installable Claude and ChatGPT/Codex packages are built from this
repository. The current package is 0.3.1. There is no public plugin-directory
listing yet. Give a new agent the repository URL and
[setup instructions](docs/getting-started.md)
rather than relying on discovery by name alone.

Native memory uses a private notebook in a capable host, with readable journals
per project. Guarded saves and readback protect the validated record; the
execution sandbox is disposable. ChatGPT/Claude notebooks have passed
save and fresh-chat restoration tests. Version 0.3.1 adds exact file transfer for
Claude Docs, verified with a 52 KB synthetic cloud notebook, plus Claude's smaller
block limit and clearer blocked-send guidance. Check the installed version and
storage tools in the presenting account before a live demo. See the [current demo guide](docs/demo-start-here.md),
[Claude investigation](docs/claude-cloud-memory-investigation.md), and
[28 October acceptance history](docs/acceptance-2026-10-28.md) for evidence and
remaining host limitations. Run the [rollout checks](docs/rollout.md) before
inviting researchers through a particular app route.

A research sitting can continue across conversations. New roles save an
appropriate scientific output and a decision before concluding; they can discuss
a method, result or paper without inventing a hypothesis. `/pi` keeps its
hypothesis requirement. Pausing leaves the sitting open; closing a chat is not
recorded as abandonment.

## Private records

The append-only journal lives outside Git: in the private native notebook for
cloud accounts, or by default at `~/.local/share/benchside/projects/<id>/journal.jsonl`
for local desktop use. The runtime records
hypotheses, targeted critiques and resolutions, decisions with rationale,
role-specific scientific outputs with sources, and local workflow observations.
It restores the project record and unfinished sittings when you return.

Optional legacy Claude Code hooks inject recall and archive transcripts. Session
identity is passed to each conversation's shell, so concurrent conversations
are not all attributed to whichever one started last.

## Optional sharing

One flow offers three independent choices: workflow observations, usability
feedback and weekly usage reporting. All are off until consented, and every
submission needs an exact preview and approval.

- Workflow observations capture general research-workflow friction and problems
  for metascience research, using the five existing problem types in a `benchside.gaps.v2` envelope (v3 when optional public tool/dataset context is included). They
  exclude project and session IDs; a random contributor ID supports grouping. Free text is scrubbed
  and reviewed because a schema cannot guarantee anonymity.
- Feedback contains an ease-of-use rating, repeat-use intent and optional comment.
- New contributions share a pseudonymous store ID across channels; participation
  stays opt-in. Existing participants must accept this change before linked sharing.
  Historical unlinked contributions remain unlinked.
- Usage contains weekly counts and role/app/version information, with a random
  installation ID to estimate returning use. It never contains research text.
- Prepared drafts can select or edit observations. Sending verifies the consent,
  reviewed digest, destination, size limits and collector receipt. Retrying a
  successful draft does not send it again.
- Revoking consent stops future reporting. Receipts support review and
  operator-assisted removal of earlier submissions.

The Science Works endpoint is included in the product; researchers configure no
credentials. All five collection routes from the companion
`science-works/benchside-ingest` repository were deployed and verified with
synthetic records on 28 October. The matching linked formats and optional-context
v3 format were deployed and verified by 29 October. App network access and
research release checks still apply; deployment does not authorise collection
from researchers. Claude's current account network setting still blocks its
cloud execution from contacting the receiver until access is explicitly enabled.

## Optional studies and wider observation

The app skill also supports occasional study invitations and private analysis
of selected research conversations, including work without a Benchside role.
These are separate opt-in choices, with reviewed sharing as a third choice.
Invitations are capped at one per week. Analysis covers up to 20 relevant research
conversations from the previous complete week: automatically take all when there
are 20 or fewer, randomly select 20 when there are more, or let the researcher
choose up to 20. Both methods share one fixed weekly batch and are labelled and
reported separately. Reviewed workflow problems are the primary output and use
the gaps collector. Fixed activity categories provide supporting context, marked
as work with or without a Benchside role. No raw logs or private research records
are submitted. New reports carry the random contributor ID. A centrally published
catalog supports new surveys without reinstalling the client. Surveys support
fixed options and researcher-written text. Agreement comes before the questions;
answers are then sent as written without a second approval prompt.

See [the metascience implementation and review guide](docs/metascience.md).
The survey/activity routes are deployed. The released catalog starts empty,
and installation creates no background listener or schedule. Scheduled checks
depend on explicit researcher setup and the host's available tools.

## Git and terminal installation

This route remains available alongside plugins and in-app skills. An agent with
local execution tools can perform installation and setup for the researcher.
An agent can read [the setup flow](content/app/references/onboarding.md), install
from source, and run the same JSON interface used by the plugins. Setup asks for
a local directory, private native documents, or a compatible installed connector.
Claude and Codex can continue the same project in a shared accessible store.
The expanded review build has not yet been published to the default Git branch.
Before merge, use the
[review branch](https://github.com/WilliamBolton/benchside/tree/codex/research-roles-rollout)
and its guided setup. The default-branch install below becomes the route for
these expanded features after the reviewed merge.

```bash
uv tool install git+https://github.com/science-works/benchside
bench setup
bench init
```

The default commands install one shared entry for all seven roles. For Codex use
`bench setup --agent codex`; for another agent use `bench setup --agent generic
--skills-dir <its skill directory>`. The shared Benchside skill includes every
role and an entry script that remembers its source runtime, with no Claude hooks required.
Later conversations can use it outside the checkout without `bench` on PATH. If the
source environment is moved or removed, the agent can reinstall it and rerun setup
for the same skill location; research storage stays separate. An agent can perform
these steps for the researcher. `--storage /absolute/chosen/folder` remembers an
explicit local choice; native or connected memory is chosen through guided setup.

`bench init` installs the shared skill without transcript hooks. For explicit
legacy Claude Code role commands and session hooks, use `bench init --legacy-cli`;
those role skills require explicit invocation. Shared setup marks only recognized,
unedited generated legacy skills this way and preserves customized skills.
Legacy CLI project journals are separate from app project IDs. Choose to continue
an existing CLI journal or explicitly migrate it before starting an app project;
setup does not silently migrate or merge records.

```text
sitting open|resume|status|close   manage a research discussion
hypothesis, critique, resolve,
decide, record, gap               record scientific work and workflow problems
journal <view>, recall            read the project record
share status|grant|revoke         control the three sharing choices
share feedback|preview|send       review optional submissions
share history                    inspect receipts
```

For sharing, `bench share grant --channel gaps --kinds missing_index` enables
that choice. `bench share preview` saves a draft; `bench share send --draft <id>
--approve-sha256 <reviewed digest>` submits exactly that draft. Use `--channel
feedback` or `--channel usage` for those choices, and `bench share revoke
--channel all` to stop all reporting. Scientists can do this through the
assistant instead of typing commands.

## Development and packaging

```bash
uv sync --frozen
uv run pytest
uv run ruff check benchside
uv run bench compile --check
uv build --wheel
uv run --with pip python scripts/build_release.py
```

Personas are YAML records; edit their sources and run `bench compile`. The app
package uses the same records, core wheel and pinned dependency lock. Build
outputs are `dist/benchside-claude-0.3.1.zip` (standalone skill),
`dist/benchside-plugin-0.3.1.zip` (OpenAI/portable plugin), and
`dist/benchside-claude-plugin-0.3.1.zip` (Claude plugin upload). All use the same
core and central submission endpoints. The build downloads hash-locked wheels
for CPython 3.11–3.14 on macOS (Intel/Apple Silicon) and glibc Linux (x86-64/ARM64).
Installed app packages bootstrap offline; they do not need access to PyPI.

Generate an aggregate rollout report from authorised collector downloads with
`python -m benchside.reporting <directory>` (or add `--json`). It deduplicates
retries and replaces earlier weekly snapshots, without joining individual
submissions across channels. Installation counts are not exact people.

[ARCHITECTURE.md](ARCHITECTURE.md) explains the implementation.
[Rollout notes](docs/rollout.md) describe the remaining live-app checks and keep
the original workshop evaluation separate from exploratory rollout results.

## License

Apache 2.0
