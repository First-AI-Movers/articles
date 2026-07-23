# www.firstaimovers.com Migration — SEO Pre-Flight Checklist

Launch checklist for moving `www.firstaimovers.com` from **Beehiiv** to **WordPress on Hetzner**, covering the surfaces named in [`ROADMAP.md`](../ROADMAP.md) N4: robots.txt, sitemap, Cloudflare bot allowlisting, IndexNow, and canonical redirects.

**This document does not authorize, schedule, or perform the migration.** The migration's blocker is recorded as "Owner timeline" in [`docs/ROADMAP_CLOSEOUT_TRACKS.md`](ROADMAP_CLOSEOUT_TRACKS.md). This is the written pre-flight that has to exist *before* a cutover date is picked, not a claim that one has been picked.

Sibling document: [`docs/search-visibility-monitoring.md`](search-visibility-monitoring.md) — the ongoing weekly/monthly monitoring process for `articles.firstaimovers.com`. This checklist is one-shot and migration-scoped; that one is recurring.

---

## 1. Scope — and why an *archive* repository owns this checklist

`www.firstaimovers.com` is a **different property** from this archive. This repository publishes `articles.firstaimovers.com` (see `CNAME`), which is **not** migrating. [`docs/MULTI_PROPERTY_PATTERN.md`](MULTI_PROPERTY_PATTERN.md) is explicit that each property keeps its own repository, domain, sitemap, Search Console property, and canonical policy — so nothing here proposes merging the two.

The archive nevertheless carries a hard, measurable dependency on www's URL structure.

### Measured on `main` at `c08b8a52` (2026-07-23)

| Measurement | Value | Source of truth |
|---|---|---|
| Published articles whose `canonical_url` is on `www.firstaimovers.com` | **306** | `articles/*/metadata.json` |
| URL shape of all 306 | **`/p/<slug>`** — the Beehiiv path form | `articles/*/metadata.json` |
| Citation-graph nodes canonical to www | **306** of 829 | `citation_graph.json` |
| Citation-graph edges in the corpus | 1245 | `citation_graph.json` → `stats` |
| English article pages | `noindex, follow`, with `rel=canonical` pointing at the **external** `canonical_url` | `templates/article.html.j2` (robots + canonical blocks) |
| `www.firstaimovers.com` in the sitemap ownership allowlist | yes | `tools/rebuild_local.py` → `CANONICAL_ALLOWED_HOSTS` |
| Bing crawlability of www today | **403 to Bingbot** (Googlebot 200) | [`docs/search-visibility-monitoring.md`](search-visibility-monitoring.md) §9, `ROADMAP.md` |

Two repository invariants turn those numbers into an obligation:

- [`CONTRIBUTING.md`](../CONTRIBUTING.md) archive invariant 2 — **"Canonical URLs are permanent … must never change."** The archive cannot rewrite the 306 URLs to match a new structure.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) archive invariant 1 — article text is immutable once published.

So: 306 archive pages are `noindex` and delegate their indexation authority, by `rel=canonical`, to `https://www.firstaimovers.com/p/<slug>`. If those paths stop resolving after the migration, the archive is left pointing 306 canonicals at dead URLs and cannot fix it from this side. **Preserving the `/p/<slug>` path space — or 301-redirecting it — is the single non-negotiable item in this checklist.**

Everything else here is a normal migration hygiene item. Section 3 is the one that can silently damage this repository.

---

## 2. Phase 0 — before the cutover: freeze and capture the baseline

Do this while the **old** site is still live. Every later verification compares against it.

- [ ] Record the cutover date and the responsible owner.
- [ ] Capture the current live bot-response baseline for all three properties, using the exact commands in [`docs/search-visibility-monitoring.md`](search-visibility-monitoring.md) §7 ("Bot access checks"). Record the status codes; the known-current values are www **403** to Bingbot / **200** to Googlebot, and radar **429** to both.
- [ ] Export the current www URL inventory from the Beehiiv side (all published post paths), not just the 306 the archive knows about. The archive's 306 is a **lower bound** on what must keep resolving — it only counts posts that were archived here.
- [ ] Regenerate the archive's own derived list of required-to-survive URLs and keep it with the migration record:

```bash
# From the repository root. Writes every www URL this archive declares canonical
# to urls.txt — §8 consumes that exact file after cutover. Keep it with the
# migration record; do not commit it (it is a working file, not an artifact).
python3 - > urls.txt <<'PY'
import glob, json
from urllib.parse import urlparse
for p in sorted(glob.glob('articles/*/metadata.json')):
    u = json.load(open(p)).get('canonical_url') or ''
    if urlparse(u).netloc == 'www.firstaimovers.com':
        print(u)
PY
printf 'Required www URLs: %s\n' "$(wc -l < urls.txt)"
```

- [ ] Record the current Google Search Console and Bing Webmaster indexed counts for the www property, so post-migration recovery can be measured rather than asserted.
- [ ] Confirm nothing in this repository needs to change at cutover. Under the invariants above the answer should be **no** — the archive's `canonical_url` values stay exactly as they are. If someone concludes otherwise, that is a `CONTRIBUTING.md` invariant change and belongs in its own reviewed PR, not in a migration runbook.

---

## 3. Phase 1 — URL and redirect map (**blocking**)

- [ ] Decide the WordPress permalink structure **before** content import. None of the stock permalink presets — "Post name" (`/<slug>/`), "Day and name" (`/YYYY/MM/DD/<slug>/`), "Month and name" (`/YYYY/MM/<slug>/`) — matches the Beehiiv `/p/<slug>` shape that all 306 archived canonicals use. A custom structure is required to preserve it.
- [ ] Either (a) configure the permalink structure as `/p/%postname%/` so the existing paths survive unchanged, **or** (b) publish a permanent **301** from `/p/<slug>` to the new path for every URL in the Phase-0 inventory. Option (a) is lower risk: it needs no redirect table to be maintained, and it cannot drift.
- [ ] If redirecting, use **301** (permanent), not 302 — a temporary redirect does not transfer indexing signals, and these URLs are the canonical targets of `noindex` pages.
- [ ] Verify the redirect map is **total** over the Phase-0 inventory. A partial map is the failure mode that is easy to miss: the archive has 306 entries and the Beehiiv export may have more.
- [ ] Confirm redirects are server-side (WordPress/nginx/Cloudflare), not JavaScript. Crawlers resolving a `rel=canonical` target do not execute client-side redirects reliably.
- [ ] Check for redirect chains and loops — each hop loses signal, and Cloudflare rules plus WordPress rules can stack unintentionally.
- [ ] Preserve HTTPS and the `www.` host. A migration that lands on the apex `firstaimovers.com` changes the canonical host for all 306 URLs, which is the same failure as changing the path. Both `firstaimovers.com` and `www.firstaimovers.com` are in `CANONICAL_ALLOWED_HOSTS` (`tools/rebuild_local.py`), but the archive's stored canonicals name **`www.`** specifically.

---

## 4. Phase 2 — robots.txt on the new host

The archive's own `robots.txt` is a useful reference model: it explicitly `Allow`s Googlebot, Bingbot, and a long list of AI/LLM agents, and declares a `Sitemap:` line. Beehiiv does not expose that level of control; WordPress/Hetzner does.

- [ ] Publish a `robots.txt` at `https://www.firstaimovers.com/robots.txt`.
- [ ] Explicitly `Allow` **Googlebot** and **Bingbot**. Bingbot is the one currently being refused — see §6.
- [ ] Decide the AI/LLM crawler stance for www deliberately. The archive's stance is documented in [`docs/AI_TRAINING_POLICY.md`](AI_TRAINING_POLICY.md) and expressed in its `robots.txt`; www is a separate property and may legitimately choose differently. Record the decision either way — an unstated default is the thing that causes surprise later.
- [ ] Add the `Sitemap:` directive pointing at the new www sitemap (§5).
- [ ] Confirm no `Disallow: /` survives from a staging configuration. This is the single most common migration regression: staging sites are routinely built with a blanket disallow, and it ships to production.
- [ ] Confirm no `noindex` meta tag or `X-Robots-Tag: noindex` header is emitted site-wide by the staging setup.

---

## 5. Phase 3 — sitemap on the new host

- [ ] Publish a sitemap for www (WordPress core generates `/wp-sitemap.xml`; SEO plugins commonly use `/sitemap_index.xml`). Pick one and make the other 404 rather than serving both.
- [ ] Submit it in Google Search Console and Bing Webmaster Tools for the **www property** — a separate property from `articles.firstaimovers.com`, per [`docs/MULTI_PROPERTY_PATTERN.md`](MULTI_PROPERTY_PATTERN.md) ("Search Console / Bing isolation").
- [ ] Confirm the www sitemap contains **only** www URLs. Do not list `articles.firstaimovers.com` URLs in it. The archive applies the mirror-image rule to itself — [`docs/search-visibility-monitoring.md`](search-visibility-monitoring.md) §3 checks that no cross-host URL appears in the archive sitemap, and §6 escalates a cross-host entry as a repo defect.
- [ ] Do **not** add www URLs to this repository's `sitemap.xml`. It is a generated artifact rebuilt by `tools/rebuild_local.py` and must never be hand-edited ([`CONTRIBUTING.md`](../CONTRIBUTING.md) invariant 3); it deliberately advertises only first-party indexable pages on `articles.firstaimovers.com`.

---

## 6. Phase 4 — Cloudflare / WAF bot allowlisting (remediation path for the recorded defect)

This is the item that makes the migration worth doing from the archive's point of view. Note the tense: this section **documents the steps** that would resolve the Bingbot 403. The defect stays open, and the "Allowlist Bingbot on www" row in [`docs/search-visibility-monitoring.md`](search-visibility-monitoring.md) §8 stays paused, until the migration runs and §10 confirms a 200.

**Recorded baseline:** during the Search Visibility Sprint, `www.firstaimovers.com` returned **403 to Bingbot** while Googlebot received 200. Beehiiv exposes no low-level WAF rules, so the defect is unfixable on the current host. Sources: [`docs/search-visibility-monitoring.md`](search-visibility-monitoring.md) §9 and §8 (the "Allowlist Bingbot on www" row, status "Paused — external platform"), and `ROADMAP.md`.

- [ ] On the new stack, allowlist **Bingbot** explicitly in the Cloudflare WAF / bot-management rules.
- [ ] Allowlist **Googlebot** explicitly rather than relying on a default; a managed bot-fight or under-attack mode can refuse verified crawlers.
- [ ] Verify by reverse DNS or Cloudflare's verified-bot category rather than by user-agent string alone — user-agent allowlisting is trivially spoofable and is not a security control.
- [ ] Re-run the §7 bot-access checks from [`docs/search-visibility-monitoring.md`](search-visibility-monitoring.md) against the new host and confirm **200** for both Googlebot and Bingbot on www.
- [ ] Update the "Allowlist Bingbot on www" row in [`docs/search-visibility-monitoring.md`](search-visibility-monitoring.md) §8 from "Paused — external platform" to its resolved state, and update the www paragraph in §9. Update `ROADMAP.md` in the same PR.
- [ ] Note that `radar.firstaimovers.com` (Hashnode, 429 to both crawlers) is a **separate** parked item and is not resolved by this migration.

---

## 7. Phase 5 — IndexNow for www

The archive already runs IndexNow for `articles.firstaimovers.com`: a key file generated from the `INDEXNOW_API_KEY_ARTICLES_FAIM` environment variable, submitted by `tools/submit_indexnow.py`, with CI running `--dry-run` after deploy. See [`docs/search-visibility-monitoring.md`](search-visibility-monitoring.md) §2 and §7.

- [ ] Treat www as a **separate IndexNow property with its own key**. Do not reuse `INDEXNOW_API_KEY_ARTICLES_FAIM`; a key is bound to the host that serves its key file, and reuse across properties breaks verification.
- [ ] Host the www key file at the www root and confirm it returns the exact key as its body.
- [ ] Validate the key in Bing Webmaster Tools for the www property.
- [ ] Submit the migrated URL set once after cutover, so Bing re-crawls the redirects promptly rather than waiting for organic discovery.
- [ ] Do not wire www submissions into this repository's tooling. `tools/` is a deploy-triggering path here and www is a separate property; keep the two pipelines independent per [`docs/MULTI_PROPERTY_PATTERN.md`](MULTI_PROPERTY_PATTERN.md).

---

## 8. Phase 6 — canonical and cross-property integrity

- [ ] Confirm each migrated www post emits `rel=canonical` pointing at **itself** on www. It is the canonical publisher for those 306 articles; the archive copies are deliberately `noindex, follow` and point *at* it (`templates/article.html.j2`).
- [ ] Do **not** set a canonical from www to `articles.firstaimovers.com`. That would invert the established relationship and orphan both copies — the archive pages are `noindex`, so a mutual hand-off leaves nothing indexable.
- [ ] Verify the archive's stored canonicals still resolve after cutover, using the Phase-0 inventory. This is the single check that proves §3 worked:

```bash
# Consumes urls.txt from Phase 0 (§2). Follows redirects, so a 301 that lands on
# 200 reports 200. Any 404 is a blocker. Prints only the failures.
UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
while read -r u; do
  code=$(curl -s -o /dev/null -w '%{http_code}' -L -A "$UA" "$u")
  [ "$code" = "200" ] || printf '%s %s\n' "$code" "$u"
done < urls.txt
echo "checked $(wc -l < urls.txt) URLs — any lines above are failures"
```

> **Set a realistic user agent, and re-run per crawler.** Measured 2026-07-23 against the *current* Beehiiv host: a default-user-agent `curl` receives **403** for these URLs. A run without `-A` would therefore report every URL as failing regardless of whether the migration succeeded. After cutover, run this loop once with a browser user agent (above) and again with the Googlebot and Bingbot user agents from [`docs/search-visibility-monitoring.md`](search-visibility-monitoring.md) §7 — the crawler runs are what prove §6.

- [ ] Re-check the citation graph after cutover. `citation_graph.json` matches link targets by canonical-URL prefix, by local archive URL, and by slug for "Beehiiv `/p/<slug>` paths and similar patterns" — see [`docs/CITATION_GRAPH.md`](CITATION_GRAPH.md). A www path change therefore affects graph edge resolution, and `www.firstaimovers.com` is one of the hosts whose links count as edges.
- [ ] If the path shape changes despite §3, raise it as a repository issue **before** regenerating `citation_graph.json`. The file is a generated artifact ([`CONTRIBUTING.md`](../CONTRIBUTING.md) invariant 3); a silent edge-count drop on the next rebuild would be the first visible symptom, long after the cause.
- [ ] Leave `CANONICAL_ALLOWED_HOSTS` in `tools/rebuild_local.py` unchanged unless the canonical **host** actually changes. It governs which canonicals the archive is willing to advertise as its own.

---

## 9. Phase 7 — Search Console and Bing property handling

- [ ] Keep www and `articles.firstaimovers.com` as **separate** properties in both Google Search Console and Bing Webmaster Tools ([`docs/MULTI_PROPERTY_PATTERN.md`](MULTI_PROPERTY_PATTERN.md)).
- [ ] Re-verify ownership of the www property on the new host — verification methods tied to the old platform (DNS TXT is portable; an HTML file or platform meta tag may not be) can silently lapse.
- [ ] Do **not** use Google's Change of Address tool unless the **domain** changes. It is for domain moves, not host or platform moves. If the hostname is unchanged, there is nothing to file.
- [ ] Submit the new sitemap (§5) in both consoles.
- [ ] Watch the www property's index coverage for 2–4 weeks post-cutover and record it. This mirrors the cadence already used for the archive in [`docs/search-visibility-monitoring.md`](search-visibility-monitoring.md) §3–§4.

---

## 10. Phase 8 — post-cutover verification

Run all of these and record the results with the migration record. Nothing here needs credentials except the console checks in §9.

- [ ] Every URL in the Phase-0 inventory returns 200 or a single 301 landing on 200. **Zero 404s.**
- [ ] `https://www.firstaimovers.com/robots.txt` is present, allows Googlebot and Bingbot, and contains no leftover `Disallow: /`.
- [ ] The www sitemap is reachable, contains only www URLs, and is accepted by both consoles.
- [ ] Bot-access checks from [`docs/search-visibility-monitoring.md`](search-visibility-monitoring.md) §7 return **200** for Googlebot **and** Bingbot on www.
- [ ] The www IndexNow key file resolves and is validated in Bing.
- [ ] A sample of migrated posts emits self-referential `rel=canonical` on www.
- [ ] This repository's own checks are unaffected — run the archive's existing sitemap-health block from [`docs/search-visibility-monitoring.md`](search-visibility-monitoring.md) §7 and confirm no cross-host URL has entered `sitemap.xml`.
- [ ] `git status` in this repository is clean. **A correctly executed www migration requires zero commits here.** If this repository changed, something in §3 or §8 went differently than planned — find out what before proceeding.

---

## 11. Rollback

- [ ] Keep the Beehiiv property live, or its DNS reversible, until Phase 8 passes in full.
- [ ] Rollback is a DNS revert plus restoring the previous host — it is not a repository operation. Nothing in this archive changes during the migration, so there is nothing here to revert.
- [ ] If rollback happens after crawlers have seen new 301s, expect a re-crawl lag. Re-submit the sitemap and re-run IndexNow for www after reverting.

---

## 12. Owner-side actions

These need account access and cannot be performed by repository tooling, matching the split already used in [`docs/search-visibility-monitoring.md`](search-visibility-monitoring.md) §8:

| Action | Tool | Owner |
|---|---|---|
| Choose the cutover date | — | Owner |
| Export the full Beehiiv URL inventory | Beehiiv | Owner |
| Configure permalinks / redirects | WordPress + Hetzner | Owner |
| Configure WAF bot allowlist | Cloudflare | Owner |
| Re-verify the www property | GSC + Bing Webmaster | Owner |
| Create and validate the www IndexNow key | Bing Webmaster | Owner |
| Record post-cutover index coverage | GSC + Bing Webmaster | Owner |

---

## 13. What this checklist does not claim

- It does **not** claim an SEO outcome. No migration has taken place; nothing here has been executed or verified against a live WordPress/Hetzner host.
- It does **not** set a migration date. The blocker remains "Owner timeline" ([`docs/ROADMAP_CLOSEOUT_TRACKS.md`](ROADMAP_CLOSEOUT_TRACKS.md)).
- It does **not** assert the current www URL inventory. The 306 figure counts only posts archived in this repository and is a lower bound on what must keep resolving; Phase 0 exists to get the true number from the platform.
- It does **not** cover the `radar.firstaimovers.com` / Hashnode 429 defect, which is separately parked ([`docs/search-visibility-monitoring.md`](search-visibility-monitoring.md) §9).
- It does **not** cover non-SEO migration concerns — content fidelity, subscriber/email list continuity, analytics continuity, or billing.

## 14. Retirement condition

This document is migration-scoped and should be retired, not maintained indefinitely. When the migration completes and Phase 8 passes, fold the durable outcome into [`docs/search-visibility-monitoring.md`](search-visibility-monitoring.md) — resolve its §8 "Allowlist Bingbot on www" row and its §9 www paragraph — and move the N4 entry to [`docs/ROADMAP_HISTORY.md`](ROADMAP_HISTORY.md). If the migration is abandoned, retire this file in the same PR that records that decision.

---

*Created 2026-07-23 against `main` `c08b8a52`, for `ROADMAP.md` N4. Not executed — see §13.*
