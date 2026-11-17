# Private Benchside memory in Claude file artifacts

Use this account-native route when Claude exposes exact artifact file downloads
and version-guarded file uploads. It uses the same `native.*` runtime and single
snapshot as [native memory](native-memory.md); it is not a new backend or a public
website. Use this for new Claude app notebooks; Claude Code normally uses a
chosen durable local folder. Claude Docs is no longer a supported notebook store.
The 16 November 2026 synthetic test passed file readback, a deliberately stale
write and restoration in a separate chat. Check the actual account's tools;
tool names alone do not prove that files reach the execution environment.

## Check and locate

- Discover the Artifact tools and inspect `get_artifact`, `list_files`,
  `read_file` and `publish_files`. The required read form uses **`paths`**, not
  singular `path`: it returns a file resource that the host saves locally.
  `publish_files` must accept local file paths and a `base_version` that rejects
  stale writes. Never substitute inline snapshot text or a blind update.
- Discover existing notebooks through the host's list/search tools and retained
  locator. Verify the artifact's stable `slug`, owner-only `read` and private
  `folder_audience`; do not choose by title alone or create inside a shared folder.
  A normal file artifact has no true `made_from_type` value. If a selected Doc
  rejects `read_file`, do not keep retrying it as a file artifact.
- If a selected existing notebook cannot be read exactly, pause recording for
  that project and keep discussion/checkpoints explicitly unsaved. Only a
  separately chosen **new project** may start in a new store. A new empty
  notebook is never a restoration.

## Older Claude Docs and duplicate copies

Do not create or write Benchside notebooks in Claude Docs. Earlier development
notebooks remain intact and read-only. There is no supported automatic migration
in this beta, and no need to migrate synthetic test notebooks during setup.

If the researcher explicitly needs an older notebook recovered, they can supply
an exact Markdown export (Export → Markdown, then attach), or a capable local
agent may obtain an exact export file. Do not promise that every host exposes
that export route; it still needs account-level verification. Validate the file
with `native.inspect`, deriving the workspace ID from its envelope and comparing
its ID/revision with the source if accessible. Never retype the payload. Reading
an export successfully is not proof of a completed migration. Stop after the
read-only inspection and explain that resuming it in a different store requires
an explicitly arranged, verified move; do not create an active second copy.

Candidates with the same `workspace_id` are copies of one notebook, even if their
names differ. A title or highest revision cannot establish which has all the
work. Never write to a copy marked “Moved to <link>”; follow its destination and
verify it. If two unretired copies exist, show both links and pause recording
until they are reconciled. A future agreed move must preserve the source, verify
exact destination readback and, with the researcher's approval, mark the source
“Moved to <link> on <date>; do not record here” outside the encoded state. Never
modify the state block or rename project registrations to manufacture a move.

### Discovery in a new chat

For new installations, title the ordinary artifact **Benchside private memory**.
This title is a search aid, not identity or access control. On a fresh chat with
no notebook link, use the discovered artifact list/search operation scoped to the
current owner's artifacts, searching for `Benchside`. Include older/custom-titled
Benchside candidates; do not assume a cached path or ordinary chat memory exists.
Read candidate metadata first. List older Docs separately as “may hold earlier
Benchside projects; cannot be opened through this route” before registering a
new project. For ordinary file artifacts, use `list_files` for `memory/state.md`
and validate snapshots with `native.inspect` to find registered project titles.
Check for duplicate workspace IDs as described above.
Check privacy before fetching private state. If several notebooks match, show
their titles/links and ask the researcher which to use. Retain the selected stable
slug and exact project registration after selection; never silently choose by
the standard title. If list/search is unavailable or no candidate matches, ask
for the existing notebook link rather than create a duplicate. An ordinary
artifact's own title, owner metadata and saved project index are the durable
discovery mechanism; no undocumented host "setup context" is required.

## Layout and creation

After the researcher chooses this store, create a private ordinary artifact with:

- `memory/state.md`: exact `result.markdown` from `native.create`.
- One dedicated generated journal file per project, for example
  `projects/<unique-readable-name>/journal.md`. Choose a unique path once and keep
  it stable when titles change. Do not put manually edited notes in generated files.
- A minimal `index.html` with the Benchside title and links to readable journals.
  No network scripts, tracking, public data store or automatic sharing. Treat
  journal content as text; escape it if generating an HTML reading view.

Generate files with code in a private working directory that the upload tool
actually accepts. Initial `publish_files` takes `title` and
`files:[{"as":"memory/state.md","path":"<absolute generated file>"}, ...]`;
omit `slug`, `base_version` and `mode` only for creation. Inspect the returned
`slug`, URL, version and privacy. The observed creation default was `read:owner`
and `folder_audience:owner`; verify it rather than assuming it in another account.
Never call a share/public-access operation. The tool's name **publish_files**
does not itself mean public access: this route keeps the artifact owner-only.

Use `list_files` and `read_file` on the actual created files. Register a new
project using its **returned journal file URI**, such as
`artifact://<observed slug>/projects/<chosen path>/journal.md`, as both
`project_document.document_id` and `setup.project_key`. Do not manufacture a
document ID for a file that has not been created/read. On return, reuse the exact
saved registration and project ID, including any earlier valid locator convention;
never rename registrations to match a new example.

Give the researcher the artifact link after verified creation. The owner-scoped
artifact listing above discovers it on return; its snapshot indexes project file
locators. Do not copy the encoded snapshot into a second index or rely on temporary
paths for discovery.

## Read, operate, save, confirm

1. `list_files` before first modification in a new chat. Read with
   `read_file({"slug":"<observed slug>","paths":["memory/state.md"]})`.
   The summary supplies `version`, each file's `uri`, size and file SHA-256;
   the resource supplies an actual **saved local path**. Use that returned path,
   never a constructed `/tmp` name or inline tool text. If there is no file,
   stop recording and explain the missing bridge.
2. Read the file with code, check its byte hash against the returned file hash,
   and run `native.inspect` / `native.run` / `native.batch` as documented. Derive
   `workspace_id` from the fetched envelope without decoding the private payload
   into chat. Omit `document_limit_bytes`: ordinary files use the runtime's
   default 190000-byte bound. Respect the runtime's capacity response.
3. Save candidate `result.markdown` from the response file to a new local file.
   When `changed:true`, call the observed `publish_files` tool with:

   ```json
   {
     "slug":"<observed slug>",
     "base_version":"<version from the read that supplied the input>",
     "mode":"patch",
     "files":[{"as":"memory/state.md","path":"<candidate file>"}]
   }
   ```

   Patch only the intended file. Do not use replace mode, remove unrelated files,
   change sharing, or use `publish_version`/`edit_version` to retype the snapshot.
4. Fetch `memory/state.md` again through `read_file(paths)`. Check the fetched
   file hash and run `native.confirm` on **that fetched file** with the candidate's
   workspace ID, revision and snapshot digest. The file SHA-256 and Benchside's
   snapshot SHA-256 are different checks; do not interchange them. A local
   candidate matching an upload digest is not fetched readback.
5. After confirmation, refresh only the selected project's generated journal
   from `project_journal.markdown`. Its patch must use **the version paired with
   the exact confirmed state readback**, not a newer version from metadata or a
   conflict response. A failed view refresh does not undo a confirmed notebook
   save. Every file change advances the **whole artifact's version**. Carry the
   returned version forward with the cached state only after your journal/index
   patch succeeds against that paired version and leaves `memory/state.md`
   unchanged. Never refresh the version alone: that would allow an old cached
   notebook to overwrite another chat's newer state. If any patch conflicts,
   reread the state file and its version together, reconcile, and regenerate the
   journal before retrying. After an ambiguous patch response, reread both too.

For `changed:false`, do not publish the notebook. Prefer one `native.batch` and
one save for justified actions in the same turn; refresh the journal once.

## Conflicts and verification

A stale `base_version` produced HTTP 409 with `conflict:true` and
“Nothing was published”. Read the latest file and rerun the original operation
with the same operation ID. **Do not attach the new version to an old candidate.**
Follow the native guide's bounded retries, generation rules and ambiguous-save
reconciliation. A newer valid notebook must never be rolled back to satisfy a
confirmation against an older candidate.

Treat `(exact state file, artifact version)` as an inseparable pair. Example:
if A confirms V2 and B saves V3, A's journal patch must still use V2 and fail.
It must not fetch V3, patch its old journal to V4, and combine cached V2 state
with the V4 guard. A matching post-save checksum cannot detect that lost update.

Test a synthetic decision and open question, exact readback and fresh-chat
restoration before claiming continuity. A readable journal is a derived view,
not evidence that the state was fetched. Never send the artifact or snapshot to
Science Works: optional contribution review and approval remain separate. Sharing
the artifact would expose its state files, even if its front page hides them;
keep the whole artifact private.
