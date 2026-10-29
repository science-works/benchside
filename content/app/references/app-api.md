# App adapter

Sharing previews retain one current review batch per channel. A replacement
preview supersedes earlier drafts in that channel, so approve only the current
preview. An identical preview reuses its draft ID; failed sends retain those
exact bytes for retry. Original private observations/feedback and submitted
receipt history remain available.

The assistant executes `python3 <skill-directory>/scripts/benchside_app.py` for an
installed skill. Source setup saves `runtime/source.json` so this entry can use the
original Python environment and source directory from any working directory, even
when `bench` is not on PATH. Keep that environment/source available; after moving or
reinstalling it, rerun `bench setup` through the agent to refresh the saved paths.
Packaged skills use their bundled runtime instead. A checkout before setup can
use `uv run bench app`, or `bench app` when installed on PATH.
Provide one JSON object on stdin. Responses are JSON: `ok` plus `result`, or an
error. Read the result before continuing. Python 3.11+ and POSIX storage are required.
Use `{"action":"version"}` to check the running Benchside version without opening
research storage. Do not import modules directly from the sealed runtime cache.

For native saves, the launcher accepts `--response-file /absolute/private/new-response.json`.
It writes the complete JSON response to a new owner-only file and prints a compact
summary: opaque `snapshot` and `markdown` are replaced by a `candidate` containing
the workspace ID, revision and digest. The full response file retains both fields
unchanged, including on inner action failure. Load `result.markdown` from that file
as data when constructing a guarded document-tool request; see [native memory](native-memory.md).
The file is a temporary transfer aid, not durable memory or a save confirmation.
Native requests accept an optional `document_limit_bytes` (32768–190000) for a
store that holds less than the default; Claude Docs uses 65536. Omit it elsewhere.
Use a fresh filename per call; an existing file is refused before the action runs.
If writing fails after execution, the full response is printed with
`response_file_error`: preserve it and check what completed before retrying.
Packaged dependencies are bundled, pinned and installed offline into a temporary runtime
cache, not into the researcher's project. Release bundles support standard CPython
3.11–3.14 on macOS (Intel/Apple Silicon) and glibc Linux (x86-64/ARM64), with pip or
uv provided by the host. Do not change network settings or fetch replacement
packages when setup fails; report the error. For cloud accounts use [native memory](native-memory.md):
`native.run` restores a validated native document into a fresh temporary directory
for each call and returns a candidate to save through the host's native tools.
For local desktop storage the private journal defaults to `~/.local/share/benchside`;
`storage.configure` remembers a chosen durable directory outside Git in
`$XDG_CONFIG_HOME/benchside/storage.json` (default `~/.config/benchside/storage.json`).
An explicit `BENCHSIDE_HOME` overrides that preference; otherwise XDG/default
locations are used when no preference exists. Choosing a directory does not migrate data.

Do not use cloud `/tmp`, `/mnt/data`, or a disposable VM home as durable storage
without verification. Native document readback, including a new conversation,
is required before claiming cloud continuity. Building a package is not a host
integration test. The project source and researcher journals are separate.

## Setup and continuity

- `{"action":"roles"}` lists the seven roles.
- `{"action":"participation.status"}` returns `response`: `unasked`, `declined`,
  `deferred` or `configured`. After an explicit answer use `participation.set`
  with `response:declined`, `deferred`, or `configured`. This remembers whether
  setup already asked; it grants no permission and sends nothing. Save the
  independent consent choices first. Decline/defer requires all participation
  choices off; changing the marker never silently revokes existing consent.
- `{"action":"profile.status"}` returns optional demographic selections and
  their separate inclusion preference. `profile.set` takes `demographics` and
  boolean `include_in_usage`; see [sharing](sharing.md) for valid categories.
  Both actions work through `native.run` as well as local storage.
- `{"action":"storage.location"}` returns the effective local storage path without writing.
- `{"action":"storage.configure","directory":"/absolute/chosen/folder"}` verifies
  a write and remembers the local choice. Use only after the researcher chooses it.
  Not applicable inside `native.run`.
- `{"action":"projects"}` lists existing local app project IDs/titles.
- `{"action":"setup","project_id":"<selected existing ID>","host":"claude","surface":"desktop"}`
  starts a new session in an existing project, including one created by another app.
  Session app metadata is isolated; creation identity never changes.
  For new projects supply `project_key` instead, with an optional `title` for discovery.
- `{"action":"storage.probe"}` writes a random marker and returns its token.
- `{"action":"storage.check","token":"<returned token>"}` checks the same store.
  Run this after moving to a fresh conversation and resetting its execution
  environment. The host must retain the storage path without ongoing user setup.
- `{"action":"setup","host":"claude","surface":"desktop","project_key":"<actual stable project ID or folder>"}` returns `project_id` and `session_id`.
  `host` is `claude`, `chatgpt`, or `unknown`; use `unknown` for Codex/other apps
  under the current reporting schema rather than inventing a wire value. Surface is `web`, `desktop`, `cli`, or `unknown`.
  Optionally supply `app_version` only when the host exposes a release version
  (for example `1.2.3`); otherwise leave it `unknown`. Never use a user agent,
  account identifier, model name or guessed version. It is included only in usage
  reports if the researcher opts in and approves the preview.
- `{"action":"recall","project_id":"<returned ID>"}` returns private records,
  unresolved critiques, recent decisions and open sittings. The default `history:recent`
  includes the latest five decisions/records plus `total_decisions` and `total_records`.
  Add `"history":"all"` to retrieve every saved decision and research record for
  that project. The existing `recent_decisions`/`recent_records` field names are
  retained in both modes. This is read-only and does not change sharing choices.
  Terminal installations also support `bench recall --all`.
- `{"action":"start","project_id":"...","session_id":"...","role":"methods-clinic"}` returns the sitting and recall.
  The sitting ID is `result.sitting.id`, not `result.sitting_id`. `setup` creates
  a conversation session; `start` resumes an unambiguous existing open sitting
  for the role rather than creating another discussion.
  If multiple matching sittings exist, choose one from recall using `sitting_id`.

## Recording

Every recording request includes the returned `project_id`, `session_id` and
`sitting_id`. IDs for new records are generated by the runtime; quote returned IDs.

| Action | Additional fields |
|---|---|
| `hypothesis` | `statement`; optional `supersedes` |
| `record` | `record: {kind, summary, details: [...], sources: [...]}` |
| `critique` | `target: {kind: "claim", claim, ground}`, `{kind: "method", step, flaw}`, or `{kind: "interpretation", result, alternative}` |
| `resolve` | `critique_id`, `resolution`: `design_revised`, `rebutted`, or `accepted_as_limitation` |
| `decide` | `decision`, `rationale`; optional `supersedes` |
| `gap` | `gap` object described below |
| `close` | `converged`: true/false, `detail`: agreed outcome or explicit abandonment reason |

Record kinds: study-design → `study-design`; methods-clinic → `methods`;
results-meeting → `results`; repro-check → `reproducibility`;
journal-club → `literature`; peer-review → `review`.
These roles need a research record and decision before concluding. A literature
record also needs a real inspected source locator. `/pi` retains its hypothesis
requirement. Do not manufacture a critique to complete a phase.

Method flaws: `missing_control`, `confound`, `under_powered`, `pseudoreplication`,
`selection_bias`, `unvalidated_instrument`. For concerns outside these categories,
use a grounded claim or interpretation target rather than misclassifying it.

Gap objects:

- `{kind:"missing_tool", task, reached_for, why_failed}`
- `{kind:"unfindable_data", sought, where_searched:[...]}`
- `{kind:"manual_toil", task, frequency}`
- `{kind:"dead_end", approach, cost}`
- `{kind:"missing_index", question}`

Describe workflow needs, not unpublished findings, names, project identifiers,
source documents or data. Scientific records remain private even if sharing is on.

## Minimal example

After setup/start, record the observed methods problem using the actual returned IDs:

```json
{
  "action": "record",
  "project_id": "<returned project ID>",
  "session_id": "<returned session ID>",
  "sitting_id": "<returned sitting ID>",
  "record": {
    "kind": "methods",
    "summary": "Low recovery after extraction",
    "details": ["Expected recovery is 80%; observed 20%.", "A spike-recovery control can localise the loss."],
    "sources": []
  }
}
```

The example's content is illustrative. Record the researcher's actual evidence.

## Optional metascience

The independent `metascience.*` actions require no role or consultation. See
[metascience](metascience.md) for consent, study invitations, scope selection,
random or researcher-chosen selection, private candidate gaps, supporting activity
categories, review and delivery. `metascience.gap` adds a sanitised candidate to
the normal gap-sharing flow. `metascience.join_study` saves agreement to a specific
survey before questions; supplied answers then authorise sending without a second
approval prompt. Other submission types still need exact review and approval.
Native document transport preserves this state alongside the other records.
The host retrieves only explicitly selected, sampled conversations using its
existing tools; the Python adapter neither reads chat logs nor runs a model API.
