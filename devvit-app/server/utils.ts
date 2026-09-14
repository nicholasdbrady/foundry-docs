/**
 * Pure utility functions for the Foundry Community Monitor.
 *
 * These functions have no Devvit/Redis/network dependencies and are
 * directly unit-testable.
 */

export const DEDUP_TTL_SECONDS = 7 * 24 * 60 * 60; // 7 days
export const BODY_SNIPPET_MAX = 500;

/**
 * Parse a comma-separated keywords string into a normalized array.
 */
export function parseKeywords(raw: string | null | undefined): string[] {
  if (!raw) return [];
  return raw
    .split(",")
    .map((k) => k.trim().toLowerCase())
    .filter(Boolean);
}

/**
 * Match text against a list of keywords (case-insensitive substring match).
 * Returns the list of keywords found in the text.
 */
export function matchKeywords(text: string, keywords: string[]): string[] {
  const lower = text.toLowerCase();
  return keywords.filter((kw) => lower.includes(kw));
}

/**
 * Truncate body text to a maximum snippet length.
 */
export function truncateBody(body: string, maxLen: number = BODY_SNIPPET_MAX): string {
  return body.slice(0, maxLen);
}

/**
 * Build a Reddit permalink URL from a permalink path.
 */
export function buildRedditUrl(permalink: string): string {
  if (!permalink) return "";
  if (permalink.startsWith("https://")) return permalink;
  return `https://reddit.com${permalink}`;
}

/**
 * Build the GitHub repository_dispatch payload.
 */
export function buildDispatchPayload(opts: {
  subreddit: string;
  title: string;
  permalink: string;
  body: string;
  keywords: string[];
  source: "post" | "comment";
}): {
  event_type: string;
  client_payload: {
    subreddit: string;
    title: string;
    url: string;
    bodySnippet: string;
    keywords: string[];
    source: "post" | "comment";
  };
} {
  return {
    event_type: "reddit-foundry-mention",
    client_payload: {
      subreddit: opts.subreddit || "unknown",
      title: opts.title || "",
      url: buildRedditUrl(opts.permalink),
      bodySnippet: truncateBody(opts.body),
      keywords: opts.keywords,
      source: opts.source,
    },
  };
}

/**
 * Compute the ISO week string for a given date (e.g., "2026-W09").
 */
export function getISOWeek(date: Date): string {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() + 3 - ((d.getDay() + 6) % 7));
  const yearStart = new Date(d.getFullYear(), 0, 4);
  const weekNo = Math.ceil(
    ((d.getTime() - yearStart.getTime()) / 86400000 + 1) / 7
  );
  return `${d.getFullYear()}-W${String(weekNo).padStart(2, "0")}`;
}

/**
 * Build a Redis key for deduplication.
 */
export function dedupKey(id: string): string {
  return `dispatched:${id}`;
}

/**
 * Build a Redis key for keyword monthly counter.
 */
export function keywordCounterKey(keyword: string, date: Date): string {
  const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
  return `keyword:${keyword}:${monthKey}`;
}

/**
 * Build a Redis key for weekly dispatch counter.
 */
export function weeklyDispatchKey(date: Date): string {
  return `dispatches:week:${getISOWeek(date)}`;
}
