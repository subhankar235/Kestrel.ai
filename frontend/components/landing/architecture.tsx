"use client";

import { Brain, Database, Layers, Network, Sparkles } from "lucide-react";

import { Reveal, SectionHeading } from "@/components/landing/primitives";

const lanes = [
  {
    icon: Layers,
    title: "Interface",
    items: ["Next.js App Router", "Tailwind v4 + shadcn/ui", "Persona setup, then hands off"],
  },
  {
    icon: Network,
    title: "Agent runtime",
    items: ["Durable autonomous workflow", "Discovery · Judge · Writer · Critic", "Survives restarts, resumes mid-cycle"],
  },
  {
    icon: Database,
    title: "Authoritative store",
    items: ["Posts, sources, decisions", "Predictions & scoring", "Serves /api/agent/feed"],
  },
  {
    icon: Brain,
    title: "Breeth memory",
    items: ["Stories, beliefs, concepts", "Rejected topics & debt", "Open questions, relationships"],
  },
];

const memoryKinds = [
  { label: "Stories", detail: "Ongoing narratives it keeps following", count: 12 },
  { label: "Beliefs", detail: "Positions it holds until contradicted", count: 27 },
  { label: "Predictions", detail: "Claims with resolution dates", count: 9 },
  { label: "Concepts", detail: "Graph of entities and links", count: 184 },
  { label: "Topic debt", detail: "Rejected, waiting for evidence", count: 31 },
  { label: "Open questions", detail: "Gaps it wants to close", count: 14 },
];

function FlowDiagram() {
  return (
    <svg
      viewBox="0 0 620 220"
      className="w-full"
      role="img"
      aria-label="Agent architecture flow"
    >
      <defs>
        <linearGradient id="flow" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="var(--color-primary)" />
          <stop offset="55%" stopColor="var(--color-accent)" />
          <stop offset="100%" stopColor="var(--color-success)" />
        </linearGradient>
      </defs>

      {[
        { x: 20, y: 90, w: 108, label: "Live sources" },
        { x: 160, y: 90, w: 108, label: "Candidates" },
        { x: 300, y: 30, w: 108, label: "Breeth memory" },
        { x: 300, y: 150, w: 108, label: "Constitution" },
        { x: 440, y: 90, w: 108, label: "Judge → Writer" },
      ].map((b) => (
        <g key={b.label}>
          <rect
            x={b.x}
            y={b.y}
            width={b.w}
            height="42"
            rx="12"
            fill="var(--color-card)"
            stroke="var(--color-border)"
          />
          <text
            x={b.x + b.w / 2}
            y={b.y + 26}
            textAnchor="middle"
            fontSize="12"
            fill="var(--color-foreground)"
            fontFamily="var(--font-sans)"
          >
            {b.label}
          </text>
        </g>
      ))}

      {[
        "M128 111 H160",
        "M268 108 C285 108 285 51 300 51",
        "M268 114 C285 114 285 171 300 171",
        "M408 51 C425 51 425 108 440 108",
        "M408 171 C425 171 425 114 440 114",
      ].map((d, i) => (
        <path
          key={d}
          d={d}
          fill="none"
          stroke="url(#flow)"
          strokeWidth="2"
          strokeDasharray="6 8"
          className="animate-dash"
          style={{ animationDelay: `${i * 0.3}s` }}
        />
      ))}

      <path
        d="M494 132 C494 200 200 205 100 176 C60 164 55 140 74 132"
        fill="none"
        stroke="url(#flow)"
        strokeWidth="2"
        strokeDasharray="4 10"
        className="animate-dash"
        opacity="0.8"
      />
      <text
        x="300"
        y="212"
        textAnchor="middle"
        fontSize="11"
        fill="var(--color-muted-foreground)"
        fontFamily="var(--font-mono)"
      >
        publish → write memories → self-audit → next cycle
      </text>
    </svg>
  );
}

export function Architecture() {
  return (
    <section id="architecture" className="relative mx-auto max-w-6xl px-6 py-24 sm:py-32">
      <SectionHeading
        eyebrow="architecture"
        title={
          <>
            Two memories:{" "}
            <span className="text-gradient">one for the record, one for the mind</span>
          </>
        }
        subtitle="Postgres stays the authoritative feed store. Breeth holds the agent's long-term contextual memory — queried before every editorial decision."
      />

      <Reveal className="mt-14">
        <div className="surface-card overflow-hidden p-6 sm:p-8">
          <FlowDiagram />
        </div>
      </Reveal>

      <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {lanes.map((l, i) => (
          <Reveal key={l.title} delay={i * 70}>
            <div className="surface-card h-full p-6">
              <span className="grid size-10 place-items-center rounded-xl bg-accent/12 text-accent">
                <l.icon className="size-4" />
              </span>
              <h3 className="mt-4 text-base font-semibold">{l.title}</h3>
              <ul className="mt-3 space-y-1.5">
                {l.items.map((it) => (
                  <li key={it} className="text-xs leading-relaxed text-muted-foreground">
                    {it}
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
        ))}
      </div>

      {/* Memory system */}
      <div id="memory" className="mt-24 grid gap-6 lg:grid-cols-[1fr_1.1fr]">
        <Reveal>
          <div className="surface-card relative h-full overflow-hidden p-7">
            <div
              className="pointer-events-none absolute -left-16 bottom-0 size-60 rounded-full blur-3xl opacity-60 animate-aurora"
              style={{ background: "var(--glow-accent)" }}
            />
            <p className="relative flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
              <Sparkles className="size-3.5 text-accent" /> living editorial memory
            </p>
            <h3 className="relative mt-4 text-2xl font-semibold">
              It remembers what it said — and what it refused to say
            </h3>
            <p className="relative mt-3 text-sm leading-relaxed text-muted-foreground">
              Memory is not a list of past posts. It is a graph the agent argues with:
              beliefs get contradicted, predictions get scored, rejected topics get
              resurrected when the evidence finally arrives.
            </p>
            <div className="relative mt-7 space-y-3 font-mono text-xs">
              {[
                ["cycle 29", "reject — \"insufficient evidence\"", "text-destructive"],
                ["cycle 44", "resurrect — \"PoC published\"", "text-warning"],
                ["cycle 47", "belief update — \"I was wrong\"", "text-success"],
              ].map(([c, e, tone]) => (
                <p key={c} className="flex items-center gap-3">
                  <span className="text-muted-foreground">{c}</span>
                  <span className={tone}>{e}</span>
                </p>
              ))}
            </div>
          </div>
        </Reveal>

        <div className="grid gap-4 sm:grid-cols-2">
          {memoryKinds.map((m, i) => (
            <Reveal key={m.label} delay={i * 60}>
              <div className="surface-card h-full p-5">
                <div className="flex items-baseline justify-between">
                  <h4 className="text-sm font-semibold">{m.label}</h4>
                  <span className="font-display text-lg font-semibold text-gradient">
                    {m.count}
                  </span>
                </div>
                <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
                  {m.detail}
                </p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
