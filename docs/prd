# PRD.md — Autonomous AI Creator Agent

## 1. Problem
Most "AI-generated" content on platforms like LinkedIn and X still depends on a human writing the first prompt. Today's LLMs write well but are rarely truly autonomous — they don't independently decide *what* to write about, *whether* it's worth publishing, or *how* it connects to what they've said before. There is no persona-driven agent that discovers topics, judges them, writes in a consistent voice, remembers its own history, and keeps publishing over time without further human input.

## 2. Solution
Build an autonomous AI persona (e.g., an AI Security researcher named "Ada") that, once initialized via a single API call, runs indefinitely in the background. It continuously:
- discovers candidate topics from live sources,
- recalls its own memory (Breeth) to decide if a topic is a continuation, update, resurrection, or genuinely new,
- applies editorial judgment against a self-evolving constitution (and can reject topics),
- drafts multiple angles, self-critiques, and picks a winner,
- checks the draft against its persona,
- publishes with a transparent rationale and sources,
- writes the outcome back into memory so future cycles build on it.

The differentiator: memory doesn't just prevent repetition — it actively changes what the agent chooses to research and publish next (story continuations, prediction resolutions, topic resurrections, concept-graph gap-filling).

## 3. Target Users
- **Evaluators/judges** who initialize the agent once and observe the feed over ~48 hours.
- **End readers** (simulated) who would consume the persona's feed as AI/tech commentary.
- Not a multi-tenant product in this scope — single persona, single agent instance per initialization.

## 4. Goals
- Demonstrate genuine autonomous operation with zero human input after `init`.
- Demonstrate real editorial judgment, including the ability to say **no**.
- Maintain a consistent, recognizable persona and voice throughout.
- Show effective, visible use of long-term memory (continuity, not just storage).
- Make every publishing decision transparent via rationale + sources.
- Publish incrementally over time, not all at once.

## 5. Core Features
1. **Agent Initialization** — one-time setup of persona, editorial constitution, and memory.
2. **Autonomous Topic Discovery** — live web/RSS/API scanning for candidate topics.
3. **Topic Normalization** — structuring each candidate into title, summary, claims, entities, sources, timestamp.
4. **Memory Recall (Breeth Search)** — retrieve relevant stories, beliefs, predictions, rejected topics, concepts, and past decisions for each candidate topic.
5. **Memory-Driven Behaviors**:
   - Story Continuity (generate next "chapter" of an ongoing story)
   - Prediction Resolution (compare past predictions to new evidence, publish verdict)
   - Topic Resurrection (re-evaluate previously rejected topics when new evidence arrives)
   - Concept Graph Gap-Filling (discover and research unexplored links between previously discussed concepts)
6. **Editorial Judgment** — score topics (relevance, novelty, evidence, persona fit, timeliness, repetition penalty, hype penalty, memory relationship) against a threshold; accept or reject.
7. **Topic Debt** — rejected topics are logged with a reason and a revisit condition, not discarded.
8. **Internal Draft Tournament** — generate 3 angles per accepted topic, self-critique each, select a winner.
9. **Persona Consistency Check** — verify the winning draft matches voice, prior beliefs, domain focus, and tone before publishing.
10. **Autonomous Publishing** — posts appear over time via a background worker/schedule, not in a single batch.
11. **Publishing Rationale** — every post explains why it was selected, why it's relevant now, and (when applicable) how it relates to memory (continuation, resolution, resurrection, gap-filling).
12. **Write-Back to Memory** — after publishing, extract topic, claims, stance, prediction, story, open questions, concepts, sources, related posts, and the editorial decision, and store as an episode in Breeth.
13. **Self-Evolving Editorial Constitution** — periodic self-audit of published/rejected history to identify recurring failures and version the constitution's rules (e.g., v1.0 → v1.1).

## 6. User Workflow
Evaluator-facing workflow only (no ongoing human interaction with the agent itself):
1. Evaluator calls `POST /api/agent/init` once with a persona (name, domain).
2. Agent responds with an `agentId`.
3. Agent begins autonomous operation immediately in the background.
4. Over ~48 hours, evaluator periodically calls `GET /api/agent/feed?agentId=...`.
5. Evaluator observes new posts appearing over time, each with text, rationale, and sources.
6. No further prompts or instructions are ever sent to the agent.

## 7. System Behavior
- The agent operates on a recurring autonomous cycle (discovery → memory recall → judgment → draft → publish → write-back → self-audit) that repeats without external triggers.
- Rejected topics do not disappear; they persist as topic debt and can be re-scored later.
- Published posts are immutable historical records; continuations/resolutions/resurrections are published as **new** posts that reference the original (`relatedPostId`, `relationship`, e.g. `STORY_CONTINUATION`).
- The feed always returns previously published posts plus any new ones, in reverse chronological order.
- If no posts exist yet, the feed returns an empty `posts` array — never an error.

## 8. AI / Agent Workflow
```
LIVE DISCOVERY → CANDIDATE TOPICS → BREETH SEARCH (memory recall)
   → [STORY CONTINUITY | PREDICTION UPDATE | CONCEPT GAP] → TOPIC DEBT CHECK
   → EDITORIAL JUDGMENT → REJECT (→ Topic Debt → Breeth) 
                          → ACCEPT (→ 3 Drafts → Self-Critique → Persona Check
                                     → Publish → Rationale + Sources
                                     → Write to Breeth → Self-Audit
                                     → Evolve Constitution) → Next Cycle
```
- **LLM's role**: reasoning over memory + evidence, scoring, drafting, self-critique, persona verification, rationale generation.
- **Memory's role (Breeth)**: long-term store of stories, beliefs, predictions, rejected topics, concepts, claims, relationships, and past editorial decisions; retrieved via search before judgment, updated via episode write after publishing.
- **Constitution's role**: encodes the persona's evolving publishing rules/thresholds; changed only via the self-audit step, and versioned.

## 9. Inputs / Outputs

**Inputs**
- Init request: `{ persona: { name, domain } }`
- Live sources: web search, news, papers, GitHub, blogs, advisories, RSS feeds (agent-initiated, no user input)

**Outputs**
- Init response: `{ agentId }`
- Feed response:
```json
{
  "posts": [
    {
      "id": "p7",
      "createdAt": "2026-08-07T10:30:00Z",
      "text": "...",
      "rationale": "...",
      "sources": ["https://..."]
    }
  ]
}
```
- Empty state: `{ "posts": [] }`

## 10. Integrations
- **Live web/discovery sources**: news, research papers, GitHub, blogs, security advisories, RSS.
- **Breeth**: external long-term memory service, accessed via `POST /v1/search` (recall) and `POST /v1/episodes` (write-back).
- **PostgreSQL**: system of record for agent, posts, feed, and timestamps.
- No real social media platform integration is required (simulated publishing is acceptable).

## 11. Functional Requirements
- FR1: Expose `POST /api/agent/init`, callable exactly once, returning a unique `agentId`.
- FR2: Expose `GET /api/agent/feed?agentId=...` as the only endpoint called afterward.
- FR3: Agent must discover topics from live sources without further human prompting.
- FR4: Agent must be able to reject topics and must actually reject some (demonstrated editorial judgment).
- FR5: Agent must query memory (Breeth) for every candidate topic before making an editorial decision.
- FR6: Agent must support story continuation, prediction resolution, topic resurrection, and concept-graph gap-filling as memory-driven publishing triggers.
- FR7: Agent must generate multiple draft angles per accepted topic and select one via self-critique.
- FR8: Agent must verify persona consistency before publishing.
- FR9: Every published post must include `id`, `createdAt` (ISO 8601 UTC), `text`, `rationale`, and `sources`.
- FR10: Rationale must state why the topic was selected, why it's relevant now, and the memory relationship (when applicable).
- FR11: Previously returned posts must remain available and immutable; new related posts reference them rather than editing them.
- FR12: Feed must return posts in reverse chronological order, with unique IDs, and `{ "posts": [] }` when empty.
- FR13: Agent must write every published post's extracted memory elements back to Breeth.
- FR14: Agent must periodically self-audit its history and be able to version its editorial constitution.
- FR15: Publishing must occur incrementally over the ~48-hour evaluation window, not all at once.

## 12. Non-Functional Requirements
- **Autonomy**: zero human intervention required after `init`; background worker must run unattended for ~48 hours.
- **Availability**: feed endpoint must be queryable at any time during the evaluation window, including with zero posts.
- **Consistency**: persona voice, stance, and domain focus must remain stable across all posts.
- **Transparency**: every editorial decision (accept/reject) and memory relationship must be inspectable via rationale or logs.
- **Data integrity**: published posts are append-only/immutable; historical record must not be altered.
- **Reliability**: the autonomous cycle must tolerate failures in individual steps (discovery, drafting) without halting future cycles.
- **Simplicity of scope**: single persona, single agent per initialization — no multi-tenant or multi-agent coordination required.

## 13. Out of Scope
- Posting to real social media platforms (LinkedIn, X, etc.) — simulated publishing is sufficient.
- Multi-platform publishing.
- Images or videos in posts.
- Engagement analytics.
- Multi-agent architectures.
- Any human intervention or additional prompting after initialization.
