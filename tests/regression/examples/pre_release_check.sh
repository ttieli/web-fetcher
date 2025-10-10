#!/bin/bash
# Pre-Release Regression Check Script
# 发布前回归检查脚本
#
# Purpose: Comprehensive regression testing before releasing a new version
# 目的：在发布新版本之前进行全面的回归测试
#
# Usage: Run manually before each release
# 用法：在每次发布前手动运行
#   ./pre_release_check.sh <version>
#   Example: ./pre_release_check.sh v1.2.0
#
# Requirements:
# - Python 3.7+
# - Web Fetcher dependencies installed
# - Clean git working directory (no uncommitted changes)
# 要求：
# - Python 3.7+
# - 已安装 Web Fetcher 依赖
# - 干净的 git 工作目录（无未提交的更改）

set -euo pipefail

# Configuration
# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
REGRESSION_SCRIPT="$PROJECT_ROOT/scripts/run_regression_suite.py"
BASELINE_DIR="$PROJECT_ROOT/tests/regression/baselines"
REPORT_DIR="$PROJECT_ROOT/release-reports"

# Check arguments
# 检查参数
if [ $# -lt 1 ]; then
    echo "Usage: $0 <version>"
    echo "用法：$0 <版本>"
    echo "Example: $0 v1.2.0"
    exit 1
fi

VERSION="$1"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
DATE_STAMP=$(date +%Y%m%d-%H%M%S)

# Create report directory
# 创建报告目录
mkdir -p "$REPORT_DIR"

# Colors for output
# 输出颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function: Print colored message
# 函数：打印彩色消息
print_status() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

# Function: Check preconditions
# 函数：检查前提条件
check_preconditions() {
    print_status "$BLUE" "=========================================="
    print_status "$BLUE" "Pre-Release Regression Check"
    print_status "$BLUE" "发布前回归检查"
    print_status "$BLUE" "Version / 版本: $VERSION"
    print_status "$BLUE" "=========================================="
    echo ""

    # Check if git working directory is clean
    # 检查 git 工作目录是否干净
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        print_status "$RED" "✗ Error: Git working directory has uncommitted changes"
        print_status "$RED" "✗ 错误：Git 工作目录有未提交的更改"
        echo ""
        git status --short
        exit 1
    fi
    print_status "$GREEN" "✓ Git working directory is clean"
    print_status "$GREEN" "✓ Git 工作目录干净"

    # Check Python version
    # 检查 Python 版本
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    print_status "$GREEN" "✓ Python version: $PYTHON_VERSION"

    # Check if dependencies are installed
    # 检查是否安装了依赖项
    if ! python -c "import requests" 2>/dev/null; then
        print_status "$RED" "✗ Error: Required dependencies not installed"
        print_status "$RED" "✗ 错误：未安装必需的依赖项"
        echo "Run: pip install -r requirements.txt"
        exit 1
    fi
    print_status "$GREEN" "✓ Dependencies installed"
    print_status "$GREEN" "✓ 依赖项已安装"

    echo ""
}

# Function: Run test suite
# 函数：运行测试套件
run_test_suite() {
    local suite_name=$1
    local tags=$2
    local description=$3

    print_status "$YELLOW" "Running $suite_name..."
    print_status "$YELLOW" "运行 $suite_name..."
    echo "  $description"
    echo ""

    local report_file="$REPORT_DIR/${VERSION}-${suite_name}-${DATE_STAMP}.md"
    local exit_code=0

    if python "$REGRESSION_SCRIPT" \
        --tags "$tags" \
        --report markdown \
        --output "$report_file" 2>&1; then
        print_status "$GREEN" "✓ $suite_name PASSED"
        print_status "$GREEN" "✓ $suite_name 通过"
    else
        exit_code=$?
        print_status "$RED" "✗ $suite_name FAILED"
        print_status "$RED" "✗ $suite_name 失败"
        return $exit_code
    fi

    echo ""
    return 0
}

# Main execution
# 主执行
cd "$PROJECT_ROOT"

check_preconditions

ALL_PASSED=true

# Step 1: Fast smoke test
# 步骤 1：快速冒烟测试
print_status "$BLUE" "Step 1/5: Fast Smoke Test"
print_status "$BLUE" "步骤 1/5：快速冒烟测试"
echo ""

if ! run_test_suite "smoke" "fast,reference" "Quick validation of core functionality"; then
    print_status "$RED" "Smoke test failed. Aborting."
    print_status "$RED" "冒烟测试失败。中止。"
    exit 1
fi

# Step 2: Platform-specific tests
# 步骤 2：平台特定测试
print_status "$BLUE" "Step 2/5: Platform-Specific Tests"
print_status "$BLUE" "步骤 2/5：平台特定测试"
echo ""

if ! run_test_suite "wechat" "wechat" "WeChat parser validation / 微信解析器验证"; then
    ALL_PASSED=false
fi

if ! run_test_suite "xhs" "xhs" "XiaoHongShu parser validation / 小红书解析器验证"; then
    ALL_PASSED=false
fi

# Step 3: Full regression with baseline
# 步骤 3：完整回归测试（带基线）
print_status "$BLUE" "Step 3/5: Full Regression Test"
print_status "$BLUE" "步骤 3/5：完整回归测试"
echo ""

FULL_REPORT="$REPORT_DIR/${VERSION}-full-regression-${DATE_STAMP}.md"
JSON_REPORT="$REPORT_DIR/${VERSION}-full-regression-${DATE_STAMP}.json"

if [ -f "$BASELINE_DIR/main.json" ]; then
    print_status "$YELLOW" "Comparing against main baseline..."
    print_status "$YELLOW" "与主基线比较..."

    if ! python "$REGRESSION_SCRIPT" \
        --exclude-tags manual \
        --baseline baselines/main.json \
        --fail-on-regression \
        --report markdown \
        --output "$FULL_REPORT" 2>&1; then
        ALL_PASSED=false
        print_status "$RED" "✗ Regression detected compared to baseline"
        print_status "$RED" "✗ 与基线相比检测到回归"
    else
        print_status "$GREEN" "✓ No regression detected"
        print_status "$GREEN" "✓ 未检测到回归"
    fi
else
    print_status "$YELLOW" "No baseline found, running full test suite..."
    print_status "$YELLOW" "未找到基线，运行完整测试套件..."

    python "$REGRESSION_SCRIPT" \
        --exclude-tags manual \
        --report markdown \
        --output "$FULL_REPORT" 2>&1
fi

echo ""

# Step 4: Generate comprehensive JSON report
# 步骤 4：生成综合 JSON 报告
print_status "$BLUE" "Step 4/5: Generating Comprehensive Report"
print_status "$BLUE" "步骤 4/5：生成综合报告"
echo ""

python "$REGRESSION_SCRIPT" \
    --exclude-tags manual \
    --report json \
    --output "$JSON_REPORT"

print_status "$GREEN" "✓ JSON report generated"
print_status "$GREEN" "✓ JSON 报告已生成"
echo ""

# Step 5: Save new baseline for this version
# 步骤 5：为此版本保存新基线
print_status "$BLUE" "Step 5/5: Saving Baseline"
print_status "$BLUE" "步骤 5/5：保存基线"
echo ""

python "$REGRESSION_SCRIPT" \
    --exclude-tags manual \
    --save-baseline "$VERSION"

print_status "$GREEN" "✓ Baseline saved: $VERSION"
print_status "$GREEN" "✓ 基线已保存：$VERSION"
echo ""

# Summary
# 摘要
print_status "$BLUE" "=========================================="
print_status "$BLUE" "Pre-Release Check Summary"
print_status "$BLUE" "发布前检查摘要"
print_status "$BLUE" "=========================================="
echo ""

# Extract and display key metrics
# 提取并显示关键指标
if [ -f "$JSON_REPORT" ]; then
    python -c "
import json
with open('$JSON_REPORT') as f:
    data = json.load(f)
    summary = data.get('summary', {})
    print(f\"Total Tests: {summary.get('total', 0)}\")
    print(f\"Passed: {summary.get('passed', 0)} ✓\")
    print(f\"Failed: {summary.get('failed', 0)} ✗\")
    print(f\"Errors: {summary.get('errors', 0)} ⚠\")
    print(f\"Success Rate: {summary.get('success_rate', 0):.1f}%\")
    print(f\"Total Duration: {summary.get('total_duration', 0):.2f}s\")
"
fi

echo ""
print_status "$BLUE" "Reports Location / 报告位置:"
echo "  $REPORT_DIR"
echo ""

# Final result
# 最终结果
if [ "$ALL_PASSED" = true ]; then
    print_status "$GREEN" "=========================================="
    print_status "$GREEN" "✓ ALL CHECKS PASSED"
    print_status "$GREEN" "✓ 所有检查通过"
    print_status "$GREEN" "=========================================="
    print_status "$GREEN" ""
    print_status "$GREEN" "Ready for release $VERSION"
    print_status "$GREEN" "准备发布 $VERSION"
    exit 0
else
    print_status "$RED" "=========================================="
    print_status "$RED" "✗ SOME CHECKS FAILED"
    print_status "$RED" "✗ 某些检查失败"
    print_status "$RED" "=========================================="
    print_status "$RED" ""
    print_status "$RED" "Please review the reports before releasing"
    print_status "$RED" "请在发布前查看报告"
    exit 1
fi
