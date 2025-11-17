#!/usr/bin/env python3
"""
Unified Error Classification Engine
统一错误分类引擎

Provides intelligent error classification with pattern matching for web fetching operations.
为网络抓取操作提供基于模式匹配的智能错误分类。
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from urllib.error import HTTPError, URLError
import ssl

from webfetcher.errors.types import ErrorType, ErrorClassification

# Phase 2: Import error cache
try:
    from webfetcher.errors.cache import ErrorCache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    class ErrorCache:  # type: ignore
        pass


class UnifiedErrorClassifier:
    """
    Unified error classification engine with pattern-based detection
    基于模式检测的统一错误分类引擎
    """

    def __init__(self):
        """Initialize classifier with error patterns / 使用错误模式初始化分类器"""
        self.patterns: Dict[ErrorType, List[str]] = {}
        self.compiled_patterns: Dict[ErrorType, List[re.Pattern]] = {}
        self._init_patterns()
        self._compile_patterns()

        # Phase 2: Initialize cache
        self.cache: Optional[ErrorCache] = ErrorCache(max_size=1000) if CACHE_AVAILABLE else None

        logging.debug("UnifiedErrorClassifier initialized with compiled patterns")
        if self.cache:
            logging.debug("Error cache enabled (max_size=1000)")

    def _init_patterns(self):
        """Initialize error detection patterns / 初始化错误检测模式"""

        # Permanent errors - never retry / 永久性错误 - 永不重试
        self.patterns[ErrorType.PERMANENT] = [
            # SSL/TLS errors / SSL/TLS 错误
            r'UNSAFE_LEGACY_RENEGOTIATION_DISABLED',
            r'CERTIFICATE_VERIFY_FAILED',
            r'SSLV3_ALERT_HANDSHAKE_FAILURE',
            r'SSL23_GET_SERVER_HELLO',
            r'WRONG_VERSION_NUMBER',
            r'TLSV1_ALERT_PROTOCOL_VERSION',
            r'DH_KEY_TOO_SMALL',
            r'CERTIFICATE_EXPIRED',

            # Client errors / 客户端错误
            r'HTTP Error 401',
            r'HTTP Error 403',
            r'HTTP Error 404',
            r'HTTP Error 405',
            r'HTTP Error 410',

            # DNS/URL errors / DNS/URL 错误
            r'Name or service not known',
            r'nodename nor servname provided',
            r'No address associated with hostname',

            # Invalid URL / 无效的 URL
            r'Invalid URL',
            r'unknown url type',
        ]

        # Temporary errors - retry immediately / 临时性错误 - 立即重试
        self.patterns[ErrorType.TEMPORARY] = [
            # Network connectivity / 网络连接
            r'Connection reset by peer',
            r'Connection refused',
            r'Connection timed out',
            r'Network is unreachable',
            r'No route to host',
            r'Temporary failure in name resolution',

            # Server errors / 服务器错误
            r'HTTP Error 500',
            r'HTTP Error 502',
            r'HTTP Error 503',
            r'HTTP Error 504',

            # Timeout errors / 超时错误
            r'timed out',
            r'timeout',
            r'Read timed out',
        ]

        # Rate limit errors - long backoff / 速率限制错误 - 长时间退避
        self.patterns[ErrorType.RATE_LIMIT] = [
            r'HTTP Error 429',
            r'Too Many Requests',
            r'Rate limit exceeded',
            r'Retry after',
        ]

        # SSL configuration issues - use Selenium / SSL配置问题 - 使用Selenium
        self.patterns[ErrorType.SSL_CONFIG] = [
            r'UNSAFE_LEGACY_RENEGOTIATION_DISABLED',
            r'SSLV3_ALERT_HANDSHAKE_FAILURE',
            r'SSL23_GET_SERVER_HELLO',
            r'WRONG_VERSION_NUMBER',
            r'TLSV1_ALERT_PROTOCOL_VERSION',
            r'DH_KEY_TOO_SMALL',
        ]

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance / 预编译正则表达式以提高性能"""
        for error_type, pattern_list in self.patterns.items():
            self.compiled_patterns[error_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in pattern_list
            ]
        logging.debug(f"Compiled {sum(len(p) for p in self.compiled_patterns.values())} patterns")

    def classify_error(self, error: Exception, url: str = "", use_cache: bool = True) -> ErrorClassification:
        """
        Classify an error and provide retry recommendations (with caching support)
        分类错误并提供重试建议（支持缓存）

        Args:
            error: The exception to classify
            url: The URL being accessed (for context)
            use_cache: Whether to use cache (default: True)

        Returns:
            ErrorClassification with retry strategy
        """
        # Phase 2: Check cache first
        cache_key = None
        if use_cache and self.cache:
            cache_key = self.cache.generate_cache_key(error, url)
            cached_result = self.cache.get(cache_key)

            if cached_result:
                logging.debug(f"Using cached classification for {url}")
                return cached_result

        error_str = str(error)
        error_type_name = type(error).__name__

        logging.debug(f"Classifying error: {error_type_name}: {error_str[:100]}")

        # HTTP error classification / HTTP 错误分类
        if isinstance(error, HTTPError):
            classification = self.classify_http_error(error)
        # SSL error classification / SSL 错误分类
        elif isinstance(error, ssl.SSLError):
            classification = self.classify_ssl_error(error)
        # URL error classification / URL 错误分类
        elif isinstance(error, URLError):
            classification = self.classify_url_error(error)
        # Pattern-based classification / 基于模式的分类
        else:
            classification = self._classify_by_pattern(error_str, error_type_name)

        # Phase 2: Store in cache
        if use_cache and self.cache and cache_key:
            self.cache.put(cache_key, classification)

        return classification

    def classify_http_error(self, error: HTTPError) -> ErrorClassification:
        """
        Classify HTTP status code errors / 分类 HTTP 状态码错误

        Args:
            error: HTTPError instance

        Returns:
            ErrorClassification with appropriate strategy
        """
        status_code = error.code

        # 4xx Client errors (permanent) / 4xx 客户端错误（永久性）
        if status_code in [401, 403, 404, 405, 410]:
            return ErrorClassification(
                error_type=ErrorType.PERMANENT,
                should_retry=False,
                recommended_wait=0,
                max_retries=0,
                fallback_method=None,
                reason=f"HTTP {status_code}: Client error (permanent)",
                confidence=1.0,
                cache_duration=3600
            )

        # 429 Rate limiting / 429 速率限制
        if status_code == 429:
            return ErrorClassification(
                error_type=ErrorType.RATE_LIMIT,
                should_retry=True,
                recommended_wait=60.0,  # Start with 60s backoff
                max_retries=3,
                fallback_method=None,
                reason="HTTP 429: Rate limit exceeded",
                confidence=1.0
            )

        # 5xx Server errors (temporary) / 5xx 服务器错误（临时性）
        if 500 <= status_code < 600:
            return ErrorClassification(
                error_type=ErrorType.TEMPORARY,
                should_retry=True,
                recommended_wait=5.0,
                max_retries=3,
                fallback_method="selenium" if status_code in [503, 504] else None,
                reason=f"HTTP {status_code}: Server error (temporary)",
                confidence=0.9
            )

        # Other HTTP errors / 其他 HTTP 错误
        return ErrorClassification(
            error_type=ErrorType.UNKNOWN,
            should_retry=True,
            recommended_wait=3.0,
            max_retries=2,
            fallback_method=None,
            reason=f"HTTP {status_code}: Unknown status code",
            confidence=0.5
        )

    def classify_ssl_error(self, error: ssl.SSLError) -> ErrorClassification:
        """
        Classify SSL/TLS errors / 分类 SSL/TLS 错误

        Args:
            error: SSLError instance

        Returns:
            ErrorClassification with Selenium fallback
        """
        error_str = str(error)

        # Check for specific SSL configuration issues / 检查特定的 SSL 配置问题
        ssl_config_patterns = [
            'UNSAFE_LEGACY_RENEGOTIATION_DISABLED',
            'SSLV3_ALERT_HANDSHAKE_FAILURE',
            'WRONG_VERSION_NUMBER',
            'TLSV1_ALERT_PROTOCOL_VERSION',
            'DH_KEY_TOO_SMALL'
        ]

        for pattern in ssl_config_patterns:
            if pattern in error_str:
                return ErrorClassification(
                    error_type=ErrorType.SSL_CONFIG,
                    should_retry=False,
                    recommended_wait=0,
                    max_retries=0,
                    fallback_method="selenium",
                    reason=f"SSL configuration issue: {pattern}",
                    confidence=1.0
                )

        # Certificate verification errors (permanent) / 证书验证错误（永久性）
        if 'CERTIFICATE_VERIFY_FAILED' in error_str or 'CERTIFICATE_EXPIRED' in error_str:
            return ErrorClassification(
                error_type=ErrorType.PERMANENT,
                should_retry=False,
                recommended_wait=0,
                max_retries=0,
                fallback_method="selenium",
                reason="SSL certificate verification failed",
                confidence=1.0,
                cache_duration=3600
            )

        # Generic SSL error / 通用 SSL 错误
        return ErrorClassification(
            error_type=ErrorType.SSL_CONFIG,
            should_retry=False,
            recommended_wait=0,
            max_retries=0,
            fallback_method="selenium",
            reason=f"SSL error: {error_str[:100]}",
            confidence=0.8
        )

    def classify_url_error(self, error: URLError) -> ErrorClassification:
        """
        Classify URL/network errors / 分类 URL/网络错误

        Args:
            error: URLError instance

        Returns:
            ErrorClassification with appropriate strategy
        """
        error_str = str(error.reason) if hasattr(error, 'reason') else str(error)

        # Network connectivity issues (temporary) / 网络连接问题（临时性）
        temporary_patterns = [
            'Connection reset by peer',
            'Connection refused',
            'Connection timed out',
            'Network is unreachable',
            'No route to host',
            'timed out',
            'timeout'
        ]

        for pattern in temporary_patterns:
            if pattern.lower() in error_str.lower():
                return ErrorClassification(
                    error_type=ErrorType.TEMPORARY,
                    should_retry=True,
                    recommended_wait=3.0,
                    max_retries=3,
                    fallback_method=None,
                    reason=f"Network error: {pattern}",
                    confidence=0.9
                )

        # DNS resolution errors (permanent) / DNS 解析错误（永久性）
        dns_patterns = [
            'Name or service not known',
            'nodename nor servname provided',
            'No address associated with hostname'
        ]

        for pattern in dns_patterns:
            if pattern.lower() in error_str.lower():
                return ErrorClassification(
                    error_type=ErrorType.PERMANENT,
                    should_retry=False,
                    recommended_wait=0,
                    max_retries=0,
                    fallback_method=None,
                    reason=f"DNS resolution failed: {pattern}",
                    confidence=1.0,
                    cache_duration=1800
                )

        # Unknown URL error / 未知的 URL 错误
        return ErrorClassification(
            error_type=ErrorType.UNKNOWN,
            should_retry=True,
            recommended_wait=5.0,
            max_retries=2,
            fallback_method=None,
            reason=f"URL error: {error_str[:100]}",
            confidence=0.6
        )

    def _classify_by_pattern(self, error_str: str, error_type_name: str) -> ErrorClassification:
        """
        Classify error using pattern matching / 使用模式匹配分类错误

        Args:
            error_str: String representation of error
            error_type_name: Type name of the error

        Returns:
            ErrorClassification based on pattern match
        """
        # Check SSL_CONFIG patterns first (highest priority) / 首先检查 SSL_CONFIG 模式（最高优先级）
        for pattern in self.compiled_patterns.get(ErrorType.SSL_CONFIG, []):
            if pattern.search(error_str):
                return ErrorClassification(
                    error_type=ErrorType.SSL_CONFIG,
                    should_retry=False,
                    recommended_wait=0,
                    max_retries=0,
                    fallback_method="selenium",
                    reason=f"SSL configuration issue detected: {pattern.pattern}",
                    confidence=0.9
                )

        # Check PERMANENT patterns / 检查 PERMANENT 模式
        for pattern in self.compiled_patterns.get(ErrorType.PERMANENT, []):
            if pattern.search(error_str):
                return ErrorClassification(
                    error_type=ErrorType.PERMANENT,
                    should_retry=False,
                    recommended_wait=0,
                    max_retries=0,
                    fallback_method=None,
                    reason=f"Permanent error detected: {pattern.pattern}",
                    confidence=0.9,
                    cache_duration=3600
                )

        # Check RATE_LIMIT patterns / 检查 RATE_LIMIT 模式
        for pattern in self.compiled_patterns.get(ErrorType.RATE_LIMIT, []):
            if pattern.search(error_str):
                return ErrorClassification(
                    error_type=ErrorType.RATE_LIMIT,
                    should_retry=True,
                    recommended_wait=60.0,
                    max_retries=3,
                    fallback_method=None,
                    reason=f"Rate limit detected: {pattern.pattern}",
                    confidence=0.9
                )

        # Check TEMPORARY patterns / 检查 TEMPORARY 模式
        for pattern in self.compiled_patterns.get(ErrorType.TEMPORARY, []):
            if pattern.search(error_str):
                return ErrorClassification(
                    error_type=ErrorType.TEMPORARY,
                    should_retry=True,
                    recommended_wait=5.0,
                    max_retries=3,
                    fallback_method=None,
                    reason=f"Temporary error detected: {pattern.pattern}",
                    confidence=0.8
                )

        # Unknown error - conservative retry / 未知错误 - 保守重试
        logging.debug(f"No pattern match for {error_type_name}: {error_str[:100]}")
        return ErrorClassification(
            error_type=ErrorType.UNKNOWN,
            should_retry=True,
            recommended_wait=3.0,
            max_retries=2,
            fallback_method=None,
            reason=f"Unknown error type: {error_type_name}",
            confidence=0.5
        )

    def get_cache_metrics(self) -> Optional[dict]:
        """
        Get cache performance metrics / 获取缓存性能指标

        Returns:
            Dictionary with cache metrics or None if cache not available
        """
        if self.cache:
            metrics = self.cache.get_metrics()
            return {
                'total_requests': metrics.total_requests,
                'cache_hits': metrics.cache_hits,
                'cache_misses': metrics.cache_misses,
                'hit_rate': f"{metrics.hit_rate:.2f}%",
                'evictions': metrics.evictions
            }
        return None

    def clear_cache(self):
        """Clear error classification cache / 清除错误分类缓存"""
        if self.cache:
            self.cache.clear()
            logging.info("Error classification cache cleared")
