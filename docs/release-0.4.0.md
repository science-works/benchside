# Benchside 0.4.0

## Research supervision and memory

- `/pi` is now a broad research supervisor for exploratory, qualitative,
  descriptive, computational and experimental work. A hypothesis is optional.
  It helps clarify the question, examine evidence and tradeoffs, and agree a next
  step. A converged discussion needs a real decision; unresolved research
  questions can remain open.
- `/pi-hypothesis` preserves the focused hypothesis-challenge workflow. There
  are now eight roles, defined in `content/personas/*.yaml` and compiled into
  both app references and legacy CLI skills.
- Questions and answers have private, durable records of their own. Any role
  can save them and restore them alongside decisions. Decisions preserve the
  researcher's meaning and supplied wording. No question/decision text is
  added to Science Works submissions; optional usage counts record events only.
- Shared instructions suggest a relevant role sparingly within the current
  conversation. They work with any host/model that loads the skill; they do not
  create an account-wide listener or guarantee that an unloaded skill activates.

## Lighter setup

Keep the five independent participation choices together, with nothing selected
by default. Choosing conversation analysis saves that preference; choosing its
sources and whether to share activity labels waits until the first actual
analysis. Source access and sharing still need explicit choices before use.
Explain activity labels with examples such as literature review, data analysis,
tool failures and checking output. Gap finding remains the main focus.

Researchers can select multiple broad disciplines and one career stage, or skip
both. Including demographics in reviewed usage remains a separate choice.
Legacy single-discipline profiles still work. Reports count each selected
discipline once per installation; their totals are not mutually exclusive.

This release also includes the pending agent-led installation and host capability
checks: verify execution, durable private memory and optional sending separately.
Installation alone does not establish any of these capabilities. Free-account
limits and manual-only installation steps are reported honestly.

## Updating and compatibility

Download the matching asset from the GitHub release: `benchside-claude-plugin`
for Claude's plugin uploader, `benchside-claude` for a standalone Claude skill,
or `benchside-plugin` for OpenAI/portable plugin installation. Local agents can
update the source/package and rerun the documented setup using their existing
private store. This is a GitHub release, not a plugin-directory listing or PyPI
publication.

**Update every agent sharing a private store before recording new questions or
multiple disciplines.** Older runtimes cannot read the new question events or
multi-discipline profile. Existing notebooks remain readable by 0.4.0; keep the
host's previous revision/backups during an update.

Existing open sittings retain their original role rules. An older `/pi` sitting
can therefore still require a hypothesis. `start` reports a role update; explicit
`new_sitting:true` starts the broad supervisor while preserving the old sitting.
Do not fabricate a hypothesis or silently rewrite the historical sitting.

The receiver accepts the additional `pi-hypothesis` role and either a legacy
single discipline or an array of distinct disciplines. The reporting importer
must use this compatible Benchside version before these optional reports arrive.
Existing gap formats, destinations, consent and approval rules are unchanged.

## Validation scope

Regression tests cover private question/answer replay, project separation,
closed-sitting rejection, exact decision text, broad versus focused supervision,
legacy sitting preservation, native notebook restoration, disclosure boundaries,
multi-discipline opt-in and aggregate counting. Receiver tests check accepted and
rejected profile values and the additional role. Release smoke tests run every
role through save, fresh-process restore and close in all three archives.

These checks verify code and packaging. They do not establish scientific advice
quality for every model or re-test every account's installed cloud connectors.
The expanded synthetic role prompts in `evals/research-roles.json` are for
subsequent conversational evaluation; they do not change the original paper's
reported results.
