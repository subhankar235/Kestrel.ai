import { Brain, GitBranch, Lightbulb, Network, Target } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  concepts,
  memoryEpisodes,
  openPredictions,
  posts,
  relativeTime,
  stats,
} from "@/lib/mock-data";

export const metadata = {
  title: "Memory — Ada Agent Console",
  description:
    "Ada's long-term memory: story arcs, beliefs, predictions and the concept graph that drives what it researches next.",
};

const typeStyle: Record<string, string> = {
  STORY: "bg-primary/15 text-primary",
  PREDICTION: "bg-accent/15 text-accent",
  BELIEF: "bg-success/15 text-success",
  CONCEPT: "bg-warning/15 text-warning",
  DECISION: "bg-muted text-muted-foreground",
};

export default function MemoryPage() {
  const chapters = posts
    .filter((p) => p.storyId === "story_registry_trust")
    .sort((a, b) => (a.chapter ?? 0) - (b.chapter ?? 0));

  return (
    <div className="space-y-6 pb-12">
      <section className="grid gap-4 sm:grid-cols-3">
        {[
          { label: "Episodes stored", value: stats.memoryEpisodes, icon: Brain },
          { label: "Concept nodes", value: concepts.length, icon: Network },
          { label: "Open predictions", value: stats.openPredictions, icon: Target },
        ].map((s) => (
          <div key={s.label} className="surface-card flex items-center gap-4 p-5">
            <span className="grid size-10 place-items-center rounded-xl bg-secondary">
              <s.icon className="size-4 text-accent" />
            </span>
            <div>
              <p className="font-display text-2xl font-semibold">{s.value}</p>
              <p className="text-xs text-muted-foreground">{s.label}</p>
            </div>
          </div>
        ))}
      </section>

      <section className="grid gap-4 lg:grid-cols-5">
        <div className="surface-card p-5 lg:col-span-3">
          <h2 className="font-display text-base font-semibold">Active story arc</h2>
          <p className="mb-4 text-xs text-muted-foreground">
            Trust in model registries — memory keeps this thread alive across cycles
          </p>
          <ol className="relative space-y-4 border-l border-[var(--surface-border)] pl-6">
            {chapters.map((c) => (
              <li key={c.id} className="relative">
                <span className="absolute -left-[31px] top-1 grid size-4 place-items-center rounded-full bg-gradient-to-br from-primary to-accent text-[9px] font-bold text-primary-foreground">
                  {c.chapter}
                </span>
                <p className="text-sm font-medium">{c.title}</p>
                <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{c.text}</p>
                <p className="mt-1 font-mono text-[10px] text-muted-foreground">
                  {c.id} · {relativeTime(c.createdAt)}
                </p>
              </li>
            ))}
            <li className="relative">
              <span className="absolute -left-[31px] top-1 grid size-4 place-items-center rounded-full border border-dashed border-accent" />
              <p className="text-sm font-medium text-muted-foreground">
                Chapter 4 — pending condition
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Waiting on evidence for provenance that survives fine-tuning.
              </p>
            </li>
          </ol>
        </div>

        <div className="surface-card p-5 lg:col-span-2">
          <h2 className="font-display text-base font-semibold">Concept graph</h2>
          <p className="mb-4 text-xs text-muted-foreground">
            Node size = mentions · low-edge nodes are gap-filling candidates
          </p>
          <div className="flex flex-wrap gap-2">
            {concepts.map((c) => (
              <span
                key={c.name}
                style={{ fontSize: `${11 + c.weight * 0.45}px` }}
                className={`rounded-full border px-3 py-1 font-mono transition-colors ${
                  c.edges <= 4
                    ? "border-accent/50 bg-accent/10 text-accent"
                    : "border-[var(--surface-border)] text-muted-foreground"
                }`}
                title={`${c.weight} mentions · ${c.edges} edges`}
              >
                {c.name}
              </span>
            ))}
          </div>
          <p className="mt-4 flex items-start gap-2 rounded-xl bg-secondary/60 p-3 text-xs text-muted-foreground">
            <Lightbulb className="mt-0.5 size-3.5 shrink-0 text-accent" />
            Highlighted nodes have few connections — Ada targets those gaps to generate genuinely
            new angles rather than reacting to news.
          </p>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="surface-card p-5">
          <h2 className="mb-4 font-display text-base font-semibold">Recent memory writes</h2>
          <ul className="space-y-3">
            {memoryEpisodes.map((e) => (
              <li key={e.id} className="rounded-xl border border-[var(--surface-border)] p-3">
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className={typeStyle[e.type]}>
                    {e.type.toLowerCase()}
                  </Badge>
                  <span className="min-w-0 flex-1 truncate text-sm font-medium">{e.title}</span>
                  <span className="font-mono text-[10px] text-muted-foreground">
                    {relativeTime(e.createdAt)}
                  </span>
                </div>
                <p className="mt-1.5 text-xs text-muted-foreground">{e.summary}</p>
                <p className="mt-1.5 flex items-center gap-1 font-mono text-[10px] text-muted-foreground">
                  <GitBranch className="size-3" /> {e.links} links
                  {e.status ? ` · ${e.status.toLowerCase()}` : ""}
                </p>
              </li>
            ))}
          </ul>
        </div>

        <div className="surface-card p-5">
          <h2 className="mb-4 font-display text-base font-semibold">Prediction ledger</h2>
          <ul className="space-y-3">
            {openPredictions.map((p) => (
              <li key={p.id} className="rounded-xl border border-[var(--surface-border)] p-4">
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm leading-snug">{p.claim}</p>
                  <Badge
                    variant="secondary"
                    className={
                      p.status === "OPEN"
                        ? "bg-accent/15 text-accent"
                        : "bg-destructive/15 text-destructive"
                    }
                  >
                    {p.status === "OPEN" ? "open" : "wrong"}
                  </Badge>
                </div>
                <p className="mt-2 text-xs text-muted-foreground">
                  Resolves when: {p.resolutionCondition}
                </p>
                <div className="mt-3">
                  <div className="mb-1 flex justify-between font-mono text-[10px] text-muted-foreground">
                    <span>confidence</span>
                    <span>{p.confidence.toFixed(2)}</span>
                  </div>
                  <Progress value={p.confidence * 100} className="h-1.5" />
                </div>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}
