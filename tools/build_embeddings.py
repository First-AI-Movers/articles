#!/usr/bin/env python3
"""Build a deterministic Parquet embedding index for all articles.

Usage:
    python3 tools/build_embeddings.py --dry-run
    python3 tools/build_embeddings.py --out embeddings.parquet
    python3 tools/build_embeddings.py --limit 10 --out /tmp/test.parquet
    python3 tools/build_embeddings.py --model BAAI/bge-small-en-v1.5
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Optional dependencies: fastembed, pyarrow, numpy
# If missing, the script fails with a clear message.
try:
    import numpy as np
    import pyarrow as pa
    import pyarrow.parquet as pq
    from fastembed import TextEmbedding
except ModuleNotFoundError as exc:  # pragma: no cover
    print(
        f"[embeddings] Missing dependency: {exc.name}\n"
        "Install with: pip install fastembed pyarrow numpy",
        file=sys.stderr,
    )
    sys.exit(1)


REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = REPO_ROOT / "index.json"
ARTICLES_DIR = REPO_ROOT / "articles"

DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384
MAX_BODY_CHARS = 500

# Parquet schema
SCHEMA = pa.schema([
    ("folder", pa.string()),
    ("slug", pa.string()),
    ("title", pa.string()),
    ("published_date", pa.string()),
    ("canonical_url", pa.string()),
    ("local_url", pa.string()),
    ("topics", pa.string()),          # JSON array
    ("summary", pa.string()),
    ("text_chars", pa.int32()),
    ("model", pa.string()),
    ("embedding_dim", pa.int32()),
    ("embedding", pa.list_(pa.float32(), EMBEDDING_DIM)),
])


def _strip_front_matter(text: str) -> str:
    """Remove YAML front matter from Markdown."""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text.strip()


def _extract_tldr(body: str) -> str:
    """Extract TL;DR or summary blockquote if present."""
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


def _build_input_text(title: str, topics: list, summary: str, body: str) -> str:
    """Concatenate article fields into a single embedding input."""
    parts = [title]
    if topics:
        parts.append(", ".join(topics))
    if summary:
        parts.append(summary)
    # Append first meaningful body excerpt
    excerpt = body[:MAX_BODY_CHARS].replace("\n", " ").strip()
    if excerpt:
        parts.append(excerpt)
    return "\n".join(parts)


def _load_index() -> dict:
    with INDEX_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _read_article(folder: str) -> tuple[str, str]:
    """Return (raw_text, body_without_front_matter) for an article folder."""
    path = ARTICLES_DIR / folder / "article.md"
    raw = path.read_text(encoding="utf-8")
    body = _strip_front_matter(raw)
    return raw, body


def build_embeddings(model_name: str, limit: int | None, dry_run: bool) -> list[dict]:
    """Generate embedding rows for all (or limited) articles."""
    index = _load_index()
    articles = sorted(
        index["articles"],
        key=lambda a: (a.get("published_date", ""), a.get("folder", "")),
        reverse=True,
    )
    if limit:
        articles = articles[:limit]

    rows = []
    texts = []
    metas = []

    for art in articles:
        folder = art["folder"]
        try:
            _raw, body = _read_article(folder)
        except FileNotFoundError:
            print(f"[embeddings] Skip missing article: {folder}", file=sys.stderr)
            continue

        summary = _extract_tldr(body)
        text = _build_input_text(
            title=art.get("title", ""),
            topics=art.get("topics", []),
            summary=summary,
            body=body,
        )
        texts.append(text)
        metas.append({
            "folder": folder,
            "slug": art.get("slug", ""),
            "title": art.get("title", ""),
            "published_date": art.get("published_date", ""),
            "canonical_url": art.get("canonical_url", ""),
            "local_url": f"/articles/{art.get('slug', '')}/",
            "topics": json.dumps(art.get("topics", []), ensure_ascii=False),
            "summary": summary,
            "text_chars": len(text),
        })

    if dry_run:
        print(f"[embeddings] dry-run: would embed {len(texts)} articles")
        return []

    embedder = TextEmbedding(model_name=model_name)

    if not texts:
        print("[embeddings] No articles to embed", file=sys.stderr)
        return []

    print(f"[embeddings] Encoding {len(texts)} articles with {model_name} …")
    embeddings = list(embedder.embed(texts))

    for meta, emb in zip(metas, embeddings):
        vec = emb.tolist()
        if len(vec) != EMBEDDING_DIM:
            raise RuntimeError(
                f"Expected dimension {EMBEDDING_DIM}, got {len(vec)}"
            )
        rows.append({
            **meta,
            "model": model_name,
            "embedding_dim": EMBEDDING_DIM,
            "embedding": vec,
        })

    return rows


def _write_parquet(rows: list[dict], out_path: Path) -> None:
    """Write rows to a Parquet file matching SCHEMA."""
    arrays = {
        "folder": pa.array([r["folder"] for r in rows], type=pa.string()),
        "slug": pa.array([r["slug"] for r in rows], type=pa.string()),
        "title": pa.array([r["title"] for r in rows], type=pa.string()),
        "published_date": pa.array([r["published_date"] for r in rows], type=pa.string()),
        "canonical_url": pa.array([r["canonical_url"] for r in rows], type=pa.string()),
        "local_url": pa.array([r["local_url"] for r in rows], type=pa.string()),
        "topics": pa.array([r["topics"] for r in rows], type=pa.string()),
        "summary": pa.array([r["summary"] for r in rows], type=pa.string()),
        "text_chars": pa.array([r["text_chars"] for r in rows], type=pa.int32()),
        "model": pa.array([r["model"] for r in rows], type=pa.string()),
        "embedding_dim": pa.array([r["embedding_dim"] for r in rows], type=pa.int32()),
        "embedding": pa.array([r["embedding"] for r in rows], type=pa.list_(pa.float32(), EMBEDDING_DIM)),
    }
    table = pa.table(arrays, schema=SCHEMA)
    pq.write_table(table, out_path, compression="snappy")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build article embedding index")
    parser.add_argument("--out", type=Path, default=Path("embeddings.parquet"))
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rows = build_embeddings(model_name=args.model, limit=args.limit, dry_run=args.dry_run)

    if args.dry_run:
        print(f"[embeddings] dry-run complete")
        return 0

    if not rows:
        print("[embeddings] No rows generated", file=sys.stderr)
        return 1

    _write_parquet(rows, args.out)
    size = args.out.stat().st_size
    print(
        f"[embeddings] Wrote {args.out} — "
        f"{len(rows)} rows, {EMBEDDING_DIM}d, {size:,} bytes ({size/1024/1024:.2f} MB)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
