
# Autonomous AI Creator Agent

An AI persona that, once initialized, independently discovers AI/tech topics, judges whether they're worth publishing, writes in a consistent voice, remembers its own history, and keeps publishing over time — with **zero human input** after setup.

> "We didn't build an AI that remembers posts. We built an AI whose memory changes what it does next."

## What it does

After a single initialization call, the agent runs autonomously for the full evaluation window (~48 hours):

1. **Discovers** AI/tech topics from live sources (news, papers, GitHub, blogs, advisories, RSS).
2. **Recalls memory** (Breeth) for each candidate — has it covered this before? Made a prediction? Rejected it? Left an open question?
3. **Judges** the topic against an evolving editorial constitution — and can say **no**.
4. **Drafts** 3 angles, self-critiques, and picks a winner.
5. **Checks persona fit** before publishing.
6. **Publishes** with a transparent rationale and sources.
7. **Writes back** to memory so the next cycle can build on it (story continuations, prediction resolutions, topic resurrections, concept-graph gap-filling).
8. **Self-audits** periodically and can version its own editorial rules.

See [`PRD.md`](./PRD.md) for full product requirements and [`TECH_STACK.md`](./TECH_STACK.md) for the technology breakdown.

## Architecture

```
LIVE DISCOVERY → CANDIDATE TOPICS → BREETH SEARCH (memory recall)
   → STORY CONTINUITY / PREDICTION UPDATE / CONCEPT GAP → TOPIC DEBT CHECK
   → EDITORIAL JUDGMENT
        → REJECT → Topic Debt → Breeth
        → ACCEPT → 3 Drafts → Self-Critique → Persona Check
                 → Publish → Rationale + Sources → Write to Breeth
                 → Self-Audit → Evolve Constitution → Next Cycle
```

| Layer | Responsibility |
|---|---|
| Live Web | Discovers what's happening now |
| Breeth | Remembers + connects the agent's history |
| LLM (OpenAI) | Reasons over memory and evidence, drafts, critiques |
| Editorial Constitution | Decides what the persona considers publishable |
| PostgreSQL | Permanent feed/API records |
| Temporal | Runs the autonomous background loop |
| Feed API | What evaluators see |

## Tech Stack

- **Frontend**: Next.js, TypeScript, Tailwind, shadcn/ui, Bun
- **Backend**: FastAPI, Python, Pydantic, Uvicorn
- **AI/LLM**: OpenAI API
- **Orchestration**: Temporal
- **Database**: PostgreSQL
- **Memory**: Breeth
- **Auth**: Clerk
- **Search/Discovery**: Exa, Tavily, RSS/blog/GitHub APIs

Full rationale for each choice is in [`TECH_STACK.md`](./TECH_STACK.md).

## API

### Initialize agent (called once)
```
POST /api/agent/init
Content-Type: application/json

{
  "persona": { "name": "Ada", "domain": "AI Security" }
}
```
Response:
```json
{ "agentId": "abc-123" }
```

### Get feed (polled by evaluator)
```
GET /api/agent/feed?agentId=abc-123
```
Response:
```json
{
  "posts": [
    {
      "id": "p7",
      "createdAt": "2026-08-07T10:30:00Z",
      "text": "...",
      "rationale": "Why this topic was selected, why it's relevant now, and the memory relationship if any.",
      "sources": ["https://..."]
    }
  ]
}
```
Empty feed:
```json
{ "posts": [] }
```

## Getting Started

```bash
# Frontend
bun install
bun run dev

# Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Background worker
temporal server start-dev   # local Temporal server
python -m app.worker        # starts the autonomous cycle
```

Environment variables needed: `OPENAI_API_KEY`, `DATABASE_URL` (Postgres), `BREETH_API_KEY`, `EXA_API_KEY`, `TAVILY_API_KEY`, `CLERK_SECRET_KEY`, `TEMPORAL_ADDRESS`.

## Evaluation Notes

- `POST /api/agent/init` is called **exactly once** by the evaluator.
- `GET /api/agent/feed` is the **only** endpoint polled afterward.
- All posts appearing after init are generated entirely by the autonomous agent — no further prompts are sent.
- Simulated publishing only; no real social media integration required.

## Out of Scope

- Real social media posting (LinkedIn, X, etc.)
- Multi-platform publishing
- Images/videos
- Engagement analytics
- Multi-agent architectures
- Human intervention after initialization

## Docs

- [`PRD.md`](./PRD.md) — problem, goals, features, workflows, functional & non-functional requirements
- [`TECH_STACK.md`](./TECH_STACK.md) — full technology breakdown with rationale per layer
