# Fresh ChatGPT account setup: 4 November 2026

Status: partial. The researcher-provided chat reports successful installation
from an uploaded v0.3.1 ZIP. Automatic package retrieval, runtime execution and
durable memory have not passed. This is not evidence that all free accounts
have the same capabilities.

## Evidence

- The researcher tested a new free ChatGPT account with the public repository
  URL, then the `SETUP.md` URL. The chat found the repository but reported a
  cache miss for the setup file and no available Benchside installer. It asked
  for repeated document uploads and incorrectly suggested configuring an MCP
  server. These are user-reported chat results.
- The researcher reported that Plugin Creator was absent from `@` search and
  supplied a screenshot of the menu. They subsequently found an Add/Create
  option in Plugins that allows plugin creation. This corrects any inference
  that creation itself is unavailable; it does not establish that the chat can
  invoke that capability to install the existing release package.
- Independent unauthenticated HTTP checks returned 200 for the public raw
  `SETUP.md` file and the v0.3.1 portable plugin ZIP. A separate web-reader check
  could read the normal GitHub file page but returned cache misses for raw-file
  and release-page URLs. File availability and web-reader retrieval are separate.
- Plugin directory discovery in the maintainer's connected account returned
  Plugin Creator as installed and available. That result does not describe the
  new free account.
- [OpenAI's creation guide](https://learn.chatgpt.com/docs/build-plugins) requires
  plugin permission and Plugin Creator availability. It does not establish
  access for this particular account or prove that a paid upgrade is needed.

## Follow-up: installation and a new chat

The researcher supplied the installation response and the transcript of a new
chat opened through the created plugin. These are reported results; this review
did not independently operate or inspect the free account's tools.

| Check | Result from the supplied chats |
|---|---|
| Discover installation tool | The setup chat found a plugin creation tool without a Plugin Creator hint in the user's updated setup request. |
| Retrieve instructions/package | Blocked: web-reader cache misses continued; the agent reported no available package download tool. |
| Install uploaded package | Reported success: private personal Benchside 0.3.1 created from the researcher-uploaded release ZIP. |
| Inspect installed files | The agent reported finding the skill, references, runtime and dependencies, and a matching runtime wheel hash. |
| Load in a new chat | The new chat used Benchside's setup topics and roles, but did not show a runtime invocation. |
| Execute Benchside runtime | Unverified: no result from the installed entry point's version action was supplied. ZIP inspection alone does not establish execution. |
| Native/connected storage | Blocked in the supplied chat: it reported no suitable native document tools and unavailable Google Drive access. This has not been independently established as a plan restriction. |
| Local storage | No access demonstrated. The researcher was using the website without a connected desktop app; supplying a Mac path did not provide access. |
| Save/readback/fresh-chat recall | Not completed. The second chat was an onboarding attempt, not a saved-record restore. |

The earlier successful ChatGPT web memory tests used the maintainer's configured
paid account. They are separate from this new free-account installation test.
The second chat eventually proposed a generic folder of Markdown files for
manual upload/download. That is not the Benchside runtime's journal format and
must not be counted as successful Benchside setup.

Additional onboarding issues: storage choices were offered before an accessible
route was established; usage was called anonymous despite the documented
pseudonymous contribution ID; and the privacy wording could imply scientific
details become eligible for gap sharing after approval. The packaged guides
already require checking storage access, explaining the random ID and excluding
private scientific details from model-derived submissions. No actual consent
write or submission was evidenced. A pop-up question is a host UI capability,
not evidence that those consent rules were enforced or skipped.

## Documentation changes

The README now contains installation essentials so a failed extra-file fetch
does not block capability checks. Setup instructs agents to discover Plugin
Creator, install the existing package, respect required approval, and use manual
steps only when that is the available route. It distinguishes an attachment from
installation and explicitly says that Benchside needs no MCP server.
The suggested user prompt contains only the setup request and repository URL.
Discovering Plugin Creator and selecting the package belong to the agent's
instructions, not prerequisite knowledge for the researcher.
The setup guide now also requires a real version invocation and explicitly
distinguishes unsupported journal storage from a manual notes workaround.
These source-document changes do not update the already installed 0.3.1 package.

## Remaining verification

1. In a fresh chat in the new account, use only the documented setup request and
   repository URL after these instructions reach `main`. Do not preselect or
   mention Plugin Creator. Record whether the agent discovers it, installs the
   released portable ZIP unchanged, requests a connection/approval, or exposes
   only a manual route. A successful test using an explicit Plugin Creator hint
   is useful diagnostic evidence, but does not pass this first-use check.
2. In the already installed free-account plugin, invoke
   `scripts/benchside_app.py` with `{"action":"version"}` and record the actual
   result or missing execution capability. Then check available storage tools.
   Record the app mode, not only the plan, before attributing missing tools to
   subscription level. Do not ask the researcher to reinstall just to repeat
   package inspection.
3. Save/read back a synthetic decision in an isolated project, then restore it
   in a new conversation. Keep sharing off; send no endpoint test submissions.

Installation is reported by the supplied chat; runtime execution, a saved record
and fresh-chat restore remain unverified. No collector submissions were made by
this review, and none were reported in the supplied chats.
