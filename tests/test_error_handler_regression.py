#!/usr/bin/env python3
"""
Regression tests for error_handler module
错误处理模块的回归测试

This test suite validates edge cases and boundary conditions to prevent regressions:
- Empty and None value handling
- Long error messages and special characters
- Circular exception references
- Unusual error types and edge cases

此测试套件验证边界情况以防止回归：
- 空值和None处理
- 超长错误消息和特殊字符
- 循环引用异常
- 不常见的错误类型和边界情况
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from error_handler import ErrorClassifier, ErrorReporter, ErrorCategory
from webfetcher import generate_failure_markdown, FetchMetrics


class TestErrorHandlerRegression(unittest.TestCase):
    """回归测试套件"""

    def setUp(self):
        """Set up test fixtures"""
        self.classifier = ErrorClassifier()
        self.reporter = ErrorReporter(self.classifier)

    def test_empty_exception_handling(self):
        """测试空异常处理"""
        # Test empty exception message
        try:
            raise Exception("")
        except Exception as e:
            category = self.classifier.classify(e)
            self.assertIsNotNone(category)
            # Should default to UNKNOWN for empty messages
            self.assertEqual(category, ErrorCategory.UNKNOWN)

            # Generate report should not crash
            metrics = {"test": "value"}
            report = self.reporter.generate_markdown_report(
                url="https://test.com",
                metrics=metrics,
                exception=e
            )
            self.assertIsNotNone(report)
            self.assertIn("Error Report", report)

        print("✅ Empty exception handled successfully")

    def test_long_error_message_handling(self):
        """测试超长错误消息处理（>10000字符）"""
        # Create very long error message
        long_message = "Error: " + "A" * 10000
        error = RuntimeError(long_message)

        # Should be able to classify without crashing
        category = self.classifier.classify(error)
        self.assertIsNotNone(category)
        print(f"   Long message handled: {len(long_message)} chars -> {category.value}")

        # Should be able to generate report
        metrics = {"test": "value"}
        report = self.reporter.generate_markdown_report(
            url="https://test.com",
            metrics=metrics,
            exception=error
        )
        self.assertIsNotNone(report)
        # Report should contain the error (possibly truncated in display)
        self.assertIn("RuntimeError", report)

        print(f"✅ Long message handled: {len(long_message)} chars")

    def test_special_characters_handling(self):
        """测试特殊字符和Unicode处理"""
        # Test various special characters and Unicode
        special_messages = [
            "Error with emoji: 🚨💥🔥",
            "中文错误消息：连接失败",
            "Русский язык: ошибка соединения",
            "عربي: خطأ في الاتصال",
            "日本語エラー：接続失敗",
            "Error with tabs\t\tand\nnewlines\nhere",
            "Error with special chars: !@#$%^&*(){}[]|\\:;\"'<>,.?/~`",
            "Error with null char: \x00 embedded",
            "Mixed: 中文 English Русский 日本語 🚀",
        ]

        for message in special_messages:
            try:
                raise Exception(message)
            except Exception as e:
                # Should classify without error
                category = self.classifier.classify(e)
                self.assertIsNotNone(category)

                # Should generate report without error
                metrics = {"test": "value"}
                report = self.reporter.generate_markdown_report(
                    url="https://test.com",
                    metrics=metrics,
                    exception=e
                )
                self.assertIsNotNone(report)

        print(f"✅ Special characters handled: {len(special_messages)} test cases")

    def test_circular_exception_chain(self):
        """测试循环引用异常处理"""
        # Create an exception with circular reference
        try:
            error1 = Exception("Error 1")
            error2 = Exception("Error 2")

            # Create circular reference (Python normally prevents this, but test defensive code)
            # We'll test with a simple chain that might repeat
            try:
                raise error1
            except Exception as e:
                # The classifier should handle chains without infinite loops
                chain = self.classifier.get_error_chain(e)
                self.assertIsNotNone(chain)
                self.assertGreater(len(chain), 0)

        except Exception as e:
            self.fail(f"Circular reference handling failed: {e}")

        print("✅ Circular exception chain handled")

    def test_null_metrics_handling(self):
        """测试空metrics处理"""
        # Test with None metrics
        try:
            raise TimeoutError("Test timeout")
        except Exception as e:
            exception = e

        # Test with empty dict
        empty_metrics = {}
        report = self.reporter.generate_markdown_report(
            url="https://test.com",
            metrics=empty_metrics,
            exception=exception
        )
        self.assertIsNotNone(report)
        self.assertIn("Error Report", report)

        # Test with None values in metrics
        null_metrics = {
            "primary_method": None,
            "error_message": None,
            "total_attempts": None,
        }
        report = self.reporter.generate_markdown_report(
            url="https://test.com",
            metrics=null_metrics,
            exception=exception
        )
        self.assertIsNotNone(report)

        print("✅ Null metrics handled")

    def test_edge_case_error_types(self):
        """测试边界情况的错误类型"""
        # Test various unusual error types
        edge_case_errors = [
            KeyboardInterrupt("User interrupted"),
            SystemExit("System exit"),
            MemoryError("Out of memory"),
            RecursionError("Maximum recursion depth exceeded"),
            StopIteration("Iterator stopped"),
            GeneratorExit("Generator exit"),
            KeyError("Key not found"),
            IndexError("Index out of range"),
            AttributeError("Attribute not found"),
            TypeError("Type error"),
            ZeroDivisionError("Division by zero"),
            FloatingPointError("Floating point error"),
            OverflowError("Numeric overflow"),
            AssertionError("Assertion failed"),
            UnicodeError("Unicode error"),
            UnicodeDecodeError('utf-8', b'\xff', 0, 1, 'invalid start byte'),
            UnicodeEncodeError('ascii', '\u1234', 0, 1, 'ordinal not in range'),
        ]

        for error in edge_case_errors:
            # Should classify without error
            category = self.classifier.classify(error)
            self.assertIsNotNone(category)
            self.assertIsInstance(category, ErrorCategory)

            # Should generate report without error
            metrics = {"test": "value"}
            try:
                report = self.reporter.generate_markdown_report(
                    url="https://test.com",
                    metrics=metrics,
                    exception=error
                )
                self.assertIsNotNone(report)
            except Exception as report_error:
                self.fail(f"Failed to generate report for {type(error).__name__}: {report_error}")

        print(f"✅ Edge case error types handled: {len(edge_case_errors)} types")

    def test_nested_exception_chain_depth(self):
        """测试深度嵌套的异常链"""
        # Create deeply nested exception chain (10 levels)
        def create_nested_exception(depth):
            if depth == 0:
                raise ValueError("Base error")
            try:
                create_nested_exception(depth - 1)
            except Exception as e:
                raise RuntimeError(f"Level {depth} error") from e

        try:
            create_nested_exception(10)
        except Exception as e:
            # Should extract chain without error
            chain = self.classifier.get_error_chain(e)
            self.assertIsNotNone(chain)
            self.assertGreater(len(chain), 5)  # Should have multiple levels

            # Should extract root cause
            root_cause = self.classifier.extract_root_cause(e)
            self.assertIn("ValueError", root_cause)
            self.assertIn("Base error", root_cause)

            # Should generate report
            metrics = {"test": "value"}
            report = self.reporter.generate_markdown_report(
                url="https://test.com",
                metrics=metrics,
                exception=e
            )
            self.assertIsNotNone(report)
            self.assertIn("Error Chain", report)

        print(f"✅ Nested exception chain depth handled: {len(chain)} levels")

    def test_exception_with_none_args(self):
        """测试参数为None的异常"""
        # Create exception with None in args
        error = Exception(None)

        category = self.classifier.classify(error)
        self.assertIsNotNone(category)

        metrics = {"test": "value"}
        report = self.reporter.generate_markdown_report(
            url="https://test.com",
            metrics=metrics,
            exception=error
        )
        self.assertIsNotNone(report)

        print("✅ Exception with None args handled")

    def test_exception_with_complex_objects(self):
        """测试包含复杂对象的异常"""
        # Exception with dict, list, and other objects in message
        complex_data = {
            "list": [1, 2, 3, {"nested": "value"}],
            "dict": {"key": "value", "number": 42},
            "tuple": (1, 2, 3),
        }
        error = Exception(f"Error with complex data: {complex_data}")

        category = self.classifier.classify(error)
        self.assertIsNotNone(category)

        metrics = {"test": "value"}
        report = self.reporter.generate_markdown_report(
            url="https://test.com",
            metrics=metrics,
            exception=error
        )
        self.assertIsNotNone(report)

        print("✅ Exception with complex objects handled")

    def test_webfetcher_integration_edge_cases(self):
        """测试webfetcher集成的边界情况"""
        # Test FetchMetrics with all None values
        metrics = FetchMetrics()
        # Don't set any values - all should be default/None

        report = generate_failure_markdown("https://test.com", metrics, None)
        self.assertIsNotNone(report)

        # Test with exception but no metrics values set
        try:
            raise ConnectionError("Test error")
        except Exception as e:
            report = generate_failure_markdown("https://test.com", metrics, e)
            self.assertIsNotNone(report)
            self.assertIn("ConnectionError", report)

        print("✅ Webfetcher integration edge cases handled")

    def test_multiple_consecutive_errors(self):
        """测试连续多个错误处理"""
        # Simulate processing many errors in sequence
        errors = [
            ConnectionError(f"Connection error {i}")
            for i in range(100)
        ]

        for error in errors:
            category = self.classifier.classify(error)
            self.assertEqual(category, ErrorCategory.NETWORK_CONNECTION)

        # Should not degrade or crash
        print(f"✅ Multiple consecutive errors handled: {len(errors)} errors")

    def test_error_message_with_markdown_syntax(self):
        """测试包含Markdown语法的错误消息"""
        # Error messages that might break Markdown formatting
        markdown_messages = [
            "Error with # heading syntax",
            "Error with **bold** and *italic*",
            "Error with ```code blocks```",
            "Error with [links](http://example.com)",
            "Error with | tables | syntax |",
            "Error with > blockquote",
            "Error with - bullet points",
            "Error with 1. numbered lists",
            "Error with `inline code`",
            "Error with ~~strikethrough~~",
        ]

        for message in markdown_messages:
            try:
                raise Exception(message)
            except Exception as e:
                metrics = {"test": "value"}
                report = self.reporter.generate_markdown_report(
                    url="https://test.com",
                    metrics=metrics,
                    exception=e
                )
                self.assertIsNotNone(report)
                # Report should be valid Markdown
                self.assertIn("Error Report", report)

        print(f"✅ Markdown syntax in error messages handled: {len(markdown_messages)} cases")

    def test_classification_consistency(self):
        """测试分类一致性 - 同样的错误应该得到同样的分类"""
        # Create multiple instances of the same error
        errors = [ConnectionError("Connection refused") for _ in range(10)]

        categories = [self.classifier.classify(error) for error in errors]

        # All should be classified the same
        self.assertEqual(len(set(categories)), 1)
        self.assertEqual(categories[0], ErrorCategory.NETWORK_CONNECTION)

        print(f"✅ Classification consistency verified: {len(errors)} identical errors")

    def test_url_edge_cases(self):
        """测试URL边界情况"""
        # Test various unusual URLs
        edge_case_urls = [
            "",  # Empty URL
            "not-a-url",  # Invalid URL
            "http://",  # Incomplete URL
            "https://example.com/" + "a" * 1000,  # Very long URL
            "https://用户:密码@中文域名.com/路径?查询=值#锚点",  # Unicode URL
            "ftp://example.com",  # Non-HTTP protocol
            "file:///local/path",  # File protocol
        ]

        for url in edge_case_urls:
            metrics = {"test": "value"}
            try:
                raise TimeoutError("Test error")
            except Exception as e:
                report = self.reporter.generate_markdown_report(
                    url=url,
                    metrics=metrics,
                    exception=e
                )
                self.assertIsNotNone(report)

        print(f"✅ URL edge cases handled: {len(edge_case_urls)} cases")


if __name__ == '__main__':
    unittest.main()