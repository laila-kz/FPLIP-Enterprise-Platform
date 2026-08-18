"""
Scrap endpoints for the FPLIP API.
"""

from fastapi import APIRouter, Depends, Query
from datetime import date
from typing import Optional
import hashlib
import json
from google.cloud import bigquery
from api.dependencies.bigquery import get_bigquery_client
from api.schemas.scrap import ScrapRootCauseRow
from api.cache.ttl_cache import TTLCache
from api.core.config import get_settings
from api.core.errors import run_query_safely, validate_date_range

router = APIRouter(prefix="/scrap", tags=["scrap"])

_settings = get_settings()
scrap_cache = TTLCache(ttl_seconds=_settings.cache_ttl_seconds)


def _cache_key(endpoint: str, params: dict) -> str:
    key_string = endpoint + ":" + json.dumps(params, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()


@router.get("/root-cause", response_model=list[ScrapRootCauseRow])
def get_scrap_root_cause(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    machine_id: Optional[str] = Query(None, description="Filter by machine ID"),
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    defect_category: Optional[str] = Query(None, description="Filter by defect category"),
    client: Optional[bigquery.Client] = Depends(get_bigquery_client),
):
    """
    Get scrap root cause analysis by defect type.
    """
    validate_date_range(start_date, end_date)
    
    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "machine_id": machine_id,
        "product_id": product_id,
        "defect_category": defect_category,
    }
    cache_key = _cache_key("scrap_root_cause", params)
    cached_response = scrap_cache.get(cache_key)
    if cached_response is not None:
        return cached_response
    
    dataset_ref = f"`{_settings.project_id}.{_settings.gold_dataset}`"
    query = f"""
        SELECT 
            machine_id,
            shift_id,
            date_id,
            product_id,
            defect_type_id,
            defect_name,
            defect_category,
            severity,
            total_units_inspected,
            total_units_rejected,
            rejection_rate,
            total_scrap_units,
            scrap_percentage,
            inspection_count
        FROM {dataset_ref}.scrap_root_cause_summary
        WHERE date_id BETWEEN @start_date AND @end_date
          AND (@machine_id IS NULL OR machine_id = @machine_id)
          AND (@product_id IS NULL OR product_id = @product_id)
          AND (@defect_category IS NULL OR defect_category = @defect_category)
        ORDER BY date_id, machine_id, product_id, defect_category
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
            bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            bigquery.ScalarQueryParameter("machine_id", "STRING", machine_id),
            bigquery.ScalarQueryParameter("product_id", "STRING", product_id),
            bigquery.ScalarQueryParameter("defect_category", "STRING", defect_category),
        ]
    )
    
    results = run_query_safely(client, query, job_config, timeout=30)
    response = [dict(row) for row in results]
    scrap_cache.set(cache_key, response)
    return response