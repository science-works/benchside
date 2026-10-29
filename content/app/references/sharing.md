# One optional sharing flow

Offer these choices together in plain language during first setup, alongside the
optional studies described in `onboarding.md`. Existing preferences persist. A
broad "yes" to contributing needs a choice of categories before consent is saved.
Declining or deciding later leaves unchosen options off; do not repeatedly prompt
on return. At natural stopping points, offer reviews for enabled choices.

1. Workflow observations: edited descriptions of missing tools, hard-to-find data,
   repeated manual work, dead ends and missing indexes. No project or conversation IDs.
2. Feedback: the researcher's ease-of-use rating (1–5), whether they would use
   Benchside again (`yes`, `no`, `unsure`), and an optional comment. Never infer a
   rating from their conversation. No sitting or gap identifiers.
3. Usage: weekly consultation counts, role/app/version information and standardised
   failure counts. A random persistent installation ID estimates returning use.
   No research text, project titles, conversation IDs or exact activity times.
   Optional, self-reported discipline and career-stage categories are included
   only with the separate profile choice below.

New sharing includes one random contributor ID per private Benchside store,
reused from the usage installation ID. Explain before consent that Science Works
can group this store's contributions across channels and over time, including
previous usage reports with that ID. It is pseudonymous, not anonymous or a
verified person. No account email/name is requested. Existing unlinked grants
need a renewed explicit choice (`sharing.status.needs_policy_renewal`); do not
silently upgrade them. Multiple apps using the same store share the ID; separate
stores have separate IDs. Legacy received observations are not retroactively linked.

Before preparing any model-derived free-text observation or feedback comment, remove scientific
results, hypotheses, measurements, identifying sample/data details, detailed
protocols or analyses, source passages and project-specific names. Describe the
general workflow need instead, or omit the item if generalising it would change
its meaning. Public software/dataset names, versions and general failure details
may remain: “Fiji 2.16 loses channel names on export” is useful workflow information.
Private findings and identifying research details remain excluded. Researcher-written
survey answers follow their accepted study agreement and are preserved as written.
The format permits free text, so automatic identifier scrubbing cannot enforce
this boundary by itself; the assistant must check the content before preview.

Data goes to Science Works' collector. These choices are separate from private
scientific records. An installation is not necessarily a person. Revoking consent
stops future submissions; it does not delete previously received data.

## Calls

Workflow gaps can include an optional `context` object. Supported text fields are
`tool_name`, `tool_version`, `dataset_name`, `dataset_version`, `workflow_area`,
`frequency`, `impact`, `workaround` and `desired_improvement` (each at most 2000
characters). Use only the relevant fields; omit unknown values and the entire
object when there is nothing to add. The existing kind-specific fields remain.
Record the version actually used, never guess it or substitute the newest release.
Use public tool/dataset names only; private dataset identifiers and scientific
details stay private. Context is included in the same reviewed payload and
subject to the same redaction and approval checks.

Capture useful context already given in the conversation. At a natural pause,
ask at most one short follow-up if it would materially clarify the problem, such
as what workaround they use. Do not ask a checklist, repeatedly fill missing
fields, or interrupt the research to complete a report. Missing context is fine.
Context-bearing submissions use `benchside.gaps.v3`; the adapter chooses this
automatically. Older submissions and gaps without context keep their format.

- `sharing.status` returns current choices.
- `sharing.consent` takes `channel` (`gaps`, `feedback`, `usage`) and boolean
  `enabled`. For gaps also supply `kinds`, selected from the five supported kinds.
  Only call after the researcher makes that choice.
- `sharing.feedback` takes `feedback: {role, host, surface, ease, would_use_again, comment}`.
  Unknown role/app/surface values use `unknown`. Returns an independently generated
  feedback ID. This saves locally and sends nothing.
- `sharing.preview` takes `channel`. Gaps optionally take `only: [observation IDs]`
  and `edits: {observation ID: reviewed gap object}`; feedback takes `feedback_id`
  and optionally an edited `comment`; usage optionally takes `week` (Monday date).
- The preview returns one or more drafts, each containing its exact `payload`,
  `destination`, `payload_sha256` and draft `id`. Display the complete content of
  each draft in readable form, including every text field and usage count, plus the
  recipient. Explain that redaction cannot catch all identifying research details.
  If the researcher edits anything, prepare and show a new draft.
- After explicit approval, call `sharing.send` with that `draft_id` and its
  `approved_sha256`. Do not replace the payload, infer approval, or send subsequent
  batches that were not reviewed. A rejected or uncertain submission stays pending.
  Retry the same draft after a network failure; do not regenerate it to retry.
- If `sharing.send` specifically says a proxy blocked the HTTPS tunnel, nothing
  was sent and the draft stays pending. An ordinary HTTP 403 response proves only
  that no valid receipt was received, not that the destination saw no data.
  In Claude chat (web, desktop), a tunnel refusal usually means code
  network access is off. The researcher can open Settings → Capabilities, switch on
  Allow network egress, keep "Package managers only", and add
  `ingest.benchside.science.works` under Additional allowed domains (verified on
  an individual plan). Team/Enterprise owners control this for everyone. In
  Claude Code, approve the domain when asked. Elsewhere it is usually an
  institutional firewall. Never change settings yourself.
- `sharing.history` returns receipts. Give the researcher the channel, digest and
  received date for an operator-assisted removal request. New contributions can additionally
  be located with their random contributor ID. Do not send a removal request yourself
  unless the researcher explicitly asks.

Usage reports are cumulative weekly snapshots. Repeated reporting replaces older
revisions in analysis; it does not add another session. End of a chat is not
abandonment. Offer a refreshed usage preview when the researcher next returns,
without interrupting their work or creating an unsolicited automation.

## Optional demographic categories

`profile.status` returns the private profile and its revision (zero means no
choice has been saved). `profile.set` replaces it:

```json
{"action":"profile.set","demographics":{"discipline":"life_sciences","career_stage":"doctoral_researcher"},"include_in_usage":true}
```

Only save the researcher's actual selections. `demographics:{}` skips both;
either field may be omitted or null. `include_in_usage` defaults to false in a
new store and must be explicitly supplied when changing the profile. It is
independent of usage consent and never sends data by itself. The host uses normal
native save/readback for this state when cloud storage is selected.

Present these values with readable labels, not code identifiers:

- Discipline: life sciences, medical/health sciences, physical sciences,
  mathematics/statistics, computer/information sciences, engineering/technology,
  earth/environmental sciences, social sciences, humanities/arts,
  interdisciplinary, other, prefer not to say.
- Career stage: undergraduate student, master's student, doctoral researcher,
  postdoctoral researcher, research staff, independent researcher or group
  leader, other, prefer not to say.

Wire values use underscores (`medical_health_sciences`, `masters_student`,
`independent_researcher_or_group_leader`, `prefer_not_to_say`, etc.). Do not
request free-text details for “other”, an institution, age, name or email.
Do not infer answers. An omitted answer differs from an explicit “prefer not
to say”. The profile belongs to this chosen store; for a store shared by several
people, skip demographic reporting rather than assign one person's categories
to everyone.

If opted in, the exact usage preview shows the selected categories alongside the
random installation ID. They never enter gap observations, feedback, survey or
activity payloads. Changing or disabling the profile invalidates pending usage
drafts; make a new preview and obtain approval. It does not erase reports already
received. Aggregate reports count the latest accepted profile per participating
store. New pseudonymous contributions can be grouped with it internally; published
reports should contain aggregate counts, not identifiers or raw responses.
