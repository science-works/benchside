# Set up Benchside for the researcher

This is the entry point for an agent asked to install Benchside from the
[repository](https://github.com/science-works/benchside). Perform the supported
steps yourself; the researcher should not have to run terminal commands.
Benchside needs no model API key or Science Works account.

## 1. Check the app and any existing installation

Inspect the tools actually available: code execution, durable local files,
plugin/skill installation, and native or connected document storage. The runtime
needs Python 3.11–3.14 on macOS or Linux. A browser chat's execution directory is
temporary; it is not durable research storage.

If Benchside is already installed, read its `SKILL.md` and run its entry script to
check the version. Reuse the chosen storage and existing projects. Do not install
a second copy or replace custom files just because the user supplied this link.
Use the installed onboarding guide for an update or storage change.

## 2. Install through the route the app supports

### Local agent: Codex, Claude Code or another capable agent

1. Read the [latest release](https://github.com/science-works/benchside/releases/latest)
   and identify its tag. Clone `https://github.com/science-works/benchside` into a
   durable installation directory and check out that tag. Keep this checkout:
   the installed skill refers to its Python environment. If updating an existing
   checkout, inspect its changes first and preserve custom work. Use `main` only
   when the researcher requests a development version.
2. In that checkout, use an available package manager to install the runtime.
   With `uv`, run `uv sync --frozen`. Without `uv`, use Python 3.11–3.14 to create
   a virtual environment and install the checkout into it with `pip install .`.
   Do not install Benchside globally into the operating system's Python.
3. Install the shared seven-role skill with **one** matching command:

   | Host | Command from the checkout |
   |---|---|
   | Codex | `uv run bench setup --agent codex` |
   | Claude Code | `uv run bench setup --agent claude` |
   | Another agent | `uv run bench setup --agent generic --skills-dir <actual host skill directory>` |

   With a Python virtual environment instead of `uv`, invoke that environment's
   `bench` executable with the same arguments. Observe the generic host's skill
   directory; do not guess it. These commands install for future conversations.
   A project-scoped installation is available through `bench init`; it is not
   an additional required setup step.
4. Read the installed `benchside/SKILL.md`, then its onboarding and app API
   references. Follow them to complete setup and begin the research discussion.
   Use the installed `scripts/benchside_app.py` entry point; source setup records
   its runtime location so later chats can work outside the checkout.

If cloning or package installation is unavailable, explain the missing
capability and offer a supported app package. Do not claim that downloading or
reading a Markdown file installed a working runtime.

### Hosted app: ChatGPT, Claude or another plugin-capable app

Use the installation tools actually exposed by the host. Package availability
does not guarantee that a particular account can install custom plugins.

| Available installation flow | Asset in the latest release |
|---|---|
| Claude custom plugin | `benchside-claude-plugin-<version>.zip` |
| OpenAI / portable custom plugin | `benchside-plugin-<version>.zip` |
| Claude custom skill | `benchside-claude-<version>.zip` |

Download the appropriate asset from the release, keeping the ZIP intact for
upload. GitHub's generated **Source code** archives are not plugin packages.
If the host exposes an installation tool, use it under its normal permission
flow. Otherwise give the researcher the direct asset link and the relevant
plugin/skill upload step, then continue when it is installed. Do not ask them to
build a package or open a terminal. A private plugin belonging to someone else
is not a public installation link.

After installation, read the packaged skill and follow its onboarding flow.
Do not claim automatic installation or discovery in a fresh chat unless verified.

## 3. Keep first setup short

Follow [guided onboarding](content/app/references/onboarding.md) rather than
inventing a second setup process. Ask only what is not already known:

- **Where should private records live?** Offer a durable local folder outside
  Git, private app-native storage or a compatible connected store. Check actual
  read, guarded-write and readback tools before offering cloud storage.
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

Then return to the researcher's real project and start their first task.

## Updating later

Use a newer versioned release and the app's complete update flow. For a source
installation, update the checkout/environment and rerun the matching `bench setup`
command. Keep private storage in place and reopen the existing project. Preserve
custom files; do not unzip a package over a source installation, whose saved
runtime pointer could keep launching the older version. See the
[full update guidance](content/app/references/onboarding.md).
