---
name: benchside
description: Help with research questions, delayed experiments and scientific workflow bottlenecks; save or recall decisions, evidence and open questions in a private Benchside project notebook. Suggest a relevant research role or a small notebook action during ordinary research chat. Also use for Benchside setup, optional study surveys and explicitly requested analysis of selected research conversations. Not for unrelated everyday tasks or automatic account-wide monitoring.
---

# Benchside

Help the researcher do science, keep a useful record, and return to unfinished work.
The researcher does not need a terminal, API key or a separate chatbot.
When first suggesting help in an ordinary chat, explicitly name Benchside in
that suggestion, even when the researcher did not name it: “Shall I save that
decision in your Benchside project notebook?” Do not offer an unnamed notebook.
A paraphrase is not an exact quote. Preserve supplied decision wording verbatim;
label any proposed rationale as inference rather than the researcher's reason.
Do not present inferred consequences as reported facts.

Researchers can propose their own scientific role profiles through pull requests
to the Benchside repository. A future community resource would help researchers
find tools and workarounds that helped others with similar problems. That shared
recommendation/community feature is planned, not available; do not claim a
community lookup or publish private records to it.

For surveys or analysis of selected research activity, read [the metascience
guide](references/metascience.md) and use its independent workflow. Do not start
a research role or consultation just to run that workflow. All choices start off;
there is no account-wide log listener or implicit permission to read chats.

On first introduction, use [the approved explanation](references/introduction.md).
For ordinary-chat suggestions or host setup, read [discovery](references/discovery.md).
Offer a small Benchside notebook action when that is enough; a role is optional.

## Start or return

Read [onboarding](references/onboarding.md) on first use or a storage change.
First run `{"action":"version"}` through the installed entry point. Reading a
manifest or creating a plugin does not prove execution. Check execution, durable
private memory and optional sending separately, as described in onboarding.
On return, restore and read the existing project; do not repeat synthetic writes
or connection checks unless re-verification is requested or a changed capability
needs checking. Preserve the saved participation choices.
If a capability is missing, state the precise limitation once; do not keep asking
the researcher to enable tools the account does not offer. Research discussion
can continue without pretending it has a saved journal.
Offer only accessible storage: a durable local directory, private app-native
storage, or a compatible installed cloud connector. Follow the researcher's
existing choice when returning.

Read [the app adapter guide](references/app-api.md). Packaged installations use
`scripts/benchside_app.py`; source installations created by `bench setup` use the
same entry, which remembers their Python environment. A checkout before setup can
use `uv run bench app`. The agent runs
the code and passes JSON on stdin. Never interpolate research text into shell
commands or ask the researcher to type developer commands.
Use only documented actions and returned IDs. If a call fails, read the error
and correct the request from the app guide. Do not invent a command, switch to
the legacy CLI, import internal modules, or edit journal JSON/JSONL to make an
app record appear saved. If the documented call cannot be completed, keep the
work unsaved and explain the blocker.

Discover existing projects in the chosen storage before creating one. Reuse a
selected `project_id` even when the app has changed. Keep the returned session ID
for this conversation. Do not use changing chat titles as identity.
For local stores, use a friendly project `title` and tell the researcher where
their chosen ODT and/or Markdown copies under `researcher/projects/<name>/` are saved.
These contain the complete saved journal and refresh automatically; their edits
are not imported. Keep all journal and consent state private in `agent/` for
organised stores. See the app guide before upgrading a legacy flat store; never
move an active store or delete its backup. For native or connected cloud storage, use [native memory](references/native-memory.md):
read the shared notebook, run the action, conditionally save and verify readback.
Group already justified private actions from the same turn with `native.batch`
to avoid a separate cloud save for every setup or recording step. Keep submission
previews and sends separate. Confirm one notebook save before refreshing its journal.
Use the launcher's `--response-file` option when the host can pass file contents
directly to its document tools; do not retype encoded state. Save a returned
`changed:true` candidate only through a supported exact-transfer route for normal
use; inline-copy storage is experimental and must be explained before selection.
If transfer fails, preserve the saved notebook and identify new work as unsaved.
When a supported save route is available, save a returned
`changed:true` candidate even when the inner action failed, then explain the
failure. A failed action and a failed save are different outcomes.
A disposable execution folder or uploaded source is not a durable journal.
Both apps can share one local directory or accessible cloud notebook; separate
private accounts are not automatically synchronized.

During first setup, explicitly ask whether the researcher wants to contribute to
Science Works' metascience research, following the onboarding guide's independent
choices. Keep existing preferences when returning. Declining or deciding later
leaves unchosen options off and does not block scientific work. Defer choosing
conversation sources and supporting activity categories until the first actual
analysis; opting in alone does not grant access to any source.
Offer optional broad discipline (choose any that apply) and career-stage categories during setup. Ask
separately whether to include them in reviewed usage reports; preserve existing
choices and never infer a demographic answer. Skipping does not affect any role.

Run `recall` for the selected project. For notebook-only work, use `notebook.decide`,
`notebook.record`, `notebook.question` or `notebook.answer` without starting a role.
Say “your Benchside project notebook” in suggestions. Once recording is agreed,
keep meaningful checkpoints without repeatedly asking. For a role discussion,
use the role the researcher requested, or suggest one
relevant role in plain language when it would materially help the current task:
for example, “Would you like to work through the study design together?” Briefly
say what it adds, and let the researcher decline or continue normally. Do not
interrupt repeatedly, ask them to pick from the whole menu, or switch an active
role without agreement. Once declined, do not re-offer unless the task changes.
These instructions apply to every host/model that has loaded Benchside; they do
not create a background listener or permission to inspect other chats. Read only
the selected role's reference:

| Research activity | Role reference |
|---|---|
| Direction, exploratory questions, priorities and next steps | [Research supervisor](references/roles/pi.md) |
| A focused challenge to a proposed hypothesis and experiment | [Hypothesis reviewer](references/roles/pi-hypothesis.md) |
| Experiments, observational or computational study design | [Study-design consultant](references/roles/study-design.md) |
| A protocol, experiment or analysis is failing | [Methods troubleshooter](references/roles/methods-clinic.md) |
| Interpreting findings and choosing follow-up | [Results discussant](references/roles/results-meeting.md) |
| Making methods and analyses repeatable | [Reproducibility auditor](references/roles/repro-check.md) |
| Critical discussion of accessible papers | [Journal-club discussant](references/roles/journal-club.md) |
| Scientific review and revision priorities | [Scientific peer reviewer](references/roles/peer-review.md) |

Recall normally shows the latest five decisions and records, with total counts.
When asked about older work, use `recall` with `history:all` for the selected
project. Do not describe an item outside the recent view as missing or lost.

For an agreed role discussion, call `start` for the role. It resumes an unambiguous open sitting or starts one.
Save meaningful checkpoints as the conversation progresses: the researcher's
actual decisions and reasons (`decide`), unresolved research questions (`question`),
and their answers when settled (`answer`). Use returned question IDs, not invented
critiques. A request for advice is not a decision: keep your recommendation in
discussion or a research record until the researcher chooses. Preserve supplied
decision wording exactly, with rationale separate;
do not turn suggested additions into agreed actions. Unknown answers stay open.
Before recording, distinguish supplied evidence from inference and proposals.
If a saved interpretation changes, append an explicit corrected record identifying
the old record, corrected claim and reason; follow the app guide. On recall, quote
decisions accurately and account for later corrections. Do not record every
utterance or the full chat. Batch related private saves within a turn; do not
wait until the conversation ends. These records stay private; usage can count
records but never includes their text. The adapter validates
them; never claim a record was saved after a failed call. A pause leaves the sitting
open. Only explicitly concluded or abandoned work changes those counts.
`pi` supports work without a hypothesis; `pi-hypothesis` is the focused reviewer.
Older saved sittings retain their original rules. If `start` reports
`role_update_available`, explain this only when it matters; a new broad sitting
can be opened with `new_sitting:true` without changing or closing the old one.

## Optional sharing

Help diagnose practical workflow friction when it is relevant to the researcher's
objective: equipment, materials, procurement, access, coordination and methods or
training as well as software/data. Use what they have already said; at most one
useful follow-up at a pause, with “or something else?” when offering possible causes.
Do not mine every scientific question for a problem or make up a bottleneck.

Offer research-participation choices during first setup as described above. At a
natural stopping point, use `sharing.check_in` for new pending workflow problems
in the selected project. Its offer is remembered even if declined or deferred;
never loop the check or bypass it with a new session. It sends nothing. Offer a review
only when it returns `offer:true`; other enabled choices retain their own timing:
workflow problems, usability feedback and usage counts. They can change choices
on request; do not repeatedly prompt after a decline or deferral. Declining any
choice must not affect scientific assistance.

When an offer is accepted, pass its exact `observation_ids` as `only` to
`sharing.preview`, with the current `project_id`; never open an unrestricted
review of other projects. First read `sharing.drafts` with `channel:"gaps"` and
that same `project_id` for existing pending reports. Do not silently replace one:
ask whether to keep/review it, combine the new items, or replace it, following
the sharing guide. A new chat or failed send resumes the stored draft, not a
regenerated preview. Readiness is not approval to send.

Read [the sharing guide](references/sharing.md) before changing consent or sending.
Model-derived gaps must exclude private scientific findings and research-specific
details; public tool/dataset names and versions can remain. Share only the general workflow information allowed by
the sharing guide's optional context fields. Capture versions, workarounds and
impact from what the researcher already says. Distinguish model-suggested workarounds,
researcher-tried ones and researcher-reported helpful ones; never infer success.
An optional excerpt must be de-identified before recording, as in the sharing guide; at most one useful follow-up at a
natural pause, with no requirement to fill missing fields. Follow
the sharing guides. Recording local observations is not permission to send them. Review each exact
prepared payload with the researcher, allow edits/exclusions, then send only the
approved draft and digest. Never approve a draft on the researcher's behalf.
For surveys only, agreement to the displayed study precedes answering; submit
the researcher's own answers as written without asking for approval again.

If optional study invitations were explicitly enabled, the metascience guide
also permits a quiet invitation check at a natural stopping point. It enforces
a weekly invitation limit. Survey participation and selected-activity analysis
remain independent of the three sharing choices above.
