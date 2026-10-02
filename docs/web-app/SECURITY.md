# SECURITY

## Authentication / authorization
Explicitly **not implemented** in this build (see `CONSTRAINTS.md`, `SCOPE.md`) — the
dashboard is a single-tenant internal lab tool. Before exposing it beyond the lab with real
client data, add at minimum: an auth layer (SSO or token-based) gating every `/api/*`
route, and role separation between "can view all clients" vs "can view only assigned
clients" (the data model already carries `client_name` on every row, so row-level scoping
is a filter, not a schema change).

## Secrets
- `ANTHROPIC_API_KEY` (required for the AI draft workflow) and optional
  `ANTHROPIC_BASE_URL` are read from the environment only — never hardcoded, never logged.
  Missing key → `POST /api/ai/draft-update` returns HTTP 503 with a descriptive message
  (see `API_SPEC.md`), not a stack trace and not a fabricated draft.
- `.env` files, the SQLite database file, and `__pycache__`/`.venv` are excluded via
  `.gitignore` — the repo must never carry a live key or a copy of ingested client data
  into version control.
- `.dockerignore` mirrors the same exclusions so a built image never embeds a stray local
  `.env` or database file.

## Input handling
- CSV ingestion validates every row before it reaches SQLite (`app/ingest.py`): required
  fields present, `status` restricted to the enum via both application validation and a
  SQLite `CHECK` constraint (defense in depth — a malformed row cannot reach the table even
  if the Python-level check were bypassed), and `due_date` must parse as ISO-8601.
- All SQL is parameterized (`sqlite3` placeholders) — no string-built queries, so
  deliverable names/owners containing arbitrary text (including SQL metacharacters) cannot
  cause injection.
- The AI draft prompt is built entirely from server-side query results, not from
  unsanitized user-supplied free text — the only client input is the `client` name, which
  is used as an equality-filter SQL parameter, not interpolated into the prompt from
  request-controlled HTML/JS.

## Data sensitivity / PDPA note
Exam input data uses pseudonymous identifiers (`Mock-Client-NN-*`, `Owner-NN`) — no real
personal data. If this were pointed at real client/owner names, `DATA_MODEL.md` would need
a PDPA classification column and `CONSTRAINTS.md` an explicit retention policy; neither is
implemented here since the current dataset doesn't require it (declared, not invented).

## Transport
No TLS termination is configured in the app itself — deployed behind Coolify's
reverse proxy, which is expected to terminate TLS (see `DEPLOYMENT.md`).
