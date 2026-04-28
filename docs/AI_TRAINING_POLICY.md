# AI Training Policy

This document makes the First AI Movers article archive’s AI-ingestion posture explicit, machine-readable, and legally grounded.

## Policy summary

All article content in this archive is published under the **Creative Commons Attribution 4.0 International License (CC BY 4.0)**.

We intentionally permit responsible AI indexing, retrieval, summarization, citation, and model-training use of this archive, provided that attribution is preserved.

## What is permitted

- Indexing and crawling by search engines and AI systems
- Retrieval-augmented generation (RAG) and answer-engine citation
- Summarization and paraphrasing
- Training, fine-tuning, and evaluation of machine-learning models

## What must be preserved

- Article title
- Canonical URL (original publication source)
- Publication date
- Author attribution: **Dr. Hernani Costa**
- Organization attribution: **First AI Movers**
- License reference: **CC BY 4.0**

## Machine-readable signals

| Signal | Location |
|---|---|
| `robots.txt` allow rules | Repo root — explicit `Allow: /` for major AI/search bots |
| `<meta name="ai-training">` | Rendered in `<head>` of every HTML page |
| AI Training License header | `llms-full.txt` and `llms-recent.txt` corpus files |

## Code vs content license

- **Article content** (text, metadata, rendered HTML): CC BY 4.0
- **Code, templates, tooling, workflows**: Apache-2.0 (see `LICENSE-CODE`)

These are separate licenses for separate artifacts. Do not conflate them.

## Relationship to other systems

- `robots.txt` — declares crawl permission to bots
- `llms-full.txt` / `llms-recent.txt` — corpus files with embedded license for direct LLM ingestion
- `CITATION.cff` — academic citation metadata
- `sitemap.xml` — discoverability for crawlers

## Rollback / change process

To alter this policy:

1. Update this document.
2. Update `robots.txt` if bot rules change.
3. Update the `<meta name="ai-training">` tag in `templates/base.html.j2`.
4. Update the AI Training License header in `tools/rebuild_local.py` (llms generators).
5. Rebuild the site and regenerate corpus files.
6. Open a PR with rationale.

## Rationale

The archive exists to spread useful AI strategy knowledge. Restricting AI systems from reading it would be counter-productive. CC BY 4.0 already requires attribution; making that requirement machine-readable helps compliant systems honour it automatically.
