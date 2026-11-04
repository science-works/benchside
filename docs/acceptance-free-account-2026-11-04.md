# Fresh ChatGPT account setup: 4 November 2026

Status: incomplete. This records an onboarding investigation, not a successful
installation or evidence that all free accounts are unsupported.

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

## Documentation changes

The README now contains installation essentials so a failed extra-file fetch
does not block capability checks. Setup instructs agents to discover Plugin
Creator, install the existing package, respect required approval, and use manual
steps only when that is the available route. It distinguishes an attachment from
installation and explicitly says that Benchside needs no MCP server.

## Remaining verification

1. In the new account, ask the chat to find/use Plugin Creator and install the
   released portable ZIP unchanged. Record whether it can do so, requests a
   connection/approval, or exposes only a manual route.
2. If installed, verify runtime version, execution and available private storage.
3. Save/read back a synthetic decision in an isolated project, then restore it
   in a new conversation. Keep sharing off; send no endpoint test submissions.

No free-account installation, runtime execution, save or fresh-chat restore is
claimed by this report. No collector submissions were made during these checks.
