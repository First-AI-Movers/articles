import {
  archive,
  getEmbeddings,
  type ArticleRecord,
  type EmbeddingMap,
} from "./archive.js";

export interface SearchResult {
  title: string;
  slug: string;
  local_url: string;
  canonical_url: string;
  topics: string[];
  published_date: string;
  score: number;
  excerpt: string;
}

const MAX_QUERY_LEN = 200;
const DEFAULT_LIMIT = 5;
const MAX_LIMIT = 10;

function lexicalScore(query: string, article: ArticleRecord): number {
  const q = query.toLowerCase();
  const qWords = q.split(/\s+/).filter((w) => w.length > 2);
  let score = 0;

  // Title match is highest weight
  const title = article.title.toLowerCase();
  if (title.includes(q)) score += 10;
  for (const w of qWords) {
    if (title.includes(w)) score += 3;
  }

  // Topic match
  for (const topic of article.topics) {
    const t = topic.toLowerCase();
    if (t.includes(q)) score += 5;
    for (const w of qWords) {
      if (t.includes(w)) score += 2;
    }
  }

  // Summary match
  const summary = article.summary.toLowerCase();
  if (summary.includes(q)) score += 4;
  for (const w of qWords) {
    if (summary.includes(w)) score += 1;
  }

  // Excerpt match
  const excerpt = article.excerpt.toLowerCase();
  if (excerpt.includes(q)) score += 2;
  for (const w of qWords) {
    if (excerpt.includes(w)) score += 0.5;
  }

  return score;
}

function cosineSimilarity(a: number[], b: number[]): number {
  let dot = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

async function semanticSearch(
  query: string,
  limit: number,
  env: Record<string, unknown>,
  embeddings: EmbeddingMap
): Promise<SearchResult[]> {
  const aiBinding = env.AI as
    | { run: (model: string, inputs: unknown) => Promise<{ data: number[][] }> }
    | undefined;

  if (!aiBinding) {
    throw new Error("AI binding not available for semantic search");
  }

  // Embed query using Workers AI
  const embeddingResponse = await aiBinding.run("@cf/baai/bge-small-en-v1.5", {
    text: [query],
  });

  const queryVector = embeddingResponse.data?.[0];
  if (!queryVector || queryVector.length !== 384) {
    throw new Error("Unexpected embedding dimension from Workers AI");
  }

  // Score all articles with embeddings
  const scored: Array<{ article: ArticleRecord; score: number }> = [];
  for (const article of archive.articles) {
    const vec = embeddings[article.slug];
    if (!vec) continue;
    const sim = cosineSimilarity(queryVector, vec);
    scored.push({ article, score: sim });
  }

  scored.sort((a, b) => b.score - a.score);

  return scored.slice(0, limit).map(({ article, score }) => ({
    title: article.title,
    slug: article.slug,
    local_url: article.local_url,
    canonical_url: article.canonical_url,
    topics: article.topics,
    published_date: article.published_date,
    score: Math.round(score * 10000) / 10000,
    excerpt: article.excerpt.slice(0, 200),
  }));
}

export async function searchArticles(
  query: string,
  limit: number,
  topicFilter: string | undefined,
  env: Record<string, unknown>
): Promise<SearchResult[]> {
  if (!query || query.trim().length === 0) {
    throw new Error("Query must not be empty");
  }
  if (query.length > MAX_QUERY_LEN) {
    throw new Error(`Query exceeds maximum length of ${MAX_QUERY_LEN}`);
  }

  const cap = Math.min(Math.max(1, limit || DEFAULT_LIMIT), MAX_LIMIT);
  const semanticEnabled = (env.SEMANTIC_SEARCH_ENABLED as string) === "true";

  let candidates = archive.articles;
  if (topicFilter) {
    const topicName = topicFilter.replace(/-/g, " ");
    candidates = candidates.filter((a) =>
      a.topics.some(
        (t) =>
          t.toLowerCase().replace(/\s+/g, "-") === topicFilter.toLowerCase() ||
          t.toLowerCase() === topicName.toLowerCase()
      )
    );
  }

  // Try semantic search if enabled
  if (semanticEnabled) {
    try {
      const embeddings = await getEmbeddings(env);
      if (Object.keys(embeddings).length > 0) {
        return await semanticSearch(query, cap, env, embeddings);
      }
    } catch (e) {
      // Fall back to lexical search
      const err = e instanceof Error ? e.message : String(e);
      console.warn(`[mcp] Semantic search failed, falling back to lexical: ${err}`);
    }
  }

  // Lexical search
  const scored = candidates.map((article) => ({
    article,
    score: lexicalScore(query, article),
  }));

  scored.sort((a, b) => b.score - a.score);

  return scored
    .filter((s) => s.score > 0)
    .slice(0, cap)
    .map(({ article, score }) => ({
      title: article.title,
      slug: article.slug,
      local_url: article.local_url,
      canonical_url: article.canonical_url,
      topics: article.topics,
      published_date: article.published_date,
      score,
      excerpt: article.excerpt.slice(0, 200),
    }));
}
