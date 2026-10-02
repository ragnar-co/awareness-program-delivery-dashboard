"""SQLite access layer for the Awareness Program Delivery Dashboard."""
import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.environ.get("DASHBOARD_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "awareness.db"))

STATUS_VALUES = {"planned", "in_progress", "awaiting_acceptance", "accepted"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS deliverables (
    deliverable_id   TEXT PRIMARY KEY,
    client_name      TEXT NOT NULL,
    deliverable_name TEXT NOT NULL,
    owner            TEXT NOT NULL,
    due_date         TEXT NOT NULL,
    status           TEXT NOT NULL CHECK (status IN ('planned','in_progress','awaiting_acceptance','accepted')),
    source_row       INTEGER,
    ingested_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_deliverables_client ON deliverables(client_name);
CREATE INDEX IF NOT EXISTS idx_deliverables_status ON deliverables(status);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file   TEXT NOT NULL,
    total_rows    INTEGER NOT NULL,
    inserted_rows INTEGER NOT NULL,
    rejected_rows INTEGER NOT NULL,
    errors_json   TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ai_drafts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT NOT NULL,
    as_of       TEXT NOT NULL,
    content     TEXT NOT NULL,
    model       TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def get_connection(db_path: str = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str = None) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


@contextmanager
def session(db_path: str = None):
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
