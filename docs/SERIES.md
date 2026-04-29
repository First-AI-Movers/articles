# Article Series / Learning Paths

Article series turn clusters of related articles into structured learning paths for readers.

## Purpose

- Guide readers through multi-part content in the intended order.
- Improve time-on-site and archive navigation.
- Provide semantic structure for AI retrieval (RAG, MCP, future chatbot).
- Signal editorial intent — a series is curated, not just topically related.

## What qualifies as a series

A series requires **all four** of the following:

1. **Intentional ordering** — articles have a prescribed reading sequence (Part 1, Part 2, Day 1, Day 2, etc.).
2. **Narrative or pedagogical progression** — each article builds on the previous.
3. **Shared title stem or framework name** — a common thread ties the parts together.
4. **Editorial approval** — the author or archive owner has designated it as a series.

**Not a series:** topic clusters, republications, city-by-city format articles, or loosely related posts published months apart.

## How series are chosen

Series are discovered via `docs/SERIES_CANDIDATES.md` (editorial discovery report). Candidate series are evaluated on:

- Explicit markers in titles (`Part N/M`, `Day N/M`)
- Thematic cohesion and progression
- Confidence level (high / medium / low)
- Risks and ambiguity

Only **high-confidence** candidates with explicit markers are approved without further review. All others require editorial sign-off.

## How to propose a new series

1. Add the candidate to `docs/SERIES_CANDIDATES.md` with rationale, confidence, and article list.
2. Add the series definition to `tools/series_registry.json`.
3. Add `series` and `series_order` fields to the approved articles' `metadata.json`.
4. Run `python3 tools/check_series.py` to validate.
5. Run `python3 tools/rebuild_local.py` to preview rendering.
6. Open a PR. Do not push directly to `main`.

## Metadata format

In `articles/<folder>/metadata.json`:

```json
{
  "series": "prompt-engineering-10-day",
  "series_order": 3
}
```

Rules:

- `series` is a kebab-case slug referencing `tools/series_registry.json`.
- `series_order` is a positive integer (`1`, `2`, `3`, …).
- Both fields are optional.
- If `series_order` exists, `series` must exist.
- Existing metadata without these fields remains valid.

## Registry format

`tools/series_registry.json`:

```json
{
  "series": {
    "prompt-engineering-10-day": {
      "title": "Prompt Engineering 10-Day Course",
      "description": "A hands-on prompt-engineering curriculum...",
      "topics": ["Healthcare AI", "Prompt Engineering"]
    }
  }
}
```

- `title` — display name used in chips and navigation.
- `description` — short summary used in topic hub cards.
- `topics` — canonical topics associated with the series.

## Validation

```bash
# Basic validation
python3 tools/check_series.py

# Strict mode (warns on order gaps)
python3 tools/check_series.py --strict
```

Checks:

- `series` slug exists in registry
- `series_order` is a positive integer
- No duplicate `series_order` within the same series
- No `series_order` without `series`
- No unknown series slugs

## How series render

### Per-article page

If an article has valid series metadata:

- A **series chip** appears below the date/author line:  
  "Part 3 of 10 in Prompt Engineering 10-Day Course"
- **Previous / Next navigation** appears above the footer:  
  "← Previous in series: Day 2 …" / "Continue reading → Day 4 …"
- **JSON-LD** gains an `isPartOf` `CreativeWorkSeries` block.

If no series: the page renders exactly as before.

### Topic hub page

If a topic contains articles that belong to a series:

- A **"Series in this topic"** section appears above the article list.
- Each series card shows the title, article count, description, and link to the first article.

If no series intersect the topic: no visible change.

## Rollback

To remove a series:

1. Remove the `series` and `series_order` fields from affected `metadata.json` files.
2. Optionally remove the series from `tools/series_registry.json`.
3. Rebuild: `python3 tools/rebuild_local.py`.

The archive remains fully functional with empty or partial registries.

## Editorial approval for historical rewrites

**Do not add series metadata to historical articles purely to chase structure without editorial approval.** Article text is immutable per `CONTRIBUTING.md`. Series assignment is a metadata edit, not a content edit, but it still requires editorial judgment.

## Relationship to other features

- **GEO audit (E28):** Series do not affect GEO scores. They are editorial metadata.
- **Quality CI (E30):** Series rendering does not trigger Vale or readability changes.
- **Topic hubs:** Series complement topic hubs by adding curated paths within a topic.
- **RAG / chatbot (E33):** Series provide structured traversal signals for retrieval.
