# Benchside 0.2.0 review follow-up

These changes are on the review branches. They are not merged, deployed or installed
in the live apps. Use the matching receiver update before releasing the new client.

## Product and data decisions

- Workflow gaps and friction are the primary metascience output. A selected
  research conversation can contribute a sanitised candidate through the existing
  five gap types and review/send flow, without opening a Benchside consultation.
- Activity categories are supporting context. The host LLM chooses one main
  activity from defined categories, with `other` and `unknown` fallbacks. The rubric
  distinguishes coding from analysis and literature work from critical review.
  Work without a Benchside role remains separately labelled. Richer later grouping
  uses reviewed gap descriptions, not a new free-text summary of research logs.
- Sharing remains optional. New contributions use one random ID per private store,
  reused from the usage installation ID. Science Works can group that store's
  contributions over time and across channels. This is pseudonymous, not a verified
  person or account. Existing unlinked grants need an explicit updated choice;
  received legacy observations remain unlinked.
- Public software/dataset names, versions and general failures may explain a gap.
  Model-derived descriptions exclude private scientific findings, measurements,
  hypotheses, sample identifiers, detailed protocols and source passages.
- Surveys support fixed choices and bounded researcher-written text, preserved
  exactly. Agreement to the displayed study comes before questions. Supplied
  answers then authorise submission without a second approval prompt. Changed
  study terms, destination or consent require a new agreement; withdrawal blocks
  sending. The runtime still verifies the exact draft, version, digest and receipt.
- Study definitions and their publication history belong in the receiver repository
  (`src/studies.json` and Git history). Record publishing commit/deployment and
  definition digest. Responses in private R2 carry the corresponding version/digest.
  The catalog remains empty; no survey is enabled by this patch. Older clients need
  updating before the first text-question catalog is published.

## Projects, evidence and reporting

A Benchside project is a continuing line of research, potentially spanning many
conversations and all seven roles. Its ID selects the private project journal in
whichever store the researcher chose. Returning to an existing project restores
that journal's records, decisions and unresolved sittings. A new chat does not
require a new project. Sharing preferences and the random ID belong to the store;
scientific histories remain separated by project. Two apps using the same store
can therefore continue the same project, while separate accounts/stores do not
synchronise automatically.

Evidence labels appear in activity fields and selected-conversation problem
reports. `researcher_reported` means an explicit statement; `model_inferred` means
classification from visible evidence. Approving a batch does not change its basis.
The model cannot infer helpfulness merely because a task finished.

The internal report reads authorised private collector exports, deduplicates
submissions and revisions, and returns aggregate counts. It now counts contributing
stores across channels and per gap kind, while excluding IDs and raw survey text
from its output. An installation/store is not necessarily a person.

A practical next step for the Vercel viewer is a scheduled/manual GitHub analysis
job reading private R2 with a scoped secret. It could propose groups from sanitised
shared gap descriptions using an LLM, retain the grouping version and membership,
and calculate counts/distinct stores in code. Publish reviewed, safe aggregates
into `LauraRyanSW/tools-science-works`; Laura can deploy them. Neither this job nor
an LLM grouping pipeline or Vercel integration is implemented by this patch.

## Claude review findings

| Finding | Change |
|---|---|
| 8 | Recall-hook history is quoted as data, including embedded newlines. |
| 10 | Hook-settings writes use atomic replacement; failed writes preserve the old file. |
| 12 | Mitigated: optional analysis/study history has a 48 KiB compressed allowance in native notebooks. Growth and sends pause before consuming research space. Existing records/receipts are retained, and research/opt-out remain available. This is a capacity safeguard, not automatic archival or unlimited storage. Large legacy notebooks may still need migration. |
| 13 | Expiry/reset removes fallback registrations without retiring an explicitly addressed open conversation. Another conversation cannot adopt that pointer. Applied to PRs #5 and #6. |
| 14 | Session identity is written before registry access; registry problems do not suppress recall. Small clock skew is tolerated. Applied to PRs #5 and #6. |
| 15 | Failed sends on legacy notebooks do replay/capacity preflight on a copy, preserving the generation and safe retry ID. |
| 16 | Analysis consent states the previous complete week, random or researcher-chosen selection, and maximum 20. Old grants require the revised explanation before analysis resumes. |

Finding 4 remains addressed by PR #6 targeting Rory's PR #4. No merge is performed.
No synthetic production objects are deleted. Claude's slow literal-text notebook
save remains an installed-host limitation; these changes do not fix that connector.

## Validation

- Main client: 463 tests pass under Python 3.11 and 3.14.
- PR #6: 130 tests pass.
- Receiver: 63 local Worker tests pass, including exact-byte storage and retry
  handling for linked gaps, feedback, activity and free-text surveys; type check passes.
- Production-code lint and role compilation checks pass.
- Three archive formats pass offline extracted-runtime checks for every role,
  local/native restoration, shared-store continuation, batching and replay.
- Native optional-history tests first reproduced growth displacing the allowance,
  then verified refusal before sending, continued research and consent withdrawal.

Remaining release checks: review the changed consent/data design, deploy the
matching receiver, install the new packages and exercise the new flows in both
apps. Local/extracted-runtime tests do not establish live connector behaviour.
