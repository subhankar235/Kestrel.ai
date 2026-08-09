import { Radar } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { sources } from "@/lib/mock-data";

export const metadata = {
  title: "Discovery sources — Ada Agent Console",
  description:
    "Live discovery surfaces Ada scans every cycle: papers, advisories, neural search, news and RSS, with pull health.",
};

export default function SourcesPage() {
  const total = sources.reduce((n, s) => n + s.items, 0);

  return (
    <div className="space-y-6 pb-12">
      <section className="surface-card flex flex-wrap items-center gap-4 p-6">
        <span className="grid size-11 place-items-center rounded-2xl bg-secondary">
          <Radar className="size-5 text-accent" />
        </span>
        <div>
          <h2 className="font-display text-lg font-semibold">
            {total.toLocaleString()} items scanned
          </h2>
          <p className="text-xs text-muted-foreground">
            Across {sources.length} live surfaces · discovery runs at the head of every cycle
          </p>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {sources.map((s) => (
          <article key={s.name} className="surface-card p-5">
            <div className="flex items-start justify-between gap-3">
              <h3 className="font-display text-sm font-semibold leading-snug">{s.name}</h3>
              <Badge
                variant="secondary"
                className={
                  s.health === "ok" ? "bg-success/15 text-success" : "bg-warning/15 text-warning"
                }
              >
                {s.health}
              </Badge>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">{s.kind}</p>
            <p className="mt-4 font-display text-2xl font-semibold">{s.items}</p>
            <p className="font-mono text-[11px] text-muted-foreground">
              items · last pull {s.lastPull}
            </p>
          </article>
        ))}
      </section>
    </div>
  );
}
