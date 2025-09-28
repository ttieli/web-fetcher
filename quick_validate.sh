#!/bin/bash

# Phase 2: Quick Validation Script
# Run this after each removal step to verify functionality

echo "================================================"
echo "Phase 2: Quick Validation Check"
echo "================================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test 1: Import check
echo -e "\n[Test 1] Checking if webfetcher imports..."
if python3 -c "import webfetcher" 2>/dev/null; then
    echo -e "${GREEN}✓ webfetcher imports successfully${NC}"
else
    echo -e "${RED}✗ webfetcher import failed${NC}"
    exit 1
fi

# Test 2: fetch_html exists
echo -e "\n[Test 2] Checking if fetch_html function exists..."
if python3 -c "from webfetcher import fetch_html; print('OK')" 2>/dev/null | grep -q "OK"; then
    echo -e "${GREEN}✓ fetch_html function exists${NC}"
else
    echo -e "${RED}✗ fetch_html function not found${NC}"
    exit 1
fi

# Test 3: No Safari references (except SAFARI_AVAILABLE = False)
echo -e "\n[Test 3] Checking for Safari references..."
SAFARI_COUNT=$(grep -c "should_fallback_to_safari\|extract_with_safari_fallback\|requires_safari_preemptively" webfetcher.py 2>/dev/null || echo "0")
if [ "$SAFARI_COUNT" -eq "0" ]; then
    echo -e "${GREEN}✓ No problematic Safari references found${NC}"
else
    echo -e "${RED}✗ Found $SAFARI_COUNT Safari references${NC}"
    grep -n "should_fallback_to_safari\|extract_with_safari_fallback\|requires_safari_preemptively" webfetcher.py
fi

# Test 4: No plugin references
echo -e "\n[Test 4] Checking for plugin system references..."
PLUGIN_COUNT=$(grep -c "fetch_html_with_plugins\|get_global_registry\|FetchContext" webfetcher.py 2>/dev/null || echo "0")
if [ "$PLUGIN_COUNT" -eq "0" ]; then
    echo -e "${GREEN}✓ No plugin system references found${NC}"
else
    echo -e "${RED}✗ Found $PLUGIN_COUNT plugin references${NC}"
    grep -n "fetch_html_with_plugins\|get_global_registry\|FetchContext" webfetcher.py
fi

# Test 5: Basic fetch test
echo -e "\n[Test 5] Testing basic fetch functionality..."
TEST_OUTPUT=$(python3 -c "
try:
    from webfetcher import fetch_html
    html, metrics = fetch_html('https://example.com', timeout=5)
    if html and len(html) > 0:
        print(f'OK: {len(html)} bytes fetched via {metrics.primary_method}')
    else:
        print('FAIL: No content')
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)

if echo "$TEST_OUTPUT" | grep -q "^OK:"; then
    echo -e "${GREEN}✓ Fetch test passed: $TEST_OUTPUT${NC}"
else
    echo -e "${RED}✗ Fetch test failed: $TEST_OUTPUT${NC}"
fi

# Test 6: Check fetch_html assignment
echo -e "\n[Test 6] Checking fetch_html assignment..."
ASSIGNMENT=$(grep "^fetch_html = " webfetcher.py | head -1)
if echo "$ASSIGNMENT" | grep -q "fetch_html_with_retry"; then
    echo -e "${GREEN}✓ fetch_html correctly assigned to fetch_html_with_retry${NC}"
elif echo "$ASSIGNMENT" | grep -q "fetch_html_with_plugins"; then
    echo -e "${RED}✗ fetch_html still assigned to fetch_html_with_plugins${NC}"
else
    echo -e "${RED}✗ fetch_html assignment unclear: $ASSIGNMENT${NC}"
fi

# Summary
echo -e "\n================================================"
echo "Validation Complete"
echo "================================================"
echo ""
echo "If all tests passed, you can proceed to the next step."
echo "If any test failed, review the changes and fix issues before continuing."