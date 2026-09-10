"""
Authentication dependencies for FastAPI service-to-service communication.
"""

import logging
from typing import Optional
from fastapi import Header, HTTPException, status, Depends
from api.core.config import get_settings, Settings

logger = logging.getLogger(__name__)


def verify_api_key(
    x_internal_key: Optional[str] = Header(default=None, alias="X-Internal-Key"),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
) -> Optional[str]:
    """
    Verify incoming requests from Laravel or internal callers.

    Checks X-Internal-Key (or fallback X-API-Key) against INTERNAL_API_KEY / API_KEY.
    Supports soft mode (ENFORCE_INTERNAL_KEY=false) for zero-downtime 2-phase rollout.
    """
    expected_key = settings.internal_api_key or settings.api_key
    provided_key = x_internal_key or x_api_key

    if not expected_key:
        logger.warning("No INTERNAL_API_KEY configured; skipping header verification.")
        return provided_key

    if not provided_key or provided_key != expected_key:
        warning_msg = (
            f"Unauthorized service-to-service call. "
            f"Provided header present: {bool(provided_key)}"
        )
        if settings.enforce_internal_key:
            logger.error(warning_msg)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing X-Internal-Key header",
            )
        else:
            logger.warning(f"[SOFT-MODE WARNING] {warning_msg}")

    return provided_key
