# Set up Benchside for the researcher

This is the entry point for an agent asked to install Benchside from the
[repository](https://github.com/science-works/benchside). Perform the supported
steps yourself; the researcher should not have to run terminal commands.
Benchside itself needs no model API key or Science Works account. The host agent
supplies the model: its connection may use a provider API, OpenRouter, or a
locally hosted model, with any credentials managed by that agent. Use the generic
route below for other agents; reliable tool use and durable storage are required.

The researcher should only need to ask to set up Benchside and provide the
repository link. Discover the installer, select and download the right package,
and perform the supported installation yourself. Do not require the researcher
to know about Plugin Creator, name this file, choose a ZIP or repeat the request
with special installation terminology. Ask for their action only when the host
requires a connection/approval or a step you cannot perform with available tools.

Benchside is a package of skills and a Python runtime, not an MCP service.
Do not create or configure an MCP server to install it. The Science Works
ingestion address is an HTTPS submission API, not an MCP connection URL.

If a web reader returns a cache miss for this file or a release page, do not
conclude that the repository is missing or private. Try the normal GitHub file
page or an available permitted file-fetch/clone tool; raw-file URLs can also fail
in web readers. The repository README contains the essential installation checks.
Do not repeatedly ask the researcher to upload instructions, especially when the
actual blocker is lack of an installation tool.

## 1. Check the app and any existing installation

Use the app already specified by the researcher; ask only if the destination is
unclear. Distinguish the app's visible installer from tools the agent can invoke.
Inspect the tools actually available: code execution, durable local files,
plugin/skill installation, and native or connected document storage. The runtime
needs Python 3.11–3.14 on macOS or Linux. A browser chat's execution directory is
temporary; it is not durable research storage.
Use the [support guidance](docs/host-support.md) to explain tested routes, but
check actual tools rather than accepting or rejecting an account solely by plan
name. Private recording and optional network sending are separate capabilities:
blocked networking does not prevent a working local journal from being used.

If Benchside is already installed, read its `SKILL.md` and run its entry script to
check the version. Reuse the chosen storage and existing projects. Do not install
a second copy or replace custom files just because the user supplied this link.
Use the installed onboarding guide for an update or storage change.

## 2. Install through the route the app supports

### Local agent: Codex, Claude Code or another capable agent

1. Install the [published Python package](https://pypi.org/project/benchside/).
   With `uv`, run `uv tool install benchside`. This creates a persistent isolated
   runtime; use its installed `bench` command. If the executable is not yet on
   the agent's PATH, locate it with `uv tool dir --bin` and invoke its full path.
   Without `uv`, create a persistent Python 3.11–3.14 virtual environment and
   run that environment's `python -m pip install benchside`. Keep the environment
   and use its `bench` executable. Do not use the operating system's global Python
   or a disposable execution directory for this installation.
2. Install the shared eight-role skill with **one** matching command:

   | Host | Command |
   |---|---|
   | Codex | `bench setup --agent codex` |
   | Claude Code | `bench setup --agent claude` |
   | Another agent | `bench setup --agent generic --skills-dir <actual host skill directory>` |

   Observe the generic host's skill
   directory; do not guess it. These commands install for future conversations.
   A project-scoped installation is available through `bench init`; it is not
   an additional required setup step.
3. Read the installed `benchside/SKILL.md`, then its onboarding and app API
   references. Follow them to complete setup and begin the research discussion.
   Use the installed `scripts/benchside_app.py` entry point; setup records
   its runtime location so later chats can work outside the checkout.

The package name is `benchside`; the executable is `bench`. A model, provider
connection and the agent's tools come from the host, not from the Python package.
Do not use a one-off `uvx` environment for persistent setup.

**Source installation remains available:** identify the tag in the
[latest release](https://github.com/science-works/benchside/releases/latest),
clone `https://github.com/science-works/benchside` into a durable directory and
check out that tag. Run `uv sync --frozen`, then the matching command above with
`uv run` before `bench`. Without uv, install the checkout into a persistent
virtual environment with `python -m pip install .`. Keep the checkout/environment;
the installed skill refers to it. Preserve custom changes when updating, and
use `main` only when the researcher requests a development version.

If package installation is unavailable, explain the missing
capability and offer a supported app package. Do not claim that downloading or
reading a Markdown file installed a working runtime.

### Hosted app: ChatGPT, Claude or another plugin-capable app

Use the installation tools actually exposed by the host. Package availability
does not guarantee that a particular account can install custom plugins.

In ChatGPT, if creation tools are not loaded, use the available plugin discovery
tools to find **Plugin Creator** and connect/select it through the supported
flow as part of the original setup request. Do not wait for a user mention of
Plugin Creator. If that requires researcher approval, present it. Its absence from an `@`
search is not conclusive: a new free-account test found plugin creation in the
Plugins UI even though it was missing from that menu. Do not infer agent access
from the presence of a manual UI, or infer that an account upgrade is necessary.
OpenAI documents plugin creation as conditional on permissions and Plugin
Creator availability; it does not establish this account's capabilities.
See [OpenAI's plugin creation guide](https://learn.chatgpt.com/docs/build-plugins).

| Available installation flow | Asset in the latest release |
|---|---|
| Claude custom plugin | `benchside-claude-plugin-<version>.zip` |
| OpenAI / portable custom plugin | `benchside-plugin-<version>.zip` |
| Claude custom skill | `benchside-claude-<version>.zip` |

The two plugin archives contain the same skills, Python runtime and Claude/Codex
manifests. The portable archive wraps them in a `benchside/` directory; the Claude
plugin archive places them at the ZIP root. The standalone skill archive contains
the skill directory without the plugin wrapper. These are installer formats, not
different scientific capabilities or model-specific runtimes. Prefer the documented
format for a new installation, but if the host already accepted another variant,
inspect the installed skill and run its version action. Do not require reinstallation
solely because the uploaded filename differs. A successful check of one variant in
one account does not establish that every installer accepts every layout.

Download the appropriate asset from the release, keeping the ZIP intact for
upload. GitHub's generated **Source code** archives are not plugin packages.
If the host exposes an installation tool, use it under its normal permission
flow to install the existing package unchanged, not generate a new approximation
of Benchside. Otherwise, if a manual package installer is actually available,
give the researcher the direct asset link and its observed upload step, then
continue when it is installed. Do not ask them to build a package or open a
terminal. A private plugin belonging to someone else is not a public installation
link, and an ordinary chat attachment is not proof of installation.

If neither tool nor manual package installation is available, state that setup
is blocked in this account and name the missing capability. Reading role prompts
is not a substitute for the runtime, saved memory or approved submissions. Offer
another supported route without claiming it works in this account. Do not ask
storage and consent questions as though installation has succeeded.

After installation, read the packaged skill and follow its onboarding flow.
Do not claim automatic installation or discovery in a fresh chat unless verified.
Tests in an already configured account do not establish first-time installation
support in another account. The [free-account test](docs/acceptance-free-account-2026-11-04.md)
reports installation from a researcher-uploaded ZIP, but has not verified an
automatic download, runtime execution or saved memory.
The separate [free-Claude report](docs/acceptance-free-claude-2026-11-05.md) reached
native notebook setup after manual plugin upload before a usage-limit pause.
Neither report establishes a complete fresh-account workflow yet. Do not treat a
custom skill as a guaranteed workaround for a plan or tool restriction; inspect
whether that installation route and the required runtime/storage tools exist.

## 3. Keep first setup short

Follow [guided onboarding](content/app/references/onboarding.md) rather than
inventing a second setup process. Ask only what is not already known:

- **Where should private records live?** Offer a durable local folder outside
  Git, private app-native storage or a compatible connected store. Check actual
  read, guarded-write and readback tools before offering cloud storage.
  For local records, offer ODT (default), Markdown or both once alongside this
  choice; preserve the saved preference on return. Follow onboarding to save it.
- **Which project?** List existing projects in that store and continue the
  selected one, or create a separate new project. Never merge projects by title.
- **Optional metascience participation?** Explain the independent choices and
  preserve existing preferences. Declining or deciding later never blocks use.

Offer the optional discipline/career-stage question as described in onboarding;
it is not required. Then ask what the researcher wants help with and choose a
suitable role. They do not need to learn slash commands or choose a permanent role.

Private records and optional submissions are separate. Do not upload notebooks
or research documents to Science Works. Setup consent does not approve a gap,
feedback, usage or activity submission; those need an exact preview and approval.
Surveys use the agreement shown before their questions. No sharing or network
test should submit data as part of installation.

## 4. Verify and explain the result

First invoke the installed `scripts/benchside_app.py` with
`{"action":"version"}`. Reading a manifest or validating a wheel hash does not
verify that the runtime can execute. This check needs no research notebook or
collector request. If execution is unavailable, identify that missing capability.

Use the storage checks in onboarding and the
[native-memory guide](content/app/references/native-memory.md) where applicable.
Save and read back a clearly synthetic decision in an isolated test project;
keep it separate from real research records and do not submit it. Verify restore
from the saved store. When the host supports a separate conversation, check
discovery and recall there too; otherwise give the researcher one follow-up:

> In a new chat, ask Benchside to reopen the setup test and recall its decision.

Report the installed version, storage location, project, saved participation
choices, and whether fresh-chat restoration was actually checked. Do not describe
a same-process readback as a fresh-chat test. Failed or unsupported storage must
be reported as unverified; never claim unsaved work is saved.

If no supported durable store is accessible, report that the plugin may be
installed but the research journal is not set up. A path supplied by a researcher
does not grant a browser chat access to their computer. Do not invent a folder
of Markdown files and present it as Benchside's journal or substitute it for the
runtime's record format. If the researcher separately requests manual notes,
explain that they require manual download/upload and do not provide Benchside's
verified recording, recall or persisted sharing choices. Ordinary scientific
discussion can continue, with its unsaved status made clear.

Then return to the researcher's real project and start their first task.

## Updating later

Use a newer versioned release and the app's complete update flow. For a uv tool
installation, run `uv tool upgrade benchside`; for pip, run the installation
environment's `python -m pip install --upgrade benchside`. Then rerun the same
`bench setup` command to refresh the installed skill, including the same skills
directory for a generic host. For a source installation, update the
checkout/environment and rerun setup there. Keep private storage in place and
reopen the existing project. **Every app sharing a notebook saved by 0.4.1 must
use 0.4.1 or newer**, including apps previously using 0.4.0. Preserve
custom files; do not unzip a package over a source installation, whose saved
runtime pointer could keep launching the older version. See the
[full update guidance](content/app/references/onboarding.md).
