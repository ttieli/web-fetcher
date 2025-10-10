#!/bin/bash
# Phase 3 Feature Demonstration
# 阶段 3 功能演示
#
# This script demonstrates all Phase 3 features:
# 此脚本演示所有阶段 3 功能：
# - Baseline save/load
# - Report generation (markdown, JSON, text)
# - Baseline comparison
# - Regression detection
# - Advanced CLI options

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BASELINES_DIR="$PROJECT_ROOT/tests/regression/baselines"
OUTPUT_DIR="/tmp/regression_reports"

echo "============================================================"
echo "Phase 3 Feature Demonstration / 阶段 3 功能演示"
echo "============================================================"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

cd "$PROJECT_ROOT"

echo "1. Save Baseline / 保存基线"
echo "------------------------------------------------------------"
echo "Running tests and saving as baseline 'demo_v1'..."
python scripts/run_regression_suite.py \
    --tags fast,reference \
    --save-baseline demo_v1 \
    --timeout 30
echo ""

echo "2. List Available Baselines / 列出可用的基线"
echo "------------------------------------------------------------"
ls -lh "$BASELINES_DIR"/*.json 2>/dev/null || echo "No baselines found"
echo ""

echo "3. Generate Markdown Report / 生成 Markdown 报告"
echo "------------------------------------------------------------"
echo "Generating markdown report to $OUTPUT_DIR/report.md..."
python scripts/run_regression_suite.py \
    --tags fast,reference \
    --report markdown \
    --output "$OUTPUT_DIR/report.md"
echo ""

echo "4. Generate JSON Report / 生成 JSON 报告"
echo "------------------------------------------------------------"
echo "Generating JSON report to $OUTPUT_DIR/report.json..."
python scripts/run_regression_suite.py \
    --tags fast,reference \
    --report json \
    --output "$OUTPUT_DIR/report.json"
echo ""

echo "5. Compare Against Baseline / 与基线比较"
echo "------------------------------------------------------------"
echo "Running tests and comparing against demo_v1 baseline..."
python scripts/run_regression_suite.py \
    --tags fast,reference \
    --baseline demo_v1
echo ""

echo "6. Comparison Report (Markdown) / 比较报告（Markdown）"
echo "------------------------------------------------------------"
echo "Generating comparison report to $OUTPUT_DIR/comparison.md..."
python scripts/run_regression_suite.py \
    --tags fast,reference \
    --baseline demo_v1 \
    --report markdown \
    --output "$OUTPUT_DIR/comparison.md"
echo ""

echo "7. Filter by Strategy / 按策略过滤"
echo "------------------------------------------------------------"
echo "Showing only urllib strategy tests..."
python scripts/run_regression_suite.py \
    --tags fast,reference \
    --strategy urllib \
    --report text \
    --output "$OUTPUT_DIR/urllib_only.txt"
echo ""

echo "8. Filter by Duration / 按持续时间过滤"
echo "------------------------------------------------------------"
echo "Showing only tests taking > 5 seconds..."
python scripts/run_regression_suite.py \
    --tags fast,reference \
    --min-duration 5.0 \
    --report text \
    --output "$OUTPUT_DIR/slow_tests.txt"
echo ""

echo "============================================================"
echo "Phase 3 Demonstration Complete / 阶段 3 演示完成"
echo "============================================================"
echo ""
echo "Generated Files / 生成的文件:"
echo "------------------------------------------------------------"
ls -lh "$OUTPUT_DIR"/*.{md,json,txt} 2>/dev/null || echo "No reports found"
echo ""
echo "Baselines / 基线:"
echo "------------------------------------------------------------"
ls -lh "$BASELINES_DIR"/*.json 2>/dev/null || echo "No baselines found"
echo ""

echo "Sample Reports / 示例报告:"
echo "------------------------------------------------------------"
echo "Markdown Report Preview:"
head -30 "$OUTPUT_DIR/report.md" 2>/dev/null || echo "Report not found"
echo ""
echo "JSON Report Stats:"
jq '.summary, .performance' "$OUTPUT_DIR/report.json" 2>/dev/null || echo "Report not found"
echo ""

echo "To view comparison report: cat $OUTPUT_DIR/comparison.md"
echo "To view baseline data: cat $BASELINES_DIR/demo_v1.json"
echo ""
echo "Cleanup commands / 清理命令:"
echo "  rm -rf $OUTPUT_DIR"
echo "  rm $BASELINES_DIR/demo_v1.json"
