---
name: bench-init
description: >
  Initialize the current directory as a benchside project: sets up project
  identity, session hooks, and the /pi supervisor skill. Use when the user
  wants to set up benchside, start using /pi here, or asks to "init bench".
allowed-tools: "Bash(bench *)"
---

# /bench-init — set up benchside in this project

You are initializing benchside for the scientist's current project directory.

## Before doing anything

1. Run `bench project` and show them what project id this directory resolves
   to. If it looks wrong (a generic directory name like `work` or `analysis`),
   suggest they name it: the id can be pinned in `.bench/config.yaml`.
2. Tell them, plainly, what `bench init` will write:
   - `.bench/config.yaml` — the project's identity
   - `.claude/settings.json` — two session hooks (SessionStart injects the
     project's memory into new sessions; SessionEnd archives the transcript
     locally). Both are tagged and idempotent.
   - `.claude/skills/pi/SKILL.md` — the /pi supervisor persona
   And the data guarantee: **everything stays on this machine** under
   `~/.benchside/`. Nothing is ever shared without an explicit, revocable
   `bench consent grant`, and `bench export --preview` always shows the exact
   bytes before anything leaves.

## Ask, then act

Ask for their go-ahead. If they agree, run:

```bash
bench init --yes
```

Show them the output. If a `.bench/config.yaml` already exists, init is
idempotent — say so rather than warning about it.

## Afterwards

Tell them /pi is now available in this project (they may need to start a new
Claude session for the skill and hooks to load), and that a sitting begins by
just invoking `/pi`.
