"""Tests for tools/publication_receipt.py -- the receipt gate of
ADR:archive-eligibility-by-verified-publication-receipt.

Every case runs against an injected fake ``fetch``; nothing here touches the network.
The fixture set mirrors the ADR's Validation section: id present + canonical match,
id present + canonical drift, a 200 page without the id (must reject), 404, 429,
slug-suffix resolution, an owned-host source receipt, a refused third-party host,
``archive_exclude`` and the license deny-set -- plus the read budget.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "tools" / "publication_receipt.py"

PUB = "https://radar.firstaimovers.com"
POST_ID = "6965681a4531576997954f6b"
OTHER_ID = "000000000000000000000000"
SOURCE = "https://www.firstaimovers.com/p/ai-memory-education-2025"
SOURCE_RENAMED = "https://www.firstaimovers.com/p/ai-memory-value-gap-education-2025"
STEM = "ai-memory-education-2025"
FIXED_NOW = datetime(2026, 9, 18, 11, 2, 0, tzinfo=timezone.utc)


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("publication_receipt", MODULE_PATH)
    m = importlib.util.module_from_spec(spec)
    sys.modules["publication_receipt"] = m
    spec.loader.exec_module(m)
    return m


def _normalize(url: str) -> str:
    """A deliberately simple normalizer: scheme/host case, trailing slash, query."""
    url = url.strip().split("?", 1)[0].rstrip("/")
    scheme, _, rest = url.partition("://")
    return scheme.lower() + "://" + rest


def _sitemap_index(*children):
    locs = "".join(f"<sitemap><loc>{c}</loc></sitemap>" for c in children)
    return f'<?xml version="1.0"?><sitemapindex xmlns="x">{locs}</sitemapindex>'


def _urlset(*urls):
    locs = "".join(f"<url><loc>{u}</loc><lastmod>2026-09-01</lastmod></url>" for u in urls)
    return f'<?xml version="1.0"?><urlset xmlns="x">{locs}</urlset>'


def _page(post_id: str | None, canonical: str | None, *, og_only=False):
    head = "<html><head>"
    if canonical and not og_only:
        head += f'<link rel="canonical" href="{canonical}"/>'
    if canonical and og_only:
        head += f'<meta property="og:url" content="{canonical}"/>'
    head += "</head><body>"
    if post_id:
        head += f'<script>{{"post":{{"id":"{post_id}"}}}}</script>'
    return head + "</body></html>"


class FakeFetch:
    """Dict-backed fetcher that records every URL it was asked for."""

    def __init__(self, mod, pages: dict):
        self.mod = mod
        self.pages = pages
        self.calls: list[str] = []

    def __call__(self, url):
        self.calls.append(url)
        if url not in self.pages:
            return 404, "<html>not found</html>"
        value = self.pages[url]
        if isinstance(value, Exception):
            raise value
        return value


def _verifier(mod, pages, **kw):
    fetch = FakeFetch(mod, pages)
    v = mod.Verifier(fetch, normalize_url=_normalize, now=lambda: FIXED_NOW, **kw)
    return v, fetch


def _sitemap_pages(*post_urls):
    return {
        f"{PUB}/sitemap.xml": (200, _sitemap_index(f"{PUB}/sitemap.xml?page=1")),
        f"{PUB}/sitemap.xml?page=1": (200, _urlset(f"{PUB}/", *post_urls)),
    }


HASHNODE_FIELDS = {"hashnode": "published", "hashnode_post_id": POST_ID}


# --------------------------------------------------------------------------
# R1 -- HASHNODE_POST
# --------------------------------------------------------------------------

class TestHashnodeReceipt:
    def test_id_present_and_canonical_match_is_eligible(self, mod):
        pages = _sitemap_pages(f"{PUB}/{STEM}")
        pages[f"{PUB}/{STEM}"] = (200, _page(POST_ID, SOURCE))
        v, fetch = _verifier(mod, pages)
        d = v.decide(HASHNODE_FIELDS, canonical_url=SOURCE, slug=STEM)
        assert d.eligible and d.klass == mod.CLASS_ELIGIBLE
        assert d.canonical_match is True
        assert d.receipt == {
            "kind": "HASHNODE_POST", "post_id": POST_ID, "url": f"{PUB}/{STEM}",
            "canonical_match": True, "verified_at": "2026-09-18T11:02:00Z",
        }

    def test_id_present_and_canonical_drift_is_eligible_with_signal(self, mod):
        """The newsletter renamed the slug after publication: the page canonical names
        the new slug, the source row still names the old one. Still a receipt."""
        pages = _sitemap_pages(f"{PUB}/{STEM}")
        pages[f"{PUB}/{STEM}"] = (200, _page(POST_ID, SOURCE_RENAMED))
        v, _ = _verifier(mod, pages)
        d = v.decide(HASHNODE_FIELDS, canonical_url=SOURCE, slug=STEM)
        assert d.eligible
        assert d.canonical_match is False
        assert d.receipt["canonical_match"] is False

    def test_page_without_the_post_id_is_not_a_receipt(self, mod):
        """A 200 page under the right slug that does not embed the record's post id
        proves nothing -- it could be a different article."""
        pages = _sitemap_pages(f"{PUB}/{STEM}")
        pages[f"{PUB}/{STEM}"] = (200, _page(OTHER_ID, SOURCE))
        v, _ = _verifier(mod, pages)
        d = v.decide(HASHNODE_FIELDS, canonical_url=SOURCE, slug=STEM)
        assert not d.eligible and d.klass == mod.CLASS_NO_RECEIPT

    def test_404_on_every_candidate_is_no_receipt(self, mod):
        pages = _sitemap_pages(f"{PUB}/{STEM}")  # listed, but the page 404s
        v, _ = _verifier(mod, pages)
        d = v.decide(HASHNODE_FIELDS, canonical_url=SOURCE, slug=STEM)
        assert d.klass == mod.CLASS_NO_RECEIPT

    def test_slug_absent_from_sitemap_falls_through_to_the_source_not_a_page_fetch(self, mod):
        """No sitemap candidate = unresolved, so R2 is consulted (the source page 404s
        here -> no receipt); no publication page is fetched."""
        pages = _sitemap_pages(f"{PUB}/something-else")
        v, fetch = _verifier(mod, pages)
        d = v.decide(HASHNODE_FIELDS, canonical_url=SOURCE, slug=STEM)
        assert d.klass == mod.CLASS_NO_RECEIPT
        assert not any(STEM in u and PUB in u for u in fetch.calls), "no publication page fetch without a candidate"
        assert fetch.calls[-1] == SOURCE

    def test_429_is_unverifiable_not_a_rejection(self, mod):
        pages = _sitemap_pages(f"{PUB}/{STEM}")
        pages[f"{PUB}/{STEM}"] = (429, "rate limited")
        v, _ = _verifier(mod, pages)
        d = v.decide(HASHNODE_FIELDS, canonical_url=SOURCE, slug=STEM)
        assert d.klass == mod.CLASS_UNVERIFIABLE and not d.eligible

    def test_transport_failure_is_unverifiable(self, mod):
        pages = _sitemap_pages(f"{PUB}/{STEM}")
        pages[f"{PUB}/{STEM}"] = mod.FetchError("connection reset")
        v, _ = _verifier(mod, pages)
        d = v.decide(HASHNODE_FIELDS, canonical_url=SOURCE, slug=STEM)
        assert d.klass == mod.CLASS_UNVERIFIABLE

    def test_sitemap_unavailable_is_unverifiable_and_fetched_once(self, mod):
        pages = {f"{PUB}/sitemap.xml": mod.FetchError("dns")}
        v, fetch = _verifier(mod, pages)
        assert v.decide(HASHNODE_FIELDS, canonical_url=SOURCE, slug=STEM).klass == mod.CLASS_UNVERIFIABLE
        assert v.decide(HASHNODE_FIELDS, canonical_url=SOURCE, slug=STEM).klass == mod.CLASS_UNVERIFIABLE
        assert fetch.calls.count(f"{PUB}/sitemap.xml") == 1, "a broken sitemap is not hammered"

    def test_suffixed_hashnode_slug_is_resolved_through_the_sitemap(self, mod):
        """The Hashnode slug carries a suffix the source slug lacks."""
        real = f"{PUB}/{STEM}-skills-gap"
        pages = _sitemap_pages(real, f"{PUB}/{STEM}-skills-gap-longer-decoy", f"{PUB}/unrelated")
        pages[real] = (200, _page(POST_ID, SOURCE))
        pages[f"{PUB}/{STEM}-skills-gap-longer-decoy"] = (200, _page(OTHER_ID, SOURCE))
        v, fetch = _verifier(mod, pages)
        d = v.decide(HASHNODE_FIELDS, canonical_url=SOURCE, slug=STEM)
        assert d.eligible and d.receipt["url"] == real
        assert fetch.calls[-1] == real, "shortest suffix is tried first"

    def test_candidates_are_exact_first_then_shortest_suffix_and_capped(self, mod):
        urls = [f"{PUB}/{STEM}-{s}" for s in ("bbb", "a", "cccc", "dd")] + [f"{PUB}/{STEM}", f"{PUB}/{STEM}x"]
        v, _ = _verifier(mod, _sitemap_pages(*urls))
        cands = v.candidates(STEM)
        assert cands == [f"{PUB}/{STEM}", f"{PUB}/{STEM}-a", f"{PUB}/{STEM}-dd"]
        assert f"{PUB}/{STEM}x" not in v.candidates(STEM), "a bare prefix without '-' is another slug"

    def test_malformed_post_id_does_not_use_r1(self, mod):
        pages = _sitemap_pages(f"{PUB}/{STEM}")
        pages[f"{PUB}/{STEM}"] = (200, _page(POST_ID, SOURCE))
        v, fetch = _verifier(mod, pages)
        d = v.decide({"hashnode": "published", "hashnode_post_id": "not-a-post-id"},
                     canonical_url="https://example.org/x", slug=STEM)
        assert d.klass == mod.CLASS_NO_RECEIPT
        assert f"{PUB}/{STEM}" not in fetch.calls

    def test_select_object_shape_is_tolerated(self, mod):
        pages = _sitemap_pages(f"{PUB}/{STEM}")
        pages[f"{PUB}/{STEM}"] = (200, _page(POST_ID, SOURCE))
        v, _ = _verifier(mod, pages)
        fields = {"hashnode": {"id": "selx", "name": "Published"}, "hashnode_post_id": POST_ID}
        assert v.decide(fields, canonical_url=SOURCE, slug=STEM).eligible


# --------------------------------------------------------------------------
# R2 -- OWNED_SOURCE_URL
# --------------------------------------------------------------------------

class TestOwnedSourceReceipt:
    def test_owned_host_declaring_itself_canonical_is_eligible(self, mod):
        pages = {SOURCE: (200, _page(None, SOURCE))}
        v, _ = _verifier(mod, pages)
        d = v.decide({"hashnode": "todo"}, canonical_url=SOURCE, slug=STEM)
        assert d.eligible and d.receipt["kind"] == "OWNED_SOURCE_URL" and d.canonical_match is True

    def test_og_url_counts_as_declared_canonical(self, mod):
        pages = {SOURCE: (200, _page(None, SOURCE, og_only=True))}
        v, _ = _verifier(mod, pages)
        assert v.decide({}, canonical_url=SOURCE, slug=STEM).eligible

    def test_third_party_host_is_refused_without_a_fetch(self, mod):
        v, fetch = _verifier(mod, {})
        d = v.decide({"hashnode": "error"}, canonical_url="https://medium.com/@someone/post", slug="post")
        assert d.klass == mod.CLASS_NO_RECEIPT
        assert fetch.calls == [], "no request is made to a host outside the allow-list"

    def test_http_scheme_is_refused(self, mod):
        v, fetch = _verifier(mod, {})
        d = v.decide({}, canonical_url="http://www.firstaimovers.com/p/x", slug="x")
        assert d.klass == mod.CLASS_NO_RECEIPT and fetch.calls == []

    def test_source_page_with_a_different_canonical_is_no_receipt(self, mod):
        pages = {SOURCE: (200, _page(None, SOURCE_RENAMED))}
        v, _ = _verifier(mod, pages)
        assert v.decide({}, canonical_url=SOURCE, slug=STEM).klass == mod.CLASS_NO_RECEIPT

    def test_source_404_is_no_receipt_and_5xx_is_unverifiable(self, mod):
        v, _ = _verifier(mod, {})
        assert v.decide({}, canonical_url=SOURCE, slug=STEM).klass == mod.CLASS_NO_RECEIPT
        v, _ = _verifier(mod, {SOURCE: (503, "down")})
        assert v.decide({}, canonical_url=SOURCE, slug=STEM).klass == mod.CLASS_UNVERIFIABLE

    def test_blank_canonical_is_no_receipt(self, mod):
        v, fetch = _verifier(mod, {})
        assert v.decide({}, canonical_url="", slug="").klass == mod.CLASS_NO_RECEIPT
        assert fetch.calls == []


# --------------------------------------------------------------------------
# Exclusion, rights, budget
# --------------------------------------------------------------------------

class TestExclusionRightsAndBudget:
    def test_archive_exclude_wins_before_any_fetch(self, mod):
        v, fetch = _verifier(mod, {})
        d = v.decide({**HASHNODE_FIELDS, "archive_exclude": True}, canonical_url=SOURCE, slug=STEM)
        assert d.klass == mod.CLASS_EXCLUDED and fetch.calls == []

    def test_license_deny_set_is_honoured_and_empty_by_default(self, mod):
        pages = _sitemap_pages(f"{PUB}/{STEM}")
        pages[f"{PUB}/{STEM}"] = (200, _page(POST_ID, SOURCE))
        v, _ = _verifier(mod, dict(pages), deny_licenses={"All Rights Reserved"})
        d = v.decide(HASHNODE_FIELDS, canonical_url=SOURCE, slug=STEM, license_value="all rights reserved")
        assert d.klass == mod.CLASS_RIGHTS_DENIED
        v, _ = _verifier(mod, dict(pages))
        assert v.decide(HASHNODE_FIELDS, canonical_url=SOURCE, slug=STEM,
                        license_value="all rights reserved").eligible, "deny set ships empty"

    def test_sitemap_is_fetched_once_across_many_decisions(self, mod):
        pages = _sitemap_pages(f"{PUB}/{STEM}", f"{PUB}/second")
        pages[f"{PUB}/{STEM}"] = (200, _page(POST_ID, SOURCE))
        pages[f"{PUB}/second"] = (200, _page(OTHER_ID, "https://www.firstaimovers.com/p/second"))
        v, fetch = _verifier(mod, pages)
        v.decide(HASHNODE_FIELDS, canonical_url=SOURCE, slug=STEM)
        v.decide({"hashnode": "published", "hashnode_post_id": OTHER_ID},
                 canonical_url="https://www.firstaimovers.com/p/second", slug="second")
        sitemap_calls = [u for u in fetch.calls if "sitemap" in u]
        assert len(sitemap_calls) == 2, "index + one page, once"
        assert v.requests_made == 4

    def test_sitemap_index_page_cap(self, mod):
        children = [f"{PUB}/sitemap.xml?page={i}" for i in range(1, 30)]
        pages = {f"{PUB}/sitemap.xml": (200, _sitemap_index(*children))}
        for c in children:
            pages[c] = (200, _urlset(f"{PUB}/p{c[-2:]}"))
        v, fetch = _verifier(mod, pages)
        v.sitemap_urls()
        assert v.requests_made == 1 + mod.SITEMAP_MAX_PAGES

    def test_all_classes_are_enumerated(self, mod):
        assert set(mod.ALL_CLASSES) == {"eligible", "excluded", "rights_denied", "no_receipt",
                                        "receipt_unverifiable"}


class TestPageCanonical:
    def test_link_then_og(self, mod):
        assert mod.page_canonical('<link rel="canonical" href="https://a/x"/>') == "https://a/x"
        assert mod.page_canonical('<link href="https://a/y" rel="canonical">') == "https://a/y"
        assert mod.page_canonical('<meta property="og:url" content="https://a/z">') == "https://a/z"
        assert mod.page_canonical("<html></html>") == ""



class TestFallbackFromUnresolvedHashnode:
    """A Hashnode receipt that cannot be RESOLVED (no sitemap candidate -- cross-posted
    articles carry a hand-written publication slug) falls through to the first-party
    source receipt. A publication page that is found but lacks the id never does."""

    def test_unresolved_r1_falls_through_to_owned_source(self, mod):
        pages = _sitemap_pages(f"{PUB}/completely-different-slug")
        pages[SOURCE] = (200, _page(None, SOURCE))
        v, fetch = _verifier(mod, pages)
        d = v.decide(HASHNODE_FIELDS, canonical_url=SOURCE, slug=STEM)
        assert d.eligible and d.receipt["kind"] == "OWNED_SOURCE_URL"
        assert SOURCE in fetch.calls

    def test_unresolved_r1_with_refused_source_is_unverifiable(self, mod):
        pages = _sitemap_pages(f"{PUB}/completely-different-slug")
        pages["https://insights.firstaimovers.com/x-abc123"] = (403, "forbidden")
        v, _ = _verifier(mod, pages)
        d = v.decide(HASHNODE_FIELDS, canonical_url="https://insights.firstaimovers.com/x-abc123", slug="x-abc123")
        assert d.klass == mod.CLASS_UNVERIFIABLE, "a first-party host refusing the reader has not said 'absent'"

    def test_unresolved_r1_with_third_party_source_is_no_receipt_with_both_reasons(self, mod):
        v, fetch = _verifier(mod, _sitemap_pages(f"{PUB}/other"))
        d = v.decide(HASHNODE_FIELDS, canonical_url="https://medium.com/@x/y", slug="y")
        assert d.klass == mod.CLASS_NO_RECEIPT and "slug stem" in d.reason and "first-party" in d.reason
        assert "https://medium.com/@x/y" not in fetch.calls

    def test_disproved_r1_never_falls_through(self, mod):
        """The page under the record's slug exists but embeds a DIFFERENT post id: a
        disproved claim. The source page would pass R2 -- it must not be consulted."""
        pages = _sitemap_pages(f"{PUB}/{STEM}")
        pages[f"{PUB}/{STEM}"] = (200, _page(OTHER_ID, SOURCE))
        pages[SOURCE] = (200, _page(None, SOURCE))
        v, fetch = _verifier(mod, pages)
        d = v.decide(HASHNODE_FIELDS, canonical_url=SOURCE, slug=STEM)
        assert d.klass == mod.CLASS_NO_RECEIPT and SOURCE not in fetch.calls

    def test_owned_source_401_and_403_are_unverifiable(self, mod):
        for code in (401, 403):
            v, _ = _verifier(mod, {SOURCE: (code, "nope")})
            assert v.decide({}, canonical_url=SOURCE, slug=STEM).klass == mod.CLASS_UNVERIFIABLE

    def test_unresolved_marker_never_leaks_into_a_receipt(self, mod):
        pages = _sitemap_pages(f"{PUB}/other")
        pages[SOURCE] = (200, _page(None, SOURCE))
        v, _ = _verifier(mod, pages)
        d = v.decide(HASHNODE_FIELDS, canonical_url=SOURCE, slug=STEM)
        assert "_unresolved" not in d.receipt
