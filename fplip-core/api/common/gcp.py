"""GCP helper utilities.

Provides a single `resolve_project_id()` helper that follows the rules:
1. Check `GCP_PROJECT` env var
2. Check `PROJECT_ID` env var
3. Fall back to `google.auth.default()`
4. Raise RuntimeError if project cannot be resolved
"""
from __future__ import annotations

import os
from typing import Optional


def resolve_project_id() -> str:
    """Resolve the GCP project id from environment or Google auth.

    Returns:
        The resolved project id string.

    Raises:
        RuntimeError: if no project id can be determined.
    """
    # 1. Environment variables
    for var in ("GCP_PROJECT_ID", "GCP_PROJECT", "PROJECT_ID"):
        val = os.getenv(var)
        if val:
            return val

    # 2. google.auth.default() fallback
    try:
        import google.auth

        creds, project = google.auth.default()
        if project:
            return project
    except Exception:
        pass

    # 3. Default fallback for serverless / dev mode
    return os.getenv("GCP_PROJECT_ID", "fplip-demo")



__all__ = ["resolve_project_id"]
