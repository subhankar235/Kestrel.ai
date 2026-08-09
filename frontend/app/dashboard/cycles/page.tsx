"use client";

import { Activity } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useDashboard } from "@/hooks/use-dashboard";

export default function CyclesPage() {
  const { data, loading, error } = useDashboard();
  if (loading) return <p className="text-sm text-muted-foreground">Loading cycle status...</p>;
  if (error || !data) return <p className="text-sm text-destructive">{error || "Cycle status unavailable"}</p>;

  return (
    <div className="space-y-6 pb-12">
      <section className="surface-card p-6">
        <div className="flex items-center gap-3">
          <Activity className="size-5 text-accent" />
          <h2 className="font-display text-xl font-semibold">Agent cycle scheduler</h2>
          <Badge variant="secondary">{data.cycle?.status || "unknown"}</Badge>
        </div>
        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          <div><p className="font-display text-2xl font-semibold">{data.cycleCount}</p><p className="text-xs text-muted-foreground">Cycles recorded</p></div>
          <div><p className="font-mono text-sm">{data.cycle?.scheduleId || "Unavailable"}</p><p className="text-xs text-muted-foreground">Schedule</p></div>
          <div><p className="font-mono text-sm">{data.cycle?.nextRunTime || "Unavailable"}</p><p className="text-xs text-muted-foreground">Next run</p></div>
        </div>
        <p className="mt-5 text-sm text-muted-foreground">{data.cycle?.note || "No scheduler details available."}</p>
      </section>
    </div>
  );
}
