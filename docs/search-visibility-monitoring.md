# Search Visibility Monitoring

Operational checklist for tracking SEO, GEO, and AEO discovery of the First AI Movers article archive.

---

## 1. Purpose

This process ensures the archive remains discoverable by search engines and AI answer engines. It tracks whether sitemap changes, IndexNow submissions, and topic-hub SEO improvements translate into measurable indexation, impressions, clicks, and answer-engine citations.

**Why it matters:** A clean sitemap and strong topic hubs are worthless if crawlers cannot reach them or if indexation stalls. Weekly monitoring catches blockers early.

---

## 2. Current Search Architecture

| Component | State |
|---|---|
| **Sitemap** | `sitemap.xml` contains 80 indexable first-party HTML pages on `articles.firstaimovers.com`: homepage, about, topics index, 77 topic hubs |
| **Local article pages** | `/articles/<slug>/` are `noindex, follow` with external `rel=canonical`. Not in sitemap. |
| **Raw data / feeds** | `index.json`, `feed.xml`, `feed.json`, `llms.txt`, `llms-full.txt`, `llms-recent.txt` are accessible and linked in footer. Not in sitemap. |
| **IndexNow** | Key file live at `https://articles.firstaimovers.com/<key>.txt`, generated from env var `INDEXNOW_API_KEY_ARTICLES_FAIM`. `tools/submit_indexnow.py` supports dry-run and live submission. CI runs dry-run after deploy. |
| **Google** | Discovered via GSC + sitemap. No Google Indexing API (not eligible). |
| **Bing / Yandex** | Discovered via IndexNow + Bing Webmaster Tools sitemap. |
| **AI / LLM bots** | `robots.txt` explicitly allows GPTBot, ClaudeBot, PerplexityBot, Google-Extended, etc. |

---

## 3. Weekly Checklist

### Google Search Console

- [ ] Check sitemap status for `https://articles.firstaimovers.com/sitemap.xml`
- [ ] Record **discovered URL count**
- [ ] Record **indexed count**
- [ ] Record **not indexed count**
- [ ] Review top 3 not-indexed reasons (e.g., "Crawled — currently not indexed", "Discovered — currently not indexed", "Duplicate without user-selected canonical")
- [ ] Inspect sample URLs:
  - [ ] Homepage
  - [ ] Topics index
  - [ ] 3 topic hubs (pick high-volume ones)
- [ ] Record **impressions**, **clicks**, **CTR**, **average position** for the last 7 days

### Bing Webmaster Tools

- [ ] Confirm `articles.firstaimovers.com` property is verified
- [ ] Confirm sitemap is submitted
- [ ] Confirm IndexNow key is validated
- [ ] Record **indexed pages**
- [ ] Review crawl/index issues
- [ ] Run `tools/submit_indexnow.py --dry-run` locally; record output

### Bot Access

Run these curl checks and record status codes:

```bash
# Googlebot
curl -A "Googlebot/2.1 (+http://www.google.com/bot.html)" -I https://articles.firstaimovers.com/
curl -A "Googlebot/2.1 (+http://www.google.com/bot.html)" -I https://radar.firstaimovers.com/
curl -A "Googlebot/2.1 (+http://www.google.com/bot.html)" -I https://www.firstaimovers.com/

# Bingbot
curl -A "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)" -I https://articles.firstaimovers.com/
curl -A "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)" -I https://radar.firstaimovers.com/
curl -A "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)" -I https://www.firstaimovers.com/
```

- [ ] Flag any **403**, **429**, or **5xx** as blockers
- [ ] Radar (`radar.firstaimovers.com`) should not return 429 to Googlebot/Bingbot
- [ ] www (`www.firstaimovers.com`) should not return 403 to Bingbot

### Repo / Live Checks

```bash
# Sitemap count must be 80
grep -c '<url>' sitemap.xml

# No local article pages in sitemap
grep '/articles/' sitemap.xml || echo "OK"

# No cross-host URLs in sitemap
grep 'radar.firstaimovers.com' sitemap.xml || echo "OK"

# No raw data / feed URLs in sitemap
grep -E '\.md|\.txt|\.json|\.cff|feed\.xml|feed\.json' sitemap.xml || echo "OK"

# IndexNow dry-run returns 80 URLs
python3 tools/submit_indexnow.py --dry-run

# Key file is live and returns exact body (replace <key> with current env var value)
curl -sL https://articles.firstaimovers.com/<key>.txt
```

- [ ] All checks pass

---

## 4. Monthly Checklist

- [ ] Review query growth by topic hub (which topics are gaining impressions?)
- [ ] Identify topic hubs with impressions but low CTR — candidates for title/meta improvements
- [ ] Review discovered-not-indexed trend: is it declining?
- [ ] Review bot protection status for Radar and www (ask Vercel/Cloudflare if needed)
- [ ] Decide if duplicate-title remediation should be scheduled (6 pairs remain)
- [ ] Decide if IndexNow CI should switch from `--dry-run` to live submission
- [ ] Review if any new topic hubs should get curated intros (check `tools/topic_intros.json`)

---

## 5. Metrics Table Template

Copy this table into a new row each week:

| Date | GSC indexed | GSC not indexed | Sitemap discovered | Impressions | Clicks | CTR | Avg position | Bing indexed | IndexNow status | Bot blockers | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| YYYY-MM-DD | | | | | | | | | | | |

**Definitions:**
- **GSC indexed**: Pages marked "Valid" in GSC Index > Pages
- **GSC not indexed**: Pages in any non-Valid bucket
- **Sitemap discovered**: URLs shown in GSC Sitemaps report for `/sitemap.xml`
- **IndexNow status**: dry-run output or live submission result
- **Bot blockers**: Any 403/429 from radar/www to Googlebot/Bingbot

---

## 6. Escalation Rules

| Symptom | Action | Owner |
|---|---|---|
| Googlebot/Bingbot gets **403/429** on Radar/www | Fix Vercel/Cloudflare bot protection allowlist immediately | You / Vercel / Cloudflare |
| Sitemap URL count **≠ 80** | Inspect `tools/rebuild_local.py` `build_sitemap()`; check for unintended URL additions | Repo |
| Local `/articles/<slug>/` appears in sitemap | **Block deployment**. Fix `build_sitemap()` filter. | Repo |
| IndexNow key file returns **404** | Trigger manual deploy or inspect `INDEXNOW_API_KEY_ARTICLES_FAIM` env var / build output | Repo |
| Indexed count **flat for 2–4 weeks** after PR A/C | Inspect topic hub quality, internal links, and GSC URL Inspection samples | You + Repo |
| GSC flags **duplicate/canonical** issues | Sample URL Inspection before changing repo canonical policy | You |
| Bing Webmaster shows **IndexNow key invalid** | Re-verify key file URL and content; check Bing dashboard | You |
| Topic hub impressions **high but CTR low** | Test title/meta tweaks in PR C follow-up | Repo |

---

## 7. Commands Appendix

### Sitemap health

```bash
# Count URLs
grep -c '<url>' sitemap.xml

# Check for excluded patterns
grep '/articles/' sitemap.xml || echo "OK no local articles"
grep 'radar.firstaimovers.com' sitemap.xml || echo "OK no cross-host"
grep -E '\.md|\.txt|\.json|\.cff|feed\.xml|feed\.json' sitemap.xml || echo "OK no raw data"
```

### IndexNow

```bash
# Dry-run (safe, no network submission)
python3 tools/submit_indexnow.py --dry-run

# Or via Doppler
# doppler run -- python3 tools/submit_indexnow.py --dry-run

# Live submission (run manually after verifying key is live)
python3 tools/submit_indexnow.py
```

### Key file live check

```bash
# Replace <key> with the current key from INDEXNOW_API_KEY_ARTICLES_FAIM
curl -I https://articles.firstaimovers.com/<key>.txt
curl -sL https://articles.firstaimovers.com/<key>.txt
```

### Bot access checks

```bash
# Googlebot
curl -A "Googlebot/2.1 (+http://www.google.com/bot.html)" -I https://articles.firstaimovers.com/
curl -A "Googlebot/2.1 (+http://www.google.com/bot.html)" -I https://radar.firstaimovers.com/
curl -A "Googlebot/2.1 (+http://www.google.com/bot.html)" -I https://www.firstaimovers.com/

# Bingbot
curl -A "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)" -I https://articles.firstaimovers.com/
curl -A "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)" -I https://radar.firstaimovers.com/
curl -A "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)" -I https://www.firstaimovers.com/
```

### Full validation

```bash
python3 -m pytest tools/tests -v
INDEXNOW_API_KEY_ARTICLES_FAIM=<key> python3 tools/rebuild_local.py
INDEXNOW_API_KEY_ARTICLES_FAIM=<key> python3 tools/submit_indexnow.py --dry-run
python3 tools/normalize_tags.py --dry-run
```

---

## 8. Account Actions (User-side)

These require your login and cannot be done by repo tooling alone:

| Action | Tool | Status | Notes |
|---|---|---|---|
| Resubmit sitemap in GSC | Google Search Console | ✅ Done | Discovers 80 URLs for `https://articles.firstaimovers.com/sitemap.xml` |
| Verify site in Bing Webmaster | Bing Webmaster Tools | ✅ Done | `articles.firstaimovers.com` |
| Submit sitemap in Bing | Bing Webmaster Tools | ✅ Done | Same URL as GSC |
| Validate IndexNow key in Bing | Bing Webmaster Tools | ✅ Done | Key from `INDEXNOW_API_KEY_ARTICLES_FAIM` env var |
| Allowlist Googlebot/Bingbot on Radar | Vercel dashboard | ⏳ Paused — external platform | `radar.firstaimovers.com` is on Hashnode; platform-level control may be required |
| Allowlist Bingbot on www | Cloudflare dashboard | ⏳ Paused — external platform | `www.firstaimovers.com` is on Beehiiv; track for WordPress/Hetzner migration |
| Yandex Webmaster (optional) | Yandex.Webmaster | ⏳ Optional | Only if targeting RU/CIS traffic |

---

## 9. External platform follow-ups — paused

These are not repo blockers. They depend on external platform capabilities.

### Radar / Hashnode

`radar.firstaimovers.com` is hosted on Hashnode. During sprint QA, Radar returned **429** to both Googlebot and Bingbot. Hashnode platform-level bot protection may require support ticket or premium feature. Parked until migration or platform confirmation.

### www / Beehiiv

`www.firstaimovers.com` is currently hosted on Beehiiv. During sprint QA, www returned **403 to Bingbot** (Googlebot returns 200). Beehiiv does not expose low-level WAF rules. This will be addressed during the future WordPress/Hetzner migration where Cloudflare rules and a custom `robots.txt` can be configured.

---

*Last updated: 2026-04-28. Search Visibility Sprint closed for `articles.firstaimovers.com`.*
