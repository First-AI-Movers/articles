import { describe, it, expect } from "vitest";
import { SELF } from "cloudflare:test";

// For now, import the worker so we can test it in integration mode
// Integration testing via SELF is preferred in the workers vitest pool

describe("og-worker", () => {
  it("returns SVG for article route", async () => {
    const request = new Request(
      "http://localhost/article/my-article.png?title=Hello+World&topic=AI&date=2024-01-15&author=Alice"
    );
    const response = await SELF.fetch(request);
    expect(response.status).toBe(200);
    expect(response.headers.get("Content-Type")).toBe("image/svg+xml");
    expect(response.headers.get("Cache-Control")).toContain("max-age=86400");
    const body = await response.text();
    expect(body).toContain("Hello World");
    expect(body).toContain("AI");
    expect(body).toContain("2024-01-15");
    expect(body).toContain("Alice");
    expect(body).toContain("First AI Movers");
  });

  it("returns SVG for topic route", async () => {
    const request = new Request(
      "http://localhost/topic/ai.png?title=AI+Trends"
    );
    const response = await SELF.fetch(request);
    expect(response.status).toBe(200);
    expect(response.headers.get("Content-Type")).toBe("image/svg+xml");
    const body = await response.text();
    expect(body).toContain("AI Trends");
  });

  it("returns SVG for default route", async () => {
    const request = new Request("http://localhost/default.png");
    const response = await SELF.fetch(request);
    expect(response.status).toBe(200);
    expect(response.headers.get("Content-Type")).toBe("image/svg+xml");
    const body = await response.text();
    expect(body).toContain("First AI Movers");
  });

  it("health check returns JSON", async () => {
    const request = new Request("http://localhost/health");
    const response = await SELF.fetch(request);
    expect(response.status).toBe(200);
    expect(response.headers.get("Content-Type")).toContain("application/json");
    const body = await response.json() as { status: string };
    expect(body.status).toBe("ok");
  });

  it("handles missing params gracefully", async () => {
    const request = new Request("http://localhost/article/test.png");
    const response = await SELF.fetch(request);
    expect(response.status).toBe(200);
    const body = await response.text();
    expect(body).toContain("First AI Movers");
  });

  it("escapes XSS attempts in title", async () => {
    const request = new Request(
      'http://localhost/article/test.png?title=<script>alert(1)</script>'
    );
    const response = await SELF.fetch(request);
    expect(response.status).toBe(200);
    const body = await response.text();
    expect(body).not.toContain("<script>");
    expect(body).toContain("&lt;script&gt;");
  });

  it("varies on Accept header", async () => {
    const request = new Request("http://localhost/default.png");
    const response = await SELF.fetch(request);
    expect(response.headers.get("Vary")).toBe("Accept");
  });
});
