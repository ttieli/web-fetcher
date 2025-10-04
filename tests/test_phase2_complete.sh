#!/bin/bash
# Phase 2 Complete Validation Test Suite
# Tests tail process cleanup and Selenium logging suppression

set -euo pipefail

PROJECT_DIR="/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher"
cd "${PROJECT_DIR}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_test() {
    echo -e "${YELLOW}[TEST]${NC} $*"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $*"
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $*"
}

# Clean up any existing Chrome processes
cleanup() {
    log_test "Cleaning up existing Chrome processes..."
    pkill -f "remote-debugging-port=9222" 2>/dev/null || true
    sleep 1
}

# Test 1: Tail Process Cleanup
test_tail_cleanup() {
    log_test "Test 1: Tail Process Cleanup"
    log_test "Starting Chrome multiple times to verify tail process cleanup..."

    # Start Chrome first time
    ./config/chrome-debug-launcher.sh > /dev/null 2>&1
    sleep 2
    pkill -f "remote-debugging-port=9222" 2>/dev/null || true
    sleep 1

    # Start Chrome second time
    ./config/chrome-debug-launcher.sh > /dev/null 2>&1
    sleep 2
    pkill -f "remote-debugging-port=9222" 2>/dev/null || true
    sleep 1

    # Start Chrome third time
    ./config/chrome-debug-launcher.sh > /dev/null 2>&1
    sleep 2

    # Count tail processes
    tail_count=$(ps aux | grep "tail -f" | grep -v grep | wc -l | tr -d ' ')

    log_test "Current tail processes: ${tail_count}"

    if [[ "${tail_count}" -eq 1 ]]; then
        log_pass "Test 1 PASSED: Only 1 tail process found (expected)"
        return 0
    else
        log_fail "Test 1 FAILED: Found ${tail_count} tail processes (expected 1)"
        ps aux | grep "tail -f" | grep -v grep || true
        return 1
    fi
}

# Test 2: PID File Management
test_pid_file() {
    log_test "Test 2: PID File Management"

    # Ensure Chrome is running
    if ! pgrep -f "remote-debugging-port=9222" > /dev/null 2>&1; then
        ./config/chrome-debug-launcher.sh > /dev/null 2>&1
        sleep 2
    fi

    # Check tail.pid file exists
    if [[ ! -f ~/.chrome-wf/tail.pid ]]; then
        log_fail "Test 2 FAILED: tail.pid file does not exist"
        return 1
    fi

    log_test "tail.pid file found"

    # Verify it contains a valid PID
    tail_pid=$(cat ~/.chrome-wf/tail.pid)

    if [[ -z "${tail_pid}" ]]; then
        log_fail "Test 2 FAILED: tail.pid file is empty"
        return 1
    fi

    log_test "tail.pid contains: ${tail_pid}"

    # Verify PID is valid and process is running
    if ps -p "${tail_pid}" > /dev/null 2>&1; then
        log_pass "Test 2 PASSED: PID ${tail_pid} is valid and process is running"
        ps -p "${tail_pid}" | tail -1
        return 0
    else
        log_fail "Test 2 FAILED: PID ${tail_pid} is not running"
        return 1
    fi
}

# Test 3: Selenium Logging Suppression
test_selenium_logging() {
    log_test "Test 3: Selenium Logging Suppression"

    # Ensure Chrome is running
    if ! pgrep -f "remote-debugging-port=9222" > /dev/null 2>&1; then
        ./config/chrome-debug-launcher.sh > /dev/null 2>&1
        sleep 2
    fi

    log_test "Testing Selenium connection with logging suppression..."

    # Capture output
    output=$(python3 -c "
from selenium_fetcher import SeleniumFetcher
import sys
config = {'debug_port': 9222}
fetcher = SeleniumFetcher(config)
connected, msg = fetcher.connect_to_chrome()
print(f'Connected: {connected}')
fetcher.close()
" 2>&1)

    log_test "Selenium output:"
    echo "${output}"

    # Check for unwanted logging messages
    if echo "${output}" | grep -qiE "(DevTools|ChromeDriver|selenium\..*WARNING)"; then
        log_fail "Test 3 FAILED: Found unwanted logging messages"
        return 1
    else
        log_pass "Test 3 PASSED: Clean output, no unwanted logging messages"
        return 0
    fi
}

# Test 4: Integration Test
test_integration() {
    log_test "Test 4: Integration Test (Full Workflow)"

    # Clean up first
    cleanup
    sleep 1

    log_test "Running full fetch workflow..."

    # Capture output
    output=$(python3 wf.py --fetch-mode selenium https://example.com 2>&1 || true)

    log_test "Full workflow output:"
    echo "${output}"

    # Check for successful fetch
    if echo "${output}" | grep -qi "success\|fetched\|completed"; then
        log_pass "Test 4 PASSED: Full workflow completed successfully"

        # Check for clean output
        if echo "${output}" | grep -qiE "(allocator multiple times|DEPRECATED_ENDPOINT|TensorFlow)"; then
            log_fail "Test 4 WARNING: Found suppressed error messages in output"
            return 1
        else
            log_pass "Test 4 PASSED: Clean console output confirmed"
            return 0
        fi
    else
        log_fail "Test 4 FAILED: Workflow did not complete successfully"
        return 1
    fi
}

# Main test execution
main() {
    echo "========================================="
    echo "Phase 2 Complete Validation Test Suite"
    echo "========================================="
    echo ""

    # Clean up before tests
    cleanup

    # Run all tests
    test_results=()

    if test_tail_cleanup; then
        test_results+=("Test 1: PASS")
    else
        test_results+=("Test 1: FAIL")
    fi
    echo ""

    if test_pid_file; then
        test_results+=("Test 2: PASS")
    else
        test_results+=("Test 2: FAIL")
    fi
    echo ""

    if test_selenium_logging; then
        test_results+=("Test 3: PASS")
    else
        test_results+=("Test 3: FAIL")
    fi
    echo ""

    if test_integration; then
        test_results+=("Test 4: PASS")
    else
        test_results+=("Test 4: FAIL")
    fi
    echo ""

    # Summary
    echo "========================================="
    echo "Test Summary:"
    echo "========================================="
    for result in "${test_results[@]}"; do
        if echo "${result}" | grep -q "PASS"; then
            log_pass "${result}"
        else
            log_fail "${result}"
        fi
    done
    echo ""

    # Final cleanup
    cleanup

    # Check overall result
    if printf '%s\n' "${test_results[@]}" | grep -q "FAIL"; then
        log_fail "Some tests FAILED"
        exit 1
    else
        log_pass "All tests PASSED!"
        exit 0
    fi
}

# Execute main
main "$@"
