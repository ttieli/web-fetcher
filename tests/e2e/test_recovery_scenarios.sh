#!/bin/bash
# End-to-End Test: Recovery Scenarios
#
# Tests recovery from various failure scenarios:
# 1. Chrome crash during fetch
# 2. Port conflict recovery
# 3. Permission error handling
#
# Author: Cody (Claude Code)
# Date: 2025-10-04
# Phase: 3.6 - E2E Recovery Testing

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENSURE_SCRIPT="${PROJECT_DIR}/config/ensure-chrome-debug.sh"
LAUNCHER_SCRIPT="${PROJECT_DIR}/config/chrome-debug-launcher.sh"
DEBUG_PORT=9222
PROFILE_DIR="${HOME}/.chrome-wf"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_test() {
    echo -e "${BLUE}[TEST]${NC} $*"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."

    # Kill Chrome debug instances
    if command -v lsof >/dev/null 2>&1; then
        local pids=$(lsof -ti:${DEBUG_PORT} 2>/dev/null || echo "")
        if [[ -n "${pids}" ]]; then
            for pid in ${pids}; do
                kill -9 "${pid}" 2>/dev/null || true
            done
        fi
    fi

    # Clean lock files
    rm -f "${PROFILE_DIR}/.chrome-debug.lock" 2>/dev/null || true
    rm -f "${PROFILE_DIR}/.chrome-debug.pid" 2>/dev/null || true
}

# Test 1: Chrome crash recovery
test_chrome_crash_recovery() {
    log_test "Test 1: Chrome crash during operation"

    # Start Chrome
    log_info "Starting Chrome..."
    local chrome_pid
    chrome_pid=$("${LAUNCHER_SCRIPT}" 2>/dev/null || echo "")

    if [[ -z "${chrome_pid}" ]]; then
        log_error "Failed to start Chrome"
        return 1
    fi

    log_info "Chrome started with PID: ${chrome_pid}"

    # Wait for Chrome to be ready
    sleep 2

    # Verify Chrome is accessible
    if curl -s --max-time 3 "http://localhost:${DEBUG_PORT}/json/version" >/dev/null 2>&1; then
        log_info "✓ Chrome is accessible"
    else
        log_error "Chrome not accessible"
        return 1
    fi

    # Simulate crash by killing Chrome with SIGKILL
    log_info "Simulating Chrome crash (kill -9)..."
    kill -9 "${chrome_pid}" 2>/dev/null || true
    sleep 1

    # Verify Chrome is down
    if ! kill -0 "${chrome_pid}" 2>/dev/null; then
        log_info "✓ Chrome process terminated"
    fi

    # Try to recover using ensure-chrome-debug
    log_info "Attempting recovery..."
    if "${ENSURE_SCRIPT}" --port "${DEBUG_PORT}" --timeout 10; then
        log_info "✓ Recovery successful"

        # Verify Chrome is running again
        if curl -s --max-time 3 "http://localhost:${DEBUG_PORT}/json/version" >/dev/null 2>&1; then
            log_info "✓ Chrome is accessible after recovery"
            return 0
        else
            log_error "Chrome not accessible after recovery"
            return 1
        fi
    else
        log_error "Recovery failed"
        return 1
    fi
}

# Test 2: Port conflict recovery
test_port_conflict_recovery() {
    log_test "Test 2: Port conflict recovery"

    # Kill any existing Chrome on the port
    cleanup

    # Start a dummy server on the debug port to create conflict
    log_info "Creating port conflict on ${DEBUG_PORT}..."

    # Use nc (netcat) to occupy the port
    if command -v nc >/dev/null 2>&1; then
        # Start nc in background to listen on port
        nc -l "${DEBUG_PORT}" >/dev/null 2>&1 &
        local nc_pid=$!
        sleep 1

        log_info "Port ${DEBUG_PORT} occupied by PID: ${nc_pid}"

        # Try to start Chrome (should detect conflict)
        log_info "Attempting to start Chrome with port conflict..."

        if "${ENSURE_SCRIPT}" --port "${DEBUG_PORT}" --diagnose 2>&1 | grep -q "Port occupied"; then
            log_info "✓ Port conflict detected correctly"

            # Kill the dummy server
            kill -9 "${nc_pid}" 2>/dev/null || true
            sleep 1

            # Try recovery
            log_info "Attempting recovery after clearing port..."
            if "${ENSURE_SCRIPT}" --port "${DEBUG_PORT}" --timeout 10; then
                log_info "✓ Recovery successful after port cleared"
                return 0
            else
                log_error "Recovery failed after port cleared"
                return 1
            fi
        else
            # Kill the dummy server
            kill -9 "${nc_pid}" 2>/dev/null || true
            log_warning "Port conflict not detected as expected"
            return 1
        fi
    else
        log_warning "nc (netcat) not available, skipping port conflict test"
        return 0
    fi
}

# Test 3: Permission error handling
test_permission_error_handling() {
    log_test "Test 3: Permission error handling"

    # Backup launcher script permissions
    local launcher_mode
    launcher_mode=$(stat -f "%Lp" "${LAUNCHER_SCRIPT}" 2>/dev/null || echo "755")

    # Remove execute permission
    log_info "Removing execute permission from launcher..."
    chmod -x "${LAUNCHER_SCRIPT}"

    # Try to ensure Chrome (should fail with permission error)
    log_info "Attempting to start Chrome without execute permission..."

    local result_code=0
    local result_output
    result_output=$("${ENSURE_SCRIPT}" --port "${DEBUG_PORT}" --timeout 5 2>&1 || echo "FAILED")
    result_code=$?

    # Check for permission-related error
    if echo "${result_output}" | grep -qi "permission\|executable\|denied"; then
        log_info "✓ Permission error detected correctly"
        log_info "Error message: ${result_output}"

        # Restore permissions
        chmod "${launcher_mode}" "${LAUNCHER_SCRIPT}"
        log_info "✓ Permissions restored"

        # Verify recovery works now
        if "${ENSURE_SCRIPT}" --port "${DEBUG_PORT}" --timeout 10; then
            log_info "✓ Works correctly after permission restore"
            return 0
        else
            log_error "Failed after permission restore"
            return 1
        fi
    else
        # Restore permissions anyway
        chmod "${launcher_mode}" "${LAUNCHER_SCRIPT}"
        log_warning "Expected permission error not detected"
        log_info "Output: ${result_output}"
        return 1
    fi
}

# Main test execution
main() {
    log_info "=== E2E Recovery Scenarios Test Suite ==="

    local total_tests=0
    local passed_tests=0
    local failed_tests=0

    # Clean start
    cleanup
    sleep 1

    # Test 1: Chrome crash recovery
    total_tests=$((total_tests + 1))
    if test_chrome_crash_recovery; then
        passed_tests=$((passed_tests + 1))
        log_info "✓ Test 1 PASSED"
    else
        failed_tests=$((failed_tests + 1))
        log_error "✗ Test 1 FAILED"
    fi
    cleanup
    sleep 1

    # Test 2: Port conflict recovery
    total_tests=$((total_tests + 1))
    if test_port_conflict_recovery; then
        passed_tests=$((passed_tests + 1))
        log_info "✓ Test 2 PASSED"
    else
        failed_tests=$((failed_tests + 1))
        log_error "✗ Test 2 FAILED"
    fi
    cleanup
    sleep 1

    # Test 3: Permission error handling
    total_tests=$((total_tests + 1))
    if test_permission_error_handling; then
        passed_tests=$((passed_tests + 1))
        log_info "✓ Test 3 PASSED"
    else
        failed_tests=$((failed_tests + 1))
        log_error "✗ Test 3 FAILED"
    fi
    cleanup

    # Summary
    echo ""
    log_info "=== Test Summary ==="
    log_info "Total tests: ${total_tests}"
    log_info "Passed: ${passed_tests}"
    log_info "Failed: ${failed_tests}"

    if [[ ${failed_tests} -eq 0 ]]; then
        log_info "✓ All recovery scenario tests PASSED"
        return 0
    else
        log_error "✗ Some recovery scenario tests FAILED"
        return 1
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Run main
main "$@"
