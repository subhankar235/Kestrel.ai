"use client";

import { Radar } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useDashboard } from "@/hooks/use-dashboard";

export default function SourcesPage() {
  const { data, loading, error } = useDashboard();
  if (loading) return <p className="text-sm text-muted-foreground">Loading sources...</p>;
  if (error || !data) return <p className="text-sm text-destructive">{error || "Sources unavailable"}</p>;

  return (
    <div className="space-y-6 pb-12">
      <section className="surface-card flex items-center gap-4 p-6">
        <Radar className="size-5 text-accent" />
        <div><h2 className="font-display text-lg font-semibold">Configured discovery sources</h2><p className="text-xs text-muted-foreground">Live configuration reported by the backend</p></div>
      </section>
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {data.sources.map((source) => (
          <article key={source.name} className="surface-card p-5">
            <div className="flex items-start justify-between gap-3">
              <h3 className="font-display text-sm font-semibold">{source.name}</h3>
              <Badge variant="secondary" className={source.configured ? "bg-success/15 text-success" : "bg-warning/15 text-warning"}>
                {source.configured ? "configured" : "not configured"}
              </Badge>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">{source.kind}</p>
          </article>
        ))}
      </section>
    </div>
  );
}
