"""Local LLM (Ollama) integration — the natural-language explanation engine.

Offline-first posture:
- Disabled by default (LOCAL_LLM_ENABLED=false); no network call unless enabled.
- Never claims a model is loaded without telemetry: `local_llm_status()` probes
  the runtime and returns the actual model list.
- When Ollama is disabled or unreachable, a deterministic template fallback
  explains the anomalies — and the `source` field says which one produced it.
"""
from __future__ import annotations

import json
import urllib.request

from ..config import get_settings


def _probe(base_url: str, path: str, payload: dict | None = None, timeout: float = 2.0):
    url = base_url.rstrip("/") + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def local_llm_status() -> dict:
    """Honest telemetry: is a local model actually reachable right now?"""
    s = get_settings()
    if not s.local_llm_enabled:
        return {
            "available": False,
            "source": "disabled",
            "model": s.local_llm_model,
            "runtime": "unavailable",
        }
    try:
        tags = _probe(s.local_llm_url, "/api/tags", timeout=1.5)
        models = [m.get("name") for m in tags.get("models", [])]
        return {
            "available": bool(models),
            "source": "ollama",
            "runtime": "gguf_ollama",
            "model": s.local_llm_model,
            "models": models,
        }
    except Exception as exc:
        return {
            "available": False,
            "source": "unreachable",
            "runtime": "unavailable",
            "model": s.local_llm_model,
            "error": type(exc).__name__,
        }


def _template_explanation(analysis: dict) -> str:
    n = analysis.get("anomaly_count", 0)
    base = (
        f"IQR analysis of {analysis.get('sample_count', 'the')} values: "
        f"Q1={analysis.get('q1')}, Q3={analysis.get('q3')}, IQR={analysis.get('iqr')}. "
        f"Acceptable range [{analysis.get('lower_fence')}, {analysis.get('upper_fence')}]. "
    )
    if n == 0:
        return base + "No anomalies: every value falls within the fences."
    parts = [base + f"{n} anomal{'y' if n == 1 else 'ies'} detected:"]
    for a in analysis.get("anomalies", [])[:5]:
        position = "above the upper fence" if a.get("value", 0) > analysis.get("upper_fence", 0) else "below the lower fence"
        parts.append(
            f" value {a.get('value')} at index {a.get('index')} is a {a.get('severity')} outlier, {position}."
        )
    return "".join(parts)


def explain_anomalies(analysis: dict) -> dict:
    """Natural-language explanation of IQR anomalies. Local Ollama when enabled
    and reachable; deterministic template fallback otherwise. The `source` field
    always states honestly which engine produced the text."""
    s = get_settings()
    status = local_llm_status()
    if status["available"]:
        try:
            prompt = (
                "You are an anomaly explanation engine for a fintech control plane. "
                "Explain these IQR results in plain language for an operator, max 120 words. "
                f"Data: {json.dumps(analysis)}"
            )
            resp = _probe(
                s.local_llm_url,
                "/api/chat",
                payload={
                    "model": s.local_llm_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                },
                timeout=s.provider_timeout_seconds,
            )
            text = (resp.get("message") or {}).get("content", "").strip()
            if text:
                return {"source": "ollama", "model": s.local_llm_model, "text": text}
        except Exception:
            pass  # fall through to template — never fabricate LLM output
    return {"source": "template", "model": None, "text": _template_explanation(analysis)}
