# DEPLOYMENT

## Environments
- **Dev** — local `uvicorn --reload` against a throwaway `data/awareness.db`.
- **Production (Coolify)** — single Docker container, SQLite file on a persisted volume so
  ingested data survives redeploys.

## Environment variables
| Variable | Required | Purpose |
|---|---|---|
| `PORT` | No (default `8000`) | Port Uvicorn binds to inside the container. |
| `DASHBOARD_DB_PATH` | No (default `/app/data/awareness.db` in the image) | SQLite file location — point at the mounted volume. |
| `DASHBOARD_CSV_PATH` | No | If set and the DB is empty at boot, auto-ingests this CSV on startup (see `app/main.py` lifespan). Useful for seeding the exam dataset without a manual upload step. |
| `DASHBOARD_AS_OF` | No | Pins the reference date server-wide for reproducible grading (overridable per-request via `?as_of=`). |
| `ANTHROPIC_API_KEY` | Only for the bonus AI workflow | Company-provided Claude API key. Never commit; set via Coolify's environment variable UI / secret store. |
| `ANTHROPIC_BASE_URL` | No | Set only if routing through a company-managed API gateway instead of api.anthropic.com. |

See `.env.example` for a template — copy to `.env` for local Docker Compose use; Coolify
should get these as first-class environment variables in its UI, not via a committed file.

## Build & run locally with Docker
```bash
docker build -t awareness-dashboard .
docker run -p 8000:8000 \
  -e DASHBOARD_CSV_PATH=/app/data/seed.csv \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/mukie_awareness_deliverables.csv:/app/data/seed.csv:ro" \
  awareness-dashboard
```
or `docker compose up --build` using the provided `docker-compose.yml`.

## Deploying on Coolify
This repo ships deploy-ready (`Dockerfile`, healthcheck, documented env vars) but the
build agent did not have Coolify API credentials in this environment — the following steps
are for the operator with Coolify access, confirmed with the requester as the intended
handoff point:

1. In Coolify: **New Resource → Application → Public/Private Git Repository**, point at
   `ragnar-co/tee-ai-tech-user-exam` (branch `main`), build pack = **Dockerfile**.
2. Set environment variables per the table above (`ANTHROPIC_API_KEY` as a secret).
3. Attach a persistent volume at `/app/data` so `awareness.db` survives redeploys.
4. Set the health check path to `/api/health` (container already defines a Docker
   `HEALTHCHECK`; Coolify can additionally probe this path over HTTP).
5. Deploy. First boot auto-seeds from `DASHBOARD_CSV_PATH` if set and the DB is empty;
   otherwise `POST /api/ingest` the CSV once via `curl` against the live URL.
6. Verify: `curl https://<coolify-domain>/api/health` → `{"status":"ok"}`, then open the
   domain in a browser and confirm the client dropdown populates.

## Rollback
Coolify keeps prior image builds — redeploy the previous successful build from its
dashboard. Because all state lives in the mounted `data/` volume, rolling the application
image back does not lose ingested deliverables or AI draft history.

## CI/CD
Not set up in this build (no CI pipeline file) — out of scope for the 120-minute timebox.
`python -m pytest -q` is expected to be run manually before every push (see `TESTING.md`,
`RUNBOOK.md`).
