# PROMPTS.md — Backend (FastAPI + Temporal)

> All backend-related prompts are logged here.
> At project end, merge into root `PROMPTS.md`.

## Prompt

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

