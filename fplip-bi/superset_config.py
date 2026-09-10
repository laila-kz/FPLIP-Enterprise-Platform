import os
from flask_caching.backends.filesystemcache import FileSystemCache

# ---------------------------------------------------------
# Superset Security & Core Configuration
# ---------------------------------------------------------
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "fplip_secure_superset_secret_key_2026_dev_prod")
ENABLE_PROXY_FIX = True
ROW_LIMIT = 50000

# ---------------------------------------------------------
# Database Connection (Metadata DB)
# ---------------------------------------------------------
# Default to SQLite in superset_home, or use external DB if configured
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "SUPERSET_DATABASE_URI",
    f"sqlite:///{os.environ.get('SUPERSET_HOME', '/app/superset_home')}/superset.db"
)

# ---------------------------------------------------------
# 4-Hour In-Memory / File TTL Caching Strategy
# Protects GCP BigQuery query limits and enables low-latency caching (<20ms)
# ---------------------------------------------------------
CACHE_DEFAULT_TIMEOUT = int(os.environ.get("SUPERSET_CACHE_TTL", 14400)) # 4 hours

CACHE_CONFIG = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": CACHE_DEFAULT_TIMEOUT,
    "CACHE_THRESHOLD": 5000,
}

DATA_CACHE_CONFIG = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": CACHE_DEFAULT_TIMEOUT,
    "CACHE_THRESHOLD": 5000,
}

FILTER_STATE_CACHE_CONFIG = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": CACHE_DEFAULT_TIMEOUT,
}

EXPLORE_FORM_DATA_CACHE_CONFIG = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": CACHE_DEFAULT_TIMEOUT,
}

# ---------------------------------------------------------
# Feature Flags
# ---------------------------------------------------------
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "GENERIC_CHART_AXES": True,
}

# Enable CSV and Excel uploads
CSV_EXTENSIONS = {"csv", "tsv"}
EXCEL_EXTENSIONS = {"xls", "xlsx"}
ALLOWED_EXTENSIONS = CSV_EXTENSIONS | EXCEL_EXTENSIONS

# CORS / Talisman configuration
TALISMAN_ENABLED = False
ENABLE_CORS = True
CORS_OPTIONS = {
    "supports_credentials": True,
    "allow_headers": ["*"],
    "resources": ["*"],
    "origins": ["*"],
}
