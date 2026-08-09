"use client";

import { Quote } from "lucide-react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { useDashboard } from "@/hooks/use-dashboard";
import { useAgents } from "@/hooks/use-agents";

export default function PersonaPage() {
  const { data, loading, error } = useDashboard();
  const { agents } = useAgents();
  const livePersona = data?.persona;

  if (loading) return <p className="text-sm text-muted-foreground">Loading persona...</p>;
  if (error || !livePersona) {
    return (
      <div className="surface-card mx-auto max-w-md p-8 text-center">
        <h2 className="font-display text-xl font-semibold">No persona created yet</h2>
        <p className="mt-2 text-sm text-muted-foreground">Create your first persona to start researching and publishing.</p>
        <Link href="/init" className="mt-6 inline-flex rounded-xl bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">
          Create your first persona
        </Link>
      </div>
    );
  }
  const voiceRules = Array.isArray(livePersona.voiceConfig.vocabulary_rules) ? livePersona.voiceConfig.vocabulary_rules : [];
  const stance = typeof livePersona.voiceConfig.stance === "string" ? livePersona.voiceConfig.stance : "No stance configured.";
  const intervalLabel = data.publishIntervalMinutes < 60
    ? `Every ${data.publishIntervalMinutes} minute${data.publishIntervalMinutes === 1 ? "" : "s"}`
    : `Every ${data.publishIntervalMinutes / 60} hour${data.publishIntervalMinutes === 60 ? "" : "s"}`;
  function openPersona(agentId: string) {
    window.localStorage.setItem("kestrel.agentId", agentId);
    window.location.reload();
  }

  return (
    <div className="space-y-6 pb-12">
      <section className="surface-card noise-overlay relative overflow-hidden p-8">
        <div className="flex flex-wrap items-center gap-5">
          <span className="grid size-16 place-items-center rounded-3xl bg-gradient-to-br from-primary to-accent font-display text-2xl font-bold text-primary-foreground">
            A
          </span>
          <div>
            <h2 className="font-display text-2xl font-semibold">{livePersona.name}</h2>
            <p className="text-sm text-muted-foreground">{livePersona.domain}</p>
          </div>
          <div className="ml-auto flex flex-wrap gap-2">
            <Badge variant="secondary" className="bg-success/15 text-success">
              {data.status.toLowerCase()}
            </Badge>
            <Badge variant="secondary" className="font-mono">
              {data.constitution?.version || "unversioned"}
            </Badge>
            <Link href="/init" className="rounded-full bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground">
              Create another persona
            </Link>
          </div>
        </div>
        <p className="mt-6 flex max-w-2xl gap-3 text-sm leading-relaxed text-muted-foreground">
          <Quote className="mt-0.5 size-4 shrink-0 text-accent" />
          {stance}
        </p>
        <p className="mt-5 font-mono text-[11px] text-muted-foreground">
          initialized {new Date(livePersona.createdAt).toLocaleString()} · agentId {data.agentId}
        </p>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="surface-card p-5">
          <h3 className="mb-4 font-display text-base font-semibold">Voice rules</h3>
          <ul className="space-y-2.5">
                {voiceRules.map((r, i) => (
              <li
                key={r}
                className="flex gap-3 rounded-xl border border-[var(--surface-border)] p-3 text-sm"
              >
                <span className="font-mono text-xs text-accent">{String(i + 1).padStart(2, "0")}</span>
                {String(r)}
              </li>
            ))}
          </ul>
        </div>

        <div className="surface-card p-5"><h3 className="mb-4 font-display text-base font-semibold">Publishing behavior</h3><p className="text-sm text-muted-foreground">{intervalLabel}</p><p className="mt-2 text-sm text-muted-foreground">Observation period: {data.observationPeriodHours} hours</p><p className="mt-2 text-sm text-muted-foreground">Start mode: {data.startMode}{data.startAt ? ` · ${new Date(data.startAt).toLocaleString()}` : ""}</p><p className="mt-3 text-sm text-muted-foreground">Tone: {String(livePersona.voiceConfig.tone ?? "not specified")}</p></div>
      </section>

      <section className="surface-card p-5">
        <h3 className="mb-4 font-display text-base font-semibold">
          Published posts ({data.posts.length})
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[520px] text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-widest text-muted-foreground">
                <th className="pb-3 font-medium">Post</th>
                <th className="pb-3 font-medium">Voice</th>
                <th className="pb-3 font-medium">Domain</th>
                <th className="pb-3 font-medium">Belief conflict</th>
              </tr>
            </thead>
            <tbody>
              {data.posts.map((p) => (
                <tr key={p.id} className="border-t border-[var(--surface-border)]">
                  <td className="max-w-[280px] truncate py-3 pr-4">{p.text.split(/[.!?]\s/)[0] || p.id}</td>
                  <td className="py-3 font-mono text-xs">not recorded</td>
                  <td className="py-3 font-mono text-xs">{livePersona.domain}</td>
                  <td className="py-3">
                    <Badge
                      variant="secondary"
                      className={
                        p.relationship === "PREDICTION_RESOLUTION"
                          ? "bg-warning/15 text-warning"
                          : "bg-success/15 text-success"
                      }
                    >
                      {p.relationship === "PREDICTION_RESOLUTION" ? "stance revised" : "none"}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="surface-card p-5">
        <h3 className="mb-4 font-display text-base font-semibold">Persona history</h3>
        <div className="space-y-2">
          {agents.map((agent) => (
            <div key={agent.agentId} className={`flex flex-wrap items-center gap-3 rounded-xl border p-3 ${agent.agentId === data.agentId ? "border-primary/50 bg-secondary" : "border-[var(--surface-border)]"}`}>
              <div className="min-w-0 flex-1"><p className="font-medium">{agent.name}</p><p className="text-xs text-muted-foreground">{agent.domain} · {new Date(agent.createdAt).toLocaleString()}</p></div>
              <Badge variant="secondary">{agent.status}</Badge>
              <span className="font-mono text-[10px] text-muted-foreground">{agent.agentId}</span>
              <button type="button" onClick={() => openPersona(agent.agentId)} className="rounded-lg border border-[var(--surface-border)] px-2.5 py-1 text-xs hover:bg-secondary">
                View details
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
