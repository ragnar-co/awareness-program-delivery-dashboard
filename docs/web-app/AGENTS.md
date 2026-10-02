# AGENTS.md — rules for AI coding agents working in this repo

## Source of truth for status logic
`app/analytics.py` is the **only** place that defines what counts as `team_completed`,
`client_accepted`, and `overdue`. Any new endpoint, report, or AI prompt that needs these
numbers must call the functions in that module — never re-implement the status/date
comparison inline elsewhere (UI, a new route, the AI workflow). See `DATA_MODEL.md`
Enumeration Registry for the `status` values this logic depends on.

## Reference date discipline
Never call `date.today()` (or any wall-clock source) directly inside status-sensitive code
paths other than `app/main.py::_default_as_of`. Every function that computes overdue/
completed status takes `as_of` as an explicit parameter. This keeps results reproducible
(`PRD.md` A4) and testable without monkeypatching the clock.

## Status enum changes
If a new `status` value is ever introduced, it must be added in exactly one place —
`app/db.py::STATUS_VALUES` and the SQLite `CHECK` constraint — then every consumer
(`analytics.py`, `ai_workflow.py` prompt text, `app/static/app.js` rendering) updated to
decide explicitly which bucket it falls into. Do not let a new status silently fall through
as "not overdue, not completed" by omission.

## AI draft workflow guardrail
`app/ai_workflow.py::build_prompt` must keep passing the model **pre-classified** lists
(pending/accepted/overdue), not raw deliverable rows — this is what prevents the model from
independently deciding a pending-acceptance item is "done". Do not refactor this to hand
the model the raw `deliverables` table and ask it to classify status itself.

## Tests
Any change to `analytics.py` or `ingest.py` must keep `tests/test_analytics.py` and
`tests/test_ingest.py` passing, and extend them for new behavior — these are the
deterministic contract for the status rules (`TESTING.md`). Use the fixed `AS_OF =
"2026-10-02"` convention already established in the test fixtures; do not introduce
`datetime.now()` into any test assertion.

## Scope discipline
Do not add authentication, multi-format ingestion, notifications, or trend charts without
first updating `SCOPE.md` — these are explicitly out-of-scope decisions for this build, not
oversights.
