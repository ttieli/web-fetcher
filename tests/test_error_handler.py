#!/usr/bin/env python3
"""
Unit tests for error_handler module
error_handler模块的单元测试

Tests cover:
- Error classification / 错误分类
- Error chain extraction / 错误链提取
- Root cause analysis / 根因分析
- Markdown report generation / Markdown报告生成
- Troubleshooting guides / 故障排除指南
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path to import error_handler
# 将父目录添加到路径以导入error_handler
sys.path.insert(0, str(Path(__file__).parent.parent))

from error_handler import ErrorClassifier, ErrorCategory, ErrorReporter


class TestErrorClassification(unittest.TestCase):
    """
    Test suite for ErrorClassifier
    ErrorClassifier的测试套件
    """

    def setUp(self):
        """Set up test fixtures / 设置测试夹具"""
        self.classifier = ErrorClassifier()

    def test_network_error_classification(self):
        """
        Test classification of network-related errors
        测试网络相关错误的分类
        """
        # Test ConnectionError
        try:
            raise ConnectionError("Connection refused")
        except Exception as e:
            category = self.classifier.classify(e)
            self.assertEqual(category, ErrorCategory.NETWORK_CONNECTION)

        # Test SSL error
        try:
            raise Exception("SSL certificate verification failed")
        except Exception as e:
            category = self.classifier.classify(e)
            self.assertEqual(category, ErrorCategory.NETWORK_CONNECTION)

        # Test connection timeout
        try:
            raise Exception("Connection timed out")
        except Exception as e:
            category = self.classifier.classify(e)
            self.assertEqual(category, ErrorCategory.NETWORK_CONNECTION)

    def test_browser_init_error_classification(self):
        """
        Test classification of browser initialization errors
        测试浏览器初始化错误的分类
        """
        # Test Chrome error
        try:
            raise Exception("Chrome driver not found")
        except Exception as e:
            category = self.classifier.classify(e)
            self.assertEqual(category, ErrorCategory.BROWSER_INIT)

        # Test WebDriver error
        try:
            raise Exception("WebDriver initialization failed")
        except Exception as e:
            category = self.classifier.classify(e)
            self.assertEqual(category, ErrorCategory.BROWSER_INIT)

        # Test Selenium error
        try:
            raise Exception("Selenium browser not found")
        except Exception as e:
            category = self.classifier.classify(e)
            self.assertEqual(category, ErrorCategory.BROWSER_INIT)

    def test_timeout_error_classification(self):
        """
        Test classification of timeout errors
        测试超时错误的分类
        """
        # Test TimeoutError exception type
        try:
            raise TimeoutError("Operation timed out")
        except Exception as e:
            category = self.classifier.classify(e)
            self.assertEqual(category, ErrorCategory.TIMEOUT)

        # Test timeout in message
        try:
            raise Exception("Request timeout exceeded")
        except Exception as e:
            category = self.classifier.classify(e)
            self.assertEqual(category, ErrorCategory.TIMEOUT)

        # Test deadline exceeded
        try:
            raise Exception("Deadline exceeded while waiting for response")
        except Exception as e:
            category = self.classifier.classify(e)
            self.assertEqual(category, ErrorCategory.TIMEOUT)

    def test_page_load_error_classification(self):
        """
        Test classification of page loading errors
        测试页面加载错误的分类
        """
        # Test page load error
        try:
            raise Exception("Page load timeout")
        except Exception as e:
            category = self.classifier.classify(e)
            self.assertEqual(category, ErrorCategory.PAGE_LOAD)

        # Test navigation error
        try:
            raise Exception("Navigation failed to complete")
        except Exception as e:
            category = self.classifier.classify(e)
            self.assertEqual(category, ErrorCategory.PAGE_LOAD)

        # Test 404 error
        try:
            raise Exception("404 page not found")
        except Exception as e:
            category = self.classifier.classify(e)
            self.assertEqual(category, ErrorCategory.PAGE_LOAD)

    def test_permission_error_classification(self):
        """
        Test classification of permission errors
        测试权限错误的分类
        """
        # Test PermissionError
        try:
            raise PermissionError("Permission denied")
        except Exception as e:
            category = self.classifier.classify(e)
            self.assertEqual(category, ErrorCategory.PERMISSION)

        # Test access denied
        try:
            raise Exception("Access denied to resource")
        except Exception as e:
            category = self.classifier.classify(e)
            self.assertEqual(category, ErrorCategory.PERMISSION)

        # Test 403 error
        try:
            raise Exception("403 Forbidden")
        except Exception as e:
            category = self.classifier.classify(e)
            self.assertEqual(category, ErrorCategory.PERMISSION)

    def test_dependency_error_classification(self):
        """
        Test classification of dependency errors
        测试依赖错误的分类
        """
        # Test ImportError
        try:
            raise ImportError("No module named 'nonexistent'")
        except Exception as e:
            category = self.classifier.classify(e)
            self.assertEqual(category, ErrorCategory.DEPENDENCY)

        # Test ModuleNotFoundError
        try:
            raise ModuleNotFoundError("Module not found: requests")
        except Exception as e:
            category = self.classifier.classify(e)
            self.assertEqual(category, ErrorCategory.DEPENDENCY)

        # Test package not found
        try:
            raise Exception("Package not found in system")
        except Exception as e:
            category = self.classifier.classify(e)
            self.assertEqual(category, ErrorCategory.DEPENDENCY)

    def test_unknown_error_classification(self):
        """
        Test classification of unknown errors
        测试未知错误的分类
        """
        # Test generic error
        try:
            raise Exception("Some random error message")
        except Exception as e:
            category = self.classifier.classify(e)
            self.assertEqual(category, ErrorCategory.UNKNOWN)

        # Test ValueError
        try:
            raise ValueError("Invalid value provided")
        except Exception as e:
            category = self.classifier.classify(e)
            self.assertEqual(category, ErrorCategory.UNKNOWN)

    def test_error_chain_extraction(self):
        """
        Test extraction of error chains
        测试错误链提取
        """
        # Create nested exception chain
        try:
            try:
                try:
                    raise ValueError("Inner error")
                except Exception as inner:
                    raise RuntimeError("Middle error") from inner
            except Exception as middle:
                raise Exception("Outer error") from middle
        except Exception as e:
            chain = self.classifier.get_error_chain(e)
            self.assertGreaterEqual(len(chain), 2)
            self.assertIsInstance(chain[0], Exception)
            self.assertEqual(str(chain[0]), "Outer error")

    def test_error_chain_single_exception(self):
        """
        Test error chain with single exception
        测试单个异常的错误链
        """
        try:
            raise ValueError("Single error")
        except Exception as e:
            chain = self.classifier.get_error_chain(e)
            self.assertEqual(len(chain), 1)
            self.assertIsInstance(chain[0], ValueError)

    def test_root_cause_extraction(self):
        """
        Test root cause extraction
        测试根因提取
        """
        # Create nested exception
        try:
            try:
                raise ValueError("Root cause error")
            except Exception as inner:
                raise RuntimeError("Outer error") from inner
        except Exception as e:
            root_cause = self.classifier.extract_root_cause(e)
            self.assertIn("ValueError", root_cause)
            self.assertIn("Root cause error", root_cause)

    def test_root_cause_single_exception(self):
        """
        Test root cause with single exception
        测试单个异常的根因
        """
        try:
            raise ConnectionError("Connection failed")
        except Exception as e:
            root_cause = self.classifier.extract_root_cause(e)
            self.assertIn("ConnectionError", root_cause)
            self.assertIn("Connection failed", root_cause)


class TestErrorReporter(unittest.TestCase):
    """
    Test suite for ErrorReporter
    ErrorReporter的测试套件
    """

    def setUp(self):
        """Set up test fixtures / 设置测试夹具"""
        self.reporter = ErrorReporter()

    def test_markdown_report_generation(self):
        """
        Test generation of Markdown error reports
        测试Markdown错误报告生成
        """
        # Create sample exception
        try:
            raise TimeoutError("Operation timed out after 30 seconds")
        except Exception as e:
            exception = e

        # Generate report
        metrics = {
            "total_time": "30.5s",
            "attempts": 3,
            "method": "selenium"
        }
        report = self.reporter.generate_markdown_report(
            url="https://example.com",
            metrics=metrics,
            exception=exception
        )

        # Verify report structure
        self.assertIn("Error Report", report)  # Updated to check without emoji
        self.assertIn("Error Summary", report)
        self.assertIn("Error Classification", report)
        self.assertIn("Root Cause Analysis", report)
        self.assertIn("Troubleshooting Steps", report)
        self.assertIn("Technical Details", report)
        self.assertIn("Metrics", report)
        self.assertIn("https://example.com", report)
        self.assertIn("TimeoutError", report)
        self.assertIn("Operation timed out", report)

    def test_markdown_report_without_exception(self):
        """
        Test Markdown report generation without exception
        测试无异常的Markdown报告生成
        """
        metrics = {
            "total_time": "5.2s",
            "method": "urllib"
        }
        report = self.reporter.generate_markdown_report(
            url="https://example.com",
            metrics=metrics,
            exception=None
        )

        # Verify report structure
        self.assertIn("Error Report", report)  # Updated to check without emoji
        self.assertIn("Status", report)
        self.assertIn("No errors occurred", report)
        self.assertIn("Metrics", report)
        self.assertIn("https://example.com", report)

    def test_troubleshooting_guide(self):
        """
        Test retrieval of troubleshooting guides
        测试故障排除指南检索
        """
        # Test network error guide
        guide = self.reporter.get_troubleshooting_guide(ErrorCategory.NETWORK_CONNECTION)
        self.assertIn("title", guide)
        self.assertIn("steps", guide)
        self.assertIn("common_causes", guide)
        self.assertIsInstance(guide["steps"], list)
        self.assertIsInstance(guide["common_causes"], list)
        self.assertGreater(len(guide["steps"]), 0)
        self.assertGreater(len(guide["common_causes"]), 0)

        # Test timeout error guide
        guide = self.reporter.get_troubleshooting_guide(ErrorCategory.TIMEOUT)
        self.assertIn("Timeout", guide["title"])

        # Test browser init guide
        guide = self.reporter.get_troubleshooting_guide(ErrorCategory.BROWSER_INIT)
        self.assertIn("Browser", guide["title"])

    def test_all_categories_have_guides(self):
        """
        Test that all error categories have troubleshooting guides
        测试所有错误类别都有故障排除指南
        """
        for category in ErrorCategory:
            guide = self.reporter.get_troubleshooting_guide(category)
            self.assertIsNotNone(guide)
            self.assertIn("title", guide)
            self.assertIn("steps", guide)
            self.assertIn("common_causes", guide)

    def test_report_with_nested_exception(self):
        """
        Test report generation with nested exceptions
        测试嵌套异常的报告生成
        """
        # Create nested exception
        try:
            try:
                raise ConnectionError("Connection refused")
            except Exception as inner:
                raise TimeoutError("Timeout waiting for connection") from inner
        except Exception as e:
            exception = e

        metrics = {"attempts": 2}
        report = self.reporter.generate_markdown_report(
            url="https://example.com",
            metrics=metrics,
            exception=exception
        )

        # Verify error chain is included
        self.assertIn("Error Chain", report)
        self.assertIn("ConnectionError", report)
        self.assertIn("TimeoutError", report)

    def test_report_metrics_formatting(self):
        """
        Test that metrics are properly formatted in report
        测试指标在报告中的格式正确
        """
        metrics = {
            "total_time": "15.3s",
            "page_load_time": "10.2s",
            "attempts": 2,
            "fallback_used": True
        }

        report = self.reporter.generate_markdown_report(
            url="https://example.com",
            metrics=metrics,
            exception=None
        )

        # Verify all metrics are present
        self.assertIn("Total Time", report)
        self.assertIn("15.3s", report)
        self.assertIn("Page Load Time", report)
        self.assertIn("10.2s", report)
        self.assertIn("Attempts", report)
        self.assertIn("2", report)
        self.assertIn("Fallback Used", report)
        self.assertIn("True", report)


class TestIntegration(unittest.TestCase):
    """
    Integration tests for the error handling framework
    错误处理框架的集成测试
    """

    def test_complete_error_handling_workflow(self):
        """
        Test complete workflow from error to report
        测试从错误到报告的完整工作流程
        """
        classifier = ErrorClassifier()
        reporter = ErrorReporter(classifier)

        # Simulate an error scenario
        try:
            raise ConnectionError("Failed to establish connection to remote server")
        except Exception as e:
            # Classify the error
            category = classifier.classify(e)
            self.assertEqual(category, ErrorCategory.NETWORK_CONNECTION)

            # Extract error details
            root_cause = classifier.extract_root_cause(e)
            self.assertIn("ConnectionError", root_cause)

            # Generate report
            metrics = {
                "url": "https://example.com",
                "attempt_count": 3,
                "total_time": "15.5s"
            }
            report = reporter.generate_markdown_report(
                url="https://example.com",
                metrics=metrics,
                exception=e
            )

            # Verify complete report
            self.assertIn("Error Report", report)  # Updated to check without emoji
            self.assertIn("network_connection", report)
            self.assertIn("ConnectionError", report)
            self.assertIn("Troubleshooting Steps", report)

    def test_classifier_reporter_integration(self):
        """
        Test that classifier and reporter work together correctly
        测试分类器和报告器协同工作正确
        """
        classifier = ErrorClassifier()
        reporter = ErrorReporter(classifier)

        # Test with different error types
        test_cases = [
            (TimeoutError("Timeout"), ErrorCategory.TIMEOUT),
            (ImportError("Module not found"), ErrorCategory.DEPENDENCY),
            (PermissionError("Access denied"), ErrorCategory.PERMISSION),
        ]

        for exception, expected_category in test_cases:
            category = classifier.classify(exception)
            self.assertEqual(category, expected_category)

            report = reporter.generate_markdown_report(
                url="https://test.com",
                metrics={"test": "value"},
                exception=exception
            )
            self.assertIn(expected_category.value, report)


if __name__ == "__main__":
    unittest.main()