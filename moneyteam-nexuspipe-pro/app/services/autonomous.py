"""Paper-mode autonomous cycle: ingest -> verify, blocked if live modes requested."""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from ..models import Run
from .audit import audit
from .ml_checker import evaluate_iqr


async def run_cycle(db: Session, trading_mode: str, financial_mode: str) -> dict:
    run_id = f"run_{uuid.uuid4().hex[:20]}"
    row = Run(run_id=run_id, status="running", phase="start", result={})
    db.add(row)
    db.commit()

    # Phase: ingest simulated signals (paper mode only)
    signals = [round(10 + 3 * ((i * 37) % 11), 2) for i in range(20)] + [99.5]
    analysis = evaluate_iqr(signals)
    steps = [{"phase": "ingest", "result": "ok", "anomalies": analysis["anomaly_count"]}]

    if trading_mode != "paper" or financial_mode != "sandbox":
        row.status = "blocked"
        row.phase = "gate"
        row.result = {"steps": steps, "reason": "cycle supports paper/sandbox modes only"}
        db.commit()
        audit(db, "cycle_blocked", f"{run_id}: non-paper mode requested")
        return {"status": "blocked", "run_id": run_id, "steps": steps}

    row.phase = "verify"
    db.commit()
    steps.append({"phase": "verify", "result": "ok"})

    row.status = "success"
    row.phase = "complete"
    row.result = {
        "steps": steps,
        "trading_mode": trading_mode,
        "financial_mode": financial_mode,
    }
    db.commit()
    audit(db, "cycle_completed", f"{run_id} paper cycle complete")
    return {
        "status": "success",
        "run_id": run_id,
        "steps": steps,
        "modes": {"trading": trading_mode, "financial": financial_mode},
        "simulated": True,
    }
