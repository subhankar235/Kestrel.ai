import type { PersonaIn, InitRequest, InitResponse, Post, FeedResponse } from "@/types/feed";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function initAgent(
  persona: PersonaIn,
  token: string,
): Promise<InitResponse> {
  const response = await fetch(`${API_BASE_URL}/api/agent/init`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ persona } satisfies InitRequest),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new ApiError(response.status, error.detail || "Failed to initialize agent");
  }

  return response.json();
}

export async function getFeed(agentId: string): Promise<FeedResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/agent/feed?agentId=${encodeURIComponent(agentId)}`,
    { cache: "no-store" },
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new ApiError(response.status, error.detail || "Failed to fetch feed");
  }

  return response.json();
}

export type { PersonaIn, InitRequest, InitResponse, Post, FeedResponse };
