# Acceptance checks — 23 October 2026

Scope: the four requested follow-up areas, using synthetic records only. Work
remains on the review branches. Nothing was merged, published or deployed to
Science Works, and no test contributions were sent to production.

## Results by area

| Area | Verified | Still required |
| --- | --- | --- |
| Setup and usability | Friendly project titles, remembered participation deferral, atomic private batches, exact replay and rollback pass local/package checks and live Google/Pages storage. Installed Claude saved a new project in one notebook transaction in about 7½ minutes; installed ChatGPT's setup/recording turn took 2m 21s. | Reduce Claude setup latency further. These are individual runs with different hosts and prompt histories, not a controlled speed comparison. |
| Seven research roles | The installed Claude plugin read all seven role references and answered independent synthetic scientific cases. The three corrected overclaims did not recur in a fresh installed-plugin check. Recording and resumption work for every role in all three archive formats. | A remaining reproducibility evidence-wording error is corrected in source and rebuilt but still needs installation and retest. Broaden beyond one prompt per role before interpreting this as scientific validation. |
| Installation and storage | All three extracted archives run offline. Both installed plugins passed batched setup and fresh-chat resumption from their native notebooks. The rebuilt runtime also saved seven roles through actual Google Docs and ChatGPT Pages connectors. | Verify actual Claude/ChatGPT access to the same Google notebook if advertising cross-app Google continuity. Claude's Google connector is not connected; its native Docs tools do not expose sharing permissions. |
| In-app sharing | All five routes accepted synthetic HTTPS requests from the local test client and returned stored/duplicate receipts. Both installed plugins previewed exact feedback payloads, retained drafts on failure and blocked sending after consent withdrawal. | Successful delivery from both apps to an approved reachable staging address. Both temporary-domain attempts received HTTP 403 before the Worker handled them. |

## Changes made after testing

- `native.batch` runs up to 16 private actions atomically, producing one candidate
  notebook revision. The host must still use a guarded write and readback before
  claiming it was saved. Previews, network requests and sends cannot be batched.
- Batches resolve references to earlier step results, preserve exact operation
  replay and roll back all changes when a step fails. Read-only batches do not
  create a new revision.
- Recall returns friendly project names, including older native notebooks where
  the title existed only in the project index.
- A private participation marker distinguishes not-yet-asked, declined, deferred
  and configured choices. It grants no permissions. An active consent must be
  explicitly revoked before marking participation declined/deferred.
- Supervisor instructions now distinguish a described pilot from an observed
  result. Results instructions require the effect scale before judging magnitude
  and avoid assuming how repeated measures alter an interval. Journal-club
  instructions distinguish recruitment from random allocation.
- A further correction makes the reproducibility role distinguish a researcher's
  description of a file from actually reading that file. The setup guides now
  explicitly document `start.sitting.id` and the required notebook workspace ID,
  after live agents initially guessed/omitted those fields. These last edits are
  rebuilt locally; installation of this final small update remains pending.

## Scientific conversation observations

Evidence: [installed Claude seven-role conversation](https://claude.ai/chat/e3387b4d-b148-4742-a3ba-af4a2683d661).
The model saw the seven scenario prompts and role references, not the assessment
rubric. These are qualitative observations from one run, not a scored evaluation.

| Role | Observation |
| --- | --- |
| Research supervisor | Flagged the unclear question and missing untreated comparison, but invented that the pilot showed a measurable change. Source corrected; the overclaim did not recur in the installed follow-up below. |
| Study-design consultant | Identified confounding by indication, time zero, overlap and residual confounding; did not invent a power calculation. |
| Methods troubleshooter | Proposed paired pre/post-extraction spikes and a controlled diagnostic sequence without asserting a particular reagent caused the loss. |
| Results discussant | Correctly rejected non-significance as evidence of equivalence, but asserted that repeated measurements would widen the interval and assigned magnitude without knowing the scale. Source corrected; these overclaims did not recur in the installed follow-up below. |
| Reproducibility auditor | Identified missing input versions, exclusions, parameters and environment. Did not claim to reproduce the figure, but described having read the README when only its description was supplied; evidence wording needs another check. |
| Journal-club discussant | Limited discussion to the excerpt and challenged its generalisation, but inferred nonrandomised groups from convenience sampling. Source corrected; the overclaim did not recur in the installed follow-up below. |
| Scientific peer reviewer | Narrowed the deployment claim and proposed proportionate external validation; treated possible patient leakage conditionally. |

## Live storage evidence

### Installed-app follow-up

Will installed the batched Claude build, and the same portable build was uploaded
and installed as a personal ChatGPT plugin through its supported archive UI.
ChatGPT sign-in is complete. Initial automated file uploads remained blocked, but
the normal picker successfully completed the ChatGPT installation.

- [Claude batched setup](https://claude.ai/chat/58a125af-1a8c-4aa5-af56-95c8f91b0396):
  discovered the structured synthetic notebook, preserved two earlier projects,
  created BATCH-O3 and committed revision 9 → 10 with one guarded notebook write
  and confirmed readback. The first batch used an incorrect reference and rolled
  back without changing the notebook; the corrected retry succeeded. The decision,
  evidence and full open question appear in the readable journal. No hypothesis
  was invented, participation is deferred and all sharing remains off. The live
  journal UI shows “Only you”; the model itself reported not checking its sharing
  metadata. The measured run was about 7½ minutes, including recovery and journal
  setup, so there is still a usability cost.
- [Claude fresh-chat resume](https://claude.ai/chat/87970b0e-51ef-42f0-a660-5700197555df):
  given only the synthetic project name, recovered the full decision, unresolved
  question and evidence from native Docs. It reused project
  `p-980e1dd4d5d21624919ee852540a5563` and sitting
  `c-45e8c0ad5f9e400c909520b134c020e7`, created a new conversation session, and
  confirmed revision 11 after a guarded replacement and byte-identical readback.
  The readable journal needed only its revision updated. Deferred participation,
  all sharing off and empty demographics were preserved without re-asking. The
  available Docs tools expose ownership but not sharing permissions, so the model
  correctly did not claim an automatic privacy check. The earlier UI showed
  “Only you”; ownership alone must not be treated as equivalent. Google Drive is
  listed as an organisation-installed connector but is not connected in this
  Claude account/chat, so cross-app Google continuity remains untested.
- [ChatGPT installed setup](https://chatgpt.com/c/6adb97a6-8b64-83eb-80b6-df46e73987b5):
  asked for storage, project and participation; verified the private location;
  created GPT-O3 through the installed runtime and `native.batch`; confirmed
  revision 6 → 7 and refreshed the journal. This turn took 2m 21s. A separate
  read/unpack of the actual notebook verified exactly one new project and byte-for-
  byte preservation of the prior projects' journals and project index entries.
- [ChatGPT fresh-chat resume](https://chatgpt.com/c/6adb98ea-b8c4-83eb-aa18-2991b08492b6):
  given only the synthetic project name, recovered the decision, full open question
  and evidence from native storage. It reused project
  `p-75520ce7d9ceeee8aeaf5479e4c7cc07` and sitting
  `c-b3e2718eaeaa4788b17e645d5676db45`, created a new conversation session, and
  confirmed revision 8. It preserved deferred participation and empty demographics
  without re-asking; no results or duplicate discussion were created. The UI
  reports 2m 11s. Google Docs schema inspection in that host exposed complete
  document reads and `write_control.requiredRevisionId`; no Google document was
  read or changed during that check.
- [Corrected-role follow-up](https://claude.ai/chat/771085cf-b0ad-421c-838f-ccbeb32a4099):
  the installed supervisor asked what the pilot actually observed; the results
  role asked for the scale and independence without asserting a wider interval;
  journal club distinguished convenience recruitment from unknown allocation.
  The reproducibility role repeated its unsupported “I read the README” wording,
  which prompted the final source correction described above. No records or
  submissions were made in this response-only test.

### Runtime-to-connector checks

The packaged runtime ran in a fresh local process using the documents fetched
through the connected tools. This verifies the runtime/connector path, not plugin
discovery or tool availability in every AI app.

- Google Docs: the existing private synthetic notebook advanced from revision 7
  to 8 using one batch (setup, remembered deferral, and seven role starts/records).
  The exact old-state replacement used the observed Google revision guard and
  changed one occurrence. Fresh readback passed `native.confirm`. Reusing the
  stale Google revision was rejected with a revision mismatch. The readable
  journal matched the generated content, preserving its synthetic-test prefix;
  metadata still reported both documents unshared.
- ChatGPT Pages: the existing synthetic notebook advanced from revision 5 to 6
  with the equivalent batch. A guarded block edit, fetched readback and fresh
  `native.confirm` passed. Another fresh read-only process restored all seven open
  roles, the friendly title, deferred participation and all sharing off without
  changing the snapshot. The readable journal matched the generated content after
  normalising block whitespace, preserving its introductory test note.
- The readable journal intentionally shows the five most recent research records;
  older records remain in the validated notebook. Seven open role discussions
  were visible. Existing decisions and unresolved questions remained present.

## In-app submission evidence

Evidence: [Claude feedback acceptance conversation](https://claude.ai/chat/88bf55da-b22f-41c4-8d73-cca9ae20bf20).
The test used the installed bundled runtime in disposable session storage, with
all six endpoint settings directed to the temporary synthetic receiver. Its
sending code is unchanged in the rebuilt archive.

The preview contained `benchside.feedback.v1`, Benchside version, a generated
feedback ID, role, host, surface, ease, repeat-use intent and a clearly synthetic
comment. It contained neither research text nor an installation ID. The runtime
displayed the exact bytes, destination and SHA-256 and stopped before approval.

After approval, the first send and one identical retry returned
`submission_unavailable`. Expanded command outputs show the gateway's 403 refusal,
not a stored receipt. Turning feedback off succeeded; the same approved send then
returned `ConsentRequiredError` without another gateway connection. Final history
was empty, all sharing/metascience choices were off and installation ID was null.
The original draft remained on disk but its consent grant was revoked.

The consent error code uses a class name while other codes use snake case; this
is a consistency issue, not evidence of a consent bypass. Failure counts remain
absent while usage reporting is off. No host networking controls were changed.
The temporary receiver was stopped after testing, and its local storage directory
was confirmed removed. The temporary URL is not a continuing service.

The [ChatGPT installed-plugin conversation](https://chatgpt.com/c/6adb97a6-8b64-83eb-80b6-df46e73987b5)
also tested feedback in a disposable store, leaving its native notebook and
preferences unchanged. All six endpoint settings targeted a newly started
synthetic receiver. The exact approved preview used feedback ID
`5000b4e14228425886506a09e6b77663` and SHA-256
`9bea358a84845fcf254117e87d999de912cc38f56e98b2d67cc393c7d49a25bc`;
the hash was independently checked against the displayed JSON. The first send
and one identical retry returned `submission_rejected` with HTTP 403. Withdrawal
then blocked the same send with `ConsentRequiredError` before the sink was called.
History remained empty, all sharing was off and the installation ID was null.

The receiver log contained only the four baseline feedback requests and its two
baseline feedback objects; none contained the ChatGPT feedback ID. The Worker
logged no 403 response and its source has no 403 response branch. This locates the
failure before the Worker, but does not distinguish an app gateway from a
Cloudflare edge restriction. Both cloud-app paths still need a successful staging
receipt. The second temporary receiver was stopped and its storage directory was
confirmed removed as well.

## Build checks and remaining access

- 215 Python tests passed on Python 3.14; lint and the seven compiled-role checks
  passed. The earlier 201-test baseline passed on Python 3.11 as well; the new
  cases have not been rerun on 3.11.
- All three rebuilt archives passed offline extraction/runtime smoke checks:
  seven roles saved/resumed/concluded across fresh processes, native restoration,
  private metascience state, batched setup, remembered choices, exact replay and
  rejection of a damaged dependency even with a populated cache.
- Claude manifest, app skill and portable/OpenAI plugin validation passed.
- The companion collector's earlier 37 tests and type check passed. Its code was
  not changed during these four follow-up checks.
- Both apps now have the batched review build installed. The later reproducibility
  wording and setup-guide clarification are in the newly rebuilt archives but not
  yet installed: automated upload still reports disabled file access, and further
  native picker attempts became unavailable. `/tmp/benchside-review-batch.zip`
  now contains that latest Claude archive. Do not claim this final small update was
  installed merely because the earlier build passed its installed tests.
- Will has created his Cloudflare login; the Science Works invitation from Ben is
  still pending. A login and GitHub Admin access do not grant Worker/R2 access.
  Staging provisioning, cloud-host reachability and new-route deployment remain.

Next checks: install the final small package update and retest the reproducibility
wording; reduce Claude setup latency; verify private sharing in the UI when the
host cannot expose it; connect and test Google from both apps if that route is to
be offered; and run approved synthetic submissions against reachable staging from
both hosts. Keep the public study catalog empty until a reviewed study and
data-handling process are ready.
