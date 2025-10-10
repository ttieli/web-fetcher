#!/usr/bin/env python3
"""
Regression Test Runner - Execute regression tests against URL suite
回归测试运行器 - 对 URL 套件执行回归测试

This module executes regression tests using the existing webfetcher infrastructure.
本模块使用现有的 webfetcher 基础设施执行回归测试。
"""

import sys
import time
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
from enum import Enum

# Add parent directory to path to import webfetcher
# 将父目录添加到路径以导入 webfetcher
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.regression.url_suite_parser import URLTest


# Import webfetcher components
# 导入 webfetcher 组件
try:
    from webfetcher import fetch_html_with_retry, FetchMetrics
    WEBFETCHER_AVAILABLE = True
except ImportError as e:
    logging.error(f"Failed to import webfetcher: {e}")
    WEBFETCHER_AVAILABLE = False
    # Create dummy for type hints
    class FetchMetrics:
        pass


class TestStatus(Enum):
    """Test execution status / 测试执行状态"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """
    Result of a single test execution.
    单个测试执行的结果。

    Attributes:
        test: Original test case / 原始测试用例
        status: Execution status / 执行状态
        duration: Execution time in seconds / 执行时间（秒）
        content_size: Size of fetched content / 获取内容的大小
        error_message: Error message if failed / 如果失败，错误消息
        fetch_metrics: Webfetcher metrics / Webfetcher 指标
        strategy_used: Actual strategy used (urllib/selenium) / 实际使用的策略
    """
    test: URLTest
    status: TestStatus
    duration: float
    content_size: int = 0
    error_message: Optional[str] = None
    fetch_metrics: Optional[FetchMetrics] = None
    strategy_used: Optional[str] = None

    @property
    def passed(self) -> bool:
        """Check if test passed / 检查测试是否通过"""
        return self.status == TestStatus.PASSED

    @property
    def failed(self) -> bool:
        """Check if test failed / 检查测试是否失败"""
        return self.status == TestStatus.FAILED

    @property
    def skipped(self) -> bool:
        """Check if test was skipped / 检查测试是否被跳过"""
        return self.status == TestStatus.SKIPPED


class RegressionRunner:
    """
    Regression test runner that executes URL suite tests.
    执行 URL 套件测试的回归测试运行器。
    """

    def __init__(self, timeout: int = 30, skip_manual: bool = True):
        """
        Initialize regression runner.
        初始化回归测试运行器。

        Args:
            timeout: Timeout per URL in seconds / 每个 URL 的超时时间（秒）
            skip_manual: Skip tests tagged 'manual' / 跳过标记为 'manual' 的测试
        """
        self.timeout = timeout
        self.skip_manual = skip_manual

        if not WEBFETCHER_AVAILABLE:
            raise RuntimeError("Webfetcher not available - cannot run regression tests")

    def run_test(self, test: URLTest) -> TestResult:
        """
        Execute a single test case.
        执行单个测试用例。

        Args:
            test: URL test case to execute / 要执行的 URL 测试用例

        Returns:
            TestResult: Test execution result / 测试执行结果
        """
        # Check if test should be skipped
        # 检查测试是否应该跳过
        if self.skip_manual and test.has_tag('manual'):
            return TestResult(
                test=test,
                status=TestStatus.SKIPPED,
                duration=0.0,
                error_message="Skipped: manual test"
            )

        # Execute the test
        # 执行测试
        start_time = time.time()
        html = None
        fetch_metrics = None
        error_msg = None
        strategy_used = None

        try:
            # Determine fetch mode based on expected strategy
            # 根据期望的策略确定抓取模式
            fetch_mode = 'auto'  # Default to auto routing
            if test.expected_strategy == 'urllib':
                fetch_mode = 'urllib'
            elif test.expected_strategy == 'selenium':
                fetch_mode = 'selenium'

            # Determine user agent based on URL
            # 根据 URL 确定用户代理
            ua = self._get_user_agent(test.url)

            # Fetch the URL
            # 抓取 URL
            html, fetch_metrics = fetch_html_with_retry(
                url=test.url,
                ua=ua,
                timeout=self.timeout,
                fetch_mode=fetch_mode
            )

            # Extract strategy used
            # 提取使用的策略
            if fetch_metrics:
                strategy_used = fetch_metrics.primary_method or 'unknown'

            # Determine test status
            # 确定测试状态
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

        return TestResult(
            test=test,
            status=status,
            duration=duration,
            content_size=content_size,
            error_message=error_msg,
            fetch_metrics=fetch_metrics,
            strategy_used=strategy_used
        )

    def run_suite(
        self,
        tests: List[URLTest],
        progress_callback=None
    ) -> List[TestResult]:
        """
        Execute a suite of tests.
        执行一组测试。

        Args:
            tests: List of tests to execute / 要执行的测试列表
            progress_callback: Optional callback for progress updates / 可选的进度更新回调

        Returns:
            List[TestResult]: Results for all tests / 所有测试的结果
        """
        results = []

        for i, test in enumerate(tests, start=1):
            if progress_callback:
                progress_callback(i, len(tests), test)

            result = self.run_test(test)
            results.append(result)

            # Log result
            # 记录结果
            status_symbol = self._get_status_symbol(result.status)
            logging.info(
                f"{status_symbol} [{i}/{len(tests)}] {test.url[:60]}... "
                f"({result.duration:.2f}s, {result.content_size} bytes)"
            )

        return results

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
        # 微信使用移动 UA
        if 'mp.weixin.qq.com' in url or 'weixin.qq.com' in url:
            return 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.42(0x18002a2c) NetType/WIFI Language/zh_CN'

        # XiaoHongShu uses desktop Chrome UA
        # 小红书使用桌面 Chrome UA
        elif 'xiaohongshu.com' in url or 'xhslink.com' in url:
            return 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

        # Default Chrome UA
        # 默认 Chrome UA
        else:
            return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36"

    def _get_status_symbol(self, status: TestStatus) -> str:
        """
        Get colored symbol for test status.
        获取测试状态的彩色符号。

        Args:
            status: Test status / 测试状态

        Returns:
            str: Status symbol / 状态符号
        """
        symbols = {
            TestStatus.PASSED: "✓",
            TestStatus.FAILED: "✗",
            TestStatus.SKIPPED: "⊘",
            TestStatus.ERROR: "⚠"
        }
        return symbols.get(status, "?")


def print_summary(results: List[TestResult]) -> None:
    """
    Print summary of test results.
    打印测试结果摘要。

    Args:
        results: List of test results / 测试结果列表
    """
    total = len(results)
    passed = sum(1 for r in results if r.status == TestStatus.PASSED)
    failed = sum(1 for r in results if r.status == TestStatus.FAILED)
    errors = sum(1 for r in results if r.status == TestStatus.ERROR)
    skipped = sum(1 for r in results if r.status == TestStatus.SKIPPED)

    total_duration = sum(r.duration for r in results)
    total_size = sum(r.content_size for r in results)

    print("\n" + "=" * 70)
    print("REGRESSION TEST SUMMARY / 回归测试摘要")
    print("=" * 70)
    print(f"Total Tests:    {total}")
    print(f"Passed:         {passed} ✓")
    print(f"Failed:         {failed} ✗")
    print(f"Errors:         {errors} ⚠")
    print(f"Skipped:        {skipped} ⊘")
    print(f"Total Duration: {total_duration:.2f}s")
    print(f"Total Data:     {total_size:,} bytes ({total_size / 1024:.1f} KB)")

    # Show failed tests
    # 显示失败的测试
    failed_results = [r for r in results if r.failed or r.status == TestStatus.ERROR]
    if failed_results:
        print("\n" + "-" * 70)
        print("FAILED TESTS / 失败的测试")
        print("-" * 70)
        for result in failed_results:
            print(f"\n✗ {result.test.description}")
            print(f"  URL: {result.test.url}")
            print(f"  Expected: {result.test.expected_strategy}")
            if result.strategy_used:
                print(f"  Used: {result.strategy_used}")
            if result.error_message:
                print(f"  Error: {result.error_message}")
            print(f"  Duration: {result.duration:.2f}s")

    print("\n" + "=" * 70)

    # Calculate success rate
    # 计算成功率
    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    # Simple test of the runner
    # 对运行器的简单测试
    import sys
    from url_suite_parser import parse_url_suite

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    suite_file = Path(__file__).parent.parent / 'url_suite.txt'

    try:
        tests = parse_url_suite(suite_file)
        print(f"Loaded {len(tests)} tests from suite")

        # Run a quick test with just the reference tests
        # 仅使用参考测试运行快速测试
        from url_suite_parser import filter_by_tags
        quick_tests = filter_by_tags(tests, include_tags={'reference', 'fast'})

        if quick_tests:
            print(f"\nRunning {len(quick_tests)} quick tests...\n")
            runner = RegressionRunner(timeout=30, skip_manual=True)
            results = runner.run_suite(quick_tests)
            print_summary(results)
        else:
            print("No quick tests found")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
