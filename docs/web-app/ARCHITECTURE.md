# ARCHITECTURE

## System diagram (text)

```
 Browser (vanilla HTML/CSS/JS, app/static/)
        │  fetch() JSON over HTTP
        ▼
 FastAPI app (app/main.py)  ──────────────┐
        │                                  │
        ▼                                  ▼
 app/ingest.py (CSV validate+upsert)  app/ai_workflow.py (OpenRouter chat-completion call)
        │                                  │
        ▼                                  ▼
 app/db.py ── SQLite file (data/awareness.db) ── ai_drafts / ingestion_runs tables
        ▲
        │
 app/analytics.py (status/overdue/completed definitions — single source of truth,
                    used identically by API routes and by the AI draft prompt builder)
```

## Tech stack
- **Backend**: Python 3.12, FastAPI + Uvicorn (ASGI). Chosen for minimal boilerplate to
  ship a JSON API + static file server inside a 120-minute timebox.
- **Storage**: SQLite3 via the Python stdlib `sqlite3` module — no extra server process,
  one file, trivial to bind-mount as a Docker volume. See "Decision: SQLite over DuckDB"
  below.
- **Frontend**: no build step — static HTML/CSS/vanilla JS served directly by FastAPI's
  `StaticFiles`, calling the JSON API with `fetch`. Avoids a Node toolchain for a lab-scale
  dashboard with four cards and three tables.
- **AI integration**: plain `httpx` POST to the company-provided OpenRouter gateway's
  OpenAI-compatible `/chat/completions` endpoint (`AI_API_KEY` / `AI_BASE_URL` / `AI_MODEL`
  from the environment — see `SECURITY.md`). No SDK dependency beyond `httpx`, which the
  project already needs for its own test client.

### Note: extended thinking must be disabled for this workflow
The default model (`anthropic/claude-sonnet-5`) runs extended thinking by default on
OpenRouter. With a bounded `max_tokens`, thinking can consume the entire budget and return
`finish_reason: "length"` with `content: null` — observed directly while building this
feature. Fixed by sending `"reasoning": {"max_tokens": 0, "exclude": true}` in the request
body, and by capping each formatted list to `MAX_LISTED_ITEMS = 20` lines (with an explicit
"...and N more" plus a stated total) so large clients (one test client had 245 accepted
rows) don't blow up prompt size/cost. `generate_draft` raises if `content` still comes back
empty rather than persisting a null draft.

## Decision: SQLite over DuckDB
The exam brief allows either. SQLite is chosen because: (a) it is in the Python stdlib —
zero extra dependency risk under a token/time budget; (b) the workload is point lookups and
small aggregations (~12.5k rows, grouped by client) well within SQLite's comfort zone;
(c) DuckDB's advantage (fast OLAP over large columnar data) is not exercised at this data
scale. Noted as a reasonable alternative, not a wrong one, if the dataset were 100x larger
or the dashboard needed heavier analytical SQL.

## Track choice: ddd-web-app over ddd-data-analytics
The deliverable is an interactive page+API system a person drives directly (filter by
client, read lists, trigger an AI draft) — exactly the `ddd-web-app` template's
`applicable_when`. `ddd-data-analytics` targets BI/pipeline/warehouse-shaped deliverables
(dashboards fed by a modeled semantic layer with SLAs/lineage), which is heavier than this
single-table, single-service lab app needs.

## Reference date handling
`as_of` resolution order, applied identically across every status-sensitive endpoint
(`app/main.py::_default_as_of`):
1. Explicit `?as_of=YYYY-MM-DD` query parameter on the request.
2. `DASHBOARD_AS_OF` environment variable (lets an operator pin "today" server-wide for
   reproducible grading without changing client code).
3. The server's current date (`date.today()`).

`as_of` never mutates stored data — it only changes which rows `analytics.py` counts as
overdue/completed in a given response, keeping ingestion and status computation decoupled.

## Request flow: AI draft update
`POST /api/ai/draft-update?client=X&as_of=Y` → `ai_workflow.generate_draft` calls
`analytics.pending_acceptance/accepted_items/overdue_items` (the same functions the
dashboard UI uses) → formats them into a constrained Thai prompt → calls Claude → persists
the response row in `ai_drafts` → returns it. The model never sees raw CSV rows or an
unfiltered table dump, only the three pre-classified lists for one client.

## Observability (minimal, in scope)
`GET /api/health` for container healthchecks (used by `Dockerfile` HEALTHCHECK and
Coolify). `ingestion_runs` table keeps an audit trail of every ingest call (file name,
counts, error list) queryable directly via `sqlite3 data/awareness.db`.
