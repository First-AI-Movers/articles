import { describe, it, expect } from "vitest";
import { buildSVG } from "../src/svg-template.js";
import type { OGParams } from "../src/types.js";

function makeParams(overrides: Partial<OGParams> = {}): OGParams {
  return {
    title: "Hello World",
    topic: "",
    date: "",
    author: "",
    slug: "hello-world",
    type: "article",
    ...overrides,
  };
}

describe("buildSVG", () => {
  it("returns a valid SVG string", () => {
    const svg = buildSVG(makeParams());
    expect(svg).toContain('<svg xmlns="http://www.w3.org/2000/svg"');
    expect(svg).toContain("width=\"1200\"");
    expect(svg).toContain("height=\"630\"");
    expect(svg).toContain("</svg>");
  });

  it("includes the title text", () => {
    const svg = buildSVG(makeParams({ title: "Building AI Systems" }));
    expect(svg).toContain("Building AI Systems");
  });

  it("escapes XML entities in title", () => {
    const svg = buildSVG(makeParams({ title: "A < B & C > D" }));
    expect(svg).not.toContain("A < B & C > D");
    expect(svg).toContain("A &lt; B &amp; C &gt; D");
  });

  it("includes topic chip when provided", () => {
    const svg = buildSVG(makeParams({ topic: "Machine Learning" }));
    expect(svg).toContain("Machine Learning");
    expect(svg).toContain('fill="#e67e45"');
  });

  it("includes date and author metadata", () => {
    const svg = buildSVG(makeParams({ date: "2024-01-15", author: "Alice" }));
    expect(svg).toContain("2024-01-15");
    expect(svg).toContain("Alice");
    expect(svg).toContain("·");
  });

  it("includes only date when author absent", () => {
    const svg = buildSVG(makeParams({ date: "2024-01-15" }));
    expect(svg).toContain("2024-01-15");
    expect(svg).not.toContain("·");
  });

  it("includes brand text", () => {
    const svg = buildSVG(makeParams());
    expect(svg).toContain("First AI Movers");
  });

  it("uses larger font for short titles", () => {
    const svg = buildSVG(makeParams({ title: "Short" }));
    expect(svg).toContain('font-size="64"');
  });

  it("uses medium font for medium titles", () => {
    const svg = buildSVG(makeParams({ title: "a".repeat(70) }));
    expect(svg).toContain('font-size="52"');
  });

  it("uses small font for long titles", () => {
    const svg = buildSVG(makeParams({ title: "a".repeat(120) }));
    expect(svg).toContain('font-size="40"');
  });

  it("wraps long titles into multiple lines", () => {
    const title = "word ".repeat(50);
    const svg = buildSVG(makeParams({ title }));
    const tspanCount = (svg.match(/<tspan/g) || []).length;
    expect(tspanCount).toBeGreaterThan(1);
  });

  it("truncates to max lines", () => {
    const title = "word ".repeat(100);
    const svg = buildSVG(makeParams({ title }));
    const tspanCount = (svg.match(/<tspan/g) || []).length;
    expect(tspanCount).toBeLessThanOrEqual(4);
  });
});
