# MCP Server on Cloudflare Workers

A stateless Model Context Protocol (MCP) server that exposes the First AI Movers article archive as tools and resources for AI assistants.

## Purpose

Enable AI assistants (Claude, Cursor, etc.) to search, browse, and retrieve articles from the archive via the MCP protocol — without requiring a live database or API keys.

## Architecture

- **Runtime:** Cloudflare Workers (stateless, edge-deployed)
- **Protocol:** MCP over HTTP (Streamable HTTP transport)
- **SDK:** `@modelcontextprotocol/sdk` v1.26.0
- **Data source:** Bundled `archive-data.json` (generated from `index.json` + article Markdown)
- **Search:** Lexical scoring (default) with optional semantic search via Workers AI

## Directory layout

```
mcp-server/
├── src/
│   ├── index.ts          # Worker entry point — HTTP routing + MCP + Ask handler
│   ├── archive.ts        # Data loader and lookup helpers
│   ├── search.ts         # Lexical and semantic search
│   ├── ask.ts            # Ask the Archive chatbot handler (POST /api/ask)
│   └── generated/
│       ├── archive-data.json   # Bundled article metadata + excerpts
│       └── embeddings.json     # Optional embedding vectors (384-dim)
├── test/
│   ├── archive.test.ts   # Unit tests for archive lookups
│   ├── search.test.ts    # Unit tests for search scoring
│   └── ask.test.ts       # Unit tests for Ask endpoint
├── package.json
├── tsconfig.json
├── vitest.config.ts      # Vitest pool-workers config
└── wrangler.jsonc        # Cloudflare Workers config
```

## Tools

| Tool | Description |
|---|---|
| `search_articles` | Search by keyword with optional topic filter. Returns ranked results with titles, URLs, dates, and excerpts. |
| `get_article` | Retrieve full metadata for a single article by slug. |
| `list_topics` | List canonical topics, optionally filtered by minimum article count. |
| `get_topic_intro` | Get overview for a topic including sample articles. |
| `get_quick_reads` | Get short summaries for articles in a topic, ordered by recency. |

## Resources

| Resource | URI Pattern | Description |
|---|---|---|
| `corpus` | `firstaimovers://corpus` | Archive metadata (article count, date range, site URL) |
| `article` | `firstaimovers://article/{slug}` | Individual article metadata |
| `topic` | `firstaimovers://topic/{slug}` | Topic metadata (name, article count) |

## Search modes

### Lexical (default)

Scores articles by keyword overlap with weighted fields:
- Title match: ×10 (exact) / ×3 (word)
- Topic match: ×5 (exact) / ×2 (word)
- Summary match: ×4 (exact) / ×1 (word)
- Excerpt match: ×2 (exact) / ×0.5 (word)

### Semantic (optional)

When `SEMANTIC_SEARCH_ENABLED=true` and the Workers AI binding is available:
1. Embeds the query via `@cf/baai/bge-small-en-v1.5` (384-dim)
2. Computes cosine similarity against pre-generated article embeddings
3. Returns top-k by similarity

**Disabled by default** because E22 embeddings were generated with fastembed (ONNX, mean pooling) and live compatibility with Workers AI's pooling mode is unverified without deployment.

## Local development

```bash
cd mcp-server
npm install

# Type check
npm run typecheck

# Run tests (uses vitest pool-workers)
npm test

# Local dev server
npm run dev

# Dry-run build (validates bundle size)
npm run build
```

## Regenerate archive data

```bash
# Generate archive-data.json and embeddings.json
python3 tools/export_mcp_data.py

# Verify generated files are up to date (CI check)
python3 tools/export_mcp_data.py --check
```

## Deployment

Deployment is gated and **not automatic**:

1. Requires `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` repository secrets
2. Requires `MCP_DEPLOY_ENABLED=1` repository variable
3. Runs only on `push` to `main`

To enable deployment:

1. Add secrets in GitHub Settings → Secrets and variables → Actions
2. Add `MCP_DEPLOY_ENABLED=1` in Variables
3. Push to `main` or run the workflow manually

### Manual deployment

```bash
cd mcp-server
npm run deploy
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `ARCHIVE_SITE_URL` | `https://articles.firstaimovers.com` | Public site URL |
| `GITHUB_RAW_URL` | `https://raw.githubusercontent.com/First-AI-Movers/articles/main` | Fallback for embeddings fetch |
| `SEMANTIC_SEARCH_ENABLED` | `false` | Enable semantic search via Workers AI |

## CI / workflow

- **File:** `.github/workflows/mcp-server.yml`
- **Triggers:** PR and push to `main` when `mcp-server/**`, `tools/export_mcp_data.py`, or the workflow itself changes
- **Jobs:**
  1. `test` — type check, Node unit tests, dry-run build
  2. `export-data` — Python contract tests, verify generated data is up to date
  3. `deploy` — gated deployment to Cloudflare Workers (only on `main` push)

## Bundle size

- **Raw:** ~4.2 MB (includes `archive-data.json` with 829 articles)
- **Gzipped:** ~1.1 MB
- Well within Cloudflare Workers free tier limits

## Security

- **Read-only:** No write tools, no article mutation, no arbitrary code execution
- **Bounded results:** All tools return max 10 results
- **Slug validation:** Regex `^[a-z0-9-]+$` prevents path traversal
- **No secrets in repo:** Cloudflare credentials are GitHub secrets only

## Relationship to other epics

| Epic | Relationship |
|---|---|
| **E22 Embeddings** | Provides the `embeddings.parquet` that feeds `embeddings.json` |
| **E33 Chatbot** | Extends the same Worker with `/api/ask` for the "Ask the Archive" POC |
| **Site build** | `archive-data.json` is regenerated whenever `index.json` or articles change |

## Rollback

To remove the MCP server:

1. Delete `mcp-server/` directory
2. Delete `tools/export_mcp_data.py`
3. Delete `tools/tests/test_export_mcp_data.py`
4. Delete `.github/workflows/mcp-server.yml`
5. Delete `docs/MCP_SERVER.md`
6. Remove MCP server mention from `docs/OPERATIONS.md` and `CHANGELOG.md`
