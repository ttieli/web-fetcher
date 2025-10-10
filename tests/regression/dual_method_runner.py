#!/usr/bin/env python3
"""
Dual-Method Regression Runner - Execute tests with multiple fetch strategies
双方法回归运行器 - 使用多个抓取策略执行测试

This module extends the standard regression runner to support testing URLs
with multiple fetch methods (urllib, selenium) and comparing results.
本模块扩展标准回归运行器以支持使用多个抓取方法（urllib，selenium）测试 URL 并比较结果。
"""

import sys
import time
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from enum import Enum

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.regression.url_suite_parser import URLTest
from tests.regression.regression_runner import TestStatus, TestResult, RegressionRunner

# Import webfetcher components
try:
    from webfetcher import fetch_html_with_retry, FetchMetrics
    WEBFETCHER_AVAILABLE = True
except ImportError as e:
    logging.error(f"Failed to import webfetcher: {e}")
    WEBFETCHER_AVAILABLE = False
    class FetchMetrics:
        pass


class DifferenceLevel(Enum):
    """
    Classification of content differences between methods.
    方法间内容差异的分类。
    """
    IDENTICAL = "identical"        # <1% difference / <1% 差异
    MINOR = "minor"                # 1-5% difference / 1-5% 差异
    SIGNIFICANT = "significant"     # 5-20% difference / 5-20% 差异
    MAJOR = "major"                # >20% difference / >20% 差异
    ERROR = "error"                # One or both methods failed / 一个或两个方法失败


class URLClassification(Enum):
    """
    Classification of URLs based on JS dependency.
    基于 JS 依赖的 URL 分类。
    """
    STATIC_FRIENDLY = "static-friendly"    # Works well with urllib / urllib 工作良好
    JS_ENHANCED = "js-enhanced"            # Better with selenium / selenium 更好
    JS_REQUIRED = "js-required"            # Requires selenium / 需要 selenium
    UNKNOWN = "unknown"                    # Cannot determine / 无法确定


@dataclass
class MethodResult:
    """
    Result from testing with a single method.
    使用单个方法测试的结果。

    Attributes:
        strategy: Method used (urllib/selenium) / 使用的方法
        status: Test execution status / 测试执行状态
        duration: Execution time in seconds / 执行时间（秒）
        content_size: Size of fetched content / 获取内容的大小
        content_lines: Number of lines in content / 内容行数
        error_message: Error message if failed / 如果失败，错误消息
        fetch_metrics: Webfetcher metrics / Webfetcher 指标
        html: Raw HTML content (optional, for comparison) / 原始 HTML 内容（可选，用于比较）
    """
    strategy: str
    status: TestStatus
    duration: float
    content_size: int = 0
    content_lines: int = 0
    error_message: Optional[str] = None
    fetch_metrics: Optional[FetchMetrics] = None
    html: Optional[str] = None

    @property
    def passed(self) -> bool:
        """Check if method test passed / 检查方法测试是否通过"""
        return self.status == TestStatus.PASSED

    @property
    def failed(self) -> bool:
        """Check if method test failed / 检查方法测试是否失败"""
        return self.status == TestStatus.FAILED or self.status == TestStatus.ERROR


@dataclass
class ContentComparison:
    """
    Comparison results between two methods.
    两种方法之间的比较结果。

    Attributes:
        difference_level: Classification of difference magnitude / 差异幅度分类
        url_classification: Classification of URL JS dependency / URL JS 依赖分类
        size_diff_percent: Size difference percentage / 大小差异百分比
        lines_diff_percent: Lines difference percentage / 行数差异百分比
        urllib_size: Size from urllib method / urllib 方法的大小
        selenium_size: Size from selenium method / selenium 方法的大小
        urllib_lines: Lines from urllib method / urllib 方法的行数
        selenium_lines: Lines from selenium method / selenium 方法的行数
        speed_ratio: Selenium time / urllib time / Selenium 时间 / urllib 时间
        notes: Additional notes about the comparison / 关于比较的附加说明
    """
    difference_level: DifferenceLevel
    url_classification: URLClassification
    size_diff_percent: float
    lines_diff_percent: float
    urllib_size: int
    selenium_size: int
    urllib_lines: int
    selenium_lines: int
    speed_ratio: float
    notes: List[str]


@dataclass
class DualMethodResult:
    """
    Result from dual-method testing.
    双方法测试的结果。

    Attributes:
        test: Original test case / 原始测试用例
        urllib_result: Result from urllib method / urllib 方法的结果
        selenium_result: Result from selenium method / selenium 方法的结果
        comparison: Content comparison (if enabled) / 内容比较（如果启用）
        total_duration: Total time for both methods / 两种方法的总时间
    """
    test: URLTest
    urllib_result: Optional[MethodResult]
    selenium_result: Optional[MethodResult]
    comparison: Optional[ContentComparison]
    total_duration: float

    @property
    def both_passed(self) -> bool:
        """Check if both methods passed / 检查两种方法是否都通过"""
        return (
            self.urllib_result and self.urllib_result.passed and
            self.selenium_result and self.selenium_result.passed
        )

    @property
    def any_passed(self) -> bool:
        """Check if at least one method passed / 检查至少一种方法是否通过"""
        return (
            (self.urllib_result and self.urllib_result.passed) or
            (self.selenium_result and self.selenium_result.passed)
        )

    @property
    def both_failed(self) -> bool:
        """Check if both methods failed / 检查两种方法是否都失败"""
        return (
            (not self.urllib_result or self.urllib_result.failed) and
            (not self.selenium_result or self.selenium_result.failed)
        )


class DualMethodRunner:
    """
    Regression test runner that supports dual-method testing.
    支持双方法测试的回归测试运行器。
    """

    def __init__(self, timeout: int = 30, skip_manual: bool = True):
        """
        Initialize dual-method runner.
        初始化双方法运行器。

        Args:
            timeout: Timeout per URL per method in seconds / 每个方法每个 URL 的超时时间（秒）
            skip_manual: Skip tests tagged 'manual' / 跳过标记为 'manual' 的测试
        """
        self.timeout = timeout
        self.skip_manual = skip_manual

        if not WEBFETCHER_AVAILABLE:
            raise RuntimeError("Webfetcher not available - cannot run regression tests")

    def test_with_method(
        self,
        test: URLTest,
        strategy: str,
        store_html: bool = False
    ) -> MethodResult:
        """
        Test a URL with a specific method.
        使用特定方法测试 URL。

        Args:
            test: URL test case / URL 测试用例
            strategy: Method to use (urllib/selenium) / 要使用的方法
            store_html: Store HTML content for comparison / 存储 HTML 内容以进行比较

        Returns:
            MethodResult: Result from this method / 此方法的结果
        """
        start_time = time.time()
        html = None
        fetch_metrics = None
        error_msg = None

        try:
            # Determine user agent based on URL
            ua = self._get_user_agent(test.url)

            # Fetch the URL with specified method
            html, fetch_metrics = fetch_html_with_retry(
                url=test.url,
                ua=ua,
                timeout=self.timeout,
                fetch_mode=strategy
            )

            # Determine status
            if html and len(html) > 0:
                status = TestStatus.PASSED
            else:
                status = TestStatus.FAILED
                error_msg = "Empty content returned"

        except TimeoutError as e:
            status = TestStatus.ERROR
            error_msg = f"Timeout: {str(e)}"
        except Exception as e:
            status = TestStatus.ERROR
            error_msg = f"{type(e).__name__}: {str(e)}"

        duration = time.time() - start_time
        content_size = len(html) if html else 0
        content_lines = html.count('\n') + 1 if html else 0

        return MethodResult(
            strategy=strategy,
            status=status,
            duration=duration,
            content_size=content_size,
            content_lines=content_lines,
            error_message=error_msg,
            fetch_metrics=fetch_metrics,
            html=html if store_html else None
        )

    def run_dual_method_test(self, test: URLTest) -> DualMethodResult:
        """
        Execute a test with dual methods and compare results.
        使用双方法执行测试并比较结果。

        Args:
            test: URL test case to execute / 要执行的 URL 测试用例

        Returns:
            DualMethodResult: Results from both methods / 两种方法的结果
        """
        # Check if test should be skipped
        if self.skip_manual and test.has_tag('manual'):
            return DualMethodResult(
                test=test,
                urllib_result=MethodResult(
                    strategy="urllib",
                    status=TestStatus.SKIPPED,
                    duration=0.0,
                    error_message="Skipped: manual test"
                ),
                selenium_result=None,
                comparison=None,
                total_duration=0.0
            )

        start_time = time.time()
        urllib_result = None
        selenium_result = None

        # Test with each specified strategy
        store_html = test.compare_methods  # Store HTML only if comparison needed

        if test.has_strategy('urllib'):
            urllib_result = self.test_with_method(test, 'urllib', store_html)

        if test.has_strategy('selenium'):
            selenium_result = self.test_with_method(test, 'selenium', store_html)

        total_duration = time.time() - start_time

        # Compare results if both methods were tested and comparison is enabled
        comparison = None
        if test.compare_methods and urllib_result and selenium_result:
            comparison = self._compare_results(urllib_result, selenium_result)

        return DualMethodResult(
            test=test,
            urllib_result=urllib_result,
            selenium_result=selenium_result,
            comparison=comparison,
            total_duration=total_duration
        )

    def _compare_results(
        self,
        urllib_result: MethodResult,
        selenium_result: MethodResult
    ) -> ContentComparison:
        """
        Compare results from urllib and selenium methods.
        比较 urllib 和 selenium 方法的结果。

        Args:
            urllib_result: Result from urllib / urllib 的结果
            selenium_result: Result from selenium / selenium 的结果

        Returns:
            ContentComparison: Comparison analysis / 比较分析
        """
        notes = []

        # Handle failure cases
        if urllib_result.failed and selenium_result.failed:
            return ContentComparison(
                difference_level=DifferenceLevel.ERROR,
                url_classification=URLClassification.UNKNOWN,
                size_diff_percent=0.0,
                lines_diff_percent=0.0,
                urllib_size=urllib_result.content_size,
                selenium_size=selenium_result.content_size,
                urllib_lines=urllib_result.content_lines,
                selenium_lines=selenium_result.content_lines,
                speed_ratio=0.0,
                notes=["Both methods failed"]
            )

        if urllib_result.failed:
            notes.append("urllib failed, selenium succeeded")
            return ContentComparison(
                difference_level=DifferenceLevel.MAJOR,
                url_classification=URLClassification.JS_REQUIRED,
                size_diff_percent=100.0,
                lines_diff_percent=100.0,
                urllib_size=0,
                selenium_size=selenium_result.content_size,
                urllib_lines=0,
                selenium_lines=selenium_result.content_lines,
                speed_ratio=0.0,
                notes=notes
            )

        if selenium_result.failed:
            notes.append("selenium failed, urllib succeeded")
            return ContentComparison(
                difference_level=DifferenceLevel.MAJOR,
                url_classification=URLClassification.STATIC_FRIENDLY,
                size_diff_percent=100.0,
                lines_diff_percent=100.0,
                urllib_size=urllib_result.content_size,
                selenium_size=0,
                urllib_lines=urllib_result.content_lines,
                selenium_lines=0,
                speed_ratio=0.0,
                notes=notes
            )

        # Both passed - calculate differences
        urllib_size = urllib_result.content_size
        selenium_size = selenium_result.content_size
        urllib_lines = urllib_result.content_lines
        selenium_lines = selenium_result.content_lines

        # Calculate size difference percentage
        max_size = max(urllib_size, selenium_size)
        size_diff_percent = abs(urllib_size - selenium_size) / max_size * 100 if max_size > 0 else 0.0

        # Calculate lines difference percentage
        max_lines = max(urllib_lines, selenium_lines)
        lines_diff_percent = abs(urllib_lines - selenium_lines) / max_lines * 100 if max_lines > 0 else 0.0

        # Calculate speed ratio
        speed_ratio = selenium_result.duration / urllib_result.duration if urllib_result.duration > 0 else 0.0

        # Classify difference level
        diff_level = self._classify_difference(size_diff_percent, lines_diff_percent)

        # Classify URL type
        url_class = self._classify_url(diff_level, urllib_size, selenium_size, notes)

        # Add performance notes
        if speed_ratio > 5.0:
            notes.append(f"selenium {speed_ratio:.1f}x slower than urllib")
        elif speed_ratio > 2.0:
            notes.append(f"selenium {speed_ratio:.1f}x slower")

        return ContentComparison(
            difference_level=diff_level,
            url_classification=url_class,
            size_diff_percent=size_diff_percent,
            lines_diff_percent=lines_diff_percent,
            urllib_size=urllib_size,
            selenium_size=selenium_size,
            urllib_lines=urllib_lines,
            selenium_lines=selenium_lines,
            speed_ratio=speed_ratio,
            notes=notes
        )

    def _classify_difference(
        self,
        size_diff_percent: float,
        lines_diff_percent: float
    ) -> DifferenceLevel:
        """
        Classify the magnitude of difference between methods.
        对方法间差异的幅度进行分类。

        Args:
            size_diff_percent: Size difference percentage / 大小差异百分比
            lines_diff_percent: Lines difference percentage / 行数差异百分比

        Returns:
            DifferenceLevel: Classification of difference / 差异分类
        """
        # Use the larger of the two percentages
        max_diff = max(size_diff_percent, lines_diff_percent)

        if max_diff < 1.0:
            return DifferenceLevel.IDENTICAL
        elif max_diff < 5.0:
            return DifferenceLevel.MINOR
        elif max_diff < 20.0:
            return DifferenceLevel.SIGNIFICANT
        else:
            return DifferenceLevel.MAJOR

    def _classify_url(
        self,
        diff_level: DifferenceLevel,
        urllib_size: int,
        selenium_size: int,
        notes: List[str]
    ) -> URLClassification:
        """
        Classify URL based on JS dependency.
        根据 JS 依赖对 URL 进行分类。

        Args:
            diff_level: Difference level / 差异级别
            urllib_size: Size from urllib / urllib 的大小
            selenium_size: Size from selenium / selenium 的大小
            notes: Notes list to append findings / 要附加发现的注释列表

        Returns:
            URLClassification: URL classification / URL 分类
        """
        if diff_level == DifferenceLevel.IDENTICAL or diff_level == DifferenceLevel.MINOR:
            notes.append("Content nearly identical between methods")
            return URLClassification.STATIC_FRIENDLY

        if diff_level == DifferenceLevel.SIGNIFICANT:
            if selenium_size > urllib_size * 1.5:
                notes.append("selenium provides significantly more content")
                return URLClassification.JS_ENHANCED
            elif urllib_size > selenium_size * 1.5:
                notes.append("urllib provides significantly more content")
                return URLClassification.STATIC_FRIENDLY
            else:
                return URLClassification.JS_ENHANCED

        if diff_level == DifferenceLevel.MAJOR:
            if selenium_size > urllib_size * 2.0:
                notes.append("selenium provides substantially more content")
                return URLClassification.JS_REQUIRED
            elif urllib_size < 1000 and selenium_size > 5000:
                notes.append("urllib returned minimal content")
                return URLClassification.JS_REQUIRED
            else:
                return URLClassification.JS_ENHANCED

        return URLClassification.UNKNOWN

    def _get_user_agent(self, url: str) -> str:
        """
        Get appropriate user agent for URL.
        获取适合 URL 的用户代理。

        Args:
            url: Target URL / 目标 URL

        Returns:
            str: User agent string / 用户代理字符串
        """
        # WeChat uses mobile UA
        if 'mp.weixin.qq.com' in url or 'weixin.qq.com' in url:
            return 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.42(0x18002a2c) NetType/WIFI Language/zh_CN'

        # XiaoHongShu uses desktop Chrome UA
        elif 'xiaohongshu.com' in url or 'xhslink.com' in url:
            return 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

        # Default Chrome UA
        else:
            return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36"

    def run_suite(
        self,
        tests: List[URLTest],
        progress_callback=None
    ) -> List[DualMethodResult]:
        """
        Execute a suite of dual-method tests.
        执行一组双方法测试。

        Args:
            tests: List of tests to execute / 要执行的测试列表
            progress_callback: Optional callback for progress updates / 可选的进度更新回调

        Returns:
            List[DualMethodResult]: Results for all tests / 所有测试的结果
        """
        results = []

        for i, test in enumerate(tests, start=1):
            if progress_callback:
                progress_callback(i, len(tests), test)

            result = self.run_dual_method_test(test)
            results.append(result)

            # Log result
            self._log_result(i, len(tests), result)

        return results

    def _log_result(self, index: int, total: int, result: DualMethodResult) -> None:
        """
        Log a test result.
        记录测试结果。

        Args:
            index: Current test index / 当前测试索引
            total: Total number of tests / 测试总数
            result: Test result to log / 要记录的测试结果
        """
        url_short = result.test.url[:60] + "..." if len(result.test.url) > 60 else result.test.url

        if not result.test.is_dual_method:
            # Single-method test
            method_result = result.urllib_result or result.selenium_result
            if method_result:
                status_symbol = "✓" if method_result.passed else "✗"
                logging.info(
                    f"{status_symbol} [{index}/{total}] {url_short} "
                    f"({method_result.strategy}, {method_result.duration:.2f}s, "
                    f"{method_result.content_size} bytes)"
                )
        else:
            # Dual-method test
            urllib_status = "✓" if result.urllib_result and result.urllib_result.passed else "✗"
            selenium_status = "✓" if result.selenium_result and result.selenium_result.passed else "✗"

            logging.info(
                f"[{index}/{total}] {url_short}"
            )
            if result.urllib_result:
                logging.info(
                    f"  urllib: {urllib_status} ({result.urllib_result.duration:.2f}s, "
                    f"{result.urllib_result.content_size} bytes)"
                )
            if result.selenium_result:
                logging.info(
                    f"  selenium: {selenium_status} ({result.selenium_result.duration:.2f}s, "
                    f"{result.selenium_result.content_size} bytes)"
                )

            if result.comparison:
                logging.info(
                    f"  Comparison: {result.comparison.difference_level.value}, "
                    f"{result.comparison.url_classification.value}"
                )


def print_summary(results: List[DualMethodResult]) -> None:
    """
    Print summary of dual-method test results.
    打印双方法测试结果摘要。

    Args:
        results: List of dual-method test results / 双方法测试结果列表
    """
    total = len(results)
    single_method = sum(1 for r in results if not r.test.is_dual_method)
    dual_method = total - single_method

    # Count single-method results
    single_passed = sum(
        1 for r in results
        if not r.test.is_dual_method and r.any_passed
    )

    # Count dual-method results
    dual_both_passed = sum(1 for r in results if r.test.is_dual_method and r.both_passed)
    dual_partial = sum(
        1 for r in results
        if r.test.is_dual_method and r.any_passed and not r.both_passed
    )
    dual_both_failed = sum(1 for r in results if r.test.is_dual_method and r.both_failed)

    total_duration = sum(r.total_duration for r in results)

    print("\n" + "=" * 70)
    print("DUAL-METHOD REGRESSION TEST SUMMARY / 双方法回归测试摘要")
    print("=" * 70)
    print(f"Total Tests:       {total}")
    print(f"Single-Method:     {single_method} ({single_passed} passed)")
    print(f"Dual-Method:       {dual_method} ({dual_both_passed} both passed, {dual_partial} partial)")
    print(f"Total Duration:    {total_duration:.2f}s")
    print()

    # Classification summary
    if dual_method > 0:
        comparisons = [r.comparison for r in results if r.comparison]
        if comparisons:
            print("URL Classifications / URL 分类:")
            classifications = {}
            for comp in comparisons:
                classifications[comp.url_classification.value] = classifications.get(comp.url_classification.value, 0) + 1

            for class_name, count in sorted(classifications.items()):
                print(f"  {class_name}: {count}")
            print()

    print("=" * 70 + "\n")


if __name__ == '__main__':
    # Simple test of the dual-method runner
    import sys
    from url_suite_parser import parse_url_suite

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    suite_file = Path(__file__).parent.parent / 'url_suite.txt'

    try:
        tests = parse_url_suite(suite_file)
        print(f"Loaded {len(tests)} tests from suite\n")

        # Create a simple dual-method test
        test_url = "https://httpbin.org/html"
        dual_test = URLTest(
            url=test_url,
            description="HTTPBin test (dual-method)",
            expected_strategies=["urllib", "selenium"],
            tags={"test"},
            line_number=999,
            compare_methods=True
        )

        print(f"Running dual-method test on: {test_url}\n")
        runner = DualMethodRunner(timeout=30, skip_manual=True)
        result = runner.run_dual_method_test(dual_test)

        print("\nResults:")
        print(f"  urllib: {result.urllib_result.status.value if result.urllib_result else 'N/A'}")
        print(f"  selenium: {result.selenium_result.status.value if result.selenium_result else 'N/A'}")
        if result.comparison:
            print(f"  Difference: {result.comparison.difference_level.value}")
            print(f"  Classification: {result.comparison.url_classification.value}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
