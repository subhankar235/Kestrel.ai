"use client";

import { SignIn, useAuth, useUser } from "@clerk/nextjs";
import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { initAgent } from "@/lib/api-client";

export default function InitPage() {
  const { isSignedIn, isLoaded } = useUser();
  const { getToken } = useAuth();
  const router = useRouter();
  const [name, setName] = useState("Ada");
  const [domain, setDomain] = useState("AI Security");
  const [error, setError] = useState<string>();
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(undefined);

    try {
      const token = await getToken();
      if (!token) throw new Error("No authentication token available");

      const response = await initAgent({ name, domain }, token);
      window.localStorage.setItem("kestrel.agentId", response.agentId);
      router.push("/dashboard/feed");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Initialization failed");
    } finally {
      setSubmitting(false);
    }
  }

  if (!isLoaded) {
    return (
      <main className="flex-1">
        <div className="mx-auto max-w-md px-4 py-16">
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="flex-1">
      <div className="mx-auto max-w-md px-4 py-16">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-bold">Initialize Agent</h1>
          {isSignedIn && <UserButton />}
        </div>

        {!isSignedIn ? (
          <>
            <p className="mb-6 text-muted-foreground">Sign in to initialize the agent.</p>
            <SignIn />
          </>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <label className="block text-sm">
              Name
              <input
                required
                value={name}
                onChange={(event) => setName(event.target.value)}
                className="mt-1 w-full rounded-xl border border-[var(--surface-border)] bg-secondary px-3 py-2"
              />
            </label>
            <label className="block text-sm">
              Domain
              <input
                required
                value={domain}
                onChange={(event) => setDomain(event.target.value)}
                className="mt-1 w-full rounded-xl border border-[var(--surface-border)] bg-secondary px-3 py-2"
              />
            </label>
            {error ? <p className="text-sm text-destructive">{error}</p> : null}
            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-xl bg-primary px-4 py-2 font-medium text-primary-foreground disabled:opacity-50"
            >
              {submitting ? "Initializing..." : "Initialize Agent"}
            </button>
          </form>
        )}
      </div>
    </main>
  );
}
