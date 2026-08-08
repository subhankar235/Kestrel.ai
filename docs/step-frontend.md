# FRONTEND_STEPS.md — Autonomous AI Creator Agent
### Complete Frontend Implementation Playbook (Zero → Production)

This document is the sequential build guide for `frontend/` as defined in `PRD.md`, `TECH_STACK.md`, and `frontend/STRUCTURE.md`. Follow phases in order.

Stack in use: **Next.js (App Router), TypeScript, Tailwind CSS, shadcn/ui, Bun.**

**Scope reminder from the PRD:** the frontend is *not required by the spec* — evaluators interact only with the backend's two HTTP endpoints. Its job is to give evaluators/humans a readable view of the feed, rationale, and story threads, plus a convenience UI to trigger the one-time init call. There is no end-user chat/command interface and no streaming requirement — the agent is autonomous and produces posts on a schedule that the frontend polls for, it does not converse with the user. Sections below that don't apply for this reason (e.g. "AI/agent chat UI", "Streaming/real-time UI") are marked **N/A** with the reason stated, per PRD scope.

---

## Phase 1 — Frontend Architecture Overview

**Goal:** Shared understanding before coding starts.

**Architecture summary:**
- Next.js App Router app with two real pages: `/` (feed viewer, polls `GET /api/agent/feed`) and `/init` (gated one-time trigger for `POST /api/agent/init`).
- `packages/shared-types` is the source of truth for `Post`, `FeedResponse`, `InitRequest`/`InitResponse` — the frontend's `types/feed.ts` re-exports from it so the UI can never drift from the backend contract.
- Clerk protects `/init` only; the feed view is public, matching the backend's auth model (Phase 10 of `BACKEND_STEPS.md`).
- Server Components render the initial feed for fast loads; a client-side polling hook (`use-feed.ts`) keeps it updated live during the 48h evaluation window without page reloads.
- No client-side app state beyond feed data, poll status, and Clerk session — no global client state library is introduced (unnecessary for this scope).

**Expected result:** Agreement on the two-page, mostly-server-rendered structure before Phase 2.

---

## Phase 2 — Frontend Project Initialization

**Goal:** Empty, runnable Next.js app scaffold matching `frontend/STRUCTURE.md`.

**Prerequisites:** Bun installed; `frontend/` folder exists in the monorepo; root `package.json` declares the Bun workspace (`frontend`, `packages/*`).

**Files/folders to create:**
```
frontend/
├── app/layout.tsx
├── app/page.tsx
├── app/globals.css
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── .env.example
```

**Implementation:** `bunx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir`, then reconcile the generated tree with `frontend/STRUCTURE.md` (remove anything the scaffolder adds that isn't in the spec, e.g. default sample pages). Add `frontend` to the root `package.json` workspaces array if not already present.

**Verification:** `bun install && bun run dev` from `frontend/` serves the default page at `localhost:3000`.

**Expected result:** A blank but building Next.js app inside the Bun workspace.

---

## Phase 3 — Framework and Dependency Setup

**Goal:** Install every library the tech stack calls for.

**Prerequisites:** Phase 2 complete.

**Dependencies (add via `bun add`):**
```
next react react-dom typescript                 # framework (from scaffold)
tailwindcss postcss autoprefixer                 # styling (from scaffold)
@clerk/nextjs                                    # auth for /init
clsx tailwind-merge                              # class-name utilities used by shadcn/ui
class-variance-authority                          # shadcn/ui component variants
lucide-react                                      # icon set used by shadcn/ui components
```
Dev dependencies:
```
@types/react @types/node
eslint eslint-config-next
prettier
vitest @testing-library/react @testing-library/jest-dom  # unit/component tests (Phase 22)
@playwright/test                                   # e2e tests (Phase 24)
```

**Implementation:** Initialize shadcn/ui with `bunx shadcn@latest init`, selecting the design tokens/paths matching `components/ui/`. This generates `components.json` and wires Tailwind's `tailwind.config.ts` theme extension.

**Verification:** `bun run build` completes with no missing-module errors.

---

## Phase 4 — Environment / Configuration Setup

**Goal:** Define every frontend env var, clearly split public vs. server-only.

**Files:** `frontend/.env.example`

**Configuration:**

| Variable | Public/Server | Purpose | Required |
|---|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Public | Base URL of the FastAPI backend (`/api/agent/init`, `/api/agent/feed`) | Required |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Public | Clerk client SDK init | Required |
| `CLERK_SECRET_KEY` | **Server-only** | Used only inside Next.js server context (middleware/route handlers) to verify sessions server-side — never sent to the browser | Required |
| `NEXT_PUBLIC_FEED_POLL_INTERVAL_MS` | Public | Polling cadence for `use-feed.ts` (e.g. `15000`) | Optional (default in code) |

**Security:** Only variables prefixed `NEXT_PUBLIC_` are ever exposed to the browser bundle. `CLERK_SECRET_KEY` must never be prefixed `NEXT_PUBLIC_` and is only referenced from `middleware.ts` (server runtime). No OpenAI/Breeth/Exa/Tavily/Postgres/Temporal secrets ever appear in `frontend/` — those are backend-only per `BACKEND_STEPS.md`.

**Where to obtain keys:** `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` / `CLERK_SECRET_KEY` from the Clerk dashboard → API Keys (same Clerk application as the backend, so sessions are shared). `NEXT_PUBLIC_API_BASE_URL` is the deployed backend's URL (Railway/Fly/Render host from `infra/`).

**Verification:** `frontend/.env.example` lists all four vars with placeholder values and a comment marking `CLERK_SECRET_KEY` as server-only.

---

## Phase 5 — Global Styles / Theme / Design System

**Goal:** Establish the visual language before building components.

**Files:** `frontend/app/globals.css`, `frontend/tailwind.config.ts`, `frontend/components.json`

**Implementation:** Define the Tailwind theme extension (colors, spacing, font family) reflecting the persona/editorial tone of the product — a calm, editorial/reading-focused palette (the product is a content feed, not a dashboard). Import a readable serif or humanist sans font for post `text` and a monospace/label font for metadata (timestamps, source domains, badges). Configure `globals.css` with Tailwind's `@tailwind base/components/utilities` layers plus CSS variables shadcn/ui expects (`--background`, `--foreground`, `--card`, `--muted`, etc.) in both light and dark values.

**UI behavior:** Support light/dark via `prefers-color-scheme` at minimum (no manual toggle required by the PRD — skip building one unless time allows, since it's not a PRD requirement).

**Accessibility:** Confirm text/background color pairs meet WCAG AA contrast in both themes before building components on top of them.

**Verification:** A static Tailwind test div using theme tokens renders correctly in both light and dark OS settings.

---

## Phase 6 — Application Layout and Routing

**Goal:** Root layout and the two-route structure.

**Prerequisites:** Phase 5.

**Files:** `frontend/app/layout.tsx`, `frontend/app/page.tsx`, `frontend/app/init/page.tsx`

**Implementation:**
- `layout.tsx`: root HTML shell, imports `globals.css`, sets fonts, wraps children in `<ClerkProvider>` (needed since `/init` uses Clerk, and the provider must wrap the whole tree per Clerk's Next.js integration), renders `persona-header` (Phase 11) at the top of every page once persona data exists.
- `app/page.tsx` (`/`): the feed viewer route — server component that does an initial server-side fetch of the feed (Phase 8) for fast first paint, then hands off to the client polling hook.
- `app/init/page.tsx` (`/init`): the gated demo page for the one-time `POST /api/agent/init` call.

**UI behavior:** `/` is the default landing route (feed-first product); `/init` is a secondary, clearly-labeled "Admin / Setup" route, not linked prominently from the main feed nav (it's a one-time action).

**Routing:** No dynamic route segments are needed (single agent instance per the PRD's single-tenant scope) — avoid inventing `/agent/[id]` routes not required by the spec.

**Testing:** route smoke test confirming both `/` and `/init` render without throwing.

**Verification:** `bun run dev`, navigate to both routes manually, confirm layout/header renders on each.

---

## Phase 7 — Authentication and Session Handling

**Goal:** Gate `/init` behind Clerk; leave `/` public.

**Prerequisites:** Phase 4 (Clerk keys), Phase 6 (routes exist).

**Files:** `frontend/middleware.ts`

**Implementation:** Use `@clerk/nextjs`'s `authMiddleware` (or `clerkMiddleware` depending on SDK version) configured so `/init` requires a signed-in session and `/` (and its API-consuming children) is public. Unauthenticated visits to `/init` redirect to Clerk's hosted sign-in (or an embedded `<SignIn/>` component rendered inline on `/init` itself — simpler for a single-admin-action page, avoids building a full auth UI).

**Authentication:**
- **Login:** Clerk's prebuilt `<SignIn/>` component embedded on `/init`, no custom login form built (avoids unnecessary UI work not required by the PRD).
- **Session:** Clerk manages session cookies/JWT automatically; the frontend obtains the session token via `auth()`/`getToken()` server-side when calling the backend's `POST /api/agent/init` (Phase 8) so the `Authorization: Bearer <token>` header matches what `BACKEND_STEPS.md` Phase 10 expects.
- **Protected routes:** only `/init`; `/` and the feed data are intentionally public, matching the backend's unauthenticated `GET /api/agent/feed`.
- **Logout:** Clerk's `<UserButton/>` (sign-out built in) shown only on `/init` when signed in.

**Security:** Never read `CLERK_SECRET_KEY` in any Client Component — only in `middleware.ts`/server route handlers. Never store the bearer token in `localStorage`; rely on Clerk's own secure session handling and fetch tokens on demand server-side.

**Testing:** integration test asserting an unauthenticated request to `/init` is redirected/shown the sign-in component instead of the init form.

**Verification:** visiting `/init` while signed out shows sign-in; signing in reveals the init form (Phase 13).

---

## Phase 8 — API Client / Backend Communication Layer

**Goal:** One typed client wrapping both backend endpoints.

**Prerequisites:** Phase 4 (`NEXT_PUBLIC_API_BASE_URL`), Phase 9 (types, built alongside).

**Files:** `frontend/lib/api-client.ts`

**Backend integration:**

| Call | Endpoint | Method | Auth | Input | Response | Frontend behavior |
|---|---|---|---|---|---|---|
| `initAgent(persona)` | `${NEXT_PUBLIC_API_BASE_URL}/api/agent/init` | POST | `Authorization: Bearer <Clerk token>` | `{persona: {name, domain}}` | `{agentId}` on 200; `401`/`409`/`400` errors | Called once from `/init`'s form submit; on success, persist `agentId` (Phase 10) and redirect to `/` |
| `getFeed(agentId)` | `${NEXT_PUBLIC_API_BASE_URL}/api/agent/feed?agentId=...` | GET | none | — | `{posts: Post[]}`; `404` if unknown agentId | Called on initial server render of `/` and repeatedly by `use-feed.ts` (Phase 16) |

**Implementation:** `api-client.ts` exports `initAgent()` and `getFeed()` using `fetch` with `next: {revalidate: 0}` (or `cache: 'no-store'`) for the feed call so evaluators always see fresh data; typed with `InitRequest`/`InitResponse`/`FeedResponse` from `types/feed.ts`. Centralize error handling: non-2xx responses throw a typed `ApiError{status, message}` that calling code catches to drive UI error states (Phase 17).

**Errors/retries:** `getFeed` failures (network error, 5xx) are retried with a short backoff (e.g. 2 attempts) inside `use-feed.ts`, not inside `api-client.ts` itself — keep the client a thin, retry-agnostic wrapper; retry policy lives in the hook that owns polling.

**Testing:** unit tests mocking `fetch` and asserting `initAgent`/`getFeed` build the correct URL, headers, and body, and correctly throw `ApiError` on non-2xx.

**Verification:** call `getFeed()` against a running backend from a Node script and confirm the shape matches `FeedResponse`.

---

## Phase 9 — Shared Types / Interfaces

**Goal:** Zero-drift contract with the backend.

**Files:** `frontend/types/feed.ts` (re-exports), `packages/shared-types/src/{agent.ts, feed.ts, index.ts}`

**Implementation:** `packages/shared-types` defines:
```ts
// agent.ts
export interface PersonaIn { name: string; domain: string }
export interface InitRequest { persona: PersonaIn }
export interface InitResponse { agentId: string }

// feed.ts
export type PostRelationship = "STORY_CONTINUATION" | "PREDICTION_RESOLUTION" | "TOPIC_RESURRECTION" | "CONCEPT_GAP";
export interface Post {
  id: string;
  createdAt: string;       // ISO 8601 UTC
  text: string;
  rationale: string;
  sources: string[];
  relatedPostId?: string;
  relationship?: PostRelationship;
}
export interface FeedResponse { posts: Post[] }
```
`frontend/types/feed.ts` does `export * from "shared-types"` (via the Bun workspace package reference) so app code imports from a local, stable path.

**Naming consistency:** field names (`agentId`, `createdAt`, `rationale`, `sources`, `relatedPostId`, `relationship`) match the backend's Pydantic schemas exactly (`BACKEND_STEPS.md` Phase 13) — no renaming/mapping layer needed.

**Testing:** a type-only test (`tsd` or a compile-time assertion file) ensuring `Post` has no drift if `packages/shared-types` changes.

**Verification:** `tsc --noEmit` passes across `frontend/` and `packages/shared-types`.

---

## Phase 10 — Global State Management

**Goal:** Define what state exists and where — deliberately minimal.

**State management breakdown:**
- **Server state:** the feed (`Post[]`) — fetched via `getFeed()`, owned by `use-feed.ts` (Phase 16), not duplicated into a global store. No React Query/Redux/Zustand is introduced; a single custom hook with `useState`/`useEffect` is sufficient for one polled endpoint (avoids unnecessary technology per project constraints).
- **Local/component state:** `/init` form fields (`name`, `domain`), submit-in-progress flag, submit error — local `useState` inside `app/init/page.tsx`'s client form component only.
- **Persisted state:** the `agentId` returned from `init` must survive a page reload so `/` knows which agent's feed to poll. Persist it via a `NEXT_PUBLIC`-safe mechanism — a same-site cookie set from the `/init` success handler (readable server-side on `/` for the initial SSR fetch) is preferred over `localStorage`, since the feed page does an initial **server-side** fetch (Phase 6) that needs the id before any client JS runs.
- **Session state:** handled entirely by Clerk (Phase 7), not custom state.
- **Temporary/UI state:** toast/notification visibility (Phase 18), expanded/collapsed rationale panels (Phase 11) — local component state, not global.

**Implementation:** `frontend/hooks/use-feed.ts` is the single source of truth for feed data + loading/error/poll status, consumed by `app/page.tsx`'s client boundary.

**Verification:** confirm no state library dependency exists in `package.json` beyond React/Next built-ins.

---

## Phase 11 — Core Reusable UI Components

**Goal:** Build the visual building blocks before assembling pages.

**Prerequisites:** Phase 5 (theme), Phase 9 (types).

**Files:** `frontend/components/ui/*` (shadcn primitives: `button.tsx`, `card.tsx`, `badge.tsx`, `tabs.tsx` — generated via `bunx shadcn@latest add button card badge tabs`), `frontend/components/feed/{post-card.tsx, rationale-panel.tsx, story-thread.tsx, prediction-badge.tsx, rejected-topic-badge.tsx}`, `frontend/components/persona/persona-header.tsx`

**Implementation per component:**
- `post-card.tsx`: renders one `Post` — `text`, formatted `createdAt` (via `lib/format.ts`), a `sources` link list, and an embedded collapsed `rationale-panel`. Props: `post: Post`.
- `rationale-panel.tsx`: collapsible (`<details>`/shadcn `Collapsible` pattern) panel showing the `rationale` string; visually distinct (muted background) so it reads as "why this was published" metadata, not part of the post body itself. Expanded by default is off — user opens it, keeping the feed scannable.
- `story-thread.tsx`: given a list of `Post[]` that share a `relatedPostId` chain, renders them grouped with a "Chapter N" label derived from position in the chain; used by the feed page to group posts (Phase 12) rather than showing every related post as an isolated card.
- `prediction-badge.tsx`: small `Badge` shown on a `post-card` when `relationship === "PREDICTION_RESOLUTION"`, colored by verdict (correct/wrong/unclear) parsed from the post's `rationale`/`text` — no new backend field is invented for this; the badge is a presentational read of existing data (avoid inventing an unspecified `verdict` field not in `packages/shared-types`).
- `rejected-topic-badge.tsx`: optional/debug — only rendered if a future admin surface exposes `topic_debt` data; **not wired to any current endpoint**, since the spec's only read endpoint is `feed`. Build the component but leave it unused/behind a feature flag rather than fabricating a `topic-debt` API call.
- `persona-header.tsx`: persona `name`, `domain`, and a short static voice description; sourced from the first post's context or a minimal `GET`-free placeholder if no persona metadata endpoint exists (the spec doesn't expose a persona-read endpoint — display name/domain captured from the `/init` form submission, persisted alongside `agentId`, per Phase 10).

**Accessibility:** every interactive element (`Collapsible` trigger, `Tabs`) is a real `<button>` with `aria-expanded`/`aria-controls`; `post-card` uses semantic `<article>`; source links have descriptive `aria-label`s (e.g. "Source: TechCrunch") rather than bare URLs as link text.

**Testing:** component tests (Vitest + Testing Library) for `post-card` (renders text/rationale/sources), `rationale-panel` (toggles visibility on click/Enter), `prediction-badge` (renders only when relationship matches).

**Verification:** a Storybook-less manual check — render each component with fixture `Post` data in a scratch page and visually confirm.

---

## Phase 12 — Main Pages / Screens

**Goal:** Assemble components into the two real pages.

**Prerequisites:** Phases 6–11.

**Files:** `frontend/app/page.tsx` (feed viewer), `frontend/app/init/page.tsx` (init trigger)

**Implementation — `/` (feed viewer):**
- Server Component does the first `getFeed(agentId)` call (agentId read from the persisted cookie, Phase 10) for instant first paint; if no `agentId` cookie exists, render an empty/"not initialized yet" state pointing to `/init`.
- Passes initial posts into a Client Component boundary that mounts `use-feed.ts` for live polling.
- Groups posts: for any post with `relatedPostId`, renders via `story-thread.tsx`; standalone posts render as individual `post-card.tsx`.
- Renders `persona-header.tsx` above the list.

**Implementation — `/init`:**
- Client Component form (Phase 13) with `name`/`domain` fields, gated by Clerk (Phase 7).
- On submit, calls `initAgent()` (Phase 8), on success sets the `agentId` cookie/persisted value and redirects to `/`.
- Once `agentId` already exists (init already called), render a disabled/"already initialized" state instead of the form — mirrors the backend's "callable exactly once" rule (`BACKEND_STEPS.md` Phase 12) and prevents a confusing duplicate 409 UX.

**UI behavior:** `/` is read-focused and works with zero interaction (auto-refreshing feed); `/init` is a single, short, one-time action.

**Testing:** integration test rendering `/` with a mocked `getFeed` fixture and asserting posts render in the given order; test rendering `/init` in both "not yet initialized" and "already initialized" states.

**Verification:** manual walkthrough — visit `/init` signed in, submit, get redirected to `/`, see the (possibly empty) feed.

---

## Phase 13 — Forms and User Input Flows

**Goal:** The single form in the product — the init form.

**Files:** touches `frontend/app/init/page.tsx` (or a dedicated `components/persona/init-form.tsx` if extracted)

**Fields:**
| Field | Type | Validation | Error message |
|---|---|---|---|
| `name` | text | required, 1–80 chars | "Persona name is required." / "Keep it under 80 characters." |
| `domain` | text | required, 1–120 chars | "Domain/focus is required." / "Keep it under 120 characters." |

**Implementation:** plain controlled inputs (no form library needed for two fields — avoids an unnecessary dependency); client-side validation on submit before calling `initAgent()`; submit button disabled while `submitting` is true and while fields are invalid.

**Submission behavior:** on success → set persisted `agentId`, `name`, `domain` → redirect to `/`. On `400` → show field-level validation errors from the backend if provided, else the generic messages above. On `401` → prompt re-sign-in (shouldn't normally occur since the route is gated, but handle defensively). On `409` (already initialized) → show "This agent has already been initialized" and link to `/`.

**Accessibility:** `<label htmlFor>` for every input, `aria-invalid`/`aria-describedby` wired to inline error text, submit button has a clear accessible name ("Initialize Agent"), focus moves to the first invalid field on failed client-side validation.

**Testing:** component test submitting empty fields shows both errors; submitting valid fields calls `initAgent` with the right payload; mocked 409 response renders the "already initialized" message.

**Verification:** manual submit with empty/invalid/valid data, confirm each path's UI matches the table above.

---

## Phase 14 — AI / Agent Interaction UI

**N/A per PRD scope.** The PRD explicitly defines an *autonomous* agent with **no human interaction after initialization** (`FR15`, "Out of Scope: any human intervention or additional prompting after initialization"). There is no chat, command, or prompt interface to build. The frontend's only "agent-facing" surface is the read-only feed (Phase 12) and the one-time init form (Phase 13). Do not build a chat box, message composer, or agent command UI — it would contradict the autonomy requirement.

---

## Phase 15 — Streaming / Real-Time UI

**Partially N/A.** No token-level LLM streaming is required or exposed by the backend (the backend returns completed posts, not streamed generations). What *is* "real-time" from the evaluator's point of view is the feed appearing to update over the 48h window — implemented as **polling**, not a persistent connection, since the spec only requires the feed to be "queryable at any time," not pushed.

**Implementation:** `frontend/hooks/use-feed.ts` — `useEffect` interval (`NEXT_PUBLIC_FEED_POLL_INTERVAL_MS`, default e.g. 15–30s) calling `getFeed(agentId)`, diffing against current state, prepending any posts not already present (feed is reverse-chronological, so new posts appear at index 0), never removing/mutating existing posts (matches the backend's immutability guarantee). Pauses polling when the browser tab is hidden (`document.visibilitychange`) to avoid unnecessary calls, resumes on focus.

**UI behavior:** a subtle "Live" indicator (small pulsing dot + "checking for updates") near the persona header; when a new post arrives, briefly highlight the new card (CSS transition) so evaluators notice fresh content without a jarring layout jump.

**Testing:** hook test using fake timers asserting `getFeed` is called on each interval tick and that new posts are prepended, not duplicated (dedupe by `id`).

**Verification:** manually publish a post via a backend test cycle while `/` is open and confirm it appears within one poll interval without a manual refresh.

---

## Phase 16 — Backend Data Fetching and Mutations

**Goal:** Consolidate fetch/mutation logic used by the pages.

**Files:** `frontend/hooks/use-feed.ts`, calls into `lib/api-client.ts` (Phase 8)

**Implementation:** `use-feed.ts` signature: `useFeed(agentId: string | null): {posts: Post[], status: "idle"|"loading"|"success"|"error", error?: string, lastCheckedAt: Date}`. Internally: initial fetch on mount (skipped if SSR already provided initial data — accepts an `initialPosts` param from `app/page.tsx`'s server fetch to avoid a redundant first client call), then interval polling per Phase 15. The one mutation in the app (`initAgent`) is called directly from `app/init/page.tsx`'s submit handler — not abstracted into a generic mutation hook, since there's exactly one mutation in the entire product (avoid over-engineering).

**Backend integration:** re-states the Phase 8 table — `use-feed.ts` is the only caller of `getFeed`; `app/init/page.tsx` is the only caller of `initAgent`.

**Testing:** covered under Phase 15's hook tests plus Phase 8's client tests.

**Verification:** network tab shows exactly one `getFeed` call per poll interval and one `initAgent` call per form submit — no duplicate/rapid-fire requests.

---

## Phase 17 — Loading, Empty, Error, and Success States

**Goal:** Every async surface has all four states designed, not just the happy path.

**States to implement:**

| Surface | Loading | Empty | Error | Success |
|---|---|---|---|---|
| `/` initial load | skeleton `post-card` placeholders (3–4) | "No posts yet — Ada is still researching. Check back soon." with the live indicator visible | "Couldn't load the feed. Retrying…" with automatic retry (Phase 8 backoff), plus a manual "Retry now" button after repeated failures | rendered feed, newest first |
| `/` polling | no full-page loading state (silent background refresh); "Live" indicator shows a subtle "checking…" pulse | n/a (already covered) | small inline non-blocking banner "Live updates paused — retrying" if polling fails repeatedly; existing posts remain visible throughout | new post highlight animation (Phase 15) |
| `/init` submit | button shows spinner + "Initializing…", inputs disabled | n/a | inline field/form-level error per Phase 13's table | redirect to `/` |
| `/init` already-initialized | n/a | n/a | n/a | static message + link to `/`, no form shown |

**Accessibility:** loading skeletons carry `aria-busy="true"`; error banners use `role="alert"` so screen readers announce them; success redirects are not silent — a brief toast (Phase 18) confirms "Agent initialized" before navigating.

**Testing:** component tests forcing each state (mocked slow/failed/empty/populated `getFeed`) and asserting the correct UI renders.

**Verification:** manually simulate each state (throttle network, stop the backend, use a fresh agentId with zero posts) and confirm the table above matches what renders.

---

## Phase 18 — Notifications / Toasts / Modals

**Goal:** Lightweight, non-blocking feedback — no modals are required by the PRD (no destructive/confirmable actions exist beyond the single init submit, which already has its own inline states).

**Files:** `frontend/components/ui/toast.tsx` (shadcn `sonner` or `toast` primitive via `bunx shadcn@latest add sonner`)

**Implementation:** A single toast on successful `/init` submission ("Agent initialized — redirecting…") before navigating to `/`. A toast on the "Live updates paused" recovery ("Live updates restored") once polling succeeds again after a failure streak. No modals are built — there is nothing in the PRD requiring a confirm/cancel dialog.

**Accessibility:** toasts use `aria-live="polite"` (non-urgent) region, auto-dismiss with a reasonable timeout, and are also dismissible via keyboard (`Escape` or a focusable close button).

**Testing:** component test asserting a toast appears after a mocked successful init call.

**Verification:** manual init flow shows the toast before redirect.

---

## Phase 19 — Feature-Specific Workflows from the PRD

**Goal:** Cross-check every PRD workflow (Section 6, "User Workflow") has a corresponding frontend implementation.

| PRD workflow step | Frontend implementation |
|---|---|
| "Evaluator calls `POST /api/agent/init` once" | `/init` page + form (Phases 7, 13) |
| "Agent responds with an `agentId`" | handled by `initAgent()`, persisted (Phase 10), used to key all feed fetches |
| "Agent begins autonomous operation immediately in the background" | purely backend; frontend reflects it only via the feed eventually populating — no frontend action needed |
| "Evaluator periodically calls `GET /api/agent/feed`" | `use-feed.ts` polling (Phases 15–16) automates this so a human evaluator doesn't have to manually re-call it, while still allowing direct API polling independently |
| "Evaluator observes new posts appearing over time, each with text, rationale, and sources" | `post-card.tsx` + `rationale-panel.tsx` (Phase 11) |
| "No further prompts or instructions are ever sent to the agent" | confirmed by Phase 14's N/A — no input surface exists beyond the one-time init |
| Story continuation / prediction resolution / topic resurrection / concept-gap visibility (PRD §5, memory-driven behaviors) | `story-thread.tsx` (grouping by `relatedPostId`) and `prediction-badge.tsx` (Phase 11) make these differentiators visible in the feed, not just present in backend logs |

**Verification:** walk this table against the running app and check each row off.

---

## Phase 20 — Responsive / Mobile Implementation

**Goal:** Feed and init form work down to small mobile viewports.

**Responsive behavior:**
- **Desktop (≥1024px):** feed as a centered single column, max-width ~680px (optimized for reading, not a wide dashboard grid — matches the editorial/content nature of the product); `persona-header` and "Live" indicator in a sticky top bar.
- **Tablet (768–1023px):** same single-column layout, reduced horizontal padding.
- **Mobile (<768px):** full-width cards with tighter padding; `rationale-panel` collapses by default (already default) to keep cards short; source links wrap to their own lines; `/init` form fields stack full-width with larger touch targets (min 44px height).

**Implementation:** Tailwind responsive utility classes (`sm:`, `md:`, `lg:`) directly in `post-card.tsx`, `persona-header.tsx`, and `app/init/page.tsx`'s form — no separate mobile-only components.

**Testing:** component snapshot/visual check at 375px, 768px, 1440px viewports (Playwright viewport presets, Phase 24).

**Verification:** manual resize in browser dev tools across the three breakpoints; confirm no horizontal scroll and all interactive elements remain tappable.

---

## Phase 21 — Accessibility and UX Polishing

**Goal:** Final pass across the whole app.

**Accessibility checklist to apply:**
- Full keyboard navigation: tab order follows visual order on both pages; `rationale-panel` and `Tabs`/`Collapsible` triggers operable via Enter/Space.
- Semantic landmarks: `<header>` for `persona-header`, `<main>` wrapping the feed/form, `<article>` per post.
- Color contrast re-verified against the final theme (Phase 5) with real content, not placeholder text.
- All images/icons (lucide-react) marked `aria-hidden="true"` when purely decorative; meaningful icons (e.g. the "Live" dot) paired with visible or `sr-only` text.
- Form errors (Phase 13) and async states (Phase 17) already wired with `aria-live`/`role="alert"` — verify no regressions.
- Focus is visibly styled (Tailwind `focus-visible:` rings) on every interactive element, not suppressed.

**UX polish:** consistent spacing scale from the Phase 5 theme applied everywhere; loading skeleton shapes match final card dimensions (no layout shift); relative time display (e.g. "2h ago") in `lib/format.ts` with the full ISO timestamp available via `title` attribute on hover/focus for precision.

**Testing:** automated accessibility audit (`@axe-core/react` in dev, or Playwright's `axe` integration in Phase 24) run against both pages.

**Verification:** zero critical/serious axe violations on `/` and `/init` in both populated and empty states.

---

## Phase 22 — Unit / Component Testing

**Goal:** Isolated tests for components, hooks, and utilities.

**Files:** colocated `*.test.tsx`/`*.test.ts` next to each source file, or `frontend/__tests__/` mirroring `components/`/`lib/`/`hooks/`.

**Coverage required:** every component in Phase 11 (rendering + interaction), `lib/api-client.ts` (Phase 8), `lib/format.ts` (date formatting edge cases — same-minute, hours, days, and the raw ISO fallback), `hooks/use-feed.ts` (Phase 15/16).

**Verification:** `bun run test` (Vitest) passes with no network calls (all `fetch` mocked).

---

## Phase 23 — Integration Testing

**Goal:** Test full pages against a mocked API layer (MSW or manual `fetch` mocks), not individual components in isolation.

**Files:** `frontend/__tests__/pages/*` (or colocated with `app/page.tsx`, `app/init/page.tsx`)

**Coverage required:** `/` renders correctly for populated feed, empty feed, and error-from-backend fixtures; `/init` full happy-path submit → redirect flow; `/init` already-initialized state; Clerk-gated redirect behavior for signed-out users hitting `/init` (mocked Clerk state).

**Verification:** `bun run test` integration suite passes against mocked API responses matching real backend response shapes exactly (cross-check against `BACKEND_STEPS.md` Phase 13 schemas).

---

## Phase 24 — End-to-End Testing

**Goal:** Real browser test against a running (local or staging) backend.

**Prerequisites:** Backend deployed/running per `BACKEND_STEPS.md` Phase 25/26; `NEXT_PUBLIC_API_BASE_URL` pointed at it.

**Files:** `frontend/e2e/*.spec.ts` (Playwright)

**Coverage required:** sign in (Clerk test mode) → visit `/init` → submit persona → redirected to `/` → confirm empty/loading state → (in a shortened-cycle staging backend) wait for and observe a real post appear via polling without any manual refresh → confirm rationale panel expands → confirm source links are valid absolute URLs → run at mobile and desktop viewport presets → run the axe accessibility check from Phase 21 as part of the same suite.

**Verification:** `bunx playwright test` passes end-to-end against staging.

---

## Phase 25 — Production Build Configuration

**Goal:** Ensure `next build` is production-safe.

**Implementation:** confirm `next.config.js` has no `dangerouslyAllowSVG`/unsafe settings not needed here; set `output` mode appropriate to the deploy target (default Node server output for Vercel, per the tech stack). Verify all `NEXT_PUBLIC_*` vars are supplied at build time in CI (Next.js inlines them at build, not runtime). Run a bundle-size sanity check — no unused heavy dependency (e.g. accidentally including a full icon set beyond `lucide-react`'s tree-shaken imports).

**Security:** confirm `CLERK_SECRET_KEY` does not appear in the client bundle (`next build` output analysis / `grep` the `.next/static` output for the secret's value as a smoke check).

**Verification:** `bun run build && bun run start` serves the production build locally; both pages work identically to dev mode.

---

## Phase 26 — Frontend Deployment Preparation

**Goal:** Ready for Vercel deployment per the tech stack.

**Implementation:** connect the repo to Vercel, set the project root to `frontend/` (monorepo-aware build), configure the same env vars from Phase 4 in Vercel's project settings (marking `CLERK_SECRET_KEY` as a server-only/encrypted env var), confirm `NEXT_PUBLIC_API_BASE_URL` points at the production backend host from `infra/deploy/`. `infra/ci/github-actions/frontend-ci.yml` runs lint (`eslint`), typecheck (`tsc --noEmit`), and build on every PR before Vercel's own deploy preview.

**Verification:** a Vercel preview deployment for a test PR loads `/` and `/init` correctly against the staging backend.

---

## Phase 27 — Final Frontend Verification

Run this checklist before considering the frontend done.

### Complete frontend file checklist
- [ ] `app/layout.tsx`, `app/page.tsx`, `app/globals.css`, `app/init/page.tsx`
- [ ] `components/ui/{button,card,badge,tabs,sonner}.tsx`
- [ ] `components/feed/{post-card,rationale-panel,story-thread,prediction-badge,rejected-topic-badge}.tsx`
- [ ] `components/persona/persona-header.tsx`
- [ ] `lib/{api-client,format}.ts`
- [ ] `hooks/use-feed.ts`
- [ ] `types/feed.ts`
- [ ] `middleware.ts`
- [ ] `next.config.js`, `tailwind.config.ts`, `tsconfig.json`, `components.json`
- [ ] `package.json`, `.env.example`
- [ ] `packages/shared-types/src/{agent.ts, feed.ts, index.ts}`

### Required dependencies checklist
`next`, `react`, `react-dom`, `typescript`, `tailwindcss`, `@clerk/nextjs`, `clsx`, `tailwind-merge`, `class-variance-authority`, `lucide-react`, `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@playwright/test`, `eslint-config-next`.

### Required environment variables checklist
- [ ] `NEXT_PUBLIC_API_BASE_URL` (public)
- [ ] `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` (public)
- [ ] `CLERK_SECRET_KEY` (server-only)
- [ ] `NEXT_PUBLIC_FEED_POLL_INTERVAL_MS` (public, optional)

### Page/screen checklist
- [ ] `/` — feed viewer (populated, empty, loading, error states)
- [ ] `/init` — init form (empty form, validation errors, submitting, already-initialized, success)

### Component checklist
- [ ] `post-card`, `rationale-panel`, `story-thread`, `prediction-badge`, `rejected-topic-badge`, `persona-header`, shadcn primitives (`button`, `card`, `badge`, `tabs`, `sonner`)

### API integration checklist
- [ ] `POST /api/agent/init` — authenticated, one-time, error states handled (400/401/409)
- [ ] `GET /api/agent/feed` — polled, unauthenticated, reverse-chronological render, empty/404-agent handling

### State-management checklist
- [ ] Server state: feed, via `use-feed.ts` only
- [ ] Local state: init form fields
- [ ] Persisted state: `agentId`/`name`/`domain` cookie
- [ ] Session state: Clerk-managed only
- [ ] No global state library introduced

### Authentication checklist
- [ ] `/init` gated via Clerk middleware
- [ ] `/` and feed reads remain public
- [ ] Bearer token attached to `initAgent()` only, sourced server-side
- [ ] Sign-out available via `<UserButton/>` on `/init`

### Testing checklist
- [ ] Unit/component tests (Phase 22) passing
- [ ] Integration tests (Phase 23) passing
- [ ] E2E tests against staging (Phase 24) passing
- [ ] Accessibility audit (Phase 21/24) — zero critical/serious violations

### Local development commands
```
cd frontend
bun install
bun run dev            # http://localhost:3000
bun run test            # unit/component
bunx playwright test    # e2e (requires running backend)
```

### Production build/deployment checklist
- [ ] `bun run build` succeeds
- [ ] `CLERK_SECRET_KEY` confirmed absent from client bundle
- [ ] Vercel project env vars configured (public + server-only correctly split)
- [ ] `frontend-ci.yml` (lint/typecheck/build) passing on PRs
- [ ] Preview deployment verified against staging backend

### Final UX/accessibility checklist
- [ ] Full keyboard operability on both pages
- [ ] WCAG AA contrast in light and dark
- [ ] `aria-live` regions for async/error/toast states
- [ ] Responsive at mobile/tablet/desktop breakpoints
- [ ] No layout shift between skeleton and loaded states

### Exact Build Order
1. Project init → 2. Dependencies/shadcn setup → 3. Env config → 4. Theme/design system → 5. Root layout + two routes → 6. Clerk middleware/auth → 7. Shared types (`packages/shared-types`) → 8. API client → 9. State plan (`use-feed` skeleton) → 10. Core UI components (`post-card`, `rationale-panel`, `story-thread`, `prediction-badge`, `persona-header`) → 11. Assemble `/` and `/init` pages → 12. Init form + validation → 13. Feed polling hook (real-time) → 14. Loading/empty/error/success states → 15. Toasts → 16. PRD workflow cross-check → 17. Responsive pass → 18. Accessibility pass → 19. Unit/component tests → 20. Integration tests → 21. E2E tests against staging backend → 22. Production build hardening → 23. Vercel deployment → 24. Final verification checklist.
