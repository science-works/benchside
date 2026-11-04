# Supported routes and next compatibility checks

Updated 4 November 2026. A plugin appearing in an account is only an installation
result. The full Benchside workflow also needs runtime execution and durable
private storage; optional contributions additionally need outbound HTTPS.

## Recommended routes for the current rollout

| Route | Guidance and evidence |
|---|---|
| ChatGPT web | Use a paid account with the required execution and storage tools. This is the route verified in the maintainer's account, not a guarantee for every paid plan or workspace. |
| Free ChatGPT web | Not currently supported for the complete workflow. The tested account installed an uploaded ZIP, but had no Work option and reported no usable journal storage or outbound request tool. Runtime execution was not demonstrated. |
| Claude web/plugin | Use a paid plugin-capable account. Earlier account-specific memory and approved-send checks passed; a fresh-user install-to-recall-and-send check remains required. |
| Local agent | Use an agent that can read the skill, execute Python and access a durable local directory. The generic installer and JSON bridge exist. Additional provider/model combinations need live acceptance tests before being named as verified. |

These are Benchside's current rollout recommendations, not a universal statement
about account entitlements. OpenAI says available plugin actions depend on plan
and workspace ([guidance](https://developers.openai.com/training/walkthroughs/plugins-and-skills)).
Anthropic currently lists plugins for paid plans
([guidance](https://support.claude.com/en/articles/13837440-use-plugins-in-claude)).
Always inspect the tools in the actual account. Do not require a particular UI
mode if the needed tools already work, or suggest switching to a mode the account
does not offer.

Evidence: [free-account investigation](acceptance-free-account-2026-11-04.md),
[earlier memory tests](acceptance-2026-10-28.md), and
[Claude transfer/send findings](claude-memory-and-sending-findings-2026-10-29.md).

## Three independent checks

1. **Execution:** run the installed entry point with `{"action":"version"}`.
   Reading the manifest does not pass this check.
2. **Private memory:** use the chosen store and Benchside's actual record format
   to save a synthetic decision, read it back, and restore it in a new
   conversation/process. A local folder must be accessible and durable; a
   cloud connector must support exact transfer and guarded updates.
3. **Optional sending:** check the host's HTTP capability when requested or
   when setting up an opted-in network feature. A read-only `GET /v1/studies`
   can establish reachability without submitting a record. It is not proof
   that a contribution was stored. A send test requires a separate synthetic
   preview, explicit approval, the real client send and a matching receipt.
   Never enable survey consent just to obtain a connectivity check.

If execution and memory work but networking does not, private Benchside work
can continue. Keep reviewed submissions pending and explain why they were not
sent. If durable memory is unavailable, do not claim completed journal setup or
substitute an invented Markdown folder. The Science Works collector accepts
optional metascience contributions; it is not a private notebook service.

## Local use with other providers or locally hosted models

The model is supplied by the agent app. Benchside does not call a model provider
API itself. A local model server by itself is not enough: the agent around it
must read instructions, call tools and handle their results reliably.

The baseline requires Python 3.11–3.14 on macOS or Linux, process execution with
JSON input/output, and a chosen private local folder outside Git. Network access
is needed to obtain the release initially and to send optional contributions;
the installed local journal does not depend on the collector. The agent's own
model/provider configuration is separate from Benchside installation.

The agent follows [SETUP.md](../SETUP.md) and, in the release checkout, uses:

```bash
uv sync --frozen
uv run bench setup --agent generic --skills-dir <observed-agent-skill-directory>
```

It then reads the installed `benchside/SKILL.md` and uses
`scripts/benchside_app.py` with one JSON request on stdin per call. The launcher
remembers the source environment so later conversations can run outside the
checkout. The researcher should not need to type these commands. If the host
does not discover skills, use its supported instruction-loading mechanism; do
not invent a skill directory. Hosts with no process tool may need a small tool
adapter to this same interface rather than a fork of the scientific logic.

Generic launcher tests establish process-level behavior, not that every model
will follow the workflow, use tools correctly, or provide good scientific advice.
Local record storage also does not mean a remotely hosted model processes the
conversation locally. Both the model and its execution/storage must be local
for that arrangement; optional approved sharing still uses the collector.

## Next implementation and validation

1. Update the packaged onboarding instructions to perform the three checks and
   report each result before offering unavailable features. Keep the single
   repository-link setup request and the existing runtime, storage and consent
   actions. Avoid adding a new service for this step.
2. Test the Claude release as a new user: installation, one scientific role,
   save, fresh-chat recall and one approved synthetic contribution. Verify its
   network allowance without changing account settings silently. Repeat private
   work with sending unavailable. Prior configured-account tests are useful
   evidence but do not pass fresh installation.
3. Test one independent local agent with a non-OpenAI/non-Anthropic hosted model
   and with one locally hosted model. Use the same script: setup from the repo
   link, choose storage, save and recall a decision across processes/chats,
   check project separation, decline sharing, then separately exercise an
   approved synthetic send and retry. Record the exact host/model versions.
   Include a scientific task check; runtime tests alone do not validate the model.
4. If a tested host needs it, add only a thin process/tool adapter. Keep one
   Benchside implementation and the same reviewed collection formats. A new
   MCP server or hosted private-memory service is not required by the existing
   local route and is outside this compatibility pass.
5. Build a new patch release when packaged instructions/adapters change. Do not
   replace the published 0.3.1 binaries. Install that release in the tested hosts
   and verify the update preserves records before changing the support claims.

Register any live synthetic payloads for exclusion from research reporting.
Do not send test records as part of ordinary researcher installation. Public
plugin-directory publication can simplify acquisition, but cannot grant missing
execution, storage or network capabilities to a host.
