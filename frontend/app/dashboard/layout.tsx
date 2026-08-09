"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BookOpen,
  Brain,
  Gauge,
  Newspaper,
  Radar,
  ScrollText,
  Scale,
} from "lucide-react";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { useDashboard } from "@/hooks/use-dashboard";

const nav = [
  { href: "/dashboard", label: "Overview", icon: Gauge, exact: true },
  { href: "/dashboard/feed", label: "Feed", icon: Newspaper },
  { href: "/dashboard/memory", label: "Memory", icon: Brain },
  { href: "/dashboard/decisions", label: "Decisions", icon: Scale },
  { href: "/dashboard/cycles", label: "Cycles", icon: Activity },
  { href: "/dashboard/constitution", label: "Constitution", icon: ScrollText },
  { href: "/dashboard/sources", label: "Sources", icon: Radar },
  { href: "/dashboard/persona", label: "Persona", icon: BookOpen },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { data } = useDashboard();
  const persona = data?.persona;

  function isActive(href: string, exact?: boolean) {
    if (exact) return pathname === href;
    return pathname.startsWith(href);
  }

  return (
    <div className="relative min-h-screen">
      <div className="pointer-events-none fixed inset-0 grid-bg opacity-70" aria-hidden />
      <div className="pointer-events-none fixed inset-x-0 top-0 h-[420px] [background:var(--gradient-hero)]" aria-hidden />

      <div className="relative mx-auto flex w-full max-w-[1500px] gap-6 px-4 py-6 lg:px-8">
        <aside className="sticky top-6 hidden h-[calc(100vh-3rem)] w-60 shrink-0 flex-col rounded-3xl glass p-4 lg:flex">
          <Link href="/dashboard" className="mb-6 flex items-center gap-3 px-2">
            <span className="grid size-9 place-items-center rounded-xl bg-gradient-to-br from-primary to-accent text-sm font-bold text-primary-foreground">
              A
            </span>
            <span className="leading-tight">
               <span className="block font-display text-sm font-semibold">{persona?.name || "Agent"}</span>
              <span className="block text-[11px] text-muted-foreground">Autonomous agent</span>
            </span>
          </Link>

          <nav className="flex flex-1 flex-col gap-1">
            {nav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`group flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition-colors ${
                  isActive(item.href, item.exact)
                    ? "bg-secondary text-foreground"
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                }`}
              >
                <item.icon className="size-4" />
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="rounded-2xl border border-[var(--surface-border)] p-3 text-xs text-muted-foreground">
            <div className="mb-1 flex items-center gap-2 text-foreground">
              <span className="relative flex size-2">
                <span className="absolute inline-flex size-2 animate-pulse-ring rounded-full bg-success" />
                <span className="relative inline-flex size-2 rounded-full bg-success" />
              </span>
              <span className="font-medium">Running autonomously</span>
            </div>
               {data?.cycle?.nextRunTime ? `Next cycle ${data.cycle.nextRunTime}` : "Scheduler status unavailable"}
          </div>
        </aside>

        <main className="min-w-0 flex-1">
          <header className="mb-6 flex flex-wrap items-center gap-3 rounded-2xl glass px-4 py-3">
            <div className="min-w-0 flex-1">
              <h1 className="truncate font-display text-lg font-semibold">
                {persona?.name || "Agent"} <span className="text-muted-foreground">·</span>{" "}
                <span className="text-gradient">{persona?.domain || "Loading"}</span>
              </h1>
              <p className="truncate text-xs text-muted-foreground">
                agentId {data?.agentId || "Loading"} · constitution {data?.constitution?.version || "Unavailable"}
              </p>
            </div>
            <nav className="flex gap-1 overflow-x-auto lg:hidden">
              {nav.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`rounded-lg px-2.5 py-1.5 text-xs ${
                    isActive(item.href, item.exact)
                      ? "bg-secondary text-foreground"
                      : "text-muted-foreground"
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
            <ThemeToggle />
          </header>

          {children}
        </main>
      </div>
    </div>
  );
}
