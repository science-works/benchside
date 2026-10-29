# Architecture

This document explains why benchside is built the way it is. For setup and
usage, see [README.md](README.md).

## The core idea

benchside has two products in one workspace. The first is a set of seven
scientific roles, delivered through CLI skills and a packaged app adapter.
The second is underneath: while a
scientist works, the system builds a structured record of where their workflow
broke down, which a science-policy nonprofit uses to find gaps where tools are
needed.

Both products depend on the same structural decision: **the conversation is
prose, but the record is typed.** The persona talks to the scientist in
natural language; at each meaningful transition the skill calls the `bench`
CLI or structured app adapter, which turns what happened into a validated, typed event in an append-only
journal. Everything else — cross-session memory, cheap evals, aggregatable
insights — falls out of that split.

## Layers

Hexagonal, dependencies pointing inward:

```
cli/  ──────────▶  application/  ──────────▶  domain/  ◀──────  infrastructure/
(entry points)     (composition root)         (pure)            (port impls)
```

The domain layer has no I/O and no LLM calls, so it tests in seconds without
an API key. The skill surface is an adapter: the same `/pi` logic is reachable
from a skill, the CLI, or a test harness.

Per-domain layout is uniform:

```
<domain>/
  model/      aggregates, entities, value objects — pure, no I/O
  command/    write side: one file per use case (Command DTO + Result + Handler)
  query/      read side: same shape, must not mutate
  event/      journal events
  port/       Protocol interfaces
  service/    business logic
  util/di/    this domain's Dishka provider
```

No `adapter/` inside a domain — implementations live in `infrastructure/`.
No `api/` — domains are protocol-agnostic. Entry points call application
handlers or domain services, which use ports. Handlers are thin and do not
implement persistence.

## The domains

**`consultation`** — everything that happens when a scientist meets a persona.
Two aggregates, split by lifetime:

- `Project` is the durable thread: hypotheses and their supersession chain,
  critiques and their resolutions, decisions with rationale, and role-specific
  research records with source locators. This is what a
  scientist means by "my work on X".
- `Consultation` is one episode (a "sitting"): just the state machine
  `Framing → Probing → Challenged → Converged | Abandoned`, referencing its
  project by id.

The service keeps them in step: raising a critique mutates the project, then
reconciles the sitting's state against the project's open-critique set. A
sitting cannot converge while a critique is open.

**`authoring`** — seven personas, templates, and compilation for CLI and app delivery. Runtime policy is snapshotted when a sitting opens.

**`export`** — consent, redaction, preview, and the single path off the
machine. Deliberately separate from `consultation`: the authority governing
what leaves must not live inside the code that wants to send it.

**`shared`** — the kernel: typed ids, the gap taxonomy, the capture
vocabulary, the `Journal` port, and base classes (`Aggregate`, `Service`,
`Command`/`Query`/`Result`, `Event`).

## The journal is the source of truth

Every durable fact is an event appended to a per-project JSONL stream under
`~/.local/share/benchside/projects/<id>/`. Aggregates are folds over that
stream; repositories hide the folding, so the domain never knows the store is
event-sourced. "Active" state (the current hypothesis, the open grant) is
always computed from history, never stored as a mutable flag. Corrections are
new events that supersede old ones — history is never rewritten.

Two consequences worth naming:

- **Replay determinism.** A sitting's close requirements are snapshotted into
  its `ConsultationOpened` event. Reading the persona YAML live at close would
  mean editing a persona retroactively changes whether last month's sitting
  can legally close. The journal must be self-contained.
- **Session identity is local.** Journal envelopes carry the session that
  produced them (`{"type", "session", "data"}`). Claude Code's SessionStart hook
  registers its session per project and writes `CLAUDE_ENV_FILE` so concurrent
  shells retain their own identity. The app adapter generates a random session
  ID at setup. Neither session identity nor transcripts enter exported payloads.
- **Ids are opaque and runtime-generated.** The model never invents `h1` or `k3`;
  every recording command returns the id it created. Deterministic ids collided
  and let replayed duplicates corrupt folds; uuids ended that class of bug.

## Personas are programs, compiled to skills

A persona is a data record (`content/personas/pi.yaml`): stance, voice,
expertise, forcing questions (ask / push-until / red-flags), failure modes,
escalation rules, and a `flow` — ordered phases with goals, guidance, capture
obligations, and prose exit conditions. `bench compile` renders it through a
template into a skill.

One record generates three artifacts that therefore cannot drift apart:

1. the skill prose Claude reads,
2. the eval judge rubric — derived from the persona's declared failure modes,
3. the capture obligations the CLI enforces at close.

Adding a specialist means adding a YAML file, not writing orchestration code.

The consultation state machine stays the invariant layer underneath: persona
phases are conversation guidance, enforced only at `bench sitting close`.
Mid-flow phase position is model-held on purpose — only the close is a gate.

## The runtime owns the invariants

The model's job is to say what happened in words; the runtime's job is to turn
that into a valid typed record — or refuse. Ids, timestamps, enum validation,
referential integrity, state legality, and close enforcement live in the shared
services and domain models, used by both adapters.
The one that matters most: a converged close is refused until the sitting's
capture requirements are met. You cannot cleanly finish a sitting you never
recorded, which is what keeps journals from silently ending up empty.

Command surface follows the two audiences. Capture verbs (`hypothesis`,
`record`, `critique`, `resolve`, `decide`, `gap`) are flat and terse because they are
the model's mid-sitting hot path, where nesting is a compliance risk. Human
surfaces (`journal`, `share`) are grouped nouns. Project-bound commands refuse
to run outside a `bench init`-ed project; `BENCH_SITTING` is the explicit
escape hatch for cleaning up stranded sittings.

## Hooks are plumbing, never meaning

Explicit `bench init --legacy-cli` enables Claude Code hooks; the default shared
entry uses the app adapter without these hooks or competing per-role CLI skills.
Claude Code hooks fire on session lifecycle, so they own what can be done
deterministically with no model compliance:

- **SessionStart** injects the project's memory (current hypothesis, open
  questions, recent decisions) into context via stdout — the model starts
  warm without being told to run anything.
- **SessionEnd** archives the transcript under the project and retires the
  session's sitting pointer. It never auto-closes a sitting; the next session
  is told it's still open.

Hooks cannot see semantics ("the scientist stated a hypothesis" is not a tool
event), so all capture stays in explicit `bench` calls, instructed by skill
prose. Hook hygiene is inherited from gstack: always exit 0, hard timeouts,
errors to a log, a fast bail-out outside benchside projects, and consented,
idempotent registration — Claude Code runs project hooks without prompting,
so the consent moment has to be ours (`bench init --legacy-cli` asks).

Sitting pointers are per-session files keyed by `session_id` and scoped to a
project at resolution time, so parallel sessions never fight and one
project's stranded sitting can never bleed into another (a bug we shipped and
fixed; see `tests/unit/cli/test_pointer_scoping.py`).

## Consent and export

Consent is an event-sourced ledger, not a config flag: grants and revocations
are events, the active grant is computed by folding them, and every export
appends a content-free record (observation ids + payload sha256). Revocation
is meaningful because the ledger shows exactly what left and when.

The export path enforces its order: check consent, filter to what the grant
covers, redact, preview, send — and the preview is the exact bytes that would
be sent, not a summary. Scanning happens on those same bytes (scan-at-sink;
never scan a string and re-render it). The HTTPS sender is reached only after
consent and exact-content approval; an empty endpoint setting selects the
refusing sink. The shared unit is a typed gap
(`missing_tool`, `unfindable_data`, `manual_toil`, `dead_end`,
`missing_index`) — hypotheses, results, and data are structurally absent from
the export schema.

## The UI layer

`benchside/cli/ui/` follows a two-layer pattern: a `UI` facade over a
`Renderer` protocol with three implementations — `RichRenderer` (the only
module allowed to import rich), `PlainRenderer` (identical wording, no ANSI,
exact-string testable), and `RecordingRenderer` (asserts event sequences).
Chrome goes to stderr; machine channels stay pure stdout: `--json` outputs,
the `<bench-sitting:>` marker, hook context injection, and the share-preview
payload. Non-TTY, `NO_COLOR`, `CI`, and dumb terminals all degrade to plain.

## Dependency injection

[Dishka](https://github.com/reagento/dishka), two scopes: `APP` (process) and
`UOW` (one `bench` invocation). Domain providers bind services and handlers;
`infrastructure/journal/di.py` binds ports to file-backed implementations via
`provides=`. `create_container(*extra_providers)` lets tests substitute fakes
because later providers override earlier ones, and the graph is validated
eagerly — a missing binding fails at startup, not first use.

## Testing

Strict TDD (red before green, regression test before every bug fix) across
three tiers:

1. **Free static tests** — domain, adapters, CLI dispatch, persona validity,
   compiled-skill freshness. No API key, seconds, every commit.
2. **LLM-judge evals** — does `/pi` press or cheerlead? Scored against rubrics
   generated from the persona's failure modes. Cheap, sampled. (Planned.)
3. **End-to-end** — real Claude sessions, reserved for guardrails (nothing
   shared without consent) and golden paths. (Manual today, harness planned.)

A persona with no eval is unverified, not merely untested.

## App access and reporting

`application/app.py` exposes structured requests for guided setup, scientific
recording, recall, resumption and sharing. The assistant invokes the bundled
runtime or `bench app`; both dispatch through `application/bridge.py`, and
researchers need no terminal commands. Onboarding asks for an accessible storage
location. `storage.configure` verifies and remembers an explicit local directory;
`BENCHSIDE_HOME` remains the highest-priority override. It never migrates data.

Stable creation keys become opaque IDs. `projects` exposes IDs and optional titles;
setup can reuse a selected ID from any app. Creation identity is immutable, while
`app-sessions` preserves each caller's project/app context so simultaneous setup
cannot relabel another session. Legacy notebooks without session files still replay.
Journals live outside Git. File locks serialize app/CLI transactions and protect
individual journal appends. They do not coordinate cloud-sync clients across machines.

New roles snapshot their research-record kind and whether critique requires a
hypothesis. Their records contain a summary, details and source locators.
Literature records require a source. Old events retain their defaults and close
requirements, so replay never depends on current persona definitions.

`application/sharing.py` coordinates independent sharing choices. Prepared drafts
are saved outside the repo with consent grant, destination, exact payload and
digest. Sending rechecks these, validates the collector's bounds, scans the same
bytes, verifies its receipt and records a content-free receipt. Edits affect a
submission, never the private scientific journal.

Feedback and usage have strict separate schemas. Usage aggregates consultation
events into versioned weekly snapshots; conversation IDs and scientific text are
discarded. The internal report deduplicates retries and selects the highest
revision per installation/week, without joining individual datasets.

`application/packaging.py` generates the same agent skill for source installation
and release builds. The Claude manifest, portable root manifest and Codex overlay
all describe this shared package. A dedicated Claude plugin ZIP has its manifest
at the archive root; the standalone skill ZIP remains available.

The app packages share the core wheel and a pinned dependency lock. Startup
requires verification of native writable storage across conversations and
execution resets. A same-sandbox probe is not proof of cloud durability. There
is no remote private-journal service. The native document adapter is described below.

### Native documents

`application/native.py` bridges authorized host document tools and the same app
engine. Each `native.run` validates a compressed, checksummed notebook, restores
only allowlisted state files to a disposable directory, executes one app action,
and returns a candidate snapshot. It never calls native document APIs itself.
The skill performs a conditional write using the host's current revision/hash,
reads it back and calls `native.confirm`. A candidate is never a save receipt.

One private notebook contains project streams, consent, draft payloads, receipts
and installation-level usage metadata. That gives one commit boundary for related
state. Project IDs remain distinct and recall returns only the selected project.
Readable project journal Pages are derived projections that can be regenerated.
Persistent operation IDs make retries of already committed actions idempotent;
conflicts require rereading and revalidating against the latest notebook. Native
document persistence and external collector delivery remain separate operations.

### Optional metascience

`application/metascience.py` implements independent invitation, analysis and
sharing consent, scoped random sampling and exact reviewed submission through
the structured app API. It requires no consultation or persona. Strict models in
`domain/export/model/metascience.py` define public data-only study catalogs,
categorical survey answers and bounded activity classifications. Raw transcripts
never enter this adapter. The host performs extraction with its existing tools
only after consent, scope selection and persisted sampling.

Private `metascience/state.json` is allowlisted and validated by the native
adapter. It holds settings, private source references, sample selection, drafts
and receipts. Changing scope/consent invalidates approvals; editing records
invalidates their preview. A private random seed stabilises sampling, independent
of the optional usage installation ID. No stable participant identifier appears
in either new submission schema. Batch revisions replace earlier counts.

The collector publishes only the study catalog for reading; submitted data remain
write-only. Surveys require an active published definition with a matching digest.
The default catalog is empty. Scheduled operation belongs to the host and must be
explicitly configured, not inferred from installing this package. Host access and
classifier accuracy require separate acceptance checks; see `docs/metascience.md`.

## What's intentionally not here

- **No MCP server, no daemon.** `bench` is a short-lived CLI; the journal is
  files. Nothing needs a persistent process yet.
- **No branching in persona flows.** Linear phases + prose exit conditions
  cover the personas we have; a graph earns its complexity when a persona
  demands one.
- **No mid-flow enforcement.** The CLI gates only the close. Phase position
  lives in the model's context by design.
- **No automatic transmission.** Every prepared batch needs explicit approval.
  Identifier scrubbing is conservative and cannot guarantee anonymous free text.
