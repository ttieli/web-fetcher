#!/usr/bin/env python3
"""
Slack Notifier for Regression Tests
回归测试的 Slack 通知器

Send regression test results to Slack webhook.
将回归测试结果发送到 Slack webhook。

Usage:
    # Set Slack webhook URL as environment variable
    export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

    # Run regression tests and notify
    python scripts/run_regression_suite.py --report json --output report.json
    python examples/slack_notifier.py report.json

    # Or use directly in Python
    from examples.slack_notifier import send_slack_notification
    send_slack_notification(results, webhook_url)
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import urllib.request
import urllib.error

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.regression.regression_runner import TestResult


def build_slack_message(report_data: Dict[str, Any], webhook_url: str = None) -> Dict[str, Any]:
    """
    Build Slack message payload from report data.
    从报告数据构建 Slack 消息负载。

    Args:
        report_data: Report JSON data / 报告 JSON 数据
        webhook_url: Slack webhook URL (optional) / Slack webhook URL（可选）

    Returns:
        Slack message payload / Slack 消息负载
    """
    summary = report_data.get('summary', {})
    timestamp = report_data.get('timestamp', 'Unknown')
    suite_file = report_data.get('suite_file', 'Unknown')

    # Determine overall status
    success_rate = summary.get('success_rate', 0)
    if success_rate == 100:
        status_emoji = ':white_check_mark:'
        status_color = 'good'
        status_text = 'All Tests Passed / 所有测试通过'
    elif success_rate >= 90:
        status_emoji = ':large_orange_diamond:'
        status_color = 'warning'
        status_text = 'Most Tests Passed / 大部分测试通过'
    else:
        status_emoji = ':x:'
        status_color = 'danger'
        status_text = 'Tests Failed / 测试失败'

    # Build message
    message = {
        "text": f"{status_emoji} Regression Test Report",
        "attachments": [
            {
                "color": status_color,
                "title": "Regression Test Summary / 回归测试摘要",
                "fields": [
                    {
                        "title": "Status / 状态",
                        "value": status_text,
                        "short": True
                    },
                    {
                        "title": "Suite / 套件",
                        "value": suite_file,
                        "short": True
                    },
                    {
                        "title": "Total Tests / 总测试数",
                        "value": str(summary.get('total', 0)),
                        "short": True
                    },
                    {
                        "title": "Success Rate / 成功率",
                        "value": f"{success_rate:.1f}%",
                        "short": True
                    },
                    {
                        "title": "Passed / 通过",
                        "value": f":white_check_mark: {summary.get('passed', 0)}",
                        "short": True
                    },
                    {
                        "title": "Failed / 失败",
                        "value": f":x: {summary.get('failed', 0)}",
                        "short": True
                    },
                    {
                        "title": "Errors / 错误",
                        "value": f":warning: {summary.get('errors', 0)}",
                        "short": True
                    },
                    {
                        "title": "Duration / 持续时间",
                        "value": f"{summary.get('total_duration', 0):.1f}s",
                        "short": True
                    }
                ],
                "footer": "Web Fetcher Regression Tests",
                "ts": report_data.get('timestamp', '')
            }
        ]
    }

    # Add failed tests if any
    failed_results = [r for r in report_data.get('results', []) if r.get('status') != 'PASSED']
    if failed_results:
        failed_text = "\n".join([
            f"• {r.get('url', 'Unknown')[:60]} - {r.get('error_message', 'Unknown error')[:100]}"
            for r in failed_results[:5]  # Show first 5 failures
        ])

        if len(failed_results) > 5:
            failed_text += f"\n... and {len(failed_results) - 5} more failures"

        message['attachments'].append({
            "color": "danger",
            "title": "Failed Tests / 失败的测试",
            "text": failed_text,
            "mrkdwn_in": ["text"]
        })

    return message


def send_to_slack(message: Dict[str, Any], webhook_url: str) -> bool:
    """
    Send message to Slack webhook.
    将消息发送到 Slack webhook。

    Args:
        message: Slack message payload / Slack 消息负载
        webhook_url: Slack webhook URL

    Returns:
        True if successful / 成功返回 True
    """
    try:
        data = json.dumps(message).encode('utf-8')
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print("✓ Slack notification sent successfully")
                print("✓ Slack 通知发送成功")
                return True
            else:
                print(f"✗ Slack notification failed with status: {response.status}")
                print(f"✗ Slack 通知失败，状态码：{response.status}")
                return False

    except urllib.error.HTTPError as e:
        print(f"✗ HTTP Error sending to Slack: {e.code} - {e.reason}")
        print(f"✗ 发送到 Slack 时出现 HTTP 错误：{e.code} - {e.reason}")
        return False

    except urllib.error.URLError as e:
        print(f"✗ URL Error sending to Slack: {e.reason}")
        print(f"✗ 发送到 Slack 时出现 URL 错误：{e.reason}")
        return False

    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        print(f"✗ 意外错误：{e}")
        return False


def send_slack_notification(report_data: Dict[str, Any], webhook_url: str = None) -> bool:
    """
    Send regression test notification to Slack.
    向 Slack 发送回归测试通知。

    Args:
        report_data: Report JSON data or results / 报告 JSON 数据或结果
        webhook_url: Slack webhook URL (uses env var if not provided) / Slack webhook URL（如果未提供，使用环境变量）

    Returns:
        True if successful / 成功返回 True
    """
    # Get webhook URL from env if not provided
    if not webhook_url:
        webhook_url = os.environ.get('SLACK_WEBHOOK_URL')

    if not webhook_url:
        print("✗ Error: SLACK_WEBHOOK_URL not set")
        print("✗ 错误：未设置 SLACK_WEBHOOK_URL")
        print()
        print("Set it using:")
        print('export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"')
        return False

    # Build and send message
    message = build_slack_message(report_data, webhook_url)
    return send_to_slack(message, webhook_url)


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python slack_notifier.py <report.json> [webhook_url]")
        print("用法：python slack_notifier.py <report.json> [webhook_url]")
        print()
        print("Environment variables:")
        print("  SLACK_WEBHOOK_URL - Slack webhook URL")
        sys.exit(1)

    report_file = Path(sys.argv[1])
    webhook_url = sys.argv[2] if len(sys.argv) > 2 else None

    if not report_file.exists():
        print(f"✗ Error: Report file not found: {report_file}")
        print(f"✗ 错误：未找到报告文件：{report_file}")
        sys.exit(1)

    # Load report
    try:
        with open(report_file) as f:
            report_data = json.load(f)
    except Exception as e:
        print(f"✗ Error loading report file: {e}")
        print(f"✗ 加载报告文件时出错：{e}")
        sys.exit(1)

    # Send notification
    success = send_slack_notification(report_data, webhook_url)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
