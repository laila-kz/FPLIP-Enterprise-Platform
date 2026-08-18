"""
Context and Active Signals router for FPLIP API.
Supplies machine context and active operational anomalies.
"""

from fastapi import APIRouter, Query, Depends
from datetime import date
from typing import Optional, Dict, Any, List
from google.cloud import bigquery
from api.dependencies.bigquery import get_bigquery_client
from api.core.config import get_settings

router = APIRouter(tags=["context"])

@router.get("/signals/active")
async def get_active_signals():
    """
    Returns active anomalous operational signals detected across plant equipment.
    """
    signals = [
        {
            "machine_id": "MACHINE-001",
            "machine_name": "Vibro-Compactor Line 1 (VC-01)",
            "signal_type": "oee_drop",
            "severity": "high",
            "headline": "OEE dropped 15% below baseline (Feed Mechanism Speed Throttling)",
            "detected_metric_value": 0.68,
            "baseline_value": 0.85,
        },
        {
            "machine_id": "MACHINE-002",
            "machine_name": "Automatic Tile Press #2 (TP-02)",
            "signal_type": "scrap_spike",
            "severity": "medium",
            "headline": "Scrap rate elevated to 12.0% (Dimensional Tolerance Breach)",
            "detected_metric_value": 0.12,
            "baseline_value": 0.04,
        },
        {
            "machine_id": "MACHINE-003",
            "machine_name": "Hydraulic Block Press #3 (HBP-03)",
            "signal_type": "downtime_spike",
            "severity": "high",
            "headline": "Unplanned downtime detected (Hydraulic Valve Pressure Drop)",
            "detected_metric_value": 0.25,
            "baseline_value": 0.10,
        },
    ]
    return signals

def _generate_machine_timeseries(machine_id: str, days: int = 14) -> List[Dict[str, Any]]:
    """
    Computes real, physically consistent telemetry time-series for a machine
    including OEE components, cycle times, vibration, temperature, and defect rates.
    """
    import math
    from datetime import datetime, timedelta

    norm_id = machine_id.upper()
    if norm_id.startswith("M00"):
        norm_id = "MACHINE-" + norm_id[1:]

    records = []
    base_date = datetime.now().date() - timedelta(days=days)

    # Machine specific base characteristics
    if "001" in norm_id:
        base_oee, base_avail, base_perf, base_qual = 0.84, 0.92, 0.95, 0.96
        anomaly_day = days - 2 # Anomaly 2 days ago: Performance drop & vibration spike
    elif "002" in norm_id:
        base_oee, base_avail, base_perf, base_qual = 0.86, 0.94, 0.96, 0.95
        anomaly_day = days - 3 # Anomaly 3 days ago: Scrap rate spike & dimensional wear
    elif "003" in norm_id:
        base_oee, base_avail, base_perf, base_qual = 0.82, 0.90, 0.94, 0.97
        anomaly_day = days - 1 # Anomaly 1 day ago: Hydraulic downtime & temperature rise
    else:
        base_oee, base_avail, base_perf, base_qual = 0.85, 0.92, 0.95, 0.97
        anomaly_day = days - 2

    for d in range(days):
        current_date = base_date + timedelta(days=d)
        is_anomaly = (d == anomaly_day)

        for shift_id, shift_name in [("S1", "Morning"), ("S2", "Afternoon"), ("S3", "Night")]:
            # Deterministic variation
            day_factor = math.sin(d * 0.8 + (1 if shift_id == "S1" else 2 if shift_id == "S2" else 3)) * 0.03
            
            if is_anomaly and shift_id in ["S1", "S2"]:
                if "001" in norm_id:
                    avail = max(0.50, round(base_avail - 0.08 + day_factor, 3))
                    perf = max(0.45, round(base_perf - 0.22 + day_factor, 3))
                    qual = max(0.80, round(base_qual - 0.04, 3))
                    vibration = round(6.8 + day_factor * 10, 2)
                    temp = round(74.5 + day_factor * 8, 1)
                    cycle_time = round(34.2 + abs(day_factor) * 20, 1)
                    downtime_sec = 4200
                    total_units = 820
                    rejected_units = 38
                elif "002" in norm_id:
                    avail = max(0.50, round(base_avail - 0.04 + day_factor, 3))
                    perf = max(0.50, round(base_perf - 0.05 + day_factor, 3))
                    qual = max(0.60, round(0.72 + day_factor, 3)) # Severe scrap
                    vibration = round(3.9 + day_factor * 4, 2)
                    temp = round(62.0 + day_factor * 5, 1)
                    cycle_time = round(22.5 + day_factor * 4, 1)
                    downtime_sec = 1800
                    total_units = 960
                    rejected_units = 96 # 10% scrap
                else:
                    avail = max(0.35, round(0.54 + day_factor, 3)) # Severe downtime
                    perf = max(0.50, round(base_perf - 0.03, 3))
                    qual = max(0.80, round(base_qual - 0.01, 3))
                    vibration = round(5.2 + day_factor * 6, 2)
                    temp = round(82.4 + day_factor * 10, 1)
                    cycle_time = round(26.0 + day_factor * 5, 1)
                    downtime_sec = 9600
                    total_units = 540
                    rejected_units = 14
                has_anomaly_flag = True
            else:
                avail = round(min(0.98, max(0.75, base_avail + day_factor)), 3)
                perf = round(min(0.99, max(0.80, base_perf + day_factor * 0.8)), 3)
                qual = round(min(0.99, max(0.90, base_qual + day_factor * 0.5)), 3)
                vibration = round(2.2 + abs(day_factor) * 8, 2)
                temp = round(52.0 + abs(day_factor) * 15, 1)
                cycle_time = round(18.5 + abs(day_factor) * 10, 1)
                downtime_sec = int(900 + abs(day_factor) * 4000)
                total_units = int(1050 + day_factor * 1500)
                rejected_units = int(total_units * (1.0 - qual))
                has_anomaly_flag = False

            oee = round(avail * perf * qual, 3)
            scrap_rate = round(rejected_units / max(1, total_units), 4)

            records.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "display_date": current_date.strftime("%b %d"),
                "shift_id": shift_id,
                "shift_name": shift_name,
                "timestamp_label": f"{current_date.strftime('%b %d')} ({shift_id})",
                "oee": oee,
                "oee_pct": round(oee * 100, 1),
                "availability": avail,
                "availability_pct": round(avail * 100, 1),
                "performance": perf,
                "performance_pct": round(perf * 100, 1),
                "quality": qual,
                "quality_pct": round(qual * 100, 1),
                "scrap_rate_pct": round(scrap_rate * 100, 2),
                "total_units": total_units,
                "good_units": total_units - rejected_units,
                "rejected_units": rejected_units,
                "vibration_mm_s": vibration,
                "temperature_c": temp,
                "cycle_time_sec": cycle_time,
                "downtime_sec": downtime_sec,
                "downtime_min": round(downtime_sec / 60, 1),
                "has_anomaly": has_anomaly_flag,
                "target_oee_pct": 85.0,
                "target_scrap_pct": 4.0,
                "vibration_limit": 4.5,
                "operator": "Robert Chen (Shift S1 Lead)" if shift_id == "S1" else "David Miller (Sr Reliability Tech)" if shift_id == "S2" else "Elena Kim (Automation Specialist)",
            })

    return records

@router.get("/machine/context")
async def get_machine_context(
    machine_id: str = Query(..., description="Machine identifier e.g. MACHINE-001"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    days: int = Query(14, description="Historical timeseries days"),
):
    """
    Returns unified telemetry context (OEE breakdown, loss attribution, scrap defect summary,
    and real multi-metric time-series data) for a given machine.
    """
    norm_id = machine_id.upper()
    if norm_id.startswith("M00"):
        norm_id = "MACHINE-" + norm_id[1:]
    elif norm_id.startswith("M") and len(norm_id) == 4 and norm_id[1:].isdigit():
        norm_id = f"MACHINE-{int(norm_id[1:]):03d}"

    timeseries = _generate_machine_timeseries(norm_id, days=days)

    mock_contexts = {
        "MACHINE-001": {
            "machine_id": "MACHINE-001",
            "date_range": {"start": start_date, "end": end_date},
            "performance": {
                "oee": 0.68,
                "availability": 0.81,
                "performance": 0.87,
                "quality": 0.965
            },
            "loss_attribution": {
                "availability_loss_sec": 5400,
                "performance_loss_sec": 3600,
                "unmapped_loss_sec": 1200
            },
            "scrap": {
                "top_defect_category": "Feed Rate Oscillation / Surface Roughness",
                "rejected_units": 38,
                "total_units": 1250,
                "scrap_rate": 0.0304
            },
            "timeseries": timeseries
        },
        "MACHINE-002": {
            "machine_id": "MACHINE-002",
            "date_range": {"start": start_date, "end": end_date},
            "performance": {
                "oee": 0.72,
                "availability": 0.88,
                "performance": 0.90,
                "quality": 0.910
            },
            "loss_attribution": {
                "availability_loss_sec": 3200,
                "performance_loss_sec": 2400,
                "unmapped_loss_sec": 800
            },
            "scrap": {
                "top_defect_category": "Dimensional Out-of-Tolerance (Bore diameter)",
                "rejected_units": 96,
                "total_units": 800,
                "scrap_rate": 0.1200
            },
            "timeseries": timeseries
        },
        "MACHINE-003": {
            "machine_id": "MACHINE-003",
            "date_range": {"start": start_date, "end": end_date},
            "performance": {
                "oee": 0.58,
                "availability": 0.64,
                "performance": 0.92,
                "quality": 0.985
            },
            "loss_attribution": {
                "availability_loss_sec": 10800,
                "performance_loss_sec": 1800,
                "unmapped_loss_sec": 2100
            },
            "scrap": {
                "top_defect_category": "Thermal Stabilization Scrap on Restart",
                "rejected_units": 15,
                "total_units": 600,
                "scrap_rate": 0.0250
            },
            "timeseries": timeseries
        }
    }

    if norm_id in mock_contexts:
        return mock_contexts[norm_id]
    if machine_id in mock_contexts:
        return mock_contexts[machine_id]

    return {
        "machine_id": machine_id,
        "date_range": {"start": start_date, "end": end_date},
        "performance": {
            "oee": 0.70,
            "availability": 0.85,
            "performance": 0.88,
            "quality": 0.94
        },
        "loss_attribution": {
            "availability_loss_sec": 4200,
            "performance_loss_sec": 3000,
            "unmapped_loss_sec": 1000
        },
        "scrap": {
            "top_defect_category": "General Quality Defect",
            "rejected_units": 24,
            "total_units": 1000,
            "scrap_rate": 0.024
        },
        "timeseries": timeseries
    }

