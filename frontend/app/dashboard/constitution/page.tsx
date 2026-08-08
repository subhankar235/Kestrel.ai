import { GitCommitVertical, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { constitution, formatDate } from "@/lib/mock-data";

export const metadata = {
  title: "Constitution — Ada Agent Console",
  description:
    "The self-evolving editorial constitution: current rules, scoring threshold and the audit history behind each version bump.",
};

export default function ConstitutionPage() {
  return (
    <div className="space-y-6 pb-12">
      <section className="surface-card gradient-border overflow-hidden p-6">
        <div className="flex flex-wrap items-center gap-3">
          <ShieldCheck className="size-5 text-accent" />
          <h2 className="font-display text-xl font-semibold">
            Editorial constitution{" "}
            <span className="text-gradient">{constitution.version}</span>
          </h2>
          <Badge variant="secondary" className="font-mono">
            threshold {constitution.threshold}
          </Badge>
          <span className="ml-auto font-mono text-xs text-muted-foreground">
            updated {formatDate(constitution.updatedAt)} UTC
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
            {constitution.rules.map((r) => (
              <li key={r.id} className="rounded-xl border border-[var(--surface-border)] p-4">
                <p className="text-sm">{r.rule}</p>
                <div className="mt-2 flex items-center gap-2">
                  <Badge variant="secondary" className="font-mono text-[10px]">
                    {r.weight}
                  </Badge>
                  <span className="font-mono text-[10px] text-muted-foreground">
                    added {r.addedIn}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className="surface-card p-5">
          <h3 className="mb-4 font-display text-base font-semibold">Version history</h3>
          <ol className="relative space-y-5 border-l border-[var(--surface-border)] pl-6">
            {constitution.history.map((h) => (
              <li key={h.version} className="relative">
                <span className="absolute -left-[31px] top-0.5 grid size-4 place-items-center rounded-full bg-card">
                  <GitCommitVertical className="size-3.5 text-primary" />
                </span>
                <div className="flex items-center gap-2">
                  <p className="font-display text-sm font-semibold">{h.version}</p>
                  <span className="font-mono text-[10px] text-muted-foreground">
                    {formatDate(h.at)} UTC
                  </span>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{h.finding}</p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {h.changed.map((c) => (
                    <span
                      key={c}
                      className="rounded-md bg-secondary px-2 py-0.5 font-mono text-[10px] text-accent"
                    >
                      {c}
                    </span>
                  ))}
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>
    </div>
  );
}
