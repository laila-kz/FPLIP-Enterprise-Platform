"""
BigQuery client dependency for the FPLIP API.
Supports standard GCP credentials, GOOGLE_APPLICATION_CREDENTIALS path,
and GCP_SA_KEY / GOOGLE_CREDENTIALS_JSON env vars (direct JSON or Base64) for serverless deployments like Vercel.
"""

import os
import json
import base64
from functools import lru_cache
from typing import Optional
from google.cloud import bigquery
from google.oauth2 import service_account
from google.auth.exceptions import DefaultCredentialsError


@lru_cache
def get_bigquery_client() -> Optional[bigquery.Client]:
    """
    Return a singleton BigQuery client.
    Supports GCP_SA_KEY / GOOGLE_CREDENTIALS_JSON env vars (direct JSON or Base64)
    as well as GOOGLE_APPLICATION_CREDENTIALS file path.
    """
    # 1. Check for raw JSON or Base64 environment variable (ideal for Vercel / serverless)
    for env_var in ("GCP_SA_KEY", "GOOGLE_CREDENTIALS_JSON", "GOOGLE_APPLICATION_CREDENTIALS_JSON"):
        sa_raw = os.getenv(env_var)
        if sa_raw:
            try:
                # Try raw JSON first
                try:
                    sa_info = json.loads(sa_raw)
                except Exception:
                    # Try base64 decoded JSON
                    decoded = base64.b64decode(sa_raw).decode("utf-8")
                    sa_info = json.loads(decoded)
                
                credentials = service_account.Credentials.from_service_account_info(sa_info)
                project = sa_info.get("project_id", os.getenv("GCP_PROJECT_ID", os.getenv("PROJECT_ID")))
                return bigquery.Client(credentials=credentials, project=project)
            except Exception as e:
                print(f"[BigQuery Notice] Failed to parse service account from {env_var}: {e}")

    # 2. Standard credentials / file path fallback
    try:
        return bigquery.Client()
    except (DefaultCredentialsError, Exception) as e:
        print(f"[BigQuery Notice] BigQuery client offline: {e}")
        return None