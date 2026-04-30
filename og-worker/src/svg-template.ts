import type { OGParams } from "./types.js";
import { sanitize } from "./types.js";

const BG = "#121212";
const TEXT_PRIMARY = "#e0e0e0";
const TEXT_MUTED = "#aaa";
const ACCENT = "#e67e45";
const CHIP_TEXT = "#121212";

function computeTitleStyle(title: string): { fontSize: number; maxLines: number } {
  const len = title.length;
  if (len <= 60) return { fontSize: 64, maxLines: 2 };
  if (len <= 100) return { fontSize: 52, maxLines: 3 };
  return { fontSize: 40, maxLines: 4 };
}

function wrapTitle(title: string, fontSize: number, maxLines: number): string[] {
  const maxWidth = 1040;
  const avgCharWidth = fontSize * 0.52;
  const charsPerLine = Math.floor(maxWidth / avgCharWidth);

  const words = title.split(/\s+/);
  const lines: string[] = [];
  let current = "";

  for (const word of words) {
    const test = current ? `${current} ${word}` : word;
    if (test.length <= charsPerLine) {
      current = test;
    } else {
      if (current) lines.push(current);
      current = word;
    }
  }
  if (current) lines.push(current);

  if (lines.length > maxLines) {
    const truncated = lines.slice(0, maxLines);
    const last = truncated[maxLines - 1];
    if (last.length > 3) {
      truncated[maxLines - 1] = last.slice(0, last.length - 3).trimEnd() + "…";
    }
    return truncated;
  }

  return lines;
}

export function buildSVG(params: OGParams): string {
  const { title, topic, date, author } = params;
  const { fontSize, maxLines } = computeTitleStyle(title);
  const lines = wrapTitle(title, fontSize, maxLines);
  const safeLines = lines.map((l) => sanitize(l));

  const metaParts: string[] = [];
  if (date) metaParts.push(sanitize(date));
  if (author) metaParts.push(sanitize(author));
  const metaLine = metaParts.join(" · ");

  const hasTopic = topic && topic.trim().length > 0;

  let titleTspans = "";
  const lineHeight = fontSize * 1.15;
  for (let i = 0; i < safeLines.length; i++) {
    titleTspans += `<tspan x="80" dy="${i === 0 ? 0 : lineHeight}">${safeLines[i]}</tspan>`;
  }

  const chipSVG = hasTopic
    ? `<rect x="80" y="80" width="${Math.min(300, topic.length * 16 + 48)}" height="44" rx="4" fill="${ACCENT}"/><text x="104" y="110" font-family="system-ui, sans-serif" font-size="24" font-weight="600" fill="${CHIP_TEXT}">${sanitize(topic)}</text>`
    : "";

  const metaSVG = metaLine
    ? `<text x="80" y="570" font-family="system-ui, sans-serif" font-size="24" font-weight="400" fill="${TEXT_MUTED}">${metaLine}</text>`
    : "";

  return `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <rect width="1200" height="630" fill="${BG}"/>
  ${chipSVG}
  <text font-family="system-ui, sans-serif" font-size="${fontSize}" font-weight="600" fill="${TEXT_PRIMARY}">${titleTspans}</text>
  ${metaSVG}
  <g transform="translate(1120, 570)" text-anchor="end">
    <circle cx="-12" cy="-12" r="6" fill="${ACCENT}"/>
    <text x="0" y="0" font-family="system-ui, sans-serif" font-size="24" font-weight="600" fill="${TEXT_PRIMARY}">First AI Movers</text>
  </g>
</svg>`;
}
