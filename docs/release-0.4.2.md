# Benchside 0.4.2

Survey answers can include broader public web links after the researcher confirms
each exact link is public and contains no private details or access tokens.
Ordinary answers still send under the study participation agreement. Answers are
preserved exactly; Benchside never silently rewrites a refused answer.

## Changes

- Survey preparation and sending accept `confirmed_public_urls`. Confirmation
  applies only to the exact links in that answer; it is not a standing exemption,
  stored consent, or an additional field sent to Science Works.
- Other sensitive-text checks remain enforced. Links containing queries,
  fragments, credentials, explicit ports, local/IP hosts or recognised sensitive
  patterns still require an edited answer. The checks do not establish that a
  link is public or detect every confidential detail; researcher review matters.
- Blank, overlong and invalid survey answers return `survey_answer_invalid`,
  with instructions to correct or omit the answer rather than suggesting setup
  failed. Whitespace-only answers, including Unicode whitespace, are refused.
- The companion receiver rejects blank text before storing it. This requires
  its separate deployment; installing the client does not deploy the receiver.
- Setup/demo documentation points to current packages and daily reporting rather
  than an expired October demo watcher.

## Updating

Update local installs with `uv tool upgrade benchside`, or
`python -m pip install --upgrade benchside` in the existing virtual environment;
then rerun the appropriate setup command in [SETUP.md](../SETUP.md). Hosted apps
need the complete updated plugin/skill package from GitHub Releases.

No notebook format or submission schema changes in this patch. The 0.4.1 minimum
for shared notebooks still applies: update every app sharing an older notebook
to at least 0.4.1, and to 0.4.2 to use the new survey-link handling consistently.
Keep the existing notebook and project records.

## Verification and limits

Regression tests cover exact-link confirmation, unchanged answer bytes, unsafe
links, other sensitive text, consent withdrawal, duplicate receipts and invalid
answers. Receiver tests exercise HTTP rejection and absence of stored objects.
All package formats must pass extracted-runtime save/restore checks before release.
Live installed-app acceptance and production receipt checks are separate from
those automated tests; see the dated acceptance report when complete.
