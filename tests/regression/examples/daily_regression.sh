#!/bin/bash
# Daily Regression Check Script
# 每日回归检查脚本
#
# Purpose: Run comprehensive regression tests daily and send notifications
# 目的：每天运行全面的回归测试并发送通知
#
# Usage: Add to crontab for daily execution
# 用法：添加到 crontab 以便每天执行
#   0 2 * * * /path/to/daily_regression.sh
#
# Requirements:
# - Python 3.7+
# - Web Fetcher dependencies installed
# - Optional: mail command for email notifications
# 要求：
# - Python 3.7+
# - 已安装 Web Fetcher 依赖
# - 可选：用于电子邮件通知的 mail 命令

set -euo pipefail

# Configuration
# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
REGRESSION_SCRIPT="$PROJECT_ROOT/scripts/run_regression_suite.py"
BASELINE_DIR="$PROJECT_ROOT/tests/regression/baselines"
REPORT_DIR="$PROJECT_ROOT/regression-reports"
DATE_STAMP=$(date +%Y%m%d)
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Email configuration (optional)
# 电子邮件配置（可选）
EMAIL_RECIPIENT="${REGRESSION_EMAIL:-}"
EMAIL_SUBJECT="Daily Regression Test Report - $DATE_STAMP"

# Logging
# 日志
LOG_FILE="$REPORT_DIR/daily-$DATE_STAMP.log"

# Create report directory
# 创建报告目录
mkdir -p "$REPORT_DIR"

# Function: Log message
# 函数：记录消息
log() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

# Function: Send email notification
# 函数：发送电子邮件通知
send_email() {
    local status=$1
    local report_file=$2

    if [ -n "$EMAIL_RECIPIENT" ] && command -v mail &> /dev/null; then
        if [ "$status" = "success" ]; then
            subject="✓ $EMAIL_SUBJECT - PASSED"
        else
            subject="✗ $EMAIL_SUBJECT - FAILED"
        fi

        mail -s "$subject" "$EMAIL_RECIPIENT" < "$report_file"
        log "Email sent to $EMAIL_RECIPIENT"
    fi
}

# Start
# 开始
log "=========================================="
log "Daily Regression Test Starting"
log "每日回归测试开始"
log "=========================================="

cd "$PROJECT_ROOT"

# Run regression tests
# 运行回归测试
log "Running regression tests..."
log "运行回归测试..."

REPORT_FILE="$REPORT_DIR/daily-$DATE_STAMP.md"
JSON_REPORT="$REPORT_DIR/daily-$DATE_STAMP.json"
EXIT_CODE=0

# Run with baseline comparison if main baseline exists
# 如果存在主基线，则使用基线比较运行
if [ -f "$BASELINE_DIR/main.json" ]; then
    log "Comparing against baseline: main.json"
    log "与基线比较：main.json"

    python "$REGRESSION_SCRIPT" \
        --exclude-tags manual,slow \
        --baseline baselines/main.json \
        --fail-on-regression \
        --report markdown \
        --output "$REPORT_FILE" \
        2>&1 | tee -a "$LOG_FILE" || EXIT_CODE=$?
else
    log "No baseline found, running without comparison"
    log "未找到基线，运行时不进行比较"

    python "$REGRESSION_SCRIPT" \
        --exclude-tags manual,slow \
        --report markdown \
        --output "$REPORT_FILE" \
        2>&1 | tee -a "$LOG_FILE" || EXIT_CODE=$?
fi

# Generate JSON report for programmatic processing
# 生成 JSON 报告以便程序处理
log "Generating JSON report..."
log "生成 JSON 报告..."

python "$REGRESSION_SCRIPT" \
    --exclude-tags manual,slow \
    --report json \
    --output "$JSON_REPORT" \
    2>&1 | tee -a "$LOG_FILE"

# Check results
# 检查结果
if [ $EXIT_CODE -eq 0 ]; then
    log "=========================================="
    log "✓ Daily regression tests PASSED"
    log "✓ 每日回归测试通过"
    log "=========================================="

    send_email "success" "$REPORT_FILE"
else
    log "=========================================="
    log "✗ Daily regression tests FAILED"
    log "✗ 每日回归测试失败"
    log "Exit code: $EXIT_CODE"
    log "=========================================="

    send_email "failure" "$REPORT_FILE"
fi

# Cleanup old reports (keep last 30 days)
# 清理旧报告（保留最近 30 天）
log "Cleaning up old reports..."
log "清理旧报告..."

find "$REPORT_DIR" -name "daily-*.md" -mtime +30 -delete
find "$REPORT_DIR" -name "daily-*.json" -mtime +30 -delete
find "$REPORT_DIR" -name "daily-*.log" -mtime +30 -delete

log "Reports saved to: $REPORT_DIR"
log "报告保存到：$REPORT_DIR"

# Summary statistics
# 摘要统计
if [ -f "$JSON_REPORT" ]; then
    log ""
    log "Summary from JSON report:"
    log "JSON 报告摘要："

    # Extract key metrics using Python
    # 使用 Python 提取关键指标
    python -c "
import json
with open('$JSON_REPORT') as f:
    data = json.load(f)
    summary = data.get('summary', {})
    print(f\"  Total Tests: {summary.get('total', 0)}\")
    print(f\"  Passed: {summary.get('passed', 0)}\")
    print(f\"  Failed: {summary.get('failed', 0)}\")
    print(f\"  Errors: {summary.get('errors', 0)}\")
    print(f\"  Success Rate: {summary.get('success_rate', 0):.1f}%\")
    print(f\"  Total Duration: {summary.get('total_duration', 0):.2f}s\")
" | tee -a "$LOG_FILE"
fi

log ""
log "Daily regression check complete"
log "每日回归检查完成"

exit $EXIT_CODE
