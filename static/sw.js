/**
 * Service Worker for First AI Movers Article Archive.
 *
 * Strategy:
 * - Precache: app shell, core CSS/JS/fonts, key JSON feeds.
 * - Runtime cache: navigation requests (network-first with offline fallback),
 *   CSS/JS/fonts/icons (cache-first), index.json/feed.json (stale-while-revalidate).
 * - Never cache: GoatCounter, Giscus, external canonical pages, cross-origin.
 *
 * Cache version is derived from the precache URL list so it invalidates
 * deterministically when the shell changes.
 */

const PRECACHE_URLS = [
  "/",
  "/topics/",
  "/about/",
  "/offline/",
  "/style.css",
  "/search.js",
  "/pwa.js",
  "/manifest.webmanifest",
  "/index.json",
  "/feed.json",
  "/llms.txt",
  "/fonts/inter/Inter-Regular.woff2",
  "/fonts/inter/Inter-SemiBold.woff2",
  "/fonts/inter/Inter-Bold.woff2",
  "/fonts/jetbrains-mono/JetBrainsMono-Regular.woff2",
  "/fonts/jetbrains-mono/JetBrainsMono-SemiBold.woff2",
  "/fonts/jetbrains-mono/JetBrainsMono-Bold.woff2",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
];

function _cacheVersion() {
  // Deterministic version from precache list
  let hash = 0;
  for (const url of PRECACHE_URLS) {
    for (let i = 0; i < url.length; i++) {
      hash = ((hash << 5) - hash + url.charCodeAt(i)) | 0;
    }
  }
  return "faim-sw-v" + Math.abs(hash).toString(36);
}

const CACHE_VERSION = _cacheVersion();
const PRECACHE = CACHE_VERSION + "-precache";
const RUNTIME = CACHE_VERSION + "-runtime";

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches
      .open(PRECACHE)
      .then(function (cache) {
        return cache.addAll(PRECACHE_URLS);
      })
      .then(function () {
        return self.skipWaiting();
      })
  );
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches
      .keys()
      .then(function (cacheNames) {
        return Promise.all(
          cacheNames
            .filter(function (name) {
              return name.startsWith("faim-sw-v") && name !== PRECACHE && name !== RUNTIME;
            })
            .map(function (name) {
              return caches.delete(name);
            })
        );
      })
      .then(function () {
        return self.clients.claim();
      })
  );
});

function _shouldNeverCache(request) {
  const url = new URL(request.url);

  // Never cache cross-origin
  if (url.origin !== self.location.origin) {
    return true;
  }

  // Never cache GoatCounter
  if (url.hostname === "gc.zgo.at" || url.pathname.startsWith("/count")) {
    return true;
  }

  // Never cache Giscus (if enabled)
  if (url.pathname.includes("giscus") || url.hostname.includes("giscus")) {
    return true;
  }

  // Never cache MCP server endpoint
  if (url.pathname.startsWith("/mcp")) {
    return true;
  }

  return false;
}

function _isNavigationRequest(request) {
  return request.mode === "navigate";
}

function _isStaticAsset(request) {
  const dest = request.destination;
  return dest === "style" || dest === "script" || dest === "font" || dest === "image";
}

function _isStaleWhileRevalidate(request) {
  const url = new URL(request.url);
  return (
    url.pathname === "/index.json" ||
    url.pathname === "/feed.json" ||
    url.pathname === "/llms.txt" ||
    url.pathname === "/llms-full.txt" ||
    url.pathname === "/llms-recent.txt"
  );
}

self.addEventListener("fetch", function (event) {
  const request = event.request;

  if (_shouldNeverCache(request)) {
    return;
  }

  if (_isNavigationRequest(request)) {
    // Network-first for navigation, fallback to offline page
    event.respondWith(
      fetch(request)
        .then(function (response) {
          if (response.ok) {
            const clone = response.clone();
            caches.open(RUNTIME).then(function (cache) {
              cache.put(request, clone);
            });
          }
          return response;
        })
        .catch(function () {
          return caches.match(request).then(function (cached) {
            if (cached) {
              return cached;
            }
            return caches.match("/offline/");
          });
        })
    );
    return;
  }

  if (_isStaticAsset(request)) {
    // Cache-first for CSS/JS/fonts/icons
    event.respondWith(
      caches.match(request).then(function (cached) {
        if (cached) {
          return cached;
        }
        return fetch(request).then(function (response) {
          if (response.ok) {
            const clone = response.clone();
            caches.open(RUNTIME).then(function (cache) {
              cache.put(request, clone);
            });
          }
          return response;
        });
      })
    );
    return;
  }

  if (_isStaleWhileRevalidate(request)) {
    // Stale-while-revalidate for JSON feeds
    event.respondWith(
      caches.match(request).then(function (cached) {
        const networkFetch = fetch(request).then(function (response) {
          if (response.ok) {
            const clone = response.clone();
            caches.open(RUNTIME).then(function (cache) {
              cache.put(request, clone);
            });
          }
          return response;
        });
        return cached || networkFetch;
      })
    );
    return;
  }

  // Default: network only
});
