# TASKS

Breakdown of implementation work, mapped back to `PRD.md` user stories.

| Task | Implements | Status |
|---|---|---|
| SQLite schema: `deliverables`, `ingestion_runs`, `ai_drafts` | DATA_MODEL | Done |
| CSV parsing + row validation (required fields, status enum, date format, in-file dedupe) | US1 (A1.1–A1.3) | Done |
| Upsert on `deliverable_id` conflict | US1 (A1.1) | Done |
| `analytics.py`: team_completed / client_accepted / overdue definitions, overall + per-client | US2 (A2.1–A2.4) | Done |
| `GET /api/summary` with `client` + `as_of` filters | US2, US3, US4 | Done |
| `GET /api/deliverables/pending-acceptance`, `/overdue`, `/accepted` | US5 (A5.1–A5.2) | Done |
| `as_of` resolution chain (query param → env var → server date) | US4 (A4.1–A4.2) | Done |
| Frontend: client dropdown, as-of date picker, summary cards, per-client table, pending/overdue tables | US2, US3, US5 | Done |
| AI draft workflow: prompt builder grounded in pre-classified lists, OpenRouter chat-completion call, persistence | US6 (A6.1–A6.3) | Done |
| 503 handling when `AI_API_KEY` missing | US6 (A6.4) | Done |
| AI draft history endpoint + UI panel | US6 (A6.3) | Done |
| Pytest: ingestion validation (5 cases), analytics (6 cases), API (8 cases) with fixed `as_of` | NFR — deterministic tests | Done |
| Dockerfile + healthcheck, `.dockerignore`, `docker-compose.yml` | DEPLOYMENT | Done |
| Push to `ragnar-co/tee-ai-tech-user-exam`, deploy-ready for Coolify | NFR — deployment | Done (repo); Coolify wiring handed to operator per `DEPLOYMENT.md` |

## Explicitly deferred (see `SCOPE.md` Roadmap)
- GLOSSARY.md, ADR.md, UI_SPEC.md, TRACKING_PLAN.md, CHANGELOG.md (P1 docs).
- Auth/RBAC, non-CSV ingestion, notifications, trend charts.
