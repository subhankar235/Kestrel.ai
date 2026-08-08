Root Structure — Autonomous AI Creator Agent
.
├── backend/                # FastAPI service, Temporal workflows, editorial/memory logic
├── frontend/                # Next.js feed viewer / evaluator dashboard
├── infra/                   # Docker, CI/CD, deployment, monitoring configs
├── docs/                    # PRD, architecture, API contract, persona bible
├── packages/                # Shared TypeScript types/contracts (frontend <-> backend)
├── .env.example              # Root-level env template (shared/global vars only)
├── .gitignore
├── README.md
├── docker-compose.yml         # Local dev orchestration (postgres, backend, worker, temporal, frontend)
└── package.json               # Root workspace manifest (bun workspaces: frontend, packages/*)



# Backend Structure — FastAPI + Temporal + Breeth

```
backend/
├── app/
│   ├── main.py                        # FastAPI app entrypoint; mounts routers, middleware, startup hooks
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── agent_init.py          # POST /api/agent/init (called exactly once)
│   │   │   └── agent_feed.py          # GET /api/agent/feed?agentId=... (only endpoint polled after init)
│   │   └── deps.py                    # shared FastAPI dependencies (DB session, auth guard)
│   │
│   ├── core/
│   │   ├── config.py                  # Pydantic BaseSettings — env vars, thresholds, intervals
│   │   ├── security.py                # Clerk token verification for the init endpoint
│   │   └── logging.py                 # structured JSON logging (feeds self-audit + observability)
│   │
│   ├── models/                        # SQLAlchemy ORM models (system of record)
│   │   ├── agent.py                   # agent instance + agentId
│   │   ├── persona.py                 # persona name/domain/voice config
│   │   ├── post.py                    # published post (immutable, id/createdAt/text/rationale/sources)
│   │   ├── constitution.py            # versioned editorial constitution rules
│   │   └── topic_debt.py              # rejected topics + reason + revisit condition
│   │
│   ├── schemas/                       # Pydantic request/response contracts
│   │   ├── agent.py                   # InitRequest / InitResponse
│   │   ├── feed.py                    # FeedResponse / PostOut (matches API_REQUIREMENTS)
│   │   └── memory.py                  # Breeth search/episode payload shapes
│   │
│   ├── db/
│   │   ├── session.py                 # SQLAlchemy engine/session factory
│   │   └── base.py                    # declarative base + model registry
│   │
│   ├── migrations/                    # Alembic migrations for agent/post/constitution tables
│   │   ├── versions/
│   │   └── env.py
│   │
│   ├── persona/
│   │   ├── constitution.py            # editorial rules/thresholds (relevance, novelty, evidence...)
│   │   ├── voice.py                   # persona voice/style/tone definitions
│   │   └── seed_personas.py           # example personas (e.g. "Ada" — AI Security)
│   │
│   ├── discovery/
│   │   ├── sources/
│   │   │   ├── exa_client.py          # Exa semantic/live web search
│   │   │   ├── tavily_client.py       # Tavily search, cross-checking sources
│   │   │   ├── rss_client.py          # RSS feeds (blogs, advisories)
│   │   │   └── github_client.py       # GitHub releases/repos as candidate topics
│   │   ├── normalizer.py              # raw source result -> Topic (title/summary/claims/entities/sources)
│   │   └── discovery_service.py       # orchestrates multi-source discovery into candidate topics
│   │
│   ├── memory/                        # Breeth ("long-term memory") integration layer
│   │   ├── breeth_client.py           # thin client for POST /v1/search, POST /v1/episodes
│   │   ├── recall.py                  # runs memory search + interprets results before judgment
│   │   ├── episode_writer.py          # write-back of topic/claims/stance/story/etc after publish
│   │   └── behaviors/
│   │       ├── story_continuity.py    # detects/generates story "chapters", sets relatedPostId
│   │       ├── prediction_update.py   # compares past predictions to new evidence, publishes verdicts
│   │       ├── topic_resurrection.py  # re-scores previously rejected topic debt
│   │       └── concept_gap.py         # finds unconnected concepts, researches the gap
│   │
│   ├── editorial/
│   │   ├── scorer.py                  # scores relevance/novelty/evidence/persona-fit/timeliness/etc.
│   │   ├── judge.py                   # accept/reject decision against constitution threshold
│   │   └── topic_debt.py              # logs rejections with reason + revisit condition
│   │
│   ├── drafting/
│   │   ├── draft_generator.py         # generates 3 candidate angles per accepted topic
│   │   ├── self_critique.py           # scores/ranks drafts, selects a winner
│   │   └── persona_check.py           # verifies winning draft matches voice/beliefs/domain
│   │
│   ├── publishing/
│   │   ├── publisher.py               # persists the final post (immutable record)
│   │   └── rationale_builder.py       # builds the "why selected / why now / memory link" rationale
│   │
│   ├── llm/
│   │   ├── openai_client.py           # OpenAI API wrapper (JSON/structured output mode)
│   │   └── prompts/                   # prompt templates per pipeline step (score, draft, critique...)
│   │
│   ├── workflows/                     # Temporal — the autonomous background loop
│   │   ├── agent_workflow.py          # main cycle: discover -> recall -> judge -> draft -> publish -> write-back
│   │   ├── activities.py              # individual Temporal activities calling the modules above
│   │   ├── schedules.py               # Temporal Schedule config controlling publish cadence
│   │   └── worker.py                  # Temporal worker process entrypoint (runs unattended for 48h)
│   │
│   └── self_audit/
│       ├── auditor.py                 # periodic review of published/rejected history for failure patterns
│       └── constitution_versioning.py # applies rule changes, bumps constitution version
│
├── tests/
│   ├── unit/                          # scorer, judge, recall, rationale_builder, etc.
│   ├── integration/                   # API endpoints, DB, Breeth client (mocked)
│   └── conftest.py
│
├── alembic.ini
├── pyproject.toml                     # dependencies, tool config (FastAPI, SQLAlchemy, Temporal SDK, etc.)
├── requirements.txt                   # (or poetry.lock, generated from pyproject.toml)
├── Dockerfile
└── .env.example                       # OPENAI_API_KEY, DATABASE_URL, BREETH_API_KEY, EXA/TAVILY keys, TEMPORAL_ADDRESS
```

## Key responsibilities

- **api/routes/** — the only two HTTP surfaces the evaluator touches; kept intentionally thin, delegating to `publishing/` and `db/` for reads/writes.
- **workflows/** — the actual "autonomy": once `agent_workflow.py` is started at init time, `schedules.py` keeps re-running the cycle without any further external calls.
- **memory/** — implements the Breeth-driven behaviors (story continuity, prediction resolution, topic resurrection, concept-graph gap-filling) described in the architecture doc; this is the project's core differentiator.
- **editorial/** + **persona/** — encode the "can say no" requirement and the self-evolving constitution.
- **models/** vs **memory/** — PostgreSQL (`models/`) is the authoritative feed/API store; Breeth (`memory/`) is the associative long-term memory the agent reasons over. They are kept as separate concerns per the architecture doc.







# Frontend Structure — Next.js Feed Viewer

```
frontend/
├── app/
│   ├── layout.tsx                  # root layout, fonts, providers
│   ├── page.tsx                    # feed viewer — polls GET /api/agent/feed, renders posts newest-first
│   ├── globals.css                 # Tailwind base styles
│   └── init/
│       └── page.tsx                # gated demo page to trigger POST /api/agent/init once
│
├── components/
│   ├── ui/                         # shadcn/ui primitives: button, card, badge, tabs
│   ├── feed/
│   │   ├── post-card.tsx           # single post: text, createdAt, sources
│   │   ├── rationale-panel.tsx     # expandable "why this was published" panel
│   │   ├── story-thread.tsx        # groups posts by relatedPostId / STORY_CONTINUATION chapters
│   │   ├── prediction-badge.tsx    # marks prediction-resolution posts (correct/wrong/unclear)
│   │   └── rejected-topic-badge.tsx# optional debug view of topic debt (if exposed)
│   └── persona/
│       └── persona-header.tsx      # persona name, domain, short voice description
│
├── lib/
│   ├── api-client.ts               # typed fetch wrapper for /api/agent/init and /api/agent/feed
│   └── format.ts                   # ISO 8601 date formatting, relative time helpers
│
├── hooks/
│   └── use-feed.ts                 # polling hook that re-fetches the feed on an interval
│
├── types/
│   └── feed.ts                     # local types, re-exported from packages/shared-types
│
├── middleware.ts                   # Clerk auth middleware (protects /init)
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── .env.example                    # NEXT_PUBLIC_API_BASE_URL, Clerk keys
```

## Key responsibilities

- **app/page.tsx + hooks/use-feed.ts** — the primary evaluator-facing view: polls the feed endpoint and renders new posts as they appear, satisfying the "observe over 48 hours" workflow.
- **components/feed/** — visualizes the memory-driven behaviors (story chapters, prediction verdicts) so the differentiating logic in the backend is visible, not just logged.
- **app/init/** — a convenience UI for the one-time init call; not required by the spec (init can be called directly via API) but useful for demos.
- **types/feed.ts** — kept thin; the source of truth for shared shapes lives in `packages/shared-types` to avoid frontend/backend contract drift.











# Infra Structure — Docker, CI/CD, Deployment, Monitoring

```
infra/
├── docker/
│   ├── backend.Dockerfile          # FastAPI service image
│   ├── worker.Dockerfile           # Temporal worker image (runs the autonomous cycle)
│   └── frontend.Dockerfile         # Next.js image
│
├── docker-compose.yml              # local dev stack: postgres, backend, worker, temporal, frontend
├── temporal/
│   └── docker-compose.temporal.yml # self-hosted Temporal server + Web UI (used if not on Temporal Cloud)
│
├── ci/
│   └── github-actions/
│       ├── backend-ci.yml          # lint (ruff/black) + test (pytest) + build backend image
│       ├── frontend-ci.yml         # lint (eslint) + typecheck + build frontend
│       └── deploy.yml              # deploy backend/worker to Railway/Fly/Render, frontend to Vercel
│
├── deploy/
│   ├── railway.json                # (or fly.toml / render.yaml) — backend + worker + Postgres deploy config
│   └── vercel.json                 # frontend deploy config
│
├── monitoring/
│   └── sentry.yml                  # Sentry DSN + environment config for backend/worker error tracking
│
└── env/
    ├── .env.staging.example
    └── .env.production.example
```

## Key responsibilities

- **docker/** — one Dockerfile per runnable process; the worker is separated from the API service since it must stay alive independently for the full 48-hour unattended window.
- **docker-compose.yml** — brings up Postgres + Temporal + backend + worker + frontend together for local development and demoing the full autonomous loop.
- **ci/github-actions/** — keeps backend and frontend pipelines independent so either can be tested/deployed without the other; `deploy.yml` ships the worker and API together since they share the same Temporal workflow code.
- **monitoring/** — Temporal's own Web UI (from `temporal/docker-compose.temporal.yml`) is used to verify the workflow ran autonomously; Sentry catches unhandled failures in the FastAPI/worker processes during the unattended run.
- **env/** — per-environment secrets templates (OpenAI, Breeth, Exa, Tavily, Clerk, Postgres, Temporal address), kept out of `backend/` and `frontend/` so deployment config isn't mixed with app code.





# Packages Structure — Shared Types

```
packages/
└── shared-types/
    ├── src/
    │   ├── agent.ts        # InitRequest, InitResponse ({ agentId })
    │   ├── feed.ts          # Post, FeedResponse ({ posts: Post[] })
    │   └── index.ts         # barrel export
    ├── package.json
    └── tsconfig.json
```

## Key responsibilities

- **shared-types/** — the single source of truth for the JSON contracts defined in the API spec (`Post`, `FeedResponse`, `InitRequest`/`InitResponse`). Consumed directly by `frontend/types/feed.ts` and `frontend/lib/api-client.ts` via the Bun workspace, preventing schema drift between the Next.js UI and the FastAPI backend's Pydantic models.
- This package is TypeScript-only; the backend's Pydantic schemas in `backend/app/schemas/` are kept manually aligned with it (or optionally generated from the FastAPI OpenAPI spec in a future iteration).
