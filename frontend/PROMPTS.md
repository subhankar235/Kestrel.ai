# PROMPTS.md — Frontend (Next.js)

> All frontend-related prompts are logged here.
> At project end, merge into root `PROMPTS.md`.

## Prompt

i am sing bun for frotend

checl how to sart the fortend

You are a frontend agent You have to do all frontend work of this project first explore a little about this project then just complete the phase 1 of this project, all the context in C:\Users\soumo\OneDrive\Desktop\Kestrel.ai\docs also remember through the session you have follow @frontend/AGENTS.md

## Prompt

Ok after phase 1 now you have to start phase 2 of this project, Frontend Project Initialization complete it carefully

## Prompt

Move globals.css to a styles folder and update any required imports

## Prompt

Now start Phase 3 (Framework and Dependency Setup). Complete it carefully.

## Prompt

Complete Phase 4 (Environment / Configuration Setup).

## Prompt

Begin Phase 6 — Set up the root layout with ClerkProvider, create the feed viewer page at `/`, and the gated init page at `/init`.

## Prompt

Start Phase 7 — Set up Clerk authentication using `proxy.ts` (Next.js 16) instead of `middleware.ts` to protect the `/init` route while keeping `/` public.

## Prompt

Start Phase 8 — Create a typed API client (`lib/api-client.ts`) with functions for `initAgent` (POST, authenticated) and `getFeed` (GET, public), including error handling and shared type exports.

## Prompt

Complete Phase 9 — Create the `packages/shared-types` package with `Post`, `FeedResponse`, `InitRequest`, and `InitResponse` types, then re-export them from `frontend/types/feed.ts` for zero-drift frontend-backend contract.

## Prompt

Complete Phase 10 — Create a `useFeed` hook (`hooks/use-feed.ts`) that manages feed polling with interval-based fetching, deduplication, and tab visibility handling.

## Prompt

Complete Phase 11 — Build feed components (`post-card`, `rationale-panel`, `story-thread`, `prediction-badge`, `rejected-topic-badge`) and the `persona-header` component.
