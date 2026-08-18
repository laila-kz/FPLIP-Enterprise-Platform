"""
Pydantic schemas for OEE endpoints.
"""

from datetime import date
from typing import Optional
from pydantic import BaseModel


class OeeDailyRow(BaseModel):
    """One row from oee_daily."""
    machine_id: str
    shift_id: str
    date_id: date
    availability: Optional[float] = None
    performance: Optional[float] = None
    quality: Optional[float] = None
    oee: Optional[float] = None
    cycle_time_confidence: str
    availability_loss_sec: int
    performance_loss_sec: int
    unmapped_loss_sec: int


class OeeSummaryRow(BaseModel):
    """Aggregated OEE summary by machine."""
    machine_id: str
    avg_oee: Optional[float] = None
    avg_availability: Optional[float] = None
    avg_performance: Optional[float] = None
    avg_quality: Optional[float] = None
    total_days: int