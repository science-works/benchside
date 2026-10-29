# Test the receiver and check deployment access

Private research memory and metascience submissions are separate. An existing
project restores from the folder or private notebook chosen during setup. The
Science Works receiver never supplies project memory and never receives the
private notebook wholesale.

## What the browser response means

Opening `https://ingest.benchside.science.works` in a browser sends a GET request
for `/`. The original Worker replies that its supported operation is
`POST /v1/gaps`. That response is expected: the address is an HTTPS API, not a
web page or upload form. It establishes that the original program answered that
browser. It does not prove a submitted object was stored or that the new routes
have been deployed.

Every production package uses this same receiver. The review build adds separate
paths for feedback, usage, surveys and activity, plus a read-only study catalog.
Those central changes and their storage must be deployed before use. Scientists
do not need Cloudflare accounts or API keys to send approved contributions.

## Test without Science Works access

With the companion `benchside-ingest` review branch and its Node dependencies
installed, run from the Benchside repository:

```bash
uv run --frozen python scripts/test_endpoints.py
```

The helper copies the current receiving program into a temporary directory,
creates independent local storage and sends synthetic examples to all five
submission routes. It verifies storage receipts, exact duplicate retries,
catalog retrieval, forbidden transcript rejection and consent withdrawal. It
removes the server and storage afterwards. It copies no production configuration,
account IDs, routes or cloud buckets. This passed on 23 October 2026, including
usage with optional demographic fields.

For testing from another app, the helper can expose that isolated local service
through a temporary HTTPS address. Install Cloudflare's official `cloudflared`
tool first, then run:

```bash
uv run --frozen python scripts/test_endpoints.py --public --keep-alive-seconds 1800
```

It first verifies that the public address serves this exact synthetic catalog,
then sends synthetic requests over HTTPS and verifies receipts. Only after those
checks does it print `TEMPORARY_HTTPS_ENDPOINT`. The receiver stays up for 30
minutes or until stopped. Anyone with the URL can reach it: use synthetic test
data only. All storage remains temporary on the developer's computer, and normal
package destinations are unchanged. A failed DNS lookup or tunnel check is not
a successful public endpoint test. This is a development option, not staging
deployment or a service for participants. See [Cloudflare Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).

On 23 October 2026 this HTTPS check passed all five routes, including exact-retry
receipts. The first attempts hit DNS resolution failures; the final attempt
allowed the new name to propagate. This does not establish deployment or R2
permissions in Science Works' account.

A subsequent installed-plugin test in Claude reached the preview/approval stage,
but Claude's execution gateway refused the temporary domain with HTTP 403 before
the receiver could answer. Two sends returned `submission_unavailable` and kept
the same draft pending. After feedback consent was withdrawn, the same send was
rejected before any further connection attempt. Submission history stayed empty.
An installed ChatGPT test against a fresh temporary receiver also returned HTTP
403 for the first send and identical retry. Receiver logs and stored objects
confirmed neither request reached the Worker; they do not identify whether the
app gateway or Cloudflare edge blocked it. Consent withdrawal blocked the next
send before networking, and no receipt was recorded. Both temporary receivers
were stopped and their synthetic storage directories removed.
See the [acceptance report](acceptance-2026-10-23.md). Local HTTPS success does not
establish that a cloud app permits that destination. Test the approved staging
address from each intended host; do not bypass host network controls.

To test a packaged client against that verified temporary address, the testing
agent may set the per-channel `BENCHSIDE_GAPS_ENDPOINT`,
`BENCHSIDE_FEEDBACK_ENDPOINT`, `BENCHSIDE_USAGE_ENDPOINT`,
`BENCHSIDE_SURVEYS_ENDPOINT`, and `BENCHSIDE_ACTIVITY_ENDPOINT` to the matching
`https://.../v1/<channel>` routes in a disposable test environment. Use
`BENCHSIDE_STUDIES_ENDPOINT` for `/v1/studies`. Keep the native/private test notebook
separate from real projects. The normal preview and exact-content approval still
apply; endpoint overrides do not grant consent. Do not rewrite release defaults.

## Access to check or request

Will has created a Cloudflare account with his Science Works email and is waiting
for Ben to invite it to Science Works. Creating the login does not itself grant
access to the organisation's Worker or storage. No account is needed to use the
public submission API or the local/temporary HTTPS tests. Ben can alternatively
deploy staging and provide its URL.

For Will's preferred direct-maintenance route, use his Science Works email for
the login and ask Ben to invite it to the existing Science Works account. Keep
the Worker, domain and storage owned by that organisation. GitHub separately
reports that Will already has Admin access to `science-works/benchside-ingest`;
repository access does not itself grant Cloudflare deployment permissions.

Once invited, sign in at [Cloudflare](https://dash.cloudflare.com/), select Science
Works, and inspect membership and the Benchside Worker. A successful local
`wrangler login` followed by `wrangler whoami` is another way to identify accessible
accounts; never paste its tokens into chat. Cloudflare currently requires an
account-owned API token for granular Wrangler authorization; OAuth login does
not support those granular roles. Agree the supported deployment authentication
with Ben and exchange any credentials through an appropriate secure route.

For staging work, request permission to:

- Deploy/edit the Benchside staging Worker.
- Create and bind separate staging R2 buckets for gaps, feedback, usage, surveys
  and activity, or have Ben create them and grant access to use them.
- Inspect synthetic receipts, staging objects and operational errors.
- Configure a route/custom domain only if you are responsible for that step.

Worker Editor/resource-scoped permissions or a suitable scoped deployment token
can be used; account-wide administrator access is not the default request. The
operator should scope R2 access to the staging resources where possible. Editing
an existing Worker and creating a new resource can require different grants.
Ben can create the staging Worker first and grant Editor access, or grant the
Workers product permissions needed to create it. Existing R2 bindings do not
require separate R2 permissions just to redeploy a Worker; creating buckets or
inspecting their contents does. Production uses a custom domain, which currently
does not support per-Worker roles, so Ben must account for that when choosing the
production grant. Route changes need the appropriate zone permissions too.
Cloudflare describes the current roles and limitations in its
[Workers authorization guide](https://developers.cloudflare.com/workers/authorization/)
and [Workers permissions](https://developers.cloudflare.com/workers/authorization/workers/).

Ben's original integration note said app developers did not need Science Works
Cloudflare access to submit. That is different from deploying new receiving
routes. Ask Ben to confirm membership and either grant the staging capabilities
above or deploy the reviewed collector changes for you. Production access and
release remain separate. Also ask him to inspect API-client blocking: earlier
read-only requests from this environment received Cloudflare 403/error 1010.

## Relationship to the wider Science Works backend

Ben's 20 October note describes a standalone receiving service: Benchside sends
approved JSON to a Cloudflare Worker, which stores the exact bytes in EU R2.
The original client change was an HTTP export sink; changes to collection limits,
schemas or authentication belonged in `science-works/benchside-ingest`.
It did not specify deployment into a main web app, shared database, account
system or dashboard. Wider usage collection was explicitly a future extension
requiring a revised schema/consent design.

The expanded build follows that service boundary with separate feedback, usage,
survey and activity routes and buckets. Updating this receiver is sufficient for
collection. Showing the findings inside another Science Works product would be
an additional reporting integration to agree with Ben, not something provisioned
by deploying this Worker. Private researcher notebooks remain outside ingestion.

## What arrives

The client sends UTF-8 JSON in an HTTPS POST with `Content-Type: application/json`.
The reviewed payload itself is stored as a `.json` object in the corresponding
R2 bucket. For example, a workflow observation uses the unchanged format:

```json
{
  "schema": "benchside.gaps.v1",
  "observations": [{
    "id": "o-1a2b3c4d",
    "gap": {
      "kind": "manual_toil",
      "task": "Manually reformatting software-generated tables",
      "frequency": "weekly"
    }
  }]
}
```

It has no project, installation or demographic identifiers. Each other channel
has its own strict schema. See the [complete synthetic usage example](../tests/fixtures/reporting/benchside-usage-demographics.json),
including optional categories, counts and standard failures. Demographic answers
are absent unless the researcher chose to include them in reviewed usage.

The storage path is `<channel>/v1/dt=YYYY-MM-DD/<payload-sha256>.json`. A successful
POST returns HTTP 201 and this receipt shape:

```json
{
  "status": "stored",
  "sha256": "<64-character SHA-256 of the exact submitted bytes>",
  "received_at": "<UTC timestamp>",
  "observations": 1
}
```

An exact retry on the same UTC day returns HTTP 200 with `status: "duplicate"`;
the aggregate report deduplicates cross-day repeats too. The client verifies the
receipt digest before marking a draft submitted. Invalid fields return 422 and
are not stored. The collector validates format, while free-text generalisation
and the researcher's review keep scientific details out of submissions.
