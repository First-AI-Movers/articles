# Article Embedding Index

A deterministic, local RAG-ready embedding index for the article archive.

## Purpose

Make the archive useful for downstream retrieval, future MCP search (E21), future "Ask the archive" chatbot (E33), and external AI consumers — without requiring a live database or paid API.

## Model

- **Name:** `BAAI/bge-small-en-v1.5`
- **License:** MIT (confirmed on [HuggingFace model card](https://huggingface.co/BAAI/bge-small-en-v1.5))
- **Dimensions:** 384
- **Sequence length:** 512 tokens
- **Runtime:** [fastembed](https://github.com/qdrant/fastembed) (ONNX-based, no PyTorch, CPU-optimized)
- **Parameters:** 33.4M
- **Cache size:** ~78 MB after first download

## Generated artifact

- **Path:** `embeddings.parquet` (repo root)
- **Format:** Apache Parquet with Snappy compression
- **Size:** ~1–2 MB for 829 articles
- **Deterministic:** Same article set + same model → identical bytes

## Schema

| Column | Type | Description |
|---|---|---|
| `folder` | string | Article folder name (`YYYY-MM-DD-slug`) |
| `slug` | string | URL-safe slug |
| `title` | string | Article headline |
| `published_date` | string | `YYYY-MM-DD` |
| `canonical_url` | string | External canonical URL |
| `local_url` | string | Local archive path (`/articles/<slug>/`) |
| `topics` | string | JSON array of canonical topics |
| `summary` | string | TL;DR or summary blockquote if present |
| `text_chars` | int32 | Length of the embedding input text |
| `model` | string | Embedding model name |
| `embedding_dim` | int32 | Vector dimension (384) |
| `embedding` | `fixed_size_list<float32>[384]` | Normalized embedding vector |

## Text input builder

For each article, the following fields are concatenated into a single text string:

1. **Title**
2. **Topics** (comma-separated canonical topics)
3. **TL;DR / Summary** (extracted from blockquote after front matter, if present)
4. **Body excerpt** (first 500 characters after front matter stripping)

This gives the model semantic context from title, classification, summary, and opening content without chunking the full article.

## Regenerate locally

```bash
# Dry run (shows count, does not write)
python3 tools/build_embeddings.py --dry-run

# Full rebuild
python3 tools/build_embeddings.py --out embeddings.parquet

# Limit to first N articles (for testing)
python3 tools/build_embeddings.py --limit 10 --out /tmp/test.parquet

# Use a different fastembed-supported model
python3 tools/build_embeddings.py --model BAAI/bge-base-en-v1.5 --out embeddings.parquet
```

The first run downloads the ONNX model to `~/.cache/huggingface/`. Subsequent runs are fully offline.

## Sample retrieval

```bash
# Top 5 articles for a query
python3 tools/embeddings_sample.py "AI governance for European SMEs"

# Custom index path
python3 tools/embeddings_sample.py --index /tmp/test.parquet --top 3 "machine learning"
```

This is a **demonstration script**, not production search. It loads the full index into memory and uses NumPy cosine similarity. For production-scale retrieval, consider FAISS or a vector database.

## CI / workflow

- **File:** `.github/workflows/build-embeddings.yml`
- **Triggers:**
  - `workflow_dispatch` (manual)
  - Weekly cron: Sundays at 03:17 UTC
- **Behavior:**
  1. Installs dependencies
  2. Restores model cache
  3. Runs `build_embeddings.py`
  4. Uploads parquet as artifact
  5. Opens a PR if `embeddings.parquet` changed (via `create-pull-request`)
- **Not required** in branch protection
- **Never pushes directly to `main`**

## Cache / model download

fastembed downloads quantized ONNX models via HuggingFace Hub on first use:

- Default cache: `~/.cache/huggingface/hub/`
- On CI this is cached between runs via `actions/cache`
- No authentication required (unauthenticated HF requests have rate limits, but a single model download is well within them)

## Relationship to other epics

| Epic | Relationship |
|---|---|
| **E21 MCP server** | `search_articles` tool will load `embeddings.parquet` and perform cosine-similarity retrieval |
| **E33 chatbot** | RAG step will retrieve top-k articles from the embedding index, then prompt a small LLM |
| **llms-full.txt** | Both are derived artifacts; embeddings add semantic structure, llms-full adds raw text |
| **AI training policy** | Embeddings are a derived artifact of CC-BY-4.0 content; downstream consumers should respect the same license |

## Limitations

- **One vector per article** in v1 — not chunk-level retrieval
- **No live database** — parquet is a static snapshot
- **Local model only** — no API fallback
- **FAISS deferred** — NumPy cosine similarity is sufficient for v1; add FAISS later if latency or scale demands it
- **English-only model** — articles are published in English

## Rollback

To remove the embedding index from the site:

1. Delete `embeddings.parquet`
2. Remove `tools/build_embeddings.py` and `tools/embeddings_sample.py`
3. Remove `.github/workflows/build-embeddings.yml`
4. Remove embedding dependencies from `tools/requirements.txt`
5. Delete `docs/EMBEDDINGS.md` and update `docs/OPERATIONS.md`
