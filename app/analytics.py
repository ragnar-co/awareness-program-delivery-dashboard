"""Delivery status analytics — the definitions here are the single source
of truth for what counts as "completed", "accepted" and "overdue".

Status lifecycle: planned -> in_progress -> awaiting_acceptance -> accepted.

team_completed  = team finished their side of the work (sent for client
                   review OR already accepted) -> status in
                   {awaiting_acceptance, accepted}
client_accepted = client has signed off -> status == accepted
overdue         = due_date < as_of AND status != accepted
                   (still overdue even if it is sitting in
                   awaiting_acceptance — the client has not signed off yet)
pending_acceptance = status == awaiting_acceptance (sent to client, no
                   verdict yet) — must never be reported as "done".
"""
from dataclasses import dataclass, field

from .db import session


@dataclass
class ClientSummary:
    client_name: str
    total: int = 0
    team_completed: int = 0
    client_accepted: int = 0
    overdue: int = 0


def _base_rows(conn, client: str | None):
    query = "SELECT deliverable_id, client_name, deliverable_name, owner, due_date, status FROM deliverables"
    params: tuple = ()
    if client:
        query += " WHERE client_name = ?"
        params = (client,)
    return conn.execute(query, params).fetchall()


def get_clients(db_path: str = None) -> list[str]:
    with session(db_path) as conn:
        rows = conn.execute("SELECT DISTINCT client_name FROM deliverables ORDER BY client_name").fetchall()
    return [r["client_name"] for r in rows]


def summarize(as_of: str, client: str | None = None, db_path: str = None) -> dict:
    with session(db_path) as conn:
        rows = _base_rows(conn, client)

    by_client: dict[str, ClientSummary] = {}
    overall = ClientSummary(client_name="__overall__")

    for row in rows:
        cs = by_client.setdefault(row["client_name"], ClientSummary(client_name=row["client_name"]))
        for target in (cs, overall):
            target.total += 1
            if row["status"] in ("awaiting_acceptance", "accepted"):
                target.team_completed += 1
            if row["status"] == "accepted":
                target.client_accepted += 1
            if row["due_date"] < as_of and row["status"] != "accepted":
                target.overdue += 1

    return {
        "as_of": as_of,
        "overall": vars(overall) | {"client_name": None},
        "by_client": [vars(by_client[name]) for name in sorted(by_client)],
    }


def pending_acceptance(as_of: str, client: str | None = None, db_path: str = None) -> list[dict]:
    with session(db_path) as conn:
        rows = _base_rows(conn, client)
    items = [dict(r) for r in rows if r["status"] == "awaiting_acceptance"]
    items.sort(key=lambda r: r["due_date"])
    return items


def overdue_items(as_of: str, client: str | None = None, db_path: str = None) -> list[dict]:
    with session(db_path) as conn:
        rows = _base_rows(conn, client)
    items = [dict(r) for r in rows if r["due_date"] < as_of and r["status"] != "accepted"]
    items.sort(key=lambda r: r["due_date"])
    return items


def accepted_items(as_of: str, client: str | None = None, db_path: str = None) -> list[dict]:
    with session(db_path) as conn:
        rows = _base_rows(conn, client)
    items = [dict(r) for r in rows if r["status"] == "accepted"]
    items.sort(key=lambda r: r["due_date"], reverse=True)
    return items
