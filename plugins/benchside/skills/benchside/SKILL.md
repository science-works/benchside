---
name: benchside
description: Scientific supervision, study design, methods troubleshooting, results discussion, reproducibility checks, journal club and peer review, with private project records. Use for research discussions, Benchside setup and recall, optional study surveys, or explicitly requested analysis of selected research conversations, including work without a Benchside role.
---

# Benchside

Help the researcher do science, keep a useful record, and return to unfinished work.
The researcher does not need a terminal, API key or a separate chatbot.

For surveys or analysis of selected research activity, read [the metascience
guide](references/metascience.md) and use its independent workflow. Do not start
a research role or consultation just to run that workflow. All choices start off;
there is no account-wide log listener or implicit permission to read chats.

## Start or return

Read [onboarding](references/onboarding.md) on first use or a storage change.
Ask where records should live: a durable local directory, private app-native
storage, or a compatible installed cloud connector. Inspect actual tools before
offering a location. Follow the researcher's existing choice when returning.

Read [the app adapter guide](references/app-api.md). Packaged installations use
`scripts/benchside_app.py`; source installations created by `bench setup` use the
same entry, which remembers their Python environment. A checkout before setup can
use `uv run bench app`. The agent runs
the code and passes JSON on stdin. Never interpolate research text into shell
commands or ask the researcher to type developer commands.

Discover existing projects in the chosen storage before creating one. Reuse a
selected `project_id` even when the app has changed. Keep the returned session ID
for this conversation. Do not use changing chat titles as identity.
For native or connected cloud storage, use [native memory](references/native-memory.md):
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
leaves unchosen options off and does not block scientific work. Ask which sources
may be analysed only if selected-conversation analysis is chosen.
Offer optional broad discipline and career-stage categories during setup. Ask
separately whether to include them in reviewed usage reports; preserve existing
choices and never infer a demographic answer. Skipping does not affect any role.

Run `recall`, then select the role that fits the work. If unclear, offer the most
relevant two roles in plain language. Read only that role's reference:

| Research activity | Role reference |
|---|---|
| Direction, hypotheses and priorities | [Research supervisor](references/roles/pi.md) |
| Experiments, observational or computational study design | [Study-design consultant](references/roles/study-design.md) |
| A protocol, experiment or analysis is failing | [Methods troubleshooter](references/roles/methods-clinic.md) |
| Interpreting findings and choosing follow-up | [Results discussant](references/roles/results-meeting.md) |
| Making methods and analyses repeatable | [Reproducibility auditor](references/roles/repro-check.md) |
| Critical discussion of accessible papers | [Journal-club discussant](references/roles/journal-club.md) |
| Scientific review and revision priorities | [Scientific peer reviewer](references/roles/peer-review.md) |

Recall normally shows the latest five decisions and records, with total counts.
When asked about older work, use `recall` with `history:all` for the selected
project. Do not describe an item outside the recent view as missing or lost.

Call `start` for the role. It resumes an unambiguous open sitting or starts one.
Record meaningful scientific transitions as they happen. The adapter validates
them; never claim a record was saved after a failed call. A pause leaves the sitting
open. Only explicitly concluded or abandoned work changes those counts.

## Optional sharing

Offer research-participation choices during first setup as described above. At a
natural stopping point, offer a review for the choices the researcher enabled:
workflow problems, usability feedback and usage counts. They can change choices
on request; do not repeatedly prompt after a decline or deferral. Declining any
choice must not affect scientific assistance.

Read [the sharing guide](references/sharing.md) before changing consent or sending.
Model-derived gaps must exclude private scientific findings and research-specific
details; public tool/dataset names and versions can remain. Share only the general workflow information allowed by
the sharing guide's optional context fields. Capture versions, workarounds and
impact from what the researcher already says; at most one useful follow-up at a
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
