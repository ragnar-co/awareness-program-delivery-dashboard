# API_SPEC

REST, JSON. No auth in this scope (see `SECURITY.md`). Base path: `/`.

## `GET /api/health`
Liveness probe. → `{"status": "ok"}`

## `GET /api/clients`
→ `{"clients": ["Mock-Client-01-Manufacturing", ...]}` — distinct `client_name` values.

## `GET /api/summary`
Query: `client` (optional), `as_of` (optional, `YYYY-MM-DD`, see `ARCHITECTURE.md`).
→
```json
{
  "as_of": "2026-10-02",
  "overall": {"client_name": null, "total": 12536, "team_completed": 5908, "client_accepted": 3629, "overdue": 4106,
              "status_counts": {"planned": 4529, "in_progress": 2099, "awaiting_acceptance": 2279, "accepted": 3629}},
  "by_client": [{"client_name": "Mock-Client-01-Manufacturing", "total": 502, "team_completed": 288, "client_accepted": 245, "overdue": 65,
                 "status_counts": {"planned": 109, "in_progress": 105, "awaiting_acceptance": 43, "accepted": 245}}, ...]
}
```
`status_counts` breaks the same total down by the four mutually-exclusive `status` values
(see `DATA_MODEL.md` Enumeration Registry) — it's what the dashboard's status-composition
chart renders; `team_completed`/`client_accepted`/`overdue` remain the derived metrics for
the headline cards. If `client` is set, `overall` and `by_client` both scope to that one
client.

## `GET /api/deliverables/pending-acceptance`
Query: `client` (optional), `as_of` (optional). Rows with `status == awaiting_acceptance`,
sorted by `due_date` ascending.
→ `{"as_of": "...", "items": [{"deliverable_id": "...", "client_name": "...", "deliverable_name": "...", "owner": "...", "due_date": "...", "status": "awaiting_acceptance"}, ...]}`

## `GET /api/deliverables/overdue`
Query: `client` (optional), `as_of` (optional). Rows with `due_date < as_of AND status !=
accepted`, sorted by `due_date` ascending. Same item shape as above, `status` varies.

## `GET /api/deliverables/accepted`
Query: `client` (optional), `as_of` (optional). Rows with `status == accepted`, sorted by
`due_date` descending (most recently due first).

## `POST /api/ingest`
Multipart form upload, field `file` = the CSV. Validates and upserts (see `DATA_MODEL.md`,
`PRD.md` US1).
→
```json
{"source_file": "mukie_awareness_deliverables.csv", "total_rows": 12536, "inserted_rows": 12536, "rejected_rows": 0, "errors": []}
```
`errors[]` entries look like `"row 42: invalid status 'done'"` — one per rejected row,
never a silent drop.

## `POST /api/ai/draft-update`
Query params (not body — kept simple for a single-purpose action trigger): `client`
(required), `as_of` (optional).
→ 200:
```json
{
  "client": "Mock-Client-01-Manufacturing", "as_of": "2026-10-02",
  "content": "1. งานที่รอตรวจรับ...\n2. งานที่ลูกค้ารับรองแล้ว...\n3. เรื่องที่ควรติดตาม...",
  "model": "anthropic/claude-sonnet-5",
  "counts": {"pending_acceptance": 43, "accepted": 245, "overdue": 65}
}
```
→ 503 if `AI_API_KEY` is not configured: `{"detail": "AI_API_KEY is not set — ..."}`

## `GET /api/ai/drafts`
Query: `client` (optional), returns up to the 20 most recent drafts, newest first —
`{"drafts": [{"id": 1, "client_name": "...", "as_of": "...", "content": "...", "model": "...", "created_at": "..."}, ...]}`.

## `GET /`
Serves the dashboard SPA shell (`app/static/index.html`). Static assets under `/static/*`.
