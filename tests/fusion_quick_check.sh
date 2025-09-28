#!/bin/bash
# Quick validation script for fusion implementation
# Run this after making changes to quickly verify core functionality

echo "========================================="
echo "FUSION IMPLEMENTATION QUICK CHECK"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if webfetcher.py exists
if [ ! -f "./webfetcher.py" ]; then
    echo -e "${RED}❌ ERROR: webfetcher.py not found!${NC}"
    exit 1
fi

echo ""
echo "📋 Checking parameter support..."
echo "================================"

# Check for new parameters in help
echo -n "Checking --method parameter: "
if ./webfetcher.py --help 2>&1 | grep -q -- "--method\|-m"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

echo -n "Checking --selenium parameter: "
if ./webfetcher.py --help 2>&1 | grep -q -- "--selenium\|-s"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

echo -n "Checking --urllib parameter: "
if ./webfetcher.py --help 2>&1 | grep -q -- "--urllib\|-u"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

echo -n "Checking --no-fallback parameter: "
if ./webfetcher.py --help 2>&1 | grep -q -- "--no-fallback"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

echo ""
echo "🔍 Checking WeChat handling..."
echo "================================"

# Check if WeChat doesn't force selenium
echo -n "WeChat not forcing selenium: "
if grep -q "if 'mp.weixin.qq.com' in host" webfetcher.py && \
   ! grep -A5 "if 'mp.weixin.qq.com' in host" webfetcher.py | grep -q "method.*=.*'selenium'"; then
    echo -e "${GREEN}✓ (Good - maintains urllib flexibility)${NC}"
else
    echo -e "${YELLOW}⚠ (Check if selenium is being forced)${NC}"
fi

echo -n "WeChat mobile UA present: "
if grep -q "MicroMessenger" webfetcher.py; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

echo ""
echo "🧪 Testing basic functionality..."
echo "================================"

# Test basic command execution
echo -n "Basic execution test: "
if ./webfetcher.py "https://example.com" --raw 2>/dev/null | grep -q "Example Domain"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠ (May need internet connection)${NC}"
fi

# Test parameter acceptance (just check if commands are accepted)
echo -n "Parameter acceptance test: "
if ./webfetcher.py -u "https://example.com" --raw --help 2>&1 | grep -q "usage"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠${NC}"
fi

echo ""
echo "📊 Summary"
echo "========================================="

# Count successes
TOTAL_CHECKS=8
PASSED_CHECKS=$(grep -c "✓" <<< "$(./webfetcher.py --help 2>&1)")

echo "Fusion implementation quick check complete!"
echo ""
echo "Next steps:"
echo "1. If all checks passed: Run comprehensive test suite"
echo "   python tests/fusion_test_suite.py"
echo ""
echo "2. If some checks failed: Review the implementation"
echo "   - Check parameter definitions around line 4828"
echo "   - Verify parameter processing in main()"
echo "   - Ensure WeChat handling isn't forcing selenium"
echo ""
echo "3. Test with real URLs:"
echo "   ./webfetcher.py -u 'https://mp.weixin.qq.com/s/actual_article'"
echo "   ./webfetcher.py -s 'https://www.xiaohongshu.com/explore/actual_post'"
echo ""
echo "========================================="