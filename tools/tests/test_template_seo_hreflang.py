"""Template SEO regression test for the translation hreflang cluster.

Pins the fix from `fix(seo): repair translation hreflang canonical targets`.

Before the fix, `templates/article.html.j2` emitted the hreflang block on
every page variant and pointed `hreflang="en"` + `hreflang="x-default"` at
`{{ site_url }}/articles/{{ slug }}/` — the local English archive page,
which is `noindex, follow` and canonicalises to the external
`canonical_url`. Google explicitly requires hreflang targets to be
indexable; pointing at a noindex page typically causes the entire cluster
to be dropped.

After the fix, the block:

- Renders only on translated pages (`lang` is set and `lang != 'en'`).
- Points `hreflang="en"` and `hreflang="x-default"` at the external
  `canonical_url` (the authoritative English under this repo's
  archive-copy strategy).
- Keeps inter-language alternates pointing at their local
  `/<lang>/articles/<slug>/` URLs (those pages are `index, follow` and
  self-canonical, which the renderer enforces in `block canonical`).

Renders the article template directly via a minimal Jinja2 environment.
Does not build the full site, does not touch any article, does not run
any workflow.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

jinja2 = pytest.importorskip("jinja2")

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = REPO_ROOT / "templates"

SITE_URL = "https://articles.firstaimovers.com"
CANONICAL_URL = "https://radar.firstaimovers.com/example-article"
SLUG = "example-article"

# Reference URLs used in assertions.
LOCAL_EN_ARCHIVE_URL = f"{SITE_URL}/articles/{SLUG}/"
LOCAL_ES_URL = f"{SITE_URL}/es/articles/{SLUG}/"
LOCAL_FR_URL = f"{SITE_URL}/fr/articles/{SLUG}/"


def _base_context() -> dict:
    """Minimum render context the article template + base layout needs.

    Keeps every dependency value-stable so the only thing the asserting
    test code can observe is the hreflang block's behaviour.
    """
    return {
        "site_url": SITE_URL,
        "site_title": "First AI Movers — Article Archive",
        "site_description": "Test fixture description.",
        "page_path": f"/articles/{SLUG}/",
        "rel_root": "../../",
        "canonical_url": CANONICAL_URL,
        "slug": SLUG,
        "folder": f"2026-05-01-{SLUG}",
        "title": "Example Article",
        "summary": "",
        "summary_short": "",
        "published_date": "2026-05-01",
        "author": "Test Author",
        "canonical_host_label": "radar.firstaimovers.com",
        "reading_time": 5,
        "topics": [],
        "translations": {
            "es": {"ai_generated": True, "approval_method": "ai_qa"},
            "fr": {"ai_generated": True, "approval_method": "ai_qa"},
        },
        "lang": None,
        "outgoing_citations": [],
        "incoming_citations": [],
        "related_articles": [],
        "series": None,
        "doi": None,
        "og_config": {"enabled": False},
        "errata": [],
        "errata_entries": [],
        "comments_enabled": False,
        "tldr": None,
    }


@pytest.fixture(scope="module")
def env():
    """A Jinja2 environment that can render the article template.

    Article template references `topic_slug(...)` as a function call;
    provide a deterministic stub so the render doesn't error on it.
    """
    e = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=jinja2.select_autoescape(["html", "j2"]),
        # ChainableUndefined lets the render traverse attribute access on
        # values the test fixture doesn't set (e.g. stats.total) without
        # crashing — these tests only care about the hreflang block, not
        # the full rendered page.
        undefined=jinja2.ChainableUndefined,
    )
    e.globals["topic_slug"] = lambda s: (s or "").lower().replace(" ", "-")
    # The full site renderer registers a `markdown` filter via
    # tools/rebuild_local.py. The article template uses it for errata
    # bodies. Provide an identity-stub here so the render doesn't error
    # — these tests only care about the hreflang block.
    e.filters["markdown"] = lambda s: s
    return e


def _hreflang_lines(rendered: str) -> list[str]:
    """Return the rendered ``<link rel="alternate" hreflang=...>`` lines."""
    return [
        ln.strip()
        for ln in rendered.splitlines()
        if 'rel="alternate"' in ln and "hreflang=" in ln
    ]


def _hreflang_href_for(rendered: str, hreflang_value: str) -> str | None:
    """Return the ``href`` for the ``<link>`` whose hreflang matches."""
    pattern = (
        rf'<link[^>]*rel="alternate"[^>]*hreflang="{re.escape(hreflang_value)}"'
        rf'[^>]*href="([^"]+)"'
    )
    m = re.search(pattern, rendered)
    if m:
        return m.group(1)
    # Tolerate href-before-hreflang ordering.
    pattern2 = (
        rf'<link[^>]*href="([^"]+)"[^>]*rel="alternate"[^>]*hreflang="{re.escape(hreflang_value)}"'
    )
    m2 = re.search(pattern2, rendered)
    return m2.group(1) if m2 else None


def test_english_archive_page_emits_no_hreflang_block(env):
    """English archive page is `noindex, follow` and canonicalises to the
    external `canonical_url`. Emitting hreflang from a noindex page only
    confuses search engines; the block must be suppressed entirely.
    """
    template = env.get_template("article.html.j2")
    ctx = _base_context()
    ctx["lang"] = "en"  # English archive page
    rendered = template.render(**ctx)

    lines = _hreflang_lines(rendered)
    assert lines == [], (
        "English archive page (lang='en') must emit NO hreflang lines. "
        "It is `noindex, follow` and canonicalises to the external "
        f"canonical_url, so any hreflang there points at a noindex page. "
        f"Got: {lines!r}"
    )


def test_english_archive_page_no_lang_unset_emits_no_hreflang_block(env):
    """Defensive: same outcome when `lang` is unset entirely (the common
    case for the auto-rendered English archive page where the renderer
    does not pass `lang`).
    """
    template = env.get_template("article.html.j2")
    ctx = _base_context()
    ctx["lang"] = None
    rendered = template.render(**ctx)

    assert _hreflang_lines(rendered) == [], (
        "English archive page with lang unset must also emit NO hreflang."
    )


def test_translated_page_en_and_xdefault_point_at_external_canonical(env):
    """The fix's load-bearing assertion: on translated pages,
    `hreflang="en"` and `hreflang="x-default"` MUST point at the external
    `canonical_url` (the authoritative English), NOT at the local English
    archive page (which is noindex + canonicalised away).
    """
    template = env.get_template("article.html.j2")
    ctx = _base_context()
    ctx["lang"] = "es"
    rendered = template.render(**ctx)

    en_href = _hreflang_href_for(rendered, "en")
    xdefault_href = _hreflang_href_for(rendered, "x-default")

    assert en_href == CANONICAL_URL, (
        f"hreflang='en' on a translated page must point at the external "
        f"canonical_url ('{CANONICAL_URL}'). Got: {en_href!r}"
    )
    assert xdefault_href == CANONICAL_URL, (
        f"hreflang='x-default' on a translated page must point at the "
        f"external canonical_url ('{CANONICAL_URL}'). Got: {xdefault_href!r}"
    )


def test_translated_page_does_not_use_local_english_archive_for_en_or_xdefault(env):
    """Explicit negative assertion: the local English archive URL must
    NEVER appear as the target of `hreflang="en"` or `hreflang="x-default"`.
    """
    template = env.get_template("article.html.j2")
    ctx = _base_context()
    ctx["lang"] = "es"
    rendered = template.render(**ctx)

    en_href = _hreflang_href_for(rendered, "en")
    xdefault_href = _hreflang_href_for(rendered, "x-default")

    assert en_href != LOCAL_EN_ARCHIVE_URL, (
        "hreflang='en' must NOT point at the local English archive URL "
        f"('{LOCAL_EN_ARCHIVE_URL}') — that page is noindex and "
        f"canonicalises away."
    )
    assert xdefault_href != LOCAL_EN_ARCHIVE_URL, (
        "hreflang='x-default' must NOT point at the local English archive "
        f"URL ('{LOCAL_EN_ARCHIVE_URL}')."
    )


def test_translated_page_emits_local_alternates_for_every_translation_lang(env):
    """Reciprocity: each language variant in the `translations` mapping
    must have a `hreflang="<lang>"` entry pointing at its local
    `/<lang>/articles/<slug>/` URL (those pages are `index, follow` and
    self-canonical).
    """
    template = env.get_template("article.html.j2")
    ctx = _base_context()
    ctx["lang"] = "es"
    rendered = template.render(**ctx)

    es_href = _hreflang_href_for(rendered, "es")
    fr_href = _hreflang_href_for(rendered, "fr")

    assert es_href == LOCAL_ES_URL, (
        f"hreflang='es' must point at the local Spanish URL "
        f"('{LOCAL_ES_URL}'). Got: {es_href!r}"
    )
    assert fr_href == LOCAL_FR_URL, (
        f"hreflang='fr' must point at the local French URL "
        f"('{LOCAL_FR_URL}'). Got: {fr_href!r}"
    )


def test_translated_page_fully_qualified_urls(env):
    """Every emitted hreflang URL must be absolute (fully qualified),
    per Google's hreflang specification.
    """
    template = env.get_template("article.html.j2")
    ctx = _base_context()
    ctx["lang"] = "es"
    rendered = template.render(**ctx)

    lines = _hreflang_lines(rendered)
    assert lines, "Translated page must emit at least one hreflang line."

    for line in lines:
        # Extract href value.
        m = re.search(r'href="([^"]+)"', line)
        assert m, f"Could not find href in hreflang line: {line!r}"
        href = m.group(1)
        assert href.startswith("https://"), (
            f"hreflang href must be fully qualified (start with 'https://'); "
            f"got: {href!r} on line: {line!r}"
        )
