#!/usr/bin/env python3
"""Demonstrate local semantic retrieval against embeddings.parquet.

Usage:
    python3 tools/embeddings_sample.py "AI governance for European SMEs"
    python3 tools/embeddings_sample.py --index embeddings.parquet --top 5 "AI agents"
    python3 tools/embeddings_sample.py --index /tmp/test.parquet "machine learning"
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import numpy as np
    import pyarrow.parquet as pq
    from fastembed import TextEmbedding
except ModuleNotFoundError as exc:  # pragma: no cover
    print(
        f"[embeddings-sample] Missing dependency: {exc.name}\n"
        "Install with: pip install fastembed pyarrow numpy",
        file=sys.stderr,
    )
    sys.exit(1)


DEFAULT_INDEX = Path("embeddings.parquet")
DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_TOP = 5


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Cosine similarity between a 1-D query vector and a 2-D matrix."""
    a_norm = a / np.linalg.norm(a)
    b_norm = b / np.linalg.norm(b, axis=1, keepdims=True)
    return b_norm @ a_norm


def search(index_path: Path, query: str, model_name: str, top_k: int):
    if not index_path.exists():
        print(
            f"[embeddings-sample] Index not found: {index_path}\n"
            "Generate it first: python3 tools/build_embeddings.py --out embeddings.parquet",
            file=sys.stderr,
        )
        sys.exit(1)

    table = pq.read_table(index_path)
    embeddings = np.vstack(table.column("embedding").to_pylist())
    titles = table.column("title").to_pylist()
    slugs = table.column("slug").to_pylist()
    local_urls = table.column("local_url").to_pylist()
    canonical_urls = table.column("canonical_url").to_pylist()
    models = table.column("model").to_pylist()

    model = TextEmbedding(model_name=model_name)
    query_emb = np.array(list(model.embed([query]))[0])

    scores = _cosine_similarity(query_emb, embeddings)
    top_idx = np.argsort(scores)[::-1][:top_k]

    print(f"Query: {query}")
    print(f"Index: {index_path} ({len(titles)} articles)")
    print(f"Model: {models[0] if models else model_name}")
    print("-" * 60)
    for rank, idx in enumerate(top_idx, 1):
        print(f"{rank}. {titles[idx]}")
        print(f"   Local:    {local_urls[idx]}")
        print(f"   Canonical: {canonical_urls[idx]}")
        print(f"   Score:    {scores[idx]:.4f}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Local semantic retrieval demo")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--top", type=int, default=DEFAULT_TOP)
    args = parser.parse_args()

    search(args.index, args.query, args.model, args.top)
    return 0


if __name__ == "__main__":
    sys.exit(main())
