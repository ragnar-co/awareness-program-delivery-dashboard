# TESTING

## Strategy
Three layers, all deterministic (no wall-clock dependence, no network calls):

1. **Ingestion validation** (`tests/test_ingest.py`) — valid CSV accepted in full; each
   rejection reason (missing field, invalid status, bad date, in-file duplicate id) tested
   individually; upsert-on-re-ingest verified to update in place rather than duplicate.
2. **Analytics correctness** (`tests/test_analytics.py`) — a fixed 5-row, 2-client fixture
   (`tests/conftest.py::SAMPLE_CSV`) with a fixed `AS_OF = "2026-10-02"` constant, hand-
   verified counts for overall, per-client, and client-filtered summaries, plus the
   specific edge case that matters most: an `accepted` deliverable whose due date has
   passed must **not** appear in the overdue list (PRD A2.3).
3. **API contract** (`tests/test_api.py`) — FastAPI `TestClient` against a fresh temp
   SQLite file per test (via `DASHBOARD_DB_PATH` + reloading `app.*` modules), covering
   health, clients, summary (overall + filtered), pending-acceptance, overdue, and the
   AI draft endpoint's 503 behavior when `ANTHROPIC_API_KEY` is absent.

No test ever calls the real Anthropic API — the bonus AI workflow is tested only for its
fail-closed behavior (missing key → 503), since exercising the live endpoint would consume
the company's quota non-deterministically in CI.

## Running
```bash
python3 -m venv .venv && source .venv/bin/activate   # python >= 3.10 required (PEP 604 `X | None` syntax)
pip install -r requirements-dev.txt
python -m pytest -q
```
Expected: `19 passed`.

## Manual smoke test (done during this build)
Ran the server with `DASHBOARD_CSV_PATH` pointed at the real exam CSV
(`mukie_awareness_deliverables.csv`, 12,536 rows), confirmed: `/api/health` → `ok`,
`/api/clients` lists all 25 mock clients, `/api/summary` overall and per-client totals sum
correctly, `/api/deliverables/pending-acceptance` and `/overdue` return owner-tagged rows
scoped by client, and `/` + `/static/app.js` serve with HTTP 200.

## Known gap
No browser-automation (e.g. Playwright) test of the actual rendered dashboard — covered
instead by a manual run during the build (see above) plus full API-level coverage, which is
what the UI is a thin client over.
