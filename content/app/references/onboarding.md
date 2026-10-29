# Set up Benchside in any capable agent

Use this flow on first use and when the researcher asks to change storage. Do not
infer a storage preference from the model or app name. Setup has two independent
choices: where private research records live, and optional contributions to Science Works.

## Find the available tools

Inspect the current host's actual tools and installed connectors. Check code
execution (Python 3.11+, POSIX), durable local filesystem access, and native or
connected document storage. Do not install a cloud connector or create an account
without the researcher's request. A connector being installed does not prove it
can write or safely update records. Ordinary chat memory is not a journal.

For an installed skill, invoke `scripts/benchside_app.py`. A packaged skill uses
`runtime/manifest.json`; source setup saves `runtime/source.json` with the original
Python environment and source location, so later conversations can run it outside
the checkout without `bench` on PATH. If that saved environment or source was moved
or removed, restore/reinstall it and rerun `bench setup` for the same skill location.
Do this through the agent; the researcher need not run repair commands. All routes accept the same JSON on stdin
and return the same JSON result. Pass input through the execution tool, not shell
interpolation. The researcher should not have to type commands.

If starting from a Git checkout, the agent can install the project using its
available Python package manager (for example `uv sync --frozen`) and invoke
`uv run bench app`. For discovery and runtime access in later conversations,
`uv run bench setup --agent codex` installs the shared skill in `~/.agents/skills`;
`--agent claude` installs
it in `~/.claude/skills` with the legacy `/bench-init` helper. For another host,
use `--agent generic --skills-dir <its observed skill directory>`. If it cannot
automatically discover skills, tell the researcher to reference the installed
`benchside/SKILL.md` in a new conversation. Do not claim automatic discovery until tested.

When changing installation method or replacing a release, use the host's complete
plugin update flow or stage the replacement in a clean directory. Do not unzip a
packaged release over a source-installed skill: its retained `runtime/source.json`
would still select the earlier source environment. Copying over an existing folder
also retains files removed or renamed by the new release. Preserve custom files
separately and replace only the managed installation after checking the new copy;
do not delete unknown files. Keep private record storage in place and reopen the
same project after the update.

## Ask where records should live

Offer only locations the host can actually access, and explain which still need
verification. Ask a short question, for example:

> Where would you like Benchside to keep your research records: this computer,
> your app's private Benchside folder/Space, or a connected storage service?

Respect a location already chosen by the researcher; confirm it by reading it,
not by asking the same question again. Native cloud storage can be used by a
local agent too if its tools support it. An existing preference is a candidate
on a new host, not permission to copy or relocate research records.

- **This computer:** ask for or suggest a durable folder outside Git. Inspect
  `storage.location` first so the current location is visible. Call
  `storage.configure` with the agreed absolute directory. It verifies a local
  write and remembers the folder in the OS account's Benchside configuration.
  `BENCHSIDE_HOME`, if set, takes precedence. Configure does not copy, move or
  delete earlier records. A new location starts a separate notebook unless it
  already contains one. Never silently switch an established project.
- **App-native storage:** use a private Benchside Space/collection and notebook
  through [native memory](native-memory.md). Offer this only with complete reads,
  conditional writes, readback and an exact data-transfer route to/from the
  execution environment. Inline tool text that the model must retype is an
  experimental route, even if a small test passes; explain that limitation
  before selection. ChatGPT Pages and Claude Docs are examples;
  account capabilities decide availability. A Library upload alone is insufficient.
- **Connected storage:** ask which actual service/location. Google Drive and
  Google Cloud Storage are different services. Inspect the installed connector
  and offer a private document/object only if it supports the same native-memory
  protocol. Require a revision/hash/generation precondition on updates, complete
  reads, discoverable stable IDs, readback and exact transfer to/from execution.
  Do not invent a Google API or ask
  for an API key when the installed connector can provide access. If the connector
  is read-only or has only blind overwrites, explain the missing capability and
  offer a working local/native option. No Google connector is bundled here.

For native/connected storage, save the notebook locator and workspace ID in a
private host-discoverable index. Always restore the complete notebook before
continuing. The local path preference does not redirect native requests.

## Choose the project and prove continuity

For local storage, call `projects`. For document storage, call `native.inspect`.
Show existing titles/IDs and let the researcher select one or create a new project.
A project is a separate scientific notebook: existing restores its decisions,
open questions and discussions; new starts an empty, separate record. This does
not change available roles or reporting consent, which belongs to the chosen
Benchside store. If the current project is already clear, reuse it without asking.
Never merge by title. When returning, pass the selected `project_id` to `setup`;
this reuses the same journal regardless of the app. For new local projects pass a
stable `project_key` (an actual project ID or absolute research folder) and a
human-readable `title`. Native setup registers the actual journal document ID.

Legacy CLI journals are separate from app projects. If the researcher is returning
to earlier CLI work, continue that journal explicitly or agree a migration first;
do not create an empty app project and call it restored. Shared setup preserves
existing journals and custom role skills. Recognized generated legacy skills
become explicit-invocation-only, so automatic role selection uses this shared flow.

Keep the returned session ID for this conversation. Record the selected notebook
locator in the host's durable setup context, not just in the execution sandbox.
Run the appropriate save/readback probe and test discovery in a fresh conversation.
A same-process test is useful but does not establish fresh-chat continuity. Report
what was verified and what still needs the researcher to reopen a chat.

Two agents with access to the **same local directory** can select the same project
and continue its records. Local transactions use filesystem locks. Two agents
with access to the **same cloud notebook** can do the same using conditional writes
and conflict retries. Different Claude/OpenAI private accounts are not automatically
connected. A synced local folder on two computers is not safe concurrent storage:
filesystem locks do not coordinate across sync clients; use a conditional-write
cloud connector or one local machine instead.

## Ask about contributing to metascience research

During first setup, explicitly ask about optional participation; do not defer this
question until the end of the first scientific discussion. Read `participation.status`,
`sharing.status` and `metascience.status` first so existing choices are preserved when another app
opens the same store. Returning to a project or changing storage settings is not
an invitation to ask for consent again. Let the researcher reopen these choices
at any time.

Use a short invitation, for example:

> Would you like to contribute to Science Works' research on how AI is used in
> science? You can choose what to contribute, keep everything private, or decide later.

A general expression of interest is not consent to every category. If interested,
show the following choices together, with nothing preselected:

| Choice | What participation means |
|---|---|
| Workflow observations | Review descriptions of missing tools/data, repeated manual work, dead ends and missing indexes before sharing them. |
| Usability feedback | Optionally give a rating and comment after using Benchside; do not ask for an experience rating during setup. |
| Usage counts | Share reviewed counts of consultations, roles, app/version information and failures. A random installation ID helps estimate repeat use; no research text is included. |
| Optional surveys | Receive occasional study invitations, at most one per seven days; each survey explains its purpose, data use and retention before participation. |
| Selected-conversation analysis | Privately analyse up to 20 relevant conversations from the previous complete week, randomly selected or researcher-chosen. Find workflow problems for reviewed gap sharing; activity categories provide optional supporting context. |

Explain that model-derived problem reports exclude private findings, hypotheses,
measurements, sample identifiers, detailed protocols and source passages. Public
software/dataset names and versions can remain when they explain a workflow
problem. Raw transcripts never go to Science Works. Researcher-written survey
answers are sent as written under the agreement for that study; do not copy or
infer extra scientific details into them.

New contributions share a random pseudonymous ID, allowing Science Works to group
problems and optional feedback, usage, surveys and activity over time. Explain
this before saving choices. Older unlinked grants need a renewed choice. The ID
identifies a private store, not an exact person or account. These preferences
apply to that store, including its projects and apps sharing it; they are not
account-wide permission to read conversations.

Follow [sharing](sharing.md) for the first three choices and
[metascience](metascience.md) for invitations, analysis and sharing workflow categories.

Sending needs network access to `ingest.benchside.science.works`. If the
researcher turns on any choice that sends data and your commands run in
Anthropic's cloud (claude.ai or Claude Desktop chat), tell them once how to allow
that domain (steps in [sharing](sharing.md)); until then, reviewed items stay
saved and unsent. This never blocks setup. In Claude Code the commands run on
their own computer, so say nothing. Elsewhere, mention it only if a send is blocked.
Record only explicit choices with the existing consent actions and persist them
before enabling the corresponding work. Do not grant every category from a vague
"yes". Declining or deferring leaves unchosen options off and never blocks setup
or scientific assistance. Do not re-offer declined/deferred choices in every chat.
Persist `participation.set` with `response:declined` or `deferred` after those
answers, or `configured` after saving the individually chosen permissions. This
marker is private setup history, not consent. Legacy notebooks may lack it: do
not interpret a returning project's `unasked` marker as permission to repeat the
pitch. Preserve existing choices and let the researcher reopen them.

If conversation analysis is selected, ask only then which accessible projects or
conversations may be analysed, and whether supporting activity categories
should remain private or be prepared for review. Reviewed problems use gap sharing.
For example: activity = coding, obstacle = tool failure, verification = ran a test.
These categories describe how the tool was used, never the scientific result. Save the selected source scope before reading
additional conversation bodies. Do not infer permission for other chats, background
monitoring or scheduled runs. The existing sampling and invitation limits apply;
ordinary setup requires no notification schedule.

Consent during setup enables the selected workflow, not automatic transmission.
Gap, feedback, usage and activity submissions require exact preview and approval.
For surveys, agree to the study before questions; supplying answers then authorises
submission without a second prompt. Explain that
choices can be changed later; stopping participation blocks future activity/sends
but does not erase data already received. Do not claim an unavailable receiving
route or connector is working. A saved preference can remain pending deployment.

## Keep the remaining setup short

The essential questions are where records live, which existing/new project to use,
and whether to contribute to metascience. Ask one optional scientific-context
question if the conversation has not already answered it:

> What are you working on, and what would you like help with first?

Use that answer to suggest a role; all seven remain available. Do not require a
fixed role, institution, email address or demographic profile. Ask for source
documents or more scientific detail when the actual task needs them.

Offer one optional demographic question, following [sharing](sharing.md):

> Would you like to add your broad research discipline and career stage? You can
> skip either. If you choose to include them in reviewed usage reports, they help
> Science Works understand which groups are trying Benchside.

Let the researcher select broad categories; never infer them from papers, names,
institution or conversation content. Then ask whether to include those choices
in usage reports or keep them private. This does not turn on usage reporting.
Use `profile.status` to preserve existing choices; do not ask again on every visit.
After a skip, save an empty profile with `include_in_usage:false` so the nonzero
profile revision records that setup already offered the question. A changed
profile requires a fresh usage preview. These categories do not gate any role or
change scientific advice; adapt advice to the actual task and stated preferences.

Finish by naming the chosen storage, project, continuity test status, available
roles and saved research-participation choices. Name any unverified capability.
Do not suggest that any private journal must be uploaded to Science Works.
