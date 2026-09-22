"""ML route: anomaly explanation (natural-language engine)."""
from fastapi import APIRouter
from pydantic import BaseModel

from ..services.local_llm import explain_anomalies
from ..services.ml_checker import evaluate_iqr

router = APIRouter(prefix="/api/v1")


class ValuesRequest(BaseModel):
    values: list[float]


@router.post("/ml/explain")
def ml_explain(req: ValuesRequest):
    """IQR anomaly analysis plus a natural-language explanation.
    Explanation source is honestly reported (ollama vs template fallback)."""
    analysis = evaluate_iqr(req.values)
    if analysis.get("status") != "success":
        return analysis
    explanation = explain_anomalies(analysis)
    return {"status": "success", "analysis": analysis, "explanation": explanation}
