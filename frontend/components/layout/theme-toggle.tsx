"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    queueMicrotask(() => setMounted(true));
  }, []);

  if (!mounted) {
    return (
      <button
        type="button"
        aria-label="Toggle theme"
        className="group relative grid size-10 place-items-center overflow-hidden rounded-full glass transition-transform hover:scale-105 active:scale-95"
      >
        <span
          className="absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
          style={{ background: "var(--gradient-brand)", filter: "blur(14px)" }}
        />
        <Moon className="absolute size-4 opacity-0" />
        <Sun className="absolute size-4 opacity-0" />
      </button>
    );
  }

  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className="group relative grid size-10 place-items-center overflow-hidden rounded-full glass transition-transform hover:scale-105 active:scale-95"
    >
      <span
        className="absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{ background: "var(--gradient-brand)", filter: "blur(14px)" }}
      />
      <Sun
        className={`absolute size-4 transition-all duration-500 ${
          isDark ? "rotate-90 scale-0 opacity-0" : "rotate-0 scale-100 opacity-100"
        }`}
      />
      <Moon
        className={`absolute size-4 transition-all duration-500 ${
          isDark ? "rotate-0 scale-100 opacity-100" : "-rotate-90 scale-0 opacity-0"
        }`}
      />
    </button>
  );
}
