"use client";

import { ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useDashboard } from "@/hooks/use-dashboard";

export default function ConstitutionPage() {
  const { data, loading, error } = useDashboard();
  const liveConstitution = data?.constitution;

  if (loading) return <p className="text-sm text-muted-foreground">Loading constitution...</p>;
  if (error || !liveConstitution) return <p className="text-sm text-destructive">{error || "Constitution unavailable"}</p>;

  const rules = Array.isArray(liveConstitution.rules)
    ? liveConstitution.rules.map((rule, index) => [String(index + 1), rule] as const)
    : Object.entries(liveConstitution.rules as Record<string, unknown>);

  return (
    <div className="space-y-6 pb-12">
      <section className="surface-card gradient-border overflow-hidden p-6">
        <div className="flex flex-wrap items-center gap-3">
          <ShieldCheck className="size-5 text-accent" />
          <h2 className="font-display text-xl font-semibold">
            Editorial constitution{" "}
            <span className="text-gradient">{liveConstitution.version}</span>
          </h2>
          <Badge variant="secondary" className="font-mono">
              active version
          </Badge>
          <span className="ml-auto font-mono text-xs text-muted-foreground">
            updated {new Date(liveConstitution.createdAt).toLocaleString()}
          </span>
        </div>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Rules are written by the agent itself during periodic self-audits. No human has edited
          this document since initialization.
        </p>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="surface-card p-5">
          <h3 className="mb-4 font-display text-base font-semibold">Active rules</h3>
          <ul className="space-y-3">
            {rules.length === 0 ? <p className="text-sm text-muted-foreground">No constitution rules returned.</p> : rules.map(([name, rule]) => (
              <li key={name} className="rounded-xl border border-[var(--surface-border)] p-4">
                <p className="text-xs uppercase tracking-widest text-muted-foreground">{name}</p>
                <p className="mt-1 text-sm">{typeof rule === "string" ? rule : JSON.stringify(rule)}</p>
                <Badge variant="secondary" className="mt-2 font-mono text-[10px]">
                  active
                </Badge>
              </li>
            ))}
          </ul>
        </div>

        <div className="surface-card p-5">
          <h3 className="mb-4 font-display text-base font-semibold">Version history</h3>
          <p className="text-sm text-muted-foreground">
            The current version was created at {new Date(liveConstitution.createdAt).toLocaleString()}.
            Historical versions are not exposed by the current backend schema.
          </p>
        </div>
      </section>
    </div>
  );
}
