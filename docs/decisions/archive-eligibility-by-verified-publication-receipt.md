# ADR:archive-eligibility-by-verified-publication-receipt — Archive Eligibility by Verified Publication Receipt

- **Decision ID:** ADR:archive-eligibility-by-verified-publication-receipt
- **Status:** Accepted
- **Date:** 2026-09-18
- **Deciders:** the operator (programme amendment accepted 2026-09-17); archive maintainers (mechanism)
- **Campaign:** `ARTICLES-RECEIPT-GATED-ELIGIBILITY-A` — tracked in #423, follow-on to #388

## Context

The archive admits a source record when its editorial select `FAIM Status` reads
`Posted` (`tools/ingest_airtable.py`, `ALLOWED_STATUSES`). That select is stamped by
several channel automations for their own purposes; it is not the act of
publication. A counts-only census of the source table on 2026-09-18 (947 rows)
showed how far the two have drifted:

| Fact | Rows |
|---|---|
| `FAIM Status = Posted` (the current gate) | 883 |
| Published on the Hashnode publication and **not** `Posted` (`Draft` 16, `Ready` 30, empty 5, `Error` 5) | **56** |
| …of which archived by no writer at all | **36** |
| `Posted` and **not** published on Hashnode (`todo` 22, `error` 13) | 35 |
| …of which carry no usable canonical URL | 4 |
| Rows carrying a Hashnode post id (24-hex) | 903 |

The gate is wrong in both directions: it hides live articles behind a workflow
label, and it admits records whose only evidence of publication is that label.
Green CI proved nothing about either.

Three further facts shape the mechanism:

1. **Hashnode is the syndication hub.** Every source (newsletter, Medium,
   LinkedIn-first pieces) is cross-posted to the Hashnode publication, and the
   source table records the resulting post id (`hashnode_post_id`) and state
   (`hashnode` ∈ `todo | published | error`). A receipt keyed on that id covers
   903 of 947 rows.
2. **Hashnode's GraphQL API is paid.** Since 2026-05-13 every request, reads
   included, requires a Pro plan on the publication
   ([changelog](https://hashnode.com/announcements/graphql-api)). A read-back
   "by post id via the API" is therefore a financial commitment, not a free
   instrument. The publication's **public surfaces** remain free: the sitemap
   index (every published post URL with `lastmod`, ~20 pages), the RSS feed
   (latest 20 only) and the post pages themselves, which embed the post's id and
   declare `<link rel="canonical">` pointing at the original source URL.
3. **Canonical URLs drift.** The newsletter platform serves a post under both its
   original and a later-renamed slug; the Hashnode page's canonical link then
   names the new slug while the source table's `GUID` names the old one. The
   reconciler already anticipates this drift. A receipt must therefore be
   decided by the **post id**, with the canonical comparison recorded as a
   signal, not used as a gate.

A second writer also exists — an external automation that marks rows
`github_published` and has written rows the repository's own gate rejects
(23 `Ready` rows, 106 rows without a URL-shaped `GUID`). Its retirement is
owned elsewhere; this decision must not depend on its marker.

## Decision

Archive eligibility becomes:

```text
eligible(record) =
      schema_valid(record)
  AND NOT explicitly_excluded(record)
  AND verified_receipt(record) ∈ {HASHNODE_POST, OWNED_SOURCE_URL}
```

`FAIM Status` becomes **advisory**: it is logged as `editorial_status` in every
classification and never decides admission.

### Receipt kinds

**R1 — `HASHNODE_POST` (primary).** All of:

- `hashnode = published` and `hashnode_post_id` matches `^[0-9a-f]{24}$`;
- the post URL is resolved without the paid API: the publication sitemap is
  fetched once per run and candidates are the sitemap URLs whose slug starts
  with the record's slug stem (the Hashnode slug may carry a suffix);
- the candidate page returns `200` and **embeds the record's post id** (hard
  condition);
- `canonical_match` is recorded as `true | false` by comparing the page's
  `<link rel="canonical">` with the normalized `GUID`. `false` is a
  `CANONICAL_DRIFT` signal for the reconciler, not a rejection.

**R2 — `OWNED_SOURCE_URL` (fallback, only when R1 is unavailable).** All of:

- `GUID` is an `https` URL whose host is in `OWNED_SOURCE_HOSTS` — the
  first-party properties (`www.firstaimovers.com`, `insights.firstaimovers.com`,
  `voices.firstaimovers.com`, `radar.firstaimovers.com`). Third-party hosts that
  block automated reads are **not** in the set; a row on such a host needs R1;
- the URL returns `200` and its page canonical (`<link rel="canonical">` or
  `og:url`) normalizes to the same URL.

**No receipt → not eligible.** A row is never archived on a status label alone.
Network failures (`429`, `5xx`, timeouts) classify the row as
`RECEIPT_UNVERIFIABLE`: counted, logged, retried next run, never treated as a
receipt and never as a rejection.

### Explicit exclusion and rights

An editorial decision to keep a live article out of the archive is expressed by
a dedicated checkbox `archive_exclude` on the source table, never by the
editorial status select. Creating that field is a change to the source of truth
and is the operator's; until it exists the gate has no exclusion path, which is
today's behaviour for `Posted` rows. Rights are an eligibility input through the
mapped `License` field: values in a configurable deny-set are ineligible (the
set ships empty; no row changes class by this decision alone).

### Recorded receipt

A created article's `metadata.json` gains an optional block, so the archive can
answer "why is this here?" without re-reading the source:

```json
"publication_receipt": {
  "kind": "HASHNODE_POST",
  "post_id": "<24-hex>",
  "url": "https://radar.firstaimovers.com/<slug>",
  "canonical_match": true,
  "verified_at": "2026-09-18T11:02:00Z"
}
```

### Read budget and determinism

- Sitemap: ≤ 21 requests per run, cached in-run. Post pages: **one request per
  candidate** (new or missing record), never per row of the table. The weekly
  reconciler classifies presence from the sitemap and confirms only
  `eligible_missing` candidates page-by-page.
- Browser-like `User-Agent`, ≤ 1 request/s, bounded retries with backoff. Public
  pages only; no credential is sent to any publisher.
- Selection order and batch caps are unchanged (`--max-created`,
  `--backfill-oldest`, hard batch cap of 5 in the recovery tool).

### Cut-over control

A single switch `ARCHIVE_ELIGIBILITY_GATE = receipt | status` (repository
variable, default `receipt` once the validation below has passed) selects the
gate in all three tools. `status` is the rollback position; it is never a
fallback taken silently.

## Alternatives considered

### Read back by post id through the Hashnode GraphQL API
- **Pros:** exact id lookup, no slug resolution, structured `publishedAt` / `canonicalUrl` fields.
- **Cons:** requires a paid Pro plan on the publication since 2026-05-13; a token becomes a workflow secret.
- **Rejected because:** it turns a free public read into a recurring financial commitment that is the operator's to make, and the receipt schema above does not need it — it remains the upgrade path if sitemap resolution proves brittle.

### Keep the `Posted` gate and sweep manually
- **Pros:** no code change; no outbound requests.
- **Cons:** gates on the wrong fact (56 live rows hidden, 35 admitted on a label); every miss needs a human to notice.
- **Rejected because:** the archive's own contract cannot be checked against a mutable workflow label.

### Trust the external writer's `github_published` marker
- **Pros:** already present on 824 rows.
- **Cons:** it is the marker of a second writer slated for retirement and has admitted rows the repository's validation rejects.
- **Rejected because:** eligibility must not depend on a writer the archive is removing.

### RSS feed only
- **Pros:** one request, structured items.
- **Cons:** exposes the latest 20 posts only.
- **Rejected because:** the backlog is older than the feed window.

## Consequences

### Positive
- The archive's contract ("all First AI Movers articles") becomes checkable: ~36 live articles become eligible and are drained through the existing bounded recovery tool.
- A status flip on a live post no longer silently removes it from eligibility.
- Every archived article carries evidence of publication that a reader can verify on a public page.
- No paid API, no new secret, no new writer, no new reconciler.

### Negative
- Ingestion and reconciliation now make outbound HTTP requests to the publication and first-party properties; a platform outage degrades a run to `RECEIPT_UNVERIFIABLE` counts instead of a clean green.
- Rows on third-party hosts that never gained a Hashnode receipt (13 `error` rows today) stay ineligible until their syndication is repaired upstream.
- Two receipt kinds are more code than one status comparison; the fixtures in Validation are the price of keeping it honest.

### Neutral
- The status gate survives behind the rollback switch; the archive stays append-only.

## NFR impact

| Dimension | Impact | Notes |
|---|---|---|
| Cost | ~ | none recurring; the paid API is explicitly not required |
| Latency | - | +≤ 21 sitemap requests and one page request per candidate per run — seconds inside the current daily run |
| Observability | + | counts gain `receipt_hashnode`, `receipt_source_url`, `receipt_unverifiable`, `canonical_drift`, `excluded`; each archived article records its receipt |
| Security | ~ | public reads only; no credential leaves the workflow; publisher rate limits respected by budget, not by retries |
| Scalability | + | one sitemap read scales with the publication; page reads scale with new work, not with the archive |
| Maintainability | + | one eligibility function shared by ingestion, reconciliation and recovery; the status gate survives only behind the rollback switch |

## Validation

Acceptance requires, before the default switches to `receipt`:

1. **Read-only delta.** `audit_airtable_reconciliation.py` run under the `receipt`
   gate on a branch against the live source explains every change of class
   row-by-row against the `status` gate: expected ≈ +36 newly eligible,
   **0 false-eligible** (every newly eligible row has an id-verified page),
   `receipt_unverifiable` enumerated, no Airtable write, no PR, no publication.
2. **Fixtures, no network in unit tests.** Recorded sitemap and page fixtures
   for: id present + canonical match; id present + canonical drift; page `200`
   without the id (must reject); `404`; `429`; slug-suffix resolution; R2 on an
   owned host; R2 refused on a non-owned host; `archive_exclude` honoured;
   `License` deny-set honoured.
3. **Negative controls.** Each new guard is broken separately and observed
   failing its test with a fresh bytecode cache; a guard never seen failing
   proves nothing.
4. **Tool parity.** `ingest_airtable.py`, `audit_airtable_reconciliation.py` and
   `recover_airtable_backlog.py` classify a fixture set identically under both
   gates.
5. **Dry-run proof in CI.** One `recover-airtable-backlog.yml` run with
   `apply=false` under `ARCHIVE_ELIGIBILITY_GATE=receipt` reports the new backlog
   counts without creating anything.
6. **Drain.** Backlog batches of ≤ 5 through the existing recovery workflow, each
   PR reviewed on its diff and CI; `llms.txt` / `index.json` regenerated from the
   reconciled set.

## Rollback

Set `ARCHIVE_ELIGIBILITY_GATE=status`; every tool returns to the `Posted`
comparison on its next run. Archive content is append-only — nothing created
under the receipt gate is deleted by a rollback, and each such article carries
its receipt. Reverting the code change itself is a normal PR; the recorded
`publication_receipt` block is optional in the metadata schema and tolerated by
the previous readers.

## Related

- Runbooks: [`docs/airtable-ingestion.md`](../airtable-ingestion.md), [`docs/OPERATIONS.md`](../OPERATIONS.md) (Airtable ingestion, backlog recovery).
- Issues: #423 (owner), #388 (credential restoration and receipt), #369 (reconciler discrepancy signal).
- Identity: `NS:articles:decision-record` in `identifier-namespaces.yaml` — semantic slug, no number allocated.
