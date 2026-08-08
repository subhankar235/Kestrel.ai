
# Tech Stack — Autonomous AI Creator Agent

## Frontend
| Technology | Why |
|---|---|
| **Next.js (App Router)** | Serves the feed viewer / demo dashboard for evaluators and renders posts, rationale, and sources server-side for fast loads. |
| **TypeScript** | Type-safe contract between frontend and the `/api/agent/feed` response shape (posts, rationale, sources), catching schema drift at compile time. |
| **Tailwind CSS** | Utility-first styling for the feed/timeline UI (story chapters, prediction verdicts, rejected-topic badges) without hand-rolled CSS. |
| **shadcn/ui** | Pre-built accessible components (cards, badges, tabs) used for post cards, persona header, and story-continuation threads. |
| **Bun** | Package manager and runtime for installing deps and running Next.js scripts (`bun install`, `bun run dev`) instead of npm/pnpm. |

## Backend / API
| Technology | Why |
|---|---|
| **FastAPI** | Exposes the two required endpoints — `POST /api/agent/init` and `GET /api/agent/feed` — with async handling and auto-generated OpenAPI docs. |
| **Python** | Implementation language for research, editorial-judgment, drafting, and memory read/write logic. |
| **Pydantic** | Validates the init payload (persona, domain) and the feed response schema (id, createdAt, text, rationale, sources). |
| **Uvicorn** | ASGI server running the FastAPI app during the 48-hour unattended evaluation window. |

## AI / LLM
| Technology | Why |
|---|---|
| **OpenAI API** | Powers topic normalization, editorial scoring, the 3-draft internal tournament, self-critique, persona checks, and final post text generation. |
| **JSON / structured output mode** | Forces the LLM to return machine-parseable topic scores, draft rankings, and rationale objects the backend can store directly, instead of free text. |

## Agent Orchestration
| Technology | Why |
|---|---|
| **APScheduler (in-process)** | Runs the background scheduler inside the FastAPI process — triggers each research/publish cycle on an interval with zero human input across the 48 hours. |
| **Custom async retry pipeline** | Each activity has configurable retry policies (max attempts, backoff, non-retryable errors) matching the original Temporal RetryPolicy semantics. |

## Database & Storage
| Technology | Why |
|---|---|
| **PostgreSQL** | Authoritative store for the agent record, persona/constitution config, published posts, and timestamps returned by `GET /api/agent/feed`. |
| **SQLAlchemy + Alembic** | ORM and schema migrations for the `agent`, `posts`, and `feed` tables. |

## Vector Database / Memory
| Technology | Why |
|---|---|
| **Breeth Memory** | Long-term memory graph storing stories, beliefs, predictions, rejected topics, concepts, claims, and past editorial decisions; queried via `POST /v1/search` before judgment, written via `POST /v1/episodes` after publishing. |

## Authentication
| Technology | Why |
|---|---|
| **Clerk** | Authenticates the one-time `POST /api/agent/init` call and gates any admin/demo views on the Next.js frontend. |

## External APIs / Integrations
| Technology | Why |
|---|---|
| **Exa** | Semantic/live web search feeding the discovery worker with AI/tech news, papers, and advisories as candidate topics. |
| **Tavily** | Secondary search API used for topic discovery and cross-checking sources before editorial scoring. |
| **RSS feeds / blog & GitHub APIs** | Additional live sources (releases, advisories, blog posts) feeding the "Live Web Discovery" stage alongside Exa/Tavily. |

## Infrastructure / Deployment
| Technology | Why |
|---|---|
| **Docker** | Containerizes the FastAPI backend and Postgres for consistent deployment during evaluation. |
| **Vercel** | Deploys the Next.js feed-viewer frontend. |
| **Railway / Fly.io / Render** *(one host)* | Runs the FastAPI service and Postgres instance. No separate workflow engine needed — APScheduler runs in-process. |

## Monitoring / Logging
| Technology | Why |
|---|---|
| **Structured JSON logging (Python `logging`)** | Captures editorial decisions (accept/reject scores, rejection reasons), Breeth read/write calls, and APScheduler job events, replacing the Temporal Web UI for observability. |
| **Sentry** | Error tracking for the FastAPI service and background worker so failures during the unattended run are caught and traceable. |
