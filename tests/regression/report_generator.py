#!/usr/bin/env python3
"""
Report Generator - Generate various formats of regression test reports
报告生成器 - 生成各种格式的回归测试报告

This module generates reports in markdown, JSON, and comparison formats.
本模块生成 markdown、JSON 和比较格式的报告。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, TextIO
import sys

from tests.regression.regression_runner import TestResult, TestStatus
from tests.regression.baseline_manager import Baseline, ComparisonResult, BaselineManager


class ReportGenerator:
    """
    Generate regression test reports in various formats.
    以各种格式生成回归测试报告。
    """

    def __init__(self, results: List[TestResult], suite_name: str = "url_suite.txt"):
        """
        Initialize report generator.
        初始化报告生成器。

        Args:
            results: Test results to report / 要报告的测试结果
            suite_name: Name of test suite / 测试套件名称
        """
        self.results = results
        self.suite_name = suite_name
        self.timestamp = datetime.now()

    def generate_markdown(
        self,
        output: Optional[TextIO] = None,
        comparison: Optional[ComparisonResult] = None
    ) -> str:
        """
        Generate markdown format report.
        生成 markdown 格式报告。

        Args:
            output: Output stream (default: None, returns string) / 输出流（默认：None，返回字符串）
            comparison: Optional comparison result / 可选的比较结果

        Returns:
            str: Markdown report / Markdown 报告
        """
        lines = []

        # Header
        # 标题
        lines.append("# Regression Test Report / 回归测试报告")
        lines.append("")
        lines.append(f"**Generated / 生成时间:** {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Suite / 测试套件:** {self.suite_name} ({len(self.results)} URLs)")
        lines.append("")

        # Summary statistics
        # 摘要统计
        lines.append("## Summary / 总结")
        lines.append("")
        lines.extend(self._generate_summary_table())
        lines.append("")

        # Performance section
        # 性能部分
        lines.append("## Performance / 性能")
        lines.append("")
        lines.extend(self._generate_performance_summary())
        lines.append("")

        # Comparison section (if provided)
        # 比较部分（如果提供）
        if comparison:
            lines.append("## Baseline Comparison / 基线对比")
            lines.append("")
            lines.extend(self._generate_comparison_section(comparison))
            lines.append("")

        # Failed tests
        # 失败的测试
        failed_results = [r for r in self.results if r.failed or r.status == TestStatus.ERROR]
        if failed_results:
            lines.append("## Failed Tests / 失败测试")
            lines.append("")
            lines.extend(self._generate_failed_tests_section(failed_results))
            lines.append("")

        # Tag breakdown
        # 标签分类
        lines.append("## Test Breakdown by Tags / 按标签分类测试")
        lines.append("")
        lines.extend(self._generate_tag_breakdown())
        lines.append("")

        report = "\n".join(lines)

        if output:
            output.write(report)

        return report

    def generate_json(
        self,
        output: Optional[TextIO] = None,
        comparison: Optional[ComparisonResult] = None
    ) -> str:
        """
        Generate JSON format report.
        生成 JSON 格式报告。

        Args:
            output: Output stream (default: None, returns string) / 输出流（默认：None，返回字符串）
            comparison: Optional comparison result / 可选的比较结果

        Returns:
            str: JSON report / JSON 报告
        """
        # Build report data structure
        # 构建报告数据结构
        report_data = {
            'metadata': {
                'generated_at': self.timestamp.isoformat(),
                'suite_name': self.suite_name,
                'total_tests': len(self.results)
            },
            'summary': self._calculate_summary_stats(),
            'performance': self._calculate_performance_stats(),
            'results': [self._result_to_json(r) for r in self.results]
        }

        # Add comparison if provided
        # 如果提供，添加比较
        if comparison:
            report_data['comparison'] = self._comparison_to_json(comparison)

        json_str = json.dumps(report_data, indent=2, ensure_ascii=False)

        if output:
            output.write(json_str)

        return json_str

    def generate_text(
        self,
        output: Optional[TextIO] = None,
        comparison: Optional[ComparisonResult] = None
    ) -> str:
        """
        Generate plain text format report.
        生成纯文本格式报告。

        Args:
            output: Output stream (default: None, returns string) / 输出流（默认：None，返回字符串）
            comparison: Optional comparison result / 可选的比较结果

        Returns:
            str: Text report / 文本报告
        """
        lines = []

        # Header
        # 标题
        lines.append("=" * 70)
        lines.append("REGRESSION TEST REPORT / 回归测试报告")
        lines.append("=" * 70)
        lines.append(f"Generated: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Suite: {self.suite_name} ({len(self.results)} URLs)")
        lines.append("")

        # Summary
        # 摘要
        stats = self._calculate_summary_stats()
        lines.append("SUMMARY / 总结")
        lines.append("-" * 70)
        lines.append(f"Total Tests:    {stats['total']}")
        lines.append(f"Passed:         {stats['passed']} ✓")
        lines.append(f"Failed:         {stats['failed']} ✗")
        lines.append(f"Errors:         {stats['errors']} ⚠")
        lines.append(f"Skipped:        {stats['skipped']} ⊘")
        lines.append(f"Success Rate:   {stats['success_rate']:.1f}%")
        lines.append("")

        # Performance
        # 性能
        perf_stats = self._calculate_performance_stats()
        lines.append("PERFORMANCE / 性能")
        lines.append("-" * 70)
        lines.append(f"Total Duration:     {perf_stats['total_duration']:.2f}s")
        lines.append(f"Average Duration:   {perf_stats['avg_duration']:.2f}s")
        lines.append(f"Fastest:            {perf_stats['fastest']['url'][:40]}... ({perf_stats['fastest']['duration']:.2f}s)")
        lines.append(f"Slowest:            {perf_stats['slowest']['url'][:40]}... ({perf_stats['slowest']['duration']:.2f}s)")
        lines.append(f"Total Content Size: {perf_stats['total_size']:,} bytes ({perf_stats['total_size']/1024:.1f} KB)")
        lines.append("")

        # Comparison
        # 比较
        if comparison:
            lines.append("BASELINE COMPARISON / 基线对比")
            lines.append("-" * 70)
            lines.append(comparison.summary)
            lines.append("")

            if comparison.has_regressions:
                lines.append("REGRESSIONS DETECTED / 检测到回归:")
                for reg in comparison.regressions:
                    lines.append(f"\n⚠ {reg['url']}")
                    for detail in reg['changes']['details']:
                        lines.append(f"  {detail}")
                lines.append("")

        # Failed tests
        # 失败的测试
        failed_results = [r for r in self.results if r.failed or r.status == TestStatus.ERROR]
        if failed_results:
            lines.append("FAILED TESTS / 失败测试")
            lines.append("-" * 70)
            for i, result in enumerate(failed_results, 1):
                lines.append(f"\n{i}. {result.test.url}")
                lines.append(f"   Status: {result.status.value.upper()}")
                if result.error_message:
                    lines.append(f"   Error: {result.error_message}")
                lines.append(f"   Duration: {result.duration:.2f}s")
            lines.append("")

        lines.append("=" * 70)

        report = "\n".join(lines)

        if output:
            output.write(report)

        return report

    def generate_comparison_report(
        self,
        baseline: Baseline,
        output: Optional[TextIO] = None
    ) -> str:
        """
        Generate detailed comparison report against baseline.
        生成与基线的详细比较报告。

        Args:
            baseline: Baseline to compare against / 要比较的基线
            output: Output stream / 输出流

        Returns:
            str: Comparison report / 比较报告
        """
        # Use baseline manager to compare
        # 使用基线管理器进行比较
        manager = BaselineManager()
        comparison = manager.compare(baseline, self.results)

        lines = []

        # Header
        # 标题
        lines.append("=" * 70)
        lines.append("BASELINE COMPARISON REPORT / 基线对比报告")
        lines.append("=" * 70)
        lines.append(f"Baseline: {baseline.timestamp}")
        lines.append(f"Current:  {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Summary
        # 摘要
        lines.append("SUMMARY / 摘要")
        lines.append("-" * 70)
        lines.append(comparison.summary)
        lines.append("")

        # Regressions
        # 回归
        if comparison.regressions:
            lines.append("REGRESSIONS DETECTED / 检测到回归")
            lines.append("-" * 70)
            for i, reg in enumerate(comparison.regressions, 1):
                lines.append(f"\n{i}. ⚠ {reg['url']}")
                for detail in reg['changes']['details']:
                    lines.append(f"   {detail}")
            lines.append("")

        # Improvements
        # 改进
        if comparison.improvements:
            lines.append("IMPROVEMENTS / 改进")
            lines.append("-" * 70)
            for i, imp in enumerate(comparison.improvements, 1):
                lines.append(f"\n{i}. ✓ {imp['url']}")
                for detail in imp['changes']['details']:
                    lines.append(f"   {detail}")
            lines.append("")

        # New tests
        # 新测试
        if comparison.new_tests:
            lines.append("NEW TESTS / 新测试")
            lines.append("-" * 70)
            for url in comparison.new_tests:
                lines.append(f"+ {url}")
            lines.append("")

        # Removed tests
        # 移除的测试
        if comparison.removed_tests:
            lines.append("REMOVED TESTS / 移除的测试")
            lines.append("-" * 70)
            for url in comparison.removed_tests:
                lines.append(f"- {url}")
            lines.append("")

        lines.append("=" * 70)

        report = "\n".join(lines)

        if output:
            output.write(report)

        return report

    def _generate_summary_table(self) -> List[str]:
        """Generate summary statistics table / 生成摘要统计表"""
        stats = self._calculate_summary_stats()

        lines = [
            "| Metric / 指标 | Value / 值 |",
            "|--------------|-----------|",
            f"| Total / 总数 | {stats['total']} |",
            f"| Passed / 通过 | {stats['passed']} |",
            f"| Failed / 失败 | {stats['failed']} |",
            f"| Error / 错误 | {stats['errors']} |",
            f"| Skipped / 跳过 | {stats['skipped']} |",
            f"| Success Rate / 成功率 | {stats['success_rate']:.1f}% |",
        ]

        return lines

    def _generate_performance_summary(self) -> List[str]:
        """Generate performance summary / 生成性能摘要"""
        perf_stats = self._calculate_performance_stats()

        lines = [
            f"- **Total Duration / 总耗时:** {perf_stats['total_duration']:.2f}s",
            f"- **Average Duration / 平均耗时:** {perf_stats['avg_duration']:.2f}s",
            f"- **Fastest / 最快:** {perf_stats['fastest']['url']} ({perf_stats['fastest']['duration']:.2f}s)",
            f"- **Slowest / 最慢:** {perf_stats['slowest']['url']} ({perf_stats['slowest']['duration']:.2f}s)",
            f"- **Total Content / 总内容:** {perf_stats['total_size']:,} bytes ({perf_stats['total_size']/1024:.1f} KB)",
        ]

        return lines

    def _generate_comparison_section(self, comparison: ComparisonResult) -> List[str]:
        """Generate comparison section / 生成比较部分"""
        lines = [
            f"**{comparison.summary}**",
            ""
        ]

        if comparison.has_regressions:
            lines.append("### Regressions / 回归")
            lines.append("")
            for i, reg in enumerate(comparison.regressions, 1):
                lines.append(f"{i}. ⚠ **{reg['url']}**")
                for detail in reg['changes']['details']:
                    lines.append(f"   - {detail}")
                lines.append("")

        if comparison.improvements:
            lines.append("### Improvements / 改进")
            lines.append("")
            for i, imp in enumerate(comparison.improvements, 1):
                lines.append(f"{i}. ✓ **{imp['url']}**")
                for detail in imp['changes']['details']:
                    lines.append(f"   - {detail}")
                lines.append("")

        return lines

    def _generate_failed_tests_section(self, failed_results: List[TestResult]) -> List[str]:
        """Generate failed tests section / 生成失败测试部分"""
        lines = []

        for i, result in enumerate(failed_results, 1):
            lines.append(f"{i}. **{result.test.url}**")
            lines.append(f"   - **Status:** {result.status.value.upper()}")
            if result.error_message:
                lines.append(f"   - **Error:** {result.error_message}")
            lines.append(f"   - **Duration:** {result.duration:.2f}s")
            if result.test.expected_strategy:
                lines.append(f"   - **Expected Strategy:** {result.test.expected_strategy}")
            if result.strategy_used:
                lines.append(f"   - **Strategy Used:** {result.strategy_used}")
            lines.append("")

        return lines

    def _generate_tag_breakdown(self) -> List[str]:
        """Generate tag breakdown section / 生成标签分类部分"""
        # Collect tag statistics
        # 收集标签统计
        tag_stats = {}
        for result in self.results:
            for tag in result.test.tags:
                if tag not in tag_stats:
                    tag_stats[tag] = {'total': 0, 'passed': 0}
                tag_stats[tag]['total'] += 1
                if result.passed:
                    tag_stats[tag]['passed'] += 1

        if not tag_stats:
            return ["No tags found / 未找到标签"]

        lines = [
            "| Tag / 标签 | Total / 总数 | Passed / 通过 | Success Rate / 成功率 |",
            "|----------|------------|--------------|---------------------|",
        ]

        for tag in sorted(tag_stats.keys()):
            stats = tag_stats[tag]
            success_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            lines.append(
                f"| {tag} | {stats['total']} | {stats['passed']} | {success_rate:.1f}% |"
            )

        return lines

    def _calculate_summary_stats(self) -> dict:
        """Calculate summary statistics / 计算摘要统计"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)

        success_rate = (passed / total * 100) if total > 0 else 0

        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'skipped': skipped,
            'success_rate': success_rate
        }

    def _calculate_performance_stats(self) -> dict:
        """Calculate performance statistics / 计算性能统计"""
        # Exclude skipped tests
        # 排除跳过的测试
        active_results = [r for r in self.results if r.status != TestStatus.SKIPPED]

        total_duration = sum(r.duration for r in active_results)
        total_size = sum(r.content_size for r in active_results)
        avg_duration = total_duration / len(active_results) if active_results else 0

        fastest = min(active_results, key=lambda r: r.duration) if active_results else None
        slowest = max(active_results, key=lambda r: r.duration) if active_results else None

        return {
            'total_duration': total_duration,
            'avg_duration': avg_duration,
            'total_size': total_size,
            'fastest': {
                'url': fastest.test.url if fastest else 'N/A',
                'duration': fastest.duration if fastest else 0
            },
            'slowest': {
                'url': slowest.test.url if slowest else 'N/A',
                'duration': slowest.duration if slowest else 0
            }
        }

    def _result_to_json(self, result: TestResult) -> dict:
        """Convert TestResult to JSON-serializable dict / 将 TestResult 转换为 JSON 可序列化字典"""
        return {
            'url': result.test.url,
            'description': result.test.description,
            'status': result.status.value,
            'duration': result.duration,
            'content_size': result.content_size,
            'strategy_used': result.strategy_used,
            'error_message': result.error_message,
            'tags': list(result.test.tags),
            'expected_strategy': result.test.expected_strategy
        }

    def _comparison_to_json(self, comparison: ComparisonResult) -> dict:
        """Convert ComparisonResult to JSON-serializable dict / 将 ComparisonResult 转换为 JSON 可序列化字典"""
        return {
            'summary': comparison.summary,
            'has_regressions': comparison.has_regressions,
            'regressions': comparison.regressions,
            'improvements': comparison.improvements,
            'new_tests': comparison.new_tests,
            'removed_tests': comparison.removed_tests,
            'unchanged_count': len(comparison.unchanged)
        }


def write_report(
    report_content: str,
    output_path: Optional[Path] = None
) -> None:
    """
    Write report to file or stdout.
    将报告写入文件或标准输出。

    Args:
        report_content: Report content to write / 要写入的报告内容
        output_path: Output file path (None = stdout) / 输出文件路径（None = 标准输出）
    """
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"Report written to: {output_path}")
    else:
        print(report_content)
