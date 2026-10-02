# DATA_MODEL

## Entities

### `deliverables` (canonical source for status reporting)
| Column | Type | Notes |
|---|---|---|
| `deliverable_id` | TEXT PK | From CSV, e.g. `W000001`. Upsert key. |
| `client_name` | TEXT NOT NULL | e.g. `Mock-Client-01-Manufacturing`. |
| `deliverable_name` | TEXT NOT NULL | Free text, e.g. "สื่ออบรมเรื่อง Phishing...". |
| `owner` | TEXT NOT NULL | e.g. `Owner-04`. Who to chase for pending/overdue items. |
| `due_date` | TEXT NOT NULL | ISO-8601 `YYYY-MM-DD`, stored as text (SQLite has no native DATE type; lexicographic comparison works because the format is fixed-width ISO). |
| `status` | TEXT NOT NULL | Enum: `planned`, `in_progress`, `awaiting_acceptance`, `accepted`. Enforced by `CHECK` constraint — see Enumeration below. |
| `source_row` | INTEGER | Reserved for future lineage; not populated in this build. |
| `ingested_at` | TEXT | `datetime('now')` default, set on first insert. |

### `ingestion_runs` (audit trail)
| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `source_file` | TEXT | Uploaded filename or path. |
| `total_rows` / `inserted_rows` / `rejected_rows` | INTEGER | Counts for one ingest call. |
| `errors_json` | TEXT | JSON array of human-readable rejection reasons. |
| `created_at` | TEXT | `datetime('now')` default. |

### `ai_drafts` (bonus workflow output)
| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `client_name` | TEXT | Which client the draft is for. |
| `as_of` | TEXT | Reference date used to build the draft. |
| `content` | TEXT | Full generated Thai-language draft text. |
| `model` | TEXT | Model identifier used, for traceability. |
| `created_at` | TEXT | `datetime('now')` default. |

## Enumeration Registry — `status`
Owner document: this one (`DATA_MODEL.md`). Referenced, never redefined, by
`ARCHITECTURE.md`, `API_SPEC.md`, and the frontend.

| Value | Meaning | Counted in |
|---|---|---|
| `planned` | Not started. | `total`; `overdue` if past due. |
| `in_progress` | Team actively working. | `total`; `overdue` if past due. |
| `awaiting_acceptance` | Sent to client, no verdict yet. | `total`, `team_completed`, pending-acceptance list; `overdue` if past due. |
| `accepted` | Client signed off. | `total`, `team_completed`, `client_accepted`. Never `overdue`. |

## Derived metrics (computed, not stored — see `analytics.py`)
- `team_completed` = count where `status IN ('awaiting_acceptance','accepted')`.
- `client_accepted` = count where `status = 'accepted'`.
- `overdue` = count where `due_date < :as_of AND status != 'accepted'`.
- All four are computed overall and grouped by `client_name` in the same pass.

## Retention
No retention/soft-delete policy is implemented in this build — `deliverables` rows persist
until the backing CSV upserts them again or the SQLite file is replaced. Flagged as a gap
for a production iteration, not calibrated here (see `CONSTRAINTS.md`).
