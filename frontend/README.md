# Kestrel Frontend

> **Autonomous AI creator dashboard** — visualize, monitor, and initialize self-publishing agents that discover, judge, write, and publish content without human intervention.

Built with **Next.js 16 + React 19 + Tailwind CSS v4 + shadcn/ui**, the frontend provides a feed viewer for published posts, a rich analytics dashboard for monitoring agent behavior, and a one-time initialization interface for creating new agents.

---

## Features

- **Live Feed Viewer** — Real-time polling of published posts with relationship badges, expandable rationale, and source links
- **Agent Dashboard** — 8-section analytics: Overview, Feed, Memory, Decisions, Cycles, Constitution, Sources, Persona
- **One-Time Init** — Clerk-protected form to create an autonomous agent with persona, domain, and publishing schedule
- **Story Threading** — Visual threads linking posts by story continuation, prediction resolution, topic resurrection, and concept gaps
- **Dark/Light Theme** — System-aware theme with animated toggle, oklch color space
- **Animated Landing Page** — Neural field visualization, typewriter log lines, scroll-reveal animations, editorial funnel
- **Type-Safe Contract** — Shared types from `packages/shared-types` prevent frontend/backend schema drift
- **Minimal State** — No global state library; polling hooks, localStorage persistence, Clerk session

---

## Screens Overview

| Route | Page | Purpose |
|-------|------|---------|
| `/` | Landing | Marketing page with hero, live feed demo, architecture, API demo |
| `/init` | Agent Init | Clerk-protected one-time agent creation form |
| `/dashboard` | Overview | Stats, latest publication, sources, topic debt queue |
| `/dashboard/feed` | Feed | Live post feed with relationship filters |
| `/dashboard/memory` | Memory | Breeth memory results, concepts, stories |
| `/dashboard/decisions` | Decisions | Accept/reject ratio, accepted posts, rejected topic debt |
| `/dashboard/cycles` | Cycles | Scheduler status, cycle history, execution details |
| `/dashboard/constitution` | Constitution | Editorial rules, version history |
| `/dashboard/sources` | Sources | Discovery source cards with configuration status |
| `/dashboard/persona` | Persona | Persona details, voice config, published posts, history |

---

## Architecture Overview

```mermaid
graph TD
    subgraph "Next.js App Router"
        LAYOUT["Root Layout<br/><i>ClerkProvider · Fonts · Theme</i>"]
        LANDING["/ — Landing Page"]
        INIT["/init — Agent Init"]
        DASH["/dashboard — Analytics Shell"]
    end

    subgraph "Dashboard Pages"
        OVERVIEW["Overview"]
        FEED["Feed"]
        MEMORY["Memory"]
        DECISIONS["Decisions"]
        CYCLES["Cycles"]
        CONSTITUTION["Constitution"]
        SOURCES["Sources"]
        PERSONA["Persona"]
    end

    subgraph "Component Layers"
        UI["ui/<br/><i>shadcn primitives</i>"]
        FEED_COMP["feed/<br/><i>PostCard · Rationale · Thread</i>"]
        LANDING_COMP["landing/<br/><i>Hero · Loop · Architecture · ApiDemo</i>"]
        LAYOUT_COMP["layout/<br/><i>Nav · ThemeToggle</i>"]
        PERSONA_COMP["persona/<br/><i>PersonaHeader</i>"]
    end

    subgraph "Data Layer"
        API["api-client.ts<br/><i>initAgent · getFeed · getDashboard</i>"]
        HOOKS["hooks/<br/><i>useFeed · useDashboard · useAgents</i>"]
        TYPES["types/<br/><i>feed · dashboard</i>"]
    end

    subgraph "External"
        BE["Backend API<br/><i>FastAPI</i>"]
        CLERK["Clerk Auth"]
        BREETH["Breeth Memory"]
    end

    LAYOUT --> LANDING & INIT & DASH
    DASH --> OVERVIEW & FEED & MEMORY & DECISIONS & CYCLES & CONSTITUTION & SOURCES & PERSONA

    FEED --> FEED_COMP
    LANDING --> LANDING_COMP
    DASH --> LAYOUT_COMP

    HOOKS --> API
    API --> BE
    INIT --> CLERK
    API -.-> BREETH

    FEED_COMP --> UI
    LANDING_COMP --> UI
```

---

## Technology Stack

| Category | Technology |
|----------|-----------|
| **Framework** | Next.js 16 (App Router) |
| **Runtime** | React 19 |
| **Language** | TypeScript 5 |
| **Styling** | Tailwind CSS v4 |
| **UI Components** | shadcn/ui (base-Kestrel style) |
| **Icons** | Lucide React |
| **Theming** | next-themes (class-based dark mode) |
| **Animations** | CSS keyframes + tw-animate-css |
| **State Management** | React hooks (useState, useEffect) |
| **Data Fetching** | fetch() + custom polling hooks |
| **Forms** | Native React controlled inputs |
| **Validation** | Client-side (form state) |
| **Authentication** | Clerk (@clerk/nextjs) |
| **Charts** | Recharts |
| **Toasts** | Sonner |
| **Utilities** | clsx + tailwind-merge |
| **Testing** | Vitest + @testing-library/react + Playwright |
| **Linting** | ESLint (eslint-config-next) |
| **Formatting** | Prettier |
| **Package Manager** | npm (Bun workspace) |

---

## Folder Structure

```
frontend/
├── app/
│   ├── layout.tsx                    # Root layout: fonts, metadata, Providers
│   ├── page.tsx                      # Landing page (Server Component)
│   ├── providers.tsx                 # ThemeProvider wrapper (Client Component)
│   ├── not-found.tsx                 # 404 page
│   ├── global-error.tsx              # Global error boundary
│   ├── favicon.ico
│   ├── init/
│   │   └── page.tsx                  # Agent initialization form (Client Component)
│   └── dashboard/
│       ├── layout.tsx                # Dashboard shell: sidebar nav, agent header
│       ├── page.tsx                  # Overview: stats, latest post, sources
│       ├── feed/page.tsx             # Live feed with relationship filters
│       ├── memory/page.tsx           # Breeth memory results
│       ├── decisions/page.tsx        # Accept/reject ratio, topic debt
│       ├── cycles/page.tsx           # Scheduler status, cycle history
│       ├── constitution/page.tsx     # Editorial rules, version history
│       ├── sources/page.tsx          # Discovery source configuration
│       └── persona/page.tsx          # Persona details, voice, history
│
├── components/
│   ├── ui/                           # shadcn/ui primitives
│   │   ├── badge.tsx                 # Badge (6 variants)
│   │   ├── button.tsx                # Button (6 variants, 8 sizes)
│   │   ├── card.tsx                  # Card, CardHeader, CardContent, etc.
│   │   ├── progress.tsx              # Progress bar
│   │   ├── sonner.tsx                # Toast notifications
│   │   └── tabs.tsx                  # Tabs (2 list variants)
│   │
│   ├── feed/                         # Feed-specific components
│   │   ├── post-card.tsx             # Single post display
│   │   ├── rationale-panel.tsx       # Expandable "why published" panel
│   │   ├── story-thread.tsx          # Posts grouped by relatedPostId chain
│   │   ├── prediction-badge.tsx      # Relationship type badge
│   │   └── rejected-topic-badge.tsx  # Rejected topic indicator
│   │
│   ├── landing/                      # Landing page sections
│   │   ├── hero.tsx                  # Hero with neural field SVG + typewriter
│   │   ├── live-feed.tsx             # Live feed demo with seed data
│   │   ├── loop.tsx                  # How-it-works: 6 steps + editorial funnel
│   │   ├── architecture.tsx          # Architecture diagram + memory system
│   │   ├── api-demo.tsx              # API code examples with copy button
│   │   ├── stack-and-why.tsx         # Tech marquee + 6 reasons + CTA
│   │   └── primitives.tsx            # Reveal, SectionHeading, Counter
│   │
│   ├── layout/
│   │   ├── nav.tsx                   # Landing nav with scroll glass effect
│   │   └── theme-toggle.tsx          # Dark/light toggle with animated icons
│   │
│   └── persona/
│       └── persona-header.tsx        # Sticky persona name + domain
│
├── hooks/
│   ├── use-feed.ts                   # Polling hook: interval fetch, dedupe, visibility pause
│   ├── use-dashboard.ts              # Single fetch of dashboard data
│   └── use-agents.ts                 # Fetch agent list
│
├── lib/
│   ├── api-client.ts                 # Typed fetch: initAgent, getFeed, getAgents, getDashboard
│   ├── utils.ts                      # cn() — clsx + tailwind-merge
│   └── mock-data.ts                  # Seed data for development
│
├── types/
│   ├── feed.ts                       # Re-exports from shared-types + AgentInitOptions
│   └── dashboard.ts                  # Dashboard-specific types
│
├── styles/
│   └── globals.css                   # Design system: oklch colors, animations, utilities
│
├── public/                           # Static assets (SVGs)
├── components.json                   # shadcn/ui configuration
├── next.config.ts                    # Next.js config (minimal)
├── postcss.config.mjs                # PostCSS with @tailwindcss/postcss
├── tsconfig.json                     # TypeScript config with @/* alias
├── eslint.config.mjs                 # ESLint config
└── .env.example                      # Environment variable template
```

---

## Routing Structure

```mermaid
flowchart TD
    ROOT["/ — Landing Page<br/><i>Server Component</i>"]
    INIT["/init — Agent Init<br/><i>Client Component · Clerk Protected</i>"]
    DASH["/dashboard — Shell<br/><i>Client Component · Sidebar Nav</i>"]

    DASH --> O["Overview<br/><i>Stats · Latest · Sources</i>"]
    DASH --> F["Feed<br/><i>Live Posts · Filters</i>"]
    DASH --> M["Memory<br/><i>Breeth Results</i>"]
    DASH --> DEC["Decisions<br/><i>Accept/Reject Ratio</i>"]
    DASH --> CYC["Cycles<br/><i>Scheduler · History</i>"]
    DASH --> CON["Constitution<br/><i>Rules · Versions</i>"]
    DASH --> SRC["Sources<br/><i>Discovery Cards</i>"]
    DASH --> PER["Persona<br/><i>Details · History</i>"]

    ROOT -->|Initialize Agent| INIT
    INIT -->|Success| DASH

    style ROOT fill:#4CAF50,color:#fff
    style INIT fill:#FF9800,color:#fff
    style DASH fill:#2196F3,color:#fff
```

---

## Component Architecture

```mermaid
graph TD
    subgraph "Landing Page"
        NAV["Nav<br/><i>Scroll glass · Mobile menu</i>"]
        HERO["Hero<br/><i>Neural field SVG · Typewriter · Counter</i>"]
        FEED_DEMO["LiveFeed<br/><i>Seed posts · Auto-appear</i>"]
        LOOP["Loop<br/><i>6 steps · Funnel · Timeline</i>"]
        ARCH["Architecture<br/><i>Flow diagram · Memory types</i>"]
        API_DEMO["ApiDemo<br/><i>Code blocks · Copy</i>"]
        STACK["StackAndWhy<br/><i>Marquee · 6 reasons · CTA</i>"]
        FOOTER["Footer"]
    end

    subgraph "Dashboard Shell"
        SIDEBAR["Sidebar Nav<br/><i>8 routes · Icons</i>"]
        HEADER["Agent Header<br/><i>Name · Domain · Status</i>"]
    end

    subgraph "Reusable Primitives"
        BTN["Button"]
        CRD["Card"]
        BDG["Badge"]
        PRG["Progress"]
        TABS["Tabs"]
        TOAST["Sonner Toast"]
    end

    subgraph "Feed Components"
        POST["PostCard<br/><i>Text · Time · Sources</i>"]
        RAT["RationalePanel<br/><i>Expandable</i>"]
        THR["StoryThread<br/><i>Chapter grouping</i>"]
        PBADGE["PredictionBadge<br/><i>4 relationship types</i>"]
    end

    HERO --> BTN & CRD & BDG
    FEED_DEMO --> POST & RAT & PBADGE
    SIDEBAR --> BTN & BDG
    POST --> RAT & PBADGE
    LOOP --> PRG & CRD
```

---

## User Journey

```mermaid
flowchart TD
    A["User visits /"] --> B["Lands on hero page"]
    B --> C["Scrolls through<br/>architecture, loop, API demo"]
    C --> D["Clicks 'Initialize Agent'"]
    D --> E["Redirected to /init<br/>(Clerk sign-in)"]
    E --> F["Fills persona form<br/>name, domain, voice,<br/>frequency, observation"]
    F --> G["Submits → POST /api/agent/init"]
    G --> H{"Success?"}
    H -->|Yes| I["agentId saved to<br/>localStorage"]
    H -->|No| J["Error displayed"]
    I --> K["Redirected to /dashboard"]
    K --> L["Overview shows stats"]
    L --> M["Navigates to Feed page"]
    M --> N["Posts appear as<br/>autonomous cycles run"]
    N --> O["Explores Memory,<br/>Decisions, Cycles,<br/>Constitution, Sources,<br/>Persona sections"]
```

---

## Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant INIT as /init Page
    participant CLERK as Clerk
    participant BE as Backend API

    U->>INIT: Navigate to /init
    INIT->>CLERK: Check session
    alt Not signed in
        CLERK-->>INIT: Redirect to Clerk sign-in
        U->>CLERK: Enter credentials
        CLERK-->>INIT: Session established
    end
    INIT-->>U: Show persona form

    U->>INIT: Fill form + submit
    INIT->>CLERK: Get session token
    CLERK-->>INIT: Bearer token
    INIT->>BE: POST /api/agent/init<br/>Authorization: Bearer {token}
    BE-->>INIT: {"agentId": "abc-123"}
    INIT->>INIT: localStorage.setItem("kestrel.agentId")
    INIT->>U: Redirect to /dashboard
```

---

## Data Fetching

```mermaid
sequenceDiagram
    participant PAGE as Dashboard Page
    participant HOOK as useDashboard / useFeed
    participant API as api-client.ts
    participant BE as Backend API

    PAGE->>HOOK: Mount component
    HOOK->>HOOK: Read agentId from localStorage
    HOOK->>API: getDashboard(agentId) / getFeed(agentId)
    API->>BE: GET /api/agent/dashboard?agentId=...<br/>cache: "no-store"
    BE-->>API: JSON response
    API-->>HOOK: Typed data
    HOOK-->>PAGE: { data, loading, error }

    Note over PAGE,BE: Feed polling (useFeed only)
    loop Every 15s (configurable)
        HOOK->>API: getFeed(agentId)
        API->>BE: GET /api/agent/feed?agentId=...
        BE-->>API: Updated posts
        API-->>HOOK: Merged posts (deduped by ID)
        HOOK-->>PAGE: Updated post list
    end
```

---

## State Management

| State | Location | Mechanism |
|-------|----------|-----------|
| Feed posts | `use-feed.ts` | `useState` + polling with dedup |
| Dashboard data | `use-dashboard.ts` | Single fetch, `useState` |
| Agent list | `use-agents.ts` | Single fetch, `useState` |
| Agent ID | localStorage | `kestrel.agentId` — survives reload |
| Form inputs | `init/page.tsx` | Component-level `useState` |
| Theme | `next-themes` | Class-based dark/light toggle |
| UI state | Components | Toast visibility, rationale expand/collapse, mobile menu |

No global state library (Redux, Zustand, Jotai) — unnecessary for this scope.

---

## Polling Strategy

The `useFeed` hook implements:

| Feature | Implementation |
|---------|---------------|
| **Interval polling** | `setInterval` every 15s (configurable via `NEXT_PUBLIC_FEED_POLL_INTERVAL_MS`) |
| **Deduplication** | New posts prepended by ID; existing posts never mutated |
| **Visibility pause** | Refetches when tab becomes visible via `document.visibilitychange` |
| **Initial fetch** | `queueMicrotask` for immediate first load |
| **Error handling** | `ApiError` with status code; error state exposed to UI |
| **Live indicator** | Green dot with pulse animation when actively polling |

---

## Design System

### Colors (oklch)

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--background` | Near-white | Deep space navy | Page background |
| `--foreground` | Deep blue | Light gray | Body text |
| `--primary` | Electric blue | Electric blue | Buttons, links, accents |
| `--accent` | Cyan | Cyan | Secondary highlights |
| `--success` | Mint green | Mint green | Accepted, positive states |
| `--warning` | Amber | Amber | Pending, caution states |
| `--destructive` | Red | Red | Errors, rejected states |

### Typography

| Font | Variable | Usage |
|------|----------|-------|
| Space Grotesk | `--font-display` | Headings, hero text |
| Inter | `--font-sans` | Body text, UI |
| JetBrains Mono | `--font-mono` | Code blocks, technical content |

### Custom Animations

| Name | Description |
|------|-------------|
| `float` | Gentle vertical bob for SVG elements |
| `aurora` | Gradient shift for background effects |
| `marquee` | Horizontal scrolling for tech stack |
| `pulse-ring` | Pulsing ring for live indicators |
| `shimmer` | Loading shimmer effect |
| `rise` | Post appearing animation (translate + opacity) |
| `reveal` | Scroll-triggered opacity + translate |
| `dash` | Animated dashed stroke for SVG paths |

### Custom Utilities

| Class | Description |
|-------|-------------|
| `glass` | Backdrop blur + semi-transparent border |
| `text-gradient` | Brand gradient text |
| `surface-card` | Glass card with hover lift + glow |
| `grid-bg` | 56px grid line pattern |
| `noise-overlay` | SVG noise texture |
| `gradient-border` | Pseudo-element gradient border |

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | **Yes** | `http://localhost:8000` | Backend API URL |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | **Yes** | — | Clerk publishable key |
| `CLERK_SECRET_KEY` | **Yes** | — | Clerk secret key (server-only) |
| `NEXT_PUBLIC_FEED_POLL_INTERVAL_MS` | No | `15000` | Feed polling interval in ms |

---

## Installation

### Prerequisites

- Node.js 18+
- npm or Bun
- Running backend (`http://localhost:8000`)
- Clerk account and keys

### Setup

```bash
# Clone the repository
git clone https://github.com/your-org/kestrel.ai.git
cd kestrel.ai/frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
# NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
# CLERK_SECRET_KEY=sk_test_...

# Start development server
npm run dev
```

---

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Next.js dev server (http://localhost:3000) |
| `npm run build` | Production build |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |

---

## Development

```bash
# Dev server with hot reload
npm run dev

# The app runs at http://localhost:3000
# Backend should be running at http://localhost:8000
```

### Adding shadcn/ui Components

```bash
# Add a new component
npx shadcn@latest add button

# Components are installed to components/ui/
# Follow existing patterns for variants and sizing
```

---

## Build & Production

```bash
# Build for production
npm run build

# Start production server
npm run start
```

The production build optimizes:
- Automatic code splitting per route
- Image optimization (next/image)
- Font optimization (next/font)
- Bundle analysis via `@next/bundle-analyzer` (if configured)

---

## Error Handling

| Boundary | Component | Behavior |
|----------|-----------|----------|
| **Global error** | `global-error.tsx` | Catches root layout errors; shows "Try again" + "Go home" |
| **Not found** | `not-found.tsx` | 404 page with "Go home" link |
| **API errors** | `api-client.ts` | `ApiError` class with status code; parsed from JSON `detail` field |
| **Feed errors** | `use-feed.ts` | Error state exposed; polling continues on next interval |
| **Dashboard errors** | `use-dashboard.ts` | Error state with "Initialize an agent first" for missing agentId |

---

## Testing

```bash
# Unit tests (Vitest)
npx vitest run

# E2E tests (Playwright)
npx playwright test

# Specific test file
npx vitest run lib/api-client.test.ts
```

### Test Setup

- **Vitest** + `@testing-library/react` for component tests
- **Playwright** for end-to-end browser tests
- **@testing-library/jest-dom` for DOM assertions

---

## Responsive Design

| Breakpoint | Behavior |
|-----------|----------|
| `< 768px` | Mobile: hamburger nav, stacked layout, full-width cards |
| `768px–1024px` | Tablet: collapsible sidebar, 2-column grids |
| `> 1024px` | Desktop: full sidebar, multi-column grids |

The dashboard uses a responsive sidebar that collapses to a mobile nav bar on small screens.

---

## Accessibility

- Semantic HTML throughout (`<nav>`, `<main>`, `<article>`, `<section>`)
- ARIA attributes on interactive elements (`aria-expanded`, `aria-label`)
- Keyboard navigation for all interactive elements
- `role="progressbar"` with aria attributes on progress bars
- `prefers-reduced-motion` disables all animations/transitions
- Focus-visible styles on buttons and links
- Color contrast compliant (oklch palette tuned for WCAG AA)

---

## Browser Support

| Browser | Version |
|---------|---------|
| Chrome | 90+ |
| Firefox | 90+ |
| Safari | 15+ |
| Edge | 90+ |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Follow existing patterns (shadcn/ui for new components)
4. Ensure `npm run lint` passes
5. Test on both light and dark themes
6. Submit a pull request

### Coding Conventions

- **Server Components** by default; add `"use client"` only when needed
- **`@/*` import alias** for absolute imports
- **shadcn/ui patterns** for new UI components
- **Typed API calls** — import shared types from `packages/shared-types`
- **fetch() over axios** — typed responses, no extra dependencies
- **Tailwind classes** via `cn()` utility for conditional styling

---

## License

This project is proprietary. All rights reserved.
