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
import re
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
    (REPO_ROOT / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
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
    for filename, patcher in (("README.md", patch_readme), ("llms.txt", patch_llms)):
        path = REPO_ROOT / filename
        old = path.read_text(encoding="utf-8")
        new = patcher(old, stats)
        if new != old:
            path.write_text(new, encoding="utf-8")
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
    """Return (topic_counts: dict, pageable_topics: set).

    A topic is 'pageable' if it has >= MIN_ARTICLES_FOR_TOPIC_PAGE articles.
    Shared between build_site and build_sitemap so the set of URLs advertised
    to Google matches the set of URLs actually rendered.
    """
    counts = {}
    for a in index.get("articles", []):
        for t in a.get("topics") or []:
            counts[t] = counts.get(t, 0) + 1
    pageable = {t for t, c in counts.items() if c >= MIN_ARTICLES_FOR_TOPIC_PAGE}
    return counts, pageable


def build_sitemap(index):
    today = str(date.today())
    urlset = Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    # articles.firstaimovers.com stays in the sitemap as the raw-data / LLM
    # mirror AND now as the host of topic hub pages. Weekly changefreq for the
    # root (not daily — root is mostly stable).
    _add_url(urlset, f"{SITE_BASE}/", today, "weekly", "1.0")
    _add_url(urlset, f"{SITE_BASE}/about/", today, "monthly", "0.6")
    _add_url(urlset, f"{SITE_BASE}/topics/", today, "weekly", "0.7")
    for path in ("ABOUT.md", "CITATION.cff", "hernanicosta.json", "llms.txt",
                 "llms-full.txt", "llms-recent.txt", "index.json", "feed.xml"):
        _add_url(urlset, f"{SITE_BASE}/{path}", today, "weekly", "0.5")
    _add_url(urlset, f"{SITE_BASE}/README.md", today, "weekly", "0.7")

    # Topic hub pages — unique curated content we own. These are the strongest
    # self-canonical pages on this domain and should be advertised explicitly.
    _, pageable_topics = _topics_with_page(index)
    topic_urls = 0
    for topic in sorted(pageable_topics):
        _add_url(urlset, f"{SITE_BASE}/topics/{_slugify(topic)}/",
                 today, "weekly", "0.7")
        topic_urls += 1

    # Article URLs: emit each article's declared canonical, not a fabricated
    # articles.firstaimovers.com path. The canonical fields point to where
    # the article actually lives (newsletter, radar, insights, voices).
    skipped_external = 0
    skipped_malformed = 0
    emitted = 0
    for article in index["articles"]:
        parsed = _clean_canonical(article.get("canonical_url"))
        if parsed is None:
            skipped_malformed += 1
            continue
        canonical, host = parsed
        if host not in CANONICAL_ALLOWED_HOSTS:
            skipped_external += 1
            continue
        _add_url(urlset, canonical,
                 article.get("published_date") or today, "monthly", "0.8")
        emitted += 1

    raw = tostring(urlset, encoding="unicode")
    pretty = parseString(raw).toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")
    cleaned = "\n".join(line for line in pretty.split("\n") if line.strip()) + "\n"
    (REPO_ROOT / "sitemap.xml").write_text(cleaned, encoding="utf-8")
    print(f"[sitemap.xml] urls={cleaned.count('<url>')} "
          f"article_urls={emitted} topic_urls={topic_urls} "
          f"skipped_external={skipped_external} "
          f"skipped_malformed={skipped_malformed}")


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
    (REPO_ROOT / "feed.xml").write_text(cleaned, encoding="utf-8")
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
    (REPO_ROOT / "llms-full.txt").write_text(full, encoding="utf-8")
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
    (REPO_ROOT / "llms-recent.txt").write_text(full, encoding="utf-8")
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
MIN_ARTICLES_FOR_TOPIC_PAGE = 5
HOME_LATEST_COUNT = 20
RELATED_TOPICS_ON_TOPIC_PAGE = 6

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
        autoescape=select_autoescape(["html", "xml"]),
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

    # Topic narratives — optional intro / key-themes / why-it-matters per
    # topic, sourced from tools/topic_intros.json. Topics without an entry
    # render the list-only fallback. File may be wrapped as
    # {"version": N, "intros": {...}} or flat {"Topic Name": {...}}.
    narratives = {}
    intros_path = REPO_ROOT / "tools" / "topic_intros.json"
    if intros_path.exists():
        try:
            loaded = json.loads(intros_path.read_text(encoding="utf-8"))
            narratives = loaded.get("intros", loaded) if isinstance(loaded, dict) else {}
        except json.JSONDecodeError as e:
            print(f"[site] warning: topic_intros.json invalid JSON: {e}", file=sys.stderr)

    # Per-topic pages (only topics with >= threshold)
    topic_pages = 0
    topics_with_narrative = 0
    for topic in sorted(topics_with_page):
        topic_articles = by_topic[topic]  # already newest-first (from index sort)
        related = _related_topics_for(topic, topic_articles, topic_counts, RELATED_TOPICS_ON_TOPIC_PAGE)
        slug = _slugify(topic)
        narrative = narratives.get(topic)
        if narrative:
            topics_with_narrative += 1
        _render("topic.html.j2", f"topics/{slug}/index.html",
                topic=topic, articles=topic_articles, related_topics=related,
                narrative=narrative)
        topic_pages += 1

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

    # 404
    _render("404.html.j2", "404.html")

    # Static assets
    for static_file in STATIC_DIR.iterdir():
        if static_file.is_file():
            (staging / static_file.name).write_bytes(static_file.read_bytes())

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
    # Google verification file (google*.html) — pick up any matches.
    for f in REPO_ROOT.glob("google*.html"):
        (staging / f.name).write_bytes(f.read_bytes())

    # Copy the full articles/ tree so raw .md and metadata.json keep serving.
    shutil.copytree(REPO_ROOT / "articles", staging / "articles")

    # Atomic swap: only now do we replace the real site/ dir with the freshly
    # built staging/. If anything above raised, staging is removed at the next
    # run and the prior site/ survives untouched.
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    staging.rename(SITE_DIR)

    total_pages = 1 + 1 + topic_pages + 1 + 1  # home + topics_index + topic pages + about + 404
    print(f"[site] pages={total_pages} topic_pages={topic_pages} "
          f"topics_with_page={len(topics_with_page)} "
          f"topics_with_narrative={topics_with_narrative} "
          f"min_articles={MIN_ARTICLES_FOR_TOPIC_PAGE} "
          f"out={SITE_DIR}")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    idx = build_index()
    update_docs(idx)
    build_sitemap(idx)
    build_feed(idx)
    build_llms_full(idx)
    build_llms_recent(idx)
    build_site(idx)
