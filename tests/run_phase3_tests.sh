#!/bin/bash
# Phase 3 Integration Test Runner
#
# Master test runner for Phase 3 comprehensive integration tests.
# Runs all integration tests, E2E tests, and generates summary report.
#
# Author: Cody (Claude Code)
# Date: 2025-10-04
# Phase: 3.7 - Master Test Runner

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
INTEGRATION_DIR="${SCRIPT_DIR}/integration"
E2E_DIR="${SCRIPT_DIR}/e2e"
REPORT_FILE="${SCRIPT_DIR}/phase3_test_report_$(date +%Y%m%d_%H%M%S).txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Test results tracking
declare -a TEST_RESULTS
declare -a TEST_NAMES
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Logging functions
log_header() {
    echo -e "\n${BOLD}${CYAN}========================================${NC}"
    echo -e "${BOLD}${CYAN}$*${NC}"
    echo -e "${BOLD}${CYAN}========================================${NC}\n"
}

log_section() {
    echo -e "\n${BOLD}${BLUE}>>> $*${NC}\n"
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_result() {
    local status=$1
    local test_name=$2

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    TEST_NAMES+=("${test_name}")

    case "${status}" in
        PASS)
            echo -e "${GREEN}✓${NC} ${test_name} - PASSED"
            TEST_RESULTS+=("PASS")
            PASSED_TESTS=$((PASSED_TESTS + 1))
            ;;
        FAIL)
            echo -e "${RED}✗${NC} ${test_name} - FAILED"
            TEST_RESULTS+=("FAIL")
            FAILED_TESTS=$((FAILED_TESTS + 1))
            ;;
        SKIP)
            echo -e "${YELLOW}○${NC} ${test_name} - SKIPPED"
            TEST_RESULTS+=("SKIP")
            SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
            ;;
    esac
}

# Cleanup function
cleanup() {
    log_info "Cleaning up test environment..."

    # Kill Chrome debug instances
    if command -v lsof >/dev/null 2>&1; then
        local pids=$(lsof -ti:9222 2>/dev/null || echo "")
        if [[ -n "${pids}" ]]; then
            for pid in ${pids}; do
                kill -9 "${pid}" 2>/dev/null || true
            done
        fi
    fi

    # Clean lock files
    rm -f "${HOME}/.chrome-wf/.chrome-debug.lock" 2>/dev/null || true
    rm -f "${HOME}/.chrome-wf/.chrome-debug.pid" 2>/dev/null || true
}

# Run Python integration tests
run_python_tests() {
    log_section "Running Python Integration Tests"

    cd "${PROJECT_DIR}"

    # Check if pytest is available
    if ! command -v pytest >/dev/null 2>&1; then
        log_warning "pytest not found, trying python -m pytest"

        if ! python3 -m pytest --version >/dev/null 2>&1; then
            log_error "pytest is not installed. Install with: pip install pytest"
            log_result SKIP "Python Integration Tests"
            return 1
        fi
    fi

    # Test 1: Base Integration Test
    log_info "Running: base_integration_test.py"
    if python3 -m pytest "${INTEGRATION_DIR}/base_integration_test.py" -v --tb=short 2>&1 | tee -a "${REPORT_FILE}"; then
        log_result PASS "Base Integration Test"
    else
        log_result FAIL "Base Integration Test"
    fi

    cleanup
    sleep 2

    # Test 2: Auto-Launch Tests
    log_info "Running: test_chrome_auto_launch.py"
    if python3 -m pytest "${INTEGRATION_DIR}/test_chrome_auto_launch.py" -v --tb=short 2>&1 | tee -a "${REPORT_FILE}"; then
        log_result PASS "Auto-Launch Integration Tests"
    else
        log_result FAIL "Auto-Launch Integration Tests"
    fi

    cleanup
    sleep 2

    # Test 3: Fallback Mechanism Tests
    log_info "Running: test_fallback_mechanisms.py"
    if python3 -m pytest "${INTEGRATION_DIR}/test_fallback_mechanisms.py" -v --tb=short 2>&1 | tee -a "${REPORT_FILE}"; then
        log_result PASS "Fallback Mechanism Tests"
    else
        log_result FAIL "Fallback Mechanism Tests"
    fi

    cleanup
    sleep 2

    # Test 4: Concurrent Operations Tests
    log_info "Running: test_concurrent_operations.py"
    if python3 -m pytest "${INTEGRATION_DIR}/test_concurrent_operations.py" -v --tb=short 2>&1 | tee -a "${REPORT_FILE}"; then
        log_result PASS "Concurrent Operations Tests"
    else
        log_result FAIL "Concurrent Operations Tests"
    fi

    cleanup
    sleep 2

    # Test 5: Performance Benchmarks
    log_info "Running: test_performance_benchmarks.py"
    if python3 -m pytest "${INTEGRATION_DIR}/test_performance_benchmarks.py" -v --tb=short 2>&1 | tee -a "${REPORT_FILE}"; then
        log_result PASS "Performance Benchmark Tests"
    else
        log_result FAIL "Performance Benchmark Tests"
    fi

    cleanup
    sleep 2
}

# Run E2E tests
run_e2e_tests() {
    log_section "Running End-to-End Tests"

    # Test 1: Cold Start Workflow
    log_info "Running: test_cold_start_workflow.sh"
    if "${E2E_DIR}/test_cold_start_workflow.sh" 2>&1 | tee -a "${REPORT_FILE}"; then
        log_result PASS "Cold Start Workflow Test"
    else
        log_result FAIL "Cold Start Workflow Test"
    fi

    cleanup
    sleep 2

    # Test 2: Recovery Scenarios
    log_info "Running: test_recovery_scenarios.sh"
    if "${E2E_DIR}/test_recovery_scenarios.sh" 2>&1 | tee -a "${REPORT_FILE}"; then
        log_result PASS "Recovery Scenarios Test"
    else
        log_result FAIL "Recovery Scenarios Test"
    fi

    cleanup
    sleep 2
}

# Generate test report
generate_report() {
    log_section "Generating Test Report"

    local report_content
    report_content=$(cat <<EOF

========================================
Phase 3 Integration Test Report
========================================
Date: $(date '+%Y-%m-%d %H:%M:%S')
Project: Web_Fetcher
Test Suite: Phase 3 - Comprehensive Integration Testing

========================================
Test Summary
========================================
Total Tests:   ${TOTAL_TESTS}
Passed:        ${PASSED_TESTS}
Failed:        ${FAILED_TESTS}
Skipped:       ${SKIPPED_TESTS}

Success Rate:  $(awk "BEGIN {printf \"%.1f\", (${PASSED_TESTS}/${TOTAL_TESTS})*100}")%

========================================
Test Results
========================================
EOF
)

    echo "${report_content}" | tee -a "${REPORT_FILE}"

    # List all test results
    for i in "${!TEST_NAMES[@]}"; do
        local status="${TEST_RESULTS[$i]}"
        local name="${TEST_NAMES[$i]}"

        case "${status}" in
            PASS) echo "✓ ${name}" | tee -a "${REPORT_FILE}" ;;
            FAIL) echo "✗ ${name}" | tee -a "${REPORT_FILE}" ;;
            SKIP) echo "○ ${name}" | tee -a "${REPORT_FILE}" ;;
        esac
    done

    echo "" | tee -a "${REPORT_FILE}"
    echo "========================================" | tee -a "${REPORT_FILE}"
    echo "Report saved to: ${REPORT_FILE}" | tee -a "${REPORT_FILE}"
    echo "========================================" | tee -a "${REPORT_FILE}"
}

# Main execution
main() {
    log_header "Phase 3: Comprehensive Integration Testing"

    # Initialize report file
    echo "Phase 3 Integration Test Execution Log" > "${REPORT_FILE}"
    echo "Started at: $(date)" >> "${REPORT_FILE}"
    echo "========================================" >> "${REPORT_FILE}"
    echo "" >> "${REPORT_FILE}"

    # Pre-flight checks
    log_section "Pre-flight Checks"

    # Check Python
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "python3 not found"
        exit 1
    fi
    log_info "✓ Python 3: $(python3 --version)"

    # Check required Python packages
    if python3 -c "import requests" 2>/dev/null; then
        log_info "✓ requests package available"
    else
        log_warning "requests package not available (some tests may fail)"
    fi

    if python3 -c "import psutil" 2>/dev/null; then
        log_info "✓ psutil package available"
    else
        log_warning "psutil package not available (some tests may fail)"
    fi

    # Check scripts
    if [[ -f "${PROJECT_DIR}/config/ensure-chrome-debug.sh" ]]; then
        log_info "✓ ensure-chrome-debug.sh found"
    else
        log_error "ensure-chrome-debug.sh not found"
        exit 1
    fi

    # Initial cleanup
    cleanup

    # Run test suites
    run_python_tests
    run_e2e_tests

    # Generate final report
    generate_report

    # Final cleanup
    cleanup

    # Exit with appropriate code
    if [[ ${FAILED_TESTS} -eq 0 ]]; then
        log_header "✓ All Phase 3 Tests Completed Successfully!"
        exit 0
    else
        log_header "✗ Some Phase 3 Tests Failed"
        exit 1
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Run main
main "$@"
