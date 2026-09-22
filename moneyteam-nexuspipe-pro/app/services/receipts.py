"""Persistent execution receipts — no verified receipt, no claimed execution."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models import Receipt


def _evidence_hash(evidence: dict) -> str:
    canonical = json.dumps(evidence, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def make_receipt(db: Session, operation: str, status: str, verified: bool, evidence: dict) -> Receipt:
    evidence = dict(evidence or {})
    evidence["evidence_sha256"] = _evidence_hash(evidence)
    row = Receipt(
        receipt_id=f"rcpt_{uuid.uuid4().hex[:24]}",
        operation=operation,
        status=status,
        verified=verified,
        evidence=evidence,
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def serialize_receipt(row: Receipt) -> dict:
    return {
        "receipt_id": row.receipt_id,
        "operation": row.operation,
        "status": row.status,
        "verified": row.verified,
        "evidence": row.evidence,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }
