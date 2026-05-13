#!/usr/bin/env python3
"""
Custom Report Template Example
自定义报告模板示例

This demonstrates how to create custom report formats by extending ReportGenerator.
演示如何通过扩展 ReportGenerator 创建自定义报告格式。

Usage:
    from examples.custom_report_template import CustomHTMLReporter
    reporter = CustomHTMLReporter(results, 'url_suite.txt')
    html = reporter.generate_html()
"""

import sys
from pathlib import Path
from typing import List
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.regression.report_generator import ReportGenerator
from tests.regression.regression_runner import TestResult, TestStatus


class CustomHTMLReporter(ReportGenerator):
    """
    Custom HTML report generator with enhanced styling.
    自定义 HTML 报告生成器，具有增强的样式。
    """

    def generate_html(self) -> str:
        """
        Generate HTML report with interactive elements.
        生成带有交互元素的 HTML 报告。
        """
        html = []

        # HTML header with CSS
        html.append(self._html_header())

        # Summary section
        html.append(self._html_summary())

        # Results table
        html.append(self._html_results_table())

        # Charts (using Chart.js placeholders)
        html.append(self._html_charts())

        # Footer
        html.append(self._html_footer())

        return '\n'.join(html)

    def _html_header(self) -> str:
        """Generate HTML header with CSS"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Regression Test Report</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }
        .header h1 { margin-bottom: 10px; }
        .header p { opacity: 0.9; }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f9f9f9;
        }
        .metric {
            background: white;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .metric-label {
            color: #666;
            margin-top: 5px;
        }
        .content { padding: 30px; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        th {
            background: #f5f5f5;
            font-weight: 600;
            color: #333;
        }
        tr:hover { background: #f9f9f9; }
        .status {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .status-passed {
            background: #d4edda;
            color: #155724;
        }
        .status-failed {
            background: #f8d7da;
            color: #721c24;
        }
        .status-error {
            background: #fff3cd;
            color: #856404;
        }
        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            border-top: 1px solid #e0e0e0;
        }
        .url-cell {
            max-width: 400px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
    </style>
</head>
<body>
    <div class="container">
"""

    def _html_summary(self) -> str:
        """Generate summary section"""
        summary = self.get_summary()

        return f"""
        <div class="header">
            <h1>🧪 Regression Test Report</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Suite: {self.suite_file}</p>
        </div>

        <div class="summary">
            <div class="metric">
                <div class="metric-value">{summary['total']}</div>
                <div class="metric-label">Total Tests</div>
            </div>
            <div class="metric">
                <div class="metric-value" style="color: #28a745;">{summary['passed']}</div>
                <div class="metric-label">✓ Passed</div>
            </div>
            <div class="metric">
                <div class="metric-value" style="color: #dc3545;">{summary['failed']}</div>
                <div class="metric-label">✗ Failed</div>
            </div>
            <div class="metric">
                <div class="metric-value" style="color: #ffc107;">{summary['errors']}</div>
                <div class="metric-label">⚠ Errors</div>
            </div>
            <div class="metric">
                <div class="metric-value">{summary['success_rate']:.1f}%</div>
                <div class="metric-label">Success Rate</div>
            </div>
            <div class="metric">
                <div class="metric-value">{summary['total_duration']:.1f}s</div>
                <div class="metric-label">Total Duration</div>
            </div>
        </div>
"""

    def _html_results_table(self) -> str:
        """Generate results table"""
        html = ['<div class="content">']
        html.append('<h2>Test Results</h2>')
        html.append('<table>')
        html.append('<thead><tr>')
        html.append('<th>Status</th>')
        html.append('<th>URL</th>')
        html.append('<th>Duration</th>')
        html.append('<th>Size</th>')
        html.append('<th>Strategy</th>')
        html.append('</tr></thead>')
        html.append('<tbody>')

        for result in self.results:
            status_class = 'passed' if result.passed else ('failed' if result.status == TestStatus.FAILED else 'error')
            status_text = '✓ PASSED' if result.passed else ('✗ FAILED' if result.status == TestStatus.FAILED else '⚠ ERROR')

            html.append('<tr>')
            html.append(f'<td><span class="status status-{status_class}">{status_text}</span></td>')
            html.append(f'<td class="url-cell" title="{result.test.url}">{result.test.url}</td>')
            html.append(f'<td>{result.duration:.2f}s</td>')
            html.append(f'<td>{self._format_size(result.content_size)}</td>')
            html.append(f'<td>{result.strategy_used or "N/A"}</td>')
            html.append('</tr>')

        html.append('</tbody></table>')
        html.append('</div>')

        return '\n'.join(html)

    def _html_charts(self) -> str:
        """Generate charts section (placeholder for Chart.js)"""
        return """
        <div class="content">
            <h2>Performance Charts</h2>
            <p>Charts can be added using Chart.js or similar libraries.</p>
        </div>
"""

    def _html_footer(self) -> str:
        """Generate footer"""
        return """
        <div class="footer">
            <p>Generated by Web Fetcher Regression Test Harness</p>
            <p>由 Web Fetcher 回归测试工具生成</p>
        </div>
    </div>
</body>
</html>
"""

    def _format_size(self, size_bytes: int) -> str:
        """Format byte size for display"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"


class CustomCSVReporter(ReportGenerator):
    """
    CSV report generator for spreadsheet import.
    CSV 报告生成器，用于电子表格导入。
    """

    def generate_csv(self) -> str:
        """Generate CSV report"""
        csv_lines = []

        # Header
        csv_lines.append("URL,Description,Status,Duration,Content Size,Strategy,Error")

        # Data rows
        for result in self.results:
            status = "PASSED" if result.passed else ("FAILED" if result.status == TestStatus.FAILED else "ERROR")
            error = (result.error_message or "").replace('"', '""')  # Escape quotes

            csv_lines.append(
                f'"{result.test.url}",'
                f'"{result.test.description}",'
                f'{status},'
                f'{result.duration:.2f},'
                f'{result.content_size},'
                f'{result.strategy_used or ""},'
                f'"{error}"'
            )

        return '\n'.join(csv_lines)


# Example usage
if __name__ == '__main__':
    print("Custom Report Template Examples")
    print("自定义报告模板示例")
    print()
    print("Usage:")
    print("------")
    print("from examples.custom_report_template import CustomHTMLReporter")
    print("reporter = CustomHTMLReporter(results, 'url_suite.txt')")
    print("html = reporter.generate_html()")
    print()
    print("Or for CSV:")
    print("from examples.custom_report_template import CustomCSVReporter")
    print("reporter = CustomCSVReporter(results, 'url_suite.txt')")
    print("csv = reporter.generate_csv()")
