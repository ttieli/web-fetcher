#!/usr/bin/env python3
"""
Integration tests for error_handler module with webfetcher
错误处理模块与webfetcher的集成测试

This test suite validates the integration between error_handler and webfetcher modules,
ensuring proper error classification, reporting, and troubleshooting guide generation.
此测试套件验证error_handler和webfetcher模块之间的集成，
确保正确的错误分类、报告和故障排除指南生成。
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from error_handler import ErrorClassifier, ErrorReporter, ErrorCategory
from webfetcher import generate_failure_markdown, FetchMetrics


class TestErrorHandlerIntegration(unittest.TestCase):
    """测试错误处理器与webfetcher的集成"""

    def setUp(self):
        """Set up test fixtures"""
        self.classifier = ErrorClassifier()
        self.reporter = ErrorReporter(self.classifier)

    def test_webfetcher_network_error_handling(self):
        """验证网络错误在webfetcher中的处理"""
        # Create FetchMetrics with network error
        metrics = FetchMetrics()
        metrics.primary_method = "urllib"
        metrics.final_status = "failed"
        metrics.error_message = "Connection refused by remote server"
        metrics.total_attempts = 3

        # Create network exception
        try:
            raise ConnectionError("Connection refused")
        except Exception as e:
            exception = e

        # Call generate_failure_markdown
        report = generate_failure_markdown("https://example.com", metrics, exception)

        # Verify report contains NETWORK_CONNECTION classification
        self.assertIn("network_connection", report.lower())
        self.assertIn("Error Classification", report)
        self.assertIn("Troubleshooting", report)

        # Verify troubleshooting steps are present
        self.assertIn("Network Connection", report)
        self.assertIn("internet connection", report.lower())
        print("✅ Network error handling verified")

    def test_webfetcher_timeout_error_handling(self):
        """验证超时错误在webfetcher中的处理"""
        # Create FetchMetrics with timeout error
        metrics = FetchMetrics()
        metrics.primary_method = "selenium"
        metrics.final_status = "failed"
        metrics.error_message = "Operation timed out after 30 seconds"
        metrics.total_attempts = 2

        # Create timeout exception
        try:
            raise TimeoutError("Operation timed out")
        except Exception as e:
            exception = e

        # Call generate_failure_markdown
        report = generate_failure_markdown("https://slow-site.com", metrics, exception)

        # Verify timeout classification
        self.assertIn("timeout", report.lower())
        self.assertIn("Error Classification", report)
        self.assertIn("TimeoutError", report)

        # Verify troubleshooting steps
        self.assertIn("Timeout", report)
        self.assertIn("timeout values", report.lower())
        print("✅ Timeout error handling verified")

    def test_webfetcher_browser_init_error_handling(self):
        """验证浏览器初始化错误的处理"""
        # Create FetchMetrics with browser init error
        metrics = FetchMetrics()
        metrics.primary_method = "selenium"
        metrics.final_status = "failed"
        metrics.error_message = "ChromeDriver not found in system PATH"

        # Create browser initialization exception
        try:
            raise Exception("Chrome driver executable not found")
        except Exception as e:
            exception = e

        # Call generate_failure_markdown
        report = generate_failure_markdown("https://example.com", metrics, exception)

        # Verify browser_init classification
        self.assertIn("browser_init", report.lower())
        self.assertIn("Browser Initialization", report)

        # Verify troubleshooting steps include Chrome/ChromeDriver guidance
        self.assertIn("Chrome", report)
        self.assertIn("ChromeDriver", report)
        print("✅ Browser initialization error handling verified")

    def test_error_report_markdown_format(self):
        """验证错误报告的Markdown格式一致性"""
        # Create various error scenarios and verify format consistency
        test_cases = [
            (ConnectionError("Connection refused"), "network"),
            (TimeoutError("Timeout"), "timeout"),
            (ImportError("Module not found"), "dependency"),
        ]

        for exception, expected_keyword in test_cases:
            metrics = FetchMetrics()
            metrics.primary_method = "urllib"
            metrics.final_status = "failed"
            metrics.error_message = str(exception)

            report = generate_failure_markdown("https://test.com", metrics, exception)

            # Verify mandatory sections exist
            self.assertIn("# ", report)  # Title with heading
            self.assertIn("Error Report", report)
            self.assertIn("Error Classification", report)
            self.assertIn("Troubleshooting", report)
            self.assertIn("Metrics", report)

            # Verify metrics are displayed
            self.assertIn("Primary Method", report)
            self.assertIn("Final Status", report)

        print("✅ Markdown format consistency verified")

    def test_error_report_troubleshooting_steps(self):
        """验证故障排除步骤的完整性"""
        # Test that all error categories have complete troubleshooting steps
        test_errors = [
            (ConnectionError("Connection failed"), ErrorCategory.NETWORK_CONNECTION),
            (Exception("Chrome initialization failed"), ErrorCategory.BROWSER_INIT),
            (Exception("Page load timeout"), ErrorCategory.PAGE_LOAD),
            (PermissionError("Permission denied"), ErrorCategory.PERMISSION),
            (ImportError("No module named test"), ErrorCategory.DEPENDENCY),
            (TimeoutError("Timeout"), ErrorCategory.TIMEOUT),
        ]

        for exception, expected_category in test_errors:
            # Classify the error
            category = self.classifier.classify(exception)

            # Get troubleshooting guide
            guide = self.reporter.get_troubleshooting_guide(category)

            # Verify guide completeness
            self.assertIn("title", guide)
            self.assertIn("steps", guide)
            self.assertIn("common_causes", guide)
            self.assertIsInstance(guide["steps"], list)
            self.assertIsInstance(guide["common_causes"], list)
            self.assertGreater(len(guide["steps"]), 3, f"Insufficient steps for {category}")
            self.assertGreater(len(guide["common_causes"]), 2, f"Insufficient causes for {category}")

            # Generate report and verify steps are included
            metrics = FetchMetrics()
            metrics.final_status = "failed"
            metrics.error_message = str(exception)

            report = generate_failure_markdown("https://test.com", metrics, exception)
            self.assertIn("Troubleshooting Steps", report)
            self.assertIn("Common Causes", report)

        print("✅ Troubleshooting steps completeness verified")

    def test_backward_compatibility(self):
        """验证向后兼容性 - 测试ERROR_HANDLER_AVAILABLE=False场景"""
        # Mock ERROR_HANDLER_AVAILABLE to False
        import webfetcher
        original_flag = webfetcher.ERROR_HANDLER_AVAILABLE

        try:
            # Temporarily disable error handler
            webfetcher.ERROR_HANDLER_AVAILABLE = False

            # Create metrics
            metrics = FetchMetrics()
            metrics.primary_method = "urllib"
            metrics.final_status = "failed"
            metrics.error_message = "Connection failed"

            # Generate report without error handler
            report = generate_failure_markdown("https://example.com", metrics, None)

            # Verify fallback report still works
            self.assertIsNotNone(report)
            self.assertIn("https://example.com", report)
            self.assertIn("Failed" if not os.environ.get('LANG', '').lower().startswith('zh') else "失败", report)

            print("✅ Backward compatibility verified")

        finally:
            # Restore original flag
            webfetcher.ERROR_HANDLER_AVAILABLE = original_flag

    def test_error_chain_in_report(self):
        """验证错误链在报告中的正确显示"""
        # Create nested exception chain
        try:
            try:
                raise ConnectionError("Socket connection failed")
            except Exception as inner:
                raise TimeoutError("Connection timeout after socket failure") from inner
        except Exception as e:
            exception = e

        metrics = FetchMetrics()
        metrics.final_status = "failed"
        metrics.error_message = "Nested error occurred"

        report = generate_failure_markdown("https://example.com", metrics, exception)

        # Verify error chain section exists
        self.assertIn("Error Chain", report)
        self.assertIn("ConnectionError", report)
        self.assertIn("TimeoutError", report)

        print("✅ Error chain reporting verified")

    def test_metrics_integration(self):
        """验证FetchMetrics与ErrorReporter的集成"""
        # Create comprehensive metrics
        metrics = FetchMetrics()
        metrics.primary_method = "selenium"
        metrics.fallback_method = "urllib"
        metrics.total_attempts = 3
        metrics.fetch_duration = 15.5
        metrics.render_duration = 2.3
        metrics.ssl_fallback_used = True
        metrics.final_status = "failed"
        metrics.error_message = "Multiple attempts failed"
        metrics.selenium_wait_time = 10.2
        metrics.chrome_connected = False

        exception = TimeoutError("All attempts timed out")

        report = generate_failure_markdown("https://example.com", metrics, exception)

        # Verify metrics are properly included in report
        self.assertIn("Metrics", report)
        self.assertIn("Primary Method", report)
        self.assertIn("selenium", report.lower())

        print("✅ Metrics integration verified")

    def test_all_error_categories_coverage(self):
        """验证所有7个错误类别都能正确处理"""
        # Test all 7 error categories
        test_cases = [
            (ConnectionError("Connection refused"), ErrorCategory.NETWORK_CONNECTION),
            (Exception("Chrome not found"), ErrorCategory.BROWSER_INIT),
            (Exception("Page load failed"), ErrorCategory.PAGE_LOAD),
            (PermissionError("Access denied"), ErrorCategory.PERMISSION),
            (ImportError("Module missing"), ErrorCategory.DEPENDENCY),
            (TimeoutError("Timeout"), ErrorCategory.TIMEOUT),
            (ValueError("Unknown error"), ErrorCategory.UNKNOWN),
        ]

        for exception, expected_category in test_cases:
            # Classify
            category = self.classifier.classify(exception)
            self.assertEqual(category, expected_category,
                           f"Failed to classify {exception} as {expected_category}")

            # Generate report
            metrics = FetchMetrics()
            metrics.final_status = "failed"
            metrics.error_message = str(exception)

            report = generate_failure_markdown("https://test.com", metrics, exception)

            # Verify category is in report
            self.assertIn(expected_category.value, report.lower())

        print("✅ All 7 error categories coverage verified")

    def test_exception_none_handling(self):
        """验证exception=None情况的处理"""
        # Test when exception is None but metrics indicate failure
        metrics = FetchMetrics()
        metrics.primary_method = "urllib"
        metrics.final_status = "failed"
        metrics.error_message = "Connection timeout"

        # Call with exception=None
        report = generate_failure_markdown("https://example.com", metrics, exception=None)

        # Verify report is still generated
        self.assertIsNotNone(report)
        self.assertIn("Error", report)
        self.assertIn("Connection timeout", report)

        print("✅ Exception=None handling verified")


class TestSeleniumFetcherIntegration(unittest.TestCase):
    """测试与selenium_fetcher的集成（如果存在）"""

    def setUp(self):
        """Set up test fixtures"""
        self.classifier = ErrorClassifier()
        self.reporter = ErrorReporter(self.classifier)

    def test_chrome_connection_failure(self):
        """测试Chrome连接失败场景"""
        # Create metrics simulating Chrome connection failure
        metrics = FetchMetrics()
        metrics.primary_method = "selenium"
        metrics.final_status = "failed"
        metrics.error_message = "Failed to connect to Chrome on port 9222"
        metrics.chrome_connected = False

        # Simulate Chrome connection error
        try:
            raise Exception("Failed to connect to Chrome at 127.0.0.1:9222")
        except Exception as e:
            exception = e

        # Generate report
        report = generate_failure_markdown("https://example.com", metrics, exception)

        # Verify Chrome-specific guidance is provided
        self.assertIn("Chrome", report)
        self.assertIn("9222", report)

        # Verify error is classified as BROWSER_INIT
        category = self.classifier.classify(exception)
        self.assertEqual(category, ErrorCategory.BROWSER_INIT)

        print("✅ Chrome connection failure handling verified")

    def test_page_load_timeout(self):
        """测试页面加载超时场景"""
        # Create metrics for page load timeout
        metrics = FetchMetrics()
        metrics.primary_method = "selenium"
        metrics.final_status = "failed"
        metrics.error_message = "Page load timeout after 30 seconds"
        metrics.chrome_connected = True
        metrics.selenium_wait_time = 30.0

        # Simulate page load timeout
        try:
            raise TimeoutError("Page load timeout")
        except Exception as e:
            exception = e

        # Generate report
        report = generate_failure_markdown("https://slow-site.com", metrics, exception)

        # Verify timeout classification and guidance
        self.assertIn("timeout", report.lower())
        self.assertIn("Timeout", report)

        category = self.classifier.classify(exception)
        self.assertEqual(category, ErrorCategory.TIMEOUT)

        print("✅ Page load timeout handling verified")

    def test_selenium_not_available_error(self):
        """测试Selenium不可用的情况"""
        # Simulate scenario where Selenium is not available
        metrics = FetchMetrics()
        metrics.primary_method = "urllib"
        metrics.fallback_method = None
        metrics.final_status = "success"  # Should fall back gracefully

        # Verify that when Selenium is not available, system falls back
        # This is more of a documentation test
        report = generate_failure_markdown("https://example.com", metrics, None)

        # When no error, report should indicate success or no error
        self.assertIn("Status", report) or self.assertIn("Metrics", report)

        print("✅ Selenium unavailable scenario handled")


if __name__ == '__main__':
    unittest.main()