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
| `DASHBOARD_CSV_PATH` | No | If set **and the path exists inside the container** and the DB is empty at boot, auto-ingests this CSV on startup (see `app/main.py` lifespan). Setting it to a host path does nothing by itself — the file must also be bind-mounted into the container at that exact path, or the auto-seed silently no-ops (confirmed the hard way: `docker compose up -d` with only the env var set left the DB empty). See "Loading data" below for the reliable alternative. |
| `DASHBOARD_AS_OF` | No | Pins the reference date server-wide for reproducible grading (overridable per-request via `?as_of=`). |
| `AI_API_KEY` | Only for the bonus AI workflow | Company-provided OpenRouter API key (works with any OpenRouter model id, default `anthropic/claude-sonnet-5`). Never commit; set via Coolify's environment variable UI / secret store. |
| `AI_BASE_URL` | No | Set only if routing through a company-managed API gateway instead of openrouter.ai. |

See `.env.example` for a template — copy to `.env` for local Docker Compose use; Coolify
should get these as first-class environment variables in its UI, not via a committed file.

## Build & run locally with Docker

```bash
docker build -t awareness-dashboard .
docker run -d -p 8000:8000 -e AI_API_KEY=sk-or-v1-... \
  -v "$(pwd)/data:/app/data" \
  awareness-dashboard
```
or `docker compose up -d --build` using the provided `docker-compose.yml` (set `AI_API_KEY`
etc. via `.env`, copied from `.env.example`).

## Loading data (the reliable way, works identically on Docker and Coolify)

Don't rely on `DASHBOARD_CSV_PATH` auto-seed for a fresh container — it requires the CSV to
already be bind-mounted at that exact in-container path, which `docker-compose.yml` does
not do by default (this was hit for real: the container came up healthy with an *empty*
`awareness.db` because the env var pointed at a host path the container couldn't see).
Instead, once the container is up, ingest once over HTTP — this has no path/mount
dependency at all:
```bash
curl -F "file=@mukie_awareness_deliverables.csv" http://<host>:8000/api/ingest
```
Check the response: `inserted_rows` should equal the file's row count and `rejected_rows`
should be `0`. Safe to re-run any time — it's an upsert, not a wipe-and-reload.

If you specifically want auto-seed-on-first-boot anyway (e.g. for a throwaway demo),
uncomment the bind-mount line in `docker-compose.yml`, set `DASHBOARD_CSV_PATH` to the
*in-container* path (`/app/data/seed.csv`) — not the host path — and set `CSV_HOST_PATH` to
the file's real location on the host before `docker compose up -d`.

## Deploying on Coolify
This repo ships deploy-ready (`Dockerfile`, healthcheck, documented env vars) but the
build agent did not have Coolify API credentials in this environment — the following steps
are for the operator with Coolify access, confirmed with the requester as the intended
handoff point:

0. **Repo location**: direct push access to `ragnar-co/tee-ai-tech-user-exam` was denied
   (pull-only token) — the build was pushed instead to
   `PreeyanutM/awareness-program-delivery-dashboard` (private). Transfer/PR it into
   `ragnar-co` before pointing Coolify at it, per the exam's own documented flow (push →
   verify on GitHub → transfer to `ragnar-co`).
1. In Coolify: **New Resource → Application → Public/Private Git Repository**, point at
   the repo above (branch `main`), build pack = **Dockerfile**.
2. Set environment variables per the table above (`AI_API_KEY` as a secret).
3. Attach a persistent volume at `/app/data` so `awareness.db` survives redeploys.
4. Set the health check path to `/api/health` (container already defines a Docker
   `HEALTHCHECK`; Coolify can additionally probe this path over HTTP).
5. Deploy, then `POST /api/ingest` the CSV once via `curl` against the live URL (see
   "Loading data" above — Coolify has no access to a file on your local machine, so the
   `DASHBOARD_CSV_PATH` auto-seed path does not apply here; the HTTP ingest is the only
   practical way to load data on Coolify).
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
