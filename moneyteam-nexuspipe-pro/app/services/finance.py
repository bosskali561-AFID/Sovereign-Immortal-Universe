"""Sandbox-only transaction processing. Live rails are refused by default."""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from ..models import Transaction


def process_transaction(db: Session, tx_id: str, rail: str, amount: float, mode: str) -> dict:
    if mode != "sandbox":
        raise RuntimeError(
            f"FINANCIAL_MODE={mode} is not enabled; live processing requires explicit approval"
        )
    if amount <= 0:
        raise ValueError("amount must be positive")
    if db.query(Transaction).filter_by(tx_id=tx_id).first():
        raise ValueError(f"tx_id {tx_id} already exists")
    row = Transaction(tx_id=tx_id, rail=rail, amount=amount, status="sandbox_simulated")
    db.add(row)
    db.commit()
    return {
        "status": "success",
        "tx_id": tx_id,
        "rail": rail,
        "amount": amount,
        "mode": "sandbox",
        "simulated": True,
        "reference": f"sim_{uuid.uuid4().hex[:16]}",
    }
