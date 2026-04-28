#!/usr/bin/env python3
"""Patch repo docs with current archive stats.

Default mode patches ROADMAP.md via explicit <!-- BEGIN/END auto:... --> markers.
Optional flags patch README.md and llms.txt using regex (same logic as rebuild_local.py).

This tool is additive — rebuild_local.py continues to patch README.md and llms.txt
on its own. Use this script standalone when you want to update docs without a full rebuild.
"""

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def compute_stats(index):
    """Duplicate of rebuild_local.py::compute_stats for standalone use."""
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


def _topic_hub_count(index):
    """Count topics with >= MIN_ARTICLES_FOR_TOPIC_PAGE articles."""
    counts = {}
    for a in index["articles"]:
        for t in a.get("topics", []):
            counts[t] = counts.get(t, 0) + 1
    return sum(1 for c in counts.values() if c >= 5)


def _sitemap_url_count(index):
    """First-party indexable URLs: homepage + about + topics index + topic hubs."""
    return 3 + _topic_hub_count(index)


def _patch_roadmap(content, stats, index):
    marker_begin = "<!-- BEGIN auto:operational-state -->"
    marker_end = "<!-- END auto:operational-state -->"

    if marker_begin not in content or marker_end not in content:
        return content, "skipped (markers missing)"

    total = stats["total"]
    topics = stats["topics_count"]
    hubs = _topic_hub_count(index)
    sitemap_urls = _sitemap_url_count(index)

    new_block = (
        f"{marker_begin}\n"
        f"Operational state today: **{total} articles**, **{topics} canonical topics**, "
        f"**{hubs} rendered topic hubs**, **{total} local noindex article pages**, "
        f"sitemap limited to **{sitemap_urls} first-party indexable URLs**, "
        f"and the current test suite split across Python unit/integration tests plus Playwright E2E.\n"
        f"{marker_end}"
    )

    pattern = re.escape(marker_begin) + r".*?" + re.escape(marker_end)
    new_content = re.sub(pattern, new_block, content, flags=re.DOTALL)
    status = "updated" if new_content != content else "unchanged"
    return new_content, status


def _month_span(date_min, date_max):
    try:
        dt_min = datetime.strptime(date_min, "%Y-%m-%d")
        dt_max = datetime.strptime(date_max, "%Y-%m-%d")
        return f"{dt_min.strftime('%B %Y')}–{dt_max.strftime('%B %Y')}"
    except ValueError:
        return f"{date_min} – {date_max}"


def patch_readme(content, stats):
    """Same regex logic as rebuild_local.py::patch_readme."""
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
    """Same regex logic as rebuild_local.py::patch_llms."""
    content = re.sub(r'\d+ original articles on AI strategy',
                     f"{stats['total']} original articles on AI strategy", content)
    content = re.sub(r'Published [^.]+\.',
                     f"Published {_month_span(stats['date_min'], stats['date_max'])}.", content)
    return content


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


def _load_index():
    path = REPO_ROOT / "index.json"
    if not path.exists():
        raise FileNotFoundError(f"index.json not found at {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Patch repo docs with current archive stats")
    parser.add_argument("--check", action="store_true",
                        help="Exit non-zero if any managed doc would change")
    parser.add_argument("--roadmap-only", action="store_true", help="Patch ROADMAP.md only")
    parser.add_argument("--readme", action="store_true", help="Patch README.md")
    parser.add_argument("--llms", action="store_true", help="Patch llms.txt")
    args = parser.parse_args(argv)

    # Default: roadmap-only unless explicit flags given
    patch_roadmap = args.roadmap_only or not (args.readme or args.llms)
    patch_readme_flag = args.readme
    patch_llms_flag = args.llms

    index = _load_index()
    stats = compute_stats(index)

    changed = False

    if patch_roadmap:
        path = REPO_ROOT / "ROADMAP.md"
        old = path.read_text(encoding="utf-8")
        new, status = _patch_roadmap(old, stats, index)
        if new != old:
            if args.check:
                print(f"[update] ROADMAP.md would change ({status})")
                changed = True
            else:
                path.write_text(new, encoding="utf-8")
                print(f"[update] ROADMAP.md {status}")
        else:
            print(f"[update] ROADMAP.md {status}")

    if patch_readme_flag:
        path = REPO_ROOT / "README.md"
        old = path.read_text(encoding="utf-8")
        new = patch_readme(old, stats)
        if new != old:
            if args.check:
                print(f"[update] README.md would change")
                changed = True
            else:
                path.write_text(new, encoding="utf-8")
                print(f"[update] README.md updated")
        else:
            print(f"[update] README.md unchanged")

    if patch_llms_flag:
        path = REPO_ROOT / "llms.txt"
        old = path.read_text(encoding="utf-8")
        new = patch_llms(old, stats)
        if new != old:
            if args.check:
                print(f"[update] llms.txt would change")
                changed = True
            else:
                path.write_text(new, encoding="utf-8")
                print(f"[update] llms.txt updated")
        else:
            print(f"[update] llms.txt unchanged")

    return 1 if changed else 0


if __name__ == "__main__":
    sys.exit(main())
