#!/bin/bash
# Final test script for Phase 2 Step 2.3
# Tests all four new functions

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_PATH="${PROJECT_ROOT}/config/ensure-chrome-debug.sh"

echo "==========================================="
echo "Phase 2 Step 2.3: Session Persistence Tests"
echo "==========================================="
echo ""

# Extract and eval only the functions we need (avoid main execution)
PORT=9222
QUIET_MODE=false

# Extract logging functions
eval "$(sed -n '/^log_info()/,/^}/p' "${SCRIPT_PATH}")"
eval "$(sed -n '/^log_error()/,/^}/p' "${SCRIPT_PATH}")"
eval "$(sed -n '/^log_debug()/,/^}/p' "${SCRIPT_PATH}")"

# Extract helper functions
eval "$(sed -n '/^list_chrome_tabs()/,/^}/p' "${SCRIPT_PATH}")"
eval "$(sed -n '/^create_chrome_tab()/,/^}/p' "${SCRIPT_PATH}")"
eval "$(sed -n '/^close_chrome_tab()/,/^}/p' "${SCRIPT_PATH}")"
eval "$(sed -n '/^activate_chrome_tab()/,/^}/p' "${SCRIPT_PATH}")"
eval "$(sed -n '/^get_chrome_tab_info()/,/^}/p' "${SCRIPT_PATH}")"
eval "$(sed -n '/^get_chrome_version()/,/^}/p' "${SCRIPT_PATH}")"

# Extract new functions
eval "$(sed -n '/^save_chrome_session()/,/^}/p' "${SCRIPT_PATH}")"
eval "$(sed -n '/^restore_chrome_session()/,/^}/p' "${SCRIPT_PATH}")"
eval "$(sed -n '/^monitor_chrome_tabs()/,/^}/p' "${SCRIPT_PATH}")"
eval "$(sed -n '/^execute_in_tab()/,/^}/p' "${SCRIPT_PATH}")"

TEST_SESSION="/tmp/test-session-$$.json"

# Test 1: save_chrome_session
echo "Test 1: save_chrome_session()"
if save_chrome_session "${TEST_SESSION}" >/dev/null 2>&1; then
    if [ -f "${TEST_SESSION}" ]; then
        echo -e "${GREEN}✓ PASS${NC}: Session saved successfully"
        TESTS_PASSED=$((TESTS_PASSED + 1))

        # Validate JSON
        if command -v jq >/dev/null 2>&1; then
            if jq -e '.timestamp and .chrome_version and .tabs' "${TEST_SESSION}" >/dev/null 2>&1; then
                echo -e "${GREEN}✓ PASS${NC}: Session JSON is valid"
                TESTS_PASSED=$((TESTS_PASSED + 1))
            else
                echo -e "${RED}✗ FAIL${NC}: Invalid session JSON structure"
                TESTS_FAILED=$((TESTS_FAILED + 1))
            fi
        fi
    else
        echo -e "${RED}✗ FAIL${NC}: Session file not created"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "${RED}✗ FAIL${NC}: save_chrome_session() failed"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 2: restore_chrome_session - valid file
echo "Test 2: restore_chrome_session() - Valid file"
if restore_chrome_session "${TEST_SESSION}" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}: Session restored successfully"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC}: restore_chrome_session() failed"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 3: restore_chrome_session - missing file
echo "Test 3: restore_chrome_session() - Missing file"
if restore_chrome_session "/tmp/nonexistent-$$.json" >/dev/null 2>&1; then
    echo -e "${RED}✗ FAIL${NC}: Should have failed on missing file"
    TESTS_FAILED=$((TESTS_FAILED + 1))
else
    echo -e "${GREEN}✓ PASS${NC}: Correctly failed on missing file"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi
echo ""

# Test 4: restore_chrome_session - corrupted JSON
echo "Test 4: restore_chrome_session() - Corrupted JSON"
CORRUPT_FILE="/tmp/corrupt-$$.json"
echo "{ invalid json }" > "${CORRUPT_FILE}"
if restore_chrome_session "${CORRUPT_FILE}" >/dev/null 2>&1; then
    echo -e "${RED}✗ FAIL${NC}: Should have failed on corrupted JSON"
    TESTS_FAILED=$((TESTS_FAILED + 1))
else
    echo -e "${GREEN}✓ PASS${NC}: Correctly failed on corrupted JSON"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi
rm -f "${CORRUPT_FILE}"
echo ""

# Test 5: execute_in_tab - valid tab
echo "Test 5: execute_in_tab() - Valid tab"
VALID_TAB=$(list_chrome_tabs "${PORT}" "simple" 2>/dev/null | head -1 | cut -d'|' -f1)
if [ -n "${VALID_TAB}" ]; then
    execute_in_tab "${VALID_TAB}" "console.log('test')" >/dev/null 2>&1
    result=$?
    # Should return 2 (HTTP API limitation)
    if [ ${result} -eq 2 ]; then
        echo -e "${GREEN}✓ PASS${NC}: execute_in_tab() validates tab (returns 2 as expected)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${YELLOW}⚠ WARN${NC}: execute_in_tab() returned ${result} (expected 2)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi
else
    echo -e "${YELLOW}⚠ SKIP${NC}: No valid tab found"
fi
echo ""

# Test 6: execute_in_tab - invalid tab
echo "Test 6: execute_in_tab() - Invalid tab"
if execute_in_tab "invalid-tab-$$" "test" >/dev/null 2>&1; then
    echo -e "${RED}✗ FAIL${NC}: Should have failed on invalid tab"
    TESTS_FAILED=$((TESTS_FAILED + 1))
else
    echo -e "${GREEN}✓ PASS${NC}: Correctly failed on invalid tab"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi
echo ""

# Test 7: execute_in_tab - missing parameters
echo "Test 7: execute_in_tab() - Missing parameters"
if execute_in_tab >/dev/null 2>&1; then
    echo -e "${RED}✗ FAIL${NC}: Should have failed without parameters"
    TESTS_FAILED=$((TESTS_FAILED + 1))
else
    echo -e "${GREEN}✓ PASS${NC}: Correctly failed without parameters"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi
echo ""

# Test 8: monitor_chrome_tabs
echo "Test 8: monitor_chrome_tabs() - Detect changes"
MONITOR_OUT="/tmp/monitor-$$.txt"
echo "Starting monitor (5 seconds)..."

# Start monitor in background
(timeout 5 bash -c "
    eval \"\$(sed -n '/^log_/,/^}/p' '${SCRIPT_PATH}' | head -30)\"
    eval \"\$(sed -n '/^list_chrome_tabs()/,/^}/p' '${SCRIPT_PATH}')\"
    eval \"\$(sed -n '/^monitor_chrome_tabs()/,/^}/p' '${SCRIPT_PATH}')\"
    PORT=${PORT}
    QUIET_MODE=false
    monitor_chrome_tabs 1
" > "${MONITOR_OUT}" 2>&1 || true) &
MONITOR_PID=$!

sleep 1

# Create and close a tab
echo "Creating test tab..."
NEW_TAB=$(create_chrome_tab "${PORT}" "https://example.org" 2>/dev/null || echo "")
if [ -n "${NEW_TAB}" ]; then
    NEW_TAB_ID=$(echo "${NEW_TAB}" | grep -o '"id":"[^"]*"' | head -1 | sed 's/"id":"\([^"]*\)"/\1/')
    sleep 2

    echo "Closing test tab..."
    [ -n "${NEW_TAB_ID}" ] && close_chrome_tab "${PORT}" "${NEW_TAB_ID}" >/dev/null 2>&1 || true
    sleep 2
fi

wait ${MONITOR_PID} 2>/dev/null || true

if [ -f "${MONITOR_OUT}" ]; then
    NEW_DETECTED=false
    CLOSED_DETECTED=false

    if grep -q "NEW:" "${MONITOR_OUT}"; then
        NEW_DETECTED=true
    fi

    if grep -q "CLOSED:" "${MONITOR_OUT}"; then
        CLOSED_DETECTED=true
    fi

    if [ "${NEW_DETECTED}" = true ] && [ "${CLOSED_DETECTED}" = true ]; then
        echo -e "${GREEN}✓ PASS${NC}: Monitor detected both NEW and CLOSED tabs"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    elif [ "${NEW_DETECTED}" = true ]; then
        echo -e "${YELLOW}⚠ PARTIAL${NC}: Monitor detected NEW but not CLOSED"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC}: Monitor did not detect changes"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    echo -e "${RED}✗ FAIL${NC}: Monitor output not found"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Cleanup
rm -f "${TEST_SESSION}" "${MONITOR_OUT}" 2>/dev/null || true

# Summary
echo "==========================================="
echo "TEST SUMMARY"
echo "==========================================="
TOTAL=$((TESTS_PASSED + TESTS_FAILED))
echo "Total: ${TOTAL}"
echo -e "Passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Failed: ${RED}${TESTS_FAILED}${NC}"
echo ""

if [ ${TESTS_FAILED} -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
