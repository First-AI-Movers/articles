# MCP Server on Cloudflare Workers

A stateless Model Context Protocol (MCP) server that exposes the First AI Movers article archive as tools and resources for AI assistants.

## Purpose

Enable AI assistants (Claude, Cursor, etc.) to search, browse, and retrieve articles from the archive via the MCP protocol — without requiring a live database or API keys.

## Architecture

- **Runtime:** Cloudflare Workers (stateless, edge-deployed)
- **Protocol:** MCP over HTTP (Streamable HTTP transport)
- **SDK:** `@modelcontextprotocol/sdk` 1.32.2 (the version pinned in `mcp-server/package-lock.json`)
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
| `get_article` | Retrieve one article by slug: metadata, summary, links and an excerpt of the opening text (up to 500 characters). With `include_full_text: true` it also returns the article body, at most 20,000 characters per call, with `total_chars`, `truncated` and `next_offset`; pass `offset` to read the next page. The body is fetched from the archive's own published `/articles/<folder>/article.md`, cached at the edge, and carries `source_url`, `license` (CC BY 4.0) and `attribution`. |
| `list_topics` | List canonical topics, optionally filtered by minimum article count. |
| `get_topic_intro` | Get overview for a topic including sample articles. |
| `get_quick_reads` | Get short summaries for articles in a topic, ordered by recency. |

## Resources

| Resource | URI Pattern | Description |
|---|---|---|
| `corpus` | `firstaimovers://corpus` | Archive metadata (article count, date range, site URL) |
| `article` | `firstaimovers://article/{slug}` | Individual article metadata |
| `topic` | `firstaimovers://topic/{slug}` | Topic metadata (name, article count) |

## Connecting a client

The server is public and read-only. It needs no account, key or token.

- **URL:** `https://articles-api.firstaimovers.com/mcp`
- **Transport:** Streamable HTTP. `POST` JSON-RPC to `/mcp`; responses arrive as server-sent events.
- **Health:** `GET https://articles-api.firstaimovers.com/health` returns `{"status":"ok", …}` with the article and topic counts.

Each of these was run against the deployed URL on 2026-11-13. None of them calls a model.

**Claude Code**

```bash
claude mcp add --transport http faim-articles https://articles-api.firstaimovers.com/mcp
claude mcp get faim-articles        # Status: ✔ Connected
```

**MCP Inspector (CLI)**

```bash
npx @modelcontextprotocol/inspector --cli https://articles-api.firstaimovers.com/mcp \
  --transport http --method tools/list
npx @modelcontextprotocol/inspector --cli https://articles-api.firstaimovers.com/mcp \
  --transport http --method tools/call --tool-name search_articles \
  --tool-arg query="AI governance" --tool-arg limit=2
```

**TypeScript SDK**

```js
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const client = new Client({ name: "my-client", version: "1.0.0" });
await client.connect(new StreamableHTTPClientTransport(new URL("https://articles-api.firstaimovers.com/mcp")));
const { tools } = await client.listTools();
const result = await client.callTool({ name: "search_articles", arguments: { query: "AI governance", limit: 2 } });
```

**Python and other HTTP clients: send your own `User-Agent`.** The host's edge protection refuses Python `urllib`'s default `User-Agent` (`Python-urllib/3.x`) with HTTP 403 (Cloudflare error 1010). Any descriptive value works, for example `User-Agent: my-archive-client/1.0`. The default user agents of `curl`, Node `fetch` and the MCP SDK are accepted.

**Limits.** Search and topic tools return metadata, summaries and short excerpts. `get_article` returns the full body only on request, in pages of at most 20,000 characters, and each page names its source and licence. If the published copy cannot be fetched, the response carries `full_text_error` and the metadata is still returned.

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

1. The `deploy` job runs in the `mcp-deploy` GitHub environment (GitHub creates it the first time the job runs)
2. It needs `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` as secrets of that environment
3. Runs only for `main`: on a `push` to `main` that matches the workflow's path filters, or on a manual `workflow_dispatch` of `main`. A dispatch of any other branch skips the job

The two secrets are the only switch. A job-level `if:` cannot read secrets, so the first step checks that both are present. When either is absent, the job ends green with a "Deploy inputs absent" notice, skips every later step and makes no Cloudflare call. There is no repository variable to set.

To enable deployment:

1. Add both secrets under GitHub Settings → Environments → `mcp-deploy`
2. Either push an authorized change to `main` that matches this workflow's path filters, or run the workflow manually (`workflow_dispatch`) on `main`. A dispatch redeploys without a code change, for example after rotating a credential. Both routes pass through the same input guard.

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
  1. `mcp-server` — type check, Node unit tests, dry-run build
  2. `export-data` — Python contract tests, verify generated data is up to date
  3. `deploy` — gated deployment to Cloudflare Workers (only on `main` push)

## Bundle size

- **Raw:** ~2.5 MB (includes `archive-data.json` with 942 articles; `wrangler deploy --dry-run`, 2026-11-13)
- **Gzipped:** ~0.5 MB
- Full article text is **not** bundled: it is about 3.4 MB gzipped, which would take the Worker past the 3 MB compressed limit of the free tier. `get_article` fetches it at request time instead.
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
