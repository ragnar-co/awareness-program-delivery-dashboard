import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from app.db import init_db


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test.db")
    init_db(path)
    return path


SAMPLE_CSV = """deliverable_id,client_name,deliverable_name,owner,due_date,status
D001,Acme Corp,Phishing training content,Owner-01,2026-09-01,accepted
D002,Acme Corp,Awareness event Q3,Owner-02,2026-09-20,awaiting_acceptance
D003,Acme Corp,Post-training report,Owner-03,2026-10-10,in_progress
D004,Globex Inc,Phishing training content,Owner-04,2026-08-15,awaiting_acceptance
D005,Globex Inc,Awareness event Q3,Owner-05,2026-09-30,planned
"""
