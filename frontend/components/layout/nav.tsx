"use client";

import { Bot, Menu, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useUser } from "@clerk/nextjs";
import Link from "next/link";

import { ThemeToggle } from "@/components/layout/theme-toggle";

const links = [
  { href: "#feed", label: "Live Feed" },
  { href: "#loop", label: "The Loop" },
  { href: "#architecture", label: "Architecture" },
  { href: "#memory", label: "Memory" },
  { href: "#api", label: "API" },
];

export function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const { isSignedIn } = useUser();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header className="fixed inset-x-0 top-0 z-50 px-4 pt-4">
      <nav
        className={`mx-auto flex max-w-6xl items-center justify-between rounded-full px-4 py-2.5 transition-all duration-500 ${scrolled ? "glass shadow-[var(--shadow-card)]" : "border border-transparent"
          }`}
      >
        <a href="#top" className="flex items-center gap-2.5 pl-1">
          <span className="relative grid size-8 place-items-center rounded-xl bg-primary/15 text-primary">
            <Bot className="size-4" />
            <span className="absolute inset-0 rounded-xl border border-primary/40 animate-pulse-ring" />
          </span>
          <span className="font-display text-sm font-semibold tracking-tight">
            Kestrel<span className="text-muted-foreground">.agent</span>
          </span>
        </a>

        <div className="hidden items-center gap-1 md:flex">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="rounded-full px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
            >
              {l.label}
            </a>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Link
            href="/init"
            className="hidden rounded-full px-4 py-2 text-sm font-medium text-primary-foreground transition-transform hover:scale-[1.03] active:scale-95 sm:inline-flex"
            style={{ background: "var(--gradient-brand)" }}
          >
            {isSignedIn ? "Dashboard" : "Sign In"}
          </Link>
          <button
            type="button"
            aria-label="Toggle menu"
            onClick={() => setOpen((o) => !o)}
            className="grid size-10 place-items-center rounded-full glass md:hidden"
          >
            {open ? <X className="size-4" /> : <Menu className="size-4" />}
          </button>
        </div>
      </nav>

      {open ? (
        <div className="mx-auto mt-2 max-w-6xl rounded-3xl glass p-3 md:hidden">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              className="block rounded-2xl px-4 py-3 text-sm text-muted-foreground hover:bg-secondary hover:text-foreground"
            >
              {l.label}
            </a>
          ))}
          <Link
            href="/init"
            onClick={() => setOpen(false)}
            className="block rounded-2xl px-4 py-3 text-sm font-medium text-primary-foreground text-center mt-2"
            style={{ background: "var(--gradient-brand)" }}
          >
            {isSignedIn ? "Dashboard" : "Sign In"}
          </Link>
        </div>
      ) : null}
    </header>
  );
}
