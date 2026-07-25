"""
CloudBoard – Cache-Aside Service & Memory/Redis Store (Module 13).
Implements cache-aside strategy, TTL expiration, cache invalidation, and telemetry hit/miss counters.
"""

import time
import json
from typing import Any, Optional, Dict

class CacheService:
    """Cache-aside manager for database queries, search results, and API telemetry."""
    
    def __init__(self, default_ttl: int = 60):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached item if present and not expired."""
        if key in self._cache:
            entry = self._cache[key]
            if time.time() < entry["expires_at"]:
                self.hits += 1
                return entry["value"]
            else:
                # Expired
                del self._cache[key]
        self.misses += 1
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cache entry with TTL (seconds)."""
        expire_seconds = ttl if ttl is not None else self.default_ttl
        self._cache[key] = {
            "value": value,
            "expires_at": time.time() + expire_seconds,
            "created_at": time.time()
        }

    def delete(self, key: str) -> bool:
        """Invalidate a specific cache key."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Flush the cache."""
        self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Return cache hit/miss statistics and active entry count."""
        total = self.hits + self.misses
        hit_ratio = round((self.hits / total) * 100, 2) if total > 0 else 100.0
        
        # Clean expired entries
        now = time.time()
        active_keys = [k for k, v in self._cache.items() if v["expires_at"] > now]

        return {
            "total_keys": len(active_keys),
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio_percent": hit_ratio,
            "strategy": "Cache-Aside with TTL"
        }


# Global cache instance
cache_service = CacheService(default_ttl=60)
