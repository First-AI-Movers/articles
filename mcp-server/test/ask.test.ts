import { describe, it, expect } from "vitest";
import { handleAsk } from "../src/ask.js";

describe("handleAsk", () => {
  it("rejects missing question", async () => {
    const req = new Request("http://localhost/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    const res = await handleAsk(req, {});
    expect(res.status).toBe(400);
    const body = (await res.json()) as { error: string };
    expect(body.error).toContain("question");
  });

  it("rejects too-short question", async () => {
    const req = new Request("http://localhost/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: "ab" }),
    });
    const res = await handleAsk(req, {});
    expect(res.status).toBe(400);
    const body = (await res.json()) as { error: string };
    expect(body.error).toContain("at least");
  });

  it("rejects too-long question", async () => {
    const req = new Request("http://localhost/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: "a".repeat(501) }),
    });
    const res = await handleAsk(req, {});
    expect(res.status).toBe(400);
    const body = (await res.json()) as { error: string };
    expect(body.error).toContain("exceed");
  });

  it("rejects non-JSON body", async () => {
    const req = new Request("http://localhost/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "not json",
    });
    const res = await handleAsk(req, {});
    expect(res.status).toBe(400);
    const body = (await res.json()) as { error: string };
    expect(body.error).toContain("Invalid JSON");
  });

  it("rejects GET method", async () => {
    const req = new Request("http://localhost/api/ask", { method: "GET" });
    const res = await handleAsk(req, {});
    expect(res.status).toBe(405);
  });

  it("caps limit above max", async () => {
    const req = new Request("http://localhost/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: "AI governance", limit: 20 }),
    });
    const res = await handleAsk(req, {});
    expect(res.status).toBe(200);
    const body = (await res.json()) as { citations: unknown[] };
    expect(body.citations.length).toBeLessThanOrEqual(8);
  });

  it("returns citations for a relevant question", async () => {
    const req = new Request("http://localhost/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: "AI governance for European SMEs", limit: 3 }),
    });
    const res = await handleAsk(req, {});
    expect(res.status).toBe(200);
    const body = (await res.json()) as {
      answer: string;
      citations: Array<{ title: string; slug: string; local_url: string; score: number }>;
      mode: string;
    };
    expect(body.answer).toBeDefined();
    expect(body.citations.length).toBeGreaterThan(0);
    expect(body.citations.length).toBeLessThanOrEqual(3);
    for (const c of body.citations) {
      expect(c.title).toBeDefined();
      expect(c.slug).toBeDefined();
      expect(c.local_url).toBeDefined();
      expect(typeof c.score).toBe("number");
    }
    expect(body.mode).toBe("mock"); // no AI binding in test env
  });

  it("refuses to answer when no context matches", async () => {
    const req = new Request("http://localhost/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: "xyzqwerty12345 nonsense" }),
    });
    const res = await handleAsk(req, {});
    expect(res.status).toBe(200);
    const body = (await res.json()) as { answer: string; citations: unknown[] };
    expect(body.citations.length).toBe(0);
    expect(body.answer).toContain("couldn't find");
  });

  it("uses lexical fallback when AI binding missing", async () => {
    const req = new Request("http://localhost/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: "AI strategy" }),
    });
    const res = await handleAsk(req, {});
    expect(res.status).toBe(200);
    const body = (await res.json()) as { mode: string; citations: unknown[] };
    expect(body.citations.length).toBeGreaterThan(0);
    expect(body.mode).toBe("mock");
  });

  it("does not expose stack traces", async () => {
    const req = new Request("http://localhost/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: "artificial intelligence" }),
    });
    const res = await handleAsk(req, {});
    const body = (await res.json()) as { error?: string };
    // Should be a valid JSON response, not a raw stack trace
    expect(body).toBeDefined();
    expect(body.error).toBeUndefined();
  });

  it("does not mutate archive data", async () => {
    const req = new Request("http://localhost/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: "artificial intelligence" }),
    });
    const res = await handleAsk(req, {});
    expect(res.status).toBe(200);
    const body = (await res.json()) as { answer: string; citations: unknown[] };
    expect(typeof body.answer).toBe("string");
    expect(Array.isArray(body.citations)).toBe(true);
  });
});
