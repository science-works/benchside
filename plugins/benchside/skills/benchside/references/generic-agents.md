# Use the same Benchside runtime with another agent

Benchside does not choose or call an LLM. The surrounding agent supplies the
model, instruction loading, process execution and filesystem/document tools.
The same journal and consent rules apply to hosted and locally hosted models.
A bare chat completion endpoint or model server is not an agent with those tools.

## Agent-led local setup

1. Inspect the host's supported skill/instruction mechanism and process tool.
   Use Python 3.11–3.14 on macOS or Linux. If Python, package installation or
   execution is unavailable, explain that specific blocker instead of inventing
   an HTTP/MCP service. A standard Windows install has not been validated.
2. Follow the repository's `SETUP.md`. Install into a dedicated environment;
   do not replace the host's dependencies. In a source checkout the agent can
   run `uv sync --frozen`, then `uv run bench setup --agent generic --skills-dir
   <observed-skill-directory>`. The launcher remembers that environment, which
   must remain accessible. Do not clone code into the private records directory.
3. Load the installed `benchside/SKILL.md`. Discoverable `.agents/skills` is the
   generic default, but use the host's actual documented location. If the host
   lacks skill discovery, use its supported instruction loader to load this
   file; explain the one-time reference the researcher may need in a new chat.
4. Run the installed `scripts/benchside_app.py` with JSON on stdin and read the
   JSON response. Use the execution tool's stdin or a quoted file-writing API;
   never interpolate researcher text into shell code. This is the same API in
   every host, described in [app-api](app-api.md). No model API key goes into
   Benchside. The agent's provider authentication is configured separately.
   After an error, correct the documented request; do not switch to legacy CLI
   journals or edit JSON/JSONL records directly. For example, the app action is
   `decide`, not `decision`; the full request fields are in the app guide.
5. Follow [onboarding](onboarding.md): chosen private store outside Git, project,
   a labelled synthetic save/readback after the storage choice, independent
   participation choices and fresh-chat restore.
   Use `host:unknown` for other agents and the actual supported `surface` value;
   do not invent a provider value in the reporting schema.

The agent runs installation and repair commands. Ask the researcher only for
missing access, host approval, a storage/project choice or participation choices.
If the host requires manual interaction, name the exact blocker and smallest
necessary action; do not turn setup into a terminal tutorial by default.

## Host qualification: isolated synthetic testing

This section is for maintainers qualifying a host, not ordinary researcher setup.
Use a separate synthetic store and projects, never an existing researcher's
records or participation preferences. Do not change real consent to test a decline.
Any live submission test requires a separately reviewed synthetic payload and
approval; ordinary onboarding must not send test records.

Check one role's scientific reasoning as well as its tool calls. Verify a saved
decision in a fresh session, isolation of a second project, and that declining
sharing leaves all choices off. Failed sends must keep the reviewed draft pending.
Do not claim every model is supported because the Python launcher works: smaller
models may miss instructions, misuse tools or fail to verify a result.

When offering local storage with a remotely hosted model, tell the researcher
briefly that local record storage does not keep the conversation local: the
host still sends prompts to its model provider. Do not imply local-only processing.
For entirely local processing, both the model and execution/storage must be local;
optional approved contributions still go to Science Works.

## Browser-hosted developer environments

Codespaces can supply Python, a filesystem and network access, but a separate
ChatGPT conversation does not automatically control it. A tool-enabled agent
inside that environment would still be needed for agent-led setup. Treat this
as an optional developer route, not a workaround that fixes free web Chat.
Records must remain outside Git and need an agreed backup: deleting the remote
environment can delete its local journal. Do not create one without a request.
