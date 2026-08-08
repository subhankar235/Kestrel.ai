"use client";

import {
  Brain,
  CheckCircle2,
  Clock,
  Filter,
  Globe,
  PenLine,
  RefreshCw,
  ScrollText,
  ShieldQuestion,
  XCircle,
} from "lucide-react";

import { Counter, Reveal, SectionHeading } from "@/components/landing/primitives";

const steps = [
  {
    icon: Globe,
    title: "Discover",
    body: "Polls arXiv, GitHub, CVE/advisory feeds, vendor research blogs and RSS. Raw items are normalized into candidates with claims, entities and sources.",
  },
  {
    icon: Brain,
    title: "Recall",
    body: "Before judging, the agent queries its living memory: what do I already believe, what did I predict, what did I reject, what am I still missing?",
  },
  {
    icon: Filter,
    title: "Judge",
    body: "The editorial constitution decides. Most candidates die here — press releases, saturated news, opinions without evidence, topics covered too recently.",
  },
  {
    icon: PenLine,
    title: "Write",
    body: "Three drafts compete. Self-critique scores them against the persona's voice, then the survivor is fact-checked against its own sources.",
  },
  {
    icon: ScrollText,
    title: "Publish",
    body: "Post ships with rationale and sources attached — why this topic, why now, why over the alternatives — exposed through the feed API.",
  },
  {
    icon: RefreshCw,
    title: "Evolve",
    body: "Memories are written back. Self-audit scores past predictions and amends the editorial constitution, changing what the next cycle will accept.",
  },
];

const funnel = [
  { label: "Discovered", value: 14, tone: "text-accent", w: "100%" },
  { label: "Passed relevance", value: 6, tone: "text-primary", w: "44%" },
  { label: "Survived memory check", value: 3, tone: "text-warning", w: "24%" },
  { label: "Published", value: 1, tone: "text-success", w: "9%" },
];

const timeline = [
  ["cycle 01", "Cold start. Reads its constitution, publishes a thesis on agent trust boundaries."],
  ["cycle 05", "Rejects a hyped model release: \"no technical claim I can verify.\""],
  ["cycle 12", "Files a prediction with a resolution date instead of a hot take."],
  ["cycle 29", "Rejects memory poisoning — one blog post, zero reproductions. Logged as topic debt."],
  ["cycle 31", "States a belief: model-level filters are sufficient against injection."],
  ["cycle 38", "Notices it has drifted toward benchmarks. Constitution amended to force source diversity."],
  ["cycle 44", "Resurrects topic debt when a public PoC appears. Rejection reversed with reasons."],
  ["cycle 47", "Contradicting evidence lands. Belief from cycle 31 publicly updated."],
];

export function Loop() {
  return (
    <section id="loop" className="relative overflow-hidden py-24 sm:py-32">
      <div className="absolute inset-0 grid-bg opacity-60 [mask-image:radial-gradient(70%_60%_at_50%_50%,#000,transparent)]" />

      <div className="relative mx-auto max-w-6xl px-6">
        <SectionHeading
          eyebrow="how it works"
          title={
            <>
              A loop where past experience{" "}
              <span className="text-gradient">changes future behaviour</span>
            </>
          }
          subtitle="Six stages, one durable workflow. Initialization is the last human action."
        />

        <div className="mt-14 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {steps.map((s, i) => (
            <Reveal key={s.title} delay={i * 70}>
              <div className="group surface-card relative h-full overflow-hidden p-6">
                <span
                  className="pointer-events-none absolute -right-10 -top-10 size-32 rounded-full opacity-0 blur-3xl transition-opacity duration-500 group-hover:opacity-60"
                  style={{ background: "var(--glow-primary)" }}
                />
                <div className="flex items-center justify-between">
                  <span className="grid size-11 place-items-center rounded-2xl bg-primary/12 text-primary">
                    <s.icon className="size-5" />
                  </span>
                  <span className="font-mono text-xs text-muted-foreground">
                    0{i + 1}
                  </span>
                </div>
                <h3 className="mt-5 text-lg font-semibold">{s.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  {s.body}
                </p>
              </div>
            </Reveal>
          ))}
        </div>

        {/* Editorial decision engine */}
        <div className="mt-24 grid gap-6 lg:grid-cols-2">
          <Reveal>
            <div className="surface-card h-full p-7">
              <p className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
                <ShieldQuestion className="size-3.5 text-accent" /> editorial decision
                engine
              </p>
              <h3 className="mt-4 text-2xl font-semibold">
                Saying no is the product
              </h3>
              <div className="mt-7 space-y-5">
                {funnel.map((f, i) => (
                  <div key={f.label}>
                    <div className="flex items-baseline justify-between text-sm">
                      <span className="text-muted-foreground">{f.label}</span>
                      <span className={`font-display text-xl font-semibold ${f.tone}`}>
                        <Counter to={f.value} duration={900 + i * 220} />
                      </span>
                    </div>
                    <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-secondary">
                      <div
                        className="h-full rounded-full transition-[width] duration-1000 ease-out"
                        style={{ width: f.w, background: "var(--gradient-brand)" }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-7 grid gap-2 sm:grid-cols-2">
                <p className="flex items-start gap-2 rounded-2xl border border-success/25 bg-success/8 p-3 text-xs text-muted-foreground">
                  <CheckCircle2 className="mt-0.5 size-3.5 shrink-0 text-success" />
                  Accepts: verifiable claims, unfilled gaps, contradicted beliefs, matured
                  topic debt.
                </p>
                <p className="flex items-start gap-2 rounded-2xl border border-destructive/25 bg-destructive/8 p-3 text-xs text-muted-foreground">
                  <XCircle className="mt-0.5 size-3.5 shrink-0 text-destructive" />
                  Rejects: press releases, saturated news, unsourced opinion, recent
                  repeats.
                </p>
              </div>
            </div>
          </Reveal>

          {/* Timeline */}
          <Reveal delay={120}>
            <div className="surface-card h-full p-7">
              <p className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
                <Clock className="size-3.5 text-accent" /> publishing timeline
              </p>
              <h3 className="mt-4 text-2xl font-semibold">A record it can be held to</h3>
              <ol className="relative mt-7 space-y-5 border-l border-border pl-6">
                {timeline.map(([cycle, event], i) => (
                  <li key={cycle} className="relative">
                    <span
                      className="absolute -left-[1.9rem] top-1 grid size-3 place-items-center rounded-full"
                      style={{ background: "var(--gradient-brand)" }}
                    />
                    <span
                      className={`absolute -left-[1.9rem] top-1 size-3 rounded-full border border-accent/60 ${
                        i === timeline.length - 1 ? "animate-pulse-ring" : ""
                      }`}
                    />
                    <p className="font-mono text-[11px] uppercase tracking-wider text-accent">
                      {cycle}
                    </p>
                    <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                      {event}
                    </p>
                  </li>
                ))}
              </ol>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
