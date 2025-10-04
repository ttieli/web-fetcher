#!/bin/bash

# Test script for Phase 2.2 Chrome tab control functions

# Set up environment
export PROFILE_DIR="/tmp/chrome-profile"
export DEBUG=true
export PORT=9222
export PID_FILE="${PROFILE_DIR}/chrome.pid"

# Source the script functions without executing main
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Define a no-op main to prevent execution
main() {
    return 0
}

# Source the script
source "${SCRIPT_DIR}/config/ensure-chrome-debug.sh"

echo "========================================="
echo "Phase 2.2 Chrome Tab Control Tests"
echo "========================================="
echo ""

# Test 1: Create a new tab
echo "Test 1: Creating new tab with about:blank..."
new_tab_id=$(create_chrome_tab "about:blank")
if [[ -n "${new_tab_id}" ]]; then
    echo "✓ Created new tab with ID: ${new_tab_id}"
else
    echo "✗ Failed to create new tab"
    exit 1
fi
echo ""

# Test 2: Get tab info
echo "Test 2: Getting tab info for ${new_tab_id}..."
tab_info=$(get_chrome_tab_info "${new_tab_id}")
if [[ -n "${tab_info}" ]]; then
    echo "✓ Retrieved tab info successfully"
    echo "Info: ${tab_info}" | head -c 200
    echo "..."
else
    echo "✗ Failed to get tab info"
    exit 1
fi
echo ""

# Test 3: Get specific field (title)
echo "Test 3: Getting tab title for ${new_tab_id}..."
tab_title=$(get_chrome_tab_info "${new_tab_id}" "title")
if [[ -n "${tab_title}" ]]; then
    echo "✓ Tab title: ${tab_title}"
else
    echo "✗ Failed to get tab title"
fi
echo ""

# Test 4: Navigate tab
echo "Test 4: Navigating tab to https://example.com..."
if navigate_chrome_tab "${new_tab_id}" "https://example.com"; then
    echo "✓ Navigation initiated successfully"
else
    echo "✗ Failed to navigate tab"
fi
echo ""

# Test 5: Activate tab
echo "Test 5: Activating tab ${new_tab_id}..."
if activate_chrome_tab "${new_tab_id}"; then
    echo "✓ Tab activated successfully"
else
    echo "✗ Failed to activate tab"
fi
echo ""

# Test 6: Create another tab for testing
echo "Test 6: Creating another tab..."
second_tab_id=$(create_chrome_tab "https://github.com")
if [[ -n "${second_tab_id}" ]]; then
    echo "✓ Created second tab with ID: ${second_tab_id}"
else
    echo "✗ Failed to create second tab"
    exit 1
fi
echo ""

# Test 7: List all tabs
echo "Test 7: Listing all tabs..."
if list_chrome_tabs 9222 simple; then
    echo "✓ Listed tabs successfully"
else
    echo "✗ Failed to list tabs"
fi
echo ""

# Test 8: Close a tab (not the last one)
echo "Test 8: Closing tab ${second_tab_id}..."
if close_chrome_tab "${second_tab_id}"; then
    echo "✓ Tab closed successfully"
else
    echo "✗ Failed to close tab"
fi
echo ""

# Test 9: Verify tab was closed
echo "Test 9: Verifying tab ${second_tab_id} was closed..."
if ! get_chrome_tab_info "${second_tab_id}" >/dev/null 2>&1; then
    echo "✓ Tab no longer exists (correctly closed)"
else
    echo "✗ Tab still exists after closure"
fi
echo ""

# Test 10: Error handling - invalid tab ID
echo "Test 10: Testing error handling with invalid tab ID..."
if ! activate_chrome_tab "invalid-tab-id-12345" 2>/dev/null; then
    echo "✓ Correctly failed with invalid tab ID"
else
    echo "✗ Should have failed with invalid tab ID"
fi
echo ""

# Test 11: Error handling - invalid URL
echo "Test 11: Testing error handling with invalid URL..."
if ! navigate_chrome_tab "${new_tab_id}" "not-a-valid-url" 2>/dev/null; then
    echo "✓ Correctly failed with invalid URL"
else
    echo "✗ Should have failed with invalid URL"
fi
echo ""

# Test 12: Performance test - measure function execution time
echo "Test 12: Performance test..."
start_time=$(date +%s%N)
list_chrome_tabs 9222 simple >/dev/null 2>&1
end_time=$(date +%s%N)
elapsed_ms=$(( (end_time - start_time) / 1000000 ))
echo "List tabs execution time: ${elapsed_ms}ms"
if [[ ${elapsed_ms} -lt 500 ]]; then
    echo "✓ Performance within 500ms requirement"
else
    echo "✗ Performance exceeds 500ms requirement"
fi
echo ""

echo "========================================="
echo "Phase 2.2 Test Suite Complete"
echo "========================================="