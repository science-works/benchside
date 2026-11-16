# Private Benchside memory in Claude file artifacts

Use this account-native route when Claude exposes exact artifact file downloads
and version-guarded file uploads. It uses the same `native.*` runtime and single
snapshot as [native memory](native-memory.md); it is not a new backend or a public
website. Claude Docs is a different artifact type and may lack this file bridge.
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
- An existing Doc remains the authoritative notebook until an explicitly agreed
  migration completes. Do not create an empty file artifact and claim the old
  project was restored. Migration requires an exact export of the existing
  snapshot, validation and verified restoration at the chosen destination;
  model reconstruction from notes is not migration. Keep the source intact.

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

Save the artifact URL/slug and state path in the host's private discoverable
setup context/index. The notebook already indexes project file locators; do not
copy the encoded snapshot into the index or rely on temporary paths for discovery.

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
   into chat. Omit the Docs-only 65536 limit: ordinary files use the runtime's
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
   from `project_journal.markdown`, using a file patch with the current artifact
   version. A failed view refresh does not undo a confirmed notebook save.
   Every file change, including a journal/index update, advances the **whole
   artifact's version**. Retain its returned version, or reread before the next
   write; do not reuse the version from before the journal update.

For `changed:false`, do not publish the notebook. Prefer one `native.batch` and
one save for justified actions in the same turn; refresh the journal once.

## Conflicts and verification

A stale `base_version` produced HTTP 409 with `conflict:true` and
“Nothing was published”. Read the latest file and rerun the original operation
with the same operation ID. **Do not attach the new version to an old candidate.**
Follow the native guide's bounded retries, generation rules and ambiguous-save
reconciliation. A newer valid notebook must never be rolled back to satisfy a
confirmation against an older candidate.

Test a synthetic decision and open question, exact readback and fresh-chat
restoration before claiming continuity. A readable journal is a derived view,
not evidence that the state was fetched. Never send the artifact or snapshot to
Science Works: optional contribution review and approval remain separate. Sharing
the artifact would expose its state files, even if its front page hides them;
keep the whole artifact private.
