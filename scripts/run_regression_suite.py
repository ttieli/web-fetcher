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
    TestStatus,
    print_summary
)
from tests.regression.dual_method_runner import (
    DualMethodRunner,
    DualMethodResult,
    print_summary as print_dual_summary
)
from tests.regression.baseline_manager import BaselineManager, Baseline
from tests.regression.report_generator import ReportGenerator, write_report


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

    # Baseline management
    # 基线管理
    parser.add_argument(
        '--save-baseline',
        metavar='NAME',
        help='Save current run as baseline / 将当前运行保存为基线'
    )

    parser.add_argument(
        '--baseline',
        metavar='FILE',
        help='Compare against baseline / 与基线比较'
    )

    # Reporting
    # 报告
    parser.add_argument(
        '--report',
        choices=['markdown', 'json', 'text'],
        metavar='FORMAT',
        help='Output format: markdown|json|text (default: text) / 输出格式：markdown|json|text（默认：text）'
    )

    parser.add_argument(
        '--output',
        metavar='FILE',
        help='Write report to file (default: stdout) / 将报告写入文件（默认：标准输出）'
    )

    # Advanced filtering
    # 高级过滤
    parser.add_argument(
        '--strategy',
        choices=['urllib', 'selenium', 'auto'],
        metavar='TYPE',
        help='Filter by strategy: urllib|selenium|auto / 按策略过滤：urllib|selenium|auto'
    )

    parser.add_argument(
        '--min-duration',
        type=float,
        metavar='SEC',
        help='Only show tests taking > N seconds / 仅显示耗时 > N 秒的测试'
    )

    # CI/CD integration
    # CI/CD 集成
    parser.add_argument(
        '--fail-on-regression',
        action='store_true',
        help='Exit 1 if performance regression detected / 如果检测到性能回归，退出码为 1'
    )

    parser.add_argument(
        '--strict',
        action='store_true',
        help='Exit 1 on any warning / 任何警告时退出码为 1'
    )

    # Dual-method testing
    # 双方法测试
    parser.add_argument(
        '--dual-method',
        action='store_true',
        help='Enable dual-method testing (urllib + selenium) / 启用双方法测试（urllib + selenium）'
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

    # Initialize runner (dual-method or single-method)
    # 初始化运行器（双方法或单方法）
    if args.dual_method:
        runner = DualMethodRunner(
            timeout=args.timeout,
            skip_manual=not args.include_manual
        )
        print("Dual-method testing enabled (urllib + selenium)\n")
    else:
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
        if args.dual_method:
            test = URLTest(
                url=args.url,
                description="Ad-hoc URL test (dual-method)",
                expected_strategies=["urllib", "selenium"],
                tags=set(),
                line_number=0,
                compare_methods=True
            )
            result = runner.run_dual_method_test(test)

            # Print dual-method result
            print(f"URL: {args.url}\n")
            if result.urllib_result:
                status = "✓ PASSED" if result.urllib_result.passed else "✗ FAILED"
                print(f"urllib: {status}")
                print(f"  Duration: {result.urllib_result.duration:.2f}s")
                print(f"  Content Size: {result.urllib_result.content_size:,} bytes")
                if result.urllib_result.error_message:
                    print(f"  Error: {result.urllib_result.error_message}")
                print()

            if result.selenium_result:
                status = "✓ PASSED" if result.selenium_result.passed else "✗ FAILED"
                print(f"selenium: {status}")
                print(f"  Duration: {result.selenium_result.duration:.2f}s")
                print(f"  Content Size: {result.selenium_result.content_size:,} bytes")
                if result.selenium_result.error_message:
                    print(f"  Error: {result.selenium_result.error_message}")
                print()

            if result.comparison:
                print(f"Comparison:")
                print(f"  Difference Level: {result.comparison.difference_level.value}")
                print(f"  URL Classification: {result.comparison.url_classification.value}")
                print(f"  Size Difference: {result.comparison.size_diff_percent:.1f}%")
                print(f"  Speed Ratio: {result.comparison.speed_ratio:.2f}x")
                if result.comparison.notes:
                    print(f"  Notes: {', '.join(result.comparison.notes)}")

            sys.exit(0 if result.any_passed else 1)
        else:
            test = URLTest(
                url=args.url,
                description="Ad-hoc URL test",
                expected_strategies=["auto"],
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

    # Apply strategy filter if specified
    # 如果指定，应用策略过滤
    if args.strategy:
        results = [r for r in results if r.strategy_used == args.strategy]
        print(f"Filtered to {len(results)} tests using {args.strategy} strategy\n")

    # Apply duration filter if specified
    # 如果指定，应用持续时间过滤
    if args.min_duration is not None:
        results = [r for r in results if r.duration >= args.min_duration]
        print(f"Filtered to {len(results)} tests with duration >= {args.min_duration}s\n")

    # Load baseline if specified
    # 如果指定，加载基线
    baseline = None
    comparison = None
    baseline_manager = BaselineManager()

    if args.baseline:
        try:
            baseline = baseline_manager.load_baseline(args.baseline)
            comparison = baseline_manager.compare(baseline, results)
            print(f"Loaded baseline: {args.baseline}")
            print(f"Comparison: {comparison.summary}\n")
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            if args.strict:
                sys.exit(2)

    # Generate report
    # 生成报告
    report_generator = ReportGenerator(results, suite_file.name)

    if args.report:
        output_path = Path(args.output) if args.output else None

        if args.report == 'markdown':
            report = report_generator.generate_markdown(comparison=comparison)
            write_report(report, output_path)
        elif args.report == 'json':
            report = report_generator.generate_json(comparison=comparison)
            write_report(report, output_path)
        elif args.report == 'text':
            report = report_generator.generate_text(comparison=comparison)
            write_report(report, output_path)
    else:
        # Default: print summary to terminal
        # 默认：向终端打印摘要
        if args.dual_method:
            print_dual_summary(results)
        else:
            print_summary(results)

        # Show comparison if baseline provided
        # 如果提供基线，显示比较
        if comparison:
            print("\n" + "=" * 70)
            print("BASELINE COMPARISON / 基线对比")
            print("=" * 70)
            print(comparison.summary)

            if comparison.has_regressions:
                print("\nREGRESSIONS DETECTED / 检测到回归:")
                for reg in comparison.regressions[:5]:  # Show first 5
                    print(f"\n⚠ {reg['url']}")
                    for detail in reg['changes']['details']:
                        print(f"  {detail}")
                if len(comparison.regressions) > 5:
                    print(f"\n... and {len(comparison.regressions) - 5} more regressions")

    # Save baseline if specified
    # 如果指定，保存基线
    if args.save_baseline:
        saved_path = baseline_manager.save_baseline(
            name=args.save_baseline,
            results=results,
            suite_file=suite_file,
            metadata={
                'total_tests': len(results),
                'total_duration': total_duration
            }
        )
        print(f"\nBaseline saved to: {saved_path}")

    # Determine exit code
    # 确定退出代码
    if args.dual_method:
        # For dual-method, count tests where at least one method passed
        passed = sum(1 for r in results if r.any_passed)
        failed = sum(1 for r in results if r.both_failed)
    else:
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if r.failed or r.status == TestStatus.ERROR)

    # Check for regressions if --fail-on-regression
    # 如果 --fail-on-regression，检查回归
    if args.fail_on_regression and comparison and comparison.has_regressions:
        print("\nExiting with error: Performance regressions detected", file=sys.stderr)
        sys.exit(1)

    # Check for failures
    # 检查失败
    if failed > 0:
        sys.exit(1)

    # Check strict mode (any warnings)
    # 检查严格模式（任何警告）
    if args.strict and (failed > 0 or (comparison and comparison.has_regressions)):
        sys.exit(1)

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
