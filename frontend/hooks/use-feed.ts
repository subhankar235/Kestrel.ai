"use client";

import { useState, useEffect, useCallback } from "react";
import { getFeed, ApiError } from "@/lib/api-client";
import type { Post } from "@/types/feed";

const POLL_INTERVAL = parseInt(
  process.env.NEXT_PUBLIC_FEED_POLL_INTERVAL_MS || "15000",
  10,
);

interface UseFeedResult {
  posts: Post[];
  status: "idle" | "loading" | "success" | "error";
  error?: string;
  lastCheckedAt: Date | null;
}

export function useFeed(
  agentId: string | null,
  initialPosts?: Post[],
  allAgents = false,
): UseFeedResult {
  const [posts, setPosts] = useState<Post[]>(initialPosts || []);
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">(
    initialPosts ? "success" : "idle",
  );
  const [error, setError] = useState<string | undefined>();
  const [lastCheckedAt, setLastCheckedAt] = useState<Date | null>(null);

  const fetchFeed = useCallback(async () => {
    if (!agentId && !allAgents) return;

    setStatus((prev) => (prev === "idle" ? "loading" : prev));
    setError(undefined);

    try {
      const response = await getFeed(allAgents ? undefined : agentId ?? undefined);
      setPosts((prev) => {
        const existingIds = new Set(prev.map((p) => p.id));
        const newPosts = response.posts.filter((p) => !existingIds.has(p.id));
        return [...newPosts, ...prev];
      });
      setStatus("success");
      setLastCheckedAt(new Date());
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to fetch feed");
      }
      setStatus("error");
    }
  }, [agentId, allAgents]);

  useEffect(() => {
    if (!agentId && !allAgents) return;

    queueMicrotask(fetchFeed);

    const interval = setInterval(fetchFeed, POLL_INTERVAL);

    return () => clearInterval(interval);
  }, [agentId, allAgents, fetchFeed]);

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible" && (agentId || allAgents)) {
        fetchFeed();
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () =>
      document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, [agentId, allAgents, fetchFeed]);

  return { posts, status, error, lastCheckedAt };
}
