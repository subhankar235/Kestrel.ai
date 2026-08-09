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
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <div className="rounded-xl border border-[var(--surface-border)] p-3"><p className="font-mono text-sm">{data.publishIntervalMinutes} minutes</p><p className="text-xs text-muted-foreground">Run interval</p></div>
          <div className="rounded-xl border border-[var(--surface-border)] p-3"><p className="font-mono text-sm">{data.observationPeriodHours} hours</p><p className="text-xs text-muted-foreground">Observation window</p></div>
          <div className="rounded-xl border border-[var(--surface-border)] p-3"><p className="font-mono text-sm">{data.startMode}</p><p className="text-xs text-muted-foreground">Start mode</p></div>
        </div>
        <p className="mt-5 text-sm text-muted-foreground">{data.cycle?.note || "No scheduler details available."}</p>
      </section>
      <section className="surface-card p-5">
        <h2 className="mb-4 font-display text-base font-semibold">Cycle history</h2>
        {data.cycles.length === 0 ? <div className="rounded-xl border border-dashed border-[var(--surface-border)] p-5"><p className="text-sm text-muted-foreground">No completed cycle history has been recorded yet.</p><p className="mt-2 text-xs text-muted-foreground">The scheduler is {data.cycle?.status || "active"}. The first detailed record appears when the current cycle finishes.</p></div> : <div className="space-y-3">{data.cycles.map((run) => <article key={run.id} className="rounded-xl border border-[var(--surface-border)] p-4"><div className="flex flex-wrap items-center gap-2"><Badge variant="secondary">Cycle {run.cycleNumber}</Badge><Badge variant="secondary">{run.status}</Badge><span className="font-mono text-xs text-muted-foreground">{new Date(run.startedAt).toLocaleString()}</span>{run.finishedAt ? <span className="font-mono text-xs text-muted-foreground">→ {new Date(run.finishedAt).toLocaleString()}</span> : null}</div><p className="mt-2 text-sm">{run.topic || "No topic selected"}</p><p className="mt-2 text-xs text-muted-foreground">Published: {run.published} · Rejected: {run.rejected}</p>{run.error ? <p className="mt-2 text-xs text-destructive">{run.error}</p> : null}<details className="mt-3 text-xs text-muted-foreground"><summary className="cursor-pointer">Execution details</summary><pre className="mt-2 overflow-auto rounded-lg bg-secondary p-3">{JSON.stringify(run.details, null, 2)}</pre></details></article>)}</div>}
      </section>
    </div>
  );
}
