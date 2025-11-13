"""Unit tests for caching layer with TTL and file change detection."""

import time
from datetime import datetime, timedelta, timezone, UTC

from hierarchical_docs_mcp.services.cache import Cache, CacheEntry, get_cache


class TestCacheEntry:
    """Test CacheEntry model."""

    def test_cache_entry_creation(self):
        """Test basic cache entry creation."""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            cached_at=datetime.now(UTC),
            ttl=3600,
        )

        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.ttl == 3600

    def test_is_expired_fresh_entry(self):
        """Test that fresh entries are not expired."""
        entry = CacheEntry(
            key="test",
            value="value",
            cached_at=datetime.now(UTC),
            ttl=3600,
        )

        assert entry.is_expired is False

    def test_is_expired_old_entry(self):
        """Test that old entries are expired."""
        entry = CacheEntry(
            key="test",
            value="value",
            cached_at=datetime.now(UTC) - timedelta(seconds=7200),
            ttl=3600,
        )

        assert entry.is_expired is True

    def test_is_stale_no_mtime(self):
        """Test that entries without mtime are not stale."""
        entry = CacheEntry(
            key="test",
            value="value",
            cached_at=datetime.now(UTC),
            ttl=3600,
            file_mtime=None,
        )

        assert entry.is_stale(None) is False
        assert entry.is_stale(datetime.now(UTC)) is False

    def test_is_stale_file_modified(self):
        """Test that entries are stale when file is modified."""
        old_time = datetime.now(UTC) - timedelta(hours=1)
        new_time = datetime.now(UTC)

        entry = CacheEntry(
            key="test",
            value="value",
            cached_at=old_time,
            ttl=3600,
            file_mtime=old_time,
        )

        assert entry.is_stale(new_time) is True

    def test_is_stale_file_not_modified(self):
        """Test that entries are not stale when file hasn't changed."""
        cache_time = datetime.now(UTC)

        entry = CacheEntry(
            key="test",
            value="value",
            cached_at=cache_time,
            ttl=3600,
            file_mtime=cache_time,
        )

        assert entry.is_stale(cache_time) is False


class TestCache:
    """Test Cache class operations."""

    def test_cache_initialization(self):
        """Test cache initialization with default values."""
        cache = Cache()

        assert cache.size == 0
        assert cache.size_bytes == 0
        assert cache._default_ttl == 3600
        assert cache._max_size_bytes == 500 * 1024 * 1024

    def test_cache_custom_initialization(self):
        """Test cache initialization with custom values."""
        cache = Cache(default_ttl=7200, max_size_mb=100)

        assert cache._default_ttl == 7200
        assert cache._max_size_bytes == 100 * 1024 * 1024

    def test_set_and_get_simple_value(self):
        """Test basic set and get operations."""
        cache = Cache()
        cache.set("key1", "value1")

        result = cache.get("key1")
        assert result == "value1"

    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist."""
        cache = Cache()
        result = cache.get("nonexistent")

        assert result is None

    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = Cache()
        assert cache.get("missing") is None

    def test_cache_hit(self):
        """Test cache hit returns value."""
        cache = Cache()
        cache.set("hit", "data")

        assert cache.get("hit") == "data"

    def test_cache_ttl_expiration(self):
        """Test that entries expire after TTL."""
        cache = Cache(default_ttl=1)  # 1 second TTL
        cache.set("expiring", "value")

        # Should be available immediately
        assert cache.get("expiring") == "value"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired now
        assert cache.get("expiring") is None

    def test_custom_ttl_per_entry(self):
        """Test setting custom TTL per entry."""
        cache = Cache(default_ttl=3600)
        cache.set("short_lived", "value", ttl=1)

        # Should be available immediately
        assert cache.get("short_lived") == "value"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        assert cache.get("short_lived") is None

    def test_file_modification_detection(self, tmp_path):
        """Test that cache detects file modifications."""
        test_file = tmp_path / "test.md"
        test_file.write_text("original")

        cache = Cache()
        cache.set("file_key", "cached_value", file_path=test_file)

        # Should hit cache
        assert cache.get("file_key", test_file) == "cached_value"

        # Modify file
        time.sleep(0.1)  # Ensure timestamp changes
        test_file.write_text("modified")

        # Should miss cache due to file modification
        assert cache.get("file_key", test_file) is None

    def test_invalidate_entry(self):
        """Test manual cache invalidation."""
        cache = Cache()
        cache.set("key1", "value1")

        assert cache.get("key1") == "value1"

        cache.invalidate("key1")

        assert cache.get("key1") is None

    def test_invalidate_nonexistent_key(self):
        """Test invalidating a nonexistent key doesn't error."""
        cache = Cache()
        cache.invalidate("nonexistent")  # Should not raise error

    def test_invalidate_prefix(self):
        """Test prefix-based invalidation."""
        cache = Cache()
        cache.set("docs:file1", "value1")
        cache.set("docs:file2", "value2")
        cache.set("api:endpoint1", "value3")

        # Invalidate all 'docs:' entries
        count = cache.invalidate_prefix("docs:")

        assert count == 2
        assert cache.get("docs:file1") is None
        assert cache.get("docs:file2") is None
        assert cache.get("api:endpoint1") == "value3"

    def test_clear_cache(self):
        """Test clearing all cache entries."""
        cache = Cache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        assert cache.size == 3

        cache.clear()

        assert cache.size == 0
        assert cache.size_bytes == 0
        assert cache.get("key1") is None

    def test_cache_size_tracking(self):
        """Test that cache tracks entry count correctly."""
        cache = Cache()

        assert cache.size == 0

        cache.set("key1", "value1")
        assert cache.size == 1

        cache.set("key2", "value2")
        assert cache.size == 2

        cache.invalidate("key1")
        assert cache.size == 1

        cache.clear()
        assert cache.size == 0

    def test_cache_size_bytes_tracking(self):
        """Test that cache tracks size in bytes."""
        cache = Cache()

        assert cache.size_bytes == 0

        cache.set("key1", "a" * 1000)

        assert cache.size_bytes > 0
        assert cache.size_mb > 0

    def test_cache_eviction_when_full(self):
        """Test that cache evicts oldest entry when full."""
        cache = Cache(max_size_mb=1)  # 1MB limit

        # Fill cache with large entries
        large_value = "x" * (200 * 1024)  # 200KB each

        cache.set("key1", large_value)
        time.sleep(0.01)
        cache.set("key2", large_value)
        time.sleep(0.01)
        cache.set("key3", large_value)
        time.sleep(0.01)
        cache.set("key4", large_value)
        time.sleep(0.01)
        cache.set("key5", large_value)
        time.sleep(0.01)

        # Adding 6th large entry should evict oldest
        cache.set("key6", large_value)

        # First entry should be evicted
        assert cache.get("key1") is None
        # Newer entries should still be there
        assert cache.get("key6") is not None

    def test_cache_update_existing_key(self):
        """Test updating an existing cache key."""
        cache = Cache()
        cache.set("key1", "value1")

        assert cache.get("key1") == "value1"

        cache.set("key1", "value2")

        assert cache.get("key1") == "value2"

    def test_cache_size_after_update(self):
        """Test that cache size is updated correctly when updating keys."""
        cache = Cache()

        cache.set("key1", "small")
        size_after_first = cache.size_bytes

        cache.set("key1", "a" * 10000)  # Much larger value
        size_after_update = cache.size_bytes

        # Size should increase after update
        assert size_after_update > size_after_first

    def test_estimate_size_string(self):
        """Test size estimation for strings."""
        cache = Cache()

        test_string = "hello world"
        estimated = cache._estimate_size(test_string)

        # Should be roughly the byte length
        assert estimated >= len(test_string.encode("utf-8"))

    def test_estimate_size_list(self):
        """Test size estimation for lists."""
        cache = Cache()

        test_list = ["item1", "item2", "item3"]
        estimated = cache._estimate_size(test_list)

        assert estimated > 0

    def test_estimate_size_dict(self):
        """Test size estimation for dicts."""
        cache = Cache()

        test_dict = {"key1": "value1", "key2": "value2"}
        estimated = cache._estimate_size(test_dict)

        assert estimated > 0

    def test_estimate_size_object(self):
        """Test size estimation for objects."""
        cache = Cache()

        class TestObject:
            def __init__(self):
                self.data = "test data"

        obj = TestObject()
        estimated = cache._estimate_size(obj)

        assert estimated > 0

    def test_concurrent_operations(self):
        """Test that cache handles concurrent-like operations."""
        cache = Cache()

        # Simulate multiple operations
        for i in range(100):
            cache.set(f"key{i}", f"value{i}")

        assert cache.size == 100

        # Get all values
        for i in range(100):
            assert cache.get(f"key{i}") == f"value{i}"

    def test_cache_with_none_value(self):
        """Test caching None values."""
        cache = Cache()
        cache.set("null_key", None)

        # Should return None (cached value, not cache miss)
        result = cache.get("null_key")
        assert result is None

    def test_cache_with_complex_objects(self):
        """Test caching complex objects."""
        cache = Cache()

        complex_obj = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "tuple": (1, 2, 3),
        }

        cache.set("complex", complex_obj)

        result = cache.get("complex")
        assert result == complex_obj

    def test_file_path_tracking(self, tmp_path):
        """Test that file paths are tracked correctly."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        cache = Cache()
        cache.set("with_file", "value", file_path=test_file)

        # Get should check file modification time
        result = cache.get("with_file", test_file)
        assert result == "value"

    def test_nonexistent_file_path(self, tmp_path):
        """Test caching with nonexistent file path."""
        nonexistent = tmp_path / "nonexistent.txt"

        cache = Cache()
        cache.set("key", "value", file_path=nonexistent)

        # Should still cache (file_mtime will be None)
        result = cache.get("key", nonexistent)
        assert result == "value"


class TestGetCache:
    """Test global cache instance management."""

    def test_get_cache_singleton(self):
        """Test that get_cache returns singleton instance."""
        cache1 = get_cache()
        cache2 = get_cache()

        assert cache1 is cache2

    def test_get_cache_persistence(self):
        """Test that cache persists across get_cache calls."""
        cache = get_cache()
        cache.set("persistent", "value")

        cache2 = get_cache()
        assert cache2.get("persistent") == "value"

    def test_get_cache_with_params(self):
        """Test get_cache with custom parameters."""
        # Note: In the actual implementation, parameters only apply on first call
        cache = get_cache(ttl=7200, max_size_mb=100)

        assert cache is not None


class TestCacheEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string_key(self):
        """Test caching with empty string key."""
        cache = Cache()
        cache.set("", "value")

        assert cache.get("") == "value"

    def test_very_long_key(self):
        """Test caching with very long key."""
        cache = Cache()
        long_key = "k" * 10000

        cache.set(long_key, "value")
        assert cache.get(long_key) == "value"

    def test_unicode_key(self):
        """Test caching with Unicode keys."""
        cache = Cache()
        cache.set("键值", "中文")

        assert cache.get("键值") == "中文"

    def test_special_char_key(self):
        """Test caching with special character keys."""
        cache = Cache()
        special_key = "key:with:colons/and/slashes"

        cache.set(special_key, "value")
        assert cache.get(special_key) == "value"

    def test_zero_ttl(self):
        """Test cache with zero TTL (immediately expired)."""
        cache = Cache(default_ttl=0)
        cache.set("zero_ttl", "value")

        # Should be immediately expired
        time.sleep(0.01)
        assert cache.get("zero_ttl") is None

    def test_negative_ttl(self):
        """Test cache with negative TTL."""
        cache = Cache(default_ttl=-1)
        cache.set("negative_ttl", "value")

        # Should be expired
        assert cache.get("negative_ttl") is None

    def test_very_large_ttl(self):
        """Test cache with very large TTL."""
        cache = Cache(default_ttl=365 * 24 * 3600)  # 1 year
        cache.set("long_lived", "value")

        # Should be available
        assert cache.get("long_lived") == "value"

    def test_cache_size_mb_property(self):
        """Test cache size in megabytes property."""
        cache = Cache()
        cache.set("key", "a" * 1024 * 1024)  # 1MB

        assert cache.size_mb >= 0.9  # Should be close to 1MB
