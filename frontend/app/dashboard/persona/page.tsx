import { Quote } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { formatDate, persona, posts, stats } from "@/lib/mock-data";

export const metadata = {
  title: "Persona — Ada Agent Console",
  description:
    "Ada's persona card: domain focus, voice rules, stated beliefs and the consistency check every draft must pass.",
};

const voiceRules = [
  "Lead with the claim, not the context.",
  "Name the uncertainty explicitly — never round it away.",
  "Cite primary sources; secondary coverage only as corroboration.",
  "No exclamation marks, no growth-hacking cadence, no thread-bait.",
  "Admit being wrong in the same voice used to be confident.",
];

const beliefs = [
  { text: "Detection is not the bottleneck for prompt injection — capability scoping is.", conf: 0.88 },
  { text: "Artifact signing solves attribution, not safety.", conf: 0.84 },
  { text: "Efficiency features become security features once they cross tenants.", conf: 0.79 },
  { text: "Leaderboard movement is rarely evidence of anything.", conf: 0.91 },
];

export default function PersonaPage() {
  return (
    <div className="space-y-6 pb-12">
      <section className="surface-card noise-overlay relative overflow-hidden p-8">
        <div className="flex flex-wrap items-center gap-5">
          <span className="grid size-16 place-items-center rounded-3xl bg-gradient-to-br from-primary to-accent font-display text-2xl font-bold text-primary-foreground">
            A
          </span>
          <div>
            <h2 className="font-display text-2xl font-semibold">{persona.name}</h2>
            <p className="text-sm text-muted-foreground">{persona.domain}</p>
          </div>
          <div className="ml-auto flex flex-wrap gap-2">
            <Badge variant="secondary" className="bg-success/15 text-success">
              {persona.status.toLowerCase()}
            </Badge>
            <Badge variant="secondary" className="font-mono">
              {persona.constitutionVersion}
            </Badge>
          </div>
        </div>
        <p className="mt-6 flex max-w-2xl gap-3 text-sm leading-relaxed text-muted-foreground">
          <Quote className="mt-0.5 size-4 shrink-0 text-accent" />
          {persona.voice}
        </p>
        <p className="mt-5 font-mono text-[11px] text-muted-foreground">
          initialized {formatDate(persona.initializedAt)} UTC · agentId {persona.agentId} ·{" "}
          {stats.uptimeHours}h unattended
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
                {r}
              </li>
            ))}
          </ul>
        </div>

        <div className="surface-card p-5">
          <h3 className="mb-4 font-display text-base font-semibold">Stated beliefs</h3>
          <ul className="space-y-3">
            {beliefs.map((b) => (
              <li key={b.text} className="rounded-xl border border-[var(--surface-border)] p-4">
                <p className="text-sm">{b.text}</p>
                <p className="mt-2 font-mono text-[10px] text-muted-foreground">
                  confidence {b.conf.toFixed(2)}
                </p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="surface-card p-5">
        <h3 className="mb-4 font-display text-base font-semibold">
          Persona consistency checks (last {posts.length} drafts)
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
              {posts.map((p, i) => (
                <tr key={p.id} className="border-t border-[var(--surface-border)]">
                  <td className="max-w-[280px] truncate py-3 pr-4">{p.title}</td>
                  <td className="py-3 font-mono text-xs">{(0.88 + (i % 4) * 0.02).toFixed(2)}</td>
                  <td className="py-3 font-mono text-xs">{(0.9 + (i % 3) * 0.03).toFixed(2)}</td>
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
    </div>
  );
}
