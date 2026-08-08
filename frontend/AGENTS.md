# AGENTS.md — Frontend (Next.js)

## Prompt Logging

Whenever the user gives you a prompt or instruction related to this frontend project, **append the exact raw user prompt to `PROMPTS.md`**.

Rules:

* Preserve the prompt exactly as written.
* Do not summarize, rewrite, or modify it.
* Append it to the end of `PROMPTS.md`.
* Never delete or modify previous prompts.
* If `PROMPTS.md` does not exist, create it.
* Do this automatically for every project-related user prompt.

Format:

```md
## Prompt

[RAW USER PROMPT]
```

## Tech Stack

- **Framework:** Next.js 15+ (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **UI Components:** shadcn/ui
- **Auth:** Clerk
- **State:** React hooks, no global state library
- **Package Manager:** npm (via Bun workspace)

## Coding Conventions

- Use App Router (`app/`), not Pages Router.
- Prefer Server Components by default; add `"use client"` only when needed.
- Use `@/*` import alias for absolute imports.
- Follow shadcn/ui patterns for new components.
- Keep API calls typed — import shared types from `packages/shared-types`.
- Use `fetch` with typed responses, not `axios`.

## File Structure

- `app/` — routes and pages
- `components/ui/` — reusable shadcn/ui primitives
- `components/feed/` — feed-specific components (post-card, rationale-panel, etc.)
- `components/persona/` — persona display components
- `lib/` — utility functions, API client, formatters
- `hooks/` — custom React hooks (e.g., `use-feed.ts`)
- `types/` — local type definitions (re-exported from `packages/shared-types`)
