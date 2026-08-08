# AGENTS.md — Backend (FastAPI + Temporal)

## Prompt Logging

Whenever the user gives you a prompt or instruction related to this backend project, **append the exact raw user prompt to `PROMPTS.md`**.

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

- **Framework:** FastAPI (Python 3.12+)
- **ORM:** SQLAlchemy 2.0+ (async)
- **Migrations:** Alembic
- **Workflows:** Temporal SDK (Python)
- **Memory:** Breeth API integration
- **Search APIs:** Exa, Tavily, RSS, GitHub
- **LLM:** OpenAI API (structured JSON output)
- **Auth:** Clerk token verification

## Coding Conventions

- Use async/await for all I/O-bound operations.
- Pydantic v2 for all schemas (request/response).
- SQLAlchemy 2.0 style (mapped_column, Mapped[]).
- Type hints on all functions and class attributes.
- Structured JSON logging via `core/logging.py`.
- Separate concerns: models (DB), schemas (API), services (logic).

## File Structure

- `app/api/routes/` — HTTP endpoints (keep thin, delegate to services)
- `app/core/` — config, security, logging
- `app/models/` — SQLAlchemy ORM models (system of record)
- `app/schemas/` — Pydantic request/response contracts
- `app/db/` — session factory, declarative base
- `app/persona/` — editorial constitution, voice config, seed personas
- `app/discovery/` — source clients, normalizer, discovery service
- `app/memory/` — Breeth integration, recall, episode writer, behaviors
- `app/editorial/` — scorer, judge, topic debt
- `app/drafting/` — draft generation, self-critique, persona check
- `app/publishing/` — publisher, rationale builder
- `app/llm/` — OpenAI client, prompt templates
- `app/workflows/` — Temporal workflows, activities, schedules, worker
- `app/self_audit/` — auditor, constitution versioning
- `tests/` — unit + integration tests
