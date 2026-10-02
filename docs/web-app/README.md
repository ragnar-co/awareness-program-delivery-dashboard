# Awareness Program Delivery Dashboard

Tracks Security Awareness Program deliverables (training media, events, reports) across
multiple clients so a program owner can see, before any client meeting, what the team has
finished, what is still waiting on the client to sign off, and what has already slipped past
its due date — without mistaking "sent for review" for "done".

## Doc set (DDD — ddd-web-app track, P0 minimum per central conditions)

This is a 120-minute lab build. Per the exam's "เงื่อนไขกลาง" (central conditions) —
produce the **minimum** documentation for one DDD track — only the **P0** documents of
`ddd-web-app-v2.8.0.json` are written: PERSONAS, CONSTRAINTS, VPD, SCOPE, PRD, ARCHITECTURE,
DATA_MODEL, SECURITY, API_SPEC, AGENTS, TASKS, DEPLOYMENT, TESTING, RUNBOOK, README (this
file). P1 documents (GLOSSARY, ADR, UI_SPEC, TRACKING_PLAN, CHANGELOG) are intentionally
skipped to fit the timebox.

## Quickstart (local)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q                        # run tests
uvicorn app.main:app --reload --port 8000  # serve the app
```

Open http://127.0.0.1:8000 — the dashboard loads empty until a CSV is ingested.

## Loading the deliverables CSV

Either call the API directly:

```bash
curl -F "file=@mukie_awareness_deliverables.csv" http://127.0.0.1:8000/api/ingest
```

or set `DASHBOARD_CSV_PATH=/path/to/file.csv` before starting the server — it auto-seeds
an empty database on first boot (see `DEPLOYMENT.md`).

## Reference date (as_of)

Every status computation (overdue, completed, accepted) is relative to a reference date,
not silently to "now", so results are reproducible. Default = server's current date;
override per request with `?as_of=YYYY-MM-DD`, or pin it server-wide with the
`DASHBOARD_AS_OF` environment variable. See `PRD.md` §Acceptance Criteria and
`ARCHITECTURE.md` §Reference Date Handling.

## Bonus: AI draft client update

Select a client in the UI and click "Generate draft" to produce a Thai-language status
update split into pending-acceptance / accepted / to-follow-up sections, grounded only in
that client's current rows (see `API_SPEC.md` → `POST /api/ai/draft-update`). Requires
`AI_API_KEY` (and optionally `AI_BASE_URL`) to be set — see `SECURITY.md`.

## Project layout

```
app/
  main.py          FastAPI app + routes
  db.py            SQLite schema + connection helper
  ingest.py        CSV validation + upsert
  analytics.py     status/overdue/completed definitions (single source of truth)
  ai_workflow.py   bonus AI draft workflow
  static/          vanilla HTML/CSS/JS frontend
tests/             pytest suite (ingestion + analytics + API)
docs/web-app/      this DDD doc set
```
