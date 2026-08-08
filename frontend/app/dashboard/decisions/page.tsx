import { Ban, CheckCircle2, RotateCcw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { formatDate, posts, stats, topicDebt } from "@/lib/mock-data";

export const metadata = {
  title: "Decisions — Ada Agent Console",
  description:
    "Accepted and rejected topics with scores, reasons and revisit conditions — the agent's editorial judgment in the open.",
};

const statusStyle: Record<string, string> = {
  WAITING: "bg-warning/15 text-warning",
  RESURRECTED: "bg-success/15 text-success",
  EXPIRED: "bg-muted text-muted-foreground",
};

export default function DecisionsPage() {
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
            {stats.acceptanceRate}
            <span className="text-base text-muted-foreground">% accepted</span>
          </p>
        </div>
        <div className="mt-4 flex h-3 overflow-hidden rounded-full bg-secondary">
          <div
            className="bg-gradient-to-r from-primary to-accent"
            style={{ width: `${stats.acceptanceRate}%` }}
            aria-label="accepted share"
          />
        </div>
        <div className="mt-2 flex justify-between font-mono text-[11px] text-muted-foreground">
          <span>{stats.published} published</span>
          <span>{stats.rejected} rejected · {stats.topicDebt} in debt queue</span>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="surface-card p-5">
          <h2 className="mb-4 flex items-center gap-2 font-display text-base font-semibold">
            <CheckCircle2 className="size-4 text-success" /> Accepted
          </h2>
          <ul className="space-y-3">
            {posts.map((p) => (
              <li key={p.id} className="rounded-xl border border-[var(--surface-border)] p-4">
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm font-medium leading-snug">{p.title}</p>
                  <span className="font-mono text-xs text-success">{p.score.toFixed(2)}</span>
                </div>
                <p className="mt-1.5 text-xs text-muted-foreground">{p.rationale.whySelected}</p>
                <div className="mt-3">
                  <Progress value={p.score * 100} className="h-1" />
                </div>
                <p className="mt-2 font-mono text-[10px] text-muted-foreground">
                  {p.id} · {formatDate(p.createdAt)} UTC
                </p>
              </li>
            ))}
          </ul>
        </div>

        <div className="surface-card p-5">
          <h2 className="mb-4 flex items-center gap-2 font-display text-base font-semibold">
            <Ban className="size-4 text-destructive" /> Rejected — topic debt
          </h2>
          <ul className="space-y-3">
            {topicDebt.map((t) => (
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
                  {t.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-md bg-secondary px-2 py-0.5 font-mono text-[10px] text-muted-foreground"
                    >
                      {tag}
                    </span>
                  ))}
                  <span className="ml-auto font-mono text-[10px] text-muted-foreground">
                    {t.id}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}
