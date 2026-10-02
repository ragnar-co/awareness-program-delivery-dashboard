# VPD — Value Proposition Design

## Pain
The Awareness Program Owner manages the same four-stage deliverable lifecycle
(`planned → in_progress → awaiting_acceptance → accepted`) across dozens of clients and
hundreds of deliverables. The recurring, costly mistake: reporting a deliverable that is
merely **sent to the client for review** (`awaiting_acceptance`) as if it were **complete
and accepted**. This erodes client trust when the client later points out they never signed
off, and it hides real schedule risk (a deliverable can be both "sent" and overdue at once).

## Gain
A single dashboard that:
1. Never conflates "team finished their part" with "client accepted" — these are two
   distinct counters, always shown side by side (see `DATA_MODEL.md`, `analytics.py`).
2. Surfaces, unprompted, every item sitting in client review and every item overdue, each
   with the owner named, so follow-up starts before the client has to ask.
3. Computes all of this against an explicit, reproducible reference date instead of
   "whatever today happens to be" — the same input always produces the same report.

## Value Proposition Statement
"For the Awareness Program Owner who must report delivery status to many clients, the
Awareness Program Delivery Dashboard turns a raw CSV export into an always-accurate,
per-client completion and acceptance picture — unlike a manually-maintained spreadsheet,
it cannot accidentally report a pending-review item as done."

## Bonus value: AI draft update
The AI draft workflow is deliberately given the already-separated pending/accepted/overdue
lists (not the raw CSV) as its only grounding, and is explicitly instructed never to call a
pending-acceptance item "done" — turning the dashboard's core guarantee into client-ready
prose instead of just internal numbers.
