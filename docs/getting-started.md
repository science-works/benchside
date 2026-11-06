# Getting started with Benchside

Benchside offers eight research roles: a supervisor, focused hypothesis reviewer, study-design consultant,
methods troubleshooter, results discussant, reproducibility auditor, journal-club
discussant and scientific peer reviewer.

## The simplest way to start

Give your agent this message:

> Set up Benchside for me in this app: https://github.com/science-works/benchside

You do not need to name an installer or choose a ZIP. The agent should find the
installation route, download the right package, guide your project and private
storage choices, explain optional sharing, and check that records can be restored.

The [agent setup guide](../SETUP.md) tells an agent how to install, reuse an
existing installation and verify storage. With local execution tools, the agent
can perform the installation. In a hosted app, it discovers and uses the app's
installation tools first. You may need to approve a connection or installation.
If only a manual installer is available, the agent gives its actual steps; it
must not invent a missing upload control. You should not need terminal commands
or API keys. If the agent cannot fetch `SETUP.md`, the
[README's setup essentials](../README.md#agent-setup-essentials) provide a fallback.

Benchside needs no MCP server. Its package contains the skill and Python runtime;
the receiving HTTPS API is already operated by Science Works.

### ChatGPT account checks

The agent's setup instructions tell it to discover and use **Plugin Creator**
when needed; you should not have to know about it or mention it in your request.
If enabling a tool needs your approval, the agent should present that step and
continue afterward. It should explain any manual-only step or missing capability
in your account rather than send you through repeated setup requests.

In the new free-account test, the agent reports **successful plugin installation
after the researcher uploaded the release ZIP**. It could not download the ZIP
itself. Runtime execution and persistent memory are **not yet verified**: the
follow-up chat reported no suitable native storage or available Google Drive
connection. Earlier ChatGPT memory tests used an already configured paid account.
These observations do not establish which capabilities every free account has.
See the [test notes](acceptance-free-account-2026-11-04.md) and
[OpenAI's conditional creation requirements](https://learn.chatgpt.com/docs/build-plugins).

Installing the plugin does not grant access to your computer's folders or add
a storage connector. If your chat has no supported storage route, the agent
should explain that the journal is not set up. A folder of manually downloaded
notes is a separate workflow, not verified Benchside memory.

## Choose an installation route

For the current rollout, use a paid ChatGPT web account with verified runtime
and private storage tools, a paid Claude plugin-capable account after the same
checks, or a capable local agent. Paid status alone does not establish those
capabilities. Free ChatGPT web is not currently supported for the complete
recording and sharing workflow. See the [support and testing plan](host-support.md)
for evidence, the generic local route and outstanding fresh-user checks.

Benchside is one research toolkit with several delivery methods. “App package”
means the installable bundle, not a separate Benchside chat app or a replacement
for the Git/terminal route. A plugin packages skills and their supporting runtime.

| Route | Current implementation |
|---|---|
| Python package (pip or uv) | The agent runs `uv tool install benchside`, or `python -m pip install benchside` inside a persistent virtual environment, then the matching `bench setup` command below. No checkout is required. |
| Clone GitHub and ask an agent to set it up | Install source dependencies and run guided setup. The installed skill remembers the runtime so later chats work outside the checkout. No model-specific backend is needed. |
| Codex or another local agent | `bench setup --agent codex` or `--agent generic --skills-dir <host directory>` installs the shared eight-role skill. The agent runs setup for the researcher. |
| Terminal / Claude Code | Shared skill through `bench setup --agent claude` or `bench init`; explicit `bench init --legacy-cli` provides legacy role commands and local session hooks. |
| OpenAI plugin | `benchside-plugin-0.4.1.zip` includes the portable manifest, Codex compatibility manifest, setup entry and bundled skill/runtime. |
| Claude plugin | `benchside-claude-plugin-0.4.1.zip` includes `.claude-plugin/plugin.json`, the shared skill, role references and runtime. The manifest passes Claude's validator. |
| Claude standalone skill | `benchside-claude-0.4.1.zip` remains available for custom-skill installation. |

Download app packages from the [latest GitHub release](https://github.com/science-works/benchside/releases/latest).
The local Python package is also on [PyPI](https://pypi.org/project/benchside/).
It installs the runtime, not a web-app plugin or a model. For source installs,
agents should use the latest released tag unless you ask for a development version. No public plugin
directory listing has been published.
Package validation does not replace installation, discovery and fresh-chat memory
checks in the intended app/account.

Name-only discovery is not guaranteed: give the repository URL. Reading a GitHub
page does not install a plugin. Keep the release ZIP intact for app uploads;
GitHub's automatic **Source code** download is not an app package. In Claude,
use Plugins (or Customize → Plugins) for the Claude plugin ZIP, or Skills for
the standalone skill ZIP. In OpenAI apps, use the custom-plugin flow available
to the intended account. Uploading the ZIP as a chat attachment alone is not
installation.
Another person's private OpenAI listing is not an installation link for colleagues.

Once installed, test recognition in a fresh conversation. If the host does not
discover installed skills automatically, explicitly select Benchside or reference
the installed skill. Do not claim fresh-chat discovery until tested.

## First research project

After installation, say:

> Set up Benchside for this research project.

Benchside guides you through choosing a project and checking that its records
will remain available. Then describe the scientific work you want help with:

> My extraction yield has fallen. Help me work out what to check next.

> Help me decide what these results actually support.

> Review the scientific claims and methods in this draft.

When you return to the same project, ask Benchside to continue. It recalls
recorded decisions, unresolved questions and open discussions. You can switch
roles as the work changes.

Setup asks where you want your records stored and shows accessible choices:

- A durable folder on this computer, outside Git. The choice is remembered for
  other agents on the same OS account. Claude and Codex can select the same project.
- A private Benchside Space/collection in your app. The notebook is restored on
  each conversation; the execution sandbox is disposable.
- A private location in an installed cloud connector, if its tools support
  complete reads, conditional updates and readback. Google Drive and Google Cloud
  Storage are different services; setup checks the connector actually available.

For existing records, setup lists projects and reuses the one you choose. It never
merges projects by title, copies records elsewhere, or changes their sharing settings.
Choosing an existing project restores its decisions and open discussions; choosing
new starts a separate project journal. All roles remain available in either case. Setup
reuses the current project when it is already clear.
Two apps can use the same cloud notebook if both can access that location and
safely update it. Separate Claude/OpenAI accounts are not automatically connected.
A folder synchronized between two computers is not a substitute for coordinated
cloud writes; filesystem locks work on one machine, not across sync clients.

Decisions come from that chosen private store, never from the metascience receiver.
For newly configured local storage, events are in
`<chosen folder>/agent/projects/<project ID>/journal.jsonl`, with readable
ODT/Markdown copies under `researcher/projects/`. Existing flat stores remain
supported; see [the folder guide](readable-records.md).
For native/connected storage, the private Benchside memory document contains the
validated records, and each project has a readable journal document. A single
private memory document can hold several isolated projects.

Cloud storage must pass a save/readback and restore check in your account.
Benchside uses guarded updates to avoid replacing a newer notebook. Claude
0.3.1 transfers notebooks as files and respects Claude Docs' smaller block limit;
if the exact transfer is unavailable, the agent must report that work was not
saved. Update all apps sharing a notebook together: notebooks saved by 0.4.1
require every app to use 0.4.1 or newer.

ChatGPT Pages, Claude Docs and supported Google Docs connectors have passed
synthetic checks in the tested accounts. Other accounts and connectors can expose
different tools. A connector that only searches or reads cannot keep a journal;
setup should offer another location. No Google connector or storage credentials
are bundled. Claude's native Docs tools do not expose sharing permissions, so
verify privacy in the document UI. Details are in the
[acceptance history](acceptance-2026-10-28.md),
[Claude transfer findings](claude-memory-and-sending-findings-2026-10-29.md), and
[demo guide](demo-start-here.md).

Memory depends on the agent's tools, not its model. The runtime needs Python 3.11+
and a POSIX execution environment, plus access to the chosen storage. Ordinary
chat without execution/storage tools cannot automatically record or submit data.

For Claude plugin review, upload the Claude **plugin** ZIP in Customize → Plugins,
using the custom-plugin upload option available to your account. The standalone
**skill** ZIP goes through Customize → Skills instead. For a local Claude Code
review, the agent can load `plugins/benchside` with `--plugin-dir` after building
the package. These routes do not publish a listing or deploy any backend.
See [Claude's installation guidance](https://support.claude.com/en/articles/13837440-use-plugins-in-claude)
and [manifest reference](https://code.claude.com/docs/en/plugins-reference).

For updates, use your app's plugin replacement flow. An agent handling a manual
installation should stage the new release in a clean directory and preserve any
customizations before replacing the managed installation. Do not unzip a package
over an earlier source installation: old runtime settings and removed files can
remain active. Keep research records in their existing storage and reopen the
same project after updating.

For the optional legacy CLI route, conversation identities normally come from
Claude's per-conversation environment. The compatibility fallback in the project
registration expires after 24 hours; an explicit conversation ID still takes
precedence. Expired registrations and their pointers are retired without closing
unfinished sittings or changing scientific records. Switching to the shared skill
clears that project's legacy registrations because its lifecycle hooks are removed.
If a crash leaves several recent registrations, ask the agent to identify the
ended conversation and run `bench session clear --project <project> --session <ended-id>`.
The error lists the registered IDs. Clear only an ended conversation, then resume
the chosen unfinished sitting explicitly if needed. Researchers can request this
recovery in chat; they do not need to open a terminal.

If `.claude/settings.json` is a symlink (a shortcut to shared settings), legacy
`bench init --legacy-cli` stops before writing setup files or changing the storage
preference. The error names the shortcut and its destination. Benchside does not
replace the shortcut or write through it. Default `bench init --agent claude`
can leave it alone unless old Benchside hooks need removing; in that case the
agent should explain the shared-file implications before the researcher chooses
how to remove them. Manual legacy hook configuration can use
`.claude/settings.local.json` for this project, or the shared file if every linked
project should receive those hooks. Automatic legacy init still requires a
regular `.claude/settings.json` file; manually adding hooks does not complete
Benchside's remaining setup steps.

## Optional sharing

During first setup, Benchside asks whether you would like to contribute to
Science Works' metascience research. You can choose what to contribute, keep
everything private, or decide later. The choices cover workflow observations,
usability feedback, usage counts, optional surveys and selected-conversation
analysis. For analysis, you choose the sources and separately decide whether its
workflow categories stay in your private notebook or are prepared for reviewed
sharing. Examples include "coding", "tool failure" and "checked sources".
Scientific findings and research-specific details are never eligible for
metascience submission. Free-text workflow observations and feedback must also
be generalised to remove those details before preview.

These preferences apply to the chosen Benchside store, including other apps using
it. Existing choices are kept when you return. Nothing is preselected, and setup
consent does not authorize automatic submissions.

You can independently choose to share workflow problems, usability feedback,
and usage counts with Science Works. The assistant shows the proposed content
and recipient before sending it, and you can edit or exclude items. Scientific
notes and source documents stay in your project record.

New contributions use a random pseudonymous store ID across sharing channels,
including workflow observations, feedback and usage, after consent to linked
sharing. Existing unlinked participants must accept this change first; historical
unlinked records remain unlinked. It describes a participating store, not an exact
person. You can stop any reporting choice at any time and ask to see previous
submission receipts.

Setup also offers optional broad discipline and career-stage categories. Skip
either, keep them private, or separately choose to include them in reviewed usage
reports. They help describe participating installations; they do not change
which roles you can use. No name, institution or free-text demographic answer is
requested. These fields are absent from individual workflow observations,
feedback, survey responses and activity reports.

## Optional research studies

Ask: “Help me set up optional Benchside research studies.” You can receive
occasional surveys, privately analyse selected research conversations, or review
and share reviewed workflow categories. Each choice starts off. Wider analysis can cover
work without any Benchside role, provided your app can access the sources you
choose. You review a small batch before anything is shared; raw logs stay out of
submissions. No schedule is installed automatically. See [the details](metascience.md).

The five receiving routes are deployed and have passed synthetic storage checks.
The released catalogue has no real active study. Claude's cloud execution needs
network egress enabled to contact the collector; native and connected memory can
work while that access is off. Benchside does not change this account setting.
See the [current acceptance report](acceptance-2026-10-28.md) for live app results.

## Developer packaging

For maintainers, build the distribution from the current source:

```bash
uv sync --frozen
uv run bench compile
uv build --wheel
uv run --with pip python scripts/build_release.py
```

This produces:

- `dist/benchside-claude-0.4.0.zip`: standalone Claude skill, with all roles.
- `dist/benchside-claude-plugin-0.4.0.zip`: Claude plugin upload, with manifest at the archive root.
- `dist/benchside-plugin-0.4.0.zip`: portable/OpenAI plugin with Codex compatibility metadata.

All packages are generated from the same code and role definitions. Claude packaging
adds its manifest and upload layout; it does not fork the implementation or create
a new endpoint. The OpenAI manifest declares the packaged onboarding skill using
[OpenAI's supported setup entry](https://developers.openai.com/plugins/build/plugins).

## One central receiving service

Every production installation—Git, terminal, Claude or OpenAI—uses the same
Science Works HTTPS API at `https://ingest.benchside.science.works`. An HTTPS API
is a secure web address that software sends requests to. Its paths separate the
kinds of approved submission: `/v1/gaps`, `/v1/feedback`, `/v1/usage`, `/v1/surveys`
and `/v1/activity`; `/v1/studies` provides the optional survey catalog.

The Cloudflare Worker is the program running behind that address. Its storage
buckets hold received submissions. The operator updates that central program once;
researchers do not deploy a backend or need a Cloudflare account. The receiving
routes and current submission formats were deployed and verified with synthetic
records by 29 October 2026. Each app still needs network access to send approved data.

Staging means a separate testing copy of the service and storage, so synthetic
submissions cannot mix with real study data. Only development/test runs point at
staging. Normal packages retain the production address. Your chosen private
journal location is independent of this service and is never uploaded wholesale.

To test without cloud access, the agent/developer can run:

```bash
uv run --frozen python scripts/test_endpoints.py
```

This starts an isolated local copy of the receiving program, sends synthetic data
to all five submission routes, checks receipts/duplicate handling and rejected
requests, then removes the test storage. It requires the companion collector
checkout and its installed Node dependencies. No deployment or Cloudflare login
is needed. Testing the real public service needs a reachable endpoint and
explicitly identified synthetic submissions; local success does not establish
that a particular app can reach it.

See [endpoint testing and access](endpoint-testing.md) for the temporary HTTPS
option, exact submission examples, and operator permissions.
