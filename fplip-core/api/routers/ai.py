"""
AI Router for FPLIP API.
Provides AI-powered operational explanations and diagnostic insights via Gemini.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from api.services.gemini_service import generate_ai_explanation

router = APIRouter(prefix="/ai", tags=["ai"])

class ExplainRequest(BaseModel):
    machine_id: str
    signal_type: str
    severity: str
    context: Optional[Dict[str, Any]] = None
    ml_risk: Optional[Dict[str, Any]] = None

class ExplanationContent(BaseModel):
    summary: str
    root_cause_analysis: str
    recommended_actions: List[str]
    preventative_measures: List[str]

class ExplainResponse(BaseModel):
    status: str
    model: str
    explanation: ExplanationContent
    fallback_reason: Optional[str] = None

@router.post("/explain", response_model=ExplainResponse)
async def explain_anomaly(request: ExplainRequest):
    """
    Generate an AI-powered diagnostic explanation for an anomalous machine signal
    using Google Gemini, incorporating performance metrics, loss attribution,
    scrap defect patterns, and ML risk scores.
    """
    result = await generate_ai_explanation(
        machine_id=request.machine_id,
        signal_type=request.signal_type,
        severity=request.severity,
        context=request.context,
        ml_risk=request.ml_risk
    )
    return result
