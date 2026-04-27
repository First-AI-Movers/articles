#!/usr/bin/env python3
"""Normalize free-form `tags` to canonical `topics` across every metadata.json.

Reads tools/canonical_topics.json (the authoritative vocabulary) and
tools/tag_aliases.json (patterns + overrides), walks every article's
metadata.json, and writes a `topics` field with the normalized values.
The raw `tags` field is left untouched — it stays as historical keywords
for search and LLM ingestion.

Also normalizes the `first_ai_movers_services` field: strips whitespace,
collapses casing, maps to canonical kebab-case values.

Safe to run repeatedly — idempotent. If a metadata.json already has a
correct `topics` field it will be regenerated to match the current alias
map (so vocabulary changes propagate on re-run).

Usage:
    python3 tools/normalize_tags.py            # write changes to metadata.json
    python3 tools/normalize_tags.py --dry-run  # report coverage, don't write
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from _atomic_io import atomic_write_json

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = REPO_ROOT / "articles"
TOPICS_FILE = Path(__file__).resolve().parent / "canonical_topics.json"
ALIASES_FILE = Path(__file__).resolve().parent / "tag_aliases.json"

MAX_TOPICS_PER_ARTICLE = 6

# Canonical set of service values. Raw values are lowercased + whitespace-
# stripped, then matched against this set.
CANONICAL_SERVICES = {
    "ai-strategy",
    "fractional-caio",
    "automation-design",
    "compliance-audit",
    "ai-literacy-training",
}


def load_aliases():
    topics_data = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
    aliases_data = json.loads(ALIASES_FILE.read_text(encoding="utf-8"))
    canonical = set(topics_data["topics"])

    # Validate: every topic referenced in aliases must exist in canonical_topics.
    bad = []
    for rule in aliases_data["patterns"]:
        for t in rule["topics"]:
            if t not in canonical:
                bad.append(f"pattern {rule['match']!r} -> {t!r}")
    for raw, topics in aliases_data["overrides"].items():
        for t in topics:
            if t not in canonical:
                bad.append(f"override {raw!r} -> {t!r}")
    if bad:
        raise ValueError("Aliases reference unknown canonical topics:\n  " + "\n  ".join(bad))

    return canonical, aliases_data["patterns"], aliases_data["overrides"]


def normalize_tag(raw_tag, patterns, overrides):
    """Return the ordered, deduped list of canonical topics for a raw tag."""
    if raw_tag in overrides:
        return list(dict.fromkeys(overrides[raw_tag]))
    lowered = " " + raw_tag.lower() + " "  # bracket with spaces for word-boundary-ish matches
    out = []
    for rule in patterns:
        if rule["match"].lower() in lowered:
            for topic in rule["topics"]:
                if topic not in out:
                    out.append(topic)
    return out


def normalize_tags_for_article(raw_tags, patterns, overrides):
    """Collect topics across all tags of one article, dedupe, cap."""
    topics = []
    for t in raw_tags or []:
        for topic in normalize_tag(t, patterns, overrides):
            if topic not in topics:
                topics.append(topic)
    return topics[:MAX_TOPICS_PER_ARTICLE]


def normalize_service(raw):
    """Return canonical service slug or None if unrecognized."""
    cleaned = (raw or "").strip().lower().replace(" ", "-")
    return cleaned if cleaned in CANONICAL_SERVICES else None


def normalize_services(raw_list):
    """Clean + dedupe + filter to canonical values. Preserves order."""
    out = []
    for raw in raw_list or []:
        c = normalize_service(raw)
        if c and c not in out:
            out.append(c)
    return out


# String fields where stray whitespace (including the raw newlines the
# 2026-01-21 LinkedIn batch left inside JSON string values) degrades
# downstream output (feed <title>, HTML <h1>, llms-full header).
STRING_FIELDS_TO_CLEAN = ("title", "slug", "canonical_url", "folder")


def _clean_string_field(value):
    """Collapse internal whitespace and strip edges. Safe on non-strings."""
    if not isinstance(value, str):
        return value
    # Strip edges first, then collapse internal whitespace runs to single spaces.
    return " ".join(value.split())


def process_metadata_file(meta_path, patterns, overrides):
    """Update one metadata.json in place. Return (changed, topics, coverage_key)."""
    raw = meta_path.read_text(encoding="utf-8")
    meta = json.loads(raw, strict=False)

    new_topics = normalize_tags_for_article(meta.get("tags", []), patterns, overrides)
    new_services = normalize_services(meta.get("first_ai_movers_services", []))
    cleaned_fields = {
        field: _clean_string_field(meta.get(field))
        for field in STRING_FIELDS_TO_CLEAN
        if field in meta
    }

    changed = (
        meta.get("topics") != new_topics
        or meta.get("first_ai_movers_services") != new_services
        or any(meta.get(f) != v for f, v in cleaned_fields.items())
    )
    meta["topics"] = new_topics
    meta["first_ai_movers_services"] = new_services
    for field, value in cleaned_fields.items():
        meta[field] = value

    if changed:
        atomic_write_json(meta_path, meta)
    return changed, new_topics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Report coverage without writing")
    args = parser.parse_args()

    canonical, patterns, overrides = load_aliases()

    total = 0
    changed = 0
    zero_topic_articles = []
    topic_counter = Counter()
    tags_with_no_match = Counter()

    for meta_path in sorted(ARTICLES_DIR.glob("*/metadata.json")):
        total += 1
        meta = json.loads(meta_path.read_text(encoding="utf-8"), strict=False)
        new_topics = normalize_tags_for_article(meta.get("tags", []), patterns, overrides)

        # Track long-tail tags that produce zero topics (visibility)
        for t in meta.get("tags", []):
            if not normalize_tag(t, patterns, overrides):
                tags_with_no_match[t] += 1

        for topic in new_topics:
            topic_counter[topic] += 1
        if not new_topics:
            zero_topic_articles.append(meta_path.parent.name)

        if not args.dry_run:
            was_changed, _ = process_metadata_file(meta_path, patterns, overrides)
            if was_changed:
                changed += 1

    print(f"Articles processed: {total}")
    print(f"  with at least one topic: {total - len(zero_topic_articles)} "
          f"({100*(total - len(zero_topic_articles))/total:.1f}%)")
    print(f"  with zero topics:        {len(zero_topic_articles)}")
    if not args.dry_run:
        print(f"  metadata.json rewritten: {changed}")

    print(f"\nCanonical topics used: {len(topic_counter)} / {len(canonical)}")
    print(f"Unused canonical topics: {sorted(canonical - set(topic_counter))}")

    print(f"\nTop 25 topics by article count:")
    for topic, count in topic_counter.most_common(25):
        print(f"  {count:4d}  {topic}")

    if tags_with_no_match:
        print(f"\nRaw tags with no canonical match ({len(tags_with_no_match)} unique, "
              f"{sum(tags_with_no_match.values())} total occurrences):")
        print("  Top 20 by frequency:")
        for t, c in tags_with_no_match.most_common(20):
            print(f"    {c:3d}  {t}")


if __name__ == "__main__":
    main()
