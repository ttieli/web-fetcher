#!/bin/bash
# Simple test script for Phase 2 Step 2.3: Session Persistence and State Management
# Tests the four new functions without triggering main script execution

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"
ENSURE_CHROME_SCRIPT="${PROJECT_ROOT}/config/ensure-chrome-debug.sh"

# Test session file
TEST_SESSION_FILE="/tmp/test-chrome-session-$$.json"

echo "========================================="
echo "Phase 2 Step 2.3: Session Persistence Tests"
echo "========================================="
echo ""

# Source the script functions without executing main
# We do this by temporarily renaming main function
if [ ! -f "${ENSURE_CHROME_SCRIPT}" ]; then
    echo -e "${RED}Error: Script not found: ${ENSURE_CHROME_SCRIPT}${NC}"
    exit 1
fi

# Create a temporary modified script that doesn't auto-execute
TEMP_SCRIPT="/tmp/ensure-chrome-debug-no-main-$$.sh"
sed 's/^main "\$@"$/# main disabled for testing/' "${ENSURE_CHROME_SCRIPT}" > "${TEMP_SCRIPT}"

# Source the temp script
source "${TEMP_SCRIPT}"

# Set port
PORT="${PORT:-9222}"
export DEBUG=1

echo "Test 1: Checking Chrome is running in debug mode..."
if check_chrome_debug_mode "${PORT}" >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Chrome is running in debug mode"
else
    echo -e "${RED}✗${NC} Chrome is not running in debug mode"
    echo "Please start Chrome in debug mode first"
    rm -f "${TEMP_SCRIPT}"
    exit 1
fi
echo ""

# ==================================================
# TEST 1: save_chrome_session()
# ==================================================
echo "Test 2: save_chrome_session() - Save current session"
echo "Creating test tabs..."
create_chrome_tab "${PORT}" "https://example.com" >/dev/null 2>&1 || true
create_chrome_tab "${PORT}" "https://www.google.com" >/dev/null 2>&1 || true
create_chrome_tab "${PORT}" "https://github.com" >/dev/null 2>&1 || true
sleep 1

if save_chrome_session "${TEST_SESSION_FILE}" >/dev/null 2>&1; then
    if [ -f "${TEST_SESSION_FILE}" ]; then
        echo -e "${GREEN}✓${NC} Session saved successfully to: ${TEST_SESSION_FILE}"
        TESTS_PASSED=$((TESTS_PASSED + 1))

        # Validate JSON
        if command -v jq >/dev/null 2>&1; then
            if jq -e '.timestamp' "${TEST_SESSION_FILE}" >/dev/null 2>&1; then
                echo -e "${GREEN}✓${NC} Session JSON is valid and contains timestamp"
                TESTS_PASSED=$((TESTS_PASSED + 1))
            else
                echo -e "${RED}✗${NC} Session JSON is missing timestamp"
                TESTS_FAILED=$((TESTS_FAILED + 1))
            fi

            tab_count=$(jq '.tabs | length' "${TEST_SESSION_FILE}" 2>/dev/null)
            if [ "${tab_count}" -ge 3 ]; then
                echo -e "${GREEN}✓${NC} Session contains ${tab_count} tabs"
                TESTS_PASSED=$((TESTS_PASSED + 1))
            else
                echo -e "${RED}✗${NC} Session contains only ${tab_count} tabs (expected >= 3)"
                TESTS_FAILED=$((TESTS_FAILED + 1))
            fi
        fi
    else
        echo -e "${RED}✗${NC} Session file was not created"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "${RED}✗${NC} save_chrome_session() failed"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# ==================================================
# TEST 2: restore_chrome_session()
# ==================================================
echo "Test 3: restore_chrome_session() - Restore session"
echo "Closing non-essential tabs..."
tabs=$(list_chrome_tabs "${PORT}" "simple" 2>/dev/null)
echo "${tabs}" | tail -n +2 | while IFS='|' read -r id title url type; do
    [ -n "${id}" ] && close_chrome_tab "${PORT}" "${id}" >/dev/null 2>&1 || true
done
sleep 1

if restore_chrome_session "${TEST_SESSION_FILE}" >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Session restored successfully"
    TESTS_PASSED=$((TESTS_PASSED + 1))

    # Check tab count
    sleep 1
    new_tabs=$(list_chrome_tabs "${PORT}" "simple" 2>/dev/null)
    new_tab_count=$(echo "${new_tabs}" | wc -l | tr -d ' ')

    if [ ${new_tab_count} -ge 3 ]; then
        echo -e "${GREEN}✓${NC} Restored ${new_tab_count} tabs"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} Only ${new_tab_count} tabs after restore"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "${RED}✗${NC} restore_chrome_session() failed"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# ==================================================
# TEST 3: restore_chrome_session() - Invalid file
# ==================================================
echo "Test 4: restore_chrome_session() - Handle missing file"
if restore_chrome_session "/tmp/nonexistent-$$.json" >/dev/null 2>&1; then
    echo -e "${RED}✗${NC} Should have failed on missing file"
    TESTS_FAILED=$((TESTS_FAILED + 1))
else
    echo -e "${GREEN}✓${NC} Correctly failed on missing file"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi
echo ""

# ==================================================
# TEST 4: execute_in_tab()
# ==================================================
echo "Test 5: execute_in_tab() - Validate tab exists"
VALID_TAB_ID=$(list_chrome_tabs "${PORT}" "simple" 2>/dev/null | head -1 | cut -d'|' -f1)

if [ -n "${VALID_TAB_ID}" ]; then
    # Should return 2 (execution limitation)
    execute_in_tab "${VALID_TAB_ID}" "console.log('test')" >/dev/null 2>&1
    result=$?
    if [ ${result} -eq 2 ]; then
        echo -e "${GREEN}✓${NC} execute_in_tab() validates tab and returns expected code (2)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} execute_in_tab() returned unexpected code: ${result}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "${YELLOW}⚠${NC} No valid tab ID found for testing"
fi
echo ""

# ==================================================
# TEST 5: execute_in_tab() - Invalid tab
# ==================================================
echo "Test 6: execute_in_tab() - Handle invalid tab"
if execute_in_tab "invalid-tab-id-$$" "console.log('test')" >/dev/null 2>&1; then
    echo -e "${RED}✗${NC} Should have failed on invalid tab"
    TESTS_FAILED=$((TESTS_FAILED + 1))
else
    echo -e "${GREEN}✓${NC} Correctly failed on invalid tab"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi
echo ""

# ==================================================
# TEST 6: monitor_chrome_tabs() - Basic test
# ==================================================
echo "Test 7: monitor_chrome_tabs() - Detect changes"
MONITOR_OUTPUT="/tmp/monitor-output-$$.txt"

echo "Starting monitor for 5 seconds..."
(timeout 5 bash -c "source '${TEMP_SCRIPT}'; export PORT=${PORT}; monitor_chrome_tabs 1" > "${MONITOR_OUTPUT}" 2>&1 || true) &
MONITOR_PID=$!
sleep 1

echo "Creating new tab..."
NEW_TAB=$(create_chrome_tab "${PORT}" "https://example.org" 2>/dev/null)
NEW_TAB_ID=$(echo "${NEW_TAB}" | grep -o '"id":"[^"]*"' | head -1 | sed 's/"id":"\([^"]*\)"/\1/')
sleep 2

echo "Closing tab..."
[ -n "${NEW_TAB_ID}" ] && close_chrome_tab "${PORT}" "${NEW_TAB_ID}" >/dev/null 2>&1 || true
sleep 2

wait ${MONITOR_PID} 2>/dev/null || true

if [ -f "${MONITOR_OUTPUT}" ]; then
    if grep -q "NEW:" "${MONITOR_OUTPUT}"; then
        echo -e "${GREEN}✓${NC} Monitor detected NEW tab"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} Monitor did not detect NEW tab"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi

    if grep -q "CLOSED:" "${MONITOR_OUTPUT}"; then
        echo -e "${GREEN}✓${NC} Monitor detected CLOSED tab"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} Monitor did not detect CLOSED tab"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "${RED}✗${NC} Monitor output file not found"
    TESTS_FAILED=$((TESTS_FAILED + 2))
fi
echo ""

# Cleanup
echo "Cleaning up..."
rm -f "${TEST_SESSION_FILE}" "${MONITOR_OUTPUT}" "${TEMP_SCRIPT}" 2>/dev/null || true

# Summary
echo "========================================="
echo "TEST SUMMARY"
echo "========================================="
TOTAL=$((TESTS_PASSED + TESTS_FAILED))
echo "Total tests: ${TOTAL}"
echo -e "Passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Failed: ${RED}${TESTS_FAILED}${NC}"
echo ""

if [ ${TESTS_FAILED} -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed!${NC}"
    exit 1
fi
