import { describe, it, expect } from "vitest";
import worker from "../src/index.js";

const origin = "https://articles.firstaimovers.com";
const endpoint = "https://articles-api.firstaimovers.com/api/ask";
const env = { ARCHIVE_SITE_URL: origin };
const ctx = {} as ExecutionContext;

describe("Ask across the archive and API hostnames", () => {
  it("admits the archive JSON POST preflight", async () => {
    const response = await worker.fetch(new Request(endpoint, {
      method: "OPTIONS",
      headers: { Origin: origin, "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type" },
    }), env, ctx);
    expect(response.status).toBe(204);
    expect(response.headers.get("Access-Control-Allow-Origin")).toBe(origin);
    expect(response.headers.get("Access-Control-Allow-Methods")).toBe("POST, OPTIONS");
    expect(response.headers.get("Access-Control-Allow-Headers")).toBe("Content-Type");
    expect(response.headers.get("Vary")).toBe("Origin");
  });

  it.each([{}, { question: "AI governance" }])("makes answers and validation errors readable: %j", async (body) => {
    const response = await worker.fetch(new Request(endpoint, {
      method: "POST", headers: { Origin: origin, "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }), env, ctx);
    expect(response.status).toBe("question" in body ? 200 : 400);
    expect(response.headers.get("Access-Control-Allow-Origin")).toBe(origin);
    expect(response.headers.get("Vary")).toBe("Origin");
    expect(response.headers.has("Access-Control-Allow-Credentials")).toBe(false);
  });

  it.each(["https://elsewhere.example", "null", "https://articles.firstaimovers.com.evil.example"])("does not allow another browser origin: %s", async (otherOrigin) => {
    const response = await worker.fetch(new Request(endpoint, {
      method: "OPTIONS", headers: { Origin: otherOrigin },
    }), env, ctx);
    expect(response.status).toBe(403);
    expect(response.headers.has("Access-Control-Allow-Origin")).toBe(false);
  });

  it("leaves non-browser POST clients supported", async () => {
    const response = await worker.fetch(new Request(endpoint, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: "{}",
    }), env, ctx);
    expect(response.status).toBe(400);
    expect(response.headers.has("Access-Control-Allow-Origin")).toBe(false);
  });
});
