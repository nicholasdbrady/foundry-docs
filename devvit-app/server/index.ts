/**
 * Foundry Community Monitor — Devvit Web Server
 *
 * Monitors subreddits for Microsoft Foundry / Azure AI keyword mentions,
 * deduplicates via Redis, and dispatches repository_dispatch events to
 * the foundry-docs GitHub repo for documentation impact analysis.
 *
 * Reddit Pro provides the discovery/analytics layer (keyword tracking,
 * trend analysis, community discovery). This Devvit app provides the
 * automation layer (event-driven triggers, GitHub dispatch, dedup).
 */

import { Hono } from "hono";
import type {
  OnPostSubmitRequest,
  OnCommentCreateRequest,
  TriggerResponse,
  TaskRequest,
  TaskResponse,
} from "@devvit/web/shared";
import { settings, redis } from "@devvit/web/server";

import {
  DEDUP_TTL_SECONDS,
  BODY_SNIPPET_MAX,
  parseKeywords,
  matchKeywords,
  truncateBody,
  buildRedditUrl,
  buildDispatchPayload,
  getISOWeek,
  dedupKey,
  keywordCounterKey,
  weeklyDispatchKey,
} from "./utils.js";

const app = new Hono();

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

async function getKeywords(): Promise<string[]> {
  const raw = (await settings.get("keywords")) as string;
  return parseKeywords(raw);
}

async function isEnabled(): Promise<boolean> {
  const val = await settings.get("enabled");
  return val !== false;
}

// ---------------------------------------------------------------------------
// Keyword matching (re-exported from utils for inline use)
// ---------------------------------------------------------------------------

// matchKeywords imported from utils.ts

// ---------------------------------------------------------------------------
// Redis deduplication
// ---------------------------------------------------------------------------

async function isDuplicate(postId: string): Promise<boolean> {
  const existing = await redis.get(dedupKey(postId));
  return existing !== null && existing !== undefined;
}

async function markDispatched(postId: string): Promise<void> {
  const key = dedupKey(postId);
  await redis.set(key, new Date().toISOString());
  await redis.expire(key, DEDUP_TTL_SECONDS);
}

async function incrementKeywordCounters(keywords: string[]): Promise<void> {
  const now = new Date();
  for (const kw of keywords) {
    const key = keywordCounterKey(kw, now);
    await redis.incrBy(key, 1);
    await redis.expire(key, 90 * 24 * 60 * 60);
  }
}

async function incrementDispatchCounter(): Promise<void> {
  const now = new Date();
  const key = weeklyDispatchKey(now);
  await redis.incrBy(key, 1);
  await redis.expire(key, 14 * 24 * 60 * 60);
}

// ---------------------------------------------------------------------------
// GitHub dispatch
// ---------------------------------------------------------------------------

async function dispatchToGitHub(payload: {
  subreddit: string;
  title: string;
  url: string;
  bodySnippet: string;
  keywords: string[];
  source: "post" | "comment";
}): Promise<boolean> {
  const token = await settings.get("githubToken");
  const repo = (await settings.get("githubRepo")) as string;

  if (!token || !repo) {
    console.error("GitHub token or repo not configured");
    return false;
  }

  try {
    const response = await fetch(
      `https://api.github.com/repos/${repo}/dispatches`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/vnd.github+json",
          "Content-Type": "application/json",
          "X-GitHub-Api-Version": "2022-11-28",
        },
        body: JSON.stringify({
          event_type: "reddit-foundry-mention",
          client_payload: payload,
        }),
      }
    );

    if (response.status === 204) {
      console.log(`Dispatched reddit-foundry-mention for: ${payload.title}`);
      return true;
    } else {
      console.error(
        `GitHub dispatch failed: ${response.status} ${response.statusText}`
      );
      return false;
    }
  } catch (error) {
    console.error("GitHub dispatch error:", error);
    return false;
  }
}

// ---------------------------------------------------------------------------
// Trigger handlers
// ---------------------------------------------------------------------------

app.post("/internal/on-post-submit", async (c) => {
  if (!(await isEnabled())) {
    return c.json<TriggerResponse>({ status: "ok" });
  }

  const input = await c.req.json<OnPostSubmitRequest>();
  const post = input.post;
  if (!post) {
    return c.json<TriggerResponse>({ status: "ok" });
  }

  const postId = post.id || "";
  if (!postId) {
    return c.json<TriggerResponse>({ status: "ok" });
  }

  // Check for duplicate
  if (await isDuplicate(postId)) {
    console.log(`Skipping duplicate post: ${postId}`);
    return c.json<TriggerResponse>({ status: "ok" });
  }

  // Keyword matching
  const keywords = await getKeywords();
  const text = `${post.title || ""} ${post.body || ""}`;
  const matched = matchKeywords(text, keywords);

  if (matched.length === 0) {
    return c.json<TriggerResponse>({ status: "ok" });
  }

  // Dispatch to GitHub
  const bodySnippet = truncateBody(post.body || "");
  const dispatched = await dispatchToGitHub({
    subreddit: post.subredditName || "unknown",
    title: post.title || "",
    url: buildRedditUrl(post.permalink || ""),
    bodySnippet,
    keywords: matched,
    source: "post",
  });

  if (dispatched) {
    await markDispatched(postId);
    await incrementKeywordCounters(matched);
    await incrementDispatchCounter();
  }

  return c.json<TriggerResponse>({ status: "ok" });
});

app.post("/internal/on-comment-create", async (c) => {
  if (!(await isEnabled())) {
    return c.json<TriggerResponse>({ status: "ok" });
  }

  const input = await c.req.json<OnCommentCreateRequest>();
  const comment = input.comment;
  if (!comment) {
    return c.json<TriggerResponse>({ status: "ok" });
  }

  const commentId = comment.id || "";
  if (!commentId) {
    return c.json<TriggerResponse>({ status: "ok" });
  }

  if (await isDuplicate(commentId)) {
    return c.json<TriggerResponse>({ status: "ok" });
  }

  const keywords = await getKeywords();
  const text = comment.body || "";
  const matched = matchKeywords(text, keywords);

  if (matched.length === 0) {
    return c.json<TriggerResponse>({ status: "ok" });
  }

  const bodySnippet = truncateBody(text);
  const dispatched = await dispatchToGitHub({
    subreddit: comment.subredditName || "unknown",
    title: `Comment on ${comment.parentId || "post"}`,
    url: buildRedditUrl(comment.permalink || ""),
    bodySnippet,
    keywords: matched,
    source: "comment",
  });

  if (dispatched) {
    await markDispatched(commentId);
    await incrementKeywordCounters(matched);
    await incrementDispatchCounter();
  }

  return c.json<TriggerResponse>({ status: "ok" });
});

// ---------------------------------------------------------------------------
// Scheduler: Weekly digest
// ---------------------------------------------------------------------------

app.post("/internal/scheduler/weekly-digest", async (c) => {
  const _input = await c.req.json<TaskRequest>();

  const now = new Date();
  const monthKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
  const weekKey = weeklyDispatchKey(now);

  // Get dispatch count for this week
  const weekDispatches = (await redis.get(weekKey)) || "0";

  // Get keyword counts for this month
  const keywords = await getKeywords();
  const keywordCounts: Record<string, number> = {};
  for (const kw of keywords) {
    const count = await redis.get(keywordCounterKey(kw, now));
    if (count) {
      keywordCounts[kw] = parseInt(count, 10);
    }
  }

  console.log("=== Weekly Foundry Community Digest ===");
  console.log(`Week: ${getISOWeek(now)}`);
  console.log(`Dispatches this week: ${weekDispatches}`);
  console.log(`Keyword counts (${monthKey}):`);
  for (const [kw, count] of Object.entries(keywordCounts)) {
    console.log(`  ${kw}: ${count}`);
  }
  console.log("=======================================");

  return c.json<TaskResponse>({ status: "ok" });
});

// ---------------------------------------------------------------------------
// Health check
// ---------------------------------------------------------------------------

app.get("/api/health", (c) => {
  return c.json({ status: "ok", app: "foundry-community-monitor" });
});

export default app;
