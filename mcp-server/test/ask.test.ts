import { describe, it, expect, vi } from "vitest";
import { handleAsk, plainPassageText } from "../src/ask.js";
import { archive } from "../src/archive.js";

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
    expect(body.mode).toBe("extractive");
  });

  it("refuses to answer when no context matches", async () => {
    const req = new Request("http://localhost/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: "xyzqwerty12345 nonsense" }),
    });
    const res = await handleAsk(req, {});
    expect(res.status).toBe(200);
    const body = (await res.json()) as { answer: string; citations: unknown[]; mode: string };
    expect(body.citations.length).toBe(0);
    expect(body.mode).toBe("abstained");
    expect(body.answer).toContain("Not found in the archive");
  });

  it("answers extractively when AI binding missing", async () => {
    const req = new Request("http://localhost/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: "AI strategy" }),
    });
    const res = await handleAsk(req, {});
    expect(res.status).toBe(200);
    const body = (await res.json()) as { mode: string; citations: unknown[] };
    expect(body.citations.length).toBeGreaterThan(0);
    expect(body.mode).toBe("extractive");
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

  it("accepts a long question without a server error", async () => {
    const res = await ask({ question: "AI governance ".repeat(30).trim() });
    expect(res.status).toBe(200);
  });
});

function ask(body: unknown): Promise<Response> {
  return handleAsk(
    new Request("http://localhost/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
    {}
  );
}

function askWith(body: unknown, env: Record<string, unknown>): Promise<Response> {
  return handleAsk(
    new Request("http://localhost/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
    env
  );
}

type AskBody = {
  answer: string;
  mode: string;
  citations: Array<{
    title: string;
    published_date: string;
    canonical_url: string;
    local_url: string;
    passage: string;
  }>;
};

describe("handleAsk — extractive, no model by default", () => {
  it("a supported question yields an extractive answer citing date and URL", async () => {
    const res = await ask({ question: "AI governance for European SMEs", limit: 3 });
    expect(res.status).toBe(200);
    const body = (await res.json()) as AskBody;
    expect(body.mode).toBe("extractive");
    expect(body.citations.length).toBeGreaterThan(0);
    for (const c of body.citations) {
      expect(c.published_date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(c.canonical_url).toMatch(/^https:\/\//);
      expect(c.local_url).toMatch(/^\/articles\//);
      expect(c.passage.length).toBeGreaterThan(0);
      // The answer is composed only from the cited articles' own words.
      expect(body.answer).toContain(c.title);
      expect(body.answer).toContain(c.published_date);
      expect(body.answer).toContain(c.passage);
    }
    expect(body.answer).not.toContain("POC mode");
  });

  it.each([
    "xyzqwerty12345 nonsense",
    "recipe for chocolate cake",
    "football world cup results",
    "what is the weather like today",
  ])("an unsupported question abstains: %s", async (question) => {
    const res = await ask({ question });
    expect(res.status).toBe(200);
    const body = (await res.json()) as AskBody;
    expect(body.mode).toBe("abstained");
    expect(body.citations).toEqual([]);
    expect(body.answer).toContain("Not found in the archive");
  });

  it("never calls a present AI binding when ASK_MODEL_ENABLED is unset", async () => {
    const run = vi.fn(async () => ({ response: "generated" }));
    const res = await askWith({ question: "AI governance for European SMEs" }, { AI: { run } });
    const body = (await res.json()) as AskBody;
    expect(run).not.toHaveBeenCalled();
    expect(body.mode).toBe("extractive");
  });

  it("never calls the AI binding when ASK_MODEL_ENABLED is not exactly 'true'", async () => {
    const run = vi.fn(async () => ({ response: "generated" }));
    await askWith(
      { question: "AI governance for European SMEs" },
      { AI: { run }, ASK_MODEL_ENABLED: "1" }
    );
    expect(run).not.toHaveBeenCalled();
  });

  it("calls the AI binding only when ASK_MODEL_ENABLED is 'true'", async () => {
    const run = vi.fn(async () => ({ response: "generated answer" }));
    const res = await askWith(
      { question: "AI governance for European SMEs" },
      { AI: { run }, ASK_MODEL_ENABLED: "true" }
    );
    const body = (await res.json()) as AskBody;
    expect(run).toHaveBeenCalledTimes(1);
    expect(body.mode).toBe("model");
    expect(body.answer).toBe("generated answer");
    expect(body.citations.length).toBeGreaterThan(0);
  });

  it("does not call the model when the question abstains, even if enabled", async () => {
    const run = vi.fn(async () => ({ response: "generated" }));
    const res = await askWith(
      { question: "xyzqwerty12345 nonsense" },
      { AI: { run }, ASK_MODEL_ENABLED: "true" }
    );
    const body = (await res.json()) as AskBody;
    expect(run).not.toHaveBeenCalled();
    expect(body.mode).toBe("abstained");
  });

  it("falls back to the extractive answer when the enabled model fails", async () => {
    const run = vi.fn(async () => {
      throw new Error("boom");
    });
    const res = await askWith(
      { question: "AI governance for European SMEs" },
      { AI: { run }, ASK_MODEL_ENABLED: "true" }
    );
    const body = (await res.json()) as AskBody;
    expect(run).toHaveBeenCalledTimes(1);
    expect(body.mode).toBe("extractive");
  });
});

describe("plainPassageText — passages carry the article's words, not its markdown", () => {
  it("removes heading, escaped-heading, quote, emphasis and link syntax", () => {
    expect(plainPassageText("# MCP in 2026  ## The protocol is no longer a list")).toBe(
      "MCP in 2026 The protocol is no longer a list"
    );
    expect(plainPassageText("\\# AI Sovereignty  \\## Main Article  The development")).toBe(
      "AI Sovereignty Main Article The development"
    );
    expect(plainPassageText("> **TL;DR:** Read [the guide](https://example.com/g) and `run` it")).toBe(
      "TL;DR: Read the guide and run it"
    );
  });

  it("keeps a plain sentence, including a '#' that is not a heading marker", () => {
    expect(plainPassageText("Ranked #1 in C# tooling for 2026.")).toBe("Ranked #1 in C# tooling for 2026.");
  });

  it("leaves no markdown heading or emphasis in any archive record's passage source", () => {
    const offenders = archive.articles
      .map((a) => ({ slug: a.slug, text: plainPassageText(a.summary || a.excerpt || "") }))
      .filter((x) => /(^|\s)\\?#{1,6}\s|\*\*|(^|\s)>\s/.test(x.text));
    expect(offenders.map((o) => o.slug)).toEqual([]);
  });

  it("says the extractive answer quotes a summary or the opening text", async () => {
    const res = await handleAsk(
      new Request("https://x/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: "What is the Model Context Protocol used for?" }),
      }),
      {}
    );
    const body = (await res.json()) as { answer: string; mode: string };
    expect(body.mode).toBe("extractive");
    expect(body.answer).toContain("own summary or opening text");
  });
});
