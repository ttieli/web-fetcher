#!/bin/bash
# Health Check Test Suite
# Validates ensure-chrome-debug.sh Phase 2.1 implementation

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HEALTH_CHECK_SCRIPT="${PROJECT_ROOT}/config/ensure-chrome-debug.sh"
PROFILE_DIR="${HOME}/.chrome-wf"

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Test helper functions
test_start() {
    echo -e "${YELLOW}[TEST]${NC} $1"
    TESTS_RUN=$((TESTS_RUN + 1))
}

test_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

test_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

# Ensure Chrome is not running
cleanup_chrome() {
    pkill -f "remote-debugging-port=9222" 2>/dev/null || true
    rm -f "${PROFILE_DIR}/.chrome-debug.pid" 2>/dev/null || true
    sleep 2
}

# Start Chrome in debug mode
start_chrome() {
    local port="${1:-9222}"

    # Ensure profile directory exists
    mkdir -p "${PROFILE_DIR}"

    # Start Chrome
    /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
        --remote-debugging-port="${port}" \
        --user-data-dir="${PROFILE_DIR}" \
        --no-first-run \
        --no-default-browser-check \
        --headless \
        >/dev/null 2>&1 &

    local chrome_pid=$!
    echo "${chrome_pid}" > "${PROFILE_DIR}/.chrome-debug.pid"

    # Wait for Chrome to start
    sleep 3

    echo "${chrome_pid}"
}

# Test 1: Healthy Chrome instance
test_healthy_instance() {
    test_start "Test 1: Healthy Chrome instance detection"

    cleanup_chrome
    local chrome_pid=$(start_chrome 9222)

    # Run health check
    if "${HEALTH_CHECK_SCRIPT}" --quiet; then
        test_pass "Correctly detected healthy Chrome instance"
    else
        test_fail "Failed to detect healthy Chrome instance"
    fi

    # Cleanup
    kill "${chrome_pid}" 2>/dev/null || true
    cleanup_chrome
}

# Test 2: Dead process detection
test_dead_process() {
    test_start "Test 2: Dead process detection"

    cleanup_chrome

    # Create a fake PID file with non-existent process
    mkdir -p "${PROFILE_DIR}"
    echo "999999" > "${PROFILE_DIR}/.chrome-debug.pid"

    # Run health check (should fail)
    if ! "${HEALTH_CHECK_SCRIPT}" --quiet 2>/dev/null; then
        test_pass "Correctly detected dead process"
    else
        test_fail "Failed to detect dead process"
    fi

    cleanup_chrome
}

# Test 3: Port not reachable
test_port_unreachable() {
    test_start "Test 3: Port unreachable detection"

    cleanup_chrome
    local chrome_pid=$(start_chrome 9222)

    # Kill Chrome but leave PID file
    kill "${chrome_pid}" 2>/dev/null || true
    sleep 2

    # Run health check (should fail)
    if ! "${HEALTH_CHECK_SCRIPT}" --quiet 2>/dev/null; then
        test_pass "Correctly detected unreachable port"
    else
        test_fail "Failed to detect unreachable port"
    fi

    cleanup_chrome
}

# Test 4: Invalid parameters
test_invalid_params() {
    test_start "Test 4: Invalid parameter handling"

    # Test invalid port
    if ! "${HEALTH_CHECK_SCRIPT}" --port 99999 2>/dev/null; then
        test_pass "Correctly rejected invalid port"
    else
        test_fail "Failed to reject invalid port"
    fi
}

# Test 5: Quiet mode
test_quiet_mode() {
    test_start "Test 5: Quiet mode operation"

    cleanup_chrome
    local chrome_pid=$(start_chrome 9222)

    # Run health check in quiet mode
    local output=$("${HEALTH_CHECK_SCRIPT}" --quiet 2>&1)

    if [[ -z "${output}" ]]; then
        test_pass "Quiet mode produces no output"
    else
        test_fail "Quiet mode produced output: ${output}"
    fi

    # Cleanup
    kill "${chrome_pid}" 2>/dev/null || true
    cleanup_chrome
}

# Test 6: Custom port and timeout
test_custom_params() {
    test_start "Test 6: Custom port and timeout parameters"

    cleanup_chrome
    local chrome_pid=$(start_chrome 9223)

    # Run health check with custom port
    if "${HEALTH_CHECK_SCRIPT}" --port 9223 --timeout 10 --quiet; then
        test_pass "Custom parameters work correctly"
    else
        test_fail "Failed with custom parameters"
    fi

    # Cleanup
    kill "${chrome_pid}" 2>/dev/null || true
    cleanup_chrome
}

# Test 7: DevTools protocol verification
test_devtools_protocol() {
    test_start "Test 7: DevTools protocol verification"

    cleanup_chrome
    local chrome_pid=$(start_chrome 9222)

    # Verify DevTools endpoint is accessible
    local response=$(curl -s "http://localhost:9222/json/version" 2>/dev/null)

    if [[ -n "${response}" ]] && echo "${response}" | grep -q '"Browser"'; then
        test_pass "DevTools protocol is accessible and valid"
    else
        test_fail "DevTools protocol not accessible or invalid"
    fi

    # Cleanup
    kill "${chrome_pid}" 2>/dev/null || true
    cleanup_chrome
}

# Main test execution
main() {
    echo "========================================"
    echo "Health Check Test Suite"
    echo "Script: ${HEALTH_CHECK_SCRIPT}"
    echo "========================================"
    echo

    # Verify script exists
    if [[ ! -f "${HEALTH_CHECK_SCRIPT}" ]]; then
        echo -e "${RED}[ERROR]${NC} Health check script not found: ${HEALTH_CHECK_SCRIPT}"
        exit 1
    fi

    # Make script executable
    chmod +x "${HEALTH_CHECK_SCRIPT}"

    # Run tests
    test_healthy_instance
    test_dead_process
    test_port_unreachable
    test_invalid_params
    test_quiet_mode
    test_custom_params
    test_devtools_protocol

    # Print summary
    echo
    echo "========================================"
    echo "Test Summary"
    echo "========================================"
    echo -e "Tests Run:    ${TESTS_RUN}"
    echo -e "Tests Passed: ${GREEN}${TESTS_PASSED}${NC}"
    echo -e "Tests Failed: ${RED}${TESTS_FAILED}${NC}"

    if [[ ${TESTS_FAILED} -eq 0 ]]; then
        echo -e "${GREEN}✓ All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}✗ Some tests failed${NC}"
        exit 1
    fi
}

# Run tests
main "$@"