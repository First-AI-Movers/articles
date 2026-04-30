export interface OGParams {
  slug: string;
  title: string;
  topic?: string;
  date?: string;
  author?: string;
  type: "article" | "topic" | "default";
}

export const DEFAULT_TITLE = "First AI Movers — Article Archive";
export const MAX_TITLE_LENGTH = 200;
export const MAX_TOPIC_LENGTH = 60;
export const MAX_DATE_LENGTH = 20;
export const MAX_AUTHOR_LENGTH = 60;

export function sanitize(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export function validateParams(searchParams: URLSearchParams, slug: string, type: OGParams["type"]): OGParams {
  const rawTitle = searchParams.get("title") ?? "";
  const rawTopic = searchParams.get("topic") ?? undefined;
  const rawDate = searchParams.get("date") ?? undefined;
  const rawAuthor = searchParams.get("author") ?? undefined;

  const title = rawTitle.trim().slice(0, MAX_TITLE_LENGTH) || DEFAULT_TITLE;
  const topic = rawTopic?.trim().slice(0, MAX_TOPIC_LENGTH);
  const date = rawDate?.trim().slice(0, MAX_DATE_LENGTH);
  const author = rawAuthor?.trim().slice(0, MAX_AUTHOR_LENGTH);

  return { slug, title, topic, date, author, type };
}
