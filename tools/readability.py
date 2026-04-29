#!/usr/bin/env python3
"""Readability audit: per-article Flesch-Kincaid scoring.

Computes deterministic readability metrics for every archived article.
Does not edit article content.

Usage:
    python3 tools/readability.py
    python3 tools/readability.py --articles-dir articles --json-out readability_report.json --md-out readability_report.md
    python3 tools/readability.py --min-reading-ease 40 --fail-on-threshold
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def _strip_front_matter(text: str) -> str:
    """Remove YAML front matter from markdown text."""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].lstrip("\n")
    return text


def _strip_markdown(text: str) -> str:
    """Remove markdown formatting to leave plain prose."""
    # Code blocks
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", "", text)
    # Images
    text = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", r"\1", text)
    # Links — keep link text, drop URL
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Bare URLs
    text = re.sub(r"https?://[^\s\)\]>]+", "", text)
    # Headings — keep the text, drop the # marks
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Bold/italic markers
    text = re.sub(r"\*\*([^\*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^\*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)
    # Blockquote markers
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    # Horizontal rules
    text = re.sub(r"^---+$", "", text, flags=re.MULTILINE)
    # List markers
    text = re.sub(r"^[\*\-\+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)
    # HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    return text


def _count_syllables(word: str) -> int:
    """Heuristic syllable counter for English words."""
    word = word.lower().strip(".,!?;:'\"")
    if not word:
        return 0
    # Handle common silent-e endings
    if word.endswith("e"):
        # Keep e if word ends in -le and consonant before l
        if len(word) > 2 and word[-2] == "l" and word[-3] not in "aeiou":
            pass  # keep the e
        else:
            word = word[:-1]
    if not word:
        return 1
    # Count vowel groups
    vowels = "aeiouy"
    count = 0
    prev_is_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_is_vowel:
            count += 1
        prev_is_vowel = is_vowel
    return max(count, 1)


def _analyze_text(text: str) -> dict:
    """Compute readability metrics from plain text."""
    # Sentence splitting — simplistic but deterministic
    sentences = re.split(r"[.!?]+\s+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = len(sentences)

    words = re.findall(r"\b[a-zA-Z']+\b", text)
    word_count = len(words)
    syllable_count = sum(_count_syllables(w) for w in words)

    avg_sentence_length = word_count / sentence_count if sentence_count else 0.0
    avg_syllables_per_word = syllable_count / word_count if word_count else 0.0

    # Flesch Reading Ease
    if sentence_count and word_count:
        flesch_reading_ease = (
            206.835
            - 1.015 * (word_count / sentence_count)
            - 84.6 * (syllable_count / word_count)
        )
    else:
        flesch_reading_ease = 0.0

    # Flesch-Kincaid Grade Level
    if sentence_count and word_count:
        flesch_kincaid_grade = (
            0.39 * (word_count / sentence_count)
            + 11.8 * (syllable_count / word_count)
            - 15.59
        )
    else:
        flesch_kincaid_grade = 0.0

    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "syllable_count": syllable_count,
        "avg_sentence_length": round(avg_sentence_length, 2),
        "avg_syllables_per_word": round(avg_syllables_per_word, 2),
        "flesch_reading_ease": round(flesch_reading_ease, 2),
        "flesch_kincaid_grade": round(flesch_kincaid_grade, 2),
    }


def _score_article(folder: Path, body_raw: str, meta: dict) -> dict:
    """Compute readability for a single article."""
    body = _strip_front_matter(body_raw)
    plain = _strip_markdown(body)
    metrics = _analyze_text(plain)
    return {
        "folder": folder.name,
        "slug": meta.get("slug", folder.name),
        "title": meta.get("title", ""),
        "published_date": meta.get("published_date", ""),
        **metrics,
    }


def _build_json_report(results: list, min_ease: float, max_grade: float) -> dict:
    scores = [r["flesch_reading_ease"] for r in results]
    grades = [r["flesch_kincaid_grade"] for r in results]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "article_count": len(results),
        "thresholds": {
            "min_reading_ease": min_ease,
            "max_grade": max_grade,
        },
        "summary": {
            "avg_reading_ease": round(sum(scores) / len(scores), 2) if scores else 0.0,
            "avg_grade": round(sum(grades) / len(grades), 2) if grades else 0.0,
            "min_reading_ease": round(min(scores), 2) if scores else 0.0,
            "max_reading_ease": round(max(scores), 2) if scores else 0.0,
            "min_grade": round(min(grades), 2) if grades else 0.0,
            "max_grade": round(max(grades), 2) if grades else 0.0,
            "below_ease_threshold": sum(
                1 for r in results if r["flesch_reading_ease"] < min_ease
            ),
            "above_grade_threshold": sum(
                1 for r in results if r["flesch_kincaid_grade"] > max_grade
            ),
        },
        "articles": results,
    }


def _build_md_report(report: dict) -> str:
    s = report["summary"]
    t = report["thresholds"]
    lines = [
        "# Readability Report",
        "",
        f"Generated: {report['generated_at']}",
        f"Articles audited: {report['article_count']}",
        "",
        "## Executive Summary",
        "",
        f"- **Average Flesch Reading Ease:** {s['avg_reading_ease']}",
        f"- **Average Flesch-Kincaid Grade:** {s['avg_grade']}",
        f"- **Reading Ease range:** {s['min_reading_ease']} – {s['max_reading_ease']}",
        f"- **Grade range:** {s['min_grade']} – {s['max_grade']}",
        f"- **Below ease threshold ({t['min_reading_ease']}):** {s['below_ease_threshold']}",
        f"- **Above grade threshold ({t['max_grade']}):** {s['above_grade_threshold']}",
        "",
        "## Hardest-to-Read Articles (top 20 by grade level)",
        "",
        "| # | Article | Grade | Ease | Words |",
        "|---|---|:---:|:---:|:---:|",
    ]
    hardest = sorted(
        report["articles"],
        key=lambda x: (-x["flesch_kincaid_grade"], -x["avg_sentence_length"]),
    )[:20]
    for i, a in enumerate(hardest, 1):
        lines.append(
            f"| {i} | {a['title']} | {a['flesch_kincaid_grade']} | {a['flesch_reading_ease']} | {a['word_count']} |"
        )
    lines += [
        "",
        "## Articles Over Threshold",
        "",
    ]
    over = [
        a
        for a in report["articles"]
        if a["flesch_reading_ease"] < t["min_reading_ease"]
        or a["flesch_kincaid_grade"] > t["max_grade"]
    ]
    if over:
        lines.append("| Article | Ease | Grade | Reason |")
        lines.append("|---|---|---|---|")
        for a in sorted(over, key=lambda x: x["flesch_kincaid_grade"], reverse=True):
            reasons = []
            if a["flesch_reading_ease"] < t["min_reading_ease"]:
                reasons.append("low ease")
            if a["flesch_kincaid_grade"] > t["max_grade"]:
                reasons.append("high grade")
            lines.append(
                f"| {a['title']} | {a['flesch_reading_ease']} | {a['flesch_kincaid_grade']} | {', '.join(reasons)} |"
            )
    else:
        lines.append("No articles exceed the current thresholds.")
    lines += [
        "",
        "> **Note:** This report is diagnostic. It does not change article content.",
        "> Run `python3 tools/readability.py` locally to refresh after content changes.",
        "",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Readability audit: Flesch-Kincaid scoring per article"
    )
    parser.add_argument(
        "--articles-dir", default="articles", help="Directory containing article folders"
    )
    parser.add_argument(
        "--json-out", default="readability_report.json", help="JSON report path"
    )
    parser.add_argument(
        "--md-out", default="readability_report.md", help="Markdown report path"
    )
    parser.add_argument(
        "--min-reading-ease",
        type=float,
        default=30.0,
        help="Minimum acceptable Flesch Reading Ease (default: 30)",
    )
    parser.add_argument(
        "--max-grade",
        type=float,
        default=18.0,
        help="Maximum acceptable Flesch-Kincaid grade level (default: 18)",
    )
    parser.add_argument(
        "--fail-on-threshold",
        action="store_true",
        help="Exit non-zero if any article exceeds thresholds",
    )
    args = parser.parse_args(argv)

    articles_dir = Path(args.articles_dir)
    if not articles_dir.is_dir():
        print(f"[readability] ERROR: {articles_dir} is not a directory", file=sys.stderr)
        return 1

    results = []
    for folder in sorted(articles_dir.iterdir()):
        if not folder.is_dir():
            continue
        article_path = folder / "article.md"
        meta_path = folder / "metadata.json"
        if not article_path.exists() or not meta_path.exists():
            continue
        body = article_path.read_text(encoding="utf-8")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        results.append(_score_article(folder, body, meta))

    if not results:
        print("[readability] No articles found.", file=sys.stderr)
        return 0

    report = _build_json_report(results, args.min_reading_ease, args.max_grade)
    Path(args.json_out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    Path(args.md_out).write_text(_build_md_report(report), encoding="utf-8")

    over = [
        r
        for r in results
        if r["flesch_reading_ease"] < args.min_reading_ease
        or r["flesch_kincaid_grade"] > args.max_grade
    ]
    print(f"[readability] {len(results)} articles audited")
    print(f"[readability] Avg Reading Ease: {report['summary']['avg_reading_ease']}")
    print(f"[readability] Avg Grade: {report['summary']['avg_grade']}")
    print(f"[readability] Below ease threshold ({args.min_reading_ease}): {report['summary']['below_ease_threshold']}")
    print(f"[readability] Above grade threshold ({args.max_grade}): {report['summary']['above_grade_threshold']}")
    print(f"[readability] JSON: {args.json_out}")
    print(f"[readability] MD:   {args.md_out}")

    if args.fail_on_threshold and over:
        print(
            f"[readability] FAIL: {len(over)} article(s) exceed threshold(s)",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
