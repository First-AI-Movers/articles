import archiveData from "./generated/archive-data.json" with { type: "json" };

export interface ArticleRecord {
  slug: string;
  title: string;
  published_date: string;
  canonical_url: string;
  local_url: string;
  topics: string[];
  summary: string;
  excerpt: string;
}

export interface ArchiveData {
  articles: ArticleRecord[];
  topics: Array<{ slug: string; name: string; count: number; local_url: string }>;
}

export interface EmbeddingMap {
  [slug: string]: number[];
}

// Build topic index from article records
function buildTopics(articles: ArticleRecord[]) {
  const topicMap = new Map<string, { name: string; count: number }>();
  for (const art of articles) {
    for (const topic of art.topics) {
      const existing = topicMap.get(topic);
      if (existing) {
        existing.count++;
      } else {
        topicMap.set(topic, { name: topic, count: 1 });
      }
    }
  }
  return Array.from(topicMap.entries())
    .map(([slug, info]) => ({
      slug: slug.toLowerCase().replace(/\s+/g, "-"),
      name: info.name,
      count: info.count,
      local_url: `/topics/${slug.toLowerCase().replace(/\s+/g, "-")}/`,
    }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
}

export const archive: ArchiveData = {
  articles: archiveData as ArticleRecord[],
  topics: buildTopics(archiveData as ArticleRecord[]),
};

// Lazy-loaded embeddings (loaded from bundled JSON or fetched at runtime)
let embeddingsCache: EmbeddingMap | null = null;
let embeddingsLoading: Promise<EmbeddingMap> | null = null;

export async function getEmbeddings(
  env: Record<string, unknown>
): Promise<EmbeddingMap> {
  if (embeddingsCache) return embeddingsCache;
  if (embeddingsLoading) return embeddingsLoading;

  embeddingsLoading = loadEmbeddings(env);
  try {
    embeddingsCache = await embeddingsLoading;
    return embeddingsCache;
  } catch (e) {
    embeddingsLoading = null;
    throw e;
  }
}

async function loadEmbeddings(
  env: Record<string, unknown>
): Promise<EmbeddingMap> {
  // Try bundled embeddings first (if they exist in the build)
  try {
    const modulePath = "./generated/embeddings.json";
    const bundled = await import(modulePath);
    if (bundled.default && Object.keys(bundled.default).length > 0) {
      return bundled.default as EmbeddingMap;
    }
  } catch {
    // Bundled embeddings not available
  }

  // Fallback: fetch from raw GitHub
  const githubUrl =
    (env.GITHUB_RAW_URL as string) ||
    "https://raw.githubusercontent.com/First-AI-Movers/articles/main";
  const url = `${githubUrl}/mcp-server/src/generated/embeddings.json`;

  const response = await fetch(url, { cf: { cacheTtl: 86400 } });
  if (!response.ok) {
    throw new Error(`Failed to fetch embeddings: ${response.status}`);
  }
  return (await response.json()) as EmbeddingMap;
}

export function getArticleBySlug(slug: string): ArticleRecord | undefined {
  return archive.articles.find((a) => a.slug === slug);
}

export function listTopics(minArticles: number) {
  return archive.topics.filter((t) => t.count >= minArticles);
}

export function getTopicBySlug(slug: string) {
  return archive.topics.find((t) => t.slug === slug);
}

export function getArticlesByTopic(
  topicSlug: string,
  limit: number
): ArticleRecord[] {
  const topicName = topicSlug.replace(/-/g, " ");
  return archive.articles
    .filter((a) =>
      a.topics.some(
        (t) =>
          t.toLowerCase().replace(/\s+/g, "-") === topicSlug ||
          t.toLowerCase() === topicName.toLowerCase()
      )
    )
    .slice(0, limit);
}
