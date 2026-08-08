import { SignIn } from "@clerk/nextjs";

export default function InitPage() {
  return (
    <main className="flex-1">
      <div className="mx-auto max-w-md px-4 py-16">
        <h1 className="text-2xl font-bold mb-2">Initialize Agent</h1>
        <p className="text-muted-foreground mb-8">
          Sign in to trigger the one-time agent initialization.
        </p>
        <SignIn />
      </div>
    </main>
  );
}
