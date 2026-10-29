---
name: bench-init
description: Set up Benchside in Claude Code, choose where research records live, and make all seven scientific roles available. Use when the researcher asks to initialize Benchside in a local project.
---

# Set up Benchside

Read the installed sibling `../benchside/SKILL.md` and follow its onboarding
reference. Ask where the researcher wants records stored: a durable local folder,
private native documents, or a compatible installed cloud connector. Do not choose
local storage merely because this is Claude Code. The agent runs setup commands;
the researcher need not use a terminal or provide a model API key.

The shared Benchside skill contains all seven roles and uses its installed
`scripts/benchside_app.py` entry, which remembers a source installation's runtime.
Prefer this route for projects also used from another agent.
List existing projects in the chosen store and reuse the selected project ID.

`bench init --yes` installs the same shared entry locally without legacy role skills
or transcript hooks. Restore an existing app project before creating a new one.
If the researcher specifically wants the legacy per-project slash commands and
Claude Code lifecycle hooks, explain that `bench init --yes --legacy-cli` writes project identity
in `.bench/config.yaml`, role skills in `.claude/skills`, and tagged session hooks in
`.claude/settings.json`. SessionStart restores legacy CLI recall; SessionEnd archives
the transcript locally. Follow their request before enabling these hooks. This is
optional; the shared skill records without hooks and works with native memory too.
Legacy role skills require explicit invocation so automatic discovery does not
switch between two journal systems. Shared setup marks only recognized, unedited
Benchside-generated legacy skills this way and preserves custom skills.
Legacy CLI journals and app project IDs are separate; do not imply automatic migration.
For existing legacy research, let the researcher choose to continue its CLI journal
or explicitly migrate it. Do not create an empty app project and claim it restored
their previous work.

Optional reporting always requires separate consent, exact preview and approval.
The shared onboarding flow also offers optional discipline/career-stage categories
and a separate choice to include them in reviewed usage reports.
