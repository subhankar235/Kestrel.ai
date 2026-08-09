import type { PersonaIn, InitRequest, InitResponse, Post, FeedResponse, AgentInitOptions } from "@/types/feed";
import type { DashboardResponse } from "@/types/dashboard";
import type { AgentSummary } from "@/types/dashboard";

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
  options: AgentInitOptions,
): Promise<InitResponse> {
  const response = await fetch(`${API_BASE_URL}/api/agent/init`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ persona, ...options } satisfies InitRequest & AgentInitOptions),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new ApiError(response.status, error.detail || "Failed to initialize agent");
  }

  return response.json();
}

export async function getFeed(agentId?: string): Promise<FeedResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/agent/feed${agentId ? `?agentId=${encodeURIComponent(agentId)}` : ""}`,
    { cache: "no-store" },
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new ApiError(response.status, error.detail || "Failed to fetch feed");
  }

  return response.json();
}

export async function getAgents(): Promise<{ agents: AgentSummary[] }> {
  const response = await fetch(`${API_BASE_URL}/api/agent/agents`, { cache: "no-store" });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new ApiError(response.status, error.detail || "Failed to fetch personas");
  }
  return response.json();
}

export async function getDashboard(agentId: string): Promise<DashboardResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/agent/dashboard?agentId=${encodeURIComponent(agentId)}`,
    { cache: "no-store" },
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new ApiError(error.status ?? response.status, error.detail || "Failed to fetch dashboard");
  }

  return response.json();
}

export type { PersonaIn, InitRequest, InitResponse, Post, FeedResponse };
