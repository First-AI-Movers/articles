# Citation Graph

Deterministic article-to-article citation graph for the First AI Movers archive.

## Purpose

The citation graph makes explicit internal links between articles machine-readable and reader-visible. It turns the archive from a flat list of posts into a connected knowledge base, improving:

- **Reader discovery** — "Referenced by" sections surface related reading.
- **Scholarly posture** — Explicit citations signal research-quality structure.
- **AI retrieval** — Connected graphs help LLMs and search engines understand content relationships.
- **Future DOI work** — Per-article DOIs (E34) can build on the graph infrastructure.

## How links are detected

`tools/build_citation_graph.py` scans every `articles/*/article.md` for markdown links:

```markdown
[Anchor text](https://radar.firstaimovers.com/target-article-slug)
```

It matches the target URL against known article URLs:

1. **Canonical URL prefix match** — `https://radar.firstaimovers.com/<slug>`, `https://insights.firstaimovers.com/<slug>`, etc.
2. **Local archive URL match** — `https://articles.firstaimovers.com/articles/<slug>/`, `/articles/<slug>/`
3. **Slug match** — for Beehiiv `/p/<slug>` paths and similar patterns where the last path segment is a known slug.

## What counts as an edge

- Explicit markdown links from one archive article to another archive article.
- Links on these hosts: `articles.firstaimovers.com`, `radar.firstaimovers.com`, `www.firstaimovers.com`, `firstaimovers.com`, `insights.firstaimovers.com`, `voices.firstaimovers.com`.

## What does NOT count

- Self-links (an article linking to its own canonical URL or slug).
- Links to non-article pages: `/page/*`, `/c/*`, `/archive*`, `/subscribe`, `/upgrade`, root homepage.
- External links (LinkedIn, Medium, docs.anthropic.com, etc.).
- Raw URLs without markdown link syntax.
- Inferred topic overlap — v1 is explicit-link only.

## Generated artifact

`citation_graph.json` at repo root:

```json
{
  "version": 1,
  "generated_from": "articles",
  "nodes": [
    {
      "folder": "2026-04-01-example",
      "slug": "example",
      "title": "Example",
      "published_date": "2026-04-01",
      "local_url": "https://articles.firstaimovers.com/articles/example/",
      "canonical_url": "https://radar.firstaimovers.com/example",
      "topics": ["AI Strategy"]
    }
  ],
  "edges": [
    {
      "source_folder": "2026-04-02-source",
      "target_folder": "2026-04-01-example",
      "source_slug": "source",
      "target_slug": "example",
      "type": "explicit-link",
      "matched_url": "https://radar.firstaimovers.com/example",
      "anchor_text": "Example"
    }
  ],
  "stats": {
    "node_count": 829,
    "edge_count": 1237,
    "articles_with_outgoing": 386,
    "articles_with_incoming": 346
  }
}
```

Nodes and edges are deterministically ordered so the file is diff-stable.

## Commands

### Build the graph

```bash
python3 tools/build_citation_graph.py
```

### Check if the graph is current (CI)

```bash
python3 tools/build_citation_graph.py --check
```

### Write to a custom path

```bash
python3 tools/build_citation_graph.py --out /tmp/citation_graph.json
```

## Rendering behavior

Per-article pages (`/articles/<slug>/`) render two optional sections:

- **"References in this archive"** — outgoing citation links from this article.
- **"Referenced by"** — incoming citation links to this article from other archive articles.

Both sections are hidden when empty. Each list is capped at 10 items with a "Showing first 10." note when truncated.

## JSON-LD behavior

When an article has outgoing citations, its Schema.org `Article` JSON-LD gains a `citation` array:

```json
"citation": [
  {
    "@type": "CreativeWork",
    "name": "Target Article Title",
    "url": "https://articles.firstaimovers.com/articles/target/"
  }
]
```

No empty `citation` field is emitted.

## Limitations

- **v1 only detects explicit links.** Articles without markdown links to other articles will have no edges. This is by design — the graph exposes existing connections, it does not manufacture them.
- **No inferred topic-overlap edges.** Future versions could add topic-similarity edges, but v1 stays strictly explicit.
- **Old articles may have few internal links.** The corpus grew organically; cross-linking density varies by era and author workflow.
- **Canonical URL drift.** If a canonical URL changes (platform migration, slug rename), existing links in article bodies may no longer resolve until the body is updated.

## Relationship to other epics

- **E23 (corpus DOI)** — Citation graph is corpus-level infrastructure; per-article DOIs extend it.
- **E34 (per-article DOIs)** — Future work can add DOI identifiers to graph nodes and JSON-LD citations.
- **E35 (multi-length summaries)** — Summaries could be shown in citation cards instead of just titles.
- **E33 (Ask-the-Archive)** — Chatbot retrieval can traverse the citation graph for follow-up recommendations.
- **E31 (series)** — Series are editorially curated learning paths; the citation graph is emergent from author links.

## Contributing

When writing or editing articles, internal links between articles become citation graph edges automatically. No extra metadata is required. Link naturally using markdown:

```markdown
See [AI Governance Framework for European SMEs](https://radar.firstaimovers.com/ai-governance-framework-european-sme-2026) for the full model.
```
