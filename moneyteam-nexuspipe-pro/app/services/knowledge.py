"""Additive knowledge base — every signal, opportunity, winner and failure is
recorded append-only. Records are never mutated or deleted; the system learns
from the full history."""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import Failure, Opportunity, SignalRaw, Winner


def record_signal(db: Session, source: str, payload: dict) -> SignalRaw:
    row = SignalRaw(source=source, payload=payload or {})
    db.add(row)
    db.commit()
    return row


def record_opportunity(
    db: Session, symbol: str, ept: float, action: str, phase: str, status: str, payload: dict
) -> Opportunity:
    row = Opportunity(
        symbol=symbol, ept=ept, action=action, phase=phase, status=status, payload=payload or {}
    )
    db.add(row)
    db.commit()
    return row


def record_winner(db: Session, symbol: str, pnl_paper: float, strategy_dna: dict) -> Winner:
    row = Winner(symbol=symbol, pnl_paper=pnl_paper, strategy_dna=strategy_dna or {})
    db.add(row)
    db.commit()
    return row


def record_failure(db: Session, symbol: str, reason: str, autopsy: dict) -> Failure:
    row = Failure(symbol=symbol, reason=reason[:200], autopsy=autopsy or {})
    db.add(row)
    db.commit()
    return row


def summary(db: Session) -> dict:
    return {
        "signals_raw": db.query(SignalRaw).count(),
        "opportunities": db.query(Opportunity).count(),
        "winners": db.query(Winner).count(),
        "failures": db.query(Failure).count(),
        "policy": "append_only_never_deleted",
    }


def recent_opportunities(db: Session, limit: int = 50) -> list[dict]:
    rows = db.query(Opportunity).order_by(Opportunity.id.desc()).limit(max(1, min(limit, 500))).all()
    return [
        {
            "id": r.id,
            "symbol": r.symbol,
            "ept": r.ept,
            "action": r.action,
            "phase": r.phase,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


def leaderboard(db: Session, limit: int = 50) -> list[dict]:
    rows = (
        db.query(Winner)
        .order_by(Winner.pnl_paper.desc())
        .limit(max(1, min(limit, 500)))
        .all()
    )
    return [
        {
            "symbol": r.symbol,
            "pnl_paper": r.pnl_paper,
            "strategy_dna": r.strategy_dna,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
