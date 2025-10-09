#!/usr/bin/env python3
"""
Unit Tests for Unified Error Classifier
统一错误分类器的单元测试
"""

import pytest
import ssl
from urllib.error import HTTPError, URLError
from io import BytesIO

# Import the modules we're testing
from error_classifier import UnifiedErrorClassifier
from error_types import ErrorType, ErrorClassification


class TestUnifiedErrorClassifier:
    """Test suite for UnifiedErrorClassifier / UnifiedErrorClassifier的测试套件"""

    @pytest.fixture
    def classifier(self):
        """Create a classifier instance for testing / 创建用于测试的分类器实例"""
        return UnifiedErrorClassifier()

    def test_classifier_initialization(self, classifier):
        """Test that classifier initializes with patterns / 测试分类器使用模式初始化"""
        assert classifier.patterns is not None
        assert classifier.compiled_patterns is not None
        assert len(classifier.compiled_patterns) > 0

    def test_http_404_permanent_error(self, classifier):
        """Test HTTP 404 classified as PERMANENT / 测试HTTP 404被分类为PERMANENT"""
        # Create a mock HTTPError for 404
        error = HTTPError(
            url="http://example.com",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=BytesIO()
        )

        classification = classifier.classify_error(error, "http://example.com")

        assert classification.error_type == ErrorType.PERMANENT
        assert classification.should_retry is False
        assert classification.max_retries == 0
        assert classification.fallback_method is None
        assert classification.confidence == 1.0
        assert "404" in classification.reason

    def test_http_403_permanent_error(self, classifier):
        """Test HTTP 403 classified as PERMANENT / 测试HTTP 403被分类为PERMANENT"""
        error = HTTPError(
            url="http://example.com",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=BytesIO()
        )

        classification = classifier.classify_error(error, "http://example.com")

        assert classification.error_type == ErrorType.PERMANENT
        assert classification.should_retry is False
        assert "403" in classification.reason

    def test_http_503_temporary_error(self, classifier):
        """Test HTTP 503 classified as TEMPORARY / 测试HTTP 503被分类为TEMPORARY"""
        error = HTTPError(
            url="http://example.com",
            code=503,
            msg="Service Unavailable",
            hdrs={},
            fp=BytesIO()
        )

        classification = classifier.classify_error(error, "http://example.com")

        assert classification.error_type == ErrorType.TEMPORARY
        assert classification.should_retry is True
        assert classification.max_retries == 3
        assert classification.recommended_wait > 0
        assert "503" in classification.reason

    def test_http_500_temporary_error(self, classifier):
        """Test HTTP 500 classified as TEMPORARY / 测试HTTP 500被分类为TEMPORARY"""
        error = HTTPError(
            url="http://example.com",
            code=500,
            msg="Internal Server Error",
            hdrs={},
            fp=BytesIO()
        )

        classification = classifier.classify_error(error, "http://example.com")

        assert classification.error_type == ErrorType.TEMPORARY
        assert classification.should_retry is True
        assert "500" in classification.reason

    def test_http_429_rate_limit(self, classifier):
        """Test HTTP 429 classified as RATE_LIMIT / 测试HTTP 429被分类为RATE_LIMIT"""
        error = HTTPError(
            url="http://example.com",
            code=429,
            msg="Too Many Requests",
            hdrs={},
            fp=BytesIO()
        )

        classification = classifier.classify_error(error, "http://example.com")

        assert classification.error_type == ErrorType.RATE_LIMIT
        assert classification.should_retry is True
        assert classification.recommended_wait >= 60.0  # Long backoff for rate limits
        assert classification.max_retries == 3
        assert "429" in classification.reason

    def test_ssl_unsafe_renegotiation_error(self, classifier):
        """Test SSL UNSAFE_LEGACY_RENEGOTIATION error / 测试SSL UNSAFE_LEGACY_RENEGOTIATION错误"""
        error = ssl.SSLError("UNSAFE_LEGACY_RENEGOTIATION_DISABLED")

        classification = classifier.classify_error(error, "https://example.com")

        assert classification.error_type == ErrorType.SSL_CONFIG
        assert classification.should_retry is False
        assert classification.fallback_method == "selenium"
        assert "SSL configuration issue" in classification.reason
        assert classification.confidence == 1.0

    def test_ssl_certificate_verify_failed(self, classifier):
        """Test SSL certificate verification failure / 测试SSL证书验证失败"""
        error = ssl.SSLError("CERTIFICATE_VERIFY_FAILED")

        classification = classifier.classify_error(error, "https://example.com")

        assert classification.error_type == ErrorType.PERMANENT
        assert classification.should_retry is False
        assert classification.fallback_method == "selenium"
        assert "certificate verification failed" in classification.reason.lower()

    def test_ssl_handshake_failure(self, classifier):
        """Test SSL handshake failure / 测试SSL握手失败"""
        error = ssl.SSLError("SSLV3_ALERT_HANDSHAKE_FAILURE")

        classification = classifier.classify_error(error, "https://example.com")

        assert classification.error_type == ErrorType.SSL_CONFIG
        assert classification.should_retry is False
        assert classification.fallback_method == "selenium"

    def test_ssl_wrong_version(self, classifier):
        """Test SSL wrong version error / 测试SSL版本错误"""
        error = ssl.SSLError("WRONG_VERSION_NUMBER")

        classification = classifier.classify_error(error, "https://example.com")

        assert classification.error_type == ErrorType.SSL_CONFIG
        assert classification.fallback_method == "selenium"

    def test_url_connection_reset(self, classifier):
        """Test connection reset error / 测试连接重置错误"""
        error = URLError("Connection reset by peer")

        classification = classifier.classify_error(error, "http://example.com")

        assert classification.error_type == ErrorType.TEMPORARY
        assert classification.should_retry is True
        assert classification.max_retries == 3
        assert "Connection reset" in classification.reason

    def test_url_connection_timeout(self, classifier):
        """Test connection timeout error / 测试连接超时错误"""
        error = URLError("Connection timed out")

        classification = classifier.classify_error(error, "http://example.com")

        assert classification.error_type == ErrorType.TEMPORARY
        assert classification.should_retry is True
        assert "timed out" in classification.reason.lower()

    def test_url_dns_error(self, classifier):
        """Test DNS resolution error / 测试DNS解析错误"""
        error = URLError("Name or service not known")

        classification = classifier.classify_error(error, "http://example.com")

        assert classification.error_type == ErrorType.PERMANENT
        assert classification.should_retry is False
        assert "DNS resolution failed" in classification.reason
        assert classification.cache_duration is not None

    def test_unknown_error_conservative_retry(self, classifier):
        """Test unknown error gets conservative retry / 测试未知错误获得保守重试"""
        error = Exception("Some unknown error occurred")

        classification = classifier.classify_error(error, "http://example.com")

        assert classification.error_type == ErrorType.UNKNOWN
        assert classification.should_retry is True
        assert classification.max_retries == 2  # Conservative
        assert classification.confidence < 1.0  # Lower confidence

    def test_pattern_matching_case_insensitive(self, classifier):
        """Test pattern matching is case-insensitive / 测试模式匹配不区分大小写"""
        # Test with different cases
        error1 = Exception("HTTP Error 404")
        error2 = Exception("http error 404")
        error3 = Exception("Http Error 404")

        classification1 = classifier.classify_http_error(
            HTTPError("http://example.com", 404, "Not Found", {}, BytesIO())
        )
        # Pattern matching tests
        result1 = classifier._classify_by_pattern("HTTP Error 404", "Exception")
        result2 = classifier._classify_by_pattern("http error 404", "Exception")

        assert result1.error_type == result2.error_type

    def test_backoff_recommendations(self, classifier):
        """Test different error types have appropriate backoff times / 测试不同错误类型有适当的退避时间"""
        # Temporary error - short wait
        temp_error = HTTPError("http://example.com", 503, "Service Unavailable", {}, BytesIO())
        temp_classification = classifier.classify_error(temp_error)
        assert 0 < temp_classification.recommended_wait < 10

        # Rate limit - long wait
        rate_error = HTTPError("http://example.com", 429, "Too Many Requests", {}, BytesIO())
        rate_classification = classifier.classify_error(rate_error)
        assert rate_classification.recommended_wait >= 60

        # Permanent error - no wait
        perm_error = HTTPError("http://example.com", 404, "Not Found", {}, BytesIO())
        perm_classification = classifier.classify_error(perm_error)
        assert perm_classification.recommended_wait == 0

    def test_max_retries_appropriate(self, classifier):
        """Test max retries are appropriate for error types / 测试最大重试次数对错误类型合适"""
        # Permanent - no retries
        perm_error = HTTPError("http://example.com", 404, "Not Found", {}, BytesIO())
        perm_classification = classifier.classify_error(perm_error)
        assert perm_classification.max_retries == 0

        # Temporary - multiple retries
        temp_error = HTTPError("http://example.com", 503, "Service Unavailable", {}, BytesIO())
        temp_classification = classifier.classify_error(temp_error)
        assert temp_classification.max_retries >= 3

        # SSL config - no retries (fallback to Selenium)
        ssl_error = ssl.SSLError("UNSAFE_LEGACY_RENEGOTIATION_DISABLED")
        ssl_classification = classifier.classify_error(ssl_error)
        assert ssl_classification.max_retries == 0

    def test_selenium_fallback_recommendation(self, classifier):
        """Test Selenium fallback is recommended for appropriate errors / 测试适当错误推荐Selenium回退"""
        # SSL errors should recommend Selenium
        ssl_error = ssl.SSLError("UNSAFE_LEGACY_RENEGOTIATION_DISABLED")
        ssl_classification = classifier.classify_error(ssl_error)
        assert ssl_classification.fallback_method == "selenium"

        # Certificate errors should recommend Selenium
        cert_error = ssl.SSLError("CERTIFICATE_VERIFY_FAILED")
        cert_classification = classifier.classify_error(cert_error)
        assert cert_classification.fallback_method == "selenium"

        # Regular HTTP errors should not recommend Selenium
        http_error = HTTPError("http://example.com", 404, "Not Found", {}, BytesIO())
        http_classification = classifier.classify_error(http_error)
        assert http_classification.fallback_method is None

    def test_confidence_levels(self, classifier):
        """Test confidence levels are appropriate / 测试置信度水平合适"""
        # HTTP status codes should have high confidence
        http_error = HTTPError("http://example.com", 404, "Not Found", {}, BytesIO())
        http_classification = classifier.classify_error(http_error)
        assert http_classification.confidence >= 0.9

        # Unknown errors should have low confidence
        unknown_error = Exception("Some unknown error")
        unknown_classification = classifier.classify_error(unknown_error)
        assert unknown_classification.confidence < 0.9

    def test_cache_duration_for_permanent_errors(self, classifier):
        """Test permanent errors have cache duration / 测试永久性错误有缓存持续时间"""
        perm_error = HTTPError("http://example.com", 404, "Not Found", {}, BytesIO())
        classification = classifier.classify_error(perm_error)

        assert classification.error_type == ErrorType.PERMANENT
        assert classification.cache_duration is not None
        assert classification.cache_duration > 0

    def test_pattern_compilation_performance(self, classifier):
        """Test that patterns are pre-compiled for performance / 测试模式已预编译以提高性能"""
        import re

        # Verify patterns are compiled
        for error_type, patterns in classifier.compiled_patterns.items():
            for pattern in patterns:
                assert isinstance(pattern, re.Pattern)

        # Verify number of compiled patterns matches original patterns
        total_patterns = sum(len(patterns) for patterns in classifier.patterns.values())
        total_compiled = sum(len(patterns) for patterns in classifier.compiled_patterns.values())
        assert total_patterns == total_compiled

    def test_error_reason_is_descriptive(self, classifier):
        """Test error reasons are descriptive and helpful / 测试错误原因描述清晰有帮助"""
        test_cases = [
            (HTTPError("http://example.com", 404, "Not Found", {}, BytesIO()), "404"),
            (HTTPError("http://example.com", 503, "Service Unavailable", {}, BytesIO()), "503"),
            (ssl.SSLError("UNSAFE_LEGACY_RENEGOTIATION_DISABLED"), "SSL"),
            (URLError("Connection reset by peer"), "Connection"),
        ]

        for error, expected_keyword in test_cases:
            classification = classifier.classify_error(error)
            assert expected_keyword.lower() in classification.reason.lower()
            assert len(classification.reason) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
