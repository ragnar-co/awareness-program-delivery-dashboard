from app import analytics
from app.ingest import ingest_csv_text
from tests.conftest import SAMPLE_CSV

AS_OF = "2026-10-02"


def _seed(db_path):
    ingest_csv_text(SAMPLE_CSV, source_file="sample.csv", db_path=db_path)


def test_summarize_overall_counts(db_path):
    _seed(db_path)
    result = analytics.summarize(AS_OF, db_path=db_path)
    overall = result["overall"]
    assert overall["total"] == 5
    assert overall["team_completed"] == 3   # D001 accepted, D002 + D004 awaiting_acceptance
    assert overall["client_accepted"] == 1  # D001
    assert overall["overdue"] == 3           # D002, D004, D005 (not D001: accepted)
    assert overall["status_counts"] == {
        "accepted": 1, "awaiting_acceptance": 2, "in_progress": 1, "planned": 1,
    }


def test_summarize_per_client(db_path):
    _seed(db_path)
    result = analytics.summarize(AS_OF, db_path=db_path)
    by_client = {c["client_name"]: c for c in result["by_client"]}

    acme = by_client["Acme Corp"]
    assert acme["total"] == 3
    assert acme["team_completed"] == 2
    assert acme["client_accepted"] == 1
    assert acme["overdue"] == 1
    assert acme["status_counts"] == {
        "accepted": 1, "awaiting_acceptance": 1, "in_progress": 1, "planned": 0,
    }

    globex = by_client["Globex Inc"]
    assert globex["total"] == 2
    assert globex["team_completed"] == 1
    assert globex["client_accepted"] == 0
    assert globex["overdue"] == 2
    assert globex["status_counts"] == {
        "accepted": 0, "awaiting_acceptance": 1, "in_progress": 0, "planned": 1,
    }


def test_summarize_filtered_by_client(db_path):
    _seed(db_path)
    result = analytics.summarize(AS_OF, client="Acme Corp", db_path=db_path)
    assert result["overall"]["total"] == 3
    assert len(result["by_client"]) == 1


def test_pending_acceptance_excludes_accepted_and_in_progress(db_path):
    _seed(db_path)
    items = analytics.pending_acceptance(AS_OF, db_path=db_path)
    ids = {i["deliverable_id"] for i in items}
    assert ids == {"D002", "D004"}


def test_overdue_excludes_accepted_even_if_due_date_passed(db_path):
    _seed(db_path)
    items = analytics.overdue_items(AS_OF, db_path=db_path)
    ids = {i["deliverable_id"] for i in items}
    assert ids == {"D002", "D004", "D005"}
    assert "D001" not in ids  # accepted, due date passed, but must not be "overdue"


def test_accepted_items(db_path):
    _seed(db_path)
    items = analytics.accepted_items(AS_OF, db_path=db_path)
    assert [i["deliverable_id"] for i in items] == ["D001"]
