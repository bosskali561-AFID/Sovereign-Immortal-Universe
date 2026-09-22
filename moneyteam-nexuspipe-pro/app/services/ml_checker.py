"""IQR-based anomaly detection."""
from __future__ import annotations


def _quantile(sorted_values: list[float], p: float) -> float:
    n = len(sorted_values)
    k = (n - 1) * p
    f = int(k)
    c = min(f + 1, n - 1)
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)


def evaluate_iqr(values: list[float]) -> dict:
    if len(values) < 4:
        return {"status": "error", "reason": "at least 4 values required"}
    ordered = sorted(values)
    q1 = _quantile(ordered, 0.25)
    q3 = _quantile(ordered, 0.75)
    iqr = q3 - q1
    low = q1 - 1.5 * iqr
    high = q3 + 1.5 * iqr
    anomalies = [
        {
            "index": i,
            "value": v,
            "severity": "high" if (v < low - 1.5 * iqr or v > high + 1.5 * iqr) else "moderate",
        }
        for i, v in enumerate(values)
        if v < low or v > high
    ]
    return {
        "status": "success",
        "sample_count": len(values),
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "lower_fence": low,
        "upper_fence": high,
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
    }
