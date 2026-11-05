# Free Claude account: partial setup, 5 November 2026

Status: partial, based on a transcript supplied by the researcher. This review
did not independently operate the free account or inspect its tool arguments,
runtime results or cloud documents. The transcript reports more capabilities
than the free ChatGPT account tested on 4 November; the two results must not be
conflated.

## Observed sequence

- The researcher asked the chat to set up Benchside using the public repository
  URL. The chat found setup guidance but said it could not download or install
  the release itself.
- The researcher attached `benchside-plugin-0.3.1.zip`. The chat inspected it,
  reported both Claude and Codex manifests, and requested the Claude-specific
  filename instead. The next user message said the ZIP was uploaded to Plugins;
  the transcript does not establish whether they changed archives first.
- After the upload, the chat reported Benchside in its skills list and read its
  instructions. The transcript shows command execution and Claude Docs tools.
- The researcher chose Claude Docs. The chat reported creating a 252-character
  empty notebook, then running the runtime checksum check. The displayed document
  card was marked "Only you". Exact outputs and the full save protocol were not
  included, so this is provisional evidence, not an independently verified pass.
- The researcher chose to select participation options. The transcript presents
  the three sharing categories and two additional metascience options; the chat
  interpreted the answers as enabling all five and began a private batch save.
  The compressed transcript does not establish a consent defect or prove that
  all choices were committed. Confirm persisted choices against the user's
  actual selections when resuming.
- The UI then paused for the free account's usage allowance. A usage-limit pause
  is not evidence of unsupported storage or a failed collector request.

## Package clarification

`scripts/build_release.py` builds both plugin ZIPs from the same plugin tree,
including both manifests. The portable ZIP uses a top-level `benchside/` wrapper;
the Claude plugin ZIP places that tree's contents at the archive root. The skill
ZIP contains the shared skill and runtime without the plugin wrapper.

Prefer the documented installer format when starting. Once a host has accepted
an archive, inspect the installed skill and invoke the actual launcher rather
than refusing to proceed based only on the filename. No different research
behaviour or provider-specific model is selected by these archive layouts.

## Remaining checks

1. Resume the existing installation and read the existing notebook. Do not
   restart installation or replace preferences merely because usage was paused.
2. Record the actual launcher `version` response, not just the archive name.
3. Verify which participation choices were saved; finish source-scope selection
   only if selected-conversation analysis was actually chosen. Submit nothing
   as part of setup.
4. In an isolated synthetic project, save a decision and verify an exact
   guarded notebook update/readback. The tiny initial notebook does not establish
   reliable transfer for larger records.
5. In a new normal chat, discover that project and restore its decision from
   the stored notebook. Same-chat readback alone is not this check.
6. Test one scientific role. Assess scientific reasoning separately from whether
   the runtime records its output correctly.
7. If separately requested, test collector reachability and then an explicitly
   approved synthetic submission with a matching receipt. No send is evidenced
   in the supplied transcript. The released 0.3.1 runtime does not include the
   candidate 0.3.2 `connection.check` action.

No conclusion is drawn about every free Claude account or about a standalone
skill bypassing a plan restriction. The observed account's capabilities govern
the next step.
