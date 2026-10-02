# RUNBOOK

## Health check
`curl http://<host>:<port>/api/health` → `{"status": "ok"}`. The Docker image also runs
this as its `HEALTHCHECK`; `docker ps` shows `(healthy)`/`(unhealthy)`.

## Container won't start / crashes on boot
1. `docker logs <container>` — most common cause: `DASHBOARD_CSV_PATH` points at a file
   that doesn't exist inside the container (bind-mount path mismatch) — the app logs and
   skips auto-seed, it should not crash; a real crash here is more likely a missing
   `requirements.txt` dependency after an edit. Check the traceback at the top of the log.
2. `docker exec -it <container> sh` then `python -c "import app.main"` to reproduce the
   import error directly.

## Dashboard loads but shows all zeros
The SQLite file has no rows yet. Either:
- `curl -F "file=@yourfile.csv" http://<host>/api/ingest` and check the JSON report for
  `rejected_rows` / `errors[]`, or
- confirm `DASHBOARD_CSV_PATH` was set **before** first boot (auto-seed only runs when the
  table is empty, so setting it after data already exists does nothing — this is
  intentional, not a bug, to avoid clobbering ingested data on every restart).

## Numbers look wrong for a specific client
Re-derive by hand against `DATA_MODEL.md`'s Enumeration Registry: open
`sqlite3 data/awareness.db` and run
```sql
SELECT status, COUNT(*) FROM deliverables WHERE client_name = 'X' GROUP BY status;
SELECT COUNT(*) FROM deliverables WHERE client_name = 'X' AND due_date < 'YYYY-MM-DD' AND status != 'accepted';
```
and compare against `/api/summary?client=X&as_of=YYYY-MM-DD`. If they disagree, the bug is
in `analytics.py`, not the data — file it against `AGENTS.md`'s single-source-of-truth
rule.

## AI draft workflow returns 503
Expected when `AI_API_KEY` is unset — not an incident. To fix: set the key (Coolify
environment variable, or `export AI_API_KEY=...` locally) and restart the container/
process; no code change needed.

## AI draft workflow returns 500 / times out
Check `AI_BASE_URL` if set (company gateway reachability), check the company's
OpenRouter quota/rate-limit status (https://openrouter.ai/api/v1/key), and check `docker logs` for the raw exception from the
`httpx` call in `app/ai_workflow.py::generate_draft`.

## Re-ingesting a corrected CSV
Safe at any time — ingestion upserts by `deliverable_id`, it does not wipe the table first.
To force a full reset instead, stop the container, delete `data/awareness.db`, restart
(auto-seed re-runs if `DASHBOARD_CSV_PATH` is set), or re-`POST /api/ingest` the full file.

## Backup / restore
Backup: copy the `data/awareness.db` file (or the Coolify-managed volume) while the
container is stopped, or use `sqlite3 data/awareness.db ".backup backup.db"` for a
consistent live snapshot. Restore: stop the container, replace the file, restart.

## Rotating the AI gateway API key
Update the `AI_API_KEY` environment variable in Coolify and redeploy/restart the
container — no application code or schema change required.
