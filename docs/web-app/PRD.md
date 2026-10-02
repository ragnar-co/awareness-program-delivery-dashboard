# PRD — Awareness Program Delivery Dashboard

## Problem
See `VPD.md`. The Program Owner needs an always-accurate, per-client delivery status view
that cannot mistake "awaiting client sign-off" for "done".

## User stories & acceptance criteria

### US1 — Ingest the deliverables feed
As the Program Owner, I upload the CSV export so the dashboard reflects current reality.
- **A1.1** Uploading a well-formed CSV inserts every row; re-uploading with changed status
  for the same `deliverable_id` updates that row (upsert), it does not duplicate it.
- **A1.2** A row missing a required field, with an unrecognized `status`, or an unparsable
  `due_date` is rejected and listed with a specific reason in the ingestion report; it does
  not silently disappear and does not abort the rows that are valid.
- **A1.3** A duplicate `deliverable_id` within the same file is rejected on the second
  occurrence with a reason, not silently overwritten mid-file.

### US2 — See overall and per-client status at a glance
As the Program Owner, I see total / team-completed / client-accepted / overdue counts.
- **A2.1** `team_completed` counts deliverables whose status is `awaiting_acceptance` or
  `accepted` (the team's side of the work is done) — this number is always ≥
  `client_accepted` and the UI never labels it "accepted".
- **A2.2** `client_accepted` counts only `status == accepted`.
- **A2.3** `overdue` counts deliverables where `due_date < as_of` and `status != accepted`
  — including ones sitting in `awaiting_acceptance`, because the client has not actually
  signed off yet regardless of how late the review is.
- **A2.4** The same four numbers are available overall and broken down per client
  (`GET /api/summary`, `by_client[]`).

### US3 — Filter to one client
As the Program Owner, I select a client from a dropdown and every card/list/section
re-scopes to that client only, via the same `client` query parameter on every endpoint.

### US4 — Reference date reproducibility
As a grader/auditor, I can pin the exact reference date used for overdue/status
calculations and get the same answer every time.
- **A4.1** Every status-sensitive endpoint accepts `?as_of=YYYY-MM-DD`.
- **A4.2** Without an explicit `as_of`, the server falls back to `DASHBOARD_AS_OF` env var
  if set, else the server's current date — this fallback chain is documented in
  `ARCHITECTURE.md` and never silently varies the stored data, only the computed view.

### US5 — Work lists with an owner to chase
As the Program Owner, I see two lists, each row carrying `owner`:
- **A5.1** Pending acceptance — `status == awaiting_acceptance`, sorted by due date.
- **A5.2** Overdue — same definition as A2.3, sorted by due date.

### US6 (bonus) — AI draft client update
As the Program Owner, I generate a Thai-language draft update for one client, split into
pending-acceptance / accepted / to-follow-up sections.
- **A6.1** The draft is grounded only in that client's current pending/accepted/overdue
  lists — the model is given the pre-computed lists, not asked to re-derive status itself.
- **A6.2** The prompt explicitly forbids calling a pending-acceptance item "done" or
  "delivered"; if a section is empty it must say so, not omit or fabricate.
- **A6.3** Every generated draft is persisted (`ai_drafts` table) and re-displayed on
  revisit, not regenerated/lost on page reload.
- **A6.4** If `ANTHROPIC_API_KEY` is not configured, the endpoint returns HTTP 503 with a
  clear message rather than a generic 500 or a fabricated draft.

## Non-functional requirements
- Must run as a single Docker container (see `DEPLOYMENT.md`) suitable for Coolify.
- Ingesting the full ~12.5k-row exam CSV must complete well within a single HTTP request
  (observed: sub-second on commodity hardware).
- Test suite (`pytest`) must pass deterministically using a fixed `as_of` — no reliance on
  wall-clock time in assertions (see `TESTING.md`).
