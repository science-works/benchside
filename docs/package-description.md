# Benchside

An AI workspace for doing science, maintained by **Science Works**. Benchside
provides eight research roles, private project records, saved decisions and
unresolved questions, and optional reviewed contributions to metascience research.

## Install for a local agent

Requires **Python 3.11+ on macOS or Linux**. Python 3.11 and 3.14 are tested.
Benchside supplies the skills and runtime; your agent supplies the model and
execution tools. It works with capable agents using OpenAI, Anthropic, other
providers or locally hosted models.

With uv:

```bash
uv tool install benchside
bench setup --agent codex
```

Or install with pip in a Python virtual environment:

```bash
python -m pip install benchside
bench setup --agent codex
```

Use `--agent claude` for Claude Code. For another agent, use
`bench setup --agent generic --skills-dir /path/to/that/agents/skills` after
identifying its actual skill directory. The agent can run these steps for you.
Then ask it to read the installed Benchside skill and complete guided setup:
choose private storage, select a project, and verify saving and restoring a
synthetic record. Installing the Python package alone does not complete that setup.

The package is named **benchside**; its command is **bench**. Upgrade with
`uv tool upgrade benchside` or `python -m pip install --upgrade benchside`, then
rerun the same `bench setup` command to refresh the installed skill. Keep private
records in their existing location. **Update every app sharing a Benchside store
to 0.4.3 or newer together**, including apps using the same local directory. Older cloud
clients refuse the new notebook format; older local clients can omit new record
types from their views. Reopen the existing project and verify recall after updating.

## Research roles and records

- Research supervisor and focused hypothesis reviewer
- Study-design consultant and methods troubleshooter
- Results discussant and reproducibility auditor
- Journal-club discussant and scientific peer reviewer

Benchside can also offer to save a decision, evidence or an open question during
ordinary research chat without starting a role. All roles share the selected
project's records and can explore practical workflow delays involving materials,
equipment, coordination, methods, software or data.

The agent selects a suitable role with the researcher. Decisions and research
records remain in the chosen private store, with ODT/Markdown reading copies
for local storage. Optional sharing is disabled initially; scientific findings
are excluded from metascience submissions. Workflow problems require review and
approval. Survey participation is agreed before answering.

Setup offers **Enable all five**, **Choose specific categories**, **Decide later**,
then **Decline all**, with none recommended or preselected. The all-five shortcut
saves participation preferences together; individual report approval, conversation
source selection and each survey's study agreement remain separate.

## ChatGPT and Claude websites

This Python package does **not** install a web-app plugin or grant storage/network
permissions. For those apps, use the matching archive from
[GitHub Releases](https://github.com/science-works/benchside/releases/latest)
and follow the [setup guide](https://github.com/science-works/benchside/blob/main/SETUP.md).

[Source and full documentation](https://github.com/science-works/benchside) ·
[Report an issue](https://github.com/science-works/benchside/issues) ·
[Contribute a research role](https://github.com/science-works/benchside/blob/main/CONTRIBUTING.md)

Benchside is research software under active development, licensed under Apache 2.0.
