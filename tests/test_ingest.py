from app.ingest import ingest_csv_text, parse_csv
from tests.conftest import SAMPLE_CSV


def test_parse_csv_accepts_valid_rows():
    rows, errors = parse_csv(SAMPLE_CSV)
    assert len(rows) == 5
    assert errors == []


def test_parse_csv_rejects_missing_field():
    csv_text = "deliverable_id,client_name,deliverable_name,owner,due_date,status\n" \
               "D001,Acme Corp,Training,,2026-09-01,accepted\n"
    rows, errors = parse_csv(csv_text)
    assert rows == []
    assert "missing field" in errors[0]


def test_parse_csv_rejects_invalid_status():
    csv_text = "deliverable_id,client_name,deliverable_name,owner,due_date,status\n" \
               "D001,Acme Corp,Training,Owner-01,2026-09-01,done\n"
    rows, errors = parse_csv(csv_text)
    assert rows == []
    assert "invalid status" in errors[0]


def test_parse_csv_rejects_bad_date():
    csv_text = "deliverable_id,client_name,deliverable_name,owner,due_date,status\n" \
               "D001,Acme Corp,Training,Owner-01,01-09-2026,accepted\n"
    rows, errors = parse_csv(csv_text)
    assert rows == []
    assert "invalid due_date" in errors[0]


def test_parse_csv_rejects_duplicate_id_within_file():
    csv_text = "deliverable_id,client_name,deliverable_name,owner,due_date,status\n" \
               "D001,Acme Corp,Training,Owner-01,2026-09-01,accepted\n" \
               "D001,Acme Corp,Training 2,Owner-02,2026-09-05,planned\n"
    rows, errors = parse_csv(csv_text)
    assert len(rows) == 1
    assert "duplicate" in errors[0]


def test_ingest_csv_text_reports_counts_and_upserts(db_path):
    report = ingest_csv_text(SAMPLE_CSV, source_file="sample.csv", db_path=db_path)
    assert report["inserted_rows"] == 5
    assert report["rejected_rows"] == 0

    # Re-ingesting an updated row should upsert, not duplicate.
    updated_csv = SAMPLE_CSV.replace("D001,Acme Corp,Phishing training content,Owner-01,2026-09-01,accepted",
                                      "D001,Acme Corp,Phishing training content,Owner-01,2026-09-01,awaiting_acceptance")
    ingest_csv_text(updated_csv, source_file="sample2.csv", db_path=db_path)

    from app.db import session
    with session(db_path) as conn:
        (total,) = conn.execute("SELECT COUNT(*) FROM deliverables").fetchone()
        (status,) = conn.execute("SELECT status FROM deliverables WHERE deliverable_id = 'D001'").fetchone()
    assert total == 5
    assert status == "awaiting_acceptance"
