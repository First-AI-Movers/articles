#!/usr/bin/env python3
"""GEO audit: per-article AI-citation friendliness scoring.

Generates deterministic, local, non-LLM scores for every archived article
based on structural signals that search/answer engines favour.

Usage:
    python3 tools/geo_audit.py
    python3 tools/geo_audit.py --articles-dir articles --json-out geo_audit_report.json --md-out geo_audit_report.md
    python3 tools/geo_audit.py --min-score 70 --fail-below-threshold
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Internal domains whose links do not count as outbound sources
INTERNAL_DOMAINS = {
    "articles.firstaimovers.com",
    "radar.firstaimovers.com",
    "firstaimovers.com",
    "www.firstaimovers.com",
    "insights.firstaimovers.com",
    "voices.firstaimovers.com",
    "drhernanicosta.com",
}

CRITERIA = {
    "single_h1": {"label": "Single H1 present", "points": 20, "max_points": 20},
    "heading_hierarchy": {"label": "Sequential heading hierarchy", "points": 20, "max_points": 20},
    "tldr": {"label": "TL;DR present", "points": 20, "max_points": 20},
    "outbound_source": {"label": "Outbound source link", "points": 15, "max_points": 15},
    "numeric_signal": {"label": "Numerical/statistical signal", "points": 15, "max_points": 15},
    "metadata": {"label": "Metadata completeness", "points": 10, "max_points": 10},
}


def _strip_front_matter(text: str) -> str:
    """Remove YAML front matter from markdown text."""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].lstrip("\n")
    return text


def _check_single_h1(body: str, meta: dict | None = None) -> dict:
    """Check that the rendered article page will have exactly one ``<h1>``.

    The site template (``templates/article.html.j2``) renders the article
    page with ``<h1>{{ title }}</h1>`` taken from ``metadata.json::title``.
    The Markdown body itself often does NOT carry a ``# Heading`` line
    because the title is supplied via metadata + Jinja. The previous
    revision of this check searched only the Markdown body for ``^# `` and
    therefore false-positive-failed any article that relied on the
    template-rendered H1 — which is the majority of the corpus.

    Pass paths:

    - Markdown body has exactly one ``# `` H1 → pass (legacy contract).
    - Markdown body has zero H1 lines AND ``meta.title`` is non-empty →
      pass (rendered ``<h1>`` is emitted from metadata by the template).

    Fail paths:

    - Zero Markdown H1 lines and metadata title missing/empty.
    - More than one Markdown H1 line (the template's metadata-rendered
      ``<h1>`` would compound with the body H1s and break the
      "single H1 per page" invariant). Metadata title presence does not
      rescue a >1 case.

    Detail string distinguishes which path was used so the GEO audit
    report stays diagnostic.
    """
    h1s = re.findall(r"^# .+$", body, re.MULTILINE)
    h1_count = len(h1s)
    title = ((meta or {}).get("title") or "").strip()
    max_points = CRITERIA["single_h1"]["max_points"]
    points = CRITERIA["single_h1"]["points"]

    if h1_count == 1:
        return {
            "passed": True,
            "points": points,
            "max_points": max_points,
            "detail": "Markdown H1 count: 1",
        }
    if h1_count == 0 and title:
        return {
            "passed": True,
            "points": points,
            "max_points": max_points,
            "detail": "Markdown H1 count: 0; metadata title renders H1",
        }
    if h1_count == 0:
        return {
            "passed": False,
            "points": 0,
            "max_points": max_points,
            "detail": "Markdown H1 count: 0; metadata title missing",
        }
    return {
        "passed": False,
        "points": 0,
        "max_points": max_points,
        "detail": f"Markdown H1 count: {h1_count}",
    }


def _check_heading_hierarchy(body: str) -> dict:
    """Detect heading level jumps (e.g., h2 -> h4 without h3)."""
    headings = re.findall(r"^(#{1,6}) .+$", body, re.MULTILINE)
    levels = [len(h) for h in headings]
    if not levels:
        # No headings at all — not a violation, but not full credit either
        return {
            "passed": True,
            "points": 10,
            "max_points": CRITERIA["heading_hierarchy"]["max_points"],
            "detail": "No subheadings found; partial credit",
        }
    violations = 0
    for i in range(1, len(levels)):
        if levels[i] > levels[i - 1] + 1:
            violations += 1
    passed = violations == 0
    return {
        "passed": passed,
        "points": CRITERIA["heading_hierarchy"]["points"] if passed else 0,
        "max_points": CRITERIA["heading_hierarchy"]["max_points"],
        "detail": f"{len(headings)} headings, {violations} jump violation(s)",
    }


def _check_tldr(body: str, meta: dict | None = None) -> dict:
    """Check whether the rendered article surfaces a TL;DR for AI extraction.

    Pass paths:

    - Markdown body contains one of the documented TL;DR markers
      (``> **TL;DR:**``, ``> TL;DR:``, ``# TL;DR`` / ``# TLDR``, etc.) →
      legacy contract; pass with detail ``"TL;DR found in body"``.
    - Body has no marker AND ``meta.summary_short`` is a non-empty string
      (after ``.strip()``) → pass with detail
      ``"TL;DR via metadata.summary_short"``. The site renderer surfaces
      ``summary_short`` via JSON-LD ``description``, ``llms-index.txt``,
      ``llms-full.txt`` per-article headers, and (downstream) feed
      summaries — so a reviewed ``summary_short`` is functionally a
      TL;DR for AI consumers, even when the body lacks an inline marker.

    Fail path:

    - No body marker AND no usable metadata summary → fail with detail
      ``"TL;DR not found in body or metadata"``.

    Mirrors the metadata-aware ``_check_single_h1`` pattern introduced in
    PR #217: the audit measures what AI consumers actually see rendered,
    not just the raw Markdown.
    """
    patterns = [
        r">\s*\*\*TL;DR:\*\*",
        r">\s*TL;DR:",
        r"^#{1,3}\s+TL;DR\b",
        r"^#{1,3}\s+TLDR\b",
    ]
    max_points = CRITERIA["tldr"]["max_points"]
    points = CRITERIA["tldr"]["points"]
    for pat in patterns:
        if re.search(pat, body, re.MULTILINE | re.IGNORECASE):
            return {
                "passed": True,
                "points": points,
                "max_points": max_points,
                "detail": "TL;DR found in body",
            }
    summary_short = ((meta or {}).get("summary_short") or "")
    if isinstance(summary_short, str) and summary_short.strip():
        return {
            "passed": True,
            "points": points,
            "max_points": max_points,
            "detail": "TL;DR via metadata.summary_short",
        }
    return {
        "passed": False,
        "points": 0,
        "max_points": max_points,
        "detail": "TL;DR not found in body or metadata",
    }


def _check_outbound_source(body: str) -> dict:
    """Count external HTTP(S) links excluding internal domains and mailto."""
    # Match markdown links [text](url) and bare URLs
    md_links = re.findall(r'\[([^\]]*)\]\((https?://[^\)]+)\)', body)
    bare_urls = re.findall(r'(?<![\("\'])https?://[^\s\)\]>]+', body)
    all_urls = [url for _, url in md_links] + bare_urls

    external = 0
    for url in all_urls:
        if url.startswith("mailto:"):
            continue
        try:
            from urllib.parse import urlparse
            netloc = urlparse(url).netloc.lower()
            if netloc and not any(netloc == d or netloc.endswith("." + d) for d in INTERNAL_DOMAINS):
                external += 1
        except Exception:
            continue

    passed = external >= 1
    return {
        "passed": passed,
        "points": CRITERIA["outbound_source"]["points"] if passed else 0,
        "max_points": CRITERIA["outbound_source"]["max_points"],
        "detail": f"External links: {external}",
    }


def _check_numeric_signal(body: str) -> dict:
    """Detect at least one percentage, number with unit/scale, or monetary value."""
    patterns = [
        r"\b\d+(?:\.\d+)?%",                       # 42%
        r"\b\d+(?:\.\d+)?\s*(million|billion|trillion|k|K|M|B|T)\b",  # 10 million
        r"\b\d+(?:\.\d+)?x\b",                       # 3.5x
        r"[\$€£]\s*\d+(?:\.\d+)?(?:\s*[KMBT])?\b",  # $1.2M, €500
        r"\b\d{1,3}(?:,\d{3})+\b",                   # 17,000
    ]
    for pat in patterns:
        if re.search(pat, body, re.IGNORECASE):
            return {
                "passed": True,
                "points": CRITERIA["numeric_signal"]["points"],
                "max_points": CRITERIA["numeric_signal"]["max_points"],
                "detail": "Numerical signal found",
            }
    return {
        "passed": False,
        "points": 0,
        "max_points": CRITERIA["numeric_signal"]["max_points"],
        "detail": "No numerical signal found",
    }


def _check_metadata(meta: dict) -> dict:
    """Check required metadata fields are present and non-empty."""
    required = ["title", "published_date", "canonical_url"]
    optional = ["tags", "author", "author_url", "company", "company_url", "license", "word_count", "read_time_minutes"]
    score = 0
    checks = []
    for field in required:
        val = meta.get(field)
        ok = val is not None and str(val).strip() != ""
        checks.append((field, ok, True))
        if ok:
            score += 2
    for field in optional:
        val = meta.get(field)
        ok = val is not None and str(val).strip() != ""
        checks.append((field, ok, False))
        if ok:
            score += 1
    # Cap at max points
    max_points = CRITERIA["metadata"]["max_points"]
    points = min(score, max_points)
    passed = points >= max_points * 0.7  # at least 70% of metadata points
    detail = ", ".join(f"{f}={'✓' if ok else '✗'}" for f, ok, req in checks)
    return {
        "passed": passed,
        "points": points,
        "max_points": max_points,
        "detail": detail,
    }


def _score_article(folder: Path, body: str, meta: dict) -> dict:
    """Run all checks and return scored result."""
    checks = {
        "single_h1": _check_single_h1(body, meta),
        "heading_hierarchy": _check_heading_hierarchy(body),
        "tldr": _check_tldr(body, meta),
        "outbound_source": _check_outbound_source(body),
        "numeric_signal": _check_numeric_signal(body),
        "metadata": _check_metadata(meta),
    }
    total = sum(c["points"] for c in checks.values())
    if total >= 80:
        status = "pass"
    elif total >= 60:
        status = "warn"
    else:
        status = "fail"
    return {
        "folder": folder.name,
        "slug": meta.get("slug", folder.name),
        "title": meta.get("title", ""),
        "published_date": meta.get("published_date", ""),
        "score": total,
        "status": status,
        "checks": checks,
    }


def _build_json_report(results: list, threshold: int) -> dict:
    scores = [r["score"] for r in results]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "article_count": len(results),
        "average_score": round(sum(scores) / len(scores), 1) if scores else 0.0,
        "min_score": min(scores) if scores else 0,
        "max_score": max(scores) if scores else 0,
        "threshold": threshold,
        "criteria": CRITERIA,
        "summary": {
            "pass_count": sum(1 for r in results if r["status"] == "pass"),
            "warn_count": sum(1 for r in results if r["status"] == "warn"),
            "fail_count": sum(1 for r in results if r["status"] == "fail"),
        },
        "articles": results,
    }


def _build_md_report(report: dict) -> str:
    s = report["summary"]
    lines = [
        "# GEO Audit Report",
        "",
        f"Generated: {report['generated_at']}",
        f"Articles audited: {report['article_count']}",
        "",
        "## Executive Summary",
        "",
        f"- **Average score:** {report['average_score']} / 100",
        f"- **Min score:** {report['min_score']}",
        f"- **Max score:** {report['max_score']}",
        f"- **Pass (≥80):** {s['pass_count']}",
        f"- **Warn (60–79):** {s['warn_count']}",
        f"- **Fail (<60):** {s['fail_count']}",
        "",
        "## Criteria",
        "",
        "| Criterion | Max Points |",
        "|---|---|",
    ]
    for key, info in report["criteria"].items():
        lines.append(f"| {info['label']} | {info['max_points']} |")
    lines += [
        "",
        "## Weakest Articles",
        "",
        "| # | Article | Score | Status |",
        "|---|---|:---:|:---:|",
    ]
    weakest = sorted(report["articles"], key=lambda x: x["score"])[:10]
    for i, a in enumerate(weakest, 1):
        lines.append(f"| {i} | {a['title']} | {a['score']} | {a['status']} |")
    lines += [
        "",
        "## Recurring Missing Checks",
        "",
    ]
    missing = {}
    for a in report["articles"]:
        for key, check in a["checks"].items():
            if not check["passed"]:
                missing[key] = missing.get(key, 0) + 1
    if missing:
        lines.append("| Check | Missing Count |")
        lines.append("|---|---|")
        for key, count in sorted(missing.items(), key=lambda x: -x[1]):
            label = report["criteria"][key]["label"]
            lines.append(f"| {label} | {count} |")
    else:
        lines.append("All checks passed on all articles.")
    lines += [
        "",
        "> **Note:** This report is diagnostic. It does not change article content.",
        "> Run `python3 tools/geo_audit.py` locally to refresh after content changes.",
        "",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="GEO audit: AI-citation friendliness scoring")
    parser.add_argument("--articles-dir", default="articles", help="Directory containing article folders")
    parser.add_argument("--json-out", default="geo_audit_report.json", help="JSON report path")
    parser.add_argument("--md-out", default="geo_audit_report.md", help="Markdown report path")
    parser.add_argument("--min-score", type=int, default=70, help="Threshold for soft-gate messaging")
    parser.add_argument("--fail-below-threshold", action="store_true", help="Exit non-zero if any article is below threshold")
    args = parser.parse_args(argv)

    articles_dir = Path(args.articles_dir)
    if not articles_dir.is_dir():
        print(f"[geo-audit] ERROR: {articles_dir} is not a directory", file=sys.stderr)
        return 1

    results = []
    for folder in sorted(articles_dir.iterdir()):
        if not folder.is_dir():
            continue
        article_path = folder / "article.md"
        meta_path = folder / "metadata.json"
        if not article_path.exists() or not meta_path.exists():
            continue
        body = _strip_front_matter(article_path.read_text(encoding="utf-8"))
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        results.append(_score_article(folder, body, meta))

    if not results:
        print("[geo-audit] No articles found.", file=sys.stderr)
        return 0

    report = _build_json_report(results, args.min_score)
    Path(args.json_out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    Path(args.md_out).write_text(_build_md_report(report), encoding="utf-8")

    below = [r for r in results if r["score"] < args.min_score]
    print(f"[geo-audit] {len(results)} articles audited")
    print(f"[geo-audit] Average score: {report['average_score']}")
    print(f"[geo-audit] Below threshold ({args.min_score}): {len(below)}")
    print(f"[geo-audit] JSON: {args.json_out}")
    print(f"[geo-audit] MD:   {args.md_out}")

    if args.fail_below_threshold and below:
        print(f"[geo-audit] FAIL: {len(below)} article(s) below threshold", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
