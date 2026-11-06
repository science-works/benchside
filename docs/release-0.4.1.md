# Benchside 0.4.1

This release improves faithful scientific recording, fixes the reviewed journal
and sharing issues, and prepares the Python package for pip/uv distribution.

## Update every app sharing a notebook

**All apps sharing a private notebook must use Benchside 0.4.1 or newer.** Once
0.4.1 saves a notebook using the hypothesis-reviewer role or multiple disciplines,
older apps—including 0.4.0—refuse to open it and request an update. This prevents
older readers from treating newer records as damaged. Keep the existing notebook
and update each app; do not recreate or overwrite it to bypass that check.

## Changes

- Research-role guidance better distinguishes supplied evidence, researcher
  decisions and suggestions. The supervisor supports exploratory discussions
  without requiring a hypothesis; focused hypothesis review remains separate.
- ODT/Markdown journal exports work for either format or both. Reading copies
  refresh once per command rather than after every event in that command.
- Survey answers that are blank or match sensitive-text checks are refused before
  sending, including older pending drafts. Ordinary answers still use the study
  participation agreement without a second approval.
- Full selected-conversation history is retained. At its notebook allowance,
  analysis pauses and explains alternatives; there is no automatic summarisation.
- Migration detects conflicting writes; malformed contributor identity files are
  preserved with a repair message. New notebook formats give older readers a
  clear update-required response.
- Local Claude Code setup checks linked settings before creating setup files or
  changing the storage preference. It preserves shared settings and explains
  manual options. Normal setup leaves unrelated linked settings alone.
- Python distributions include licence, Science Works maintainer attribution,
  source/support links and standalone setup instructions, retaining Rory's author
  credit. Clean wheel and source installation checks support first PyPI publishing.

## Known limits

The survey scanner currently also rejects full URLs and some local paths, even
when harmless. It cannot identify all confidential content; contextual review
remains necessary. Public-resource link handling is a separate proposed refinement.
Blank/invalid survey answers can still surface with a generic setup error in some
app paths. Receiver-side blank-answer enforcement is a separate deployment.

The core regression suite has 582 passing tests on Python 3.11 and 3.14. Package
tests exercise saved records and fresh-process restoration; they do not establish
live account-level persistence in every ChatGPT or Claude account. Installed-app
acceptance for this final build remains a separate check.

See [the review follow-up](review-followup-2026-11-06.md) and
[Python publishing procedure](publishing.md). PyPI availability should be verified
before recommending an unqualified `pip install benchside` to researchers.
