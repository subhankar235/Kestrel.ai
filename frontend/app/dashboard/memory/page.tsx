"use client";

import { Brain, Network } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useDashboard } from "@/hooks/use-dashboard";

export default function MemoryPage() {
  const { data, loading, error } = useDashboard();
  if (loading) return <p className="text-sm text-muted-foreground">Loading memory...</p>;
  if (error || !data) return <p className="text-sm text-destructive">{error || "Memory unavailable"}</p>;

  const concepts = new Set(data.memory.flatMap((item) => item.concepts));

  return (
    <div className="space-y-6 pb-12">
      <section className="grid gap-4 sm:grid-cols-3">
        <div className="surface-card flex items-center gap-4 p-5">
          <Brain className="size-5 text-accent" />
          <div><p className="font-display text-2xl font-semibold">{data.memory.length}</p><p className="text-xs text-muted-foreground">Memory results</p></div>
        </div>
        <div className="surface-card flex items-center gap-4 p-5">
          <Network className="size-5 text-accent" />
          <div><p className="font-display text-2xl font-semibold">{concepts.size}</p><p className="text-xs text-muted-foreground">Concepts returned</p></div>
        </div>
        <div className="surface-card p-5">
          <p className="font-display text-2xl font-semibold">{data.posts.length}</p>
          <p className="text-xs text-muted-foreground">Published posts in memory context</p>
        </div>
      </section>

      <section className="surface-card p-5">
        <h2 className="mb-4 font-display text-base font-semibold">Breeth memory results</h2>
        {data.memory.length === 0 ? (
          <p className="text-sm text-muted-foreground">Breeth returned no memory results for this persona.</p>
        ) : (
          <ul className="space-y-3">
            {data.memory.map((item) => (
              <li key={item.id} className="rounded-xl border border-[var(--surface-border)] p-4">
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">score {item.score.toFixed(2)}</Badge>
                  <span className="font-mono text-[10px] text-muted-foreground">{item.id}</span>
                </div>
                <p className="mt-2 text-sm leading-relaxed">{item.text}</p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {item.concepts.map((concept) => <span key={concept} className="rounded-md bg-secondary px-2 py-0.5 font-mono text-[10px]">#{concept}</span>)}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
