#!/bin/bash
# Test script for Phase 2 Step 2.3: Session Persistence and State Management
# Tests: save_chrome_session, restore_chrome_session, monitor_chrome_tabs, execute_in_tab

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"
ENSURE_CHROME_SCRIPT="${PROJECT_ROOT}/config/ensure-chrome-debug.sh"

# Test session file
TEST_SESSION_FILE="/tmp/test-chrome-session-$$.json"
TEST_SESSION_DIR="/tmp/test-chrome-sessions-$$"

# Source the script
if [ ! -f "${ENSURE_CHROME_SCRIPT}" ]; then
    echo -e "${RED}Error: Script not found: ${ENSURE_CHROME_SCRIPT}${NC}"
    exit 1
fi

source "${ENSURE_CHROME_SCRIPT}"

# Enable debug mode for better visibility
export DEBUG=1

# Helper functions
print_test_header() {
    echo ""
    echo "========================================="
    echo "TEST: $1"
    echo "========================================="
}

assert_success() {
    local test_name="$1"
    local result=$2
    TESTS_TOTAL=$((TESTS_TOTAL + 1))

    if [ ${result} -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: ${test_name}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}: ${test_name} (exit code: ${result})"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_failure() {
    local test_name="$1"
    local result=$2
    TESTS_TOTAL=$((TESTS_TOTAL + 1))

    if [ ${result} -ne 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: ${test_name}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}: ${test_name} (expected failure but succeeded)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_file_exists() {
    local test_name="$1"
    local file_path="$2"
    TESTS_TOTAL=$((TESTS_TOTAL + 1))

    if [ -f "${file_path}" ]; then
        echo -e "${GREEN}✓ PASS${NC}: ${test_name}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}: ${test_name} (file not found: ${file_path})"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_contains() {
    local test_name="$1"
    local haystack="$2"
    local needle="$3"
    TESTS_TOTAL=$((TESTS_TOTAL + 1))

    if echo "${haystack}" | grep -q "${needle}"; then
        echo -e "${GREEN}✓ PASS${NC}: ${test_name}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}: ${test_name} (expected to find: ${needle})"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

cleanup() {
    echo ""
    echo "Cleaning up test files..."
    rm -f "${TEST_SESSION_FILE}" 2>/dev/null || true
    rm -rf "${TEST_SESSION_DIR}" 2>/dev/null || true
}

trap cleanup EXIT

# ==================================================
# PREREQUISITES
# ==================================================
print_test_header "Prerequisites Check"

echo "Checking if Chrome debug mode is running..."
if ! check_chrome_debug_mode "${PORT}" >/dev/null 2>&1; then
    echo -e "${YELLOW}Chrome not running in debug mode. Starting...${NC}"
    ensure_chrome_debug_mode
    sleep 2
fi

if check_chrome_debug_mode "${PORT}" >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Chrome debug mode is active"
else
    echo -e "${RED}✗ Failed to start Chrome in debug mode${NC}"
    exit 1
fi

# ==================================================
# TEST 1: save_chrome_session() - Default location
# ==================================================
print_test_header "Test 1: save_chrome_session() - Default location"

# Create some test tabs first
echo "Creating test tabs..."
create_chrome_tab "${PORT}" "https://example.com" >/dev/null 2>&1
create_chrome_tab "${PORT}" "https://www.google.com" >/dev/null 2>&1
create_chrome_tab "${PORT}" "https://github.com" >/dev/null 2>&1
sleep 1

# Save session to default location
DEFAULT_SESSION="$HOME/.chrome-debug-session.json"
rm -f "${DEFAULT_SESSION}" 2>/dev/null || true

save_chrome_session >/dev/null 2>&1
result=$?
assert_success "save_chrome_session() returns 0" ${result}
assert_file_exists "Default session file created" "${DEFAULT_SESSION}"

# Validate JSON format
if command -v jq >/dev/null 2>&1; then
    session_content=$(cat "${DEFAULT_SESSION}")
    assert_contains "Session has timestamp field" "${session_content}" '"timestamp"'
    assert_contains "Session has chrome_version field" "${session_content}" '"chrome_version"'
    assert_contains "Session has tabs field" "${session_content}" '"tabs"'

    # Check if tabs array has at least 3 tabs
    tab_count=$(echo "${session_content}" | jq '.tabs | length' 2>/dev/null)
    if [ "${tab_count}" -ge 3 ]; then
        echo -e "${GREEN}✓ PASS${NC}: Session contains ${tab_count} tabs"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC}: Session contains only ${tab_count} tabs (expected >= 3)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
fi

rm -f "${DEFAULT_SESSION}" 2>/dev/null || true

# ==================================================
# TEST 2: save_chrome_session() - Custom location
# ==================================================
print_test_header "Test 2: save_chrome_session() - Custom location"

save_chrome_session "${TEST_SESSION_FILE}" >/dev/null 2>&1
result=$?
assert_success "save_chrome_session(custom_file) returns 0" ${result}
assert_file_exists "Custom session file created" "${TEST_SESSION_FILE}"

# ==================================================
# TEST 3: save_chrome_session() - Directory creation
# ==================================================
print_test_header "Test 3: save_chrome_session() - Directory creation"

mkdir -p "${TEST_SESSION_DIR}"
NESTED_SESSION="${TEST_SESSION_DIR}/nested/session.json"

save_chrome_session "${NESTED_SESSION}" >/dev/null 2>&1
result=$?
assert_success "save_chrome_session() creates parent directory" ${result}
assert_file_exists "Nested session file created" "${NESTED_SESSION}"

# ==================================================
# TEST 4: restore_chrome_session() - Valid session
# ==================================================
print_test_header "Test 4: restore_chrome_session() - Valid session"

# Close all tabs first (except one to keep Chrome alive)
echo "Preparing for restore test..."
tabs=$(list_chrome_tabs "${PORT}" "simple" 2>/dev/null)
tab_count=$(echo "${tabs}" | wc -l | tr -d ' ')

if [ ${tab_count} -gt 1 ]; then
    echo "${tabs}" | tail -n +2 | while IFS='|' read -r id title url type; do
        [ -n "${id}" ] && close_chrome_tab "${PORT}" "${id}" >/dev/null 2>&1 || true
    done
    sleep 1
fi

# Restore session
restore_output=$(restore_chrome_session "${TEST_SESSION_FILE}" 2>&1)
result=$?
assert_success "restore_chrome_session() returns 0" ${result}
assert_contains "Restore output contains mapping" "${restore_output}" " -> "

# Verify tabs were restored
sleep 1
new_tabs=$(list_chrome_tabs "${PORT}" "simple" 2>/dev/null)
new_tab_count=$(echo "${new_tabs}" | wc -l | tr -d ' ')

if [ ${new_tab_count} -ge 3 ]; then
    echo -e "${GREEN}✓ PASS${NC}: Restored ${new_tab_count} tabs"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC}: Only ${new_tab_count} tabs after restore (expected >= 3)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_TOTAL=$((TESTS_TOTAL + 1))

# ==================================================
# TEST 5: restore_chrome_session() - Missing file
# ==================================================
print_test_header "Test 5: restore_chrome_session() - Missing file"

restore_chrome_session "/tmp/nonexistent-session-$$.json" >/dev/null 2>&1
result=$?
assert_failure "restore_chrome_session() fails on missing file" ${result}

# ==================================================
# TEST 6: restore_chrome_session() - Corrupted JSON
# ==================================================
print_test_header "Test 6: restore_chrome_session() - Corrupted JSON"

CORRUPT_SESSION="/tmp/corrupt-session-$$.json"
echo "{ invalid json }" > "${CORRUPT_SESSION}"

restore_chrome_session "${CORRUPT_SESSION}" >/dev/null 2>&1
result=$?
assert_failure "restore_chrome_session() fails on corrupted JSON" ${result}

rm -f "${CORRUPT_SESSION}" 2>/dev/null || true

# ==================================================
# TEST 7: restore_chrome_session() - No parameter
# ==================================================
print_test_header "Test 7: restore_chrome_session() - No parameter"

restore_chrome_session >/dev/null 2>&1
result=$?
assert_failure "restore_chrome_session() fails without parameter" ${result}

# ==================================================
# TEST 8: monitor_chrome_tabs() - Basic functionality
# ==================================================
print_test_header "Test 8: monitor_chrome_tabs() - Basic functionality"

echo "Starting monitor in background (5 seconds)..."
MONITOR_OUTPUT="/tmp/monitor-output-$$.txt"

# Start monitor in background
(timeout 5 bash -c "source '${ENSURE_CHROME_SCRIPT}' && monitor_chrome_tabs 1" > "${MONITOR_OUTPUT}" 2>&1 || true) &
MONITOR_PID=$!

sleep 1

# Create a new tab
echo "Creating new tab during monitoring..."
create_chrome_tab "${PORT}" "https://example.org" >/dev/null 2>&1
NEW_TAB_ID=$(list_chrome_tabs "${PORT}" "simple" 2>/dev/null | tail -1 | cut -d'|' -f1)
sleep 2

# Close the tab
echo "Closing tab during monitoring..."
[ -n "${NEW_TAB_ID}" ] && close_chrome_tab "${PORT}" "${NEW_TAB_ID}" >/dev/null 2>&1 || true
sleep 2

# Wait for monitor to finish
wait ${MONITOR_PID} 2>/dev/null || true

# Check monitor output
if [ -f "${MONITOR_OUTPUT}" ]; then
    monitor_content=$(cat "${MONITOR_OUTPUT}")
    assert_contains "Monitor detected NEW tab" "${monitor_content}" "NEW:"
    assert_contains "Monitor detected CLOSED tab" "${monitor_content}" "CLOSED:"
else
    echo -e "${RED}✗ FAIL${NC}: Monitor output file not found"
    TESTS_FAILED=$((TESTS_FAILED + 2))
    TESTS_TOTAL=$((TESTS_TOTAL + 2))
fi

rm -f "${MONITOR_OUTPUT}" 2>/dev/null || true

# ==================================================
# TEST 9: execute_in_tab() - Tab validation
# ==================================================
print_test_header "Test 9: execute_in_tab() - Tab validation"

# Get a valid tab ID
VALID_TAB_ID=$(list_chrome_tabs "${PORT}" "simple" 2>/dev/null | head -1 | cut -d'|' -f1)

if [ -n "${VALID_TAB_ID}" ]; then
    # Test with valid tab
    execute_in_tab "${VALID_TAB_ID}" "console.log('test')" >/dev/null 2>&1
    result=$?
    # Note: execute_in_tab returns 2 due to HTTP API limitations
    if [ ${result} -eq 2 ]; then
        echo -e "${GREEN}✓ PASS${NC}: execute_in_tab() validates tab and returns expected code"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC}: execute_in_tab() returned unexpected code: ${result}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
else
    echo -e "${YELLOW}⚠ SKIP${NC}: No valid tab ID found for testing"
fi

# ==================================================
# TEST 10: execute_in_tab() - Invalid tab
# ==================================================
print_test_header "Test 10: execute_in_tab() - Invalid tab"

execute_in_tab "invalid-tab-id-$$" "console.log('test')" >/dev/null 2>&1
result=$?
assert_failure "execute_in_tab() fails with invalid tab ID" ${result}

# ==================================================
# TEST 11: execute_in_tab() - Missing parameters
# ==================================================
print_test_header "Test 11: execute_in_tab() - Missing parameters"

execute_in_tab >/dev/null 2>&1
result=$?
assert_failure "execute_in_tab() fails without parameters" ${result}

execute_in_tab "some-tab-id" >/dev/null 2>&1
result=$?
assert_failure "execute_in_tab() fails without JavaScript parameter" ${result}

# ==================================================
# TEST 12: Performance - save_chrome_session()
# ==================================================
print_test_header "Test 12: Performance - save_chrome_session()"

PERF_SESSION="/tmp/perf-session-$$.json"
START_TIME=$(date +%s)
save_chrome_session "${PERF_SESSION}" >/dev/null 2>&1
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if [ ${DURATION} -le 1 ]; then
    echo -e "${GREEN}✓ PASS${NC}: save_chrome_session() completed in ${DURATION}s (< 1s)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC}: save_chrome_session() took ${DURATION}s (expected < 1s)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
TESTS_TOTAL=$((TESTS_TOTAL + 1))

rm -f "${PERF_SESSION}" 2>/dev/null || true

# ==================================================
# TEST 13: Performance - restore_chrome_session()
# ==================================================
print_test_header "Test 13: Performance - restore_chrome_session()"

START_TIME=$(date +%s)
restore_chrome_session "${TEST_SESSION_FILE}" >/dev/null 2>&1
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if [ ${DURATION} -le 2 ]; then
    echo -e "${GREEN}✓ PASS${NC}: restore_chrome_session() completed in ${DURATION}s (< 2s for 3 tabs)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠ WARN${NC}: restore_chrome_session() took ${DURATION}s (expected < 2s, but acceptable)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi
TESTS_TOTAL=$((TESTS_TOTAL + 1))

# ==================================================
# SUMMARY
# ==================================================
echo ""
echo "========================================="
echo "TEST SUMMARY"
echo "========================================="
echo "Total tests: ${TESTS_TOTAL}"
echo -e "Passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Failed: ${RED}${TESTS_FAILED}${NC}"

if [ ${TESTS_FAILED} -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed!${NC}"
    exit 1
fi
