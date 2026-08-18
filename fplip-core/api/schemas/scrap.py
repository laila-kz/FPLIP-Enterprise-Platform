"""
Pydantic schemas for Scrap endpoints.
"""

from datetime import date
from typing import Optional
from pydantic import BaseModel


class ScrapRootCauseRow(BaseModel):
    """One row from scrap_root_cause_summary."""
    machine_id: str
    shift_id: str
    date_id: date
    product_id: str
    defect_type_id: str
    defect_name: str
    defect_category: str
    severity: str
    total_units_inspected: int
    total_units_rejected: int
    rejection_rate: Optional[float] = None
    total_scrap_units: Optional[int] = None
    scrap_percentage: Optional[float] = None
    inspection_count: int