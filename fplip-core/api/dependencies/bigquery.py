"""
BigQuery client dependency for the FPLIP API.
"""

from functools import lru_cache
from typing import Optional
from google.cloud import bigquery
from google.auth.exceptions import DefaultCredentialsError

@lru_cache
def get_bigquery_client() -> Optional[bigquery.Client]:
    """
    Return a singleton BigQuery client, or None if credentials are not configured.
    """
    try:
        return bigquery.Client()
    except (DefaultCredentialsError, Exception) as e:
        print(f"[BigQuery Notice] BigQuery client offline: {e}")
        return None