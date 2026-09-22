"""Data, knowledge and configuration routes for the integrated control plane."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..security import require_admin
from ..services import knowledge
from ..services.lspa import run_lspa_cycle
from ..services.payload import clean_payload

router = APIRouter(prefix="/api/v1")
settings = get_settings()


class LspaCycleRequest(BaseModel):
    seed: int = 42
    top_n: int = Field(default=2, ge=1, le=10)


@router.post("/lspa/cycle")
def lspa_cycle(req: LspaCycleRequest, db: Session = Depends(get_db), _: bool = Depends(require_admin)):
    """Run the six-phase L.S.P.A. cycle (paper mode only). Records everything
    append-only in the knowledge base and returns full telemetry."""
    return run_lspa_cycle(db, seed=req.seed, top_n=req.top_n)


@router.get("/config")
def get_config(_: bool = Depends(require_admin)):
    """Safe configuration view — secret-looking keys are redacted."""
    s = settings
    return {
        "status": "success",
        "config": clean_payload(s.model_dump()),
        "mode": {
            "trading": s.trading_mode,
            "financial": s.financial_mode,
            "kill_switch": s.kill_switch,
            "allow_live_execution": s.allow_live_execution,
            "require_human_approval": s.require_human_approval,
        },
    }


@router.get("/knowledge/summary")
def knowledge_summary(db: Session = Depends(get_db)):
    return knowledge.summary(db)


@router.get("/knowledge/opportunities")
def knowledge_opportunities(limit: int = 50, db: Session = Depends(get_db)):
    return {"status": "success", "items": knowledge.recent_opportunities(db, limit)}


@router.get("/knowledge/leaderboard")
def knowledge_leaderboard(limit: int = 50, db: Session = Depends(get_db), _: bool = Depends(require_admin)):
    return {"status": "success", "items": knowledge.leaderboard(db, limit)}
