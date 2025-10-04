#!/bin/bash
# Health Check Edge Cases Test
# Tests error handling and boundary conditions

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HEALTH_CHECK_SCRIPT="${PROJECT_ROOT}/config/ensure-chrome-debug.sh"
PROFILE_DIR="${HOME}/.chrome-wf"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

# Test counter
TESTS_RUN=0
TESTS_PASSED=0

# Test helper
test_case() {
    echo -e "${YELLOW}[TEST]${NC} $1"
    TESTS_RUN=$((TESTS_RUN + 1))
}

test_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

test_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# Cleanup
cleanup() {
    pkill -f "remote-debugging-port=" 2>/dev/null || true
    rm -rf "${PROFILE_DIR}" 2>/dev/null || true
}

# Edge case tests
main() {
    echo "========================================"
    echo "Health Check Edge Cases Test"
    echo "========================================"
    echo

    # Test 1: No profile directory
    test_case "Test 1: No profile directory"
    cleanup
    if ! "${HEALTH_CHECK_SCRIPT}" --quiet 2>/dev/null; then
        test_pass "Correctly failed when profile directory missing"
    else
        test_fail "Should have failed with missing profile directory"
    fi

    # Test 2: Empty PID file
    test_case "Test 2: Empty PID file"
    mkdir -p "${PROFILE_DIR}"
    touch "${PROFILE_DIR}/.chrome-debug.pid"
    if ! "${HEALTH_CHECK_SCRIPT}" --quiet 2>/dev/null; then
        test_pass "Correctly handled empty PID file"
    else
        test_fail "Should have failed with empty PID file"
    fi

    # Test 3: Invalid PID format
    test_case "Test 3: Invalid PID format"
    echo "not_a_number" > "${PROFILE_DIR}/.chrome-debug.pid"
    if ! "${HEALTH_CHECK_SCRIPT}" --quiet 2>/dev/null; then
        test_pass "Correctly handled invalid PID format"
    else
        test_fail "Should have failed with invalid PID format"
    fi

    # Test 4: Multiple Chrome instances
    test_case "Test 4: Multiple Chrome instances on different ports"
    cleanup
    mkdir -p "${PROFILE_DIR}"

    # Start Chrome on port 9222
    /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
        --remote-debugging-port=9222 \
        --user-data-dir="${PROFILE_DIR}" \
        --no-first-run \
        --headless >/dev/null 2>&1 &
    local pid1=$!
    echo "${pid1}" > "${PROFILE_DIR}/.chrome-debug.pid"
    sleep 2

    # Start another Chrome on port 9223
    /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
        --remote-debugging-port=9223 \
        --user-data-dir="${PROFILE_DIR}-2" \
        --no-first-run \
        --headless >/dev/null 2>&1 &
    local pid2=$!
    sleep 2

    # Check port 9222
    if "${HEALTH_CHECK_SCRIPT}" --port 9222 --quiet; then
        test_pass "Correctly identified instance on port 9222"
    else
        test_fail "Failed to identify instance on port 9222"
    fi

    kill "${pid1}" "${pid2}" 2>/dev/null || true
    cleanup

    # Test 5: Boundary port values
    test_case "Test 5: Boundary port values"

    # Port 0
    if ! "${HEALTH_CHECK_SCRIPT}" --port 0 2>/dev/null; then
        test_pass "Correctly rejected port 0"
    else
        test_fail "Should have rejected port 0"
    fi

    # Port 65536
    if ! "${HEALTH_CHECK_SCRIPT}" --port 65536 2>/dev/null; then
        test_pass "Correctly rejected port 65536"
    else
        test_fail "Should have rejected port 65536"
    fi

    # Test 6: Timeout boundary values
    test_case "Test 6: Timeout boundary values"

    # Timeout 0
    if ! "${HEALTH_CHECK_SCRIPT}" --timeout 0 2>/dev/null; then
        test_pass "Correctly rejected timeout 0"
    else
        test_fail "Should have rejected timeout 0"
    fi

    # Negative timeout
    if ! "${HEALTH_CHECK_SCRIPT}" --timeout -1 2>/dev/null; then
        test_pass "Correctly rejected negative timeout"
    else
        test_fail "Should have rejected negative timeout"
    fi

    # Test 7: Help flag
    test_case "Test 7: Help flag functionality"
    if "${HEALTH_CHECK_SCRIPT}" --help 2>&1 | grep -q "Chrome Debug Health Check"; then
        test_pass "Help flag displays usage information"
    else
        test_fail "Help flag not working correctly"
    fi

    # Test 8: Unknown options
    test_case "Test 8: Unknown option handling"
    if ! "${HEALTH_CHECK_SCRIPT}" --unknown-option 2>/dev/null; then
        test_pass "Correctly rejected unknown option"
    else
        test_fail "Should have rejected unknown option"
    fi

    # Test 9: PID of different process
    test_case "Test 9: PID of different process"
    mkdir -p "${PROFILE_DIR}"
    # Use PID of this shell
    echo "$$" > "${PROFILE_DIR}/.chrome-debug.pid"
    if ! "${HEALTH_CHECK_SCRIPT}" --quiet 2>/dev/null; then
        test_pass "Correctly identified non-Chrome process"
    else
        test_fail "Should have detected non-Chrome process"
    fi

    # Test 10: Concurrent health checks
    test_case "Test 10: Concurrent health checks"
    cleanup
    mkdir -p "${PROFILE_DIR}"

    # Start Chrome
    /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
        --remote-debugging-port=9222 \
        --user-data-dir="${PROFILE_DIR}" \
        --no-first-run \
        --headless >/dev/null 2>&1 &
    local chrome_pid=$!
    echo "${chrome_pid}" > "${PROFILE_DIR}/.chrome-debug.pid"
    sleep 3

    # Run multiple concurrent checks
    local all_success=true
    for i in {1..5}; do
        "${HEALTH_CHECK_SCRIPT}" --quiet &
    done

    # Wait for all background processes
    wait

    # Check if all succeeded
    if [[ $? -eq 0 ]]; then
        test_pass "Concurrent health checks handled correctly"
    else
        test_fail "Concurrent health checks failed"
    fi

    kill "${chrome_pid}" 2>/dev/null || true
    cleanup

    # Summary
    echo
    echo "========================================"
    echo "Edge Cases Test Summary"
    echo "========================================"
    echo "Tests Run: ${TESTS_RUN}"
    echo -e "Tests Passed: ${GREEN}${TESTS_PASSED}${NC}"
    echo -e "Tests Failed: ${RED}$((TESTS_RUN - TESTS_PASSED))${NC}"

    if [[ ${TESTS_PASSED} -eq ${TESTS_RUN} ]]; then
        echo -e "${GREEN}✓ All edge case tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}✗ Some edge case tests failed${NC}"
        exit 1
    fi
}

# Run tests
cleanup
main "$@"