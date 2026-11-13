import { describe, it, expect, vi, afterEach } from "vitest";
import { fetchFullText, fullTextUrl, stripFrontMatter, FULL_TEXT_MAX_CHARS } from "../src/fulltext.js";
import { archive, type ArticleRecord } from "../src/archive.js";

const article: ArticleRecord = {
  slug: "before-you-automate-a-workflow-7-questions",
  folder: "2026-09-27-before-you-automate-a-workflow-7-questions",
  title: "Before You Automate a Workflow",
  published_date: "2026-09-27",
  canonical_url: "https://radar.firstaimovers.com/before-you-automate-a-workflow-7-questions",
  local_url: "/articles/before-you-automate-a-workflow-7-questions/",
  topics: [],
  summary: "",
  excerpt: "",
};
const env = { ARCHIVE_SITE_URL: "https://articles.firstaimovers.com" };
const BODY = "# Title\n\n" + "x".repeat(45_000) + "END";

function stubFetch(response: Response | Error) {
  const fn = vi.fn(async (_url: string, _init?: RequestInit) => {
    if (response instanceof Error) throw response;
    return response.clone();
  });
  vi.stubGlobal("fetch", fn);
  return fn;
}
afterEach(() => vi.unstubAllGlobals());

describe("full text for get_article (#508)", () => {
  it("fetches the archive's own published article.md for the record's folder", async () => {
    const fn = stubFetch(new Response(`---\ntitle: "T"\n---\n${BODY}`));
    const r = await fetchFullText(article, env);
    expect(fn).toHaveBeenCalledTimes(1);
    expect(fn.mock.calls[0][0]).toBe(
      "https://articles.firstaimovers.com/articles/2026-09-27-before-you-automate-a-workflow-7-questions/article.md"
    );
    if (!r.ok) throw new Error(r.error);
    expect(r.page.text.startsWith("# Title")).toBe(true); // front matter dropped
    expect(r.page.source_url).toBe(fn.mock.calls[0][0]);
    expect(r.page.license).toContain("CC BY 4.0");
    expect(r.page.attribution).toContain(article.canonical_url);
    expect(r.page.local_url).toBe("https://articles.firstaimovers.com/articles/before-you-automate-a-workflow-7-questions/");
  });

  it("returns at most FULL_TEXT_MAX_CHARS and pages through the rest without loss", async () => {
    stubFetch(new Response(BODY));
    let offset = 0;
    let joined = "";
    for (let i = 0; i < 10; i++) {
      const r = await fetchFullText(article, env, offset);
      if (!r.ok) throw new Error(r.error);
      expect(r.page.returned_chars).toBeLessThanOrEqual(FULL_TEXT_MAX_CHARS);
      expect(r.page.total_chars).toBe(BODY.length);
      joined += r.page.text;
      if (r.page.next_offset === null) {
        expect(r.page.truncated).toBe(false);
        break;
      }
      expect(r.page.truncated).toBe(true);
      offset = r.page.next_offset;
    }
    expect(joined).toBe(BODY);
  });

  it("clamps an offset past the end to an empty final page", async () => {
    stubFetch(new Response("short body"));
    const r = await fetchFullText(article, env, 10_000);
    if (!r.ok) throw new Error(r.error);
    expect(r.page.text).toBe("");
    expect(r.page.next_offset).toBeNull();
  });

  it("reports an HTTP failure or a network error instead of throwing", async () => {
    stubFetch(new Response("nope", { status: 404 }));
    expect(await fetchFullText(article, env)).toEqual({ ok: false, error: "Full text could not be fetched (HTTP 404)" });
    stubFetch(new Error("network down"));
    expect(await fetchFullText(article, env)).toEqual({ ok: false, error: "Full text could not be fetched" });
  });

  it("never builds a URL from a missing or unsafe folder", async () => {
    const fn = stubFetch(new Response("x"));
    for (const folder of [undefined, "", "../secrets", "a/b", "UPPER", "x?y=1"]) {
      expect(fullTextUrl({ ...article, folder }, env)).toBeNull();
      expect((await fetchFullText({ ...article, folder }, env)).ok).toBe(false);
    }
    expect(fn).not.toHaveBeenCalled();
  });

  it("every archive record names a safe folder, so every article has a full-text URL", () => {
    const missing = archive.articles.filter((a) => fullTextUrl(a, env) === null).map((a) => a.slug);
    expect(missing).toEqual([]);
  });

  it("strips only a leading front-matter block", () => {
    expect(stripFrontMatter("---\na: 1\n---\nBody --- with dashes")).toBe("Body --- with dashes");
    expect(stripFrontMatter("No front matter")).toBe("No front matter");
  });
});
