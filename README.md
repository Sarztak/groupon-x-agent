# Groupon X Agent

Autonomous social agent for Groupon's X (Twitter) presence. Monitors mentions, posts deal drops, hooks onto trending topics, and handles customer replies — with a two-pass guardrail system and a human review queue.

## Setup

### Prerequisites

- Python 3.12+ with [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Node.js 18+
- [Claude Code CLI](https://claude.ai/code) installed and authenticated

### Install

```bash
# Python dependencies
uv sync

# Frontend dependencies
cd frontend && npm install && cd ..
```

### Environment

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=sk-...
```

### Run

Start the backend and frontend in separate terminals:

```bash
# Backend
uv run uvicorn server:app --reload --port 8000

# Frontend
cd frontend && npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

## Architecture

| Layer | File | Role |
|---|---|---|
| Input guard | `guardrails.py` | Screens incoming tweets — blocks injections, sensitive topics, competitor traps |
| Orchestrator | `orchestrator.py` | Routes to deal_request / acknowledge / positive_response / off_topic / blocked_reply |
| Copy generation | `marketing_copy.py` | Generates brand-voice copy via Claude |
| Output guard | `guardrails.py` | Reviews draft before posting |
| Router | `router.py` | End-to-end mention handler |
| Server | `server.py` | FastAPI — exposes all agent actions as REST endpoints |

## Demo modes

- **Deal drop** — agent picks a deal from catalog, generates copy, posts
- **Custom deal drop** — paste any `groupon.com/deals/` URL, agent scrapes and generates
- **Trend hook** — agent matches a trending topic to a relevant deal
- **Mention reply** — agent handles an inbound mention end-to-end

## Two-week content plan

Pre-generated plan lives in `two_week_plan/`. To regenerate:

```bash
uv run python generate_two_week_plan.py
```
