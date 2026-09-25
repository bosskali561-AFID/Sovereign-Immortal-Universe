"""Signal ingestion routes."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..security import require_admin
from ..services import signals

router = APIRouter(prefix="/api/v1")


class IngestRequest(BaseModel):
    source: str
    params: dict = {}


@router.get("/signals/sources")
def list_sources():
    """Honest availability telemetry for every registered signal source."""
    return {"status": "success", "sources": signals.available_sources()}


@router.post("/signals/ingest")
def ingest_signal(req: IngestRequest, db: Session = Depends(get_db), _: bool = Depends(require_admin)):
    """Run one signal source. On success the payload is recorded append-only
    in the knowledge base. Offline stubs return offline_by_default (no fabrication)."""
    return signals.ingest(db, req.source, **req.params)
