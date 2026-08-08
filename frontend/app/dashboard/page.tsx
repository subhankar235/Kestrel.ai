"use client";

import Link from "next/link";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ArrowUpRight, Ban, Brain, CheckCircle2, Clock, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  cycleActivity,
  cycles,
  openPredictions,
  posts,
  relationshipLabel,
  relativeTime,
  scoreBreakdown,
  stats,
  topicDebt,
} from "@/lib/mock-data";

function Stat({
  label,
  value,
  hint,
  icon: Icon,
}: {
  label: string;
  value: string;
  hint: string;
  icon: React.ElementType;
}) {
  return (
    <div className="surface-card p-5">
      <div className="flex items-start justify-between">
        <span className="text-xs uppercase tracking-widest text-muted-foreground">{label}</span>
        <Icon className="size-4 text-accent" />
      </div>
      <p className="mt-3 font-display text-3xl font-semibold">{value}</p>
      <p className="mt-1 text-xs text-muted-foreground">{hint}</p>
    </div>
  );
}

export default function Overview() {
  const latest = posts[0]!;

  return (
    <div className="space-y-6 pb-12">
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Stat
          label="Published"
          value={String(stats.published)}
          hint={`${stats.cyclesRun} cycles run`}
          icon={CheckCircle2}
        />
        <Stat
          label="Rejected"
          value={String(stats.rejected)}
          hint={`${stats.acceptanceRate}% acceptance rate`}
          icon={Ban}
        />
        <Stat
          label="Memory episodes"
          value={String(stats.memoryEpisodes)}
          hint={`${stats.openPredictions} open predictions`}
          icon={Brain}
        />
        <Stat
          label="Avg cycle"
          value={`${stats.avgCycleMinutes}m`}
          hint={`Next run in ${stats.nextCycleInMinutes}m`}
          icon={Clock}
        />
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <div className="surface-card p-5 lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="font-display text-base font-semibold">Cycle activity</h2>
              <p className="text-xs text-muted-foreground">
                Candidates discovered vs published vs rejected across the evaluation window
              </p>
            </div>
            <Badge variant="secondary" className="font-mono text-[10px]">
              last 40h
            </Badge>
          </div>
          <div className="h-[240px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={cycleActivity}>
                <defs>
                  <linearGradient id="gCand" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--chart-2)" stopOpacity={0.5} />
                    <stop offset="100%" stopColor="var(--chart-2)" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gPub" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--chart-1)" stopOpacity={0.6} />
                    <stop offset="100%" stopColor="var(--chart-1)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="var(--grid-line)" vertical={false} />
                <XAxis dataKey="hour" tickLine={false} axisLine={false} fontSize={11} stroke="var(--muted-foreground)" />
                <YAxis tickLine={false} axisLine={false} fontSize={11} stroke="var(--muted-foreground)" width={24} />
                <Tooltip
                  contentStyle={{
                    background: "var(--popover)",
                    border: "1px solid var(--border)",
                    borderRadius: 12,
                    fontSize: 12,
                    color: "var(--popover-foreground)",
                  }}
                />
                <Area
                  type="monotone"
                  isAnimationActive={false}
                  dataKey="candidates"
                  stroke="var(--chart-2)"
                  fill="url(#gCand)"
                  strokeWidth={2}
                />
                <Area
                  type="monotone"
                  isAnimationActive={false}
                  dataKey="rejected"
                  stroke="var(--chart-5)"
                  fill="transparent"
                  strokeWidth={1.5}
                  strokeDasharray="4 4"
                />
                <Area
                  type="monotone"
                  isAnimationActive={false}
                  dataKey="published"
                  stroke="var(--chart-1)"
                  fill="url(#gPub)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="surface-card p-5">
          <h2 className="font-display text-base font-semibold">Editorial scoring profile</h2>
          <p className="mb-4 text-xs text-muted-foreground">
            Rolling average across the last 20 judged candidates
          </p>
          <div className="space-y-4">
            {scoreBreakdown.map((s) => (
              <div key={s.axis}>
                <div className="mb-1.5 flex justify-between text-xs">
                  <span className="text-muted-foreground">{s.axis}</span>
                  <span className="font-mono">{s.value}</span>
                </div>
                <Progress value={s.value} className="h-1.5" />
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <div className="surface-card p-5 lg:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-display text-base font-semibold">Latest publication</h2>
            <Link
              href="/dashboard/feed"
              className="inline-flex items-center gap-1 text-xs text-accent hover:underline"
            >
              Open feed <ArrowUpRight className="size-3" />
            </Link>
          </div>
          {latest.relationship ? (
            <Badge className="mb-3 bg-primary/15 text-primary" variant="secondary">
              <Sparkles className="mr-1 size-3" />
              {relationshipLabel[latest.relationship]}
            </Badge>
          ) : null}
          <h3 className="font-display text-lg font-semibold">{latest.title}</h3>
          <p className="mt-2 line-clamp-4 text-sm leading-relaxed text-muted-foreground">
            {latest.text}
          </p>
          <p className="mt-3 font-mono text-[11px] text-muted-foreground">
            {relativeTime(latest.createdAt)} · score {latest.score.toFixed(2)} ·{" "}
            {latest.sources.length} sources
          </p>
        </div>

        <div className="surface-card p-5">
          <h2 className="mb-3 font-display text-base font-semibold">Open predictions</h2>
          <ul className="space-y-3">
            {openPredictions.map((p) => (
              <li key={p.id} className="rounded-xl border border-[var(--surface-border)] p-3">
                <p className="text-sm leading-snug">{p.claim}</p>
                <div className="mt-2 flex items-center justify-between text-[11px] text-muted-foreground">
                  <span className="font-mono">conf {p.confidence.toFixed(2)}</span>
                  <Badge
                    variant="secondary"
                    className={
                      p.status === "OPEN"
                        ? "bg-accent/15 text-accent"
                        : "bg-destructive/15 text-destructive"
                    }
                  >
                    {p.status.replace("_", " ").toLowerCase()}
                  </Badge>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="surface-card p-5">
          <h2 className="mb-3 font-display text-base font-semibold">Recent cycles</h2>
          <ul className="space-y-2">
            {cycles.slice(0, 4).map((c) => (
              <li
                key={c.id}
                className="flex items-center gap-3 rounded-xl border border-[var(--surface-border)] px-3 py-2.5"
              >
                <span className="font-mono text-[11px] text-muted-foreground">{c.id}</span>
                <span className="min-w-0 flex-1 truncate text-sm">{c.note}</span>
                <Badge
                  variant="secondary"
                  className={
                    c.outcome === "PUBLISHED"
                      ? "bg-success/15 text-success"
                      : c.outcome === "AUDIT"
                        ? "bg-warning/15 text-warning"
                        : "bg-muted text-muted-foreground"
                  }
                >
                  {c.outcome.toLowerCase()}
                </Badge>
              </li>
            ))}
          </ul>
        </div>

        <div className="surface-card p-5">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-display text-base font-semibold">Topic debt queue</h2>
            <Link href="/dashboard/decisions" className="text-xs text-accent hover:underline">
              All decisions
            </Link>
          </div>
          <ul className="space-y-2">
            {topicDebt.slice(0, 4).map((t) => (
              <li key={t.id} className="rounded-xl border border-[var(--surface-border)] px-3 py-2.5">
                <div className="flex items-center gap-2">
                  <span className="min-w-0 flex-1 truncate text-sm">{t.title}</span>
                  <span className="font-mono text-[11px] text-destructive">
                    {t.score.toFixed(2)}
                  </span>
                </div>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  Revisit when: {t.revisitCondition}
                </p>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}
