#!/bin/bash

# Standalone test for Phase 2.2 functions
# This script directly tests the functions without sourcing the entire file

PORT=9222
DEBUG=true

# Minimal logging functions
log_debug() { [[ "${DEBUG}" == "true" ]] && echo "[DEBUG] $*" >&2; }
log_info() { echo "[INFO] $*" >&2; }
log_error() { echo "[ERROR] $*" >&2; }

echo "========================================="
echo "Testing Phase 2.2 Tab Control Functions"
echo "========================================="
echo ""

# Test 1: Create new tab
echo "Test 1: Create new tab..."
response=$(curl -s -X PUT "http://localhost:${PORT}/json/new?about:blank" 2>/dev/null)
if [[ -n "${response}" ]]; then
    tab_id=$(echo "${response}" | grep -o '"id"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)".*/\1/' | head -n 1)
    if [[ -n "${tab_id}" ]]; then
        echo "✓ Created tab: ${tab_id}"
    else
        echo "✗ Failed to extract tab ID"
    fi
else
    echo "✗ Failed to create tab"
fi
echo ""

# Test 2: List tabs
echo "Test 2: List tabs..."
response=$(curl -s "http://localhost:${PORT}/json" 2>/dev/null)
if [[ -n "${response}" ]]; then
    tab_count=$(echo "${response}" | grep -o '"id"[[:space:]]*:' | wc -l | xargs)
    echo "✓ Found ${tab_count} tab(s)"
else
    echo "✗ Failed to list tabs"
fi
echo ""

# Test 3: Get tab info
echo "Test 3: Get tab info for ${tab_id}..."
if [[ -n "${tab_id}" ]]; then
    if echo "${response}" | grep -q "\"id\"[[:space:]]*:[[:space:]]*\"${tab_id}\""; then
        echo "✓ Tab ${tab_id} exists in list"
        # Extract title
        title=$(echo "${response}" | sed 's/},{/\n/g' | grep "\"id\"[[:space:]]*:[[:space:]]*\"${tab_id}\"" | grep -o '"title"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)".*/\1/')
        echo "  Title: ${title:-[empty]}"
    else
        echo "✗ Tab not found in list"
    fi
else
    echo "✗ No tab ID to test"
fi
echo ""

# Test 4: Activate tab
echo "Test 4: Activate tab ${tab_id}..."
if [[ -n "${tab_id}" ]]; then
    response=$(curl -s "http://localhost:${PORT}/json/activate/${tab_id}" 2>/dev/null)
    if [[ "${response}" == "Target activated" ]]; then
        echo "✓ Tab activated"
    else
        echo "✗ Failed to activate: ${response}"
    fi
else
    echo "✗ No tab ID to test"
fi
echo ""

# Test 5: Create second tab
echo "Test 5: Create second tab..."
response=$(curl -s -X PUT "http://localhost:${PORT}/json/new?https://github.com" 2>/dev/null)
if [[ -n "${response}" ]]; then
    tab2_id=$(echo "${response}" | grep -o '"id"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)".*/\1/' | head -n 1)
    if [[ -n "${tab2_id}" ]]; then
        echo "✓ Created second tab: ${tab2_id}"
    else
        echo "✗ Failed to extract second tab ID"
    fi
else
    echo "✗ Failed to create second tab"
fi
echo ""

# Test 6: Close tab (not the last one)
echo "Test 6: Close tab ${tab2_id}..."
if [[ -n "${tab2_id}" ]]; then
    # First check we have more than one tab
    response=$(curl -s "http://localhost:${PORT}/json" 2>/dev/null)
    tab_count=$(echo "${response}" | grep -o '"id"[[:space:]]*:' | wc -l | xargs)

    if [[ ${tab_count} -gt 1 ]]; then
        response=$(curl -s "http://localhost:${PORT}/json/close/${tab2_id}" 2>/dev/null)
        if echo "${response}" | grep -q "clos"; then
            echo "✓ Tab closed: ${response}"
        else
            echo "✗ Failed to close: ${response}"
        fi
    else
        echo "⚠ Only one tab, skipping close test"
    fi
else
    echo "✗ No tab ID to test"
fi
echo ""

# Test 7: Performance test
echo "Test 7: Performance test..."
start_ms=$(date +%s%3N 2>/dev/null || echo "0")
curl -s "http://localhost:${PORT}/json" >/dev/null 2>&1
end_ms=$(date +%s%3N 2>/dev/null || echo "100")
if [[ "${start_ms}" != "0" ]] && [[ "${end_ms}" != "100" ]]; then
    elapsed=$((end_ms - start_ms))
    echo "  List tabs time: ${elapsed}ms"
    if [[ ${elapsed} -lt 500 ]]; then
        echo "✓ Performance OK (< 500ms)"
    else
        echo "✗ Performance slow (> 500ms)"
    fi
else
    echo "⚠ Cannot measure precise timing on this system"
fi
echo ""

# Test 8: Error handling - invalid tab ID
echo "Test 8: Error handling with invalid tab..."
response=$(curl -s "http://localhost:${PORT}/json/activate/invalid-tab-xyz" 2>/dev/null)
if [[ "${response}" != "Target activated" ]]; then
    echo "✓ Correctly failed with invalid tab"
else
    echo "✗ Should have failed with invalid tab"
fi
echo ""

echo "========================================="
echo "Direct API Tests Complete"
echo "========================================="