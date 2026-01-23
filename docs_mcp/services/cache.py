"""Caching layer with TTL and file change detection."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from docs_mcp.utils.logger import logger


class CacheEntry(BaseModel):
    """Cached parsed content for performance."""

    key: str
    value: Any
    cached_at: datetime
    ttl: int
    file_mtime: datetime | None = None
    size_bytes: int = 0

    @property
    def is_expired(self) -> bool:
        """Check if entry has exceeded TTL."""
        return (datetime.now(timezone.utc) - self.cached_at).total_seconds() > self.ttl

    def is_stale(self, current_mtime: datetime | None = None) -> bool:
        """Check if source file has been modified.

        Args:
            current_mtime: Current modification time of source file

        Returns:
            True if file has been modified since caching
        """
        if self.file_mtime is None or current_mtime is None:
            return False
        return current_mtime > self.file_mtime


class Cache:
    """Simple in-memory cache with TTL and size limits."""

    def __init__(self, default_ttl: int = 3600, max_size_mb: int = 500) -> None:
        """Initialize cache.

        Args:
            default_ttl: Default time-to-live in seconds
            max_size_mb: Maximum cache size in megabytes
        """
        self._cache: dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._max_size_bytes = max_size_mb * 1024 * 1024
        self._current_size_bytes = 0

    def get(self, key: str, file_path: Path | None = None) -> Any | None:
        """Get value from cache if valid.

        Args:
            key: Cache key
            file_path: Optional file path to check for modifications

        Returns:
            Cached value if valid, None otherwise
        """
        entry = self._cache.get(key)
        if entry is None:
            logger.debug(f"Cache miss: {key}")
            return None

        # Check if expired
        if entry.is_expired:
            logger.debug(f"Cache expired: {key}")
            self.invalidate(key)
            return None

        # Check if file has been modified
        if file_path and file_path.exists():
            current_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if entry.is_stale(current_mtime):
                logger.debug(f"Cache stale (file modified): {key}")
                self.invalidate(key)
                return None

        logger.debug(f"Cache hit: {key}")
        return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        file_path: Path | None = None,
    ) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
            file_path: Optional file path to track modifications
        """
        # Estimate size (rough approximation)
        size_bytes = self._estimate_size(value)

        # Check if we need to evict entries
        while self._current_size_bytes + size_bytes > self._max_size_bytes and self._cache:
            self._evict_oldest()

        # Get file modification time if path provided
        file_mtime = None
        if file_path and file_path.exists():
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

        # Create entry
        entry = CacheEntry(
            key=key,
            value=value,
            cached_at=datetime.now(timezone.utc),
            ttl=ttl or self._default_ttl,
            file_mtime=file_mtime,
            size_bytes=size_bytes,
        )

        # Update cache
        old_entry = self._cache.get(key)
        if old_entry:
            self._current_size_bytes -= old_entry.size_bytes

        self._cache[key] = entry
        self._current_size_bytes += size_bytes

        logger.debug(
            f"Cache set: {key} (size: {size_bytes} bytes, "
            f"total: {self._current_size_bytes} / {self._max_size_bytes})"
        )

    def invalidate(self, key: str) -> None:
        """Remove entry from cache.

        Args:
            key: Cache key to invalidate
        """
        entry = self._cache.pop(key, None)
        if entry:
            self._current_size_bytes -= entry.size_bytes
            logger.debug(f"Cache invalidated: {key}")

    def invalidate_prefix(self, prefix: str) -> int:
        """Invalidate all entries with keys starting with prefix.

        Args:
            prefix: Key prefix to match

        Returns:
            Number of entries invalidated
        """
        keys_to_remove = [k for k in self._cache.keys() if k.startswith(prefix)]
        for key in keys_to_remove:
            self.invalidate(key)
        logger.debug(f"Cache invalidated prefix: {prefix} ({len(keys_to_remove)} entries)")
        return len(keys_to_remove)

    def clear(self) -> None:
        """Clear all cache entries."""
        count = len(self._cache)
        self._cache.clear()
        self._current_size_bytes = 0
        logger.info(f"Cache cleared ({count} entries)")

    def _evict_oldest(self) -> None:
        """Evict the oldest cache entry (LRU)."""
        if not self._cache:
            return

        # Find oldest entry
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].cached_at)
        logger.debug(f"Evicting oldest cache entry: {oldest_key}")
        self.invalidate(oldest_key)

    def _estimate_size(self, value: Any) -> int:
        """Estimate size of value in bytes (rough approximation).

        Args:
            value: Value to estimate

        Returns:
            Estimated size in bytes
        """
        if isinstance(value, str):
            return len(value.encode("utf-8"))
        elif isinstance(value, (list, dict)):
            # Rough estimate for collections
            return len(str(value).encode("utf-8"))
        elif hasattr(value, "__dict__"):
            # For objects, estimate based on string representation
            return len(str(value.__dict__).encode("utf-8"))
        else:
            # Default fallback
            return 1024  # 1KB default

    @property
    def size(self) -> int:
        """Get number of entries in cache."""
        return len(self._cache)

    @property
    def size_bytes(self) -> int:
        """Get current cache size in bytes."""
        return self._current_size_bytes

    @property
    def size_mb(self) -> float:
        """Get current cache size in megabytes."""
        return self._current_size_bytes / (1024 * 1024)


# Global cache instance
_cache_instance: Cache | None = None


def get_cache(ttl: int = 3600, max_size_mb: int = 500) -> Cache:
    """Get or create global cache instance.

    Args:
        ttl: Default TTL in seconds
        max_size_mb: Maximum cache size in MB

    Returns:
        Cache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = Cache(default_ttl=ttl, max_size_mb=max_size_mb)
    return _cache_instance
