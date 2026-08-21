<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/logo-dark.svg">
    <img src="docs/assets/logo-light.svg" alt="benchside" width="110">
  </picture>

  <h1>benchside</h1>

  <p><b>An AI workspace for doing science.</b></p>

  <p>
    Claude&nbsp;Code skills that simulate the roles and rituals of real scientific practice —<br>
    a supervisor meeting, an adversarial review, an experiment co-designed with a specialist.<br>
    <i>The scientist stays sovereign: personas recommend, they never decide.</i>
  </p>

  <p>
    <img alt="Python 3.13+" src="https://img.shields.io/badge/python-3.13%2B-4dd0e1?style=flat-square">
    <img alt="License" src="https://img.shields.io/badge/license-Apache--2.0-8b949e?style=flat-square">
    <img alt="Development" src="https://img.shields.io/badge/TDD-strict-0e7c86?style=flat-square">
    <img alt="Status" src="https://img.shields.io/badge/status-prototype-f0a832?style=flat-square">
  </p>

  <p>
    <a href="#quick-start">Quick start</a> ·
    <a href="#the-skills">Skills</a> ·
    <a href="#the-bench-cli">CLI</a> ·
    <a href="#architecture">Architecture</a> ·
    <a href="#your-data">Your data</a> ·
    <a href="#development">Development</a>
  </p>
</div>

---

## Two products, one workspace

**A colleague on demand.** Invoke `/pi` and get a supervisor meeting: what's the actual question,
what would change your mind, what's the cheapest experiment that could kill your hypothesis.
The conversation is prose; the *record* is typed — every hypothesis, critique, decision, and
resolution lands in an append-only journal that the next sitting remembers.

**A map of where science breaks.** While you work, benchside captures the *shape* of workflow
breakdowns — a tool that doesn't exist, data that can't be found, work done by hand for the
tenth time. These gap observations help a science-policy nonprofit see where new tools are
needed. They stay on your machine unless you explicitly, revocably consent to share.

<div align="center">
  <img src="docs/assets/journal-show.svg" alt="bench journal show — the project record rendered in the terminal" width="760">
  <br>
  <sub><code>bench journal show</code> — the record of a project, as the terminal renders it</sub>
</div>

## Quick start

```bash
# 1. install the CLI (uv manages python for you)
uv tool install git+https://github.com/science-works/benchside

# 2. once per machine: install the /bench-init skill
bench setup

# 3. in your research project directory
bench init          # or run /bench-init inside a Claude session

# 4. open Claude Code and start a sitting
❯ /pi
```

`bench init` writes three things, with your consent: `.bench/config.yaml` (project identity),
two session hooks in `.claude/settings.json` (memory injection + transcript archival), and the
`/pi` skill into `.claude/skills/`.

## The skills

| Skill | What it is | Status |
|---|---|---|
| **`/pi`** | A supervisor meeting — direction, priorities, *"what's the actual question?"* | ✅ working |
| **`/reviewer-2`** | An adversarial critic. Finds the flaw you hoped nobody would. | 🔜 planned |
| **`/exp-design <specialty>`** | Co-design an experiment with a collaborator archetype, e.g. `bioinformatician` | 🔜 planned |

Skills are **compiled, not hand-written**: a persona is a data record — its stance, voice,
forcing questions, failure modes, and conversation *flow* — and `bench compile` renders it
into a skill. The persona's eval rubric is **derived from its declared failure modes**, so a
persona can never have a rubric that tests something it wasn't built to do. Adding a
specialist means adding a YAML file.

<details>
<summary><b>What a persona declares</b> — <code>content/personas/pi.yaml</code></summary>
<br>

- **Flow** — ordered phases (*context → actual question → pressure → priorities*), each with
  a goal, guidance, what it must capture, and a prose exit condition
- **Forcing questions** — each with *ask*, *push until you hear*, and *red flags* that mark a dodge
- **Failure modes** — cheerleading, methods-before-question, overriding the scientist,
  tolerating "characterise X"… each doubles as a judge-rubric criterion
- **Close requirements** — a sitting cannot close *converged* without, e.g., a recorded
  hypothesis. Snapshotted into the journal at open, so editing the persona never rewrites
  history.

</details>

## The `bench` CLI

One binary, two audiences. The **capture verbs are the model's surface** — flat, terse,
validated; the model says what happened, the CLI decides what's valid (ids, timestamps,
state transitions, close requirements). The **journal is yours** — structured, glyphed,
readable.

```text
setup, init, project, compile     get set up (machine, then per project)
sitting open|status|close         manage the current sitting
hypothesis, critique, resolve,
decide, gap                       record what happened (used mid-sitting)
journal <view>                    query the record: show · sittings · hypotheses
                                  · critiques · decisions · gaps · events
share <action>                    consent, preview, and export
recall                            what a persona reads on arrival
```

A converged close is **refused** until the sitting's requirements are met — you cannot
cleanly finish a sitting you never recorded. That refusal, not prompt engineering, is what
keeps the journal honest.

## Architecture

Hexagonal, domain-driven, event-sourced — and the domain layer has no I/O and no LLM calls,
so all of it tests in under two seconds without an API key.

```text
cli/  ──────────▶  application/  ──────────▶  domain/  ◀──────  infrastructure/
(entry points)     (composition root)         (pure)            (port impls)
```

| Bounded context | Owns |
|---|---|
| **`consultation`** | `Project` (the durable thread: hypotheses, critiques, decisions) and `Consultation` (one sitting: the state machine `Framing → Probing → Challenged → Converged \| Abandoned`) |
| **`authoring`** | Personas, flows, templates; compilation into skills and derived judge rubrics |
| **`export`** | Consent ledger, redaction, preview — the single path off the machine |
| **`shared`** | Typed ids, the gap taxonomy, the `Journal` port, base classes |

<details>
<summary><b>Key design decisions</b></summary>
<br>

- **The journal is the source of truth.** Every durable fact is an append-only event in a
  per-project JSONL stream. Aggregates are folds; "active" state is always computed, never a
  mutable flag. Corrections supersede; history is never rewritten.
- **Conversations are prose; the record is typed.** The skill calls `bench` at transitions,
  so evals become journal queries instead of paid LLM judgments over transcripts — and the
  insight pipeline is structured *by construction*.
- **Illegal states are unrepresentable.** Consultation state is a sum type. A critique must
  name its target — claim, method step, or interpretation — and method flaws come from a
  closed taxonomy (`missing_control`, `confound`, `under_powered`, `pseudoreplication`,
  `selection_bias`, `unvalidated_instrument`) that the planted-flaw eval fixtures are built from.
- **Hooks are plumbing, never meaning.** SessionStart injects the project's memory into
  Claude's context deterministically; SessionEnd archives the transcript and retires session
  pointers. All semantic capture stays in explicit `bench` calls.
- **Ports are domain-owned; adapters are plumbing.** A JSONL file store is never a domain.
- **DI via [Dishka](https://github.com/reagento/dishka)**, scopes `APP → UOW`: one `bench`
  invocation is one unit of work. Tests substitute fakes by appending providers.

</details>

<details>
<summary><b>Per-domain layout</b></summary>
<br>

```text
<domain>/
  model/      aggregates, entities, value objects — pure, no I/O
  command/    write side: one file per use case (Command DTO + Result + Handler)
  query/      read side: same shape, must not mutate
  event/      journal events
  port/       Protocol interfaces
  service/    business logic
  util/di/    this domain's Dishka provider
```

No `adapter/` inside a domain (implementations live in `infrastructure/`), no `api/`
(domains are protocol-agnostic). The call chain is uniform:
`CLI → Handler → Service → Port`.

</details>

## Your data

Everything lives in <code>~/.local/share/benchside/</code> — journals, transcripts, all of it.

- **Local-first.** Nothing leaves your machine without an explicit, revocable grant
  (`bench share grant`). The default export sink *refuses to send* — the default wiring
  cannot leak.
- **The shared unit is a typed gap**, never research content: what you were trying to do,
  what you reached for, why it failed. Hypotheses, results, and data are structurally absent
  from the export schema.
- **The preview is the payload.** `bench share preview` prints the *exact bytes* an export
  would send. Consent is an event-sourced ledger — grants, revocations, and a content-free
  record (ids + sha256) of everything that ever left.

## Testing

Three tiers, because skill behaviour is only fully verifiable by running a model — which is
slow and paid, so most tests must not do that:

1. **Free static tests** — domain, adapters, CLI, persona validity, compiled-skill freshness.
   Seconds, no API key, every commit. Strict TDD: red tests precede every fix and feature.
2. **LLM-judge evals** — does `/pi` press, or does it cheerlead? Scored against rubrics
   generated from the persona's own failure modes. Cheap, sampled.
3. **End-to-end** — real Claude sessions, reserved for guardrails (nothing shared without
   consent) and golden paths.

> A persona with no eval is unverified, not merely untested.

## Development

```bash
uv sync                          # venv + deps
uv run pytest                    # the free tier — run before every commit
uv run ruff check benchside
uv run bench compile --check     # compiled skills must match their sources
```

`gstack/` (if present, untracked) is a reference clone of
[gstack](https://github.com/garrytan/gstack) — the skill-suite form factor benchside learns
from. Never edited, never committed, not a dependency.

## Status

The `/pi` vertical slice works end to end: persona compilation, sittings with enforced
capture, session hooks with memory injection and transcript archival, journal views, and
consent-gated export (preview-only — the real sink and redaction engine are next, along
with `/reviewer-2` and the eval tiers 2–3).

---

<div align="center">
  <sub>
    Apache 2.0 · built with <a href="https://claude.com/claude-code">Claude Code</a> ·
    a <a href="https://github.com/science-works">science-works</a> project
  </sub>
</div>
