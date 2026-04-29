import { describe, it, expect } from "vitest";
import { searchArticles } from "../src/search.js";

describe("searchArticles", () => {
  it("returns results for a common query", async () => {
    const results = await searchArticles("AI", 5, undefined, {});
    expect(results.length).toBeGreaterThan(0);
    expect(results.length).toBeLessThanOrEqual(5);
    for (const r of results) {
      expect(r.title).toBeDefined();
      expect(r.slug).toBeDefined();
      expect(r.score).toBeGreaterThan(0);
    }
  });

  it("filters by topic", async () => {
    const topic = "ai-strategy";
    const results = await searchArticles("AI", 10, topic, {});
    for (const r of results) {
      expect(
        r.topics.some(
          (t) =>
            t.toLowerCase().replace(/\s+/g, "-") === topic ||
            t.toLowerCase() === topic.replace(/-/g, " ")
        )
      ).toBe(true);
    }
  });

  it("limits results", async () => {
    const results = await searchArticles("the", 3, undefined, {});
    expect(results.length).toBeLessThanOrEqual(3);
  });

  it("throws on empty query", async () => {
    await expect(searchArticles("", 5, undefined, {})).rejects.toThrow(
      "Query must not be empty"
    );
  });

  it("throws on query exceeding max length", async () => {
    const longQuery = "a".repeat(201);
    await expect(searchArticles(longQuery, 5, undefined, {})).rejects.toThrow(
      "Query exceeds maximum length"
    );
  });

  it("falls back to lexical when semantic is enabled but AI binding missing", async () => {
    const env = { SEMANTIC_SEARCH_ENABLED: "true" };
    const results = await searchArticles("AI", 5, undefined, env);
    expect(results.length).toBeGreaterThan(0);
  });
});
