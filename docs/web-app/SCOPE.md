# SCOPE

## In scope (this build)
- CSV ingestion via `POST /api/ingest`: validate required fields, status enum, date format;
  upsert by `deliverable_id`; reject-with-reason (never silently drop) invalid rows.
- SQLite3 storage of deliverables, ingestion run history, and AI draft history.
- Dashboard summary: total / team-completed / client-accepted / overdue, overall and
  per client, computed against an explicit reference date (`as_of`).
- Client filter: view all clients at once or drill into exactly one.
- Pending-acceptance list and overdue list, each row showing owner and due date.
- Bonus: AI-generated draft client update per selected client, persisted and displayed.
- Dockerized, Coolify-deployable packaging.

## Out of scope (explicitly, for this timebox)
- Authentication / authorization / multi-tenant access control.
- Editing or creating deliverables through the UI (CSV ingest is the only write path
  besides the AI draft history).
- Ingestion formats other than CSV (e.g. Excel, API push from a PM tool).
- Notifications (email/Slack) when something becomes overdue.
- Historical trend charts (e.g. "overdue count over time") — only the point-in-time view
  as of the reference date.
- Multi-language UI (UI copy is English; generated AI drafts are Thai, matching the
  program's actual client-facing language).
- Data analytics track documents (`ddd-data-analytics`) — this build uses `ddd-web-app`
  only, since the primary deliverable is an interactive page+API system a person drives
  directly, not a BI/pipeline artifact (see `ARCHITECTURE.md` §Track choice).

## Roadmap (not built, noted for honesty)
- Role-based access per client (so a client-facing portal could reuse the same API).
- CHANGELOG.md / ADR.md / UI_SPEC.md / TRACKING_PLAN.md / GLOSSARY.md — P1 docs skipped
  under the 120-minute timebox (see `README.md`).
