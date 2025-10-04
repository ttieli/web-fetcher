#!/bin/bash
# Test Suite for Phase 2 Step 2.2: Advanced Tab Management Functions
# Tests all five new functions with comprehensive scenarios

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"
ENSURE_SCRIPT="${PROJECT_DIR}/config/ensure-chrome-debug.sh"

# Test configuration
PORT="9222"
TEST_URL_1="https://www.example.com"
TEST_URL_2="https://www.google.com"
INVALID_URL="not-a-url"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
log_test() {
    echo -e "\n${YELLOW}[TEST]${NC} $*"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $*"
    ((TESTS_PASSED++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $*"
    ((TESTS_FAILED++))
}

log_info() {
    echo -e "[INFO] $*"
}

# Source the script to access functions
source "${ENSURE_SCRIPT}" --quiet 2>/dev/null || true

# Check Chrome is running
check_chrome_running() {
    if ! nc -z localhost "${PORT}" 2>/dev/null; then
        echo -e "${RED}ERROR: Chrome is not running on port ${PORT}${NC}"
        echo "Please start Chrome in debug mode first:"
        echo "  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 --user-data-dir=~/.chrome-wf &"
        exit 1
    fi
    log_info "Chrome is running on port ${PORT}"
}

# Get a valid tab ID for testing
get_test_tab_id() {
    local tabs_json
    tabs_json=$(curl -s "http://localhost:${PORT}/json" 2>/dev/null || echo "")

    if command -v jq >/dev/null 2>&1; then
        echo "${tabs_json}" | jq -r '.[0].id // empty' 2>/dev/null
    else
        echo "${tabs_json}" | grep -o '"id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -n 1 | sed 's/.*"\([^"]*\)".*/\1/'
    fi
}

# Test 1: create_chrome_tab - Create with URL
test_create_tab_with_url() {
    log_test "create_chrome_tab: Create tab with URL"

    local new_tab_id
    new_tab_id=$(create_chrome_tab "${TEST_URL_1}" 2>&1)
    local status=$?

    if [[ ${status} -eq 0 ]] && [[ -n "${new_tab_id}" ]]; then
        log_pass "Created tab with ID: ${new_tab_id}"
        echo "${new_tab_id}"
        return 0
    else
        log_fail "Failed to create tab with URL (status: ${status})"
        return 1
    fi
}

# Test 2: create_chrome_tab - Create without URL (about:blank)
test_create_tab_blank() {
    log_test "create_chrome_tab: Create tab without URL (about:blank)"

    local new_tab_id
    new_tab_id=$(create_chrome_tab 2>&1)
    local status=$?

    if [[ ${status} -eq 0 ]] && [[ -n "${new_tab_id}" ]]; then
        log_pass "Created blank tab with ID: ${new_tab_id}"
        echo "${new_tab_id}"
        return 0
    else
        log_fail "Failed to create blank tab (status: ${status})"
        return 1
    fi
}

# Test 3: get_chrome_tab_info - Get full info
test_get_tab_info_full() {
    log_test "get_chrome_tab_info: Get full tab info"

    local tab_id="$1"
    local tab_info
    tab_info=$(get_chrome_tab_info "${tab_id}" 2>&1)
    local status=$?

    if [[ ${status} -eq 0 ]] && echo "${tab_info}" | grep -q '"id"'; then
        log_pass "Retrieved full tab info"
        log_info "Tab info (truncated): $(echo "${tab_info}" | head -c 100)..."
        return 0
    else
        log_fail "Failed to get full tab info (status: ${status})"
        return 1
    fi
}

# Test 4: get_chrome_tab_info - Extract specific field
test_get_tab_info_field() {
    log_test "get_chrome_tab_info: Extract specific field (title)"

    local tab_id="$1"
    local title
    title=$(get_chrome_tab_info "${tab_id}" "title" 2>&1)
    local status=$?

    if [[ ${status} -eq 0 ]] && [[ -n "${title}" ]]; then
        log_pass "Retrieved tab title: ${title}"
        return 0
    else
        log_fail "Failed to extract title field (status: ${status})"
        return 1
    fi
}

# Test 5: activate_chrome_tab - Activate existing tab
test_activate_tab() {
    log_test "activate_chrome_tab: Activate existing tab"

    local tab_id="$1"
    local output
    output=$(activate_chrome_tab "${tab_id}" 2>&1)
    local status=$?

    if [[ ${status} -eq 0 ]]; then
        log_pass "Activated tab ${tab_id}"
        return 0
    else
        log_fail "Failed to activate tab (status: ${status}): ${output}"
        return 1
    fi
}

# Test 6: navigate_chrome_tab - Navigate to valid URL
test_navigate_tab_valid_url() {
    log_test "navigate_chrome_tab: Navigate to valid URL"

    local tab_id="$1"
    local output
    output=$(navigate_chrome_tab "${tab_id}" "${TEST_URL_2}" 2>&1)
    local status=$?

    if [[ ${status} -eq 0 ]]; then
        log_pass "Navigation to ${TEST_URL_2} initiated"
        return 0
    else
        log_fail "Failed to navigate (status: ${status}): ${output}"
        return 1
    fi
}

# Test 7: navigate_chrome_tab - Reject invalid URL
test_navigate_tab_invalid_url() {
    log_test "navigate_chrome_tab: Reject invalid URL"

    local tab_id="$1"
    local output
    output=$(navigate_chrome_tab "${tab_id}" "${INVALID_URL}" 2>&1)
    local status=$?

    if [[ ${status} -ne 0 ]] && echo "${output}" | grep -qi "invalid"; then
        log_pass "Correctly rejected invalid URL"
        return 0
    else
        log_fail "Should have rejected invalid URL (status: ${status})"
        return 1
    fi
}

# Test 8: close_chrome_tab - Close existing tab
test_close_tab() {
    log_test "close_chrome_tab: Close existing tab"

    local tab_id="$1"
    local output
    output=$(close_chrome_tab "${tab_id}" 2>&1)
    local status=$?

    if [[ ${status} -eq 0 ]]; then
        log_pass "Closed tab ${tab_id}"
        return 0
    else
        log_fail "Failed to close tab (status: ${status}): ${output}"
        return 1
    fi
}

# Test 9: close_chrome_tab - Handle non-existent tab
test_close_nonexistent_tab() {
    log_test "close_chrome_tab: Handle non-existent tab"

    local fake_tab_id="nonexistent-tab-id-12345"
    local output
    output=$(close_chrome_tab "${fake_tab_id}" 2>&1)
    local status=$?

    if [[ ${status} -eq 1 ]] && echo "${output}" | grep -qi "not found"; then
        log_pass "Correctly handled non-existent tab"
        return 0
    else
        log_fail "Should have returned error for non-existent tab (status: ${status})"
        return 1
    fi
}

# Test 10: Handle Chrome not running
test_chrome_not_running() {
    log_test "All functions: Handle Chrome not running"

    # Save original port and use invalid port
    local orig_port="${PORT}"
    PORT="9999"

    local errors=0

    # Test create_chrome_tab
    if create_chrome_tab 2>&1 | grep -qi "not reachable"; then
        log_info "  create_chrome_tab correctly detected Chrome not running"
    else
        ((errors++))
    fi

    # Test with a fake tab ID for other functions
    local fake_id="test"

    if close_chrome_tab "${fake_id}" 2>&1 | grep -qi "not reachable"; then
        log_info "  close_chrome_tab correctly detected Chrome not running"
    else
        ((errors++))
    fi

    if activate_chrome_tab "${fake_id}" 2>&1 | grep -qi "not reachable"; then
        log_info "  activate_chrome_tab correctly detected Chrome not running"
    else
        ((errors++))
    fi

    if get_chrome_tab_info "${fake_id}" 2>&1 | grep -qi "not reachable"; then
        log_info "  get_chrome_tab_info correctly detected Chrome not running"
    else
        ((errors++))
    fi

    if navigate_chrome_tab "${fake_id}" "https://example.com" 2>&1 | grep -qi "not reachable"; then
        log_info "  navigate_chrome_tab correctly detected Chrome not running"
    else
        ((errors++))
    fi

    # Restore port
    PORT="${orig_port}"

    if [[ ${errors} -eq 0 ]]; then
        log_pass "All functions correctly handle Chrome not running"
        return 0
    else
        log_fail "${errors} functions failed to detect Chrome not running"
        return 1
    fi
}

# Main test execution
main() {
    echo "=========================================="
    echo "Phase 2 Step 2.2 - Advanced Tab Management"
    echo "Test Suite"
    echo "=========================================="

    # Check prerequisites
    check_chrome_running

    # Create test tabs
    log_info "Creating test tabs..."
    local tab1 tab2
    tab1=$(test_create_tab_with_url) || exit 1
    sleep 1
    tab2=$(test_create_tab_blank) || exit 1
    sleep 1

    # Get info tests
    test_get_tab_info_full "${tab1}"
    sleep 0.5
    test_get_tab_info_field "${tab1}"
    sleep 0.5

    # Activate test
    test_activate_tab "${tab1}"
    sleep 0.5

    # Navigate tests
    test_navigate_tab_valid_url "${tab1}"
    sleep 0.5
    test_navigate_tab_invalid_url "${tab1}"
    sleep 0.5

    # Close tests
    test_close_tab "${tab2}"
    sleep 0.5
    test_close_nonexistent_tab
    sleep 0.5

    # Chrome not running test
    test_chrome_not_running

    # Clean up: close test tab
    log_info "Cleaning up test tabs..."
    close_chrome_tab "${tab1}" 2>/dev/null || true

    # Summary
    echo ""
    echo "=========================================="
    echo "Test Results Summary"
    echo "=========================================="
    echo -e "${GREEN}Passed: ${TESTS_PASSED}${NC}"
    echo -e "${RED}Failed: ${TESTS_FAILED}${NC}"
    echo "Total:  $((TESTS_PASSED + TESTS_FAILED))"
    echo "=========================================="

    if [[ ${TESTS_FAILED} -eq 0 ]]; then
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}Some tests failed!${NC}"
        exit 1
    fi
}

# Run tests
main "$@"
