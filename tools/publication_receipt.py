#!/usr/bin/env python3
"""Verified publication receipts for archive eligibility.

Decision record: ``docs/decisions/archive-eligibility-by-verified-publication-receipt.md``.

A record is admitted to the archive because its publication can be *verified on a
public page*, never because an editorial select says ``Posted``. Two receipt kinds:

* ``HASHNODE_POST`` (primary) -- the source row says ``hashnode = published`` and carries
  a 24-hex ``hashnode_post_id``; the post URL is resolved through the publication's
  public sitemap (the Hashnode slug may carry a suffix the source slug lacks) and the
  page must **embed that post id**. The page's ``<link rel="canonical">`` is compared with
  the source canonical URL and recorded as ``canonical_match`` -- a drift signal, never
  a rejection, because the newsletter platform renames slugs after publication.
* ``OWNED_SOURCE_URL`` (fallback) -- the canonical URL is on a first-party host and its
  page canonical normalizes to itself. Used when the row carries no Hashnode receipt,
  and also when it does but the publication URL cannot be *resolved* (cross-posted
  articles carry a hand-written publication slug the source slug cannot predict). A
  publication page that IS found but does not embed the post id never falls through:
  that is a disproved claim, not an unresolved one.

No receipt -> not eligible. Transport failures, ``429`` and ``5xx`` are
``receipt_unverifiable``: counted and retried next run, never a receipt and never a
rejection. The Hashnode GraphQL API is deliberately not used: since 2026-05-13 every
request against it requires a paid plan, and the public surfaces are sufficient.

Read budget: the sitemap index and its pages are fetched at most once per
``Verifier`` (<= 21 requests) and cached, including a failed fetch so a broken
sitemap is not hammered; post pages are fetched only for candidates of the record
being decided (at most ``MAX_CANDIDATES``). Callers decide archive presence BEFORE
asking for a receipt: the gate governs admission, never retention, so a record the
archive already holds is never looked up. Unit tests inject a fake ``fetch``; the
real fetcher lives in ``build_http_fetcher``.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlsplit

HASHNODE_PUBLICATION_HOST = "radar.firstaimovers.com"
# First-party properties whose pages may serve as an OWNED_SOURCE_URL receipt.
# Third-party hosts that block automated reads are deliberately absent.
OWNED_SOURCE_HOSTS = frozenset({
    "www.firstaimovers.com",
    "insights.firstaimovers.com",
    "voices.firstaimovers.com",
    HASHNODE_PUBLICATION_HOST,
})

FIELD_HASHNODE_STATE = "hashnode"
FIELD_HASHNODE_POST_ID = "hashnode_post_id"
FIELD_ARCHIVE_EXCLUDE = "archive_exclude"
HASHNODE_PUBLISHED_STATE = "published"
POST_ID_RE = re.compile(r"^[0-9a-f]{24}$")

KIND_HASHNODE_POST = "HASHNODE_POST"
KIND_OWNED_SOURCE_URL = "OWNED_SOURCE_URL"

CLASS_ELIGIBLE = "eligible"
CLASS_EXCLUDED = "excluded"
CLASS_RIGHTS_DENIED = "rights_denied"
CLASS_NO_RECEIPT = "no_receipt"
CLASS_UNVERIFIABLE = "receipt_unverifiable"
ALL_CLASSES = (CLASS_ELIGIBLE, CLASS_EXCLUDED, CLASS_RIGHTS_DENIED, CLASS_NO_RECEIPT,
               CLASS_UNVERIFIABLE)

SITEMAP_MAX_PAGES = 20      # + the index = at most 21 sitemap requests per verifier
MAX_CANDIDATES = 3          # post pages fetched per record, at most
USER_AGENT = ("Mozilla/5.0 (compatible; first-ai-movers-archive/1.0; "
              "+https://github.com/First-AI-Movers/articles)")
REQUEST_TIMEOUT_S = 20
MIN_INTERVAL_S = 1.0

_LOC_RE = re.compile(r"<loc>\s*(.*?)\s*</loc>", re.S)
_CANONICAL_RE = re.compile(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']', re.I)
_CANONICAL_RE_ALT = re.compile(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']', re.I)
_OG_URL_RE = re.compile(r'<meta[^>]+property=["\']og:url["\'][^>]+content=["\']([^"\']+)["\']', re.I)


class FetchError(Exception):
    """A transport-level failure (DNS, TLS, timeout, connection reset)."""


@dataclass(frozen=True)
class Decision:
    """The eligibility outcome for one record under the receipt gate."""

    klass: str
    reason: str
    receipt: dict | None = None
    canonical_match: bool | None = None

    @property
    def eligible(self) -> bool:
        return self.klass == CLASS_ELIGIBLE


def _select_name(value):
    """Airtable select values arrive as a plain name over REST; tolerate the
    ``{"name": ...}`` object shape some clients return."""
    if isinstance(value, dict):
        value = value.get("name", "")
    return (value or "").strip().lower() if isinstance(value, str) else ""


def _host(url: str) -> str:
    try:
        return (urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""


def _last_segment(url: str) -> str:
    path = urlsplit(url).path.rstrip("/")
    return path.rsplit("/", 1)[-1] if path else ""


def page_canonical(html: str) -> str:
    """The page's declared canonical URL: ``<link rel=canonical>`` first, ``og:url`` second."""
    for pattern in (_CANONICAL_RE, _CANONICAL_RE_ALT, _OG_URL_RE):
        m = pattern.search(html)
        if m:
            return m.group(1).strip()
    return ""


class Verifier:
    """Decides archive eligibility from verified publication receipts.

    ``fetch(url) -> (status_code, text)`` and raises ``FetchError`` on transport
    failure. ``normalize_url`` is the archive's canonical-URL normalizer (injected so
    this module has no dependency on the ingestion module).
    """

    def __init__(self, fetch, *, normalize_url, publication_host=HASHNODE_PUBLICATION_HOST,
                 owned_hosts=OWNED_SOURCE_HOSTS, deny_licenses=frozenset(), now=None):
        self._fetch = fetch
        self._normalize = normalize_url
        self.publication_host = publication_host
        self.owned_hosts = frozenset(h.lower() for h in owned_hosts)
        self.deny_licenses = frozenset(v.strip().lower() for v in deny_licenses if v)
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._sitemap: list[str] | None = None
        self._sitemap_loaded = False
        self.requests_made = 0

    # -- sitemap ---------------------------------------------------------------

    def _get(self, url):
        self.requests_made += 1
        return self._fetch(url)

    def sitemap_urls(self) -> list[str] | None:
        """Every post URL listed by the publication sitemap, or ``None`` when the
        sitemap could not be read. Fetched once and cached either way.

        Only ``<loc>`` is used. Sitemap ``<lastmod>`` is ignored: listing freshness
        is not a publication receipt.
        """
        if self._sitemap_loaded:
            return self._sitemap
        self._sitemap_loaded = True
        base = f"https://{self.publication_host}/sitemap.xml"
        try:
            status, text = self._get(base)
            if status != 200:
                return None
            locs = _LOC_RE.findall(text)
            if "<sitemapindex" not in text:
                self._sitemap = locs
                return self._sitemap
            urls: list[str] = []
            for child in locs[:SITEMAP_MAX_PAGES]:
                status, text = self._get(child)
                if status != 200:
                    return None
                urls.extend(_LOC_RE.findall(text))
            self._sitemap = urls
        except FetchError:
            return None
        return self._sitemap

    def candidates(self, slug_stem: str) -> list[str]:
        """Publication URLs whose last path segment is the stem or the stem plus a
        ``-suffix``; exact match first, then shortest suffix. At most MAX_CANDIDATES."""
        stem = (slug_stem or "").strip().lower()
        urls = self.sitemap_urls()
        if not stem or not urls:
            return []
        exact, suffixed = [], []
        for u in urls:
            seg = _last_segment(u).lower()
            if seg == stem:
                exact.append(u)
            elif seg.startswith(stem + "-"):
                suffixed.append(u)
        suffixed.sort(key=lambda u: (len(_last_segment(u)), u))
        return (exact + suffixed)[:MAX_CANDIDATES]

    # -- receipts --------------------------------------------------------------

    def _hashnode_receipt(self, post_id: str, slug_stem: str, canonical_url: str) -> Decision:
        urls = self.sitemap_urls()
        if urls is None:
            return Decision(CLASS_UNVERIFIABLE, "publication sitemap unavailable")
        cands = self.candidates(slug_stem)
        if not cands:
            # UNRESOLVABLE, not disproved: cross-posted articles carry a hand-written
            # publication slug that the source slug cannot predict. decide() falls
            # through to the first-party source receipt in this one case.
            return Decision(CLASS_NO_RECEIPT, f"no publication URL matches slug stem '{slug_stem}'",
                            receipt={"_unresolved": True})
        for url in cands:
            try:
                status, text = self._get(url)
            except FetchError as exc:
                return Decision(CLASS_UNVERIFIABLE, f"post page fetch failed: {exc}")
            if status == 429 or status >= 500:
                return Decision(CLASS_UNVERIFIABLE, f"post page returned HTTP {status}")
            if status != 200 or post_id not in text:
                continue
            declared = page_canonical(text)
            match = bool(declared) and self._normalize(declared) == self._normalize(canonical_url)
            receipt = {
                "kind": KIND_HASHNODE_POST,
                "post_id": post_id,
                "url": url,
                "canonical_match": match,
                "verified_at": self._now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            return Decision(CLASS_ELIGIBLE, "hashnode post id embedded on publication page",
                            receipt=receipt, canonical_match=match)
        return Decision(CLASS_NO_RECEIPT, "no candidate publication page embeds the post id")

    def _owned_source_receipt(self, canonical_url: str) -> Decision:
        host = _host(canonical_url)
        if not canonical_url.lower().startswith("https://") or host not in self.owned_hosts:
            return Decision(CLASS_NO_RECEIPT, f"canonical host '{host or '-'}' is not a first-party property")
        try:
            status, text = self._get(canonical_url)
        except FetchError as exc:
            return Decision(CLASS_UNVERIFIABLE, f"source page fetch failed: {exc}")
        if status in (401, 403, 429) or status >= 500:
            # A first-party host that refuses the reader (bot protection on the
            # Medium custom domains, rate limits) has not said the article is absent.
            return Decision(CLASS_UNVERIFIABLE, f"source page returned HTTP {status}")
        if status != 200:
            return Decision(CLASS_NO_RECEIPT, f"source page returned HTTP {status}")
        declared = page_canonical(text)
        if not declared or self._normalize(declared) != self._normalize(canonical_url):
            return Decision(CLASS_NO_RECEIPT, "source page does not declare itself canonical")
        receipt = {
            "kind": KIND_OWNED_SOURCE_URL,
            "url": canonical_url,
            "canonical_match": True,
            "verified_at": self._now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        return Decision(CLASS_ELIGIBLE, "first-party source page declares itself canonical",
                        receipt=receipt, canonical_match=True)

    # -- the gate --------------------------------------------------------------

    def decide(self, fields: dict, *, canonical_url: str, slug: str, license_value: str = "") -> Decision:
        """Eligibility of one source record. ``fields`` is the raw Airtable fields dict;
        ``canonical_url`` and ``slug`` are the archive payload's values."""
        fields = fields or {}
        if bool(fields.get(FIELD_ARCHIVE_EXCLUDE)):
            return Decision(CLASS_EXCLUDED, f"{FIELD_ARCHIVE_EXCLUDE} is set")
        if license_value and license_value.strip().lower() in self.deny_licenses:
            return Decision(CLASS_RIGHTS_DENIED, f"license '{license_value}' is in the deny set")

        state = _select_name(fields.get(FIELD_HASHNODE_STATE))
        post_id = (fields.get(FIELD_HASHNODE_POST_ID) or "").strip() if isinstance(
            fields.get(FIELD_HASHNODE_POST_ID), str) else ""
        if state == HASHNODE_PUBLISHED_STATE and POST_ID_RE.match(post_id):
            primary = self._hashnode_receipt(post_id, slug, canonical_url or "")
            if not (primary.receipt or {}).get("_unresolved"):
                return primary          # verified, disproved (page without the id) or unverifiable
            fallback = self._owned_source_receipt(canonical_url or "")
            if fallback.klass in (CLASS_ELIGIBLE, CLASS_UNVERIFIABLE):
                return fallback
            return Decision(CLASS_NO_RECEIPT, f"{primary.reason}; {fallback.reason}")
        return self._owned_source_receipt(canonical_url or "")


def build_http_fetcher(session=None, *, min_interval_s=MIN_INTERVAL_S, sleep=time.sleep):
    """A polite public-page fetcher: browser-like UA, timeout, >= ``min_interval_s``
    between requests, one retry on 429/5xx. Returns ``(status_code, text)``; raises
    ``FetchError`` on transport failure. Sends no credential anywhere."""
    import requests  # local import: unit tests never need it

    sess = session or requests.Session()
    sess.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,application/xml;q=0.9,*/*;q=0.8"})
    last = {"t": 0.0}

    def fetch(url):
        for attempt in (1, 2):
            wait = min_interval_s - (time.monotonic() - last["t"])
            if wait > 0:
                sleep(wait)
            try:
                resp = sess.get(url, timeout=REQUEST_TIMEOUT_S, allow_redirects=True)
            except requests.RequestException as exc:  # pragma: no cover - transport
                raise FetchError(str(exc)) from exc
            finally:
                last["t"] = time.monotonic()
            if attempt == 1 and (resp.status_code == 429 or resp.status_code >= 500):
                sleep(3.0)
                continue
            return resp.status_code, resp.text
        return resp.status_code, resp.text  # pragma: no cover - loop always returns

    return fetch
