# PROMPTS.md — Backend (FastAPI + Temporal)

> All backend-related prompts are logged here chronologically per `AGENTS.md`.

## Prompt 1 — Scaffolding & Initial Architecture

```

## Prompt 30 — AGENTS.md Follow-up

```
also folow the agent.md
```

## Prompt 29 — Phase 23 Unit Tests Follow-up

```

## Prompt 31 — Phase 24 Integration / API Tests

```

## Prompt 32 — Phase 30 Final Backend Verification

```
Phase 30 — Final Backend Verification Checklist
Run this checklist against the deployed environment before evaluation begins.

Complete backend file checklist
app/main.py, app/core/{config,security,logging}.py
app/models/{agent,persona,post,constitution,topic_debt}.py
app/schemas/{agent,feed,memory}.py
app/db/{session,base}.py, app/migrations/ (Alembic)
app/persona/{constitution,voice,seed_personas}.py
app/discovery/sources/{exa,tavily,rss,github}_client.py, normalizer.py, discovery_service.py
app/memory/{breeth_client,recall,episode_writer}.py, behaviors/{story_continuity,prediction_update,topic_resurrection,concept_gap}.py
app/editorial/{scorer,judge,topic_debt}.py
app/drafting/{draft_generator,self_critique,persona_check}.py
app/publishing/{publisher,rationale_builder}.py
app/llm/openai_client.py, app/llm/prompts/*
app/workflows/{agent_workflow,activities,schedules,worker}.py
app/self_audit/{auditor,constitution_versioning}.py
app/api/routes/{agent_init,agent_feed}.py, app/api/deps.py
tests/unit/*, tests/integration/*, tests/conftest.py
Dockerfile(s), alembic.ini, pyproject.toml, .env.example

Required environment variables checklist
DATABASE_URL, OPENAI_API_KEY, BREETH_API_KEY, BREETH_BASE_URL, EXA_API_KEY, TAVILY_API_KEY, GITHUB_TOKEN, RSS_FEED_URLS, TEMPORAL_ADDRESS, TEMPORAL_NAMESPACE, TEMPORAL_TASK_QUEUE, CLERK_SECRET_KEY, CLERK_PUBLISHABLE_KEY, SENTRY_DSN, ENVIRONMENT, PORT, PUBLISH_CYCLE_INTERVAL_MINUTES, EDITORIAL_ACCEPT_THRESHOLD, SELF_AUDIT_EVERY_N_CYCLES.

Skip Docker and CI/CD verification for now. Test the remaining backend checklist fully, not partially.

Note: credentials supplied with this prompt were intentionally not copied into this log.
```
Phase 24 — Integration / API Tests
Goal: Test routes against a real (test) DB with mocked external services.

Files: backend/tests/integration/*

Coverage required: POST /api/agent/init happy path + 401 + 409 (double-init); GET /api/agent/feed happy path, empty-posts case, unknown-agentId 404; end-to-end reject path (candidate → topic_debt row, no post); end-to-end accept path (candidate → posts row visible via feed).

Verification: pytest tests/integration -q passes against a disposable test Postgres schema (via conftest.py fixtures), with openai_client, breeth_client, and all discovery clients mocked. now do this
```
Phase 23 — Unit Tests
Goal: Isolated tests for pure-logic modules.

Files: backend/tests/unit/*

Coverage required: scorer.py scoring math, judge.py accept/reject boundary at threshold, rationale_builder.py output shape, recall.py MemoryContext interpretation, each behaviors/*.py classification logic, self_critique.py winner selection, schema validators in schemas/*.py.

Verification: pytest tests/unit -q passes with no external network calls (all HTTP clients mocked). test and imeoemnt...thusfully not just patching...fully imoented now so this fully in my code base
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
│   │       ├── story_continuity.py    # detects/generates story "chapters", sets related_post_id
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
│   │   ├── openai_client.py           # OpenAI API wrapper (structured output mode)
│   │   └── prompts/                   # prompt templates per pipeline step (score, draft, critique...)
│   │
│   ├── workflows/                     # Temporal — the autonomous background loop
│   │   ├── agent_workflow.py          # main cycle: discover -> recall -> judge -> draft -> publish -> write-back
│   │   ├── activities.py              # individual Temporal activities calling modules above
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
├── requirements.txt                   # generated from pyproject.toml
├── Dockerfile
└── .env.example                       # OPENAI_API_KEY, DATABASE_URL, BREETH_API_KEY, EXA/TAVILY keys, TEMPORAL_ADDRESS

create this backend for me
```

## Prompt 2 — Phases 5–9 (Database Connection, ORM Models & Migrations)

```
r..do thus pHASE comeplty,,,,also i added neon url in env iff nnede check frotehre Phase 7 — Database Connection Phase 8 — Database Models / Schema Phase 9 — Migrations
```

## Prompt 3 — Database Execution Confirmation

```
doooo this now fully execute not erroe
```

## Prompt 4 — Neon DB Inspection Instructions

```
nw the db shoudl work data should be saved at db tell me hwo to check at neon?
```

## Prompt 5 — Neon Console SQL Query Details

```
now i can check thirugh neon acutlaapp ? what command or text to aste in neon tell all also what o.p will shown
```

## Prompt 6 — Phase 10 (Authentication & Authorization)

```
Phase 10 — Authentication and Authorization
Goal: Guard the one-time POST /api/agent/init call; GET /api/agent/feed remains open (evaluator polls it directly, as per the spec's two-endpoint contract — no auth is specified for the feed read).

Prerequisites: CLERK_SECRET_KEY configured.

Files: backend/app/core/security.py, backend/app/api/deps.py

Implementation: security.py verifies the Clerk-issued JWT from the Authorization: Bearer <token> header against Clerk's JWKS endpoint (via clerk-backend-api or manual python-jose verification). deps.py exposes a require_auth() FastAPI dependency applied only to the init route.

API contracts:

POST /api/agent/init — requires valid Clerk session token. Returns 401 if missing/invalid.
GET /api/agent/feed — no auth required (matches the evaluator contract, which calls it directly with only agentId).
Security: Never trust agentId alone as an auth mechanism for init (it doesn't exist yet at that point); only feed uses agentId as a lookup key. Rate-limit feed (Phase 20-adjacent) to prevent abuse even though it's unauthenticated.

Testing: integration test asserting init without a token returns 401; with a valid mocked token returns 200.

Verification: Manual call with an invalid token to /api/agent/init returns 401; feed works with no token. now imolen this phase fully in backend..,,later i willadd frotend and cinnect this,,now dont hardcode anytihng any veaer token etcjust add this....fully
```

## Prompt 7 — Phase 11 & Phase 12 (Core Modules Scaffolding & API Router Layer)

```
Phase 11 — Core Backend Modules / Services
Goal: Scaffold every non-route module directory so later phases only fill in logic.

Files/folders to create (empty modules, per backend/STRUCTURE.md):

app/persona/{constitution.py, voice.py, seed_personas.py}
app/discovery/{sources/{exa_client.py, tavily_client.py, rss_client.py, github_client.py}, normalizer.py, discovery_service.py}
app/memory/{breeth_client.py, recall.py, episode_writer.py, behaviors/{story_continuity.py, prediction_update.py, topic_resurrection.py, concept_gap.py}}
app/editorial/{scorer.py, judge.py, topic_debt.py}
app/drafting/{draft_generator.py, self_critique.py, persona_check.py}
app/publishing/{publisher.py, rationale_builder.py}
app/llm/{openai_client.py, prompts/}
app/self_audit/{auditor.py, constitution_versioning.py}
Implementation: Each file gets a docstring stating its single responsibility (matching the STRUCTURE.md table) and an empty function signature. This phase is pure scaffolding so Phases 14–21 have a fixed place to land code — no logic yet.

Verification: python -m compileall app/ succeeds (no syntax errors) across the new empty modules.

Phase 12 — API / Router Layer
Goal: Wire the two required HTTP endpoints.

Prerequisites: Phases 6–10 complete.

Files: backend/app/api/routes/agent_init.py, backend/app/api/routes/agent_feed.py

API contracts:

POST /api/agent/init

Auth: Clerk bearer token required.
Request body: {"persona": {"name": "Ada", "domain": "AI Security"}}
Behavior: validates it hasn't already been called for this deployment (enforce "callable exactly once" — check for any existing agents row, or accept a caller-supplied idempotency key); creates agents, personas, seeds constitutions v1.0 row; starts the Temporal Workflow (agent_workflow.py) with a Temporal Schedule on TEMPORAL_TASK_QUEUE.
Response: 200 {"agentId": "abc-123"}.
Errors: 400 invalid persona payload; 401 unauthenticated; 409 if init already called.
GET /api/agent/feed?agentId=abc-123

Auth: none.
Behavior: looks up agent_id, queries posts ordered created_at DESC.
Response: 200 {"posts": [ {id, createdAt, text, rationale, sources}, ... ]}; {"posts": []} if none exist.
Errors: 404 if agentId unknown; never errors on zero posts.
Implementation: Routes stay thin — parse/validate request, call publishing/db read functions, serialize via schemas (Phase 13), return. No business logic in route files.

Testing: integration tests for both routes, including the empty-feed case and the unknown-agentId 404 case.

Verification: POST /api/agent/init with a mocked Clerk token returns an agentId; immediately calling GET /api/agent/feed?agentId=<that id> returns {"posts": []}.


checl this two workinf or not fullyes stteste or not and tell me
```

## Prompt 8 — Execution Confirmation for Phase 11 & 12

```
doooo fully i wnat no erroe also it shpuld impmneted fully no erroe no patching
```

## Prompt 9 — Phase 13 (Request Validation and Response Schemas)

```
Phase 13 — Request Validation and Response Schemas
Goal: Strict Pydantic contracts matching packages/shared-types exactly.

Files: backend/app/schemas/agent.py, backend/app/schemas/feed.py, backend/app/schemas/memory.py

Implementation:

agent.py: PersonaIn(name: str, domain: str), InitRequest(persona: PersonaIn), InitResponse(agentId: str).
feed.py: PostOut(id: str, createdAt: datetime, text: str, rationale: str, sources: list[str]) with a validator serializing createdAt to ISO 8601 UTC (Z suffix); FeedResponse(posts: list[PostOut]).
memory.py: BreethSearchRequest, BreethSearchResult, BreethEpisodeIn shapes matching Breeth's /v1/search and /v1/episodes payloads.
Security: All inbound fields validated (name/domain non-empty, length-bounded) to prevent prompt-injection-sized payloads reaching the LLM unchecked.

Testing: unit tests asserting FeedResponse serializes createdAt correctly and rejects malformed InitRequest bodies.

Verification: OpenAPI docs at /docs show both schemas matching the spec's example JSON exactly.check this fullu an impemmt
```

## Prompt 10 — Execution Confirmation for Phase 13

```
dooo fulyyy no just patching
```

## Prompt 11 — Phase 14 (AI / LLM Provider Integration & OpenRouter Support)

```
iwill use openroutet api key and model ,,,but u can jeep the pc holdet of open ai...but the actual api kwey willbe openroutet Phase 14 — AI / LLM Provider Integration
Goal: A single reusable OpenAI client used by every downstream reasoning step.

Files: backend/app/llm/openai_client.py, backend/app/llm/prompts/ (one template file per pipeline step: normalize.py, score.py, draft.py, critique.py, persona_check.py, rationale.py, self_audit.py)

Configuration: OPENAI_API_KEY; choose one model for reasoning/JSON tasks (config value OPENAI_MODEL, e.g. a current GPT model — confirm the latest available model name at implementation time rather than hardcoding an assumed one).

Implementation: openai_client.py wraps chat.completions (or responses) calls with response_format={"type": "json_schema", ...} (structured output) so every caller gets back parsed, typed JSON rather than free text. Centralize retry/backoff (Phase 21) and token/cost logging here. Each prompts/*.py file exports a function building the system+user prompt for that step, keeping persona voice/constitution injected as context rather than hardcoded per call.

Security: Never interpolate raw, unsanitized web content directly into prompts without truncation/escaping — treat discovered web text as untrusted input (defense against prompt injection from scraped pages).

Testing: unit tests mock the OpenAI client and assert prompt-builder functions produce valid, schema-conformant request payloads.

Verification: a manual smoke call to score.py's prompt against a fixture topic returns parseable JSON with the expected score fields.
```

## Prompt 12 — Execution Confirmation for Phase 14

```
dooo
```

## Prompt 13 — Testing Query

```
how can i tewdt
```

## Prompt 14 — Phase 15 (Agent Architecture and Workflows)

```
Phase 15 — Agent Architecture and Workflows
Goal: Implement the Temporal-driven autonomous cycle — the core of "autonomy."

Prerequisites: Phases 11, 14 scaffolded/implemented; TEMPORAL_ADDRESS reachable (local Temporal server via infra/temporal/docker-compose.temporal.yml).

Files: backend/app/workflows/agent_workflow.py, activities.py, schedules.py, worker.py; backend/app/persona/seed_personas.py, constitution.py, voice.py

AI/agent implementation:

agent_workflow.py: defines AgentWorkflow — one cycle = discover_topics → recall_memory (per candidate) → run_memory_behaviors (story continuity / prediction update / concept gap / topic resurrection, Phase 16) → check_topic_debt → editorial_judge (Phase 18) → branch: reject → log_topic_debt + write_breeth_episode; accept → generate_drafts → self_critique → persona_check → publish_post → build_rationale → write_breeth_episode → periodically self_audit (Phase 21-adjacent, e.g. every N cycles).
activities.py: one Temporal Activity per step above, each a thin call into the corresponding discovery/, memory/, editorial/, drafting/, publishing/ module — activities handle retries/timeouts (Temporal's built-in retry policy), workflow code stays deterministic and side-effect-free.
schedules.py: registers a Temporal Schedule at the interval from PUBLISH_CYCLE_INTERVAL_MINUTES, so cycles repeat automatically without a human re-triggering anything.
worker.py: process entrypoint (python -m app.workflows.worker) that starts a Temporal Worker polling TEMPORAL_TASK_QUEUE; run as its own container/process (see Phase 27), separate from the FastAPI process, so it survives independently of API traffic for the full 48h window.
persona/seed_personas.py: builds the initial personas/voice_config row from the init request's {name, domain}, applying sensible defaults for tone/interests based on domain (e.g. "AI Security" → security-analyst voice).
persona/constitution.py: defines the initial v1.0 rule set (thresholds for relevance/novelty/evidence/persona-fit/timeliness/repetition/hype/memory-relationship) seeded at init.
Memory/state management: Workflow state itself is ephemeral (Temporal manages execution history); durable state lives in Postgres (posts, topic_debt, constitutions) and Breeth (episodes). The workflow never holds unbounded in-memory state across cycles — each cycle re-reads what it needs from Postgres/Breeth.

Configuration: TEMPORAL_ADDRESS, TEMPORAL_NAMESPACE, TEMPORAL_TASK_QUEUE, PUBLISH_CYCLE_INTERVAL_MINUTES.

Retries: Temporal Activity RetryPolicy (max attempts, backoff coefficient) set per activity — discovery/LLM/Breeth calls get retries; a failed cycle must not crash the worker or block future scheduled cycles (Phase 21 detail).

Testing: Temporal's WorkflowEnvironment test harness runs AgentWorkflow against mocked activities and asserts the reject/accept branches both execute correctly.

Verification: starting worker.py locally against a dev Temporal server and manually signaling one workflow execution produces exactly one new posts row (accept path) or one new topic_debt row (reject path).

Expected result: After POST /api/agent/init, a running Temporal Workflow exists that will keep producing cycles on schedule with zero further external calls — this is what makes the "48-hour unattended" requirement true.


imolemet this fully not partialyy fully imeonet and test no just patching after tll tel me
```

## Prompt 15 — Execution Confirmation for Phase 15

```
dooo fully imolemet this fully not partialyy fully imeonet and test no just patching after tll tel me
```

## Prompt 16 — Phase 16 (Long-Term Memory and Memory Behaviors)

```
nt just patching imoment this ,,,if any api key config file nended tell me...or i will prveded later on,,,for now just imp,ent full code later api key i will give Goal: Implement the long-term memory layer that differentiates this agent (story continuity, prediction resolution, topic resurrection, concept-graph gap-filling).

Prerequisites: BREETH_API_KEY, BREETH_BASE_URL configured; Phase 15 workflow scaffolding exists.

Files: backend/app/memory/breeth_client.py, recall.py, episode_writer.py, behaviors/story_continuity.py, behaviors/prediction_update.py, behaviors/topic_resurrection.py, behaviors/concept_gap.py

External integrations:

breeth_client.py: thin httpx client wrapping POST {BREETH_BASE_URL}/v1/search (recall) and POST {BREETH_BASE_URL}/v1/episodes (write-back), authenticated via Authorization: Bearer {BREETH_API_KEY}. Handle non-2xx with typed exceptions caught by the calling Activity's retry policy.
AI/agent implementation:

recall.py: for each normalized candidate topic, calls breeth_client.search() with the topic's entities/claims as the query; interprets results into: relevant stories, relevant beliefs/predictions, relevant rejected topics, relevant concept nodes. Returns a structured MemoryContext object consumed by both the behaviors below and editorial/scorer.py.
behaviors/story_continuity.py: if MemoryContext includes an open story with an unresolved open question the new topic answers, mark the candidate as STORY_CONTINUATION, set related_post_id to the originating post, compute the next chapter number.
behaviors/prediction_update.py: on a recurring check (each cycle, independent of new discovery), query Breeth for predictions whose deadline has passed; run a targeted discovery search to compare prediction vs. outcome; produce a verdict (correct/wrong/unclear) to be published as its own post.
behaviors/topic_resurrection.py: for each new candidate, check topic_debt (Postgres) + Breeth's rejection memory; if the candidate's new evidence satisfies the stored revisit_condition, re-score and allow publishing, referencing the original rejection in the rationale.
behaviors/concept_gap.py: periodically (config-driven cadence) queries Breeth's concept graph for two concepts previously discussed independently but never connected; if found, generates a new discovery query targeting that connection and feeds it back into the normal candidate pipeline.
episode_writer.py: after every publish (accept) or reject decision, builds the episode payload (topic, claims, stance, prediction, story, open_question, concepts, sources, related_posts, editorial_decision) and calls breeth_client.write_episode().
Database changes: none new (Breeth is external); topic_debt (Phase 8) is the Postgres-side mirror used for fast local lookups without a Breeth round-trip on every cycle.

Testing: unit tests mock breeth_client and assert each behavior module correctly classifies fixture MemoryContext inputs (e.g., a fixture with an open question triggers STORY_CONTINUATION).

Verification: publish two related fixture topics manually through the pipeline in a test/staging run and confirm the second post's rationale correctly references the first via related_post_id.
```

## Prompt 17 — Instruction to Follow AGENTS.md

```
also one tihgn i foget to tell folow the agents.md file in abckend,,,a dn imeoennt
```

## Prompt 18 — Sync All Historical User Prompts to PROMPTS.md

```
also add  all the prev command in promspst .md file folwed by gents .md
```

## Prompt 19 — Phase 18 (External API Integrations: Discovery Sources + Editorial Judgment)

```
Phase 18 — External API Integrations (Discovery Sources + Editorial Judgment)
Goal: Implement live topic discovery and the scoring/accept-reject logic.

Files: backend/app/discovery/sources/{exa_client.py, tavily_client.py, rss_client.py, github_client.py}, normalizer.py, discovery_service.py, backend/app/editorial/{scorer.py, judge.py, topic_debt.py}

External integrations:

exa_client.py: httpx POST to Exa's search endpoint, authenticated via EXA_API_KEY, queried with domain-relevant terms derived from the persona (domain).
tavily_client.py: same pattern with TAVILY_API_KEY; used for cross-checking sources found via Exa (skip gracefully if key absent, per Phase 3's optional flag).
rss_client.py: feedparser over RSS_FEED_URLS.
github_client.py: GitHub REST API (releases/repos search), authenticated via GITHUB_TOKEN if present, unauthenticated otherwise (lower rate limit).
discovery_service.py: fans out to all four sources concurrently (httpx.AsyncClient + asyncio.gather), deduplicates near-identical results, hands raw results to normalizer.py.
normalizer.py: LLM call (via llm/prompts/normalize.py) turning raw source text into a Topic{title, summary, claims, entities, sources, timestamp}.
AI/agent implementation (editorial):

scorer.py: LLM call (via llm/prompts/score.py) taking Topic + MemoryContext + active constitution rules and returning structured scores for relevance, novelty, evidence, persona fit, timeliness, repetition penalty, hype penalty, memory relationship.
judge.py: compares the weighted score total to EDITORIAL_ACCEPT_THRESHOLD from the active constitution version; returns ACCEPT/REJECT plus the reasoning text.
topic_debt.py: on reject, persists a topic_debt row with rejection_reason and an LLM-proposed revisit_condition.
Configuration: EXA_API_KEY, TAVILY_API_KEY (optional), GITHUB_TOKEN (optional), RSS_FEED_URLS, EDITORIAL_ACCEPT_THRESHOLD.

Security: all outbound discovery requests timeout-bounded; never forward evaluator/API credentials to third-party discovery calls.

Testing: unit tests with fixture HTTP responses for each source client (via httpx mock transport); unit tests for judge.py asserting a low-score fixture topic is rejected and a high-score one is accepted.

Verification: run discovery_service.py standalone against live keys in a dev shell and confirm it returns ≥1 normalized Topic from real sources.  now implemt thudNow implement this in the same way as the previous, and for the prompt part, do as the same I say, and also if any API key or any thing needed, tell me, just do the coding part. 
```

## Prompt 20 — Phase 19 (Background Jobs / Events / Webhooks)


```
now imoment this fully...no erroe not just patching imepemnt full 100% no erroe Phase 19 — Background Jobs / Events / Webhooks
Goal: Confirm the recurring cadence and any secondary scheduled behaviors beyond the primary publish cycle.

Prerequisites: Phase 15 (schedules.py) implemented.

Implementation: The primary background job is the Temporal Schedule from Phase 15 — no separate cron/webhook system is introduced (avoids unnecessary technology). Secondary scheduled checks (prediction-deadline sweep from Phase 16, self-audit from Phase 21) run as additional Activities inside the same scheduled workflow cycle, gated by their own cadence config (e.g., self-audit every Nth cycle) rather than separate schedules, to keep orchestration in one place.

Configuration: PUBLISH_CYCLE_INTERVAL_MINUTES (primary cadence), SELF_AUDIT_EVERY_N_CYCLES (secondary cadence, add to config.py).

Verification: Temporal Web UI shows the Schedule firing on the configured interval with no manual triggers.
```

## Prompt 21 — AGENTS.md Follow-up

```
dooo and folow the agnet md in backiend 
```

## Prompt 22 — Phase 20 (Business Logic: Drafting, Persona Check, Publishing)

```
 now imoement this fullyPhase 20 — Business Logic (Drafting, Persona Check, Publishing)
Goal: Implement the accept-path pipeline: draft tournament → persona check → publish → rationale.

Files: backend/app/drafting/{draft_generator.py, self_critique.py, persona_check.py}, backend/app/publishing/{publisher.py, rationale_builder.py}

AI/agent implementation:

draft_generator.py: LLM call (llm/prompts/draft.py) generating 3 distinct angles (e.g., news / analysis / prediction) for an accepted topic, each as a full post draft.
self_critique.py: LLM call (llm/prompts/critique.py) scoring each draft on voice, novelty, evidence, memory continuity, repetition; selects the winner; logs the losing drafts' scores for observability (not published).
persona_check.py: LLM call (llm/prompts/persona_check.py) verifying the winning draft matches voice_config and prior beliefs from MemoryContext; can veto and trigger a redraft (bounded retry, e.g. max 2 redraft attempts before falling back to topic_debt).
rationale_builder.py: LLM call (llm/prompts/rationale.py) producing the required rationale string — why selected, why relevant now, and (per Phase 16) the memory relationship if applicable — plus the sources list carried through from the original Topic.
publisher.py: writes the final immutable posts row (Phase 8 schema) via SQLAlchemy; sets related_post_id/relationship when a memory behavior applies.
Database changes: none new — writes to posts (Phase 8).

Testing: unit tests for self_critique.py's winner-selection logic against fixture draft scores; integration test running the full accept path against a fixture topic and asserting a posts row is created with all five required fields populated.

Verification: manually trigger one workflow cycle in a dev environment and confirm GET /api/agent/feed returns the new post with non-empty rationale and sources.
## Prompt 23 — Phase 20 Follow-up Execution

```
dooo this fully not just patch9ng
```

## Prompt 24 — Phase 21 (Error Handling and Retry Strategy)

```
now imp,emt this fully,,,not just patching ,,fully no erroe no extra erroePhase 21 — Error Handling and Retry Strategy
Goal: Ensure one failed step never halts the 48-hour autonomous run.

Files: touches backend/app/workflows/activities.py, backend/app/core/logging.py, all external-client modules.

Implementation:

Every Temporal Activity declares a RetryPolicy (initial interval, backoff coefficient, max attempts, non-retryable error types e.g. 401 auth errors).
Wrap all external client calls (openai_client, breeth_client, exa_client, tavily_client, github_client, rss_client) in typed exceptions distinguishing retryable (timeouts, 5xx) from non-retryable (bad request, auth) failures.
If an entire cycle's discovery step fails after retries, the workflow logs and skips to the next scheduled cycle rather than crashing the Workflow execution (use Temporal's try/except around Activity calls inside the Workflow, not letting exceptions propagate uncaught).
self_audit.py (Phase 15/21) itself must be fault-tolerant: a failed audit skips constitution versioning for that cycle without blocking publishing.
Testing: unit test simulating a discovery-source timeout and asserting the workflow still completes the cycle (empty candidate set) without raising.

Verification: intentionally revoke one API key in a staging run and confirm the worker logs the failure, Sentry captures it, and subsequent scheduled cycles still fire.
```

## Prompt 25 — Phase 21 Follow-up (AGENTS.md + Full Implementation)

```
dooo and folow the agnet md in backiend 
```

## Prompt 26 — Phase 21 Full Implementation Confirmation

```
 do this fully_
Phase 21 — Error Handling and Retry Strategy
Goal: Ensure one failed step never halts the 48-hour autonomous run.

Files: touches backend/app/workflows/activities.py, backend/app/core/logging.py, all external-client modules.

Implementation:

Every Temporal Activity declares a RetryPolicy (initial interval, backoff coefficient, max attempts, non-retryable error types e.g. 401 auth errors).
Wrap all external client calls (openai_client, breeth_client, exa_client, tavily_client, github_client, rss_client) in typed exceptions distinguishing retryable (timeouts, 5xx) from non-retryable (bad request, auth) failures.
If an entire cycle's discovery step fails after retries, the workflow logs and skips to the next scheduled cycle rather than crashing the Workflow execution (use Temporal's try/except around Activity calls inside the Workflow, not letting exceptions propagate uncaught).
self_audit.py (Phase 15/21) itself must be fault-tolerant: a failed audit skips constitution versioning for that cycle without blocking publishing.
Testing: unit test simulating a discovery-source timeout and asserting the workflow still completes the cycle (empty candidate set) without raising.

Verification: intentionally revoke one API key in a staging run and confirm the worker logs the failure, Sentry captures it, and subsequent scheduled cycles still fire.
```

## Prompt 27 — Phase 22 Full Implementation

```
nowimoemt this fullly test aslo alsofoloow agent.md

Phase 22 — Logging and Observability
Goal: Make every editorial decision and memory interaction inspectable, per PRD's "Transparency" NFR.

Files: backend/app/core/logging.py, integrated into editorial/judge.py, memory/recall.py, memory/episode_writer.py, self_audit/auditor.py

Implementation: structured JSON logging (Python logging + a JSON formatter) emitting one log line per: discovery batch size, editorial accept/reject with scores and reasoning, Breeth search/episode calls with latency, self-audit findings and constitution version bumps. Sentry (SENTRY_DSN) captures unhandled exceptions from both the FastAPI process and the Temporal worker process.

Configuration: SENTRY_DSN, ENVIRONMENT (tags Sentry events by env).

```

## Prompt 28 — Phase 23 Unit Tests

```
Phase 23 — Unit Tests
Goal: Isolated tests for pure-logic modules.

Files: backend/tests/unit/*

Coverage required: scorer.py scoring math, judge.py accept/reject boundary at threshold, rationale_builder.py output shape, recall.py MemoryContext interpretation, each behaviors/*.py classification logic, self_critique.py winner selection, schema validators in schemas/*.py.

Verification: pytest tests/unit -q passes with no external network calls (all HTTP clients mocked). test and imeoemnt...thusfully not just patching...fully imoented
```
