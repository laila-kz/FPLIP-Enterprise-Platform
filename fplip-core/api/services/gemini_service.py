"""
Gemini AI Explanation Service for FPLIP.
Uses Google Gemini API to analyze factory signals, metrics, and ML predictions.
"""

import os
import json
import httpx
from typing import Optional, Dict, Any
from api.core.config import get_settings

GEMINI_MODEL = "gemini-3.5-flash-lite"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

def get_gemini_api_key() -> str:
    settings = get_settings()
    # Check settings or direct environment variables
    key = getattr(settings, "gemini_api_key", None) or os.getenv("GEMINI_API_KEY", "")
    return key.strip()

def build_prompt(
    machine_id: str,
    signal_type: str,
    severity: str,
    context: Optional[Dict[str, Any]] = None,
    ml_risk: Optional[Dict[str, Any]] = None
) -> str:
    prompt = f"""You are an expert industrial engineering AI assistant for FPLIP (Factory Performance & Loss Intelligence Platform).
Analyze the following factory anomaly and provide an operational diagnosis and recommendations for plant managers and maintenance technicians.

### Investigation Details:
- Machine ID: {machine_id}
- Signal Type: {signal_type}
- Severity: {severity}

"""
    if context:
        prompt += f"### Machine Context & Telemetry:\n{json.dumps(context, indent=2)}\n\n"

    if ml_risk:
        prompt += f"### ML Predictive Scrap Risk:\n{json.dumps(ml_risk, indent=2)}\n\n"

    prompt += """Provide your output formatted as a valid JSON object with the following schema:
{
  "summary": "Brief 1-2 sentence executive summary of the operational issue.",
  "root_cause_analysis": "Detailed technical analysis of why this loss/scrap/downtime event is occurring based on telemetry.",
  "recommended_actions": [
    "Specific step 1 for maintenance/technician",
    "Specific step 2 for process engineer"
  ],
  "preventative_measures": [
    "Long-term preventive measure 1",
    "Long-term preventive measure 2"
  ]
}
Return only the raw JSON object, without markdown code fencing.
"""
    return prompt

async def generate_ai_explanation(
    machine_id: str,
    signal_type: str,
    severity: str,
    context: Optional[Dict[str, Any]] = None,
    ml_risk: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    api_key = get_gemini_api_key()
    if not api_key:
        return _fallback_explanation(machine_id, signal_type, severity, "Gemini API key is not configured.")

    prompt = build_prompt(machine_id, signal_type, severity, context, ml_risk)

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json"
        }
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{GEMINI_API_URL}?key={api_key}",
                json=payload
            )

            if resp.status_code == 200:
                data = resp.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.startswith("```"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()
                
                try:
                    parsed = json.loads(raw_text)
                    return {
                        "status": "success",
                        "model": GEMINI_MODEL,
                        "explanation": parsed
                    }
                except json.JSONDecodeError:
                    return {
                        "status": "success",
                        "model": GEMINI_MODEL,
                        "explanation": {
                            "summary": raw_text[:200],
                            "root_cause_analysis": raw_text,
                            "recommended_actions": ["Inspect machine tooling and feed rates.", "Review recent sensor telemetry."],
                            "preventative_measures": ["Calibrate vibration sensors.", "Schedule preventive maintenance."]
                        }
                    }
            else:
                error_msg = f"Gemini API returned status {resp.status_code}: {resp.text}"
                print(f"[Gemini Error] {error_msg}")
                return _fallback_explanation(machine_id, signal_type, severity, error_msg)

    except Exception as e:
        print(f"[Gemini Exception] {str(e)}")
        return _fallback_explanation(machine_id, signal_type, severity, str(e))

def _fallback_explanation(machine_id: str, signal_type: str, severity: str, reason: str) -> Dict[str, Any]:
    """Generates an intelligent contextual fallback if Gemini is temporarily unreachable."""
    if signal_type == "oee_drop":
        summary = f"Machine {machine_id} experienced an acute OEE drop driven by unexpected availability and performance losses."
        root_causes = "Analysis indicates speed throttling and micro-stoppages during shift changeovers, contributing to degraded cycle efficiency."
        actions = [
            "Inspect mechanical drive belts and bearings for thermal wear.",
            "Verify cycle time calibration against standard part specification.",
            "Check operator changeover checklist compliance."
        ]
        preventative = [
            "Implement automated feed rate telemetry monitoring.",
            "Recalibrate servo positioning sensors during weekly PM."
        ]
    elif signal_type == "scrap_spike":
        summary = f"Elevated scrap rate detected on {machine_id} exceeding acceptable quality threshold ({severity} severity)."
        root_causes = "Excessive thermal expansion and tool deflection during high-feed cutting cycles resulted in out-of-spec dimensions."
        actions = [
            "Check cutting insert edge wear and coolant flow rate.",
            "Verify raw material batch tolerance and hardness.",
            "Perform test cut and measure critical surface tolerance with micrometer."
        ]
        preventative = [
            "Adjust cutting feed rate down by 8% for high-hardness alloy batches.",
            "Enforce mandatory tool change intervals every 450 cycles."
        ]
    else:
        summary = f"Unplanned downtime event recorded on {machine_id} requiring immediate maintenance investigation."
        root_causes = "Safety interlock trip or hydraulic pressure drop triggered an automatic machine emergency halt."
        actions = [
            "Inspect hydraulic fluid pressure levels and pump seals.",
            "Review PLC error logs for intermittent electrical faults.",
            "Test emergency stop circuit and interlock sensors."
        ]
        preventative = [
            "Replace hydraulic filter cartridge.",
            "Schedule quarterly sensor validation audit."
        ]

    return {
        "status": "fallback",
        "model": "rule-based-engine",
        "fallback_reason": reason,
        "explanation": {
            "summary": summary,
            "root_cause_analysis": root_causes,
            "recommended_actions": actions,
            "preventative_measures": preventative
        }
    }
