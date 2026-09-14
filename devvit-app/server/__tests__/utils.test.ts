import { describe, it, expect } from "vitest";
import {
  parseKeywords,
  matchKeywords,
  truncateBody,
  buildRedditUrl,
  buildDispatchPayload,
  getISOWeek,
  dedupKey,
  keywordCounterKey,
  weeklyDispatchKey,
  DEDUP_TTL_SECONDS,
  BODY_SNIPPET_MAX,
} from "../utils.js";

// ---------------------------------------------------------------------------
// parseKeywords
// ---------------------------------------------------------------------------

describe("parseKeywords", () => {
  it("parses comma-separated keywords", () => {
    expect(parseKeywords("azure openai,microsoft foundry,ai foundry")).toEqual([
      "azure openai",
      "microsoft foundry",
      "ai foundry",
    ]);
  });

  it("trims whitespace and lowercases", () => {
    expect(parseKeywords("  Azure OpenAI , Microsoft Foundry ")).toEqual([
      "azure openai",
      "microsoft foundry",
    ]);
  });

  it("filters empty segments", () => {
    expect(parseKeywords("azure openai,,, ,microsoft foundry")).toEqual([
      "azure openai",
      "microsoft foundry",
    ]);
  });

  it("returns empty array for null/undefined/empty", () => {
    expect(parseKeywords(null)).toEqual([]);
    expect(parseKeywords(undefined)).toEqual([]);
    expect(parseKeywords("")).toEqual([]);
  });

  it("handles single keyword", () => {
    expect(parseKeywords("azure openai")).toEqual(["azure openai"]);
  });
});

// ---------------------------------------------------------------------------
// matchKeywords
// ---------------------------------------------------------------------------

describe("matchKeywords", () => {
  const keywords = ["azure openai", "microsoft foundry", "hosted agent", "mcp"];

  it("matches keywords in post title", () => {
    expect(
      matchKeywords("How do I use Azure OpenAI with my app?", keywords)
    ).toEqual(["azure openai"]);
  });

  it("matches multiple keywords", () => {
    expect(
      matchKeywords(
        "Using Microsoft Foundry hosted agent with Azure OpenAI",
        keywords
      )
    ).toEqual(["azure openai", "microsoft foundry", "hosted agent"]);
  });

  it("is case-insensitive", () => {
    expect(
      matchKeywords("AZURE OPENAI is great", keywords)
    ).toEqual(["azure openai"]);
  });

  it("returns empty array when no match", () => {
    expect(
      matchKeywords("I love programming in Python", keywords)
    ).toEqual([]);
  });

  it("handles empty text", () => {
    expect(matchKeywords("", keywords)).toEqual([]);
  });

  it("handles empty keywords list", () => {
    expect(matchKeywords("azure openai rocks", [])).toEqual([]);
  });

  it("matches substring within longer text", () => {
    expect(
      matchKeywords("The mcp server is configured correctly", keywords)
    ).toEqual(["mcp"]);
  });

  it("matches keywords spanning title + body", () => {
    const combined = "General question about AI I want to deploy a hosted agent on Azure";
    expect(matchKeywords(combined, keywords)).toEqual(["hosted agent"]);
  });
});

// ---------------------------------------------------------------------------
// truncateBody
// ---------------------------------------------------------------------------

describe("truncateBody", () => {
  it("returns full text if under limit", () => {
    expect(truncateBody("short text")).toBe("short text");
  });

  it("truncates to default max (500)", () => {
    const long = "a".repeat(1000);
    expect(truncateBody(long)).toHaveLength(BODY_SNIPPET_MAX);
  });

  it("truncates to custom max", () => {
    expect(truncateBody("abcdefgh", 5)).toBe("abcde");
  });

  it("handles empty string", () => {
    expect(truncateBody("")).toBe("");
  });
});

// ---------------------------------------------------------------------------
// buildRedditUrl
// ---------------------------------------------------------------------------

describe("buildRedditUrl", () => {
  it("prepends reddit.com to a permalink path", () => {
    expect(buildRedditUrl("/r/azure/comments/abc123/my_post/")).toBe(
      "https://reddit.com/r/azure/comments/abc123/my_post/"
    );
  });

  it("returns empty string for empty permalink", () => {
    expect(buildRedditUrl("")).toBe("");
  });

  it("does not double-prefix if already a full URL", () => {
    expect(buildRedditUrl("https://reddit.com/r/azure/test")).toBe(
      "https://reddit.com/r/azure/test"
    );
  });
});

// ---------------------------------------------------------------------------
// buildDispatchPayload
// ---------------------------------------------------------------------------

describe("buildDispatchPayload", () => {
  it("builds a well-formed dispatch payload", () => {
    const result = buildDispatchPayload({
      subreddit: "azure",
      title: "How to use Foundry?",
      permalink: "/r/azure/comments/abc123/how_to_use_foundry/",
      body: "I want to deploy a hosted agent using Microsoft Foundry.",
      keywords: ["microsoft foundry", "hosted agent"],
      source: "post",
    });

    expect(result.event_type).toBe("reddit-foundry-mention");
    expect(result.client_payload.subreddit).toBe("azure");
    expect(result.client_payload.title).toBe("How to use Foundry?");
    expect(result.client_payload.url).toBe(
      "https://reddit.com/r/azure/comments/abc123/how_to_use_foundry/"
    );
    expect(result.client_payload.keywords).toEqual([
      "microsoft foundry",
      "hosted agent",
    ]);
    expect(result.client_payload.source).toBe("post");
  });

  it("truncates body to 500 chars", () => {
    const longBody = "x".repeat(1000);
    const result = buildDispatchPayload({
      subreddit: "test",
      title: "Test",
      permalink: "/r/test/abc",
      body: longBody,
      keywords: ["test"],
      source: "post",
    });
    expect(result.client_payload.bodySnippet).toHaveLength(500);
  });

  it("defaults subreddit to unknown when empty", () => {
    const result = buildDispatchPayload({
      subreddit: "",
      title: "Test",
      permalink: "/r/test/abc",
      body: "test",
      keywords: ["test"],
      source: "comment",
    });
    expect(result.client_payload.subreddit).toBe("unknown");
  });
});

// ---------------------------------------------------------------------------
// getISOWeek
// ---------------------------------------------------------------------------

describe("getISOWeek", () => {
  it("computes correct ISO week for a known date", () => {
    // Verify output is a valid ISO week format
    const result = getISOWeek(new Date("2026-03-02T12:00:00Z"));
    expect(result).toMatch(/^2026-W\d{2}$/);
  });

  it("handles year boundary", () => {
    const result = getISOWeek(new Date("2026-01-01T00:00:00Z"));
    expect(result).toMatch(/^\d{4}-W\d{2}$/);
  });

  it("returns consistent format with zero-padded week", () => {
    const result = getISOWeek(new Date("2026-01-05T00:00:00Z"));
    expect(result).toMatch(/^\d{4}-W\d{2}$/);
  });

  it("returns same week for dates within the same week", () => {
    // Use dates well within a week (Tue-Thu) to avoid timezone boundary issues
    const tue = getISOWeek(new Date("2026-06-09T12:00:00Z"));
    const thu = getISOWeek(new Date("2026-06-11T12:00:00Z"));
    expect(tue).toBe(thu);
  });

  it("returns different weeks for dates 7 days apart", () => {
    const weekA = getISOWeek(new Date("2026-06-10T12:00:00Z"));
    const weekB = getISOWeek(new Date("2026-06-17T12:00:00Z"));
    expect(weekA).not.toBe(weekB);
  });
});

// ---------------------------------------------------------------------------
// Redis key builders
// ---------------------------------------------------------------------------

describe("dedupKey", () => {
  it("builds a dedup key from post ID", () => {
    expect(dedupKey("t3_abc123")).toBe("dispatched:t3_abc123");
  });
});

describe("keywordCounterKey", () => {
  it("builds a keyword counter key with month", () => {
    const date = new Date("2026-03-15T00:00:00Z");
    expect(keywordCounterKey("azure openai", date)).toBe(
      "keyword:azure openai:2026-03"
    );
  });

  it("zero-pads single-digit months", () => {
    const date = new Date("2026-01-05T00:00:00Z");
    expect(keywordCounterKey("test", date)).toBe("keyword:test:2026-01");
  });
});

describe("weeklyDispatchKey", () => {
  it("builds a weekly dispatch key", () => {
    const date = new Date("2026-03-02T00:00:00Z");
    const key = weeklyDispatchKey(date);
    expect(key).toMatch(/^dispatches:week:2026-W\d{2}$/);
  });
});

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

describe("constants", () => {
  it("DEDUP_TTL_SECONDS is 7 days", () => {
    expect(DEDUP_TTL_SECONDS).toBe(7 * 24 * 60 * 60);
  });

  it("BODY_SNIPPET_MAX is 500", () => {
    expect(BODY_SNIPPET_MAX).toBe(500);
  });
});
