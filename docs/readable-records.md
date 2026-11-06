# Read your Benchside records

For local storage, open the folder you chose during setup:

```text
Benchside/
  agent/
    projects/<internal-id>/journal.jsonl
    ...other private runtime state...
  researcher/
    projects/
      Software selection interviews — <short suffix>/
        Research record.odt
        Research record.md
```

Setup asks once whether you want **ODT (default), Markdown, or both**. The tree
above shows both. Open the ODT in a compatible document reader such as Word or
LibreOffice, or choose Markdown for a text editor. Each contains the current
questions/decisions and the complete saved project history, including previous
decisions, hypotheses, critiques, role outputs, question answers and workflow
observations. This is the saved journal, not a copy of every chat message or
attached source file. A short suffix prevents similarly named projects colliding.

Benchside refreshes these copies after recording and during local setup.
Ask “Refresh my readable records” to rebuild them explicitly. Your agent uses
`records.export`; terminal users can use `bench journal export`.
Ask “Use Markdown for my readable records” (or ODT/both) to change the preference
for this store. The agent reads `records.preferences`, saves the choice with
`records.configure`, and refreshes the current project. Other projects use the
new format on their next save/export. Earlier copies of unselected formats are
preserved but no longer refreshed; use the current returned file links. This
preference does not change JSON journals or consent.
If a copy cannot be updated, the scientific save still succeeds and Benchside
reports the stale copy. Retry the export, not the scientific recording action.

The journal is the source of truth. Editing a generated document does not update
Benchside and those edits may be replaced next time. Ask Benchside to record a
correction so it remains in the history. Other files you place in a readable
project folder are not overwritten. Changing a project's title through setup
renames that folder while retaining the same project identity.

All these files remain in your chosen private store. They are not sent to Science
Works. Neither the journal nor readable copies may be written into a Git checkout.

## Existing stores

Older stores have `projects/`, `reporting/` and related state directly at the root.
They remain supported and receive a `researcher/` reading area. To organise them
into the new structure:

1. Update every agent sharing the store to Benchside 0.4.0 or later.
2. Stop the other agents using it. An older running agent could write to the old
   path; do not migrate while testing or recording elsewhere.
3. Ask your updated agent to organise the store. It calls `storage.organise` only
   after confirming that the other agents are idle.
4. Reopen Benchside. Verify the existing projects, decisions and sharing choices.

Migration verifies a copy before switching paths. Originals remain in
`agent/legacy-backup/`; no automatic backup deletion is performed. Unrelated
files in the chosen root are left alone. If migration reports an error, preserve
both folders and use the error to recover; never start over with an empty store.

## Cloud notebooks

Claude Docs/ChatGPT native notebooks keep their existing saved-state format and
human-readable project pages. The local folder upgrade does not apply there.
Use the host's document-export functionality for a downloadable document when
available; installing Benchside cannot add a missing host download capability.
