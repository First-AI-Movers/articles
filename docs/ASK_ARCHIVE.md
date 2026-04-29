# Ask the Archive — Chatbot POC

A proof-of-concept "Ask the Archive" experience that lets users ask questions and receive grounded answers with citations to archive articles.

## Purpose

Turn the archive from a static corpus into an AI-native research surface. Readers can ask practical questions, retrieve relevant articles, and get cited answers that drive traffic back into the archive.

## Architecture

```
User ──→ /ask/ (static HTML page + ask.js)
              │
              └──→ POST /api/ask (Cloudflare Worker)
                          │
                          ├──→ lexical search (searchArticles)
                          ├──→ semantic search (optional, Workers AI)
                          └──→ Workers AI text generation (@cf/meta/llama-3.1-8b-instruct)
```

- **Frontend:** `templates/ask.html.j2` + `static/ask.js`
- **Backend:** `mcp-server/src/ask.ts` — `/api/ask` route on the same Worker as the MCP server
- **Retrieval:** Reuses `searchArticles` from `mcp-server/src/search.ts`
- **Generation:** Cloudflare Workers AI binding (only when deployed with binding)

## Pages

| Path | Description |
|---|---|
| `/ask/` | Static chat UI — question form, loading state, answer area, citations |
| `/api/ask` | Worker endpoint — accepts JSON `{ question, limit }`, returns `{ answer, citations, mode }` |

## Retrieval behavior

### v1: Lexical search (default)

Reuses the existing `searchArticles` scoring:
- Title match: highest weight
- Topic match: high weight
- Summary match: medium weight
- Excerpt match: low weight

### Semantic search (optional fallback)

When `SEMANTIC_SEARCH_ENABLED=true` and the Workers AI binding is available:
- Embeds the query via `@cf/baai/bge-small-en-v1.5` (384-dim)
- Cosine similarity against pre-generated article embeddings
- Falls back to lexical on any error

**Compatibility caveat:** E22 embeddings were generated with fastembed (ONNX, mean pooling). Workers AI pooling mode compatibility is unverified without live deployment. Semantic search is disabled by default.

### Citation policy

Every answer must cite source articles. The response includes:
- `title` — article headline
- `slug` — URL-safe identifier
- `local_url` — link to archive page
- `canonical_url` — link to original publisher
- `score` — retrieval relevance score

If no relevant articles are found, the response says so clearly and suggests browsing topic hubs. The system prompt explicitly forbids inventing facts, dates, URLs, or claims.

## Request / response format

### Request

```json
POST /api/ask
Content-Type: application/json

{
  "question": "How should a European SME start with AI governance?",
  "limit": 5
}
```

Validation:
- `question`: required, 3–500 characters after trim
- `limit`: optional, 1–8, default 5

### Response

```json
{
  "answer": "Based on the archive...",
  "citations": [
    {
      "title": "AI Governance for European SMEs",
      "slug": "ai-governance-european-smes-2026",
      "local_url": "/articles/ai-governance-european-smes-2026/",
      "canonical_url": "https://...",
      "score": 42.5
    }
  ],
  "mode": "lexical"
}
```

Modes:
- `lexical` — keyword-based retrieval
- `semantic` — vector-based retrieval (only when enabled and working)
- `mock` — no AI binding available; returns a placeholder answer for testing

## Workers AI models

| Purpose | Model | Binding |
|---|---|---|
| Query embedding | `@cf/baai/bge-small-en-v1.5` | `env.AI` |
| Text generation | `@cf/meta/llama-3.1-8b-instruct` | `env.AI` |

The generation model is capped at 512 output tokens and uses a strict system prompt requiring citations and forbidding hallucination.

## Deployment

**Live deployment is gated.**

Requirements:
1. `CLOUDFLARE_API_TOKEN` repository secret
2. `CLOUDFLARE_ACCOUNT_ID` repository secret
3. `MCP_DEPLOY_ENABLED=1` repository variable

The `/api/ask` route ships as part of the existing MCP server Worker. No separate Worker is needed.

### Current status

- ✅ Worker route code written and tested
- ✅ Frontend page and JS written
- ✅ Build integration complete
- ⏳ Live deployment pending Cloudflare credentials and rate-limit setup

## Local development

```bash
cd mcp-server
npm install
npm run dev        # local Worker dev server on :8787
npm test           # unit tests (mocked AI + retrieval)
npm run typecheck  # TypeScript validation
```

Test the ask endpoint locally:

```bash
curl -s -X POST http://localhost:8787/api/ask \
  -H "content-type: application/json" \
  -d '{"question":"How should SMEs approach AI governance?","limit":3}'
```

Build the static site locally:

```bash
python3 tools/rebuild_local.py
# Open site/ask/index.html in a browser
```

## Rate limiting

**Recommended:** Cloudflare Rate Limiting Rule on the Worker route:
- 10 requests/hour per IP
- Applies to `/api/ask` only
- Free tier supports basic rate limiting rules

**Not implemented in code** — production rate limiting should be Cloudflare-side, not in-Worker, to avoid abuse vectors.

## Safety

- **No article mutation:** The endpoint is read-only
- **No secrets in browser:** Endpoint URL is configurable but no API keys are exposed
- **No answer without citations:** If retrieval fails, the response says so
- **Prompt injection mitigation:** Article excerpts are treated as untrusted context; the system prompt instructs the model to answer only from provided excerpts
- **Input validation:** Question length capped, limit capped, JSON body validated
- **No raw stack traces:** Errors return structured JSON, not stack traces

## Rollback

1. Remove "Ask" from primary nav in `templates/base.html.j2`
2. Add `noindex` to `/ask/` (already present)
3. Disable `/api/ask` route in `mcp-server/src/index.ts`
4. Turn off `MCP_DEPLOY_ENABLED` variable
5. Remove `templates/ask.html.j2`, `static/ask.js`, and build integration if fully retiring

## Relationship to other epics

| Epic | Relationship |
|---|---|
| **E21 MCP server** | Shares the same Worker; `/api/ask` is a sibling route to `/mcp` |
| **E22 Embeddings** | Powers optional semantic retrieval |
| **E31 Series** | Ask page can surface series-related articles via search |

## Limitations (POC scope)

- No chat history or conversation context
- No user accounts or authentication
- No database, KV, D1, or Vectorize
- No production rate limiting in code
- Semantic retrieval compatibility unverified without live deployment
- Streaming responses deferred to v2
- Answer quality depends on Workers AI model capabilities

## Testing

### Backend (Node/Vitest)

`mcp-server/test/ask.test.ts` covers:
- Missing/invalid request body validation
- Question length limits
- Limit capping
- Citation presence
- Empty-context handling
- Lexical fallback when AI binding missing
- Error response structure (no stack traces)

### Frontend (Playwright E2E)

`tests-e2e/specs/ask.spec.ts` covers:
- Page renders with correct title
- Form accessibility attributes
- Empty submit validation
- `noindex` robots meta
- Disabled endpoint state (404 → friendly banner)
- Nav link presence

### Build (Python/pytest)

`tools/tests/test_rebuild_local.py::TestAskPage` covers:
- `/ask/index.html` generation
- `noindex` meta tag
- Form elements present
- `ask.js` included and copied
- Disabled banner present
- Breadcrumb present
- Nav link present

(These tests require jinja2 and are skipped when not installed.)
