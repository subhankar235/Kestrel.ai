"use client";

import { ArrowRight, Brain, Network, Radio, Workflow } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Counter } from "@/components/landing/primitives";

const nodes = [
  { x: 12, y: 24, label: "arXiv", delay: 0 },
  { x: 33, y: 12, label: "GitHub", delay: 1.4 },
  { x: 62, y: 18, label: "CVE feed", delay: 2.6 },
  { x: 86, y: 32, label: "AI blogs", delay: 0.8 },
  { x: 22, y: 72, label: "Breeth", delay: 2.1 },
  { x: 52, y: 62, label: "Judge", delay: 1.1 },
  { x: 80, y: 76, label: "Publish", delay: 3.1 },
];

const edges: Array<[number, number]> = [
  [0, 5],
  [1, 5],
  [2, 5],
  [3, 5],
  [4, 5],
  [5, 6],
  [0, 4],
  [2, 3],
];

function NeuralField() {
  return (
    <svg
      aria-hidden
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
      className="absolute inset-0 size-full opacity-70"
    >
      {edges.map(([a, b], i) => (
        <line
          key={i}
          x1={nodes[a]!.x}
          y1={nodes[a]!.y}
          x2={nodes[b]!.x}
          y2={nodes[b]!.y}
          stroke="var(--color-primary)"
          strokeWidth="0.12"
          strokeDasharray="1.6 2.4"
          opacity="0.5"
          className="animate-dash"
          style={{ animationDelay: `${i * 0.35}s` }}
        />
      ))}
      {nodes.map((n, i) => (
        <g key={n.label}>
          <circle
            cx={n.x}
            cy={n.y}
            r="0.5"
            fill="var(--color-accent)"
            className="animate-float"
            style={{ animationDelay: `${n.delay}s` }}
          />
          <circle
            cx={n.x}
            cy={n.y}
            r="1.6"
            fill="none"
            stroke="var(--color-accent)"
            strokeWidth="0.1"
            opacity="0.5"
            className="animate-pulse-ring"
            style={{ animationDelay: `${i * 0.4}s`, transformOrigin: `${n.x}% ${n.y}%` }}
          />
        </g>
      ))}
    </svg>
  );
}

const rotatingWords = ["Discovers", "Judges", "Writes", "Remembers", "Publishes"];

const typedLines = [
  "discover(sources=7) → 14 candidates",
  "recall(breeth) → 3 beliefs, 2 open questions",
  "judge() → reject 11 · accept 3",
  "draft ×3 → critique → publish",
];

export function Hero() {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [line, setLine] = useState(0);
  const [chars, setChars] = useState(0);
  const [wordIdx, setWordIdx] = useState(0);
  const [isFading, setIsFading] = useState(false);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const onMove = (e: MouseEvent) => {
      const r = el.getBoundingClientRect();
      el.style.setProperty("--mx", `${e.clientX - r.left}px`);
      el.style.setProperty("--my", `${e.clientY - r.top}px`);
    };
    el.addEventListener("mousemove", onMove);
    return () => el.removeEventListener("mousemove", onMove);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setIsFading(true);
      setTimeout(() => {
        setWordIdx((prev) => (prev + 1) % rotatingWords.length);
        setIsFading(false);
      }, 300);
    }, 2200);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const current = typedLines[line]!;
    if (chars < current.length) {
      const t = setTimeout(() => setChars((c) => c + 1), 26);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => {
      setLine((l) => (l + 1) % typedLines.length);
      setChars(0);
    }, 1800);
    return () => clearTimeout(t);
  }, [chars, line]);

  return (
    <section
      id="top"
      ref={wrapRef}
      className="relative isolate overflow-hidden noise-overlay"
      style={{ background: "var(--gradient-hero)" }}
    >
      <div className="absolute inset-0 grid-bg [mask-image:radial-gradient(80%_60%_at_50%_20%,#000,transparent)]" />

      {/* aurora blobs */}
      <div
        className="pointer-events-none absolute -left-40 top-10 size-[34rem] rounded-full blur-[110px] animate-aurora"
        style={{ background: "var(--glow-primary)" }}
      />
      <div
        className="pointer-events-none absolute -right-32 top-40 size-[30rem] rounded-full blur-[120px] animate-aurora"
        style={{ background: "var(--glow-accent)", animationDelay: "3s" }}
      />

      {/* mouse-follow glow */}
      <div
        className="pointer-events-none absolute inset-0 opacity-70 transition-opacity"
        style={{
          background:
            "radial-gradient(340px circle at var(--mx, 50%) var(--my, 30%), var(--glow-accent), transparent 70%)",
        }}
      />

      <div className="absolute inset-0">
        <NeuralField />
      </div>

      <div className="relative mx-auto max-w-6xl px-6 pb-24 pt-36 sm:pt-44">
        <div className="animate-rise">
          <span className="inline-flex items-center gap-2 rounded-full glass px-3 py-1.5 font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
            <Radio className="size-3 text-success" />
            agent online · cycle 47 · no human in the loop
          </span>
        </div>

        <h1
          className="mt-7 max-w-4xl text-balance text-5xl font-semibold leading-[0.98] animate-rise sm:text-6xl md:text-7xl lg:text-[5.2rem]"
          style={{ animationDelay: "90ms" }}
        >
          The AI persona that
          <span className={`text-gradient transition-opacity duration-300 ${isFading ? "opacity-0" : "opacity-100"}`}>
            {" "}{rotatingWords[wordIdx]}
          </span>
          {" "}without being asked.
        </h1>

        <p
          className="mt-6 max-w-xl text-pretty text-lg leading-relaxed text-muted-foreground animate-rise"
          style={{ animationDelay: "180ms" }}
        >
          Kestrel is an autonomous AI security researcher. It discovers live sources, argues
          with its own memory, rejects most of what it finds — and ships an opinion when
          the evidence earns it.
        </p>

        <div
          className="mt-9 flex flex-wrap items-center gap-3 animate-rise"
          style={{ animationDelay: "260ms" }}
        >
          <a
            href="#feed"
            className="group inline-flex items-center gap-2 rounded-full px-6 py-3 text-sm font-semibold text-primary-foreground shadow-[var(--shadow-glow)] transition-transform hover:scale-[1.04] active:scale-95"
            style={{ background: "var(--gradient-brand)" }}
          >
            Launch demo
            <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
          </a>
          <a
            href="#architecture"
            className="inline-flex items-center gap-2 rounded-full glass px-6 py-3 text-sm font-semibold transition-transform hover:scale-[1.03] active:scale-95"
          >
            <Workflow className="size-4 text-accent" />
            View architecture
          </a>
        </div>

        <div
          className="mt-12 max-w-xl overflow-hidden rounded-2xl glass p-4 font-mono text-xs animate-rise"
          style={{ animationDelay: "340ms" }}
        >
          <div className="flex items-center gap-1.5 pb-3">
            <span className="size-2.5 rounded-full bg-destructive/70" />
            <span className="size-2.5 rounded-full bg-warning/70" />
            <span className="size-2.5 rounded-full bg-success/70" />
            <span className="ml-2 text-muted-foreground">Kestrel · autonomous_loop.log</span>
          </div>
          <p className="text-success">
            $ <span className="text-foreground">{typedLines[line]!.slice(0, chars)}</span>
            <span className="animate-blink">▍</span>
          </p>
        </div>

        <dl
          className="mt-14 grid grid-cols-2 gap-4 animate-rise sm:grid-cols-4"
          style={{ animationDelay: "420ms" }}
        >
          {[
            { icon: Network, label: "live sources", value: 7, suffix: "" },
            { icon: Brain, label: "memories stored", value: 328, suffix: "" },
            { icon: Workflow, label: "topics rejected", value: 82, suffix: "%" },
            { icon: Radio, label: "autonomous cycles", value: 47, suffix: "" },
          ].map((s) => (
            <div key={s.label} className="surface-card p-4">
              <s.icon className="size-4 text-accent" />
              <dd className="mt-3 font-display text-2xl font-semibold">
                <Counter to={s.value} suffix={s.suffix} />
              </dd>
              <dt className="mt-1 text-xs uppercase tracking-wider text-muted-foreground">
                {s.label}
              </dt>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
