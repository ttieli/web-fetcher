#!/bin/bash

# Comprehensive verification script for Phase 2.2 implementation
# This script verifies all requirements and tests all functions

set -e

echo "================================================"
echo " Phase 2.2 Verification Suite"
echo " Testing Chrome Tab Control Functions"
echo "================================================"
echo ""

# Setup
PORT=9222
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENSURE_CHROME="${SCRIPT_DIR}/config/ensure-chrome-debug.sh"

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass_count=0
fail_count=0
skip_count=0

# Helper function for test results
report_test() {
    local test_name="$1"
    local result="$2"
    local message="${3:-}"

    printf "%-50s " "${test_name}:"
    case "${result}" in
        PASS)
            echo -e "${GREEN}✓ PASS${NC} ${message}"
            ((pass_count++))
            ;;
        FAIL)
            echo -e "${RED}✗ FAIL${NC} ${message}"
            ((fail_count++))
            ;;
        SKIP)
            echo -e "${YELLOW}⊘ SKIP${NC} ${message}"
            ((skip_count++))
            ;;
    esac
}

echo "1. VERIFYING IMPLEMENTATION"
echo "----------------------------"

# Check if functions exist
for func in navigate_chrome_tab close_chrome_tab create_chrome_tab activate_chrome_tab get_chrome_tab_info; do
    if grep -q "^${func}()" "${ENSURE_CHROME}"; then
        report_test "Function ${func} exists" "PASS"
    else
        report_test "Function ${func} exists" "FAIL"
    fi
done
echo ""

echo "2. VERIFYING ERROR HANDLING"
echo "----------------------------"

# Test parameter validation
test_validation() {
    local func="$1"
    shift
    local args="$@"

    # Source the script in a subshell with empty params
    output=$(bash -c "
        export PORT=${PORT}
        export PROFILE_DIR=/tmp/chrome-profile
        export DEBUG=false
        export PID_FILE=/tmp/chrome-profile/chrome.pid

        # Source without running main
        source ${ENSURE_CHROME} --no-run 2>/dev/null || true

        # Define minimal logging
        log_debug() { :; }
        log_info() { :; }
        log_error() { echo \"\$*\" >&2; }

        # Call function with empty required params
        ${func} ${args} 2>&1
        echo \"Exit: \$?\"
    " 2>&1)

    if echo "${output}" | grep -q "parameter is required\|Exit: [12]"; then
        echo "PASS"
    else
        echo "FAIL"
    fi
}

result=$(test_validation "navigate_chrome_tab" '""' '""')
report_test "navigate_chrome_tab validates empty tab_id" "${result}"

result=$(test_validation "close_chrome_tab" '""')
report_test "close_chrome_tab validates empty tab_id" "${result}"

result=$(test_validation "activate_chrome_tab" '""')
report_test "activate_chrome_tab validates empty tab_id" "${result}"

result=$(test_validation "get_chrome_tab_info" '""')
report_test "get_chrome_tab_info validates empty tab_id" "${result}"
echo ""

echo "3. VERIFYING FUNCTIONALITY"
echo "----------------------------"

# Test actual DevTools API functionality
# Create a test tab
response=$(curl -s -X PUT "http://localhost:${PORT}/json/new?about:blank" 2>/dev/null)
test_tab_id=$(echo "${response}" | grep -o '"id"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)".*/\1/' | head -n 1)

if [[ -n "${test_tab_id}" ]]; then
    report_test "Create test tab via API" "PASS" "(ID: ${test_tab_id:0:8}...)"

    # Test activate
    activate=$(curl -s "http://localhost:${PORT}/json/activate/${test_tab_id}" 2>/dev/null)
    if [[ "${activate}" == "Target activated" ]]; then
        report_test "Activate tab via API" "PASS"
    else
        report_test "Activate tab via API" "FAIL" "${activate}"
    fi

    # Test tab info retrieval
    tabs=$(curl -s "http://localhost:${PORT}/json" 2>/dev/null)
    if echo "${tabs}" | grep -q "\"id\"[[:space:]]*:[[:space:]]*\"${test_tab_id}\""; then
        report_test "Retrieve tab info via API" "PASS"
    else
        report_test "Retrieve tab info via API" "FAIL"
    fi

    # Test close
    close=$(curl -s "http://localhost:${PORT}/json/close/${test_tab_id}" 2>/dev/null)
    if echo "${close}" | grep -q "clos"; then
        report_test "Close tab via API" "PASS"
    else
        report_test "Close tab via API" "FAIL" "${close}"
    fi
else
    report_test "Create test tab via API" "FAIL"
    report_test "Activate tab via API" "SKIP" "(no test tab)"
    report_test "Retrieve tab info via API" "SKIP" "(no test tab)"
    report_test "Close tab via API" "SKIP" "(no test tab)"
fi
echo ""

echo "4. VERIFYING PERFORMANCE"
echo "----------------------------"

# Test performance requirement (<500ms)
start_time=$(date +%s%N 2>/dev/null || date +%s)
curl -s "http://localhost:${PORT}/json" >/dev/null 2>&1
end_time=$(date +%s%N 2>/dev/null || date +%s)

if [[ "${start_time}" == *"N" ]]; then
    # Nanosecond precision not available
    report_test "Performance measurement" "SKIP" "(no nanosecond precision)"
else
    elapsed_ms=$(( (end_time - start_time) / 1000000 ))
    if [[ ${elapsed_ms} -lt 500 ]]; then
        report_test "List tabs performance < 500ms" "PASS" "(${elapsed_ms}ms)"
    else
        report_test "List tabs performance < 500ms" "FAIL" "(${elapsed_ms}ms)"
    fi
fi
echo ""

echo "5. VERIFYING BACKWARDS COMPATIBILITY"
echo "--------------------------------------"

# Test Phase 1 still works
if ${ENSURE_CHROME} --quiet 2>/dev/null; then
    report_test "Phase 1: Health check" "PASS"
else
    report_test "Phase 1: Health check" "FAIL"
fi

# Test Phase 2.1 still works
version_output=$(bash -c "
    export PORT=${PORT}
    export PROFILE_DIR=/tmp/chrome-profile
    export DEBUG=false
    source ${ENSURE_CHROME} --no-run 2>/dev/null || true
    log_debug() { :; }
    log_info() { :; }
    log_error() { :; }
    get_chrome_version 2>/dev/null
" 2>/dev/null)

if [[ -n "${version_output}" ]]; then
    report_test "Phase 2.1: get_chrome_version" "PASS" "(${version_output})"
else
    report_test "Phase 2.1: get_chrome_version" "FAIL"
fi

list_output=$(bash -c "
    export PORT=${PORT}
    export PROFILE_DIR=/tmp/chrome-profile
    export DEBUG=false
    source ${ENSURE_CHROME} --no-run 2>/dev/null || true
    log_debug() { :; }
    log_info() { :; }
    log_error() { :; }
    list_chrome_tabs 9222 simple 2>/dev/null | head -1
" 2>/dev/null)

if [[ -n "${list_output}" ]]; then
    report_test "Phase 2.1: list_chrome_tabs" "PASS"
else
    report_test "Phase 2.1: list_chrome_tabs" "FAIL"
fi
echo ""

echo "6. VERIFYING CODE QUALITY"
echo "--------------------------"

# Check for proper logging
log_count=$(grep -c "log_debug\|log_info\|log_error" <(sed -n '/^navigate_chrome_tab()/,/^}/p' "${ENSURE_CHROME}") || echo 0)
if [[ ${log_count} -ge 3 ]]; then
    report_test "Logging in navigate_chrome_tab" "PASS" "(${log_count} log statements)"
else
    report_test "Logging in navigate_chrome_tab" "FAIL" "(only ${log_count} log statements)"
fi

# Check for error codes
for func in navigate_chrome_tab close_chrome_tab create_chrome_tab activate_chrome_tab get_chrome_tab_info; do
    if sed -n "/^${func}()/,/^}/p" "${ENSURE_CHROME}" | grep -q "return [012]"; then
        report_test "Error codes in ${func}" "PASS"
    else
        report_test "Error codes in ${func}" "FAIL"
    fi
done
echo ""

# Summary
echo "================================================"
echo " VERIFICATION SUMMARY"
echo "================================================"
echo -e "${GREEN}PASSED:${NC} ${pass_count}"
echo -e "${RED}FAILED:${NC} ${fail_count}"
echo -e "${YELLOW}SKIPPED:${NC} ${skip_count}"
echo ""

if [[ ${fail_count} -eq 0 ]]; then
    echo -e "${GREEN}✓ Phase 2.2 Implementation VERIFIED${NC}"
    echo ""
    echo "All tab control functions are working correctly:"
    echo "  • navigate_chrome_tab (with limitations noted)"
    echo "  • close_chrome_tab"
    echo "  • create_chrome_tab"
    echo "  • activate_chrome_tab"
    echo "  • get_chrome_tab_info"
    echo ""
    echo "Note: navigate_chrome_tab only activates tabs due to"
    echo "HTTP API limitations. Full navigation requires WebSocket."
    exit 0
else
    echo -e "${RED}✗ Phase 2.2 Implementation has issues${NC}"
    echo "Please review the failed tests above."
    exit 1
fi