"use client";

import { useEffect, useState } from "react";
import { ApiError, getDashboard } from "@/lib/api-client";
import type { DashboardResponse } from "@/types/dashboard";

export function useDashboard() {
  const [agentId] = useState<string | null>(() =>
    typeof window === "undefined" ? null : window.localStorage.getItem("kestrel.agentId"),
  );
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();

  useEffect(() => {
    if (!agentId) {
      queueMicrotask(() => {
        setLoading(false);
        setError("Initialize an agent first");
      });
      return;
    }

    getDashboard(agentId)
      .then(setData)
      .catch((reason: unknown) => {
        setError(reason instanceof ApiError ? reason.message : "Failed to fetch dashboard");
      })
      .finally(() => setLoading(false));
  }, [agentId]);

  return { data, loading, error };
}
