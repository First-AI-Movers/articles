#!/usr/bin/env python3
"""Export article archive data into Worker-friendly JSON for the MCP server.

Usage:
    python3 tools/export_mcp_data.py
    python3 tools/export_mcp_data.py --check
    python3 tools/export_mcp_data.py --out-dir mcp-server/src/generated
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import pyarrow.parquet as pq
except ModuleNotFoundError:  # pragma: no cover
    print(
        "[export-mcp-data] Missing dependency: pyarrow\n"
        "Install with: pip install pyarrow",
        file=sys.stderr,
    )
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = REPO_ROOT / "index.json"
EMBEDDINGS_PATH = REPO_ROOT / "embeddings.parquet"
DEFAULT_OUT_DIR = REPO_ROOT / "mcp-server" / "src" / "generated"

MAX_EXCERPT_CHARS = 500
EMBEDDING_PRECISION = 4


def _strip_front_matter(text: str) -> str:
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text.strip()


def _extract_tldr(body: str) -> str:
    import re
    m = re.search(
        r"^>\s*\*\*TL;DR:?\*\*\s*(.+?)(?:\n\n|\Z)",
        body,
        re.MULTILINE | re.IGNORECASE | re.DOTALL,
    )
    if m:
        return m.group(1).replace("\n>", " ").strip()
    m = re.search(
        r"^>\s*(?:Summary|Key takeaway)s?:?\s*(.+?)(?:\n\n|\Z)",
        body,
        re.MULTILINE | re.IGNORECASE | re.DOTALL,
    )
    if m:
        return m.group(1).replace("\n>", " ").strip()
    return ""


def _build_excerpt(body: str) -> str:
    text = body.replace("\n", " ").strip()
    return text[:MAX_EXCERPT_CHARS]


def export_data(out_dir: Path, check_mode: bool) -> int:
    if not INDEX_PATH.exists():
        print(f"[export-mcp-data] Missing index: {INDEX_PATH}", file=sys.stderr)
        return 1

    with INDEX_PATH.open("r", encoding="utf-8") as fh:
        index = json.load(fh)

    # Order deterministically by date desc, then folder
    articles = sorted(
        index.get("articles", []),
        key=lambda a: (a.get("published_date", ""), a.get("folder", "")),
        reverse=True,
    )

    archive_records = []
    embedding_records = {}

    has_embeddings = EMBEDDINGS_PATH.exists()
    embeddings_table = pq.read_table(EMBEDDINGS_PATH) if has_embeddings else None
    embeddings_by_slug = {}
    if embeddings_table is not None:
        slug_col = embeddings_table.column("slug").to_pylist()
        emb_col = embeddings_table.column("embedding").to_pylist()
        for s, e in zip(slug_col, emb_col):
            embeddings_by_slug[s] = e

    for art in articles:
        folder = art["folder"]
        article_path = REPO_ROOT / "articles" / folder / "article.md"
        summary = ""
        excerpt = ""
        if article_path.exists():
            body = _strip_front_matter(article_path.read_text(encoding="utf-8"))
            summary = _extract_tldr(body)
            excerpt = _build_excerpt(body)

        record = {
            "slug": art.get("slug", ""),
            "title": art.get("title", ""),
            "published_date": art.get("published_date", ""),
            "canonical_url": art.get("canonical_url", ""),
            "local_url": f"/articles/{art.get('slug', '')}/",
            "topics": art.get("topics", []),
            "summary": summary,
            "excerpt": excerpt,
        }
        archive_records.append(record)

        slug = art.get("slug", "")
        if slug in embeddings_by_slug:
            embedding_records[slug] = [
                round(v, EMBEDDING_PRECISION) for v in embeddings_by_slug[slug]
            ]

    out_dir.mkdir(parents=True, exist_ok=True)

    archive_path = out_dir / "archive-data.json"
    embeddings_out_path = out_dir / "embeddings.json"

    archive_json = json.dumps(archive_records, separators=(",", ":"), ensure_ascii=False)
    embeddings_json = json.dumps(embedding_records, separators=(",", ":"), ensure_ascii=False)

    if check_mode:
        changed = False
        if archive_path.exists():
            existing = archive_path.read_text(encoding="utf-8")
            if existing != archive_json:
                changed = True
                print(f"[export-mcp-data] {archive_path.name} would change")
        else:
            changed = True
            print(f"[export-mcp-data] {archive_path.name} would be created")

        # embeddings.json is optional (not committed to git to keep bundle small)
        if embeddings_out_path.exists():
            existing = embeddings_out_path.read_text(encoding="utf-8")
            if existing != embeddings_json:
                changed = True
                print(f"[export-mcp-data] {embeddings_out_path.name} would change")

        if changed:
            print("[export-mcp-data] CHECK FAILED: generated data is stale")
            return 1
        print("[export-mcp-data] CHECK PASSED: generated data is up to date")
        return 0

    archive_path.write_text(archive_json, encoding="utf-8")
    embeddings_out_path.write_text(embeddings_json, encoding="utf-8")

    archive_size = archive_path.stat().st_size
    embeddings_size = embeddings_out_path.stat().st_size

    print(
        f"[export-mcp-data] Wrote {archive_path} — "
        f"{len(archive_records)} records, {archive_size:,} bytes ({archive_size/1024:.1f} KB)"
    )
    print(
        f"[export-mcp-data] Wrote {embeddings_out_path} — "
        f"{len(embedding_records)} vectors, {embeddings_size:,} bytes ({embeddings_size/1024:.1f} KB)"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Export archive data for MCP server")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return export_data(args.out_dir, args.check)


if __name__ == "__main__":
    sys.exit(main())
