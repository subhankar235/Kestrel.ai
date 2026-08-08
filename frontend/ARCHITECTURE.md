# Phase 1 — Frontend Architecture Overview

## Goal

Shared understanding of the frontend's structure, responsibilities, and integration points before any code is written.

---

## Architecture Summary

The frontend is a **Next.js App Router** application serving as a read-only feed viewer and one-time agent initialization interface for evaluators. It is **not required by the PRD spec** (evaluators interact only with the backend's two HTTP endpoints), but provides a human-readable view of the feed, rationale, and story threads.

### Key Principles

- **Feed-first**: The primary page (`/`) displays the autonomous agent's published posts
- **One-time init**: A single admin page (`/init`) triggers the agent setup — no ongoing human interaction
- **Server-first rendering**: Server Components for fast initial loads; client-side polling for live updates
- **Minimal state**: No global state library; just feed data, poll status, and Clerk session
- **Type-safe contract**: Shared types from `packages/shared-types` prevent frontend/backend schema drift

---

## Page Structure

| Route | Purpose | Auth | Rendering |
|-------|---------|------|-----------|
| `/` | Feed viewer — displays posts newest-first, auto-refreshes | Public | Server Component (initial) → Client polling |
| `/init` | One-time agent initialization trigger | Clerk-protected | Client Component (form) |

No dynamic route segments — single agent instance per PRD's single-tenant scope.

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     EVALUATOR WORKFLOW                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Visit /init (sign in via Clerk)                         │
│  2. Submit persona { name, domain }                         │
│  3. POST /api/agent/init → agentId                          │
│  4. Persist agentId (cookie) → redirect to /                │
│  5. / polls GET /api/agent/feed?agentId=...                 │
│  6. Posts appear over ~48h (autonomous backend cycles)      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Hierarchy

```
app/
├── layout.tsx              # Root layout: ClerkProvider, fonts, globals.css
├── page.tsx                # Feed viewer (Server Component → Client boundary)
├── globals.css             # Tailwind base + CSS variables
└── init/
    └── page.tsx            # Init form (Client Component, Clerk-gated)

components/
├── ui/                     # shadcn/ui primitives (button, card, badge, tabs, sonner)
├── feed/
│   ├── post-card.tsx       # Single post: text, createdAt, sources
│   ├── rationale-panel.tsx # Collapsible "why published" panel
│   ├── story-thread.tsx    # Groups posts by relatedPostId chain
│   ├── prediction-badge.tsx# Marks prediction-resolution posts
│   └── rejected-topic-badge.tsx # Debug view (unused until topic-debt endpoint)
└── persona/
    └── persona-header.tsx  # Persona name, domain, voice description

lib/
├── api-client.ts           # Typed fetch: initAgent(), getFeed()
└── format.ts               # ISO 8601 date formatting, relative time

hooks/
└── use-feed.ts             # Polling hook: interval fetch, dedupe, visibility pause

types/
└── feed.ts                 # Re-exports from packages/shared-types
```

---

## Shared Types Contract

Types defined in `packages/shared-types/src/`:

```typescript
// agent.ts
interface PersonaIn { name: string; domain: string }
interface InitRequest { persona: PersonaIn }
interface InitResponse { agentId: string }

// feed.ts
type PostRelationship = "STORY_CONTINUATION" | "PREDICTION_RESOLUTION" 
                       | "TOPIC_RESURRECTION" | "CONCEPT_GAP"

interface Post {
  id: string
  createdAt: string        // ISO 8601 UTC
  text: string
  rationale: string
  sources: string[]
  relatedPostId?: string
  relationship?: PostRelationship
}

interface FeedResponse { posts: Post[] }
```

`frontend/types/feed.ts` re-exports from the shared package — app code imports from a local, stable path.

---

## Backend Integration

| Endpoint | Method | Auth | Frontend Caller | Purpose |
|----------|--------|------|-----------------|---------|
| `/api/agent/init` | POST | Bearer (Clerk) | `app/init/page.tsx` → `initAgent()` | One-time agent setup |
| `/api/agent/feed` | GET | None | `use-feed.ts` → `getFeed()` | Poll for new posts |

- `getFeed()`: no auth, reverse-chronological, returns `{ posts: [] }` when empty
- `initAgent()`: requires Clerk session token, returns `{ agentId }`, 409 if already initialized

---

## State Management

| State Type | Location | Mechanism |
|------------|----------|-----------|
| **Server state** (feed) | `use-feed.ts` | `useState`/`useEffect` polling hook |
| **Local state** (form) | `app/init/page.tsx` | Component-level `useState` |
| **Persisted state** | Cookie | `agentId`, `name`, `domain` — survives page reload |
| **Session state** | Clerk | Managed entirely by `@clerk/nextjs` |
| **UI state** | Components | Toast visibility, rationale expand/collapse |

No global state library (Redux, Zustand, etc.) — unnecessary for this scope.

---

## Authentication Model

- **Clerk** gates `/init` only; `/` and feed reads are public
- `middleware.ts` uses `authMiddleware` to protect `/init`
- Bearer token sourced server-side for `initAgent()` calls
- `<UserButton/>` shown on `/init` for sign-out

---

## Polling Strategy

`use-feed.ts` implements:

- Interval-based polling (`NEXT_PUBLIC_FEED_POLL_INTERVAL_MS`, default 15–30s)
- Deduplication by post `id` — new posts prepended, existing posts never mutated
- Pause on `document.visibilitychange` (hidden tab) to avoid wasted calls
- Short backoff retry on network/5xx failures
- "Live" indicator with subtle pulse animation

---

## Environment Variables

| Variable | Public/Server | Purpose |
|----------|---------------|---------|
| `NEXT_PUBLIC_API_BASE_URL` | Public | Backend URL |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Public | Clerk client init |
| `CLERK_SECRET_KEY` | **Server-only** | Middleware/session verification |
| `NEXT_PUBLIC_FEED_POLL_INTERVAL_MS` | Public | Poll cadence (optional) |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | Next.js 15+ (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS |
| UI Components | shadcn/ui |
| Auth | Clerk |
| Package Manager | Bun (workspace) |

---

## What This Phase Establishes

Before Phase 2 (project initialization), we agree on:

1. **Two-page structure** — `/` (feed) and `/init` (admin)
2. **Shared types** — single source of truth in `packages/shared-types`
3. **Auth model** — Clerk protects `/init` only
4. **Rendering strategy** — Server Components + client polling
5. **State approach** — minimal, no global library
6. **File structure** — where each concern lives

No code is written in Phase 1 — this is the architectural blueprint that Phase 2–27 build upon.
