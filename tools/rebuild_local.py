#!/usr/bin/env python3
"""Rebuild index.json, sitemap.xml, README.md, and llms.txt from the local
working tree.

Designed to run inside CI (GitHub Actions) immediately after the Make.com
pipeline pushes new article folders. Reads every articles/*/metadata.json
on disk, regenerates the four derived artifacts in place, and exits 0 even
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
from xml.dom.minidom import parseString
from xml.etree.ElementTree import Element, SubElement, tostring

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = REPO_ROOT / "articles"
SITE_BASE = "https://articles.firstaimovers.com"


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


def build_sitemap(index):
    today = str(date.today())
    urlset = Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    _add_url(urlset, f"{SITE_BASE}/", today, "daily", "1.0")
    for path in ("ABOUT.md", "CITATION.cff", "hernanicosta.json", "llms.txt", "index.json"):
        _add_url(urlset, f"{SITE_BASE}/{path}", today, "weekly", "0.5")
    _add_url(urlset, f"{SITE_BASE}/README.md", today, "weekly", "0.7")
    for article in index["articles"]:
        folder = article.get("folder", "")
        if not folder:
            continue
        _add_url(urlset, f"{SITE_BASE}/articles/{folder}/",
                 article.get("published_date") or today, "monthly", "0.8")

    raw = tostring(urlset, encoding="unicode")
    pretty = parseString(raw).toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")
    cleaned = "\n".join(line for line in pretty.split("\n") if line.strip()) + "\n"
    (REPO_ROOT / "sitemap.xml").write_text(cleaned, encoding="utf-8")
    print(f"[sitemap.xml] urls={cleaned.count('<url>')}")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    idx = build_index()
    update_docs(idx)
    build_sitemap(idx)
