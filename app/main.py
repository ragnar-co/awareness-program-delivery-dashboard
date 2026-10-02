import os
from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import ai_workflow, analytics
from .db import init_db, session
from .ingest import ingest_csv_file, ingest_csv_text

APP_DIR = os.path.dirname(__file__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    seed_path = os.environ.get("DASHBOARD_CSV_PATH")
    if seed_path and os.path.exists(seed_path):
        with session() as conn:
            (count,) = conn.execute("SELECT COUNT(*) FROM deliverables").fetchone()
        if count == 0:
            ingest_csv_file(seed_path)
    yield


app = FastAPI(title="Awareness Program Delivery Dashboard", lifespan=lifespan)


def _default_as_of() -> str:
    override = os.environ.get("DASHBOARD_AS_OF")
    return override if override else date.today().isoformat()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/clients")
def clients() -> dict:
    return {"clients": analytics.get_clients()}


@app.get("/api/summary")
def summary(
    client: str | None = Query(default=None),
    as_of: str | None = Query(default=None),
) -> dict:
    return analytics.summarize(as_of or _default_as_of(), client)


@app.get("/api/deliverables/pending-acceptance")
def pending(
    client: str | None = Query(default=None),
    as_of: str | None = Query(default=None),
) -> dict:
    resolved_as_of = as_of or _default_as_of()
    return {"as_of": resolved_as_of, "items": analytics.pending_acceptance(resolved_as_of, client)}


@app.get("/api/deliverables/overdue")
def overdue(
    client: str | None = Query(default=None),
    as_of: str | None = Query(default=None),
) -> dict:
    resolved_as_of = as_of or _default_as_of()
    return {"as_of": resolved_as_of, "items": analytics.overdue_items(resolved_as_of, client)}


@app.get("/api/deliverables/accepted")
def accepted(
    client: str | None = Query(default=None),
    as_of: str | None = Query(default=None),
) -> dict:
    resolved_as_of = as_of or _default_as_of()
    return {"as_of": resolved_as_of, "items": analytics.accepted_items(resolved_as_of, client)}


@app.post("/api/ingest")
async def ingest(file: UploadFile = File(...)) -> dict:
    content = (await file.read()).decode("utf-8-sig")
    report = ingest_csv_text(content, source_file=file.filename)
    return report


@app.post("/api/ai/draft-update")
def draft_update(client: str, as_of: str | None = None) -> dict:
    resolved_as_of = as_of or _default_as_of()
    try:
        return ai_workflow.generate_draft(client, resolved_as_of)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/ai/drafts")
def drafts(client: str | None = Query(default=None)) -> dict:
    return {"drafts": ai_workflow.list_drafts(client)}


app.mount("/static", StaticFiles(directory=os.path.join(APP_DIR, "static")), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(APP_DIR, "static", "index.html"))
