# benchside

An AI workspace for doing science, delivered as a suite of Claude Code skills.

Each skill simulates a role or ritual from real scientific practice — a supervisor
meeting, an adversarial review, designing an experiment with a specialist. The
scientist stays in charge throughout; the personas recommend, they never decide.

There is a second product underneath the first. While a scientist works, benchside
builds a structured record of where the scientific workflow broke down: missing
tooling, dead ends, manual toil, data that couldn't be found. Those observations
show a science-policy nonprofit where new tools are needed. **Sharing them is
opt-in, revocable, and nothing leaves the machine without an explicit grant.**

> **Status: greenfield.** The domain model and its wiring are built and tested;
> no skill runs yet. See [Current state](#current-state).

---

## The skills

| Skill | What it is |
|---|---|
| `/pi` | A supervisor meeting. Direction, priorities, "what's the actual question?" |
| `/reviewer-2` | An adversarial critic. Finds the flaw you hoped nobody would. |
| `/exp-design <specialty>` | Co-designing an experiment with a named collaborator archetype, e.g. `bioinformatician`. |

Skills are **generated artifacts, not hand-written files**. Each is compiled from a
persona record plus shared prose blocks, so adding a new specialist means adding a
data file rather than writing a new skill by hand.

## The `bench` CLI

One binary, two faces. Skills shell out to it mid-conversation; you and CI use it
at build time.

```
# runtime — called from skill bash blocks
bench consultation open|critique|resolve|close    record what happened in a sitting
bench recall <project>                            what the persona reads on arrival
bench gap capture                                 record a workflow breakdown
bench consent grant|revoke|status                 govern sharing
bench export --preview                            render the exact bytes an export would send

# dev — called by contributors and CI
bench compile                                     personas + templates -> skills/ and judge rubrics
bench check                                       freshness and validation dashboard
```

---

## Architecture

### The four components

1. **The Python package** (`benchside/`) — layered internally: domain, application,
   infrastructure, CLI. One deployable unit with a strict import direction.
2. **The `bench` CLI** (`benchside/cli/`) — the only entry point, and the only
   writer to on-disk state. That is what makes the consent chokepoint enforceable
   in one place.
3. **Content** (`content/`) — persona records, templates, eval fixtures. Data with
   no logic; the package validates it.
4. **Generated skills** (`skills/`) — the compiled output Claude Code loads.
   Regenerable at any time, freshness-gated in CI, never edited by hand.

Runtime state lives on the scientist's machine under `~/.local/share/benchside/`, owned by the
storage adapter and never in this repo.

### Layers

Dependencies point inward. Nothing in `domain/` imports from `infrastructure/`,
`application/`, or `cli/`.

```
cli/  ──────────▶  application/  ──────────▶  domain/  ◀──────  infrastructure/
(entry points)     (composition root)         (pure)            (port impls)
```

The domain layer has no I/O and no LLM calls, so it is fully testable without an
API key. The skill surface is an adapter, which means the same `/pi` logic is
reachable from a skill, a CLI, or a test harness.

### The domains

Four bounded contexts under `benchside/domain/`:

**`consultation`** — everything that happens when a scientist meets a persona. Two
aggregates, split by lifetime:

- `Project` — the **durable** thread. Owns hypotheses and their supersession chain,
  critiques and their resolutions, and decisions with rationale. This is what a
  scientist means by "my work on X."
- `Consultation` — one **episode**. Owns only the state machine
  (`Framing → Probing → Challenged → Converged | Abandoned`) and references its
  project by id.

The service keeps them in step: raising a critique mutates the project, then
reconciles the sitting's state against the project's open-critique set. A sitting
cannot converge while a critique is open.

**`authoring`** — personas, templates, and compilation into skills and judge
rubrics. Build-time only. A persona's rubric is *derived* from its declared failure
modes rather than written separately, so a persona cannot have a rubric that tests
something it was not built to do.

**`export`** — consent, redaction, preview, and the single path off the machine.
Separate from `consultation` on purpose: the authority governing what leaves must
not live inside the code that wants to send it.

**`shared`** — the kernel: typed ids, the `Gap` taxonomy, the `Journal` port, and
the base classes (`Aggregate`, `Service`, `Command`/`Query`/`Result`, `Event`).

### Per-domain layout

Every domain has the same shape:

```
<domain>/
  model/      aggregates, entities, value objects — pure, no I/O
  command/    write side: one file per use case (Command DTO + Result + Handler)
  query/      read side: same shape, must not mutate
  event/      journal events
  port/       Protocol interfaces (repositories, external services)
  service/    business logic, injected into handlers
  util/di/    this domain's Dishka provider
```

There is deliberately **no `adapter/`** inside a domain — implementations live in
`benchside/infrastructure/`. And no `api/`: domains are protocol-agnostic.

The call chain is uniform:

```
CLI → CommandHandler → Service → Port
                               → Journal
```

Handlers are thin (unpack, one service call, build a result) and never touch a port
directly.

---

## Key design decisions

**The journal is the source of truth.** Every durable fact is an append-only event
in a per-project stream. Aggregates are folds over that stream; "active" state is
always computed, never stored as a mutable flag. Corrections are new events that
supersede old ones — history is never rewritten.

**Conversations are prose; the record is typed.** The persona talks to the
scientist in natural language, but at each transition the skill calls `bench` to
emit a typed event. That makes evals cheap (query the journal instead of paying an
LLM judge to read a transcript) and makes the insight pipeline structured *by
construction* rather than by later summarisation.

**Illegal states are unrepresentable.** Consultation state is a sum type, not four
booleans. A critique must name its target — a claim, a method step, or an
interpretation — and there is no generic "concern" variant. Method flaws come from
a closed taxonomy (`missing_control`, `confound`, `under_powered`,
`pseudoreplication`, `selection_bias`, `unvalidated_instrument`), which is also
what the planted-flaw eval fixtures are built from.

**Ports are domain-owned; adapters are plumbing.** A JSONL file store is never a
domain. The `Journal` interface lives in the shared kernel because both
`consultation` and `export` need it; the thing that opens a file and appends a line
lives in `infrastructure/`.

**Dependency injection via [Dishka](https://github.com/reagento/dishka).** Scopes
are `APP → UOW` — benchside is a CLI, so one `bench` invocation is one unit of
work. Domain providers bind services and handlers; infrastructure providers bind
ports to implementations via `provides=`. `create_container(*extra_providers)`
lets tests substitute fakes, since later providers override earlier ones. The
graph is validated eagerly, so a missing binding fails at startup rather than at
first use.

## The insight pipeline

Treated as a subsystem with its own boundary, not as logging bolted onto the skills.

- **Local-first.** Observations are written to the scientist's machine. Nothing
  leaves without an explicit, revocable opt-in.
- **The shared unit is a typed gap**, captured when it happens: what the scientist
  was trying to do, what they reached for, why it failed. Never raw research
  content, hypotheses, or data.
- **Consent is an event ledger**, not a config flag. Grants and revocations are
  events; the active grant is computed by folding them. Revocation is meaningful
  because the ledger records exactly what left and when.
- **The preview is the payload.** `bench export --preview` renders the literal
  bytes that would be sent, for the scientist to read before deciding. Redaction
  scans those same bytes — never a string that is then re-rendered.
- The default export sink **refuses to send**. The default wiring cannot leak.

---

## Repository layout

```
benchside/            the package
├── domain/           consultation, authoring, export, shared
├── application/      di.py — the composition root
├── infrastructure/   port implementations (currently in-memory placeholders)
├── cli/              the `bench` entry point
└── util/di/          Provider base and Scope
content/
├── personas/         persona records
├── templates/        skill templates and shared blocks
└── fixtures/         planted-flaw study designs for evals
skills/               generated — do not edit
tests/
```

`gstack/` is an untracked clone of [gstack](https://github.com/garrytan/gstack),
kept as a reference for the skill-suite form factor. It is never edited, never
committed, and is not a dependency.

## Testing posture

Three tiers, because skill behaviour is only fully verifiable by running a model —
which is slow and paid, so most tests must not do that.

1. **Free static tests** — the domain model, persona record validity, generated
   skills matching their sources. Seconds, no API key, every change.
2. **LLM-judge evals** — does `/reviewer-2` actually produce a hard critique rather
   than praise? Cheap, sampled, scored against rubrics generated from the persona.
3. **End-to-end** — the skill invoked through a real Claude Code session. Slowest
   and priciest; reserved for guardrails (nothing shared without consent) and a few
   golden paths.

A persona skill with no eval is unverified, not merely untested.

## Development

Requires Python ≥3.13 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync              # create the venv and install dependencies
uv run pytest        # run the test suite
uv run ruff check benchside
uv run ruff format benchside
```

## Current state

Built and verified:

- All four domains, with model, ports, services, commands, queries, events, and DI
  providers.
- The full consultation flow — open, state a hypothesis, raise and resolve a
  critique, record a decision, capture a gap, close — with the aggregate correctly
  refusing to converge while a critique is open.
- The consent gate: export raises before touching anything when no grant is active.
- Rubric derivation from a persona's failure modes.

Not built yet:

- Every port is bound to an **in-memory placeholder**, so nothing persists. The
  JSONL journal, the content loader, and the redaction engine are the next
  adapters.
- The CLI raises `NotImplementedError`.
- Skill compilation is scaffolded but the renderer is not written, so `skills/` is
  empty.
- `content/` holds no personas, templates, or fixtures yet.

## Licence

Apache 2.0. See [LICENSE](LICENSE).
