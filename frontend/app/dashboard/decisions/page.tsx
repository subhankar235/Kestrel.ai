"use client";

import { Ban, CheckCircle2, RotateCcw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useDashboard } from "@/hooks/use-dashboard";

const statusStyle: Record<string, string> = {
  WAITING: "bg-warning/15 text-warning",
  RESURRECTED: "bg-success/15 text-success",
  EXPIRED: "bg-muted text-muted-foreground",
};

export default function DecisionsPage() {
  const { data, loading, error } = useDashboard();
  if (loading) return <p className="text-sm text-muted-foreground">Loading decisions...</p>;
  if (error || !data) return <p className="text-sm text-destructive">{error || "Decisions unavailable"}</p>;

  const accepted = data.posts;
  const rejected = data.topicDebt;
  const total = accepted.length + rejected.length;
  const acceptanceRate = total ? Math.round((accepted.length / total) * 100) : 0;

  return (
    <div className="space-y-6 pb-12">
      <section className="surface-card p-5">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 className="font-display text-base font-semibold">Judgment ratio</h2>
            <p className="text-xs text-muted-foreground">
              Ada rejects most of what it finds — saying no is the point
            </p>
          </div>
          <p className="font-display text-3xl font-semibold">
            {acceptanceRate}
            <span className="text-base text-muted-foreground">% accepted</span>
          </p>
        </div>
        <div className="mt-4 flex h-3 overflow-hidden rounded-full bg-secondary">
          <div
            className="bg-gradient-to-r from-primary to-accent"
             style={{ width: `${acceptanceRate}%` }}
            aria-label="accepted share"
          />
        </div>
        <div className="mt-2 flex justify-between font-mono text-[11px] text-muted-foreground">
           <span>{accepted.length} published</span>
           <span>{rejected.length} rejected · {rejected.length} in debt queue</span>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="surface-card p-5">
          <h2 className="mb-4 flex items-center gap-2 font-display text-base font-semibold">
            <CheckCircle2 className="size-4 text-success" /> Accepted
          </h2>
           {accepted.length === 0 ? <p className="text-sm text-muted-foreground">No accepted posts recorded yet.</p> : <ul className="space-y-3">
              {accepted.map((p) => (
               <li key={p.id} className="rounded-xl border border-[var(--surface-border)] p-4">
                 <div className="flex items-start justify-between gap-3">
                   <p className="text-sm font-medium leading-snug">{p.text.split(/[.!?]\s/)[0] || p.id}</p>
                   <span className="font-mono text-xs text-success">available in workflow data</span>
                 </div>
                 <p className="mt-1.5 text-xs text-muted-foreground">{p.rationale}</p>
                 <p className="mt-2 font-mono text-[10px] text-muted-foreground">{p.id} · {new Date(p.createdAt).toLocaleString()}</p>
              </li>
             ))}
           </ul>}
        </div>

        <div className="surface-card p-5">
          <h2 className="mb-4 flex items-center gap-2 font-display text-base font-semibold">
            <Ban className="size-4 text-destructive" /> Rejected — topic debt
          </h2>
           {rejected.length === 0 ? <p className="text-sm text-muted-foreground">No rejected topics or topic debt recorded yet.</p> : <ul className="space-y-3">
              {rejected.map((t) => (
              <li key={t.id} className="rounded-xl border border-[var(--surface-border)] p-4">
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm font-medium leading-snug">{t.title}</p>
                  <span className="font-mono text-xs text-destructive">{t.score.toFixed(2)}</span>
                </div>
                <p className="mt-1.5 text-xs text-muted-foreground">{t.reason}</p>
                <p className="mt-2 flex items-start gap-1.5 rounded-lg bg-secondary/60 p-2 text-[11px] text-muted-foreground">
                  <RotateCcw className="mt-0.5 size-3 shrink-0" />
                  Revisit when: {t.revisitCondition}
                </p>
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <Badge variant="secondary" className={statusStyle[t.status]}>
                    {t.status.toLowerCase()}
                  </Badge>
                  <span className="ml-auto font-mono text-[10px] text-muted-foreground">
                    {t.id}
                  </span>
                </div>
              </li>
             ))}
           </ul>}
        </div>
      </section>
    </div>
  );
}
