# CONSTRAINTS

- **Timebox** — built end-to-end (tests passing, pushed, deployed) inside a 120-minute lab
  exam window. This bounds scope (see `SCOPE.md`) and doc depth (P0-only, see `README.md`).
- **Storage** — must be SQLite3 or DuckDB per the exam brief. SQLite3 (stdlib `sqlite3`,
  zero extra services) chosen for fastest reliable setup inside the timebox — see
  `ARCHITECTURE.md` §Decision: SQLite over DuckDB.
- **Token budget** — build with the existing Claude Code/Codex session allowance; no
  top-ups. This rules out generating the full 20-document ddd-web-app set and large
  speculative refactors.
- **Reference date reproducibility** — overdue/completed/accepted must be computed against
  an explicit reference date, not wall-clock `now()`, so a grader re-running the dashboard
  later gets the same numbers (see `PRD.md` Acceptance Criteria A4).
- **Deployment target** — Coolify, via a Dockerized app pulling from the company's GitHub
  repo (`ragnar-co/tee-ai-tech-user-exam`). No assumption is made about Coolify
  credentials being available to the build agent — the repo must be deploy-ready
  (`Dockerfile`, env vars documented) for a human to wire up in the Coolify UI.
- **AI workflow budget** — the bonus draft-update workflow must use the company-provided
  Claude API endpoint/quota (`ANTHROPIC_API_KEY`, optional `ANTHROPIC_BASE_URL`), not a
  hardcoded personal key, and must degrade predictably (HTTP 503 with a clear message)
  when the key is absent rather than silently failing.
- **Data sensitivity** — the input CSV uses pseudonymous mock identifiers
  (`Mock-Client-NN-*`, `Owner-NN`) only; no real PII. Even so, the repo must never commit
  `.env`, API keys, or the generated SQLite file (see `SECURITY.md`, `.gitignore`).
- **No auth in this scope** — the dashboard is a single-tenant internal tool for this lab;
  it is explicitly not exposed to the internet with real client data without adding
  authentication first (flagged as an out-of-scope gap in `SECURITY.md`).
