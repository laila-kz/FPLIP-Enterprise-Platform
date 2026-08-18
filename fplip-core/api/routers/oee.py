"""
OEE endpoints for the FPLIP API.
"""

from fastapi import APIRouter, Depends, Query
from datetime import date
from typing import Optional
import hashlib
import json
from google.cloud import bigquery
from api.dependencies.bigquery import get_bigquery_client
from api.schemas.oee import OeeDailyRow, OeeSummaryRow
from api.cache.ttl_cache import TTLCache
from api.core.config import get_settings
from api.core.errors import run_query_safely, validate_date_range

router = APIRouter(prefix="/oee", tags=["oee"])

# Initialize cache with TTL from settings
_settings = get_settings()
oee_cache = TTLCache(ttl_seconds=_settings.cache_ttl_seconds)


def _cache_key(endpoint: str, params: dict) -> str:
    """Generate a cache key from endpoint name and parameters."""
    key_string = endpoint + ":" + json.dumps(params, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()


@router.get("/daily", response_model=list[OeeDailyRow])
def get_oee_daily(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    machine_id: Optional[str] = Query(None, description="Filter by machine ID"),
    client: Optional[bigquery.Client] = Depends(get_bigquery_client),
):
    """
    Get daily OEE data for a date range.
    """
    # Validate date range
    validate_date_range(start_date, end_date)
    
    # Check cache
    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "machine_id": machine_id,
    }
    cache_key = _cache_key("oee_daily", params)
    cached_response = oee_cache.get(cache_key)
    if cached_response is not None:
        return cached_response
    
    dataset_ref = f"`{_settings.project_id}.{_settings.gold_dataset}`"
    query = f"""
        SELECT 
            machine_id,
            shift_id,
            date_id,
            availability,
            performance,
            quality,
            oee,
            cycle_time_confidence,
            availability_loss_sec,
            performance_loss_sec,
            unmapped_loss_sec
        FROM {dataset_ref}.oee_daily
        WHERE date_id BETWEEN @start_date AND @end_date
          AND (@machine_id IS NULL OR machine_id = @machine_id)
        ORDER BY date_id, machine_id, shift_id
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
            bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            bigquery.ScalarQueryParameter("machine_id", "STRING", machine_id),
        ]
    )
    
    # Use the safe query runner
    results = run_query_safely(client, query, job_config, timeout=30)
    response = [dict(row) for row in results]
    
    # Cache the response
    oee_cache.set(cache_key, response)
    return response


@router.get("/summary", response_model=list[OeeSummaryRow])
def get_oee_summary(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    machine_id: Optional[str] = Query(None, description="Filter by machine ID"),
    client: Optional[bigquery.Client] = Depends(get_bigquery_client),
):
    """
    Get aggregated OEE summary by machine for a date range.
    """
    validate_date_range(start_date, end_date)
    
    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "machine_id": machine_id,
    }
    cache_key = _cache_key("oee_summary", params)
    cached_response = oee_cache.get(cache_key)
    if cached_response is not None:
        return cached_response
    
    dataset_ref = f"`{_settings.project_id}.{_settings.gold_dataset}`"
    query = f"""
        SELECT 
            machine_id,
            AVG(oee) as avg_oee,
            AVG(availability) as avg_availability,
            AVG(performance) as avg_performance,
            AVG(quality) as avg_quality,
            COUNT(DISTINCT date_id) as total_days
        FROM {dataset_ref}.oee_daily
        WHERE date_id BETWEEN @start_date AND @end_date
          AND (@machine_id IS NULL OR machine_id = @machine_id)
        GROUP BY machine_id
        ORDER BY machine_id
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
            bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            bigquery.ScalarQueryParameter("machine_id", "STRING", machine_id),
        ]
    )
    
    results = run_query_safely(client, query, job_config, timeout=30)
    response = [dict(row) for row in results]
    oee_cache.set(cache_key, response)
    return response