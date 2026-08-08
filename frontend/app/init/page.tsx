"use client";

import { SignIn, useUser } from "@clerk/nextjs";
import { UserButton } from "@clerk/nextjs";

export default function InitPage() {
  const { isSignedIn, isLoaded } = useUser();

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
            <p className="text-muted-foreground mb-6">
              Sign in to trigger the one-time agent initialization.
            </p>
            <SignIn />
          </>
        ) : (
          <p className="text-muted-foreground">
            You are signed in. Agent initialization form coming soon.
          </p>
        )}
      </div>
    </main>
  );
}
