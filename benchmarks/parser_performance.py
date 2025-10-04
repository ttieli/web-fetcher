#!/usr/bin/env python3
"""
Parser Performance Benchmark - Phase 3.1

Measures and compares performance of legacy and migrated parsers.
Generates performance reports for migration validation.
"""

import time
import sys
import os
from typing import Dict, List, Tuple, Callable
from dataclasses import dataclass
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class BenchmarkResult:
    """Performance benchmark result"""
    parser_name: str
    test_case: str
    execution_time: float
    success: bool
    error_message: str = ""


class ParserPerformanceBenchmark:
    """Performance benchmark suite for parsers"""

    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.test_data = self._prepare_test_data()

    def _prepare_test_data(self) -> Dict[str, Tuple[str, str]]:
        """
        Prepare test data for benchmarking

        Returns:
            Dict mapping test case name to (html, url) tuple
        """
        # Sample WeChat HTML
        wechat_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta property="og:title" content="测试文章标题">
            <meta property="og:article:author" content="测试作者">
        </head>
        <body>
            <div id="js_content">
                <p>这是一段测试内容。</p>
                <p>包含多个段落。</p>
                <img data-src="https://mmbiz.qpic.cn/test.jpg">
            </div>
        </body>
        </html>
        """

        # Sample XHS HTML
        xhs_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta property="og:title" content="小红书测试 - 小红书">
            <meta property="description" content="这是测试描述内容">
            <meta property="og:image" content="https://ci.xiaohongshu.com/test.jpg">
            <script type="application/ld+json">
            {
                "author": {"name": "测试用户"},
                "datePublished": "2024-10-04"
            }
            </script>
        </head>
        <body>
            <div class="content">测试内容</div>
        </body>
        </html>
        """

        # Sample Generic HTML
        generic_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta property="og:title" content="通用测试文章">
            <meta property="description" content="通用文章描述">
        </head>
        <body>
            <main>
                <article>
                    <h1>文章标题</h1>
                    <p>第一段内容，包含足够的文字以满足内容长度验证要求。这段文字需要达到至少500字节的阈值。</p>
                    <p>第二段继续添加更多内容。测试内容提取功能的准确性和性能表现。需要确保提取到的内容质量符合要求。</p>
                    <p>第三段进一步扩充内容。在实际应用中，文章内容通常会更长，包含更多的段落和信息。这里我们模拟一个基本的文章结构。</p>
                    <p>第四段添加更多测试数据。性能测试需要使用具有代表性的样本数据，以便准确评估解析器的实际表现。</p>
                    <p>第五段完成内容填充。确保总内容长度超过500字节的阈值，这样才能被现代选择器正确提取。</p>
                </article>
            </main>
        </body>
        </html>
        """

        return {
            'wechat_basic': (wechat_html, 'https://mp.weixin.qq.com/s/test123'),
            'xhs_basic': (xhs_html, 'https://www.xiaohongshu.com/explore/test456'),
            'generic_basic': (generic_html, 'https://example.com/article/test789'),
        }

    def _benchmark_function(self, func: Callable, html: str, url: str, iterations: int = 10) -> Tuple[float, bool, str]:
        """
        Benchmark a parser function

        Args:
            func: Parser function to benchmark
            html: HTML content
            url: URL parameter
            iterations: Number of iterations

        Returns:
            Tuple of (avg_time, success, error_message)
        """
        times = []
        error_message = ""
        success = True

        for i in range(iterations):
            try:
                start = time.perf_counter()
                result = func(html, url)
                end = time.perf_counter()

                # Validate result
                if not result or not isinstance(result, tuple) or len(result) != 3:
                    success = False
                    error_message = f"Invalid result format: {type(result)}"
                    break

                times.append(end - start)

            except Exception as e:
                success = False
                error_message = f"Exception: {str(e)}"
                break

        avg_time = sum(times) / len(times) if times else 0
        return avg_time, success, error_message

    def test_wechat_performance(self) -> None:
        """Benchmark WeChat parser performance"""
        print("\n" + "=" * 60)
        print("WeChat Parser Performance Test")
        print("=" * 60)

        html, url = self.test_data['wechat_basic']

        # Test legacy parser
        try:
            from parsers_legacy import wechat_to_markdown as legacy_wechat
            avg_time, success, error = self._benchmark_function(legacy_wechat, html, url)
            self.results.append(BenchmarkResult(
                parser_name="wechat_legacy",
                test_case="wechat_basic",
                execution_time=avg_time,
                success=success,
                error_message=error
            ))
            print(f"Legacy Parser: {avg_time*1000:.3f}ms (Success: {success})")
            if error:
                print(f"  Error: {error}")
        except Exception as e:
            print(f"Legacy Parser: FAILED - {e}")
            self.results.append(BenchmarkResult(
                parser_name="wechat_legacy",
                test_case="wechat_basic",
                execution_time=0,
                success=False,
                error_message=str(e)
            ))

        # Test migrated parser
        try:
            from parsers_migrated import wechat_to_markdown as migrated_wechat
            avg_time, success, error = self._benchmark_function(migrated_wechat, html, url)
            self.results.append(BenchmarkResult(
                parser_name="wechat_migrated",
                test_case="wechat_basic",
                execution_time=avg_time,
                success=success,
                error_message=error
            ))
            print(f"Migrated Parser: {avg_time*1000:.3f}ms (Success: {success})")
            if error:
                print(f"  Error: {error}")
        except Exception as e:
            print(f"Migrated Parser: FAILED - {e}")
            self.results.append(BenchmarkResult(
                parser_name="wechat_migrated",
                test_case="wechat_basic",
                execution_time=0,
                success=False,
                error_message=str(e)
            ))

    def test_xhs_performance(self) -> None:
        """Benchmark XHS parser performance"""
        print("\n" + "=" * 60)
        print("XiaoHongShu Parser Performance Test")
        print("=" * 60)

        html, url = self.test_data['xhs_basic']

        # Test legacy parser
        try:
            from parsers_legacy import xhs_to_markdown as legacy_xhs
            avg_time, success, error = self._benchmark_function(legacy_xhs, html, url)
            self.results.append(BenchmarkResult(
                parser_name="xhs_legacy",
                test_case="xhs_basic",
                execution_time=avg_time,
                success=success,
                error_message=error
            ))
            print(f"Legacy Parser: {avg_time*1000:.3f}ms (Success: {success})")
            if error:
                print(f"  Error: {error}")
        except Exception as e:
            print(f"Legacy Parser: FAILED - {e}")
            self.results.append(BenchmarkResult(
                parser_name="xhs_legacy",
                test_case="xhs_basic",
                execution_time=0,
                success=False,
                error_message=str(e)
            ))

        # Test migrated parser
        try:
            from parsers_migrated import xhs_to_markdown as migrated_xhs
            avg_time, success, error = self._benchmark_function(migrated_xhs, html, url)
            self.results.append(BenchmarkResult(
                parser_name="xhs_migrated",
                test_case="xhs_basic",
                execution_time=avg_time,
                success=success,
                error_message=error
            ))
            print(f"Migrated Parser: {avg_time*1000:.3f}ms (Success: {success})")
            if error:
                print(f"  Error: {error}")
        except Exception as e:
            print(f"Migrated Parser: FAILED - {e}")
            self.results.append(BenchmarkResult(
                parser_name="xhs_migrated",
                test_case="xhs_basic",
                execution_time=0,
                success=False,
                error_message=str(e)
            ))

    def test_generic_performance(self) -> None:
        """Benchmark Generic parser performance"""
        print("\n" + "=" * 60)
        print("Generic Parser Performance Test")
        print("=" * 60)

        html, url = self.test_data['generic_basic']

        # Test legacy parser
        try:
            from parsers_legacy import generic_to_markdown as legacy_generic
            avg_time, success, error = self._benchmark_function(legacy_generic, html, url)
            self.results.append(BenchmarkResult(
                parser_name="generic_legacy",
                test_case="generic_basic",
                execution_time=avg_time,
                success=success,
                error_message=error
            ))
            print(f"Legacy Parser: {avg_time*1000:.3f}ms (Success: {success})")
            if error:
                print(f"  Error: {error}")
        except Exception as e:
            print(f"Legacy Parser: FAILED - {e}")
            self.results.append(BenchmarkResult(
                parser_name="generic_legacy",
                test_case="generic_basic",
                execution_time=0,
                success=False,
                error_message=str(e)
            ))

        # Test migrated parser
        try:
            from parsers_migrated import generic_to_markdown as migrated_generic
            avg_time, success, error = self._benchmark_function(migrated_generic, html, url)
            self.results.append(BenchmarkResult(
                parser_name="generic_migrated",
                test_case="generic_basic",
                execution_time=avg_time,
                success=success,
                error_message=error
            ))
            print(f"Migrated Parser: {avg_time*1000:.3f}ms (Success: {success})")
            if error:
                print(f"  Error: {error}")
        except Exception as e:
            print(f"Migrated Parser: FAILED - {e}")
            self.results.append(BenchmarkResult(
                parser_name="generic_migrated",
                test_case="generic_basic",
                execution_time=0,
                success=False,
                error_message=str(e)
            ))

    def generate_report(self) -> None:
        """Generate performance report"""
        print("\n" + "=" * 60)
        print("Performance Benchmark Report")
        print("=" * 60)
        print(f"\nTotal Tests: {len(self.results)}")

        # Group by test case
        test_cases = {}
        for result in self.results:
            if result.test_case not in test_cases:
                test_cases[result.test_case] = []
            test_cases[result.test_case].append(result)

        # Print comparison table for each test case
        for test_case, results in test_cases.items():
            print(f"\n{test_case.upper()}")
            print("-" * 60)
            print(f"{'Parser':<20} {'Time (ms)':<15} {'Status':<10}")
            print("-" * 60)

            for result in results:
                status = "SUCCESS" if result.success else "FAILED"
                time_str = f"{result.execution_time*1000:.3f}" if result.success else "N/A"
                print(f"{result.parser_name:<20} {time_str:<15} {status:<10}")

                if result.error_message:
                    print(f"  Error: {result.error_message}")

        # Calculate speedup/slowdown
        print("\n" + "=" * 60)
        print("Migration Performance Impact")
        print("=" * 60)

        for test_case, results in test_cases.items():
            legacy = next((r for r in results if 'legacy' in r.parser_name), None)
            migrated = next((r for r in results if 'migrated' in r.parser_name), None)

            if legacy and migrated and legacy.success and migrated.success:
                if legacy.execution_time > 0:
                    ratio = migrated.execution_time / legacy.execution_time
                    change = ((migrated.execution_time - legacy.execution_time) / legacy.execution_time) * 100

                    print(f"\n{test_case}:")
                    print(f"  Legacy: {legacy.execution_time*1000:.3f}ms")
                    print(f"  Migrated: {migrated.execution_time*1000:.3f}ms")
                    print(f"  Ratio: {ratio:.2f}x")
                    print(f"  Change: {change:+.1f}%")

    def run_all(self) -> None:
        """Run all performance tests"""
        print("=" * 60)
        print("Parser Performance Benchmark Suite - Phase 3.1")
        print("=" * 60)

        self.test_wechat_performance()
        self.test_xhs_performance()
        self.test_generic_performance()
        self.generate_report()

        print("\n" + "=" * 60)
        print("Benchmark Complete")
        print("=" * 60)


def main():
    """Main entry point"""
    benchmark = ParserPerformanceBenchmark()
    benchmark.run_all()


if __name__ == '__main__':
    main()
