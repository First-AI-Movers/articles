import { describe, it, expect } from "vitest";
import { validateParams, DEFAULT_TITLE } from "../src/types.js";

describe("validateParams", () => {
  it("returns defaults when no params provided", () => {
    const result = validateParams(new URLSearchParams(), "slug", "article");
    expect(result.title).toBe(DEFAULT_TITLE);
    expect(result.topic).toBeUndefined();
    expect(result.date).toBeUndefined();
    expect(result.author).toBeUndefined();
    expect(result.slug).toBe("slug");
    expect(result.type).toBe("article");
  });

  it("uses provided params", () => {
    const search = new URLSearchParams({
      title: "My Title",
      topic: "AI",
      date: "2024-01-15",
      author: "Alice",
    });
    const result = validateParams(search, "my-title", "article");
    expect(result.title).toBe("My Title");
    expect(result.topic).toBe("AI");
    expect(result.date).toBe("2024-01-15");
    expect(result.author).toBe("Alice");
    expect(result.slug).toBe("my-title");
  });

  it("trims and truncates title", () => {
    const search = new URLSearchParams({
      title: "  " + "x".repeat(300),
    });
    const result = validateParams(search, "slug", "article");
    expect(result.title.length).toBeLessThanOrEqual(200);
    expect(result.title.startsWith("x")).toBe(true);
  });

  it("falls back to default title when empty after trim", () => {
    const search = new URLSearchParams({ title: "   " });
    const result = validateParams(search, "slug", "article");
    expect(result.title).toBe(DEFAULT_TITLE);
  });

  it("truncates topic to 60 chars", () => {
    const search = new URLSearchParams({ topic: "x".repeat(100) });
    const result = validateParams(search, "slug", "article");
    expect((result.topic || "").length).toBeLessThanOrEqual(60);
  });

  it("truncates author to 60 chars", () => {
    const search = new URLSearchParams({ author: "x".repeat(100) });
    const result = validateParams(search, "slug", "article");
    expect((result.author || "").length).toBeLessThanOrEqual(60);
  });

  it("truncates date to 20 chars", () => {
    const search = new URLSearchParams({ date: "x".repeat(50) });
    const result = validateParams(search, "slug", "article");
    expect((result.date || "").length).toBeLessThanOrEqual(20);
  });
});
