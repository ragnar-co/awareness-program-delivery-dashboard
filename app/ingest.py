"""CSV ingestion with validation for the deliverables feed.

A deliverable row is accepted only if every required field is present,
the status is one of the known enum values, and due_date parses as
ISO-8601 (YYYY-MM-DD). Rejected rows are recorded with a reason but never
silently dropped, so an ingestion run is always auditable.
"""
import csv
import json
from datetime import datetime
from io import StringIO

from .db import STATUS_VALUES, session

REQUIRED_FIELDS = ["deliverable_id", "client_name", "deliverable_name", "owner", "due_date", "status"]


def _validate_row(row: dict, line_no: int) -> tuple[dict | None, str | None]:
    missing = [f for f in REQUIRED_FIELDS if not (row.get(f) or "").strip()]
    if missing:
        return None, f"row {line_no}: missing field(s) {', '.join(missing)}"

    status = row["status"].strip()
    if status not in STATUS_VALUES:
        return None, f"row {line_no}: invalid status '{status}'"

    due_date = row["due_date"].strip()
    try:
        datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError:
        return None, f"row {line_no}: invalid due_date '{due_date}' (expected YYYY-MM-DD)"

    clean = {
        "deliverable_id": row["deliverable_id"].strip(),
        "client_name": row["client_name"].strip(),
        "deliverable_name": row["deliverable_name"].strip(),
        "owner": row["owner"].strip(),
        "due_date": due_date,
        "status": status,
    }
    return clean, None


def parse_csv(csv_text: str) -> tuple[list[dict], list[str]]:
    """Parse + validate CSV text. Returns (valid_rows, error_messages)."""
    reader = csv.DictReader(StringIO(csv_text))
    valid_rows, errors = [], []
    seen_ids = set()
    for line_no, row in enumerate(reader, start=2):  # header is line 1
        clean, err = _validate_row(row, line_no)
        if err:
            errors.append(err)
            continue
        if clean["deliverable_id"] in seen_ids:
            errors.append(f"row {line_no}: duplicate deliverable_id '{clean['deliverable_id']}' in file")
            continue
        seen_ids.add(clean["deliverable_id"])
        valid_rows.append(clean)
    return valid_rows, errors


def ingest_csv_text(csv_text: str, source_file: str, db_path: str = None) -> dict:
    """Validate and upsert CSV content into SQLite. Returns an ingestion report."""
    valid_rows, errors = parse_csv(csv_text)

    with session(db_path) as conn:
        for row in valid_rows:
            conn.execute(
                """
                INSERT INTO deliverables (deliverable_id, client_name, deliverable_name, owner, due_date, status)
                VALUES (:deliverable_id, :client_name, :deliverable_name, :owner, :due_date, :status)
                ON CONFLICT(deliverable_id) DO UPDATE SET
                    client_name = excluded.client_name,
                    deliverable_name = excluded.deliverable_name,
                    owner = excluded.owner,
                    due_date = excluded.due_date,
                    status = excluded.status
                """,
                row,
            )
        total_rows = len(valid_rows) + len(errors)
        conn.execute(
            """
            INSERT INTO ingestion_runs (source_file, total_rows, inserted_rows, rejected_rows, errors_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (source_file, total_rows, len(valid_rows), len(errors), json.dumps(errors)),
        )

    return {
        "source_file": source_file,
        "total_rows": len(valid_rows) + len(errors),
        "inserted_rows": len(valid_rows),
        "rejected_rows": len(errors),
        "errors": errors,
    }


def ingest_csv_file(path: str, db_path: str = None) -> dict:
    with open(path, "r", encoding="utf-8-sig") as f:
        text = f.read()
    return ingest_csv_text(text, source_file=path, db_path=db_path)
