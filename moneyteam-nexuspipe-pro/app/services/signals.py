"""Extensible signal-ingestion registry — offline / paper by default.

Every source reports honest availability telemetry. Sources that would require
network or hardware access are offline stubs: they refuse to fabricate data and
return status "offline_by_default" with zero network calls, instead of
pretending to fetch. Local sources are deterministic.
"""
from __future__ import annotations

import random
import re
import statistics

from .knowledge import record_signal
from .ml_checker import evaluate_iqr

SOURCES: dict[str, dict] = {}


def register(name: str, *, kind: str, requires_network: bool, fn) -> None:
    SOURCES[name] = {"kind": kind, "requires_network": requires_network, "fn": fn}


def available_sources() -> list[dict]:
    return [
        {
            "name": name,
            "kind": meta["kind"],
            "requires_network": meta["requires_network"],
            "status": "offline_stub" if meta["requires_network"] else "available_local",
        }
        for name, meta in SOURCES.items()
    ]


def run_source(name: str, **kwargs) -> dict:
    meta = SOURCES.get(name)
    if meta is None:
        return {
            "status": "error",
            "reason": "unknown_source",
            "available_sources": sorted(SOURCES),
        }
    if meta["requires_network"]:
        # Offline-first: no network call is made; report honestly instead of fabricating.
        return {
            "status": "offline_by_default",
            "source": name,
            "reason": "network/hardware sources are disabled in offline/paper mode",
            "telemetry": {"network_calls": 0},
        }
    return meta["fn"](**kwargs)


def ingest(db, name: str, **kwargs) -> dict:
    """Run a source and, on success, record it append-only in the knowledge base."""
    payload = run_source(name, **kwargs)
    if payload.get("status") != "success":
        return payload
    record_signal(db, name, payload)
    return {"status": "success", "source": name, "recorded": True, "payload": payload}


# --- local sources (deterministic, no network) ---


def _sim_market(symbol: str = "ETH-USDC", seed: int = 42) -> dict:
    rng = random.Random(f"{seed}:{symbol}")
    prices = [100.0]
    for _ in range(60):
        prices.append(max(0.01, prices[-1] * (1 + rng.gauss(0, 0.01))))
    analysis = evaluate_iqr([round(p, 4) for p in prices])
    return {
        "status": "success",
        "kind": "market_simulated",
        "symbol": symbol,
        "last": round(prices[-1], 4),
        "mean": round(statistics.mean(prices), 4),
        "stdev": round(statistics.pstdev(prices), 4),
        "trend": "up" if prices[-1] > prices[0] else "down",
        "anomalies": analysis.get("anomaly_count", 0),
        "analysis": analysis,
    }


def _document_text(text: str = "") -> dict:
    numbers = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text or "")]
    words = re.findall(r"\w+", text or "")
    analysis = (
        evaluate_iqr(numbers)
        if len(numbers) >= 4
        else {"status": "insufficient_data", "sample_count": len(numbers)}
    )
    return {
        "status": "success",
        "kind": "document_text",
        "word_count": len(words),
        "number_count": len(numbers),
        "numbers_detected": numbers[:50],
        "analysis": analysis,
    }


def _blockchain_paper(address: str = "") -> dict:
    rng = random.Random(f"paper:{address or 'default'}")
    return {
        "status": "success",
        "kind": "blockchain_paper",
        "address": address,
        "balances_simulated": {
            "ETH": round(rng.uniform(0, 2), 4),
            "BSC": round(rng.uniform(0, 5), 4),
            "SOL": round(rng.uniform(0, 20), 4),
        },
        "note": "paper-mode simulated balances; no chain query was made",
    }


def _offline_stub(**_kwargs) -> dict:
    raise NotImplementedError  # never called: run_source short-circuits


register("sim_market", kind="market", requires_network=False, fn=_sim_market)
register("document_text", kind="document", requires_network=False, fn=_document_text)
register("blockchain_paper", kind="blockchain", requires_network=False, fn=_blockchain_paper)
register("web_probe", kind="web", requires_network=True, fn=_offline_stub)
register("ocr_scan", kind="hardware", requires_network=True, fn=_offline_stub)
register("rf_scan", kind="hardware", requires_network=True, fn=_offline_stub)
