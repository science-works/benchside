<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/logo-dark.svg">
    <img src="docs/assets/logo-light.svg" alt="benchside" width="100">
  </picture>

  <h1>benchside</h1>

  <p><b>An AI workspace for doing science.</b></p>

  <p>
    <img alt="Python 3.13+" src="https://img.shields.io/badge/python-3.13%2B-4dd0e1?style=flat-square">
    <img alt="License" src="https://img.shields.io/badge/license-Apache--2.0-8b949e?style=flat-square">
    <img alt="Status" src="https://img.shields.io/badge/status-prototype-f0a832?style=flat-square">
  </p>
</div>

benchside turns conversations with AI colleagues into a durable scientific
record. You think out loud; the parts worth keeping become structured data
that your next conversation remembers and you can query.

Four pieces make that work:

- **Personas** — Claude Code skills that play a role from real practice.
  `/pi` is a supervisor meeting; an adversarial reviewer and an
  experiment-design partner are planned.
- **Sittings** — one conversation with one persona.
- **The journal** — the typed, append-only record every sitting writes.
  Local, per project.
- **Export** — the only path off your machine. Opt-in, previewable, and off
  by default.

<div align="center">
  <img src="docs/assets/journal-show.svg" alt="bench journal show" width="740">
</div>

## Install

```bash
uv tool install git+https://github.com/science-works/benchside

bench setup    # once per machine: installs the /bench-init skill
```

Then, in a research project directory:

```bash
bench init     # or run /bench-init inside a Claude session
```

`init` asks before writing anything. It sets up the project id, two session
hooks (memory injection, transcript archival), and the `/pi` skill. After
that, open Claude Code and type `/pi`.

## Sittings

A sitting is one conversation with one persona.

- The persona opens it, records into it, and closes it — you talk, it runs
  the `bench` commands.
- A sitting ends **converged** (you agreed a next step) or **abandoned**.
- Each persona declares what a sitting must capture before it can converge.
  `/pi` won't close converged without a recorded hypothesis — enforced by
  the CLI, not by hoping the prompt works.
- Nothing is lost if you `/clear` or close the terminal: the sitting stays
  open in the journal, and your next session is told about it.

## The journal

Each project gets an append-only journal at
`~/.local/share/benchside/projects/<id>/`. Five kinds of things get recorded:

| Entry | What it holds |
|---|---|
| **hypothesis** | a falsifiable statement; may supersede an earlier one |
| **critique** | a challenge, always aimed at something specific — a claim, a method step, or an interpretation — plus how it was resolved |
| **decision** | a durable call and the *reason* for it, so it isn't re-litigated next month |
| **gap** | a place your workflow broke: missing tool, unfindable data, manual toil, dead end, missing index |
| **sitting** | when it opened, which persona, how it ended |

Query it any time:

```bash
bench journal show          # the dashboard: current hypothesis, open critiques, latest decision
bench journal hypotheses    # the supersession chain
bench journal critiques     # what's open, what was resolved and how
bench journal decisions
bench journal events        # the raw stream (--json for machines)
```

Every new Claude session starts with the current state — hypothesis, open
questions, recent decisions — injected automatically. That's the point: the
persona remembers your project, not just your last message.

## Export

Sharing is a separate, deliberate act:

- Off by default. The default export sink refuses to send even if asked.
- Only **gap** entries are exportable. The export schema has no field for
  hypotheses, results, or data.
- `bench share grant` opts in (revocable); `bench share preview` shows the
  exact bytes an export would send; `bench share send` sends them.
- Every export is recorded in a local ledger: what left, when, under which
  grant.

## CLI at a glance

```text
setup, init, project, compile     get set up
sitting open|status|close         manage the current sitting
hypothesis, critique, resolve,
decide, gap                       record what happened (used mid-sitting)
journal <view>                    query the record
share <action>                    consent, preview, export
recall                            what a persona reads on arrival
```

## Development

```bash
uv sync
uv run pytest                    # fast, no API key — run before every commit
uv run ruff check benchside
uv run bench compile --check     # compiled skills must match their sources
```

Personas are YAML records compiled to skills — adding one is adding a file.
The project is strict TDD; design rationale lives in
[ARCHITECTURE.md](ARCHITECTURE.md). `gstack/`, if you see it locally, is an
untracked reference clone of [gstack](https://github.com/garrytan/gstack),
not a dependency.

## License

Apache 2.0
