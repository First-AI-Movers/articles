import type { ArticleRecord } from "./archive.js";

/**
 * Bounded, cited full text for `get_article` (#508 step 4).
 *
 * The text is fetched at request time from the archive's own published copy,
 * `<ARCHIVE_SITE_URL>/articles/<folder>/article.md`, and cached at the edge. It
 * is not bundled: the 942 articles are about 3.4 MB gzipped, more than the
 * Worker can carry on top of its own code. The archive is CC BY 4.0 and the
 * same text is already public on the site and in llms-full.txt.
 */
export const FULL_TEXT_MAX_CHARS = 20_000;
export const FULL_TEXT_LICENSE = "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)";
const DEFAULT_SITE = "https://articles.firstaimovers.com";
const FETCH_TIMEOUT_MS = 8_000;
const EDGE_CACHE_SECONDS = 3_600;
const SAFE_FOLDER = /^[0-9a-z][0-9a-z-]*$/;

export interface FullTextPage {
  text: string;
  offset: number;
  returned_chars: number;
  total_chars: number;
  truncated: boolean;
  next_offset: number | null;
  source_url: string;
  canonical_url: string;
  local_url: string;
  license: string;
  attribution: string;
}

export type FullTextResult = { ok: true; page: FullTextPage } | { ok: false; error: string };

/** Drop a leading YAML front-matter block, keeping the article body. */
export function stripFrontMatter(text: string): string {
  if (text.startsWith("---")) {
    const end = text.indexOf("\n---", 3);
    if (end !== -1) return text.slice(end + 4).replace(/^\s+/, "");
  }
  return text.trim();
}

function siteOrigin(env: Record<string, unknown>): string {
  return new URL(String(env.ARCHIVE_SITE_URL || DEFAULT_SITE)).origin;
}

/** The published article.md URL, or null when the record cannot name one safely. */
export function fullTextUrl(article: ArticleRecord, env: Record<string, unknown>): string | null {
  if (!article.folder || !SAFE_FOLDER.test(article.folder)) return null;
  return `${siteOrigin(env)}/articles/${article.folder}/article.md`;
}

export async function fetchFullText(
  article: ArticleRecord,
  env: Record<string, unknown>,
  offset = 0
): Promise<FullTextResult> {
  const url = fullTextUrl(article, env);
  if (!url) return { ok: false, error: "Full text is not available for this article" };

  let response: Response;
  try {
    response = await fetch(url, {
      headers: { "User-Agent": "faim-mcp-server/1.0" },
      signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
      cf: { cacheTtl: EDGE_CACHE_SECONDS, cacheEverything: true },
    } as RequestInit);
  } catch {
    return { ok: false, error: "Full text could not be fetched" };
  }
  if (!response.ok) {
    return { ok: false, error: `Full text could not be fetched (HTTP ${response.status})` };
  }

  const body = stripFrontMatter(await response.text());
  const total = body.length;
  const start = Math.min(Math.max(0, Math.floor(offset)), total);
  const text = body.slice(start, start + FULL_TEXT_MAX_CHARS);
  const end = start + text.length;
  return {
    ok: true,
    page: {
      text,
      offset: start,
      returned_chars: text.length,
      total_chars: total,
      truncated: end < total,
      next_offset: end < total ? end : null,
      source_url: url,
      canonical_url: article.canonical_url,
      local_url: `${siteOrigin(env)}${article.local_url}`,
      license: FULL_TEXT_LICENSE,
      attribution: `"${article.title}" by Dr. Hernani Costa, First AI Movers (${article.canonical_url})`,
    },
  };
}
