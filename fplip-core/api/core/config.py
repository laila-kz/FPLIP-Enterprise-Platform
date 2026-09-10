"""
Configuration for the FPLIP API.
"""

import os
from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv()

try:
    from common.gcp import resolve_project_id
except ImportError:
    from api.common.gcp import resolve_project_id


class Settings:
    """Application settings loaded from environment variables."""
    
    # GCP Configuration
    # Resolve project id via env or application default credentials.
    project_id: str = resolve_project_id()
    gold_dataset: str = os.getenv("GOLD_DATASET", "fplip_gold")
    
    # Cache TTL in seconds (default: 4 hours = well under daily refresh)
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "14400"))
    
    # API Key (app-level authentication)
    api_key: str = os.getenv("API_KEY", "")
    internal_api_key: str = os.getenv("INTERNAL_API_KEY", os.getenv("API_KEY", ""))
    enforce_internal_key: bool = os.getenv("ENFORCE_INTERNAL_KEY", "true").lower() in ("true", "1", "yes")


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()