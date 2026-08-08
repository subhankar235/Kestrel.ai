# BACKEND_STEPS.md — Autonomous AI Creator Agent
### Complete Backend Implementation Playbook (Zero → Production)

This document is the sequential build guide for `backend/` as defined in `PRD.md`, `TECH_STACK.md`, and `backend/STRUCTURE.md`. Follow phases in order — each phase assumes all prior phases are complete.

Stack in use: **FastAPI, Python, Pydantic, Uvicorn, SQLAlchemy + Alembic, PostgreSQL, Temporal + Temporal Schedules, OpenAI API, Breeth Memory, Exa, Tavily, RSS/GitHub APIs, Clerk, Docker, Sentry.**

---

## Phase 1 — Backend Architecture Overview

**Goal:** Establish shared understanding of the system before writing code.

**Architecture summary:**
- FastAPI exposes exactly two evaluator-facing routes: `POST /api/agent/init`, `GET /api/agent/feed`.
- `POST /api/agent/init` creates the agent/persona/constitution rows in Postgres and starts a Temporal Workflow (`agent_workflow.py`) which runs the autonomous discover → recall → judge → draft → publish → write-back cycle on a recurring `Temporal Schedule`, unattended, for the ~48h evaluation window.
- Postgres is the **system of record** for agent, posts, and feed (what the API returns).
- Breeth is the **associative long-term memory** the agent reasons over (stories, beliefs, predictions, rejected topics, concepts) — read via `POST /v1/search`, written via `POST /v1/episodes`.
- OpenAI powers topic normalization, scoring, drafting, self-critique, persona checks, and rationale generation, all in JSON structured-output mode.
- No further human input occurs after init; the Temporal worker is the sole driver of new activity.

**Expected result:** Team agreement on module boundaries in `backend/app/` matching `backend/STRUCTURE.md` before any code is written.

---

## Phase 2 — Backend Project Initialization

**Goal:** Create an empty, installable Python project skeleton.

**Prerequisites:** Python 3.11+, Git repo initialized at root, `backend/` folder exists per project structure.

**Files/folders to create:**
```
backend/
├── app/__init__.py
├── app/main.py
├── pyproject.toml
├── requirements.txt
├── Dockerfile
├── .env.example
├── tests/__init__.py
├── tests/unit/__init__.py
├── tests/integration/__init__.py
└── tests/conftest.py
```

**Dependencies:** none yet — this step only scaffolds folders and `pyproject.toml` metadata (name, version, python requirement).

**Implementation:** Initialize with `uv init` or `poetry init` (either works with `pyproject.toml`); set `requires-python = ">=3.11"`. Create empty `app/__init__.py` files for every subpackage as they're added later.

**Verification:** `python -c "import app"` succeeds from `backend/`.

**Expected result:** An empty but importable Python package, independent of the Bun/Next.js workspace (per `STRUCTURE.md`, backend is managed independently via `pyproject.toml`).

---

## Phase 3 — Environment / Configuration Setup

**Goal:** Define every environment variable the backend needs before any service integration is coded.

**Files to create:** `backend/.env.example`

**Configuration (all vars, required vs optional):**

| Variable | Required for | Local dev | Production |
|---|---|---|---|
| `DATABASE_URL` | Postgres connection | Required | Required |
| `OPENAI_API_KEY` | LLM calls (scoring, drafting, rationale) | Required | Required |
| `BREETH_API_KEY` | Memory search/episodes | Required | Required |
| `BREETH_BASE_URL` | Breeth API host | Required | Required |
| `EXA_API_KEY` | Live web discovery | Required | Required |
| `TAVILY_API_KEY` | Secondary discovery/cross-check | Optional (discovery degrades to Exa+RSS+GitHub only) | Required |
| `GITHUB_TOKEN` | Higher rate limits on GitHub discovery source | Optional | Recommended |
| `RSS_FEED_URLS` | Comma-separated list of RSS sources | Required | Required |
| `TEMPORAL_ADDRESS` | Temporal server host:port | Required | Required |
| `TEMPORAL_NAMESPACE` | Workflow namespace | Required | Required |
| `TEMPORAL_TASK_QUEUE` | Worker task queue name | Required | Required |
| `CLERK_SECRET_KEY` | Auth-guarding `/api/agent/init` | Required | Required |
| `CLERK_PUBLISHABLE_KEY` | Frontend/Clerk handshake (backend just verifies) | Required | Required |
| `SENTRY_DSN` | Error tracking | Optional | Required |
| `ENVIRONMENT` | `local` / `staging` / `production` | Required | Required |
| `PORT` | Uvicorn port (default 8000) | Optional | Required |
| `PUBLISH_CYCLE_INTERVAL_MINUTES` | Temporal Schedule cadence | Required | Required |
| `EDITORIAL_ACCEPT_THRESHOLD` | Score cutoff for accept/reject | Required | Required |

**Where to obtain keys:**
- `OPENAI_API_KEY`: platform.openai.com → API keys.
- `BREETH_API_KEY` / `BREETH_BASE_URL`: Breeth account dashboard.
- `EXA_API_KEY`: exa.ai dashboard.
- `TAVILY_API_KEY`: tavily.com dashboard.
- `GITHUB_TOKEN`: GitHub → Settings → Developer settings → Personal access tokens (read-only, public repos scope).
- `CLERK_SECRET_KEY` / `CLERK_PUBLISHABLE_KEY`: Clerk dashboard → API Keys.
- `SENTRY_DSN`: Sentry project settings.

**Security:** `.env` (real values) is git-ignored; only `.env.example` (placeholder values) is committed. Never hardcode secrets in `config.py` or prompts.

**Verification:** `backend/.env.example` lists every variable above with placeholder values and inline comments.

---

## Phase 4 — Dependency Installation

**Goal:** Install every library the tech stack calls for.

**Prerequisites:** Phase 2 complete.

**Dependencies (add to `pyproject.toml` / `requirements.txt`):**
```
fastapi
uvicorn[standard]
pydantic
pydantic-settings
sqlalchemy
alembic
psycopg2-binary          # or asyncpg if using async SQLAlchemy engine
openai
temporalio                # Temporal Python SDK
httpx                     # Breeth / Exa / Tavily / GitHub / RSS HTTP calls
feedparser                 # RSS parsing
clerk-backend-api          # or manual JWT verification via PyJWT + Clerk JWKS
python-jose[cryptography]  # JWT verification fallback
sentry-sdk[fastapi]
pytest
pytest-asyncio
httpx[testing]             # TestClient / async test client
ruff
black
```

**Implementation:** `pip install -r requirements.txt` (or `poetry install` / `uv sync`). Pin versions once confirmed compatible; commit the lockfile.

**Verification:** `uvicorn app.main:app --reload` boots without `ModuleNotFoundError`.

---

## Phase 5 — Application Entry Point

**Goal:** Minimal FastAPI app that boots and responds to a health check.

**Files:** `backend/app/main.py`

**Implementation:**
- Instantiate `FastAPI()`.
- Register CORS middleware (allow frontend origin from config).
- Register Sentry middleware if `SENTRY_DSN` set.
- Add a `GET /health` route returning `{"status": "ok"}` (not part of the evaluator contract, but needed for deploy health checks).
- Mount routers (added in Phase 12) — leave placeholder imports commented until routers exist.
- On `startup` event: verify DB connectivity; do **not** start Temporal workflows here (workflows are started per-agent from `POST /api/agent/init`, not globally).

**Security:** CORS restricted to known frontend origin(s) from config, not `*`, in production.

**Testing:** `tests/integration/test_health.py` — `GET /health` returns 200.

**Verification:** `curl localhost:8000/health` → `{"status":"ok"}`.

**Expected result:** A running, empty FastAPI service.

---

## Phase 6 — Configuration and Settings Layer

**Goal:** Centralize all env vars from Phase 3 into a typed settings object.

**Files:** `backend/app/core/config.py`

**Implementation:** `Settings(BaseSettings)` (pydantic-settings) reading from `.env`, one field per variable in the Phase 3 table, with correct types (`int` for thresholds/intervals, `str` for keys/URLs, `list[str]` for `RSS_FEED_URLS` via a validator splitting on commas). Expose a cached `get_settings()` accessor (`functools.lru_cache`) used everywhere else via FastAPI `Depends`.

**Testing:** unit test asserting `Settings()` raises a clear error when a required var is missing.

**Verification:** `from app.core.config import get_settings; get_settings()` succeeds when `.env` is populated.

---

## Phase 7 — Database Connection

**Goal:** Establish the SQLAlchemy engine/session used by every model and route.

**Prerequisites:** `DATABASE_URL` set; local Postgres running (via `infra/docker-compose.yml`).

**Files:** `backend/app/db/session.py`, `backend/app/db/base.py`

**Implementation:**
- `db/base.py`: `Base = declarative_base()`, imported by every model so Alembic can discover metadata.
- `db/session.py`: `engine = create_engine(settings.DATABASE_URL)`, `SessionLocal = sessionmaker(bind=engine)`, and a `get_db()` generator dependency for FastAPI routes (yield session, close in `finally`).

**Configuration:** `DATABASE_URL` format: `postgresql://user:pass@host:5432/dbname`.

**Security:** DB credentials only via env var, never committed; use a least-privilege DB user in production.

**Testing:** `tests/integration/conftest.py` fixture spins up a test DB session (SQLite in-memory or a disposable Postgres schema) and overrides `get_db`.

**Verification:** A throwaway script opens a session and runs `SELECT 1`.

---

## Phase 8 — Database Models / Schema

**Goal:** Define the Postgres system-of-record tables.

**Prerequisites:** Phase 7 complete.

**Files:** `backend/app/models/agent.py`, `persona.py`, `post.py`, `constitution.py`, `topic_debt.py`

**Database changes:**

- **`agents`**: `id (UUID, pk)`, `agent_id (str, unique, returned to evaluator)`, `created_at`, `status (active/stopped)`, `temporal_workflow_id`.
- **`personas`**: `id (pk)`, `agent_id (fk → agents)`, `name`, `domain`, `voice_config (JSONB)` (tone, interests, editorial opinions), `created_at`.
- **`posts`**: `id (pk, exposed as string post id e.g. "p7")`, `agent_id (fk)`, `created_at (timestamptz)`, `text`, `rationale`, `sources (JSONB array of URLs)`, `related_post_id (fk → posts, nullable)`, `relationship (enum: STORY_CONTINUATION, PREDICTION_RESOLUTION, TOPIC_RESURRECTION, CONCEPT_GAP, nullable)`, `immutable = true by convention (no update endpoint exposed)`.
- **`constitutions`**: `id (pk)`, `agent_id (fk)`, `version (str, e.g. "1.0")`, `rules (JSONB)`, `created_at`, `is_active (bool)`.
- **`topic_debt`**: `id (pk)`, `agent_id (fk)`, `topic_title`, `topic_summary`, `score`, `rejection_reason`, `revisit_condition`, `status (open/resurrected)`, `created_at`.

**Indexes:** `posts(agent_id, created_at DESC)` for feed ordering; `agents(agent_id)` unique index; `topic_debt(agent_id, status)`.

**Implementation:** Each model inherits `Base`; relationships declared with `relationship()` + `ForeignKey`. Use `UUID` primary keys (`uuid4` default) but keep a separate human-facing `agent_id`/`post_id` string column since the API contract expects opaque string IDs (`"abc-123"`, `"p7"`), not raw UUIDs.

**Testing:** unit tests instantiate each model against the test DB and assert round-trip persistence.

**Verification:** `Base.metadata.create_all(engine)` on a scratch DB creates all five tables without error.

---

## Phase 9 — Migrations

**Goal:** Version-controlled schema evolution via Alembic.

**Prerequisites:** Phase 8 models exist.

**Files:** `backend/alembic.ini`, `backend/app/migrations/env.py`, `backend/app/migrations/versions/0001_init.py`

**Implementation:** `alembic init app/migrations`, point `env.py`'s `target_metadata` at `app.db.base.Base.metadata`, set `sqlalchemy.url` from `settings.DATABASE_URL` at runtime (not hardcoded in `alembic.ini`). Generate the first migration: `alembic revision --autogenerate -m "init schema"`.

**Seed data:** Optional `seed_personas.py` (Phase 15) is applied at runtime by `POST /api/agent/init`, not via migration — migrations only create structure.

**Verification:** `alembic upgrade head` against a clean DB creates all tables; `alembic downgrade base` cleanly drops them.

**Expected result:** Repeatable schema setup for local, staging, and production DBs.

---

## Phase 10 — Authentication and Authorization

**Goal:** Guard the one-time `POST /api/agent/init` call; `GET /api/agent/feed` remains open (evaluator polls it directly, as per the spec's two-endpoint contract — no auth is specified for the feed read).

**Prerequisites:** `CLERK_SECRET_KEY` configured.

**Files:** `backend/app/core/security.py`, `backend/app/api/deps.py`

**Implementation:** `security.py` verifies the Clerk-issued JWT from the `Authorization: Bearer <token>` header against Clerk's JWKS endpoint (via `clerk-backend-api` or manual `python-jose` verification). `deps.py` exposes a `require_auth()` FastAPI dependency applied only to the `init` route.

**API contracts:**
- `POST /api/agent/init` — requires valid Clerk session token. Returns `401` if missing/invalid.
- `GET /api/agent/feed` — no auth required (matches the evaluator contract, which calls it directly with only `agentId`).

**Security:** Never trust `agentId` alone as an auth mechanism for `init` (it doesn't exist yet at that point); only `feed` uses `agentId` as a lookup key. Rate-limit `feed` (Phase 20-adjacent) to prevent abuse even though it's unauthenticated.

**Testing:** integration test asserting `init` without a token returns `401`; with a valid mocked token returns `200`.

**Verification:** Manual call with an invalid token to `/api/agent/init` returns 401; feed works with no token.

---

## Phase 11 — Core Backend Modules / Services

**Goal:** Scaffold every non-route module directory so later phases only fill in logic.

**Files/folders to create (empty modules, per `backend/STRUCTURE.md`):**
```
app/persona/{constitution.py, voice.py, seed_personas.py}
app/discovery/{sources/{exa_client.py, tavily_client.py, rss_client.py, github_client.py}, normalizer.py, discovery_service.py}
app/memory/{breeth_client.py, recall.py, episode_writer.py, behaviors/{story_continuity.py, prediction_update.py, topic_resurrection.py, concept_gap.py}}
app/editorial/{scorer.py, judge.py, topic_debt.py}
app/drafting/{draft_generator.py, self_critique.py, persona_check.py}
app/publishing/{publisher.py, rationale_builder.py}
app/llm/{openai_client.py, prompts/}
app/self_audit/{auditor.py, constitution_versioning.py}
```

**Implementation:** Each file gets a docstring stating its single responsibility (matching the `STRUCTURE.md` table) and an empty function signature. This phase is pure scaffolding so Phases 14–21 have a fixed place to land code — no logic yet.

**Verification:** `python -m compileall app/` succeeds (no syntax errors) across the new empty modules.

---

## Phase 12 — API / Router Layer

**Goal:** Wire the two required HTTP endpoints.

**Prerequisites:** Phases 6–10 complete.

**Files:** `backend/app/api/routes/agent_init.py`, `backend/app/api/routes/agent_feed.py`

**API contracts:**

**`POST /api/agent/init`**
- Auth: Clerk bearer token required.
- Request body: `{"persona": {"name": "Ada", "domain": "AI Security"}}`
- Behavior: validates it hasn't already been called for this deployment (enforce "callable exactly once" — check for any existing `agents` row, or accept a caller-supplied idempotency key); creates `agents`, `personas`, seeds `constitutions` v1.0 row; starts the Temporal Workflow (`agent_workflow.py`) with a `Temporal Schedule` on `TEMPORAL_TASK_QUEUE`.
- Response: `200 {"agentId": "abc-123"}`.
- Errors: `400` invalid persona payload; `401` unauthenticated; `409` if init already called.

**`GET /api/agent/feed?agentId=abc-123`**
- Auth: none.
- Behavior: looks up `agent_id`, queries `posts` ordered `created_at DESC`.
- Response: `200 {"posts": [ {id, createdAt, text, rationale, sources}, ... ]}`; `{"posts": []}` if none exist.
- Errors: `404` if `agentId` unknown; never errors on zero posts.

**Implementation:** Routes stay thin — parse/validate request, call `publishing`/`db` read functions, serialize via schemas (Phase 13), return. No business logic in route files.

**Testing:** integration tests for both routes, including the empty-feed case and the unknown-`agentId` 404 case.

**Verification:** `POST /api/agent/init` with a mocked Clerk token returns an `agentId`; immediately calling `GET /api/agent/feed?agentId=<that id>` returns `{"posts": []}`.

---

## Phase 13 — Request Validation and Response Schemas

**Goal:** Strict Pydantic contracts matching `packages/shared-types` exactly.

**Files:** `backend/app/schemas/agent.py`, `backend/app/schemas/feed.py`, `backend/app/schemas/memory.py`

**Implementation:**
- `agent.py`: `PersonaIn(name: str, domain: str)`, `InitRequest(persona: PersonaIn)`, `InitResponse(agentId: str)`.
- `feed.py`: `PostOut(id: str, createdAt: datetime, text: str, rationale: str, sources: list[str])` with a validator serializing `createdAt` to ISO 8601 UTC (`Z` suffix); `FeedResponse(posts: list[PostOut])`.
- `memory.py`: `BreethSearchRequest`, `BreethSearchResult`, `BreethEpisodeIn` shapes matching Breeth's `/v1/search` and `/v1/episodes` payloads.

**Security:** All inbound fields validated (`name`/`domain` non-empty, length-bounded) to prevent prompt-injection-sized payloads reaching the LLM unchecked.

**Testing:** unit tests asserting `FeedResponse` serializes `createdAt` correctly and rejects malformed `InitRequest` bodies.

**Verification:** OpenAPI docs at `/docs` show both schemas matching the spec's example JSON exactly.

---

## Phase 14 — AI / LLM Provider Integration

**Goal:** A single reusable OpenAI client used by every downstream reasoning step.

**Files:** `backend/app/llm/openai_client.py`, `backend/app/llm/prompts/` (one template file per pipeline step: `normalize.py`, `score.py`, `draft.py`, `critique.py`, `persona_check.py`, `rationale.py`, `self_audit.py`)

**Configuration:** `OPENAI_API_KEY`; choose one model for reasoning/JSON tasks (config value `OPENAI_MODEL`, e.g. a current GPT model — confirm the latest available model name at implementation time rather than hardcoding an assumed one).

**Implementation:** `openai_client.py` wraps `chat.completions` (or `responses`) calls with `response_format={"type": "json_schema", ...}` (structured output) so every caller gets back parsed, typed JSON rather than free text. Centralize retry/backoff (Phase 21) and token/cost logging here. Each `prompts/*.py` file exports a function building the system+user prompt for that step, keeping persona voice/constitution injected as context rather than hardcoded per call.

**Security:** Never interpolate raw, unsanitized web content directly into prompts without truncation/escaping — treat discovered web text as untrusted input (defense against prompt injection from scraped pages).

**Testing:** unit tests mock the OpenAI client and assert prompt-builder functions produce valid, schema-conformant request payloads.

**Verification:** a manual smoke call to `score.py`'s prompt against a fixture topic returns parseable JSON with the expected score fields.

---

## Phase 15 — Agent Architecture and Workflows

**Goal:** Implement the Temporal-driven autonomous cycle — the core of "autonomy."

**Prerequisites:** Phases 11, 14 scaffolded/implemented; `TEMPORAL_ADDRESS` reachable (local Temporal server via `infra/temporal/docker-compose.temporal.yml`).

**Files:** `backend/app/workflows/agent_workflow.py`, `activities.py`, `schedules.py`, `worker.py`; `backend/app/persona/seed_personas.py`, `constitution.py`, `voice.py`

**AI/agent implementation:**
- `agent_workflow.py`: defines `AgentWorkflow` — one cycle = `discover_topics` → `recall_memory` (per candidate) → `run_memory_behaviors` (story continuity / prediction update / concept gap / topic resurrection, Phase 16) → `check_topic_debt` → `editorial_judge` (Phase 18) → branch: reject → `log_topic_debt` + `write_breeth_episode`; accept → `generate_drafts` → `self_critique` → `persona_check` → `publish_post` → `build_rationale` → `write_breeth_episode` → periodically `self_audit` (Phase 21-adjacent, e.g. every N cycles).
- `activities.py`: one Temporal Activity per step above, each a thin call into the corresponding `discovery/`, `memory/`, `editorial/`, `drafting/`, `publishing/` module — activities handle retries/timeouts (Temporal's built-in retry policy), workflow code stays deterministic and side-effect-free.
- `schedules.py`: registers a `Temporal Schedule` at the interval from `PUBLISH_CYCLE_INTERVAL_MINUTES`, so cycles repeat automatically without a human re-triggering anything.
- `worker.py`: process entrypoint (`python -m app.workflows.worker`) that starts a Temporal Worker polling `TEMPORAL_TASK_QUEUE`; run as its own container/process (see Phase 27), separate from the FastAPI process, so it survives independently of API traffic for the full 48h window.
- `persona/seed_personas.py`: builds the initial `personas`/`voice_config` row from the `init` request's `{name, domain}`, applying sensible defaults for tone/interests based on `domain` (e.g. "AI Security" → security-analyst voice).
- `persona/constitution.py`: defines the initial v1.0 rule set (thresholds for relevance/novelty/evidence/persona-fit/timeliness/repetition/hype/memory-relationship) seeded at init.

**Memory/state management:** Workflow state itself is ephemeral (Temporal manages execution history); durable state lives in Postgres (`posts`, `topic_debt`, `constitutions`) and Breeth (episodes). The workflow never holds unbounded in-memory state across cycles — each cycle re-reads what it needs from Postgres/Breeth.

**Configuration:** `TEMPORAL_ADDRESS`, `TEMPORAL_NAMESPACE`, `TEMPORAL_TASK_QUEUE`, `PUBLISH_CYCLE_INTERVAL_MINUTES`.

**Retries:** Temporal Activity `RetryPolicy` (max attempts, backoff coefficient) set per activity — discovery/LLM/Breeth calls get retries; a failed cycle must not crash the worker or block future scheduled cycles (Phase 21 detail).

**Testing:** Temporal's `WorkflowEnvironment` test harness runs `AgentWorkflow` against mocked activities and asserts the reject/accept branches both execute correctly.

**Verification:** starting `worker.py` locally against a dev Temporal server and manually signaling one workflow execution produces exactly one new `posts` row (accept path) or one new `topic_debt` row (reject path).

**Expected result:** After `POST /api/agent/init`, a running Temporal Workflow exists that will keep producing cycles on schedule with zero further external calls — this is what makes the "48-hour unattended" requirement true.

---

## Phase 16 — Memory / State Management (Breeth Integration)

**Goal:** Implement the long-term memory layer that differentiates this agent (story continuity, prediction resolution, topic resurrection, concept-graph gap-filling).

**Prerequisites:** `BREETH_API_KEY`, `BREETH_BASE_URL` configured; Phase 15 workflow scaffolding exists.

**Files:** `backend/app/memory/breeth_client.py`, `recall.py`, `episode_writer.py`, `behaviors/story_continuity.py`, `behaviors/prediction_update.py`, `behaviors/topic_resurrection.py`, `behaviors/concept_gap.py`

**External integrations:**
- `breeth_client.py`: thin `httpx` client wrapping `POST {BREETH_BASE_URL}/v1/search` (recall) and `POST {BREETH_BASE_URL}/v1/episodes` (write-back), authenticated via `Authorization: Bearer {BREETH_API_KEY}`. Handle non-2xx with typed exceptions caught by the calling Activity's retry policy.

**AI/agent implementation:**
- `recall.py`: for each normalized candidate topic, calls `breeth_client.search()` with the topic's entities/claims as the query; interprets results into: relevant stories, relevant beliefs/predictions, relevant rejected topics, relevant concept nodes. Returns a structured `MemoryContext` object consumed by both the behaviors below and `editorial/scorer.py`.
- `behaviors/story_continuity.py`: if `MemoryContext` includes an open story with an unresolved open question the new topic answers, mark the candidate as `STORY_CONTINUATION`, set `related_post_id` to the originating post, compute the next `chapter` number.
- `behaviors/prediction_update.py`: on a recurring check (each cycle, independent of new discovery), query Breeth for predictions whose deadline has passed; run a targeted discovery search to compare prediction vs. outcome; produce a verdict (`correct`/`wrong`/`unclear`) to be published as its own post.
- `behaviors/topic_resurrection.py`: for each new candidate, check `topic_debt` (Postgres) + Breeth's rejection memory; if the candidate's new evidence satisfies the stored `revisit_condition`, re-score and allow publishing, referencing the original rejection in the rationale.
- `behaviors/concept_gap.py`: periodically (config-driven cadence) queries Breeth's concept graph for two concepts previously discussed independently but never connected; if found, generates a new discovery query targeting that connection and feeds it back into the normal candidate pipeline.
- `episode_writer.py`: after every publish (accept) or reject decision, builds the episode payload (`topic, claims, stance, prediction, story, open_question, concepts, sources, related_posts, editorial_decision`) and calls `breeth_client.write_episode()`.

**Database changes:** none new (Breeth is external); `topic_debt` (Phase 8) is the Postgres-side mirror used for fast local lookups without a Breeth round-trip on every cycle.

**Testing:** unit tests mock `breeth_client` and assert each behavior module correctly classifies fixture `MemoryContext` inputs (e.g., a fixture with an open question triggers `STORY_CONTINUATION`).

**Verification:** publish two related fixture topics manually through the pipeline in a test/staging run and confirm the second post's `rationale` correctly references the first via `related_post_id`.

---

## Phase 17 — Vector Database / Knowledge Layer

**Goal:** N/A as a separate component — **Breeth (Phase 16) serves this role** per the tech stack; no additional vector DB is introduced (avoids unnecessary technology per project constraints). This phase is intentionally a no-op beyond Phase 16.

---

## Phase 18 — External API Integrations (Discovery Sources + Editorial Judgment)

**Goal:** Implement live topic discovery and the scoring/accept-reject logic.

**Files:** `backend/app/discovery/sources/{exa_client.py, tavily_client.py, rss_client.py, github_client.py}`, `normalizer.py`, `discovery_service.py`, `backend/app/editorial/{scorer.py, judge.py, topic_debt.py}`

**External integrations:**
- `exa_client.py`: `httpx` POST to Exa's search endpoint, authenticated via `EXA_API_KEY`, queried with domain-relevant terms derived from the persona (`domain`).
- `tavily_client.py`: same pattern with `TAVILY_API_KEY`; used for cross-checking sources found via Exa (skip gracefully if key absent, per Phase 3's optional flag).
- `rss_client.py`: `feedparser` over `RSS_FEED_URLS`.
- `github_client.py`: GitHub REST API (releases/repos search), authenticated via `GITHUB_TOKEN` if present, unauthenticated otherwise (lower rate limit).
- `discovery_service.py`: fans out to all four sources concurrently (`httpx.AsyncClient` + `asyncio.gather`), deduplicates near-identical results, hands raw results to `normalizer.py`.
- `normalizer.py`: LLM call (via `llm/prompts/normalize.py`) turning raw source text into a `Topic{title, summary, claims, entities, sources, timestamp}`.

**AI/agent implementation (editorial):**
- `scorer.py`: LLM call (via `llm/prompts/score.py`) taking `Topic + MemoryContext + active constitution rules` and returning structured scores for relevance, novelty, evidence, persona fit, timeliness, repetition penalty, hype penalty, memory relationship.
- `judge.py`: compares the weighted score total to `EDITORIAL_ACCEPT_THRESHOLD` from the active constitution version; returns `ACCEPT`/`REJECT` plus the reasoning text.
- `topic_debt.py`: on reject, persists a `topic_debt` row with `rejection_reason` and an LLM-proposed `revisit_condition`.

**Configuration:** `EXA_API_KEY`, `TAVILY_API_KEY` (optional), `GITHUB_TOKEN` (optional), `RSS_FEED_URLS`, `EDITORIAL_ACCEPT_THRESHOLD`.

**Security:** all outbound discovery requests timeout-bounded; never forward evaluator/API credentials to third-party discovery calls.

**Testing:** unit tests with fixture HTTP responses for each source client (via `httpx` mock transport); unit tests for `judge.py` asserting a low-score fixture topic is rejected and a high-score one is accepted.

**Verification:** run `discovery_service.py` standalone against live keys in a dev shell and confirm it returns ≥1 normalized `Topic` from real sources.

---

## Phase 19 — Background Jobs / Events / Webhooks

**Goal:** Confirm the recurring cadence and any secondary scheduled behaviors beyond the primary publish cycle.

**Prerequisites:** Phase 15 (`schedules.py`) implemented.

**Implementation:** The primary background job **is** the Temporal Schedule from Phase 15 — no separate cron/webhook system is introduced (avoids unnecessary technology). Secondary scheduled checks (prediction-deadline sweep from Phase 16, self-audit from Phase 21) run as additional Activities inside the same scheduled workflow cycle, gated by their own cadence config (e.g., self-audit every Nth cycle) rather than separate schedules, to keep orchestration in one place.

**Configuration:** `PUBLISH_CYCLE_INTERVAL_MINUTES` (primary cadence), `SELF_AUDIT_EVERY_N_CYCLES` (secondary cadence, add to `config.py`).

**Verification:** Temporal Web UI shows the Schedule firing on the configured interval with no manual triggers.

---

## Phase 20 — Business Logic (Drafting, Persona Check, Publishing)

**Goal:** Implement the accept-path pipeline: draft tournament → persona check → publish → rationale.

**Files:** `backend/app/drafting/{draft_generator.py, self_critique.py, persona_check.py}`, `backend/app/publishing/{publisher.py, rationale_builder.py}`

**AI/agent implementation:**
- `draft_generator.py`: LLM call (`llm/prompts/draft.py`) generating 3 distinct angles (e.g., news / analysis / prediction) for an accepted topic, each as a full post draft.
- `self_critique.py`: LLM call (`llm/prompts/critique.py`) scoring each draft on voice, novelty, evidence, memory continuity, repetition; selects the winner; logs the losing drafts' scores for observability (not published).
- `persona_check.py`: LLM call (`llm/prompts/persona_check.py`) verifying the winning draft matches `voice_config` and prior beliefs from `MemoryContext`; can veto and trigger a redraft (bounded retry, e.g. max 2 redraft attempts before falling back to `topic_debt`).
- `rationale_builder.py`: LLM call (`llm/prompts/rationale.py`) producing the required `rationale` string — why selected, why relevant now, and (per Phase 16) the memory relationship if applicable — plus the `sources` list carried through from the original `Topic`.
- `publisher.py`: writes the final immutable `posts` row (Phase 8 schema) via SQLAlchemy; sets `related_post_id`/`relationship` when a memory behavior applies.

**Database changes:** none new — writes to `posts` (Phase 8).

**Testing:** unit tests for `self_critique.py`'s winner-selection logic against fixture draft scores; integration test running the full accept path against a fixture topic and asserting a `posts` row is created with all five required fields populated.

**Verification:** manually trigger one workflow cycle in a dev environment and confirm `GET /api/agent/feed` returns the new post with non-empty `rationale` and `sources`.

---

## Phase 21 — Error Handling and Retry Strategy

**Goal:** Ensure one failed step never halts the 48-hour autonomous run.

**Files:** touches `backend/app/workflows/activities.py`, `backend/app/core/logging.py`, all external-client modules.

**Implementation:**
- Every Temporal Activity declares a `RetryPolicy` (initial interval, backoff coefficient, max attempts, non-retryable error types e.g. `401` auth errors).
- Wrap all external client calls (`openai_client`, `breeth_client`, `exa_client`, `tavily_client`, `github_client`, `rss_client`) in typed exceptions distinguishing retryable (timeouts, 5xx) from non-retryable (bad request, auth) failures.
- If an entire cycle's discovery step fails after retries, the workflow logs and skips to the next scheduled cycle rather than crashing the Workflow execution (use Temporal's `try/except` around Activity calls inside the Workflow, not letting exceptions propagate uncaught).
- `self_audit.py` (Phase 15/21) itself must be fault-tolerant: a failed audit skips constitution versioning for that cycle without blocking publishing.

**Testing:** unit test simulating a discovery-source timeout and asserting the workflow still completes the cycle (empty candidate set) without raising.

**Verification:** intentionally revoke one API key in a staging run and confirm the worker logs the failure, Sentry captures it, and subsequent scheduled cycles still fire.

---

## Phase 22 — Logging and Observability

**Goal:** Make every editorial decision and memory interaction inspectable, per PRD's "Transparency" NFR.

**Files:** `backend/app/core/logging.py`, integrated into `editorial/judge.py`, `memory/recall.py`, `memory/episode_writer.py`, `self_audit/auditor.py`

**Implementation:** structured JSON logging (Python `logging` + a JSON formatter) emitting one log line per: discovery batch size, editorial accept/reject with scores and reasoning, Breeth search/episode calls with latency, self-audit findings and constitution version bumps. Sentry (`SENTRY_DSN`) captures unhandled exceptions from both the FastAPI process and the Temporal worker process.

**Configuration:** `SENTRY_DSN`, `ENVIRONMENT` (tags Sentry events by env).

**Verification:** run one full cycle locally and confirm log output contains a traceable line for each pipeline stage; trigger a deliberate exception and confirm it appears in Sentry.

---

## Phase 23 — Unit Tests

**Goal:** Isolated tests for pure-logic modules.

**Files:** `backend/tests/unit/*`

**Coverage required:** `scorer.py` scoring math, `judge.py` accept/reject boundary at threshold, `rationale_builder.py` output shape, `recall.py` `MemoryContext` interpretation, each `behaviors/*.py` classification logic, `self_critique.py` winner selection, schema validators in `schemas/*.py`.

**Verification:** `pytest tests/unit -q` passes with no external network calls (all HTTP clients mocked).

---

## Phase 24 — Integration / API Tests

**Goal:** Test routes against a real (test) DB with mocked external services.

**Files:** `backend/tests/integration/*`

**Coverage required:** `POST /api/agent/init` happy path + 401 + 409 (double-init); `GET /api/agent/feed` happy path, empty-posts case, unknown-`agentId` 404; end-to-end reject path (candidate → `topic_debt` row, no post); end-to-end accept path (candidate → `posts` row visible via feed).

**Verification:** `pytest tests/integration -q` passes against a disposable test Postgres schema (via `conftest.py` fixtures), with `openai_client`, `breeth_client`, and all discovery clients mocked.

---

## Phase 25 — End-to-End Testing

**Goal:** Validate the full unattended loop against real (or realistic sandbox) external services.

**Implementation:** Stand up the full local stack (`docker-compose.yml`: Postgres, Temporal, backend, worker). Call `POST /api/agent/init` once with a real Clerk token. Let the worker run for several scheduled cycles (shorten `PUBLISH_CYCLE_INTERVAL_MINUTES` for the test, e.g. to 2 minutes). Poll `GET /api/agent/feed` repeatedly and confirm: new posts appear over time without further calls, at least one topic was rejected (visible in logs/`topic_debt`), rationale/sources are present on every post, a second related post correctly references a first via `related_post_id` if a story-continuation fixture surfaces.

**Verification:** a checklist run matching the evaluator's exact workflow (init once, poll feed repeatedly) succeeds end-to-end.

---

## Phase 26 — Local Development Workflow

**Goal:** One-command local bring-up.

**Implementation:** `docker-compose.yml` (root, delegating to `infra/docker/`) starts Postgres, Temporal server, `backend` (Uvicorn), `worker` (Temporal worker), each with `.env` mounted. Document commands:
```
docker compose up -d postgres temporal
alembic upgrade head
uvicorn app.main:app --reload
python -m app.workflows.worker
```

**Verification:** a fresh clone + `docker compose up` + the commands above results in a working local stack in under ~10 minutes.

---

## Phase 27 — Docker / Containerization

**Goal:** Separate images for API and worker, since the worker must run independently for 48h.

**Files:** `infra/docker/backend.Dockerfile`, `infra/docker/worker.Dockerfile`

**Implementation:** Both images share a base (Python + installed deps via multi-stage build). `backend.Dockerfile` `CMD` runs `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. `worker.Dockerfile` `CMD` runs `python -m app.workflows.worker`. Neither image bakes in secrets — all via runtime env vars.

**Verification:** `docker build` succeeds for both; `docker run` the backend image responds on `/health`; the worker image connects to a reachable Temporal address and logs a successful poll.

---

## Phase 28 — Production Configuration

**Goal:** Harden config for the unattended evaluation window.

**Implementation:** `ENVIRONMENT=production`; Sentry enabled; CORS restricted to the deployed frontend origin; Postgres connection pooling sized for one API instance + one worker instance; Temporal Cloud or a self-hosted Temporal server reachable from both containers; secrets injected via the host platform's secret manager (Railway/Fly/Render), never baked into images.

**Security:** rotate `CLERK_SECRET_KEY`/`OPENAI_API_KEY`/`BREETH_API_KEY` if ever exposed; ensure the DB user has only the privileges the app needs (no superuser).

**Verification:** a staging deploy with production-equivalent config passes the Phase 25 end-to-end run.

---

## Phase 29 — Deployment

**Goal:** Ship backend + worker together (they share workflow code), independent of frontend deploys.

**Implementation:** `infra/ci/github-actions/backend-ci.yml` — lint (`ruff`, `black --check`), test (`pytest`), build both Docker images. `infra/ci/github-actions/deploy.yml` — on merge to main, push images and deploy `backend` + `worker` to the chosen host (Railway/Fly/Render) alongside the managed Postgres instance and Temporal (Cloud or self-hosted per `infra/temporal/`). Run `alembic upgrade head` as a release/pre-deploy step, not inside the app's startup path, so migrations are explicit and auditable.

**Verification:** a merge to main triggers CI → both images build → deploy succeeds → `GET /health` on the deployed backend returns 200 → Temporal Web UI shows the worker connected to the production task queue.

---

## Phase 30 — Final Backend Verification Checklist

Run this checklist against the deployed environment before evaluation begins.

### Complete backend file checklist
- [ ] `app/main.py`, `app/core/{config,security,logging}.py`
- [ ] `app/models/{agent,persona,post,constitution,topic_debt}.py`
- [ ] `app/schemas/{agent,feed,memory}.py`
- [ ] `app/db/{session,base}.py`, `app/migrations/` (Alembic)
- [ ] `app/persona/{constitution,voice,seed_personas}.py`
- [ ] `app/discovery/sources/{exa,tavily,rss,github}_client.py`, `normalizer.py`, `discovery_service.py`
- [ ] `app/memory/{breeth_client,recall,episode_writer}.py`, `behaviors/{story_continuity,prediction_update,topic_resurrection,concept_gap}.py`
- [ ] `app/editorial/{scorer,judge,topic_debt}.py`
- [ ] `app/drafting/{draft_generator,self_critique,persona_check}.py`
- [ ] `app/publishing/{publisher,rationale_builder}.py`
- [ ] `app/llm/openai_client.py`, `app/llm/prompts/*`
- [ ] `app/workflows/{agent_workflow,activities,schedules,worker}.py`
- [ ] `app/self_audit/{auditor,constitution_versioning}.py`
- [ ] `app/api/routes/{agent_init,agent_feed}.py`, `app/api/deps.py`
- [ ] `tests/unit/*`, `tests/integration/*`, `tests/conftest.py`
- [ ] `Dockerfile`(s), `alembic.ini`, `pyproject.toml`, `.env.example`

### Required environment variables checklist
`DATABASE_URL`, `OPENAI_API_KEY`, `BREETH_API_KEY`, `BREETH_BASE_URL`, `EXA_API_KEY`, `TAVILY_API_KEY`, `GITHUB_TOKEN`, `RSS_FEED_URLS`, `TEMPORAL_ADDRESS`, `TEMPORAL_NAMESPACE`, `TEMPORAL_TASK_QUEUE`, `CLERK_SECRET_KEY`, `CLERK_PUBLISHABLE_KEY`, `SENTRY_DSN`, `ENVIRONMENT`, `PORT`, `PUBLISH_CYCLE_INTERVAL_MINUTES`, `EDITORIAL_ACCEPT_THRESHOLD`, `SELF_AUDIT_EVERY_N_CYCLES`.

### Required API keys checklist
- [ ] OpenAI key active with sufficient quota for the full 48h run
- [ ] Breeth key + base URL verified against `/v1/search` and `/v1/episodes`
- [ ] Exa key active
- [ ] Tavily key active (or explicitly running without it)
- [ ] GitHub token (optional but recommended for rate limits)
- [ ] Clerk secret + publishable keys active

### Database setup checklist
- [ ] Postgres reachable from both backend and worker containers
- [ ] `alembic upgrade head` applied
- [ ] Indexes on `posts(agent_id, created_at DESC)` and `agents(agent_id)` confirmed present

### API endpoint checklist
- [ ] `POST /api/agent/init` — auth enforced, returns `{agentId}`, callable-once enforced
- [ ] `GET /api/agent/feed` — reverse-chronological, unique IDs, ISO 8601 UTC timestamps, empty-array default, unknown-agent 404

### Integration checklist
- [ ] Temporal Schedule firing on configured interval (verified in Temporal Web UI)
- [ ] Breeth read/write round-trip verified in staging
- [ ] All four discovery sources returning results in staging
- [ ] Sentry receiving test events from both backend and worker

### Testing checklist
- [ ] `pytest tests/unit -q` passing
- [ ] `pytest tests/integration -q` passing
- [ ] End-to-end shortened-interval run (Phase 25) completed with ≥1 accepted post and ≥1 rejected topic

### Local startup commands
```
docker compose up -d postgres temporal
cd backend
alembic upgrade head
uvicorn app.main:app --reload
python -m app.workflows.worker   # separate terminal
```

### Production readiness checklist
- [ ] Both Docker images built and deployed
- [ ] Migrations applied as an explicit release step
- [ ] CORS restricted to real frontend origin
- [ ] Secrets injected via platform secret manager, not committed
- [ ] Health check passing post-deploy
- [ ] Worker confirmed polling the production Temporal task queue

### Final Build Order
1. Project init → 2. Env/config → 3. Dependencies → 4. Entry point → 5. Settings layer → 6. DB connection → 7. Models → 8. Migrations → 9. Auth → 10. Module scaffolding → 11. Routers → 12. Schemas → 13. LLM client → 14. Temporal workflow/worker skeleton → 15. Breeth memory integration → 16. Discovery sources + editorial scoring → 17. Drafting/persona-check/publishing → 18. Error handling/retries → 19. Logging/observability → 20. Unit tests → 21. Integration tests → 22. End-to-end test run → 23. Local docker-compose validation → 24. Dockerize → 25. Production config → 26. CI/CD deploy → 27. Final verification checklist.
