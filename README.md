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

We welcome researchers' own scientific role profiles and improvements through
[pull requests](CONTRIBUTING.md). Our longer-term goal is a community where
researchers can discover tools and workarounds that helped others with similar
problems. **That community recommendation service is not built yet.** Today,
Benchside offers private research support and optional reviewed workflow sharing.
Read [the purpose and community direction](docs/community.md).

## Start here

Give your agent this message:

> Set up Benchside for me in this app: https://github.com/science-works/benchside

The agent should handle finding the installer, choosing and downloading the
package, and guiding setup. You do not need to know the installer's name or which
ZIP to choose. It may ask you to approve a connection or installation, then ask
where to keep your private records and whether you want optional research sharing.

**Agents: follow [SETUP.md](SETUP.md)** when asked to install or set up Benchside.
If that file cannot be fetched, the essentials below let you establish an
installation route without asking the researcher to upload Markdown files.
Researchers should not need terminal commands or API keys; app-required
installation approvals may still need their action.

### Agent setup essentials

1. Use the app the researcher specified. Check for an existing Benchside
   installation and reuse it. Inspect actual installation, execution and storage
   tools before promising setup. Benchside bundles skills and a Python runtime;
   **it does not require an MCP server**.
2. In ChatGPT, discover **Plugin Creator** through the available plugin tools
   if creation tools are not already loaded. Do this from the setup request;
   do not wait for the researcher to mention Plugin Creator or select it with `@`.
   Use it to install the existing
   release package unchanged, rather than generate a replacement. If connecting
   it requires approval, present that connection step. An absent `@` result
   alone does not establish that creation is unavailable.
3. For a supported app installer, use the matching ZIP from the
   [latest release](https://github.com/science-works/benchside/releases/latest):
   `benchside-plugin-<version>.zip` for OpenAI/portable flows or
   `benchside-claude-plugin-<version>.zip` for Claude plugins. Keep it intact.
   These contain the same Benchside code; their archive layouts suit different
   installers. If another variant is already installed and its runtime works,
   continue verification rather than reinstalling solely because of its filename.
   Attaching a ZIP to an ordinary chat is not itself installation. If only a
   manual installer is available, give its observed steps; if neither route is
   available, state the missing capability rather than invent an upload control.
4. Local agents can clone the latest released tag into a durable installation
   directory, run `uv sync --frozen`, then `uv run bench setup --agent codex`
   (or `claude`, or `generic --skills-dir <actual host skill directory>`).
   Preserve custom work and read [SETUP.md](SETUP.md) for alternatives.
5. Read the installed skill and its onboarding guide. Run the actual runtime
   version check, then inspect storage tools without writing and offer suitable
   candidates as not yet verified. Test writes only after the researcher chooses
   the store, using a labelled synthetic project.
   Ask where private records should live, which project to use, and about optional
   research participation once those preferences can be saved.
   Store journals outside Git; a disposable execution directory is not memory.
   Do not submit research records or test submissions during setup.
6. Verify the installed version and an isolated synthetic save/readback/restore.
   Report whether fresh-chat recall was actually tested. Only then describe
   installation and memory as working; preserve existing records and preferences.

**Which setup to use:** for ChatGPT web, our current recommended route is a paid
account with verified execution and private storage tools. The tested free web
account could install an uploaded ZIP but could not complete recording or sending.
Claude's paid-account workflow has passed; a researcher-reported free-account
test also installed the plugin and reached native notebook setup, but paused at
the usage limit before full verification. Check actual tools rather than rejecting
an account by plan name. Local
agents can use the generic installer with other providers or locally hosted
models when their tools meet the same requirements. See the
[support and testing plan](docs/host-support.md) and
[Getting started](docs/getting-started.md). A [researcher-run OpenCode check](docs/acceptance-opencode-free-2026-11-06.md)
with its free GLM model completed local recording and an approved gap submission;
that run used 0.3.1 and does not establish on-device inference or every provider.
There is no public Benchside
plugin-directory listing yet.

## Research roles

All eight roles are included:

| Role | Scientific output |
|---|---|
| `/pi` | Research direction, decisions, unresolved questions and next step |
| `/pi-hypothesis` | Focused hypothesis challenge and discriminating experiment |
| `/study-design` | Study outline, comparisons, controls and assumptions |
| `/methods-clinic` | Discrepancy, possible causes and diagnostic checks |
| `/results-meeting` | Evidence-to-claim assessment and follow-up |
| `/repro-check` | Reproducibility and handover checklist |
| `/journal-club` | Source-grounded appraisal of accessible papers |
| `/peer-review` | Major/minor scientific concerns and revision priorities |

## Guided app setup

See [Getting started](docs/getting-started.md) for setup without terminal commands
or API keys. Installable Claude and ChatGPT/Codex packages are built from this
repository. The current package is 0.4.0. There is no public plugin-directory
listing yet. Give a new agent the repository URL and
[setup instructions](docs/getting-started.md)
rather than relying on discovery by name alone.

Version 0.4.0 adds capability-based onboarding, lighter setup, multi-discipline
profiles, a broad research supervisor and a focused hypothesis reviewer. Decisions
and unresolved questions are saved privately as the discussion progresses. See
[the release notes](docs/release-0.4.0.md), including the shared-store update note.

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
a method, result or paper without inventing a hypothesis. `/pi` is broad supervision;
`/pi-hypothesis` keeps the focused hypothesis requirement. Pausing leaves the sitting open; closing a chat is not
recorded as abandonment.

## Private records

The append-only journal lives outside Git: in the private native notebook for
cloud accounts, or in the chosen local store. New configured local stores use
`agent/projects/<id>/journal.jsonl` for internal state and
`researcher/projects/<friendly name>/Research record.odt` for the complete readable
record by default. Setup offers ODT, Markdown or both and remembers the choice
for that store. Existing flat stores remain supported;
see [the folder guide](docs/readable-records.md) before upgrading one. The runtime records
hypotheses, targeted critiques and resolutions, decisions with rationale,
research questions and their answers,
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
from researchers. Claude cloud execution may need the receiver domain allowed
in the account's network settings before approved submissions can be sent.
Local Claude Code execution uses the computer's network access.

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
The expanded implementation is merged into `main`. Prefer the latest released
tag for installation; [SETUP.md](SETUP.md) explains how an agent selects it.
For a source checkout, the agent can run:

```bash
uv sync --frozen
uv run bench setup --agent codex
```

This installs one shared entry for all eight roles. Use `--agent claude` for
Claude Code or `--agent generic --skills-dir <its skill directory>` for another
agent. Then follow guided onboarding; `bench init` is only needed when choosing
a project-scoped installation. The shared Benchside skill includes every
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
outputs are `dist/benchside-claude-0.4.0.zip` (standalone skill),
`dist/benchside-plugin-0.4.0.zip` (OpenAI/portable plugin), and
`dist/benchside-claude-plugin-0.4.0.zip` (Claude plugin upload). All use the same
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
