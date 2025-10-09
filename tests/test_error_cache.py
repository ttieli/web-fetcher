#!/usr/bin/env python3
"""
Unit Tests for Error Cache
错误缓存单元测试

Tests LRU cache with TTL support for error classifications.
测试带TTL支持的LRU缓存用于错误分类。
"""

import sys
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from error_cache import ErrorCache, CacheEntry, CacheMetrics
from error_types import ErrorType, ErrorClassification


class TestCacheEntry:
    """Test CacheEntry dataclass / 测试CacheEntry数据类"""

    def test_cache_entry_creation(self):
        """Test cache entry creation / 测试缓存条目创建"""
        classification = ErrorClassification(
            error_type=ErrorType.PERMANENT,
            should_retry=False,
            recommended_wait=0,
            max_retries=0,
            fallback_method=None,
            reason="Test error",
            confidence=1.0
        )

        entry = CacheEntry(
            classification=classification,
            timestamp=time.time(),
            ttl=300
        )

        assert entry.classification == classification
        assert entry.ttl == 300
        assert not entry.is_expired()

    def test_cache_entry_expiration(self):
        """Test cache entry expiration / 测试缓存条目过期"""
        classification = ErrorClassification(
            error_type=ErrorType.TEMPORARY,
            should_retry=True,
            recommended_wait=5.0,
            max_retries=3,
            fallback_method=None,
            reason="Test",
            confidence=0.9
        )

        # Create entry that expires immediately
        entry = CacheEntry(
            classification=classification,
            timestamp=time.time() - 10,  # 10 seconds ago
            ttl=1  # 1 second TTL
        )

        assert entry.is_expired()

    def test_cache_entry_not_expired(self):
        """Test cache entry not expired / 测试缓存条目未过期"""
        classification = ErrorClassification(
            error_type=ErrorType.TEMPORARY,
            should_retry=True,
            recommended_wait=5.0,
            max_retries=3,
            fallback_method=None,
            reason="Test",
            confidence=0.9
        )

        entry = CacheEntry(
            classification=classification,
            timestamp=time.time(),
            ttl=300
        )

        assert not entry.is_expired()


class TestCacheMetrics:
    """Test CacheMetrics dataclass / 测试CacheMetrics数据类"""

    def test_metrics_initialization(self):
        """Test metrics initialization / 测试指标初始化"""
        metrics = CacheMetrics()
        assert metrics.total_requests == 0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert metrics.evictions == 0
        assert metrics.hit_rate == 0.0

    def test_hit_rate_calculation(self):
        """Test hit rate calculation / 测试命中率计算"""
        metrics = CacheMetrics(
            total_requests=100,
            cache_hits=80,
            cache_misses=20,
            evictions=5
        )

        assert metrics.hit_rate == 80.0

    def test_hit_rate_zero_requests(self):
        """Test hit rate with zero requests / 测试零请求的命中率"""
        metrics = CacheMetrics()
        assert metrics.hit_rate == 0.0


class TestErrorCache:
    """Test ErrorCache class / 测试ErrorCache类"""

    def setup_method(self):
        """Setup test fixtures / 设置测试装置"""
        self.cache = ErrorCache(max_size=10)
        self.test_error = Exception("Test error")
        self.test_url = "http://example.com/test"

    def test_cache_initialization(self):
        """Test cache initialization / 测试缓存初始化"""
        cache = ErrorCache(max_size=100)
        assert cache.max_size == 100
        assert len(cache.cache) == 0
        assert cache.metrics.total_requests == 0

    def test_generate_cache_key(self):
        """Test cache key generation / 测试缓存键生成"""
        key1 = self.cache.generate_cache_key(self.test_error, self.test_url)
        key2 = self.cache.generate_cache_key(self.test_error, self.test_url)

        # Same error and URL should generate same key
        assert key1 == key2
        assert len(key1) == 32  # MD5 hash length

    def test_generate_cache_key_different_errors(self):
        """Test cache key generation for different errors / 测试不同错误的缓存键生成"""
        error1 = Exception("Error 1")
        error2 = Exception("Error 2")

        key1 = self.cache.generate_cache_key(error1, self.test_url)
        key2 = self.cache.generate_cache_key(error2, self.test_url)

        assert key1 != key2

    def test_generate_cache_key_different_urls(self):
        """Test cache key generation for different URLs / 测试不同URL的缓存键生成"""
        url1 = "http://example.com/page1"
        url2 = "http://example.com/page2"

        key1 = self.cache.generate_cache_key(self.test_error, url1)
        key2 = self.cache.generate_cache_key(self.test_error, url2)

        assert key1 != key2

    def test_cache_miss(self):
        """Test cache miss behavior / 测试缓存未命中行为"""
        key = "nonexistent_key"
        result = self.cache.get(key)

        assert result is None
        assert self.cache.metrics.total_requests == 1
        assert self.cache.metrics.cache_misses == 1
        assert self.cache.metrics.cache_hits == 0

    def test_cache_hit(self):
        """Test cache hit behavior / 测试缓存命中行为"""
        classification = ErrorClassification(
            error_type=ErrorType.PERMANENT,
            should_retry=False,
            recommended_wait=0,
            max_retries=0,
            fallback_method=None,
            reason="Test",
            confidence=1.0
        )

        cache_key = self.cache.generate_cache_key(self.test_error, self.test_url)

        # Store in cache
        self.cache.put(cache_key, classification, ttl=300)

        # Retrieve from cache
        result = self.cache.get(cache_key)

        assert result is not None
        assert result.error_type == ErrorType.PERMANENT
        assert self.cache.metrics.total_requests == 1
        assert self.cache.metrics.cache_hits == 1
        assert self.cache.metrics.cache_misses == 0

    def test_cache_expiration(self):
        """Test cache expiration / 测试缓存过期"""
        classification = ErrorClassification(
            error_type=ErrorType.TEMPORARY,
            should_retry=True,
            recommended_wait=5.0,
            max_retries=3,
            fallback_method=None,
            reason="Test",
            confidence=0.9
        )

        cache_key = self.cache.generate_cache_key(self.test_error, self.test_url)

        # Store with very short TTL
        self.cache.put(cache_key, classification, ttl=1)

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        result = self.cache.get(cache_key)
        assert result is None
        assert self.cache.metrics.cache_misses == 1

    def test_lru_eviction(self):
        """Test LRU eviction when cache is full / 测试缓存满时的LRU驱逐"""
        cache = ErrorCache(max_size=3)

        classification = ErrorClassification(
            error_type=ErrorType.TEMPORARY,
            should_retry=True,
            recommended_wait=5.0,
            max_retries=3,
            fallback_method=None,
            reason="Test",
            confidence=0.9
        )

        # Fill cache to capacity
        for i in range(3):
            error = Exception(f"Error {i}")
            key = cache.generate_cache_key(error, f"http://example.com/{i}")
            cache.put(key, classification)

        assert len(cache.cache) == 3
        assert cache.metrics.evictions == 0

        # Add one more - should evict oldest
        error = Exception("Error 3")
        key = cache.generate_cache_key(error, "http://example.com/3")
        cache.put(key, classification)

        assert len(cache.cache) == 3
        assert cache.metrics.evictions == 1

    def test_lru_order(self):
        """Test LRU ordering / 测试LRU顺序"""
        cache = ErrorCache(max_size=3)

        classification = ErrorClassification(
            error_type=ErrorType.TEMPORARY,
            should_retry=True,
            recommended_wait=5.0,
            max_retries=3,
            fallback_method=None,
            reason="Test",
            confidence=0.9
        )

        # Add three items
        keys = []
        for i in range(3):
            error = Exception(f"Error {i}")
            key = cache.generate_cache_key(error, f"http://example.com/{i}")
            keys.append(key)
            cache.put(key, classification)

        # Access first item (moves it to end)
        cache.get(keys[0])

        # Add fourth item - should evict second item (now oldest)
        error = Exception("Error 3")
        key3 = cache.generate_cache_key(error, "http://example.com/3")
        cache.put(key3, classification)

        # First item should still be there
        assert cache.get(keys[0]) is not None
        # Second item should be evicted
        assert cache.get(keys[1]) is None
        # Third item should be there
        assert cache.get(keys[2]) is not None

    def test_default_ttl_from_classification(self):
        """Test default TTL from classification / 测试从分类获取默认TTL"""
        classification = ErrorClassification(
            error_type=ErrorType.PERMANENT,
            should_retry=False,
            recommended_wait=0,
            max_retries=0,
            fallback_method=None,
            reason="Test",
            confidence=1.0,
            cache_duration=600  # 10 minutes
        )

        cache_key = self.cache.generate_cache_key(self.test_error, self.test_url)
        self.cache.put(cache_key, classification)  # No TTL specified

        # Check that entry uses classification's cache_duration
        entry = self.cache.cache[cache_key]
        assert entry.ttl == 600

    def test_explicit_ttl_override(self):
        """Test explicit TTL overrides classification / 测试显式TTL覆盖分类"""
        classification = ErrorClassification(
            error_type=ErrorType.PERMANENT,
            should_retry=False,
            recommended_wait=0,
            max_retries=0,
            fallback_method=None,
            reason="Test",
            confidence=1.0,
            cache_duration=600
        )

        cache_key = self.cache.generate_cache_key(self.test_error, self.test_url)
        self.cache.put(cache_key, classification, ttl=100)  # Override TTL

        entry = self.cache.cache[cache_key]
        assert entry.ttl == 100

    def test_clear_cache(self):
        """Test cache clearing / 测试缓存清除"""
        classification = ErrorClassification(
            error_type=ErrorType.TEMPORARY,
            should_retry=True,
            recommended_wait=5.0,
            max_retries=3,
            fallback_method=None,
            reason="Test",
            confidence=0.9
        )

        # Add multiple entries
        for i in range(5):
            error = Exception(f"Error {i}")
            key = self.cache.generate_cache_key(error, f"http://example.com/{i}")
            self.cache.put(key, classification)

        assert len(self.cache.cache) == 5

        # Clear cache
        self.cache.clear()

        assert len(self.cache.cache) == 0

    def test_get_metrics(self):
        """Test metrics retrieval / 测试指标检索"""
        classification = ErrorClassification(
            error_type=ErrorType.TEMPORARY,
            should_retry=True,
            recommended_wait=5.0,
            max_retries=3,
            fallback_method=None,
            reason="Test",
            confidence=0.9
        )

        cache_key = self.cache.generate_cache_key(self.test_error, self.test_url)

        # Generate some metrics
        self.cache.put(cache_key, classification)
        self.cache.get(cache_key)  # Hit
        self.cache.get("nonexistent")  # Miss

        metrics = self.cache.get_metrics()

        assert metrics.total_requests == 2
        assert metrics.cache_hits == 1
        assert metrics.cache_misses == 1
        assert metrics.hit_rate == 50.0

    def test_cleanup_expired_entries(self):
        """Test cleanup of expired entries / 测试过期条目清理"""
        classification = ErrorClassification(
            error_type=ErrorType.TEMPORARY,
            should_retry=True,
            recommended_wait=5.0,
            max_retries=3,
            fallback_method=None,
            reason="Test",
            confidence=0.9
        )

        # Add entries with short TTL
        for i in range(3):
            error = Exception(f"Error {i}")
            key = self.cache.generate_cache_key(error, f"http://example.com/{i}")
            self.cache.put(key, classification, ttl=1)

        # Add one with long TTL
        error = Exception("Error 3")
        key = self.cache.generate_cache_key(error, "http://example.com/3")
        self.cache.put(key, classification, ttl=300)

        assert len(self.cache.cache) == 4

        # Wait for expiration
        time.sleep(1.1)

        # Cleanup expired entries
        removed = self.cache.cleanup_expired()

        assert removed == 3
        assert len(self.cache.cache) == 1

    def test_cleanup_no_expired(self):
        """Test cleanup with no expired entries / 测试无过期条目的清理"""
        classification = ErrorClassification(
            error_type=ErrorType.TEMPORARY,
            should_retry=True,
            recommended_wait=5.0,
            max_retries=3,
            fallback_method=None,
            reason="Test",
            confidence=0.9
        )

        # Add entries with long TTL
        for i in range(3):
            error = Exception(f"Error {i}")
            key = self.cache.generate_cache_key(error, f"http://example.com/{i}")
            self.cache.put(key, classification, ttl=300)

        removed = self.cache.cleanup_expired()

        assert removed == 0
        assert len(self.cache.cache) == 3


class TestThreadSafety:
    """Test thread safety / 测试线程安全"""

    def test_concurrent_put_and_get(self):
        """Test concurrent put and get operations / 测试并发存取操作"""
        cache = ErrorCache(max_size=100)

        classification = ErrorClassification(
            error_type=ErrorType.TEMPORARY,
            should_retry=True,
            recommended_wait=5.0,
            max_retries=3,
            fallback_method=None,
            reason="Test",
            confidence=0.9
        )

        def worker(thread_id):
            for i in range(10):
                error = Exception(f"Thread {thread_id} Error {i}")
                url = f"http://example.com/thread{thread_id}/item{i}"
                key = cache.generate_cache_key(error, url)

                # Put
                cache.put(key, classification)

                # Get
                result = cache.get(key)
                assert result is not None

        # Run concurrent operations
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, i) for i in range(10)]
            for future in futures:
                future.result()

        # Verify no corruption
        metrics = cache.get_metrics()
        assert metrics.cache_hits > 0
        assert metrics.cache_misses == 0  # All gets should hit

    def test_concurrent_eviction(self):
        """Test concurrent operations with eviction / 测试带驱逐的并发操作"""
        cache = ErrorCache(max_size=10)

        classification = ErrorClassification(
            error_type=ErrorType.TEMPORARY,
            should_retry=True,
            recommended_wait=5.0,
            max_retries=3,
            fallback_method=None,
            reason="Test",
            confidence=0.9
        )

        def worker(thread_id):
            for i in range(5):
                error = Exception(f"Thread {thread_id} Error {i}")
                url = f"http://example.com/thread{thread_id}/item{i}"
                key = cache.generate_cache_key(error, url)
                cache.put(key, classification)

        # Run concurrent operations that will cause evictions
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker, i) for i in range(5)]
            for future in futures:
                future.result()

        # Cache should be at max size
        assert len(cache.cache) <= 10
        assert cache.metrics.evictions > 0


class TestIntegrationWithClassifier:
    """Test integration with error classifier / 测试与错误分类器的集成"""

    def test_classifier_uses_cache(self):
        """Test that classifier uses cache / 测试分类器使用缓存"""
        from error_classifier import UnifiedErrorClassifier
        from urllib.error import HTTPError

        classifier = UnifiedErrorClassifier()

        # Create error
        error = HTTPError("http://example.com", 404, "Not Found", {}, None)

        # First classification - cache miss
        result1 = classifier.classify_error(error, "http://example.com")
        assert result1.error_type == ErrorType.PERMANENT

        # Second classification - cache hit
        result2 = classifier.classify_error(error, "http://example.com")
        assert result2.error_type == ErrorType.PERMANENT

        # Check metrics
        if classifier.cache:
            metrics = classifier.get_cache_metrics()
            assert metrics is not None
            assert metrics['total_requests'] >= 1
            assert metrics['cache_hits'] >= 1

    def test_classifier_cache_disabled(self):
        """Test classifier with cache disabled / 测试禁用缓存的分类器"""
        from error_classifier import UnifiedErrorClassifier
        from urllib.error import HTTPError

        classifier = UnifiedErrorClassifier()

        error = HTTPError("http://example.com", 404, "Not Found", {}, None)

        # Classify with cache disabled
        result = classifier.classify_error(error, "http://example.com", use_cache=False)
        assert result.error_type == ErrorType.PERMANENT

        # Metrics should not increase for cache operations
        if classifier.cache:
            metrics = classifier.get_cache_metrics()
            # Cache was not used, so requests might be 0
            assert metrics is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
