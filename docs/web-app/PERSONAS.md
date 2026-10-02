# PERSONAS

## P1 — Awareness Program Owner (primary)
Runs the Security Awareness Program for several clients at once (training media, events,
post-training reports). Pain point: before every client progress meeting, has to manually
cross-check a spreadsheet to avoid telling a client "it's done" when the deliverable is
actually sitting in client review. Needs, in under a minute: total load per client, what the
team already finished, what the client already signed off, and what has slipped past due
date with a named owner to chase.
Skill level: comfortable with spreadsheets and basic web UIs; not a developer.
Use case: opens the dashboard, filters to one client, reads the four headline numbers and
the two action lists (pending acceptance, overdue) before the call.

## P2 — Delivery Owner (Owner-01 … Owner-18 in the data)
An individual contributor responsible for specific deliverables (e.g. producing a training
deck or running an event). Pain point: doesn't always know a deliverable is overdue until
someone escalates it.
Use case: appears as the "owner" column in the overdue and pending-acceptance lists so the
Program Owner knows exactly who to follow up with — this persona does not log into the
dashboard directly in this scope (see `SCOPE.md`).

## P3 — Client Stakeholder (indirect, via AI draft)
Receives the human-reviewed version of the AI-drafted update. Never uses the dashboard
directly. Cares about one thing above all: a "pending acceptance" item must never be
described to them as finished — that is the exact failure mode this project exists to
prevent (see `VPD.md`).
