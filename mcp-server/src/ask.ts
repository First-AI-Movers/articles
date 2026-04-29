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
  score: number;
}

export interface AskResponse {
  answer: string;
  citations: Citation[];
  mode: "lexical" | "semantic" | "mock";
}

const MAX_QUESTION_LEN = 500;
const MIN_QUESTION_LEN = 3;
const DEFAULT_LIMIT = 5;
const MAX_LIMIT = 8;
const MAX_EXCERPT_CHARS = 800;
const MAX_CONTEXT_ARTICLES = 5;

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

function buildContext(results: SearchResult[]): string {
  const capped = results.slice(0, MAX_CONTEXT_ARTICLES);
  const parts: string[] = [];
  for (const r of capped) {
    const excerpt = r.excerpt.slice(0, MAX_EXCERPT_CHARS);
    parts.push(
      `---\nTitle: ${r.title}\nURL: ${r.local_url}\nScore: ${r.score}\nExcerpt: ${excerpt}\n---`
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

function toCitations(results: SearchResult[]): Citation[] {
  return results.map((r) => ({
    title: r.title,
    slug: r.slug,
    local_url: r.local_url,
    canonical_url: r.canonical_url,
    score: r.score,
  }));
}

async function generateAnswer(
  question: string,
  results: SearchResult[],
  env: Record<string, unknown>
): Promise<{ answer: string; mode: "lexical" | "semantic" | "mock" }> {
  const aiBinding = env.AI as
    | { run: (model: string, inputs: unknown) => Promise<{ response?: string }> }
    | undefined;

  const context = buildContext(results);

  // If no results, return early without calling AI
  if (results.length === 0) {
    return {
      answer:
        "I couldn't find any strongly relevant articles in the archive for that question. " +
        "Try browsing the [topic hubs](/topics/) or rephrasing your question.",
      mode: "lexical",
    };
  }

  if (!aiBinding) {
    // No AI binding available — return a structured mock response for testing
    const titles = results.map((r) => `"${r.title}"`).join("; ");
    return {
      answer:
        `[POC mode — no AI model available] Based on the archive, these articles may be relevant: ${titles}. ` +
        `Deploy the Worker with a Workers AI binding to get generated answers.`,
      mode: "mock",
    };
  }

  const prompt = buildPrompt(question, context);

  try {
    const response = await aiBinding.run("@cf/meta/llama-3.1-8b-instruct", {
      prompt,
      max_tokens: 512,
    });

    const answer = response.response?.trim() || "";
    if (!answer) {
      return {
        answer:
          "The AI model returned an empty response. This may be a temporary issue. " +
          "Try again or browse the topic hubs directly.",
        mode: "lexical",
      };
    }

    return { answer, mode: "lexical" };
  } catch (e) {
    const err = e instanceof Error ? e.message : String(e);
    console.warn(`[ask] AI generation failed: ${err}`);
    return {
      answer:
        `The AI model encountered an error. Relevant articles were found but could not be summarized. ` +
        `See the citations below for direct links.`,
      mode: "lexical",
    };
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
    const results = await searchArticles(question, limit, undefined, env);

    const { answer, mode } = await generateAnswer(question, results, env);

    const payload: AskResponse = {
      answer,
      citations: toCitations(results),
      mode,
    };

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
