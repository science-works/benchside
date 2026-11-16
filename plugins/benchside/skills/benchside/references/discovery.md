# Suggest Benchside in ordinary research conversations

An installed skill can be suggested before a research role is active. The host
must expose its name/description and allow the model to load it. Do not infer
availability from the model provider or from a successful package installation.
Benchside supplies instructions and a runtime; the host supplies model/tool access.

- OpenCode: use its discovered skill directory and permissions; the same approach
  works with OpenRouter, another API provider or a locally hosted model.
  [OpenCode skill discovery](https://opencode.ai/docs/skills/).
- ChatGPT/Codex: enable the installed skill and its normal implicit invocation.
  [Skill selection](https://learn.chatgpt.com/docs/build-skills).
- Claude Code: install in the intended project or personal scope and allow
  model invocation. [Skills](https://code.claude.com/docs/en/skills).
- Other hosts: inspect their documented skill mechanism. If absent, use a
  supported persistent instruction to describe when Benchside helps and point
  to its installed SKILL.md. A bare model API has neither discovery nor file tools.
  Follow [generic setup](generic-agents.md); never silently replace host instructions.

Use host documentation for version-specific paths and settings. Project-scoped
installation may not be visible in unrelated chats. Do not promise reliable
implicit discovery across every model/account; verify it in a fresh conversation.

## Lightweight help, shared memory

When relevant to the current research conversation, offer the smallest useful
Benchside action: a role discussion, a saved decision, evidence with its source,
an unresolved question, or a reviewed workflow report. Name Benchside explicitly:
“Shall I save that decision and your reasoning in your Benchside project notebook?”
Offer once, explain what it adds, and continue normally if declined. Do not load
unrelated project records or start a role merely because the subject is scientific.
Once recording is agreed for the selected project, save meaningful checkpoints
without repeatedly asking. Use notebook.* actions when no role is active; use
that role's actions when it is. Do not fabricate consultations for note-taking.

Use the same selected project memory across roles: recall relevant decisions,
evidence, questions and practical blockers, then suggest a specialist only when
it would help. Explain a change and let the researcher agree; no separate
always-running supervisor/model is required. Never infer a decision from advice.
Private evidence needs an inspected source or explicit researcher report.

At a natural pause, follow sharing.check_in and the sharing guide for opted-in,
unsubmitted problems. Say “You mentioned…” only for an actual researcher report;
label a model inference as such. Opt-in is not approval to send a report.

## Discovery checks

In a fresh chat with the skill installed but not named, try a research bottleneck,
a clear decision worth saving, and a discussion needing evidence recall. Verify
that the agent offers Benchside without forcing a role. Decline and confirm it
continues without repeated offers. An unrelated email edit should not trigger it.
Then verify the saved record in a new chat. Check each host/model actually used.

This is current-conversation assistance, not background surveillance. The separate
[metascience workflow](metascience.md) can inspect authorised selected older chats
through host tools. It does not install a listener or a scheduled account scan.
