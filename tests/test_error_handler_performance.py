#!/usr/bin/env python3
"""
Performance benchmark tests for error_handler module
错误处理模块的性能基准测试

This test suite validates that error_handler meets performance requirements:
- Classification speed < 1ms per error
- Report generation < 10ms per report
- Memory usage < 10MB for 1000 errors
- Concurrent handling > 100 errors/second

此测试套件验证error_handler满足性能要求：
- 分类速度 < 1ms每个错误
- 报告生成 < 10ms每个报告
- 内存使用 < 10MB/1000错误
- 并发处理 > 100错误/秒
"""

import unittest
import time
import sys
import os
import tracemalloc
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from error_handler import ErrorClassifier, ErrorReporter, ErrorCategory


class TestErrorHandlerPerformance(unittest.TestCase):
    """性能基准测试"""

    def setUp(self):
        """Set up test fixtures"""
        self.classifier = ErrorClassifier()
        self.reporter = ErrorReporter(self.classifier)

    def test_classification_speed(self):
        """错误分类速度：< 1ms per classification"""
        # Create diverse set of test errors
        errors = [
            ConnectionError('Connection refused'),
            ConnectionError('Connection reset by peer'),
            TimeoutError('Operation timed out'),
            TimeoutError('Timeout waiting for response'),
            ImportError('No module named test'),
            ImportError('Cannot import module'),
            PermissionError('Permission denied'),
            PermissionError('Access denied'),
            Exception('Chrome driver not found'),
            Exception('WebDriver initialization failed'),
            Exception('Page load timeout'),
            Exception('404 not found'),
            ValueError('Invalid value'),
            RuntimeError('Runtime error'),
            Exception('SSL certificate error'),
        ]

        # Warmup run
        for error in errors:
            self.classifier.classify(error)

        # Performance test: 1000 iterations
        iterations = 1000
        start = time.time()
        for _ in range(iterations):
            for error in errors:
                self.classifier.classify(error)
        duration = time.time() - start

        total_classifications = iterations * len(errors)
        avg_time = duration / total_classifications

        # Assert performance requirement: < 1ms (0.001s)
        self.assertLess(avg_time, 0.001,
                       f"Classification too slow: {avg_time*1000:.3f}ms (requirement: < 1ms)")

        print(f"✅ Classification speed: {avg_time*1000:.6f}ms per classification")
        print(f"   Total classifications: {total_classifications}")
        print(f"   Total time: {duration:.3f}s")
        print(f"   Throughput: {total_classifications/duration:.0f} classifications/second")

    def test_report_generation_speed(self):
        """报告生成速度：< 10ms per report"""
        # Create test exception
        try:
            raise TimeoutError("Operation timed out after 30 seconds")
        except Exception as e:
            exception = e

        # Create test metrics
        metrics = {
            "primary_method": "selenium",
            "total_attempts": 3,
            "fetch_duration": 15.5,
            "final_status": "failed",
            "error_message": "Timeout error"
        }

        # Warmup run
        for _ in range(10):
            self.reporter.generate_markdown_report(
                url="https://example.com",
                metrics=metrics,
                exception=exception
            )

        # Performance test: 100 reports
        iterations = 100
        start = time.time()
        for i in range(iterations):
            report = self.reporter.generate_markdown_report(
                url=f"https://example{i}.com",
                metrics=metrics,
                exception=exception
            )
            # Verify report was generated
            self.assertIsNotNone(report)
        duration = time.time() - start

        avg_time = duration / iterations

        # Assert performance requirement: < 10ms (0.01s)
        self.assertLess(avg_time, 0.01,
                       f"Report generation too slow: {avg_time*1000:.3f}ms (requirement: < 10ms)")

        print(f"✅ Report generation speed: {avg_time*1000:.3f}ms per report")
        print(f"   Total reports: {iterations}")
        print(f"   Total time: {duration:.3f}s")
        print(f"   Throughput: {iterations/duration:.0f} reports/second")

    def test_memory_usage(self):
        """内存使用：< 10MB for 1000 errors"""
        # Start memory tracking
        tracemalloc.start()

        # Get baseline memory
        tracemalloc.reset_peak()

        # Create and classify 1000 diverse errors
        errors_to_process = 1000
        processed_errors = []

        for i in range(errors_to_process):
            # Create different types of errors
            error_type = i % 7
            if error_type == 0:
                error = ConnectionError(f"Connection error {i}")
            elif error_type == 1:
                error = TimeoutError(f"Timeout error {i}")
            elif error_type == 2:
                error = ImportError(f"Import error {i}")
            elif error_type == 3:
                error = PermissionError(f"Permission error {i}")
            elif error_type == 4:
                error = Exception(f"Chrome error {i}")
            elif error_type == 5:
                error = Exception(f"Page load error {i}")
            else:
                error = ValueError(f"Unknown error {i}")

            # Classify and store
            category = self.classifier.classify(error)
            processed_errors.append((error, category))

        # Get peak memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Convert to MB
        peak_mb = peak / (1024 * 1024)

        # Assert performance requirement: < 10MB
        self.assertLess(peak_mb, 10.0,
                       f"Memory usage too high: {peak_mb:.2f}MB (requirement: < 10MB)")

        print(f"✅ Memory usage: {peak_mb:.2f}MB for {errors_to_process} errors")
        print(f"   Current memory: {current/(1024*1024):.2f}MB")
        print(f"   Peak memory: {peak_mb:.2f}MB")
        print(f"   Memory per error: {peak/(errors_to_process*1024):.2f}KB")

    def test_concurrent_handling(self):
        """并发处理能力：> 100 errors/second"""
        # Create test errors
        def create_error(i):
            error_type = i % 5
            if error_type == 0:
                return ConnectionError(f"Connection error {i}")
            elif error_type == 1:
                return TimeoutError(f"Timeout error {i}")
            elif error_type == 2:
                return ImportError(f"Import error {i}")
            elif error_type == 3:
                return PermissionError(f"Permission error {i}")
            else:
                return Exception(f"Generic error {i}")

        # Function to classify an error
        def classify_error(error):
            return self.classifier.classify(error)

        # Test concurrent classification
        num_errors = 500
        max_workers = 10

        start = time.time()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = [executor.submit(classify_error, create_error(i))
                      for i in range(num_errors)]

            # Wait for all to complete
            results = [future.result() for future in as_completed(futures)]

        duration = time.time() - start

        errors_per_second = num_errors / duration

        # Assert performance requirement: > 100 errors/second
        self.assertGreater(errors_per_second, 100,
                          f"Concurrent handling too slow: {errors_per_second:.0f} errors/second (requirement: > 100)")

        print(f"✅ Concurrent handling: {errors_per_second:.0f} errors/second")
        print(f"   Total errors: {num_errors}")
        print(f"   Total time: {duration:.3f}s")
        print(f"   Workers: {max_workers}")
        print(f"   Average time per error: {duration*1000/num_errors:.3f}ms")

    def test_error_chain_extraction_performance(self):
        """错误链提取性能测试"""
        # Create nested exception chain
        try:
            try:
                try:
                    try:
                        raise ValueError("Inner error")
                    except Exception as e1:
                        raise RuntimeError("Middle error 1") from e1
                except Exception as e2:
                    raise ConnectionError("Middle error 2") from e2
            except Exception as e3:
                raise TimeoutError("Outer error") from e3
        except Exception as e:
            exception = e

        # Performance test: 1000 chain extractions
        iterations = 1000
        start = time.time()
        for _ in range(iterations):
            chain = self.classifier.get_error_chain(exception)
            self.assertGreater(len(chain), 1)
        duration = time.time() - start

        avg_time = duration / iterations

        # Should be very fast (< 1ms)
        self.assertLess(avg_time, 0.001,
                       f"Chain extraction too slow: {avg_time*1000:.3f}ms")

        print(f"✅ Error chain extraction: {avg_time*1000:.6f}ms per extraction")
        print(f"   Chain length: {len(chain)}")
        print(f"   Total extractions: {iterations}")

    def test_root_cause_extraction_performance(self):
        """根因提取性能测试"""
        # Create nested exception
        try:
            try:
                raise ConnectionError("Root cause: connection refused")
            except Exception as inner:
                raise TimeoutError("Timeout waiting for connection") from inner
        except Exception as e:
            exception = e

        # Performance test: 1000 root cause extractions
        iterations = 1000
        start = time.time()
        for _ in range(iterations):
            root_cause = self.classifier.extract_root_cause(exception)
            self.assertIn("ConnectionError", root_cause)
        duration = time.time() - start

        avg_time = duration / iterations

        # Should be very fast (< 1ms)
        self.assertLess(avg_time, 0.001,
                       f"Root cause extraction too slow: {avg_time*1000:.3f}ms")

        print(f"✅ Root cause extraction: {avg_time*1000:.6f}ms per extraction")
        print(f"   Total extractions: {iterations}")

    def test_pattern_matching_efficiency(self):
        """模式匹配效率测试"""
        # Test that pattern matching doesn't degrade with multiple patterns
        test_messages = [
            "Connection refused by remote host",
            "SSL certificate verification failed",
            "Chrome driver not found in PATH",
            "Operation timed out after 30 seconds",
            "Module not found: requests",
            "Permission denied to access file",
            "Page load failed with error 404",
        ]

        # Performance test
        iterations = 1000
        start = time.time()
        for _ in range(iterations):
            for message in test_messages:
                error = Exception(message)
                category = self.classifier.classify(error)
                self.assertIsNotNone(category)
        duration = time.time() - start

        total_classifications = iterations * len(test_messages)
        avg_time = duration / total_classifications

        # Should be fast (< 1ms)
        self.assertLess(avg_time, 0.001,
                       f"Pattern matching too slow: {avg_time*1000:.3f}ms")

        print(f"✅ Pattern matching: {avg_time*1000:.6f}ms per classification")
        print(f"   Test messages: {len(test_messages)}")
        print(f"   Total classifications: {total_classifications}")

    def test_troubleshooting_guide_retrieval_speed(self):
        """故障排除指南检索速度测试"""
        # Test all categories
        categories = list(ErrorCategory)

        # Performance test: 1000 retrievals per category
        iterations = 1000
        start = time.time()
        for _ in range(iterations):
            for category in categories:
                guide = self.reporter.get_troubleshooting_guide(category)
                self.assertIsNotNone(guide)
                self.assertIn("steps", guide)
        duration = time.time() - start

        total_retrievals = iterations * len(categories)
        avg_time = duration / total_retrievals

        # Should be very fast (< 0.1ms)
        self.assertLess(avg_time, 0.0001,
                       f"Guide retrieval too slow: {avg_time*1000:.6f}ms")

        print(f"✅ Troubleshooting guide retrieval: {avg_time*1000:.6f}ms per retrieval")
        print(f"   Categories tested: {len(categories)}")
        print(f"   Total retrievals: {total_retrievals}")


if __name__ == '__main__':
    unittest.main()