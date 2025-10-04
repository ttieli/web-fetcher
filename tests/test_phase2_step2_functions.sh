#!/bin/bash
# Direct Function Test for Phase 2 Step 2.2
# Tests each function implementation in ensure-chrome-debug.sh

set -euo pipefail

# Load only the functions without executing main
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"
ENSURE_SCRIPT="${PROJECT_DIR}/config/ensure-chrome-debug.sh"

# Extract and source only functions (not main execution)
# We'll manually define the needed variables and functions
PORT="9222"
QUIET_MODE=false

# Source functions from the script (extract only function definitions)
# This is a bit hacky but works for testing
eval "$(grep -A 1000 'navigate_chrome_tab()' "${ENSURE_SCRIPT}" | grep -B 1000 '^# select_recovery_strategy' | head -n -1)"

# Also need the logging functions
log_info() {
    if [[ "${QUIET_MODE}" != "true" ]]; then
        echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') $*" >&2
    fi
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') $*" >&2
}

log_debug() {
    if [[ "${QUIET_MODE}" != "true" ]]; then
        echo "[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') $*" >&2
    fi
}

# Test utilities
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

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

# Check Chrome
if ! nc -z localhost "${PORT}" 2>/dev/null; then
    echo -e "${RED}ERROR: Chrome not running on port ${PORT}${NC}"
    exit 1
fi

echo "=========================================="
echo "Phase 2.2 - Function Implementation Tests"
echo "=========================================="

# Test 1: create_chrome_tab with URL
log_test "Function: create_chrome_tab with URL"
tab1=$(create_chrome_tab "https://www.example.com" 2>/dev/null)
status=$?
if [[ ${status} -eq 0 ]] && [[ -n "${tab1}" ]]; then
    log_pass "Created tab: ${tab1}"
else
    log_fail "Failed (status: ${status})"
fi
sleep 1

# Test 2: create_chrome_tab without URL
log_test "Function: create_chrome_tab without URL (about:blank)"
tab2=$(create_chrome_tab 2>/dev/null)
status=$?
if [[ ${status} -eq 0 ]] && [[ -n "${tab2}" ]]; then
    log_pass "Created blank tab: ${tab2}"
else
    log_fail "Failed (status: ${status})"
fi
sleep 1

# Test 3: get_chrome_tab_info - full
log_test "Function: get_chrome_tab_info (full)"
info=$(get_chrome_tab_info "${tab1}" 2>/dev/null)
status=$?
if [[ ${status} -eq 0 ]] && echo "${info}" | grep -q '"id"'; then
    log_pass "Retrieved full info"
else
    log_fail "Failed (status: ${status})"
fi

# Test 4: get_chrome_tab_info - field
log_test "Function: get_chrome_tab_info (field: title)"
title=$(get_chrome_tab_info "${tab1}" "title" 2>/dev/null)
status=$?
if [[ ${status} -eq 0 ]] && [[ -n "${title}" ]]; then
    log_pass "Title: ${title}"
else
    log_fail "Failed (status: ${status})"
fi

# Test 5: activate_chrome_tab
log_test "Function: activate_chrome_tab"
activate_chrome_tab "${tab1}" 2>/dev/null
status=$?
if [[ ${status} -eq 0 ]]; then
    log_pass "Activated tab ${tab1}"
else
    log_fail "Failed (status: ${status})"
fi
sleep 1

# Test 6: navigate_chrome_tab - valid URL
log_test "Function: navigate_chrome_tab (valid URL)"
navigate_chrome_tab "${tab1}" "https://www.google.com" 2>/dev/null
status=$?
if [[ ${status} -eq 0 ]]; then
    log_pass "Navigation initiated"
else
    log_fail "Failed (status: ${status})"
fi

# Test 7: navigate_chrome_tab - invalid URL
log_test "Function: navigate_chrome_tab (invalid URL)"
navigate_chrome_tab "${tab1}" "not-a-url" 2>/dev/null
status=$?
if [[ ${status} -ne 0 ]]; then
    log_pass "Correctly rejected invalid URL (status: ${status})"
else
    log_fail "Should have rejected invalid URL"
fi

# Test 8: close_chrome_tab
log_test "Function: close_chrome_tab"
close_chrome_tab "${tab2}" 2>/dev/null
status=$?
if [[ ${status} -eq 0 ]]; then
    log_pass "Closed tab ${tab2}"
else
    log_fail "Failed (status: ${status})"
fi
sleep 1

# Test 9: close non-existent tab
log_test "Function: close_chrome_tab (non-existent)"
close_chrome_tab "fake-id-12345" 2>/dev/null
status=$?
if [[ ${status} -eq 1 ]]; then
    log_pass "Correctly returned status 1 for non-existent tab"
else
    log_fail "Expected status 1, got ${status}"
fi

# Test 10: Error handling - Chrome not running
log_test "Function: Error handling (port not reachable)"
OLD_PORT="${PORT}"
PORT="9999"
create_chrome_tab 2>/dev/null
status=$?
PORT="${OLD_PORT}"
if [[ ${status} -ne 0 ]]; then
    log_pass "Functions correctly detect unreachable port"
else
    log_fail "Should have failed when port unreachable"
fi

# Cleanup
echo ""
echo "[INFO] Cleaning up..."
close_chrome_tab "${tab1}" 2>/dev/null || true

# Summary
echo ""
echo "=========================================="
echo "Test Results"
echo "=========================================="
echo -e "${GREEN}Passed: ${TESTS_PASSED}${NC}"
echo -e "${RED}Failed: ${TESTS_FAILED}${NC}"
echo "Total:  $((TESTS_PASSED + TESTS_FAILED))"
echo "=========================================="

if [[ ${TESTS_FAILED} -eq 0 ]]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed${NC}"
    exit 1
fi
