"use client";

import Link from "next/link";
import { ArrowUpRight, Ban, Brain, CheckCircle2, Clock } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useDashboard } from "@/hooks/use-dashboard";

function Stat({ label, value, hint, icon: Icon }: { label: string; value: string; hint: string; icon: React.ElementType }) {
  return <div className="surface-card p-5"><div className="flex items-start justify-between"><span className="text-xs uppercase tracking-widest text-muted-foreground">{label}</span><Icon className="size-4 text-accent" /></div><p className="mt-3 font-display text-3xl font-semibold">{value}</p><p className="mt-1 text-xs text-muted-foreground">{hint}</p></div>;
}

export default function Overview() {
  const { data, loading, error } = useDashboard();
  if (loading) return <p className="text-sm text-muted-foreground">Loading dashboard...</p>;
  if (error || !data) return <p className="text-sm text-destructive">{error || "Dashboard unavailable"}</p>;

  const totalDecisions = data.posts.length + data.topicDebt.length;
  const acceptanceRate = totalDecisions ? Math.round((data.posts.length / totalDecisions) * 100) : 0;
  const latest = data.posts[0];

  return <div className="space-y-6 pb-12">
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <Stat label="Published" value={String(data.posts.length)} hint={`${data.cycleCount} cycles recorded`} icon={CheckCircle2} />
      <Stat label="Rejected" value={String(data.topicDebt.length)} hint={`${acceptanceRate}% acceptance rate`} icon={Ban} />
      <Stat label="Memory results" value={String(data.memory.length)} hint="Breeth search results" icon={Brain} />
      <Stat label="Scheduler" value={data.cycle?.status || "unknown"} hint={data.cycle?.nextRunTime || "Next run unavailable"} icon={Clock} />
    </section>

    <section className="grid gap-4 lg:grid-cols-2">
      <div className="surface-card p-5">
        <div className="mb-3 flex items-center justify-between"><h2 className="font-display text-base font-semibold">Latest publication</h2><Link href="/dashboard/feed" className="inline-flex items-center gap-1 text-xs text-accent hover:underline">Open feed <ArrowUpRight className="size-3" /></Link></div>
        {latest ? <><h3 className="font-display text-lg font-semibold">{latest.text.split(/[.!?]\s/)[0] || latest.id}</h3><p className="mt-2 line-clamp-5 text-sm leading-relaxed text-muted-foreground">{latest.text}</p><p className="mt-3 font-mono text-[11px] text-muted-foreground">{new Date(latest.createdAt).toLocaleString()} · {latest.sources.length} sources</p></> : <p className="text-sm text-muted-foreground">No publications yet.</p>}
      </div>
      <div className="surface-card p-5"><h2 className="mb-3 font-display text-base font-semibold">Configured sources</h2><ul className="space-y-2">{data.sources.map((source) => <li key={source.name} className="flex items-center justify-between rounded-xl border border-[var(--surface-border)] px-3 py-2 text-sm"><span>{source.name}</span><Badge variant="secondary">{source.configured ? "configured" : "not configured"}</Badge></li>)}</ul></div>
    </section>

    <section className="surface-card p-5"><div className="mb-3 flex items-center justify-between"><h2 className="font-display text-base font-semibold">Topic debt queue</h2><Link href="/dashboard/decisions" className="text-xs text-accent hover:underline">All decisions</Link></div>{data.topicDebt.length ? <ul className="space-y-2">{data.topicDebt.slice(0, 6).map((item) => <li key={item.id} className="rounded-xl border border-[var(--surface-border)] px-3 py-2.5"><div className="flex items-center gap-2"><span className="min-w-0 flex-1 truncate text-sm">{item.title}</span><span className="font-mono text-[11px] text-destructive">{item.score.toFixed(2)}</span></div><p className="mt-1 text-[11px] text-muted-foreground">Revisit when: {item.revisitCondition}</p></li>)}</ul> : <p className="text-sm text-muted-foreground">No rejected topics recorded.</p>}</section>
  </div>;
}
