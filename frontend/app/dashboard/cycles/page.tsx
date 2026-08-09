"use client";

import { useState } from "react";
import { AlertTriangle, Check, MinusCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cycles, formatDate } from "@/lib/mock-data";

const stepIcon = {
  ok: <Check className="size-3 text-success" />,
  warn: <AlertTriangle className="size-3 text-warning" />,
  skip: <MinusCircle className="size-3 text-muted-foreground" />,
};

export default function CyclesPage() {
  const [active, setActive] = useState(cycles[0]!.id);
  const cycle = cycles.find((c) => c.id === active)!;

  return (
    <div className="grid gap-4 pb-12 lg:grid-cols-[320px_1fr]">
      <div className="surface-card h-fit p-4">
        <h2 className="mb-3 px-1 font-display text-base font-semibold">Cycle log</h2>
        <ul className="space-y-1.5">
          {cycles.map((c) => (
            <li key={c.id}>
              <button
                type="button"
                onClick={() => setActive(c.id)}
                className={`w-full rounded-xl border px-3 py-2.5 text-left transition-colors ${
                  c.id === active
                    ? "border-primary/40 bg-secondary"
                    : "border-transparent hover:bg-secondary/60"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[11px] text-muted-foreground">{c.id}</span>
                  <Badge
                    variant="secondary"
                    className={`ml-auto ${
                      c.outcome === "PUBLISHED"
                        ? "bg-success/15 text-success"
                        : c.outcome === "AUDIT"
                          ? "bg-warning/15 text-warning"
                          : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {c.outcome.toLowerCase()}
                  </Badge>
                </div>
                <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{c.note}</p>
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="surface-card p-6">
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="font-display text-lg font-semibold">{cycle.id}</h2>
          <span className="font-mono text-xs text-muted-foreground">
            {formatDate(cycle.startedAt)} UTC · {cycle.durationMin} min
          </span>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">{cycle.note}</p>

        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          {[
            { k: "Candidates", v: cycle.candidates },
            { k: "Published", v: cycle.published },
            { k: "Rejected", v: cycle.rejected },
          ].map((m) => (
            <div key={m.k} className="rounded-xl border border-[var(--surface-border)] p-4">
              <p className="font-display text-2xl font-semibold">{m.v}</p>
              <p className="text-xs text-muted-foreground">{m.k}</p>
            </div>
          ))}
        </div>

        <h3 className="mt-7 font-display text-sm font-semibold uppercase tracking-widest text-muted-foreground">
          Pipeline trace
        </h3>
        <ol className="mt-3 space-y-3 border-l border-[var(--surface-border)] pl-6">
          {cycle.steps.map((s) => (
            <li key={s.name} className="relative">
              <span className="absolute -left-[31px] top-1 grid size-4 place-items-center rounded-full border border-[var(--surface-border)] bg-card">
                {stepIcon[s.status]}
              </span>
              <p className="text-sm font-medium">{s.name}</p>
              <p className="text-xs text-muted-foreground">{s.detail}</p>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
