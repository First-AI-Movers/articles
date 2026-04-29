#!/usr/bin/env python3
"""Rebuild index.json, sitemap.xml, feed.xml, README.md, and llms.txt from
the local working tree.

Designed to run inside CI (GitHub Actions) immediately after the Make.com
pipeline pushes new article folders. Reads every articles/*/metadata.json
on disk, regenerates the five derived artifacts in place, and exits 0 even
if nothing changed.

Operates on the checked-out working tree — the calling workflow commits
and pushes via normal git. No GitHub API calls, no .env required.

Usage:
    python3 tools/rebuild_local.py
"""

import json
import os
import re
import shutil
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse
from xml.dom.minidom import parseString
from xml.etree.ElementTree import Element, SubElement, register_namespace, tostring

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = REPO_ROOT / "articles"
SITE_BASE = "https://articles.firstaimovers.com"

# Hosts this organization owns. Articles whose canonical_url points elsewhere
# (LinkedIn, Medium) stay in index.json but are not advertised in the sitemap:
# we can't declare third-party URLs as ours to search engines.
CANONICAL_ALLOWED_HOSTS = {
    "firstaimovers.com",
    "www.firstaimovers.com",
    "radar.firstaimovers.com",
    "insights.firstaimovers.com",
    "voices.firstaimovers.com",
}

# Atom feed config
ATOM_NS = "http://www.w3.org/2005/Atom"
FEED_MAX_ENTRIES = 50
FEED_CATEGORIES_PER_ENTRY = 5
SUMMARY_MAX_CHARS = 280
TLDR_BLOCKQUOTE_RE = re.compile(
    r"^>\s*\*\*TL;?DR:?\*\*:?\s*(.+?)(?=\n\n|\n#|\Z)",
    re.MULTILINE | re.DOTALL,
)
TLDR_HEADING_RE = re.compile(
    r"^##+\s*TL;?DR\s*\n+(.+?)(?=\n\n|\n##|\Z)",
    re.MULTILINE | re.DOTALL | re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Duplicate-title gate
# ---------------------------------------------------------------------------
def check_duplicate_titles(index):
    """Return a list of (title_lower, [(folder, published_date), ...]) for duplicates.

    Comparison is case-insensitive.  Empty or missing titles are ignored.
    """
    from collections import defaultdict
    by_title = defaultdict(list)
    for a in index.get("articles", []):
        title = a.get("title")
        if not title:
            continue
        by_title[title.lower()].append((a.get("folder", ""), a.get("published_date", "")))
    return [(t, folders) for t, folders in by_title.items() if len(folders) > 1]


# ---------------------------------------------------------------------------
# index.json
# ---------------------------------------------------------------------------
def build_index():
    folders = sorted(p.name for p in ARTICLES_DIR.iterdir() if p.is_dir())
    articles, skipped = [], 0
    for folder in folders:
        meta_path = ARTICLES_DIR / folder / "metadata.json"
        if not meta_path.exists():
            print(f"  SKIP {folder} (no metadata.json)")
            skipped += 1
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"), strict=False)
        except json.JSONDecodeError as e:
            print(f"  ERR  {folder}: {e}", file=sys.stderr)
            skipped += 1
            continue
        articles.append({
            "folder": meta.get("folder"),
            "slug": meta.get("slug"),
            "title": meta.get("title"),
            "published_date": meta.get("published_date"),
            "tags": meta.get("tags", []),
            "topics": meta.get("topics", []),
            "funnel_stage": meta.get("funnel_stage"),
            "canonical_url": meta.get("canonical_url"),
        })
    articles.sort(key=lambda a: a.get("published_date", ""), reverse=True)

    index = {
        "last_updated": str(date.today()),
        "total_articles": len(articles),
        "author": "Dr. Hernani Costa",
        "publication": "First AI Movers",
        "canonical_base": "https://radar.firstaimovers.com",
        "license": "CC BY 4.0",
        "articles": articles,
    }
    from _atomic_io import atomic_write_json
    atomic_write_json(REPO_ROOT / "index.json", index)
    print(f"[index.json] indexed={len(articles)} skipped={skipped}")
    return index


# ---------------------------------------------------------------------------
# README.md + llms.txt
# ---------------------------------------------------------------------------
def compute_stats(index):
    articles = index["articles"]
    tags, topics, funnel, dates = set(), set(), {}, []
    for a in articles:
        tags.update(a.get("tags", []))
        topics.update(a.get("topics", []))
        funnel[a.get("funnel_stage", "unknown")] = funnel.get(a.get("funnel_stage", "unknown"), 0) + 1
        if a.get("published_date"):
            dates.append(a["published_date"])
    dates.sort()
    return {
        "total": len(articles),
        "tags_count": len(tags),
        "topics_count": len(topics),
        "funnel": funnel,
        "date_min": dates[0] if dates else "unknown",
        "date_max": dates[-1] if dates else "unknown",
    }


def _human_date(iso):
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%B %-d, %Y")
    except (ValueError, AttributeError):
        return iso


def _funnel_summary(funnel):
    parts, first = [], True
    for stage in ("top", "middle", "bottom"):
        if stage in funnel:
            parts.append(f"{stage} ({funnel[stage]} articles)" if first else f"{stage} ({funnel[stage]})")
            first = False
    for stage, count in sorted(funnel.items()):
        if stage not in ("top", "middle", "bottom"):
            parts.append(f"{stage} ({count})")
    return ", ".join(parts)


def _month_span(date_min, date_max):
    try:
        dt_min = datetime.strptime(date_min, "%Y-%m-%d")
        dt_max = datetime.strptime(date_max, "%Y-%m-%d")
        return f"{dt_min.strftime('%B %Y')}–{dt_max.strftime('%B %Y')}"
    except ValueError:
        return f"{date_min} – {date_max}"


def patch_readme(content, stats):
    total = stats["total"]
    topics = stats["topics_count"]
    today_iso = str(date.today())
    span = _month_span(stats["date_min"], stats["date_max"])

    content = re.sub(
        r'("description":\s*"The canonical, open-access article archive of First AI Movers: )\d+( original articles)',
        rf"\g<1>{total}\2", content)
    content = re.sub(r'"dateCreated":\s*"\d{4}-\d{2}-\d{2}"',
                     f'"dateCreated": "{stats["date_min"]}"', content)
    content = re.sub(r'"dateModified":\s*"\d{4}-\d{2}-\d{2}"',
                     f'"dateModified": "{today_iso}"', content)
    content = re.sub(r'Articles-\d+-orange', f"Articles-{total}-orange", content)
    content = re.sub(r'— \d+ original articles on AI strategy',
                     f"— {total} original articles on AI strategy", content)
    content = re.sub(
        r'full-text, machine-readable versions of \d+ original articles spanning [^.]+\.',
        f"full-text, machine-readable versions of {total} original articles spanning {span}.",
        content)
    content = re.sub(r'\(\d+ article folders\)', f"({total} article folders)", content)
    content = re.sub(r'\*\*\d+\*\* articles indexed', f"**{total}** articles indexed", content)
    # "unique topic tags" was the pre-normalization label. Migrate either
    # shape to the canonical-topics one.
    content = re.sub(r'\*\*[\d,]+\*\* unique topic tags',
                     f"**{topics}** canonical topics", content)
    content = re.sub(r'\*\*\d+\*\* canonical topics',
                     f"**{topics}** canonical topics", content)
    content = re.sub(r'\*\*3 funnel stages:\*\* .+',
                     f"**3 funnel stages:** {_funnel_summary(stats['funnel'])}", content)
    content = re.sub(r'\*\*Date range:\*\* .+',
                     f"**Date range:** {_human_date(stats['date_min'])} – {_human_date(stats['date_max'])}",
                     content)
    return content


def patch_llms(content, stats):
    content = re.sub(r'\d+ original articles on AI strategy',
                     f"{stats['total']} original articles on AI strategy", content)
    content = re.sub(r'Published [^.]+\.',
                     f"Published {_month_span(stats['date_min'], stats['date_max'])}.", content)
    return content


def update_docs(index):
    stats = compute_stats(index)
    print(f"[docs] total={stats['total']} "
          f"tags={stats['tags_count']} topics={stats['topics_count']} "
          f"range={stats['date_min']}..{stats['date_max']} "
          f"funnel={_funnel_summary(stats['funnel'])}")
    from _atomic_io import atomic_write_text
    for filename, patcher in (("README.md", patch_readme), ("llms.txt", patch_llms)):
        path = REPO_ROOT / filename
        old = path.read_text(encoding="utf-8")
        new = patcher(old, stats)
        if new != old:
            atomic_write_text(path, new)
            print(f"[docs] {filename} updated")
        else:
            print(f"[docs] {filename} unchanged")


# ---------------------------------------------------------------------------
# sitemap.xml
# ---------------------------------------------------------------------------
def _add_url(parent, loc, lastmod, changefreq, priority):
    el = SubElement(parent, "url")
    SubElement(el, "loc").text = loc
    SubElement(el, "lastmod").text = lastmod
    SubElement(el, "changefreq").text = changefreq
    SubElement(el, "priority").text = priority


def _clean_canonical(raw):
    """Return a well-formed http(s) URL or None.

    107 metadata files (2026-01-21 LinkedIn batch) have raw newlines inside
    the canonical_url string; take the last non-empty line and validate.
    """
    if not raw:
        return None
    candidate = raw.strip().splitlines()[-1].strip() if raw.strip() else ""
    parsed = urlparse(candidate)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    return candidate, parsed.netloc.lower()


def _topics_with_page(index):
    """Return (topic_counts: dict, pageable_topics: set, topic_max_dates: dict).

    A topic is 'pageable' if it has >= MIN_ARTICLES_FOR_TOPIC_PAGE articles.
    topic_max_dates maps each topic to the newest published_date among its
    articles, for sitemap <lastmod> freshness signals.
    Shared between build_site and build_sitemap so the set of URLs advertised
    to Google matches the set of URLs actually rendered.
    """
    counts = {}
    max_dates = {}
    for a in index.get("articles", []):
        date = a.get("published_date", "")
        for t in a.get("topics") or []:
            counts[t] = counts.get(t, 0) + 1
            if t not in max_dates or date > max_dates[t]:
                max_dates[t] = date
    pageable = {t for t, c in counts.items() if c >= MIN_ARTICLES_FOR_TOPIC_PAGE}
    return counts, pageable, max_dates


def build_sitemap(index):
    today = str(date.today())
    urlset = Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    # articles.firstaimovers.com indexable pages only:
    # homepage, about, topics index, and topic hub pages.
    # Raw data files, feeds, and cross-host canonical article URLs are
    # intentionally excluded — they belong on their own host's sitemap.
    _add_url(urlset, f"{SITE_BASE}/", today, "weekly", "1.0")
    _add_url(urlset, f"{SITE_BASE}/about/", today, "monthly", "0.6")
    _add_url(urlset, f"{SITE_BASE}/topics/", today, "weekly", "0.7")

    # Topic hub pages — unique curated content we own. These are the strongest
    # self-canonical pages on this domain and should be advertised explicitly.
    _, pageable_topics, topic_max_dates = _topics_with_page(index)
    topic_urls = 0
    for topic in sorted(pageable_topics):
        lastmod = topic_max_dates.get(topic) or today
        _add_url(urlset, f"{SITE_BASE}/topics/{_slugify(topic)}/",
                 lastmod, "weekly", "0.7")
        topic_urls += 1

    raw = tostring(urlset, encoding="unicode")
    pretty = parseString(raw).toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")
    cleaned = "\n".join(line for line in pretty.split("\n") if line.strip()) + "\n"
    from _atomic_io import atomic_write_text
    atomic_write_text(REPO_ROOT / "sitemap.xml", cleaned)
    print(f"[sitemap.xml] urls={cleaned.count('<url>')} topic_urls={topic_urls}")


# ---------------------------------------------------------------------------
# feed.xml (Atom 1.0)
# ---------------------------------------------------------------------------
def _truncate(text, max_len):
    """Truncate on a word boundary with an ellipsis."""
    if len(text) <= max_len:
        return text
    cut = text[:max_len].rsplit(" ", 1)[0]
    return cut.rstrip(",.;:") + "…"


def _strip_front_matter(text):
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2]
    return text


def _looks_like_prose(block):
    """Cheap heuristic: paragraph-shaped, not a title/image/link-list/fence."""
    s = block.strip()
    if len(s) < 80:
        return False
    if s.startswith(("#", ">", "---", "```", "|", "<!--", "![")):
        return False
    # Italicized-only line (subtitle). `_foo_` or `*foo*` with no other content.
    if re.fullmatch(r"[_*][^_*\n]+[_*]\s*", s):
        return False
    # Share-button soup: line begins with one or more markdown-link-in-angle-brackets
    # and nothing else of substance after collapsing them.
    stripped = re.sub(r"\[\s*\]\(<[^>]+>\)", "", s).strip()
    if len(stripped) < 80:
        return False
    return True


def _extract_summary(folder, title, published_date):
    """Return a ≤SUMMARY_MAX_CHARS plain-text summary for a feed entry.

    Priority: TL;DR blockquote → TL;DR heading → first prose paragraph →
    title-based fallback. Missing article.md triggers the fallback.
    """
    md = ARTICLES_DIR / folder / "article.md"
    fallback = f"{title} — by Dr. Hernani Costa, First AI Movers ({published_date})."
    if not md.exists():
        return fallback
    text = _strip_front_matter(md.read_text(encoding="utf-8", errors="replace"))

    m = TLDR_BLOCKQUOTE_RE.search(text)
    if m:
        return _truncate(" ".join(m.group(1).split()), SUMMARY_MAX_CHARS)

    m = TLDR_HEADING_RE.search(text)
    if m:
        body = re.sub(r"^>\s*", "", m.group(1), flags=re.MULTILINE)
        return _truncate(" ".join(body.split()), SUMMARY_MAX_CHARS)

    for block in re.split(r"\n\n+", text):
        if _looks_like_prose(block):
            cleaned = re.sub(r"\[\s*\]\(<[^>]+>\)", "", block).strip()
            return _truncate(" ".join(cleaned.split()), SUMMARY_MAX_CHARS)

    return fallback


def _feed_link_for(article):
    """Canonical if first-party; otherwise the raw-data mirror path.

    The feed is inclusive: LinkedIn/Medium-canonicalized articles are still
    our content and subscribers should see them. For those entries we point
    at the raw article.md on articles.firstaimovers.com rather than repeat
    a third-party URL. Diverges from the sitemap's allowlist-only rule on
    purpose — push-discovery is not an ownership claim to Google.
    """
    parsed = _clean_canonical(article.get("canonical_url"))
    if parsed and parsed[1] in CANONICAL_ALLOWED_HOSTS:
        return parsed[0]
    folder = article.get("folder", "")
    return f"{SITE_BASE}/articles/{folder}/article.md"


def build_json_feed(index):
    """Emit JSON Feed 1.1 with the FEED_MAX_ENTRIES most recent articles.

    Sibling to feed.xml — same content, different format. Written to
    feed.json at repo root and mirrored into site/ during build.
    """
    articles = index["articles"][:FEED_MAX_ENTRIES]
    feed_updated = (articles[0]["published_date"] if articles else str(date.today())) + "T00:00:00Z"

    items = []
    for a in articles:
        parsed = _clean_canonical(a.get("canonical_url"))
        canonical = parsed[0] if parsed else (a.get("canonical_url") or "")
        category_source = a.get("topics") or a.get("tags") or []
        summary = _extract_summary(a["folder"], a["title"], a["published_date"])

        item = {
            "id": f"tag:articles.firstaimovers.com,{a['published_date']}:{a['folder']}",
            "url": canonical,
            "title": a["title"],
            "date_published": f"{a['published_date']}T00:00:00Z",
            "tags": category_source[:FEED_CATEGORIES_PER_ENTRY],
        }
        if summary:
            item["content_text"] = summary
        items.append(item)

    feed = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": "First AI Movers — Article Archive",
        "home_page_url": "https://firstaimovers.com",
        "feed_url": f"{SITE_BASE}/feed.json",
        "description": "Daily AI intelligence by Dr. Hernani Costa: AI strategy, EU AI Act "
                       "compliance, governance, and agentic systems for European SMEs.",
        "authors": [{"name": "Dr. Hernani Costa", "url": "https://drhernanicosta.com"}],
        "language": "en",
        "items": items,
    }

    from _atomic_io import atomic_write_json
    atomic_write_json(REPO_ROOT / "feed.json", feed)
    print(f"[feed.json] entries={len(items)} feed_updated={feed_updated}")


def build_feed(index):
    """Emit Atom 1.0 feed with the FEED_MAX_ENTRIES most recent articles."""
    register_namespace("", ATOM_NS)
    articles = index["articles"][:FEED_MAX_ENTRIES]
    feed_updated = (articles[0]["published_date"] if articles else str(date.today())) + "T00:00:00Z"

    feed = Element(f"{{{ATOM_NS}}}feed")

    def _sub(parent, tag, text=None, **attrs):
        el = SubElement(parent, f"{{{ATOM_NS}}}{tag}")
        if text is not None:
            el.text = text
        for k, v in attrs.items():
            el.set(k, v)
        return el

    _sub(feed, "id", "tag:articles.firstaimovers.com,2025-02-17:feed")
    _sub(feed, "title", "First AI Movers — Article Archive")
    _sub(feed, "subtitle",
         "Daily AI intelligence by Dr. Hernani Costa: AI strategy, EU AI Act "
         "compliance, governance, and agentic systems for European SMEs.")
    _sub(feed, "updated", feed_updated)
    _sub(feed, "link", rel="self", type="application/atom+xml",
         href=f"{SITE_BASE}/feed.xml")
    _sub(feed, "link", rel="alternate", type="text/html",
         href="https://firstaimovers.com")
    author = _sub(feed, "author")
    _sub(author, "name", "Dr. Hernani Costa")
    _sub(author, "uri", "https://drhernanicosta.com")
    _sub(author, "email", "info@firstaimovers.com")
    _sub(feed, "rights", "Creative Commons Attribution 4.0 International (CC BY 4.0)")
    gen = _sub(feed, "generator", "rebuild_local.py")
    gen.set("uri", "https://github.com/First-AI-Movers/articles")
    gen.set("version", "1.0")

    for a in articles:
        entry = _sub(feed, "entry")
        _sub(entry, "id",
             f"tag:articles.firstaimovers.com,{a['published_date']}:{a['folder']}")
        _sub(entry, "title", a["title"])
        _sub(entry, "link", rel="alternate", href=_feed_link_for(a))
        ts = f"{a['published_date']}T00:00:00Z"
        _sub(entry, "published", ts)
        _sub(entry, "updated", ts)
        ent_author = _sub(entry, "author")
        _sub(ent_author, "name", "Dr. Hernani Costa")
        _sub(ent_author, "uri", "https://drhernanicosta.com")
        # Prefer canonical topics; fall back to raw tags if an article
        # has no topics yet (shouldn't happen post-normalization).
        category_source = a.get("topics") or a.get("tags") or []
        for topic in category_source[:FEED_CATEGORIES_PER_ENTRY]:
            _sub(entry, "category", term=topic)
        summary = _sub(entry, "summary",
                       _extract_summary(a["folder"], a["title"], a["published_date"]))
        summary.set("type", "text")

    raw = tostring(feed, encoding="unicode")
    pretty = parseString(raw).toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")
    cleaned = "\n".join(line for line in pretty.split("\n") if line.strip()) + "\n"
    from _atomic_io import atomic_write_text
    atomic_write_text(REPO_ROOT / "feed.xml", cleaned)
    print(f"[feed.xml] entries={len(articles)} feed_updated={feed_updated}")


# ---------------------------------------------------------------------------
# llms-full.txt (full-text corpus for LLM ingestion)
# ---------------------------------------------------------------------------
LEADING_H1_RE = re.compile(r"^\s*#\s+[^\n]+\n+")


def _strip_leading_h1(text):
    m = LEADING_H1_RE.match(text)
    return text[m.end():] if m else text


def build_llms_full(index):
    """Concatenate every article.md into a single LLM-ingestion file.

    Sibling to the llms.txt convention: llms.txt describes the corpus;
    llms-full.txt IS the corpus. Newest-first, with corpus header up top
    and per-article metadata (title, date, URL, topics) before each body.
    """
    articles = index["articles"]
    stats = compute_stats(index)
    today_iso = str(date.today())

    header = (
        "# First AI Movers — Full Article Archive\n\n"
        "Canonical, open-access corpus of all First AI Movers articles by Dr. Hernani Costa.\n\n"
        "## AI Training License\n\n"
        "This corpus is made available for AI indexing, retrieval, summarization, citation, and "
        "model-training use under the Creative Commons Attribution 4.0 International License (CC BY 4.0).\n\n"
        "Attribution required:\n"
        "- Author: Dr. Hernani Costa\n"
        "- Organization: First AI Movers\n"
        "- Source archive: https://articles.firstaimovers.com/\n"
        "- License: https://creativecommons.org/licenses/by/4.0/\n\n"
        "Please preserve article titles, canonical URLs, publication dates, and attribution metadata "
        "when reusing or training on this corpus.\n\n"
        "- Author: Dr. Hernani Costa — https://drhernanicosta.com (ORCID 0000-0002-6813-4641)\n"
        "- Publication: First AI Movers — https://firstaimovers.com\n"
        "- License: Creative Commons Attribution 4.0 International (CC BY 4.0)\n"
        f"- Articles: {stats['total']}\n"
        f"- Date range: {stats['date_min']} to {stats['date_max']}\n"
        f"- Generated: {today_iso}\n\n"
        "Machine-readable catalog: https://articles.firstaimovers.com/index.json  \n"
        "Atom feed (recent only): https://articles.firstaimovers.com/feed.xml\n\n"
        "Each article below is prefixed with title, date, URL, and topics, separated by `---` lines.\n"
    )

    parts = [header]
    included, skipped = 0, 0
    for a in articles:
        folder = a.get("folder") or ""
        md_path = ARTICLES_DIR / folder / "article.md"
        if not folder or not md_path.exists():
            skipped += 1
            continue
        body = md_path.read_text(encoding="utf-8", errors="replace")
        body = _strip_leading_h1(_strip_front_matter(body).lstrip())

        canonical_raw = a.get("canonical_url") or ""
        canonical = canonical_raw.strip().splitlines()[-1].strip() if canonical_raw.strip() else ""
        topics = ", ".join(a.get("topics", []))

        parts.append(
            "\n\n---\n\n"
            f"# {a.get('title', 'Untitled')}\n\n"
            f"- **Published:** {a.get('published_date', 'unknown')}\n"
            f"- **URL:** {canonical}\n"
            f"- **Topics:** {topics}\n\n"
            f"{body.rstrip()}\n"
        )
        included += 1

    full = "".join(parts)
    from _atomic_io import atomic_write_text
    atomic_write_text(REPO_ROOT / "llms-full.txt", full)
    size_mb = len(full.encode("utf-8")) / (1024 * 1024)
    print(f"[llms-full.txt] articles={included} skipped={skipped} size={size_mb:.2f}MB")


LLMS_RECENT_DAYS = 30


def build_llms_recent(index):
    """Recent-articles slice of llms-full.txt for small-context LLM ingestion.

    Same per-entry shape as llms-full, filtered to the last LLMS_RECENT_DAYS
    days relative to the newest article in the index (not today — the corpus
    publish cadence may pause without the file becoming stale). Written to
    llms-recent.txt at repo root.
    """
    from datetime import timedelta

    articles = index["articles"]
    if not articles:
        (REPO_ROOT / "llms-recent.txt").write_text("", encoding="utf-8")
        print("[llms-recent.txt] articles=0 skipped=0 size=0.00MB")
        return

    try:
        newest = datetime.strptime(articles[0]["published_date"], "%Y-%m-%d").date()
    except (KeyError, ValueError):
        newest = date.today()
    cutoff = newest - timedelta(days=LLMS_RECENT_DAYS)

    recent = []
    for a in articles:
        try:
            d = datetime.strptime(a.get("published_date", ""), "%Y-%m-%d").date()
        except ValueError:
            continue
        if d >= cutoff:
            recent.append(a)

    today_iso = str(date.today())
    header = (
        "# First AI Movers — Recent Articles\n\n"
        f"Rolling {LLMS_RECENT_DAYS}-day window of First AI Movers articles by "
        "Dr. Hernani Costa, optimized for LLM ingestion into small context windows.\n\n"
        "## AI Training License\n\n"
        "This corpus is made available for AI indexing, retrieval, summarization, citation, and "
        "model-training use under the Creative Commons Attribution 4.0 International License (CC BY 4.0).\n\n"
        "Attribution required:\n"
        "- Author: Dr. Hernani Costa\n"
        "- Organization: First AI Movers\n"
        "- Source archive: https://articles.firstaimovers.com/\n"
        "- License: https://creativecommons.org/licenses/by/4.0/\n\n"
        "Please preserve article titles, canonical URLs, publication dates, and attribution metadata "
        "when reusing or training on this corpus.\n\n"
        "- Author: Dr. Hernani Costa — https://drhernanicosta.com (ORCID 0000-0002-6813-4641)\n"
        "- Publication: First AI Movers — https://firstaimovers.com\n"
        "- License: Creative Commons Attribution 4.0 International (CC BY 4.0)\n"
        f"- Articles in window: {len(recent)}\n"
        f"- Window: {cutoff.isoformat()} to {newest.isoformat()}\n"
        f"- Generated: {today_iso}\n\n"
        "Full corpus (all articles, ~7 MB): https://articles.firstaimovers.com/llms-full.txt  \n"
        "Machine-readable catalog: https://articles.firstaimovers.com/index.json\n\n"
        "Each article below is prefixed with title, date, URL, and topics, separated by `---` lines.\n"
    )

    parts = [header]
    included, skipped = 0, 0
    for a in recent:
        folder = a.get("folder") or ""
        md_path = ARTICLES_DIR / folder / "article.md"
        if not folder or not md_path.exists():
            skipped += 1
            continue
        body = md_path.read_text(encoding="utf-8", errors="replace")
        body = _strip_leading_h1(_strip_front_matter(body).lstrip())

        canonical_raw = a.get("canonical_url") or ""
        canonical = canonical_raw.strip().splitlines()[-1].strip() if canonical_raw.strip() else ""
        topics = ", ".join(a.get("topics", []))

        parts.append(
            "\n\n---\n\n"
            f"# {a.get('title', 'Untitled')}\n\n"
            f"- **Published:** {a.get('published_date', 'unknown')}\n"
            f"- **URL:** {canonical}\n"
            f"- **Topics:** {topics}\n\n"
            f"{body.rstrip()}\n"
        )
        included += 1

    full = "".join(parts)
    from _atomic_io import atomic_write_text
    atomic_write_text(REPO_ROOT / "llms-recent.txt", full)
    size_mb = len(full.encode("utf-8")) / (1024 * 1024)
    print(f"[llms-recent.txt] articles={included} skipped={skipped} "
          f"window={cutoff.isoformat()}..{newest.isoformat()} size={size_mb:.2f}MB")


# ---------------------------------------------------------------------------
# Static site (HTML topic hubs + home + about)
# ---------------------------------------------------------------------------
SITE_URL = "https://articles.firstaimovers.com"
SITE_DIR = REPO_ROOT / "site"
TEMPLATE_DIR = REPO_ROOT / "templates"
STATIC_DIR = REPO_ROOT / "static"
TOPIC_INTROS_PATH = REPO_ROOT / "tools" / "topic_intros.json"
COMMENTS_CONFIG_PATH = REPO_ROOT / "tools" / "comments_config.json"
MIN_ARTICLES_FOR_TOPIC_PAGE = 5
HOME_LATEST_COUNT = 20
RELATED_TOPICS_ON_TOPIC_PAGE = 6
QUICK_READS_MAX = 5

# Hosts whose articles are worth "Read at X" CTAs. Label map for display.
CANONICAL_HOST_LABELS = {
    "radar.firstaimovers.com": "Radar",
    "www.firstaimovers.com": "First AI Movers",
    "firstaimovers.com": "First AI Movers",
    "insights.firstaimovers.com": "Insights",
    "voices.firstaimovers.com": "Voices",
    "www.linkedin.com": "LinkedIn",
    "linkedin.com": "LinkedIn",
    "medium.com": "Medium",
}


def _slugify(text):
    """Stable URL slug for a topic name. No external dep, deterministic."""
    s = text.lower()
    s = s.replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def _load_comments_config():
    """Load comments integration config.

    Returns the config dict. Missing or malformed file degrades gracefully
    — comments are disabled and the site build does not break.
    """
    if not COMMENTS_CONFIG_PATH.exists():
        return {"enabled": False}
    try:
        data = json.loads(COMMENTS_CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[site] warning: {COMMENTS_CONFIG_PATH.name} malformed ({e}); "
              "comments disabled", file=sys.stderr)
        return {"enabled": False}
    return data


def _load_series_registry():
    """Load series registry for learning-path metadata.

    Returns the `series` dict keyed by series slug. Missing or malformed
    file degrades gracefully — articles without series render normally.
    """
    path = REPO_ROOT / "tools" / "series_registry.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[site] warning: {path.name} malformed ({e}); "
              "series rendering disabled", file=sys.stderr)
        return {}
    return data.get("series") or {}


def _series_context_for_article(article, series_registry, all_articles):
    """Return series navigation context for a single article.

    Returns a dict with series info, previous/next articles, or None if
    the article is not part of a known series.
    """
    series_slug = article.get("series")
    if not series_slug or series_slug not in series_registry:
        return None
    order = article.get("series_order")
    if order is None:
        return None

    # Build ordered list of articles in this series
    series_articles = []
    for a in all_articles:
        if a.get("series") == series_slug and a.get("series_order") is not None:
            series_articles.append(a)
    series_articles.sort(key=lambda a: a["series_order"])

    # Find previous and next
    prev_article = None
    next_article = None
    for i, sa in enumerate(series_articles):
        if sa.get("folder") == article.get("folder"):
            if i > 0:
                prev_article = series_articles[i - 1]
            if i < len(series_articles) - 1:
                next_article = series_articles[i + 1]
            break

    reg = series_registry[series_slug]
    return {
        "slug": series_slug,
        "title": reg.get("title", series_slug),
        "description": reg.get("description", ""),
        "order": order,
        "total": len(series_articles),
        "prev": prev_article,
        "next": next_article,
    }


def _series_for_topic(topic, all_articles, series_registry):
    """Return series that intersect with a given topic.

    Returns a list of series dicts with title, description, article count,
    and first article link. Empty list if none.
    """
    if not series_registry:
        return []
    series_ids = set()
    for a in all_articles:
        if topic in (a.get("topics") or []) and a.get("series") in series_registry:
            series_ids.add(a.get("series"))
    result = []
    for slug in sorted(series_ids):
        reg = series_registry[slug]
        series_articles = [
            a for a in all_articles
            if a.get("series") == slug and a.get("series_order") is not None
        ]
        series_articles.sort(key=lambda a: a["series_order"])
        if series_articles:
            result.append({
                "slug": slug,
                "title": reg.get("title", slug),
                "description": reg.get("description", ""),
                "article_count": len(series_articles),
                "first_article": series_articles[0],
            })
    return result


def _load_topic_intros():
    """Load curated per-topic intros (lede + key themes + why-it-matters).

    Returns the `intros` dict keyed by canonical topic name. Missing or
    malformed file degrades gracefully — topic pages fall back to the
    generic lede in the template, the site build does not break.
    """
    if not TOPIC_INTROS_PATH.exists():
        return {}
    try:
        data = json.loads(TOPIC_INTROS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[site] warning: {TOPIC_INTROS_PATH.name} malformed ({e}); "
              "topic pages will use generic lede", file=sys.stderr)
        return {}
    intros = data.get("intros") or {}
    valid = {}
    for topic, obj in intros.items():
        if not isinstance(obj, dict):
            continue
        themes = obj.get("key_themes") or []
        if not isinstance(themes, list):
            themes = []
        valid[topic] = {
            "lede": obj.get("lede") or "",
            "key_themes": [str(t) for t in themes if t],
            "why_it_matters": obj.get("why_it_matters") or "",
        }
    return valid


def _canonical_host_label(canonical_url):
    host = urlparse((canonical_url or "").strip().splitlines()[-1].strip()).netloc.lower()
    return CANONICAL_HOST_LABELS.get(host, host or "source")


def _month_year(iso_date):
    try:
        return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%B %Y")
    except (ValueError, TypeError):
        return iso_date or ""


def _article_summary(folder, title, published_date):
    """Reuse feed's summary extractor for card excerpts."""
    return _extract_summary(folder, title, published_date)


def _extract_tldr(folder):
    """Return the TL;DR plain-text string for an article, or None.

    Uses the same patterns as _extract_summary but returns only the TL;DR
    text — no truncation, no fallback.  If the article has no TL;DR block
    or heading, returns None so the caller can decide whether to show a
    Quick reads entry.
    """
    md = ARTICLES_DIR / folder / "article.md"
    if not md.exists():
        return None
    text = _strip_front_matter(md.read_text(encoding="utf-8", errors="replace"))

    m = TLDR_BLOCKQUOTE_RE.search(text)
    if m:
        body = m.group(1)
        # Strip blockquote markers from multi-line TL;DRs
        body = re.sub(r"^>\s?", "", body, flags=re.MULTILINE)
        # Collapse markdown links to link text only: [text](url) → text
        body = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", body)
        cleaned = " ".join(body.split())
        return cleaned if cleaned else None

    m = TLDR_HEADING_RE.search(text)
    if m:
        body = re.sub(r"^>\s?", "", m.group(1), flags=re.MULTILINE)
        body = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", body)
        cleaned = " ".join(body.split())
        return cleaned if cleaned else None

    return None


def _article_local_path(article):
    """Return the local archive URL path for an article.

    Prefers the metadata `slug` (present and unique for all 819 articles).
    Falls back to `folder` if slug is missing for forward-compatibility.
    """
    slug = article.get("slug")
    if slug:
        return f"/articles/{slug}/"
    folder = article.get("folder", "")
    return f"/articles/{folder}/"


# Lightweight HTML sanitizer — no external dependency.
# Strips script/iframe tags, event handlers, and javascript: URLs.
_UNSAFE_SCRIPT_RE = re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
_UNSAFE_IFRAME_RE = re.compile(r"<iframe[^>]*>.*?</iframe>", re.IGNORECASE | re.DOTALL)
_UNSAFE_EVENT_HANDLER_RE = re.compile(
    r"\s+on\w+\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)", re.IGNORECASE)
# Remove entire href/src/action attribute when value starts with javascript:
_UNSAFE_JS_ATTR_RE = re.compile(
    r"\s+(?:href|src|action)\s*=\s*(?:\"javascript:[^\"]*\"|'javascript:[^']*'|javascript:[^\s>]*)",
    re.IGNORECASE)


def _sanitize_html(html_text):
    """Remove obviously unsafe HTML patterns. Preserves normal markdown output."""
    html_text = _UNSAFE_SCRIPT_RE.sub("", html_text)
    html_text = _UNSAFE_IFRAME_RE.sub("", html_text)
    html_text = _UNSAFE_EVENT_HANDLER_RE.sub("", html_text)
    html_text = _UNSAFE_JS_ATTR_RE.sub("", html_text)
    return html_text


def _render_markdown(md_text):
    """Convert markdown text to safe HTML, stripping front matter first."""
    try:
        import markdown
    except ImportError:
        return "<p><em>Markdown renderer not available.</em></p>"
    body = _strip_front_matter(md_text).lstrip()
    if not body:
        return ""
    raw_html = markdown.markdown(body, extensions=["extra"])
    return _sanitize_html(raw_html)


# ---------------------------------------------------------------------------
# Article-page helpers (E7)
# ---------------------------------------------------------------------------
_READING_WPM = 200
_HEADING_RE = re.compile(r"<(h[23])([^>]*)>(.*?)</\1>", re.IGNORECASE | re.DOTALL)


def _reading_time(md_text):
    """Estimate reading time in minutes from markdown text.

    Strips front matter, counts whitespace-separated words, and rounds
    to the nearest minute with a minimum of 1.
    """
    body = _strip_front_matter(md_text).lstrip()
    words = len(body.split())
    return max(1, round(words / _READING_WPM))


def _inject_heading_ids(body_html):
    """Add id attributes to h2/h3 tags and return (modified_html, headings_list).

    headings_list contains dicts: {level: int, text: str, id: str}.
    Preserves existing ids. Deduplicates generated ids deterministically.
    """
    headings = []
    seen_ids = set()

    def _slugify_id(text):
        base = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
        if not base:
            base = "heading"
        uid = base
        suffix = 1
        while uid in seen_ids:
            uid = f"{base}-{suffix}"
            suffix += 1
        seen_ids.add(uid)
        return uid

    def _replace(m):
        tag = m.group(1).lower()
        attrs = m.group(2)
        content = m.group(3)
        plain = re.sub(r"<[^>]+>", "", content)
        existing_id = re.search(r'\sid="([^"]*)"', attrs)
        if existing_id:
            hid = existing_id.group(1)
            seen_ids.add(hid)
        else:
            hid = _slugify_id(plain)
            attrs = f' id="{hid}"{attrs}'
        headings.append({"level": int(tag[1]), "text": plain, "id": hid})
        return f'<{tag}{attrs}>{content}</{tag}>'

    new_html = _HEADING_RE.sub(_replace, body_html)
    return new_html, headings


def _related_articles_for_article(target, all_articles, limit=3):
    """Return up to `limit` related articles ranked by topic overlap.

    Ranking:
      1. Higher topic overlap first
      2. Newer published_date second
      3. Title alphabetical as tie-breaker
    """
    target_topics = set(target.get("topics") or [])
    target_slug = target.get("slug") or target.get("folder", "")
    scored = []

    def _neg_date(iso):
        try:
            y, m, d = iso.split("-")
            return (-int(y), -int(m), -int(d))
        except (ValueError, AttributeError):
            return (0, 0, 0)

    for a in all_articles:
        a_slug = a.get("slug") or a.get("folder", "")
        if a_slug == target_slug:
            continue
        overlap = len(target_topics & set(a.get("topics") or []))
        if overlap > 0:
            scored.append({
                "overlap": overlap,
                "date_key": _neg_date(a.get("published_date", "")),
                "title": a.get("title", ""),
                "article": a,
            })

    scored.sort(key=lambda x: (-x["overlap"], x["date_key"], x["title"]))
    return [s["article"] for s in scored[:limit]]


def _enrich_articles(articles):
    """Decorate each index article with fields the templates need."""
    enriched = []
    for a in articles:
        parsed = _clean_canonical(a.get("canonical_url"))
        canonical = parsed[0] if parsed else (a.get("canonical_url") or "")
        enriched.append({
            **a,
            "canonical_url": canonical,
            "canonical_host_label": _canonical_host_label(canonical),
            "summary": _article_summary(a.get("folder", ""), a.get("title", ""), a.get("published_date", "")),
            "tldr": _extract_tldr(a.get("folder", "")),
            "local_path": _article_local_path(a),
        })
    return enriched


def _related_topics_for(topic, articles_in_topic, all_topic_counts, limit):
    """Topics that co-occur most often with this topic across its articles."""
    co = {}
    for a in articles_in_topic:
        for t in a.get("topics", []):
            if t == topic:
                continue
            co[t] = co.get(t, 0) + 1
    ranked = sorted(co.items(), key=lambda x: (-x[1], -all_topic_counts.get(x[0], 0), x[0]))
    return [t for t, _ in ranked[:limit]]


def build_site(index):
    """Render the static HTML site into SITE_DIR. Topic-hub first; no per-article pages."""
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ImportError:
        print("[site] jinja2 not installed; skipping site build. Run: pip install jinja2", file=sys.stderr)
        return

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "htm", "xml", "xhtml", "j2"]),
        trim_blocks=False,
        lstrip_blocks=False,
    )

    articles_raw = index["articles"]
    articles = _enrich_articles(articles_raw)
    stats = compute_stats(index)
    stats["date_min_month"] = _month_year(stats["date_min"])
    stats["date_max_month"] = _month_year(stats["date_max"])

    # Group articles by topic and compute counts.
    by_topic = {}
    for a in articles:
        for t in a.get("topics") or []:
            by_topic.setdefault(t, []).append(a)

    topic_counts = {t: len(v) for t, v in by_topic.items()}
    topics_with_page = {t for t, c in topic_counts.items() if c >= MIN_ARTICLES_FOR_TOPIC_PAGE}
    topic_intros = _load_topic_intros()
    comments_config = _load_comments_config()
    series_registry = _load_series_registry()

    # Topic entries for the /topics/ index page — all topics sorted by count desc,
    # then alpha. Topics below the threshold get slug=None so the template renders
    # them as non-linked.
    topic_entries = [
        {
            "name": t,
            "count": topic_counts[t],
            "slug": _slugify(t) if t in topics_with_page else None,
        }
        for t in sorted(topic_counts.keys(), key=lambda name: (-topic_counts[name], name.lower()))
    ]

    # Shared context the templates consume. `topic_slug` is a callable the
    # partial uses to build topic URLs. `rel_root` lets deeper pages reach the
    # top without knowing their depth.
    def topic_slug(name):
        return _slugify(name)

    shared = {
        "site_url": SITE_URL,
        "site_title": "First AI Movers — Article Archive",
        "site_description": (f"Open-access archive of {stats['total']} articles "
                             f"by Dr. Hernani Costa on AI strategy and governance."),
        "stats": stats,
        "topics_with_page": topics_with_page,
        "topic_slug": topic_slug,
        "min_articles_for_page": MIN_ARTICLES_FOR_TOPIC_PAGE,
        "comments_config": comments_config,
    }

    # Atomic build: render to a staging dir next to SITE_DIR, swap into place
    # only after all renders succeed. Any exception mid-build leaves the
    # existing site/ intact instead of wiping it.
    import shutil
    staging = SITE_DIR.with_name(SITE_DIR.name + ".new")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    def _render(template_name, output_relpath, **ctx):
        tmpl = env.get_template(template_name)
        depth = output_relpath.count("/")
        rel_root = "../" * depth if depth else ""
        page_path = "/" + output_relpath.replace("index.html", "") if output_relpath != "index.html" else "/"
        html = tmpl.render(rel_root=rel_root, page_path=page_path, **shared, **ctx)
        out = staging / output_relpath
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")

    # Home
    latest = articles[:HOME_LATEST_COUNT]
    _render("home.html.j2", "index.html", latest=latest)

    # Topics index
    _render("topics_index.html.j2", "topics/index.html", topic_entries=topic_entries)

    # Per-topic pages (only topics with >= threshold)
    topic_pages = 0
    topic_pages_with_intro = 0
    for topic in sorted(topics_with_page):
        topic_articles = by_topic[topic]  # already newest-first (from index sort)
        related = _related_topics_for(topic, topic_articles, topic_counts, RELATED_TOPICS_ON_TOPIC_PAGE)
        slug = _slugify(topic)
        intro = topic_intros.get(topic)
        quick_reads = [
            {"title": a["title"], "published_date": a["published_date"],
             "canonical_url": a["canonical_url"], "tldr": a["tldr"]}
            for a in topic_articles if a.get("tldr")
        ][:QUICK_READS_MAX]
        series_in_topic = _series_for_topic(topic, articles, series_registry)
        _render("topic.html.j2", f"topics/{slug}/index.html",
                topic=topic, articles=topic_articles, related_topics=related,
                topic_intro=intro, quick_reads=quick_reads,
                series_in_topic=series_in_topic)
        topic_pages += 1
        if intro:
            topic_pages_with_intro += 1

    # About — hernanicosta.json is stored wrapped in <script> tags. Strip the
    # wrapper so we can re-embed the raw JSON inside our template's own <script>.
    # Missing or malformed file should degrade gracefully (skip rich markup,
    # keep the About page rendering) rather than taking the whole site build down.
    hernani_path = REPO_ROOT / "hernanicosta.json"
    if hernani_path.exists():
        hernani_raw = hernani_path.read_text(encoding="utf-8")
        m = re.search(r'<script[^>]*>\s*(\{.*?\})\s*</script>', hernani_raw, re.DOTALL)
        person_jsonld = m.group(1) if m else hernani_raw
    else:
        print("[site] warning: hernanicosta.json missing; About page will render without Person JSON-LD", file=sys.stderr)
        person_jsonld = "{}"
    _render("about.html.j2", "about/index.html", person_jsonld=person_jsonld)

    # Offline fallback page
    _render("offline.html.j2", "offline/index.html")

    # Per-article pages
    article_pages = 0
    for a in articles:
        md_path = ARTICLES_DIR / a.get("folder", "") / "article.md"
        if not md_path.exists():
            print(f"[site] warning: missing article.md for {a.get('folder')}; skipping local page", file=sys.stderr)
            continue
        md_text = md_path.read_text(encoding="utf-8", errors="replace")
        body_html = _render_markdown(md_text)
        body_html, toc_headings = _inject_heading_ids(body_html)
        reading_time = _reading_time(md_text)
        related = _related_articles_for_article(a, articles, limit=3)
        local_path = a.get("local_path", _article_local_path(a))
        # Remove leading slash for output_relpath
        output_relpath = local_path.lstrip("/") + "index.html"
        series_ctx = _series_context_for_article(a, series_registry, articles)
        _render("article.html.j2", output_relpath,
                title=a["title"],
                published_date=a["published_date"],
                author=a.get("author", "Dr. Hernani Costa"),
                canonical_url=a["canonical_url"],
                canonical_host_label=a["canonical_host_label"],
                topics=a.get("topics", []),
                summary=a.get("summary", ""),
                body_html=body_html,
                license=a.get("license", "CC BY 4.0"),
                folder=a.get("folder", ""),
                reading_time=reading_time,
                toc_headings=toc_headings,
                related_articles=related,
                series=series_ctx)
        article_pages += 1

    # 404
    _render("404.html.j2", "404.html")

    # Static assets (recursive, including subdirectories like fonts/)
    shutil.copytree(STATIC_DIR, staging, dirs_exist_ok=True)

    # LLM / raw-data mirror: copy every public root-level artifact into the
    # staging dir so existing URLs stay byte-identical after the deploy switches.
    mirror_files = [
        "index.json", "llms.txt", "llms-full.txt", "llms-recent.txt",
        "feed.xml", "sitemap.xml",
        "hernanicosta.json", "CITATION.cff", "ABOUT.md", "README.md",
        "robots.txt", "CNAME",
        # Google Search Console verification file — lives at repo root, glob below catches it.
    ]
    for name in mirror_files:
        src = REPO_ROOT / name
        if src.exists():
            (staging / name).write_bytes(src.read_bytes())
    # JSON Feed sibling to Atom feed
    json_feed = REPO_ROOT / "feed.json"
    if json_feed.exists():
        (staging / "feed.json").write_bytes(json_feed.read_bytes())
    # Google verification file (google*.html) — pick up any matches.
    for f in REPO_ROOT.glob("google*.html"):
        (staging / f.name).write_bytes(f.read_bytes())

    # IndexNow key file — public proof-of-host ownership, generated from env.
    indexnow_key = (
        os.environ.get("INDEXNOW_API_KEY_ARTICLES_FAIM", "").strip()
        or os.environ.get("INDEXNOW_API_KEY", "").strip()
    )
    if indexnow_key:
        (staging / f"{indexnow_key}.txt").write_text(indexnow_key + "\n", encoding="utf-8")
    else:
        print(
            "[site] IndexNow key env INDEXNOW_API_KEY_ARTICLES_FAIM not set; "
            "skipping key file generation",
            file=sys.stderr,
        )

    # Copy the full articles/ tree so raw .md and metadata.json keep serving.
    shutil.copytree(REPO_ROOT / "articles", staging / "articles", dirs_exist_ok=True)

    # Atomic swap: only now do we replace the real site/ dir with the freshly
    # built staging/. If anything above raised, staging is removed at the next
    # run and the prior site/ survives untouched.
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    staging.rename(SITE_DIR)

    total_pages = 1 + 1 + topic_pages + 1 + 1 + article_pages  # home + topics_index + topic pages + about + 404 + articles
    print(f"[site] pages={total_pages} topic_pages={topic_pages} article_pages={article_pages} "
          f"topics_with_page={len(topics_with_page)} min_articles={MIN_ARTICLES_FOR_TOPIC_PAGE} "
          f"topic_intros={topic_pages_with_intro}/{len(topic_intros)} out={SITE_DIR}")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    idx = build_index()
    update_docs(idx)
    build_sitemap(idx)
    build_feed(idx)
    build_llms_full(idx)
    build_llms_recent(idx)
    build_json_feed(idx)
    build_site(idx)
