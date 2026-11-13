import { archive } from "./archive.js";
import { searchArticles } from "./search.js";
import type { SearchResult } from "./search.js";

export interface AskRequest {
  question: string;
  limit: number;
}

interface RawAskRequest {
  question: string;
  limit?: number;
}

export interface Citation {
  title: string;
  slug: string;
  local_url: string;
  canonical_url: string;
  published_date: string;
  passage: string;
  score: number;
}

/**
 * - "extractive": the answer is quoted from the matched articles' own public
 *   summaries, with no model call. This is the default.
 * - "abstained": nothing in the archive supports the question; no citations.
 * - "model": the opt-in Workers AI path (only when ASK_MODEL_ENABLED is "true").
 */
export type AskMode = "extractive" | "abstained" | "model";

export interface AskResponse {
  answer: string;
  citations: Citation[];
  mode: AskMode;
}

const MAX_QUESTION_LEN = 500;
const MIN_QUESTION_LEN = 3;
const DEFAULT_LIMIT = 5;
const MAX_LIMIT = 8;
const MAX_SEARCH_QUERY_LEN = 200;
const MAX_EXCERPT_CHARS = 800;
const MAX_PASSAGE_CHARS = 400;
const MAX_CONTEXT_ARTICLES = 5;
/** A result supports the question when at least this share of the question's
 * content terms appear as whole words in its title, topics or summary. */
const MIN_TERM_COVERAGE = 0.5;

export const ABSTAIN_ANSWER =
  "Not found in the archive. No article supports an answer to that question. " +
  "Try rephrasing it, or browse the topic hubs at /topics/.";

const STOPWORDS = new Set(
  (
    "the and for are but not you your with what when where which who whom why how " +
    "does did doing done can could should would will shall may might must about into " +
    "from that this these those than then there their them they have has had was were " +
    "been being its our ours out over under very just also any all some such only own " +
    "same too more most other like get got make made use used using tell know want need"
  ).split(" ")
);

function validateBody(body: unknown): { ok: false; error: string } | { ok: true; data: AskRequest } {
  if (typeof body !== "object" || body === null) {
    return { ok: false, error: "Request body must be a JSON object" };
  }
  const b = body as RawAskRequest;

  if (typeof b.question !== "string") {
    return { ok: false, error: "Field 'question' is required and must be a string" };
  }

  const question = b.question.trim();
  if (question.length < MIN_QUESTION_LEN) {
    return { ok: false, error: `Question must be at least ${MIN_QUESTION_LEN} characters` };
  }
  if (question.length > MAX_QUESTION_LEN) {
    return { ok: false, error: `Question must not exceed ${MAX_QUESTION_LEN} characters` };
  }

  let limit = DEFAULT_LIMIT;
  if (b.limit !== undefined) {
    if (typeof b.limit !== "number" || !Number.isFinite(b.limit)) {
      return { ok: false, error: "Field 'limit' must be a number" };
    }
    limit = Math.min(Math.max(1, Math.floor(b.limit)), MAX_LIMIT);
  }

  return { ok: true, data: { question, limit } };
}

/** Content terms of a question: lowercase words longer than two characters
 * that are not stopwords. */
export function contentTerms(question: string): string[] {
  const words = question.toLowerCase().match(/[\p{L}\p{N}]+/gu) ?? [];
  return Array.from(new Set(words.filter((w) => w.length > 2 && !STOPWORDS.has(w))));
}

function wordSet(text: string): Set<string> {
  return new Set(text.toLowerCase().match(/[\p{L}\p{N}]+/gu) ?? []);
}

/**
 * Abstain rule. Search scores alone cannot separate support from noise: the
 * lexical scorer matches substrings ("car" in "care", "the" everywhere), and
 * semantic cosine scores are always positive. So a result counts only when at
 * least half of the question's content terms appear as whole words in that
 * article's own title, topics or summary. No supporting result means abstain.
 */
export function supportingResults(question: string, results: SearchResult[]): SearchResult[] {
  const terms = contentTerms(question);
  if (terms.length === 0) return [];
  return results.filter((r) => {
    if (r.score <= 0) return false;
    const record = archive.articles.find((a) => a.slug === r.slug);
    const words = wordSet(
      [r.title, r.topics.join(" "), record?.summary ?? "", r.excerpt].join(" ")
    );
    const hits = terms.filter((t) => words.has(t)).length;
    return hits / terms.length >= MIN_TERM_COVERAGE;
  });
}

/**
 * The article's own words with markdown syntax removed. Most archive records
 * (649 of 942 on 2026-11-13) have no summary, so the passage falls back to the
 * excerpt, which is the article's opening markdown: `# Title ## Section`,
 * sometimes escaped as `\# Title`. Remove the markup, never the words.
 */
export function plainPassageText(text: string): string {
  return text
    .replace(/\\([\\`*_{}\[\]()#+\-.!>|~])/g, "$1") // markdown escapes: \# -> #
    .replace(/!?\[([^\]]*)\]\([^)]*\)/g, "$1") // [text](url) and images -> text
    .replace(/(^|\s)#{1,6}(?=\s)/g, "$1") // heading markers
    .replace(/(^|\s)>(?=\s)/g, "$1") // blockquote markers
    .replace(/(\*\*|__|`)/g, "") // bold and inline code
    .replace(/\s+/g, " ")
    .trim();
}

function passageFor(r: SearchResult): string {
  const record = archive.articles.find((a) => a.slug === r.slug);
  const text = plainPassageText(record?.summary || r.excerpt || "");
  if (text.length <= MAX_PASSAGE_CHARS) return text;
  return text.slice(0, MAX_PASSAGE_CHARS).replace(/\s+\S*$/, "") + "…";
}

function toCitations(results: SearchResult[]): Citation[] {
  return results.map((r) => ({
    title: r.title,
    slug: r.slug,
    local_url: r.local_url,
    canonical_url: r.canonical_url,
    published_date: r.published_date,
    passage: passageFor(r),
    score: r.score,
  }));
}

/** Compose an answer only from the cited articles' own words. */
function extractiveAnswer(citations: Citation[]): string {
  const parts = [
    "From the archive (quoted from each article's own summary or opening text; no AI model wrote this answer):",
  ];
  for (const c of citations) {
    parts.push(`"${c.title}" (${c.published_date}): ${c.passage}`);
  }
  return parts.join("\n\n");
}

function buildContext(citations: Citation[]): string {
  const parts: string[] = [];
  for (const c of citations.slice(0, MAX_CONTEXT_ARTICLES)) {
    parts.push(
      `---\nTitle: ${c.title}\nDate: ${c.published_date}\nURL: ${c.local_url}\nExcerpt: ${c.passage.slice(0, MAX_EXCERPT_CHARS)}\n---`
    );
  }
  return parts.join("\n");
}

function buildPrompt(question: string, context: string): string {
  return (
    `You are a helpful research assistant for the First AI Movers article archive. ` +
    `Answer the user's question using ONLY the provided archive excerpts below. ` +
    `If the context is insufficient to answer confidently, say so clearly. ` +
    `Always cite the source articles by title. ` +
    `Do not invent facts, dates, URLs, or claims. ` +
    `Do not mention that you are an AI or that you have limited context.\n\n` +
    `Archive excerpts:\n${context}\n\n` +
    `User question: ${question}\n\n` +
    `Answer:`
  );
}

type AiBinding = { run: (model: string, inputs: unknown) => Promise<{ response?: string }> };

async function generateAnswer(
  question: string,
  citations: Citation[],
  env: Record<string, unknown>
): Promise<{ answer: string; mode: AskMode }> {
  if (citations.length === 0) {
    return { answer: ABSTAIN_ANSWER, mode: "abstained" };
  }

  const extractive = { answer: extractiveAnswer(citations), mode: "extractive" as const };

  // The model path is opt-in only. A present AI binding is never called
  // unless ASK_MODEL_ENABLED is exactly "true".
  const aiBinding = env.AI as AiBinding | undefined;
  if (env.ASK_MODEL_ENABLED !== "true" || !aiBinding) {
    return extractive;
  }

  try {
    const response = await aiBinding.run("@cf/meta/llama-3.1-8b-instruct", {
      prompt: buildPrompt(question, buildContext(citations)),
      max_tokens: 512,
    });
    const answer = response.response?.trim() || "";
    return answer ? { answer, mode: "model" } : extractive;
  } catch (e) {
    // Log the failure class only; never the question.
    const err = e instanceof Error ? e.name : "unknown";
    console.warn(`[ask] AI generation failed (${err}); returned the extractive answer`);
    return extractive;
  }
}

export async function handleAsk(
  request: Request,
  env: Record<string, unknown>
): Promise<Response> {
  if (request.method !== "POST") {
    return new Response(
      JSON.stringify({ error: "Method not allowed. Use POST." }),
      { status: 405, headers: { "Content-Type": "application/json" } }
    );
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return new Response(
      JSON.stringify({ error: "Invalid JSON body" }),
      { status: 400, headers: { "Content-Type": "application/json" } }
    );
  }

  const validated = validateBody(body);
  if (!validated.ok) {
    return new Response(
      JSON.stringify({ error: validated.error }),
      { status: 400, headers: { "Content-Type": "application/json" } }
    );
  }

  const { question, limit } = validated.data;

  try {
    const results = await searchArticles(
      question.slice(0, MAX_SEARCH_QUERY_LEN),
      limit,
      undefined,
      env
    );
    const citations = toCitations(supportingResults(question, results));

    const { answer, mode } = await generateAnswer(question, citations, env);

    const payload: AskResponse = { answer, citations, mode };

    return new Response(JSON.stringify(payload), {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
      },
    });
  } catch (e) {
    const err = e instanceof Error ? e.message : String(e);
    console.error(`[ask] Unexpected error: ${err}`);
    return new Response(
      JSON.stringify({ error: "An unexpected error occurred. Please try again." }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
}
