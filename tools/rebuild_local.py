#!/usr/bin/env python3
"""Rebuild index.json, sitemap.xml, feed.xml, README.md, and llms.txt from
the local working tree.

Designed to run inside CI (GitHub Actions) immediately after the Make.com
pipeline pushes new article folders. Reads every articles/*/metadata.json
on disk, regenerates the five derived artifacts in place, and exits 0 even
if nothing changed.

Differs from rebuild_index.py / update_docs.py / generate_sitemap.py: those
fetch from and push to the GitHub Contents API. This one operates on the
checked-out working tree, so the calling workflow can commit + push through
normal git.

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
    tags, funnel, dates = set(), {}, []
    for a in articles:
        tags.update(a.get("tags", []))
        funnel[a.get("funnel_stage", "unknown")] = funnel.get(a.get("funnel_stage", "unknown"), 0) + 1
        if a.get("published_date"):
            dates.append(a["published_date"])
    dates.sort()
    return {
        "total": len(articles),
        "tags_count": len(tags),
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
    total, tags = stats["total"], stats["tags_count"]
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
    content = re.sub(r'\*\*[\d,]+\*\* unique topic tags',
                     f"**{tags:,}** unique topic tags", content)
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
    print(f"[docs] total={stats['total']} tags={stats['tags_count']} "
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


def build_sitemap(index):
    today = str(date.today())
    urlset = Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    # articles.firstaimovers.com stays in the sitemap as the raw-data / LLM
    # mirror: index.json, llms.txt, feed.xml, ABOUT.md, etc. really do live
    # there.
    _add_url(urlset, f"{SITE_BASE}/", today, "daily", "1.0")
    for path in ("ABOUT.md", "CITATION.cff", "hernanicosta.json", "llms.txt",
                 "index.json", "feed.xml"):
        _add_url(urlset, f"{SITE_BASE}/{path}", today, "weekly", "0.5")
    _add_url(urlset, f"{SITE_BASE}/README.md", today, "weekly", "0.7")

    # Article URLs: emit each article's declared canonical, not a fabricated
    # articles.firstaimovers.com path. The repo has no static-site renderer,
    # so /articles/<folder>/ paths 404. The canonical fields point to where
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
          f"article_urls={emitted} "
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
        for tag in (a.get("tags") or [])[:FEED_CATEGORIES_PER_ENTRY]:
            _sub(entry, "category", term=tag)
        summary = _sub(entry, "summary",
                       _extract_summary(a["folder"], a["title"], a["published_date"]))
        summary.set("type", "text")

    raw = tostring(feed, encoding="unicode")
    pretty = parseString(raw).toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")
    cleaned = "\n".join(line for line in pretty.split("\n") if line.strip()) + "\n"
    (REPO_ROOT / "feed.xml").write_text(cleaned, encoding="utf-8")
    print(f"[feed.xml] entries={len(articles)} feed_updated={feed_updated}")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    idx = build_index()
    update_docs(idx)
    build_sitemap(idx)
    build_feed(idx)
