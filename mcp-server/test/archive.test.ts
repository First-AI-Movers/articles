import { describe, it, expect } from "vitest";
import {
  getArticleBySlug,
  listTopics,
  getTopicBySlug,
  getArticlesByTopic,
  archive,
} from "../src/archive.js";

describe("archive", () => {
  describe("getArticleBySlug", () => {
    it("returns an article for a known slug", () => {
      const article = archive.articles[0];
      const result = getArticleBySlug(article.slug);
      expect(result).toBeDefined();
      expect(result?.slug).toBe(article.slug);
      expect(result?.title).toBe(article.title);
    });

    it("returns undefined for unknown slug", () => {
      const result = getArticleBySlug("nonexistent-article-slug-12345");
      expect(result).toBeUndefined();
    });
  });

  describe("listTopics", () => {
    it("returns topics with at least min_articles", () => {
      const topics = listTopics(5);
      expect(topics.length).toBeGreaterThan(0);
      for (const t of topics) {
        expect(t.count).toBeGreaterThanOrEqual(5);
        expect(t.slug).toBeDefined();
        expect(t.name).toBeDefined();
        expect(t.local_url).toBeDefined();
      }
    });

    it("filters by higher min_articles", () => {
      const all = listTopics(1);
      const filtered = listTopics(1000);
      expect(filtered.length).toBeLessThanOrEqual(all.length);
    });
  });

  describe("getTopicBySlug", () => {
    it("returns topic for known slug", () => {
      const topic = archive.topics[0];
      const result = getTopicBySlug(topic.slug);
      expect(result).toBeDefined();
      expect(result?.slug).toBe(topic.slug);
    });

    it("returns undefined for unknown slug", () => {
      const result = getTopicBySlug("nonexistent-topic-12345");
      expect(result).toBeUndefined();
    });
  });

  describe("getArticlesByTopic", () => {
    it("returns articles for a known topic", () => {
      const topic = archive.topics[0];
      const articles = getArticlesByTopic(topic.slug, 5);
      expect(articles.length).toBeGreaterThan(0);
      expect(articles.length).toBeLessThanOrEqual(5);
      for (const a of articles) {
        expect(
          a.topics.some(
            (t) =>
              t.toLowerCase().replace(/\s+/g, "-") === topic.slug ||
              t.toLowerCase() === topic.name.toLowerCase()
          )
        ).toBe(true);
      }
    });

    it("returns empty array for unknown topic", () => {
      const articles = getArticlesByTopic("nonexistent-topic-12345", 5);
      expect(articles).toEqual([]);
    });

    it("respects limit", () => {
      const topic = archive.topics[0];
      const articles3 = getArticlesByTopic(topic.slug, 3);
      expect(articles3.length).toBeLessThanOrEqual(3);
    });
  });
});
