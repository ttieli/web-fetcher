#!/usr/bin/env python3
"""
Regression Test Suite Runner - CLI Entry Point
回归测试套件运行器 - CLI 入口点

Execute regression tests against the curated URL suite.
对精选 URL 套件执行回归测试。

Usage / 用法:
    # Run all tests (excluding manual)
    # 运行所有测试（不包括手动）
    python scripts/run_regression_suite.py

    # Run only fast tests
    # 仅运行快速测试
    python scripts/run_regression_suite.py --tags fast

    # Run WeChat tests
    # 运行微信测试
    python scripts/run_regression_suite.py --tags wechat

    # Exclude slow tests
    # 排除慢速测试
    python scripts/run_regression_suite.py --exclude-tags slow

    # Test a single URL
    # 测试单个 URL
    python scripts/run_regression_suite.py --url https://example.com

    # Verbose output
    # 详细输出
    python scripts/run_regression_suite.py --verbose --tags fast
"""

import argparse
import logging
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
# 将父目录添加到路径以进行导入
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.regression.url_suite_parser import (
    parse_url_suite,
    filter_by_tags,
    URLTest
)
from tests.regression.regression_runner import (
    RegressionRunner,
    TestResult,
    print_summary
)


def setup_logging(verbose: bool = False):
    """
    Configure logging based on verbosity level.
    根据详细程度配置日志记录。

    Args:
        verbose: Enable verbose logging / 启用详细日志
    """
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )


def print_progress(current: int, total: int, test: URLTest):
    """
    Print progress indicator during test execution.
    在测试执行期间打印进度指示器。

    Args:
        current: Current test number / 当前测试编号
        total: Total number of tests / 测试总数
        test: Current test being executed / 正在执行的当前测试
    """
    print(f"[{current}/{total}] Testing: {test.description[:50]}...", end='\r')


def main():
    """Main CLI entry point / 主 CLI 入口点"""
    parser = argparse.ArgumentParser(
        description='Run regression tests for Web Fetcher / 为 Web Fetcher 运行回归测试',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples / 示例:
  %(prog)s                              # Run all non-manual tests
  %(prog)s --tags fast                  # Run only fast tests
  %(prog)s --tags wechat,xhs            # Run WeChat and XHS tests
  %(prog)s --exclude-tags slow,manual   # Exclude slow and manual tests
  %(prog)s --url https://example.com    # Test single URL
  %(prog)s --verbose                    # Verbose logging
        """
    )

    parser.add_argument(
        '--tags',
        metavar='TAG',
        help='Run only tests with ANY of these tags (comma-separated) / 仅运行具有这些标签的测试（逗号分隔）'
    )

    parser.add_argument(
        '--exclude-tags',
        metavar='TAG',
        help='Exclude tests with ANY of these tags (comma-separated) / 排除具有这些标签的测试（逗号分隔）'
    )

    parser.add_argument(
        '--url',
        metavar='URL',
        help='Test a single URL (not in suite) / 测试单个 URL（不在套件中）'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        metavar='SEC',
        help='Timeout per URL in seconds (default: 30) / 每个 URL 的超时时间（秒）（默认：30）'
    )

    parser.add_argument(
        '--include-manual',
        action='store_true',
        help='Include manual tests (normally skipped) / 包含手动测试（通常跳过）'
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging / 启用详细日志'
    )

    parser.add_argument(
        '--suite-file',
        metavar='PATH',
        default=None,
        help='Path to url_suite.txt (default: tests/url_suite.txt) / url_suite.txt 的路径（默认：tests/url_suite.txt）'
    )

    args = parser.parse_args()

    # Setup logging
    # 设置日志
    setup_logging(args.verbose)

    # Determine suite file path
    # 确定套件文件路径
    if args.suite_file:
        suite_file = Path(args.suite_file)
    else:
        suite_file = Path(__file__).parent.parent / 'tests' / 'url_suite.txt'

    # Initialize runner
    # 初始化运行器
    runner = RegressionRunner(
        timeout=args.timeout,
        skip_manual=not args.include_manual
    )

    # Handle single URL mode
    # 处理单个 URL 模式
    if args.url:
        print(f"Testing single URL: {args.url}\n")

        # Create ad-hoc test
        # 创建临时测试
        test = URLTest(
            url=args.url,
            description="Ad-hoc URL test",
            expected_strategy="auto",
            tags=set(),
            line_number=0
        )

        result = runner.run_test(test)

        # Print result
        # 打印结果
        if result.passed:
            print(f"✓ PASSED: {args.url}")
            print(f"  Duration: {result.duration:.2f}s")
            print(f"  Content Size: {result.content_size:,} bytes")
            if result.strategy_used:
                print(f"  Strategy Used: {result.strategy_used}")
            sys.exit(0)
        else:
            print(f"✗ FAILED: {args.url}")
            print(f"  Duration: {result.duration:.2f}s")
            if result.error_message:
                print(f"  Error: {result.error_message}")
            sys.exit(1)

    # Load test suite
    # 加载测试套件
    try:
        tests = parse_url_suite(suite_file)
        print(f"Loaded {len(tests)} tests from {suite_file.name}")
    except FileNotFoundError:
        print(f"Error: Suite file not found: {suite_file}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error loading suite file: {e}", file=sys.stderr)
        sys.exit(2)

    # Apply tag filters
    # 应用标签过滤
    include_tags = None
    if args.tags:
        include_tags = {tag.strip() for tag in args.tags.split(',')}
        print(f"Include tags: {', '.join(sorted(include_tags))}")

    exclude_tags = None
    if args.exclude_tags:
        exclude_tags = {tag.strip() for tag in args.exclude_tags.split(',')}
        print(f"Exclude tags: {', '.join(sorted(exclude_tags))}")

    # Add 'manual' to exclude tags by default unless explicitly included
    # 默认将 'manual' 添加到排除标签，除非明确包含
    if not args.include_manual:
        if exclude_tags is None:
            exclude_tags = {'manual'}
        else:
            exclude_tags.add('manual')

    filtered_tests = filter_by_tags(tests, include_tags, exclude_tags)

    if not filtered_tests:
        print("\nNo tests match the specified filters.", file=sys.stderr)
        sys.exit(2)

    print(f"Running {len(filtered_tests)} tests...\n")

    # Run tests
    # 运行测试
    start_time = time.time()

    results = runner.run_suite(
        filtered_tests,
        progress_callback=print_progress
    )

    total_duration = time.time() - start_time

    # Clear progress line
    # 清除进度行
    print(" " * 80 + "\r", end='')

    # Print summary
    # 打印摘要
    print_summary(results)

    # Determine exit code
    # 确定退出代码
    # Exit code 0: all passed
    # 退出代码 0：全部通过
    # Exit code 1: any failures
    # 退出代码 1：任何失败
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if r.failed or r.status.value == 'error')

    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...", file=sys.stderr)
        sys.exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        print(f"\nFatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(2)
