#!/usr/bin/env python3
"""
Error Classification Cache with TTL Support
带TTL支持的错误分类缓存

Implements LRU cache with time-based expiration to prevent repeated
classification of the same errors.
实现带时间过期的LRU缓存，防止对相同错误的重复分类。
"""

import hashlib
import time
import threading
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Optional
import logging

from webfetcher.errors.types import ErrorClassification

@dataclass
class CacheEntry:
    """Cache entry with TTL / 带TTL的缓存条目"""
    classification: ErrorClassification
    timestamp: float
    ttl: int

    def is_expired(self) -> bool:
        """Check if entry has expired / 检查条目是否过期"""
        return time.time() > (self.timestamp + self.ttl)

@dataclass
class CacheMetrics:
    """Cache performance metrics / 缓存性能指标"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate / 计算缓存命中率"""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100

class ErrorCache:
    """
    Thread-safe LRU cache with TTL support for error classifications
    带TTL支持的线程安全LRU缓存，用于错误分类
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize cache

        Args:
            max_size: Maximum number of entries (default: 1000)
        """
        self.max_size = max_size
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.Lock()
        self.metrics = CacheMetrics()
        self.logger = logging.getLogger(__name__)

    def generate_cache_key(self, error: Exception, url: str) -> str:
        """
        Generate cache key from error and URL
        从错误和URL生成缓存键

        Args:
            error: The exception
            url: The URL that caused the error

        Returns:
            MD5 hash of error signature
        """
        error_type = type(error).__name__
        error_msg = str(error)[:200]  # Truncate long messages
        signature = f"{error_type}:{error_msg}:{url}"
        return hashlib.md5(signature.encode()).hexdigest()

    def get(self, cache_key: str) -> Optional[ErrorClassification]:
        """
        Get cached classification if available and not expired
        获取缓存的分类（如果可用且未过期）

        Args:
            cache_key: The cache key

        Returns:
            ErrorClassification if cached and valid, None otherwise
        """
        with self.lock:
            self.metrics.total_requests += 1

            if cache_key not in self.cache:
                self.metrics.cache_misses += 1
                self.logger.debug(f"Cache miss for key: {cache_key[:8]}...")
                return None

            entry = self.cache[cache_key]

            # Check if expired
            if entry.is_expired():
                self.logger.debug(f"Cache entry expired for key: {cache_key[:8]}...")
                del self.cache[cache_key]
                self.metrics.cache_misses += 1
                return None

            # Move to end (LRU)
            self.cache.move_to_end(cache_key)
            self.metrics.cache_hits += 1
            self.logger.debug(f"Cache hit for key: {cache_key[:8]}...")
            return entry.classification

    def put(self, cache_key: str, classification: ErrorClassification, ttl: Optional[int] = None):
        """
        Store classification in cache with TTL
        使用TTL将分类存储在缓存中

        Args:
            cache_key: The cache key
            classification: The error classification to cache
            ttl: Time to live in seconds (default: from classification.cache_duration)
        """
        with self.lock:
            # Use classification's cache_duration if TTL not specified
            if ttl is None:
                ttl = classification.cache_duration or 300  # Default 5 minutes

            # Create cache entry
            entry = CacheEntry(
                classification=classification,
                timestamp=time.time(),
                ttl=ttl
            )

            # Check if we need to evict
            if cache_key not in self.cache and len(self.cache) >= self.max_size:
                # Evict oldest entry (LRU)
                evicted_key, _ = self.cache.popitem(last=False)
                self.metrics.evictions += 1
                self.logger.debug(f"Evicted cache entry: {evicted_key[:8]}...")

            # Store entry
            self.cache[cache_key] = entry
            self.logger.debug(f"Cached classification for key: {cache_key[:8]}... (TTL: {ttl}s)")

    def clear(self):
        """Clear all cache entries / 清除所有缓存条目"""
        with self.lock:
            self.cache.clear()
            self.logger.info("Cache cleared")

    def get_metrics(self) -> CacheMetrics:
        """Get cache performance metrics / 获取缓存性能指标"""
        with self.lock:
            return CacheMetrics(
                total_requests=self.metrics.total_requests,
                cache_hits=self.metrics.cache_hits,
                cache_misses=self.metrics.cache_misses,
                evictions=self.metrics.evictions
            )

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries
        移除所有过期条目

        Returns:
            Number of entries removed
        """
        with self.lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.is_expired()
            ]

            for key in expired_keys:
                del self.cache[key]

            if expired_keys:
                self.logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

            return len(expired_keys)
