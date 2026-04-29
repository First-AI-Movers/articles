import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js";
import { z } from "zod";
import {
  archive,
  getArticleBySlug,
  listTopics,
  getTopicBySlug,
  getArticlesByTopic,
} from "./archive.js";
import { searchArticles } from "./search.js";
import { handleAsk } from "./ask.js";

function createServer(env: Record<string, unknown>) {
  const server = new McpServer({
    name: "First AI Movers Archive",
    version: "1.0.0",
  });

  // Tool: search_articles
  server.tool(
    "search_articles",
    "Search the article archive by query string and optional topic filter. " +
      "Returns ranked article titles, URLs, topics, dates, and short excerpts. " +
      "If semantic search is enabled, uses vector similarity; otherwise uses lexical scoring.",
    {
      query: z
        .string()
        .min(1)
        .max(200)
        .describe("Search query (e.g. 'AI governance for European SMEs')"),
      limit: z
        .number()
        .min(1)
        .max(10)
        .optional()
        .default(5)
        .describe("Maximum results to return (1-10, default 5)"),
      topic: z
        .string()
        .optional()
        .describe("Optional topic slug to filter results (e.g. 'ai-strategy')"),
    },
    async ({ query, limit, topic }) => {
      const results = await searchArticles(query, limit, topic, env);
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                query,
                topic: topic || null,
                count: results.length,
                results,
              },
              null,
              2
            ),
          },
        ],
      };
    }
  );

  // Tool: get_article
  server.tool(
    "get_article",
    "Retrieve a specific article by its URL slug. Returns metadata, summary, excerpt, and links.",
    {
      slug: z
        .string()
        .min(1)
        .regex(/^[a-z0-9-]+$/)
        .describe("Article slug (e.g. 'ai-governance-european-smes-2026')"),
    },
    async ({ slug }) => {
      const article = getArticleBySlug(slug);
      if (!article) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ error: "Article not found", slug }, null, 2),
            },
          ],
        };
      }
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                slug: article.slug,
                title: article.title,
                published_date: article.published_date,
                canonical_url: article.canonical_url,
                local_url: article.local_url,
                topics: article.topics,
                summary: article.summary,
                excerpt: article.excerpt,
              },
              null,
              2
            ),
          },
        ],
      };
    }
  );

  // Tool: list_topics
  server.tool(
    "list_topics",
    "List canonical topics in the archive, optionally filtering by minimum article count.",
    {
      min_articles: z
        .number()
        .min(1)
        .optional()
        .default(5)
        .describe("Minimum articles required for a topic to appear"),
    },
    async ({ min_articles }) => {
      const topics = listTopics(min_articles);
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                count: topics.length,
                topics: topics.map((t) => ({
                  slug: t.slug,
                  name: t.name,
                  article_count: t.count,
                  local_url: t.local_url,
                })),
              },
              null,
              2
            ),
          },
        ],
      };
    }
  );

  // Tool: get_topic_intro
  server.tool(
    "get_topic_intro",
    "Get overview information for a specific topic, including article count and representative articles.",
    {
      topic: z
        .string()
        .min(1)
        .describe("Topic slug (e.g. 'ai-strategy')"),
    },
    async ({ topic }) => {
      const topicInfo = getTopicBySlug(topic);
      if (!topicInfo) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                { error: "Topic not found", topic },
                null,
                2
              ),
            },
          ],
        };
      }
      const articles = getArticlesByTopic(topic, 5);
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                slug: topicInfo.slug,
                name: topicInfo.name,
                article_count: topicInfo.count,
                local_url: topicInfo.local_url,
                sample_articles: articles.map((a) => ({
                  slug: a.slug,
                  title: a.title,
                  local_url: a.local_url,
                  published_date: a.published_date,
                })),
              },
              null,
              2
            ),
          },
        ],
      };
    }
  );

  // Tool: get_quick_reads
  server.tool(
    "get_quick_reads",
    "Get short summaries (TL;DRs) of articles for a given topic, ordered by recency.",
    {
      topic: z
        .string()
        .min(1)
        .describe("Topic slug (e.g. 'ai-strategy')"),
      limit: z
        .number()
        .min(1)
        .max(10)
        .optional()
        .default(5)
        .describe("Maximum articles to return (1-10, default 5)"),
    },
    async ({ topic, limit }) => {
      const articles = getArticlesByTopic(topic, limit);
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                topic,
                count: articles.length,
                articles: articles.map((a) => ({
                  slug: a.slug,
                  title: a.title,
                  published_date: a.published_date,
                  local_url: a.local_url,
                  canonical_url: a.canonical_url,
                  summary: a.summary || a.excerpt.slice(0, 200),
                })),
              },
              null,
              2
            ),
          },
        ],
      };
    }
  );

  // Resource: corpus metadata
  server.resource(
    "corpus",
    "firstaimovers://corpus",
    async () => {
      return {
        contents: [
          {
            uri: "firstaimovers://corpus",
            mimeType: "application/json",
            text: JSON.stringify(
              {
                name: "First AI Movers Article Archive",
                total_articles: archive.articles.length,
                total_topics: archive.topics.length,
                date_range: {
                  earliest: archive.articles[archive.articles.length - 1]?.published_date,
                  latest: archive.articles[0]?.published_date,
                },
                site_url: "https://articles.firstaimovers.com",
              },
              null,
              2
            ),
          },
        ],
      };
    }
  );

  // Resource: individual article
  server.resource(
    "article",
    "firstaimovers://article/{slug}",
    async (uri) => {
      const uriStr = typeof uri === "string" ? uri : uri.toString();
      const match = /^firstaimovers:\/\/article\/(.+)$/.exec(uriStr);
      const slug = match ? match[1] : "";
      const article = getArticleBySlug(slug);
      if (!article) {
        return {
          contents: [],
        };
      }
      return {
        contents: [
          {
            uri: `firstaimovers://article/${slug}`,
            mimeType: "application/json",
            text: JSON.stringify(
              {
                slug: article.slug,
                title: article.title,
                published_date: article.published_date,
                canonical_url: article.canonical_url,
                local_url: article.local_url,
                topics: article.topics,
                summary: article.summary,
                excerpt: article.excerpt,
              },
              null,
              2
            ),
          },
        ],
      };
    }
  );

  // Resource: topic
  server.resource(
    "topic",
    "firstaimovers://topic/{slug}",
    async (uri) => {
      const uriStr = typeof uri === "string" ? uri : uri.toString();
      const match = /^firstaimovers:\/\/topic\/(.+)$/.exec(uriStr);
      const slug = match ? match[1] : "";
      const topic = getTopicBySlug(slug);
      if (!topic) {
        return {
          contents: [],
        };
      }
      return {
        contents: [
          {
            uri: `firstaimovers://topic/${slug}`,
            mimeType: "application/json",
            text: JSON.stringify(
              {
                slug: topic.slug,
                name: topic.name,
                article_count: topic.count,
                local_url: topic.local_url,
              },
              null,
              2
            ),
          },
        ],
      };
    }
  );

  return server;
}

export default {
  async fetch(request: Request, env: Record<string, unknown>, _ctx: ExecutionContext) {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return new Response(
        JSON.stringify({
          status: "ok",
          server: "First AI Movers Archive MCP",
          version: "1.0.0",
          articles: archive.articles.length,
          topics: archive.topics.length,
        }),
        {
          headers: { "Content-Type": "application/json" },
        }
      );
    }

    if (url.pathname === "/") {
      return new Response(
        "First AI Movers Archive MCP Server. Connect at /mcp\n",
        { headers: { "Content-Type": "text/plain" } }
      );
    }

    if (url.pathname === "/api/ask") {
      return handleAsk(request, env);
    }

    if (url.pathname === "/mcp") {
      const server = createServer(env);
      const transport = new WebStandardStreamableHTTPServerTransport({
        sessionIdGenerator: undefined,
      });
      await server.connect(transport);
      return transport.handleRequest(request);
    }

    return new Response("Not found", { status: 404 });
  },
};
