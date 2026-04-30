import { Hono } from "hono";
import { renderSVG } from "./render.js";
import { validateParams } from "./types.js";
import type { OGParams } from "./types.js";

const app = new Hono();

const CACHE_CONTROL = "public, max-age=86400, s-maxage=31536000";

function handleRender(c: any, params: OGParams) {
  const svg = renderSVG(params);
  c.header("Cache-Control", CACHE_CONTROL);
  c.header("Content-Type", "image/svg+xml");
  c.header("Vary", "Accept");
  return c.body(svg, 200);
}

app.get("/article/:slug.png", (c) => {
  const slug = c.req.param("slug") || "";
  const params = validateParams(new URL(c.req.url).searchParams, slug, "article");
  return handleRender(c, params);
});

app.get("/topic/:slug.png", (c) => {
  const slug = c.req.param("slug") || "";
  const params = validateParams(new URL(c.req.url).searchParams, slug, "topic");
  return handleRender(c, params);
});

app.get("/default.png", (c) => {
  const params = validateParams(new URL(c.req.url).searchParams, "default", "default");
  return handleRender(c, params);
});

// Health check
app.get("/health", (c) => {
  return c.json({ status: "ok" });
});

export default app;
