# Analytics

This document describes the privacy-respecting analytics setup for the First AI Movers Article Archive.

## Purpose

Collect real traffic data for topic hubs, article pages, feeds, and reader behavior so future content and CTR improvements are evidence-based instead of speculative.

## Provider

[GoatCounter](https://www.goatcounter.com) — a lightweight, privacy-friendly, open-source web analytics platform.

- **Endpoint:** `https://firstaimovers.goatcounter.com/count`
- **Script:** `https://gc.zgo.at/count.v5.js` (SRI-versioned)
- **Integrity:** `sha384-atnOLvQb9t+jTSipvd75X2yginT4PjVbqDdlJAmxMm+wYElFmeR6EmLP5bYeoRVQ`

## Why GoatCounter

- **Privacy-first:** No personal tracking, no cookies, no fingerprinting.
- **GDPR-compliant out of the box:** GoatCounter documents its own GDPR posture at [goatcounter.com/gdpr](https://www.goatcounter.com/gdpr).
- **Lightweight:** ~3.5 KB script, loaded asynchronously.
- **No cookie banner required:** Because no cookies or consent-requiring tracking is performed.
- **No Google Analytics, no ad pixels, no Tag Manager.**

## Local path override

Local article pages in this archive use **external canonical URLs** (they point to the original publishing property such as Radar or Insights). GoatCounter may use the canonical URL as the default tracked path, which would make all article pageviews appear as external URLs instead of local archive paths.

To fix this, the base template sets an explicit path override before the GoatCounter script loads:

```js
window.goatcounter.path = function () {
  return location.pathname + location.search;
};
```

This ensures analytics records archive-local paths such as `/articles/<slug>/` and `/topics/ai-strategy/`, preserving the ability to measure which local pages drive traffic.

## Verification

1. Open any page on `https://articles.firstaimovers.com/` in a browser without an ad blocker (or with GoatCounter allowed).
2. Open the browser's Network tab.
3. Look for a request to `https://firstaimovers.goatcounter.com/count`.
4. Check the GoatCounter dashboard to confirm the pageview appears.

## Rollback

To remove analytics:

1. Delete the GoatCounter `<script>` block from `templates/base.html.j2`.
2. Run `python3 tools/rebuild_local.py`.
3. Commit and deploy.

No data migration is required.

## Known caveats

- **Ad blockers:** Some ad blockers and privacy browsers block GoatCounter. This is expected and acceptable; the data will be slightly undercounted but still directionally useful.
- **No JavaScript:** Users with JavaScript disabled are not counted.

## What E24 does not include

- Dashboards or reports in this repository.
- Analytics API ingestion.
- Automated reporting.
- A/B testing.
- Event tracking (outbound clicks, scroll depth, etc.).
- Cookies or consent banners.
