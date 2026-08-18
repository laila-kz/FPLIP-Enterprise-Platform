"""
In-memory TTL cache for the FPLIP API.
"""

import time
from typing import Any, Optional


class TTLCache:
    """
    Simple in-memory cache with time-to-live (TTL) expiration.
    
    Usage:
        cache = TTLCache(ttl_seconds=3600)  # 1 hour
        cache.set("key", value)
        cached = cache.get("key")  # returns None if expired or not found
    """
    
    def __init__(self, ttl_seconds: int):
        """
        Initialize the cache with a TTL.
        
        Args:
            ttl_seconds: Time-to-live in seconds (e.g., 14400 = 4 hours)
        """
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key string
            
        Returns:
            The cached value if found and not expired, otherwise None
        """
        entry = self._store.get(key)
        if entry is None:
            return None
        
        expires_at, value = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key string
            value: Value to cache
        """
        self._store[key] = (time.monotonic() + self._ttl, value)
    
    def clear(self) -> None:
        """Clear the entire cache."""
        self._store.clear()
    
    def __len__(self) -> int:
        """Return the number of items in the cache."""
        return len(self._store)