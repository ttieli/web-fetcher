#!/bin/bash
# Compare Regression Baselines Script
# 比较回归基线脚本
#
# Purpose: Compare two baseline versions to identify performance changes
# 目的：比较两个基线版本以识别性能变化
#
# Usage: ./compare_versions.sh <baseline1> <baseline2>
# 用法：./compare_versions.sh <基线1> <基线2>
#   Example: ./compare_versions.sh v1.0 v1.1
#   示例：./compare_versions.sh v1.0 v1.1
#
# Requirements:
# - Python 3.7+
# - jq (for JSON processing)
# 要求：
# - Python 3.7+
# - jq（用于 JSON 处理）

set -euo pipefail

# Configuration
# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BASELINE_DIR="$PROJECT_ROOT/tests/regression/baselines"

# Check arguments
# 检查参数
if [ $# -lt 2 ]; then
    echo "Usage: $0 <baseline1> <baseline2>"
    echo "用法：$0 <基线1> <基线2>"
    echo ""
    echo "Available baselines / 可用的基线:"
    ls -1 "$BASELINE_DIR"/*.json 2>/dev/null | xargs -n1 basename | sed 's/.json$//' || echo "  (none)"
    exit 1
fi

BASELINE1="$1"
BASELINE2="$2"

# Resolve baseline paths
# 解析基线路径
if [ -f "$BASELINE1" ]; then
    BASELINE1_FILE="$BASELINE1"
elif [ -f "$BASELINE_DIR/$BASELINE1.json" ]; then
    BASELINE1_FILE="$BASELINE_DIR/$BASELINE1.json"
else
    echo "Error: Baseline not found: $BASELINE1"
    echo "错误：未找到基线：$BASELINE1"
    exit 1
fi

if [ -f "$BASELINE2" ]; then
    BASELINE2_FILE="$BASELINE2"
elif [ -f "$BASELINE_DIR/$BASELINE2.json" ]; then
    BASELINE2_FILE="$BASELINE_DIR/$BASELINE2.json"
else
    echo "Error: Baseline not found: $BASELINE2"
    echo "错误：未找到基线：$BASELINE2"
    exit 1
fi

# Check if jq is available
# 检查 jq 是否可用
if ! command -v jq &> /dev/null; then
    echo "Warning: jq not found. Using Python for JSON processing."
    echo "警告：未找到 jq。使用 Python 处理 JSON。"
    USE_PYTHON=true
else
    USE_PYTHON=false
fi

# Colors
# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Print header
# 打印标题
echo -e "${BLUE}=========================================="
echo "Baseline Comparison / 基线比较"
echo "=========================================="
echo ""
echo "Baseline 1: $(basename "$BASELINE1_FILE")"
echo "Baseline 2: $(basename "$BASELINE2_FILE")"
echo -e "==========================================${NC}"
echo ""

# Compare baselines using Python
# 使用 Python 比较基线
python3 << 'EOF'
import json
import sys
import os

def load_baseline(filepath):
    """Load baseline from JSON file"""
    with open(filepath) as f:
        return json.load(f)

def compare_baselines(baseline1, baseline2):
    """Compare two baselines and print detailed comparison"""

    # Extract metadata
    meta1 = baseline1.get('metadata', {})
    meta2 = baseline2.get('metadata', {})

    print("📊 Metadata Comparison / 元数据比较")
    print("=" * 50)
    print(f"Baseline 1 Timestamp: {baseline1.get('timestamp', 'N/A')}")
    print(f"Baseline 2 Timestamp: {baseline2.get('timestamp', 'N/A')}")
    print(f"Baseline 1 Tests: {meta1.get('total_tests', 'N/A')}")
    print(f"Baseline 2 Tests: {meta2.get('total_tests', 'N/A')}")
    print(f"Baseline 1 Duration: {meta1.get('total_duration', 'N/A')}s")
    print(f"Baseline 2 Duration: {meta2.get('total_duration', 'N/A')}s")
    print()

    # Build URL to result mapping
    results1 = {r['url']: r for r in baseline1.get('results', [])}
    results2 = {r['url']: r for r in baseline2.get('results', [])}

    all_urls = set(results1.keys()) | set(results2.keys())

    faster = []
    slower = []
    similar = []
    only_in_1 = []
    only_in_2 = []

    print("🔍 Detailed Comparison / 详细比较")
    print("=" * 50)

    for url in sorted(all_urls):
        r1 = results1.get(url)
        r2 = results2.get(url)

        if r1 and r2:
            # Both baselines have this URL
            duration1 = r1.get('duration', 0)
            duration2 = r2.get('duration', 0)
            size1 = r1.get('content_size', 0)
            size2 = r2.get('content_size', 0)

            # Calculate percentage change
            if duration1 > 0:
                duration_change = ((duration2 - duration1) / duration1) * 100
            else:
                duration_change = 0

            if size1 > 0:
                size_change = ((size2 - size1) / size1) * 100
            else:
                size_change = 0

            # Categorize
            if duration_change < -10:
                faster.append((url, duration1, duration2, duration_change, size_change))
            elif duration_change > 10:
                slower.append((url, duration1, duration2, duration_change, size_change))
            else:
                similar.append((url, duration1, duration2, duration_change, size_change))

        elif r1:
            only_in_1.append(url)
        else:
            only_in_2.append(url)

    # Print summary
    print(f"\n✅ Performance Improvements: {len(faster)}")
    print(f"⚠️  Performance Regressions: {len(slower)}")
    print(f"➡️  Similar Performance: {len(similar)}")
    print(f"📤 Only in Baseline 1: {len(only_in_1)}")
    print(f"📥 Only in Baseline 2: {len(only_in_2)}")
    print()

    # Show improvements
    if faster:
        print("\n✅ Performance Improvements (>10% faster)")
        print("性能改进 (>10% 更快)")
        print("-" * 80)
        for url, d1, d2, dc, sc in sorted(faster, key=lambda x: x[3])[:10]:
            print(f"  {url[:60]}")
            print(f"    Duration: {d1:.2f}s → {d2:.2f}s ({dc:+.1f}%)")
            print(f"    Size: {sc:+.1f}%")
            print()

    # Show regressions
    if slower:
        print("\n⚠️  Performance Regressions (>10% slower)")
        print("性能回归 (>10% 更慢)")
        print("-" * 80)
        for url, d1, d2, dc, sc in sorted(slower, key=lambda x: x[3], reverse=True)[:10]:
            print(f"  {url[:60]}")
            print(f"    Duration: {d1:.2f}s → {d2:.2f}s ({dc:+.1f}%)")
            print(f"    Size: {sc:+.1f}%")
            print()

    # Show URLs only in one baseline
    if only_in_1:
        print("\n📤 URLs only in Baseline 1:")
        for url in only_in_1[:5]:
            print(f"  {url}")
        if len(only_in_1) > 5:
            print(f"  ... and {len(only_in_1) - 5} more")
        print()

    if only_in_2:
        print("\n📥 URLs only in Baseline 2:")
        for url in only_in_2[:5]:
            print(f"  {url}")
        if len(only_in_2) > 5:
            print(f"  ... and {len(only_in_2) - 5} more")
        print()

    # Overall assessment
    print("\n📈 Overall Assessment / 总体评估")
    print("=" * 50)

    if len(slower) == 0:
        print("✅ No performance regressions detected")
        print("✅ 未检测到性能回归")
    elif len(slower) < len(faster):
        print("⚠️  Some regressions, but more improvements overall")
        print("⚠️  有一些回归，但总体改进更多")
    else:
        print("❌ More regressions than improvements")
        print("❌ 回归多于改进")

    print()

    # Exit code based on comparison
    if len(slower) > 0:
        return 1
    return 0

# Load and compare
baseline1 = load_baseline(os.environ['BASELINE1_FILE'])
baseline2 = load_baseline(os.environ['BASELINE2_FILE'])

exit_code = compare_baselines(baseline1, baseline2)
sys.exit(exit_code)
EOF

exit $?
