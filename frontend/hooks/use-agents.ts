"use client";

import { useEffect, useState } from "react";
import { ApiError, getAgents } from "@/lib/api-client";
import type { AgentSummary } from "@/types/dashboard";

export function useAgents() {
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();

  useEffect(() => {
    getAgents()
      .then((response) => setAgents(response.agents))
      .catch((reason: unknown) => setError(reason instanceof ApiError ? reason.message : "Failed to fetch personas"))
      .finally(() => setLoading(false));
  }, []);

  return { agents, loading, error };
}
