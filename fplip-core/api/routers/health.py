"""
Health check router for the FPLIP API.
"""

from fastapi import APIRouter
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import bigquery

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check():
    """
    Health check endpoint - PUBLIC (no API key required).
    
    Returns:
        - app: "ok" if the app is running
        - bigquery: "ok" if BigQuery connection works, or error message if not
    """
    app_status = "ok"
    bigquery_status = "ok"
    
    try:
        client = bigquery.Client()
        list(client.query("SELECT 1").result())
    except DefaultCredentialsError as e:
        bigquery_status = f"error: {str(e)}"
    except Exception as e:
        bigquery_status = f"error: {str(e)}"
    
    return {"app": app_status, "bigquery": bigquery_status}