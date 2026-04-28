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


def _check_single_h1(body: str) -> dict:
    """Return True if exactly one markdown H1 exists in body."""
    h1s = re.findall(r"^# .+$", body, re.MULTILINE)
    passed = len(h1s) == 1
    return {
        "passed": passed,
        "points": CRITERIA["single_h1"]["points"] if passed else 0,
        "max_points": CRITERIA["single_h1"]["max_points"],
        "detail": f"H1 count: {len(h1s)}",
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


def _check_tldr(body: str) -> dict:
    """Detect TL;DR blockquote or heading."""
    patterns = [
        r">\s*\*\*TL;DR:\*\*",
        r">\s*TL;DR:",
        r"^#{1,3}\s+TL;DR\b",
        r"^#{1,3}\s+TLDR\b",
    ]
    for pat in patterns:
        if re.search(pat, body, re.MULTILINE | re.IGNORECASE):
            return {
                "passed": True,
                "points": CRITERIA["tldr"]["points"],
                "max_points": CRITERIA["tldr"]["max_points"],
                "detail": "TL;DR found",
            }
    return {
        "passed": False,
        "points": 0,
        "max_points": CRITERIA["tldr"]["max_points"],
        "detail": "TL;DR not found",
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
        "single_h1": _check_single_h1(body),
        "heading_hierarchy": _check_heading_hierarchy(body),
        "tldr": _check_tldr(body),
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
