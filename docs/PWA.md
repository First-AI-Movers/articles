# PWA + Offline Reading Mode

The First AI Movers Article Archive is installable as a lightweight Progressive Web App (PWA). Users can add it to their home screen and access cached content when offline.

## What ships

- **`static/manifest.webmanifest`** — Web App Manifest with name, icons, theme colors, and display mode
- **`static/icons/icon-{192,512}.png`** — Installable PNG icons generated deterministically from SVG
- **`static/sw.js`** — Service worker with precache, runtime cache, and offline fallback
- **`static/pwa.js`** — Service worker registration script
- **`templates/offline.html.j2`** — Offline fallback page
- **`tools/build_pwa_icons.py`** — Deterministic icon generator

## Manifest

| Field | Value |
|---|---|
| `name` | First AI Movers Article Archive |
| `short_name` | FAIM Archive |
| `start_url` | `/` |
| `display` | `standalone` |
| `theme_color` | `#111827` (dark) |
| `background_color` | `#111827` (dark) |
| `icons` | 192×192 PNG, 512×512 PNG |

## Service worker strategy

### Precache (install)

The following URLs are cached during service worker installation:

- `/` (home)
- `/topics/` (topics index)
- `/about/` (about page)
- `/offline/` (offline fallback)
- `/style.css`, `/search.js`, `/pwa.js`, `/manifest.webmanifest`
- `/index.json`, `/feed.json`, `/llms.txt`
- All font files under `/fonts/`
- All icons under `/icons/`

### Runtime cache

| Request type | Strategy |
|---|---|
| Navigation (HTML pages) | Network-first, fallback to cached, then `/offline/` |
| CSS / JS / fonts / icons | Cache-first |
| `index.json`, `feed.json`, `llms.txt`, `llms-full.txt`, `llms-recent.txt` | Stale-while-revalidate |

### Never cached

- GoatCounter analytics (`gc.zgo.at`)
- Giscus comments (if enabled)
- MCP server endpoint (`/mcp`)
- Cross-origin requests

### Cache versioning

Cache names are derived deterministically from the precache URL list. When the precache list changes, the service worker installs a new cache and cleans up the old one on activation.

## Offline page

When a navigation request fails and no cached version exists, the service worker returns `/offline/`. The offline page:

- Uses the same base layout, theme support, and accessibility landmarks
- Is marked `noindex, nofollow`
- Links back to home and topics
- Does not load GoatCounter or Giscus

## Local testing

```bash
# 1. Build the site
python3 tools/rebuild_local.py

# 2. Serve locally
python3 -m http.server 8000 --directory site

# 3. Open Chrome DevTools → Application → Manifest
#    Verify manifest is recognized, icons load, and service worker registers.

# 4. Test offline mode
#    - Visit the site once while online
#    - In DevTools → Network, set Throttling to "Offline"
#    - Navigate to a cached page (e.g. home or topics)
#    - Confirm the offline fallback appears for uncached pages
```

## Clearing cache during debugging

```bash
# Chrome DevTools → Application → Service Workers → Unregister
# Or: DevTools → Application → Storage → Clear site data
```

## Updating the service worker

1. Edit `static/sw.js` or the precache list
2. Run `python3 tools/rebuild_local.py`
3. The new service worker will install on the next visit and activate when all tabs are closed or `skipWaiting()` fires

## Rollback

To remove PWA support:

1. Delete `static/manifest.webmanifest`
2. Delete `static/sw.js`
3. Delete `static/pwa.js`
4. Delete `static/icons/`
5. Delete `templates/offline.html.j2`
6. Remove manifest link and `pwa.js` script from `templates/base.html.j2`
7. Remove `tools/build_pwa_icons.py`
8. Remove `_render("offline.html.j2", ...)` from `tools/rebuild_local.py`
9. Delete `docs/PWA.md`
10. Rebuild and deploy

## Security / privacy

- No third-party scripts are cached
- No analytics events are added for offline usage
- Service worker scope is limited to the origin
- Cross-origin requests are passed through uncached

## Limitations

- **Not every article is guaranteed offline in v1.** The precache includes the app shell and key feeds, but individual article pages are cached on first visit only.
- **Cached content may lag** until the service worker updates.
- **Browser-specific install behavior** varies. Chrome and Edge show an install prompt; Safari requires manual "Add to Home Screen".
- **Lighthouse PWA badge is not a hard gate.** We verify Chrome installability checks, manifest validity, and service worker registration instead.
