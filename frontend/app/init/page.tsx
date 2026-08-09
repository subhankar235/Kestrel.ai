"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { initAgent } from "@/lib/api-client";

export default function InitPage() {
  const router = useRouter();
  const [name, setName] = useState("Ada");
  const [domain, setDomain] = useState("AI Security");
  const [voice, setVoice] = useState("Curious, analytical, evidence-first");
  const [publishIntervalMinutes, setPublishIntervalMinutes] = useState(240);
  const [observationPeriodHours, setObservationPeriodHours] = useState(48);
  const [startMode, setStartMode] = useState<"immediate" | "scheduled">("immediate");
  const [startAt, setStartAt] = useState("");
  const [error, setError] = useState<string>();
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(undefined);

    try {
      const response = await initAgent(
        { name, domain, voice },
        {
          publishIntervalMinutes,
          observationPeriodHours,
          startMode,
          ...(startMode === "scheduled" && startAt
            ? { startAt: new Date(startAt).toISOString() }
            : {}),
        },
      );
      window.localStorage.setItem("kestrel.agentId", response.agentId);
      router.push("/dashboard/feed");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Initialization failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="flex-1">
      <div className="mx-auto max-w-md px-4 py-16">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-bold">Initialize Agent</h1>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
            <label className="block text-sm">
              Persona Name
              <input
                required
                value={name}
                onChange={(event) => setName(event.target.value)}
                className="mt-1 w-full rounded-xl border border-[var(--surface-border)] bg-secondary px-3 py-2"
              />
            </label>
            <label className="block text-sm">
              What does this persona create about?
              <input
                required
                value={domain}
                onChange={(event) => setDomain(event.target.value)}
                className="mt-1 w-full rounded-xl border border-[var(--surface-border)] bg-secondary px-3 py-2"
              />
            </label>
            <label className="block text-sm">
              Personality / Voice
              <textarea
                required
                value={voice}
                onChange={(event) => setVoice(event.target.value)}
                rows={3}
                className="mt-1 w-full rounded-xl border border-[var(--surface-border)] bg-secondary px-3 py-2"
              />
            </label>
            <div className="border-t border-[var(--surface-border)] pt-5">
              <h2 className="mb-4 font-display text-sm font-semibold">Publishing Behavior</h2>
              <label className="block text-sm">
                Publishing Frequency
                <select
                  value={publishIntervalMinutes}
                  onChange={(event) => setPublishIntervalMinutes(Number(event.target.value))}
                  className="mt-1 w-full rounded-xl border border-[var(--surface-border)] bg-secondary px-3 py-2"
                >
                  <option value={1}>Every 1 minute</option>
                  <option value={3}>Every 3 minutes</option>
                  <option value={5}>Every 5 minutes</option>
                  <option value={10}>Every 10 minutes</option>
                  <option value={15}>Every 15 minutes</option>
                  <option value={30}>Every 30 minutes</option>
                  <option value={45}>Every 45 minutes</option>
                  <option value={60}>Every 1 hour</option>
                  <option value={120}>Every 2 hours</option>
                  <option value={180}>Every 3 hours</option>
                  <option value={240}>Every 4 hours</option>
                  <option value={360}>Every 6 hours</option>
                  <option value={720}>Every 12 hours</option>
                  <option value={1440}>Every 24 hours</option>
                </select>
              </label>
              <label className="mt-4 block text-sm">
                Observation Period (hours)
                <input
                  type="number"
                  min={1}
                  max={8760}
                  required
                  value={observationPeriodHours}
                  onChange={(event) => setObservationPeriodHours(Number(event.target.value))}
                  className="mt-1 w-full rounded-xl border border-[var(--surface-border)] bg-secondary px-3 py-2"
                />
              </label>
              <fieldset className="mt-4 space-y-2 text-sm">
                <legend className="mb-2">Start Publishing</legend>
                <label className="flex items-center gap-2"><input type="radio" checked={startMode === "immediate"} onChange={() => setStartMode("immediate")} /> Immediately</label>
                <label className="flex items-center gap-2"><input type="radio" checked={startMode === "scheduled"} onChange={() => setStartMode("scheduled")} /> At a specific time</label>
                {startMode === "scheduled" ? <input type="datetime-local" required value={startAt} onChange={(event) => setStartAt(event.target.value)} className="w-full rounded-xl border border-[var(--surface-border)] bg-secondary px-3 py-2" /> : null}
              </fieldset>
            </div>
            {error ? <p className="text-sm text-destructive">{error}</p> : null}
            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-xl bg-primary px-4 py-2 font-medium text-primary-foreground disabled:opacity-50"
            >
              {submitting ? "Initializing..." : "Initialize Agent"}
            </button>
        </form>
      </div>
    </main>
  );
}
