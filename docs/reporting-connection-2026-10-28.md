# Reporting connection and checks — 28 October 2026

Follow-up: [29 October live receiver check](live-receiver-check-2026-10-29.md)
records the production 0.2.0 deployment and five additional excluded synthetic
payloads. The results below describe the earlier 28 October pass.

Implementation: [tools-science-works PR #1](https://github.com/LauraRyanSW/tools-science-works/pull/1),
commit `1c512b3`, draft and unmerged. The existing generated Bugbear page is unchanged.

Private Cloudflare R2 remains the source of truth. A GitHub job reads all five
Benchside buckets with a scoped, read-only S3 credential. It validates object
hashes and schemas, excludes the seven registered synthetic payloads and applies
the client reporting rules for retries, conflicts and revisions. Invalid or
incomplete imports fail instead of replacing the last good report.

Two seven-day Actions artifacts are produced in the private repository:

- Internal analysis: aggregate metrics plus exact-text groups of reviewed gap
  descriptions. No contributor/source observation IDs, conversations or verbatim
  survey answers are exported. Counts distinguish observations from stores.
- Public-ready summary: fixed aggregate fields only, without submitted free text.
  A separate job validates this output again and proposes a draft data PR.
  It never merges. The future Vercel viewer can consume the reviewed JSON.

The job runs on the default branch only; scheduled runs remain disabled until
explicitly enabled with a repository variable. GitHub's setting allowing Actions
PR creation was not readable with current permissions and is not assumed enabled.
If that setting blocks the proposal step, the imported artifacts remain available.

## Checks in this pass

| Check | Result |
| --- | --- |
| Benchside client suite | 463 passed locally; PR #5 Python 3.11/3.14 CI passed, including archive checks |
| Receiver suite | 63 passed; TypeScript check passed |
| Local HTTP integration | All five channels passed; expanded to cover v2 linked selected-conversation gaps and exact free-text survey answers after study agreement |
| Consent/retries | Matching contributor IDs across opted-in gap/survey/activity channels; duplicate receipts verified; forbidden transcript rejected; withdrawn sharing blocked before HTTP |
| Reporting tests | 19 passed locally and on GitHub Python 3.11; pagination, SDK shape, deduplication, corruption/conflict rejection, privacy allowlist and failure preservation covered |
| Vercel preview check | Existing GitHub integration reported a successful preview deployment; no display changes or private artifacts were committed |
| OpenAI private package | Updated existing plugin to 0.2.0; source readback verified and obsolete 0.1.5 wheel removed; scope/audience unchanged |
| Installed OpenAI upgrade recall | Runtime reported 0.2.0; actual notebook revision 11 restored; A retained 8 decisions/7 records/7 questions and Q15-COPPER-28; B retained its isolated marker. All sharing off; every call read-only |
| Installed Claude update | Blocked: browser upload reported missing file-URL access. Installed version remains 0.1.5; 0.2.0 ZIP is built and previously archive-tested |
| Live R2 reporting import | Pending approval to create a read-only credential and store it as encrypted secrets in the private reporting repository |
| New receiver formats in production | Not deployed or tested live in this pass; local v2 integration passed |

The local smoke helper initially failed because it still asserted that an
installation ID must never exist. The 0.2.0 design intentionally creates one after
updated sharing consent. The helper now checks correct pseudonymous linkage;
consent, exact-content review and withdrawal checks remain in place. This fix is
in PR #5 commit `92a6f8f`.

[Reporting CI](https://github.com/LauraRyanSW/tools-science-works/actions/runs/40787528695)
· [Client CI](https://github.com/science-works/benchside/actions/runs/40787819772)
· [Installed OpenAI check](https://chatgpt.com/c/6ae200be-fabc-83eb-82a1-426897d5985a)
· [Private plugin](https://chatgpt.com/plugins/Plugin_a5f12a7a3860819195a9308479e22ad2)

OpenAI release: `pluginrel_6ae285d0a298819183186342d68745c6`.
No PR merged, no production object deleted, no schedule enabled, no LLM grouping
run and no new production submissions made during this pass. The storage key is
prepared in the Cloudflare UI but has not been created.
