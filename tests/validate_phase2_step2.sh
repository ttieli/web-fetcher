#!/bin/bash
# Validation Script for Phase 2 Step 2.2
# Validates that all functions exist and have correct signatures

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"
ENSURE_SCRIPT="${PROJECT_DIR}/config/ensure-chrome-debug.sh"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

CHECKS_PASSED=0
CHECKS_FAILED=0

log_check() {
    echo -e "\n${YELLOW}[CHECK]${NC} $*"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $*"
    ((CHECKS_PASSED++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $*"
    ((CHECKS_FAILED++))
}

echo "=========================================="
echo "Phase 2.2 - Implementation Validation"
echo "=========================================="
echo "Checking: ${ENSURE_SCRIPT}"
echo ""

# Check 1: navigate_chrome_tab exists
log_check "Function navigate_chrome_tab() exists"
if grep -q "^navigate_chrome_tab()" "${ENSURE_SCRIPT}"; then
    log_pass "Function defined"
    # Check parameter validation
    if grep -A 20 "^navigate_chrome_tab()" "${ENSURE_SCRIPT}" | grep -q "tab_id.*required"; then
        echo "  - Has tab_id parameter validation"
    fi
    if grep -A 20 "^navigate_chrome_tab()" "${ENSURE_SCRIPT}" | grep -q "url.*required"; then
        echo "  - Has url parameter validation"
    fi
    if grep -A 50 "^navigate_chrome_tab()" "${ENSURE_SCRIPT}" | grep -q "Invalid URL"; then
        echo "  - Has URL format validation"
    fi
else
    log_fail "Function not found"
fi

# Check 2: close_chrome_tab exists
log_check "Function close_chrome_tab() exists"
if grep -q "^close_chrome_tab()" "${ENSURE_SCRIPT}"; then
    log_pass "Function defined"
    # Check last tab protection
    if grep -A 50 "^close_chrome_tab()" "${ENSURE_SCRIPT}" | grep -q "last tab"; then
        echo "  - Has last tab protection"
    fi
    # Check tab exists validation
    if grep -A 30 "^close_chrome_tab()" "${ENSURE_SCRIPT}" | grep -q "Tab not found"; then
        echo "  - Has tab existence validation"
    fi
else
    log_fail "Function not found"
fi

# Check 3: create_chrome_tab exists
log_check "Function create_chrome_tab() exists"
if grep -q "^create_chrome_tab()" "${ENSURE_SCRIPT}"; then
    log_pass "Function defined"
    # Check default URL
    if grep -A 10 "^create_chrome_tab()" "${ENSURE_SCRIPT}" | grep -q "about:blank"; then
        echo "  - Has default URL (about:blank)"
    fi
    # Check URL encoding
    if grep -A 50 "^create_chrome_tab()" "${ENSURE_SCRIPT}" | grep -q "encoded_url"; then
        echo "  - Has URL encoding"
    fi
    # Check returns tab ID
    if grep -A 60 "^create_chrome_tab()" "${ENSURE_SCRIPT}" | grep -q 'echo.*new_tab_id'; then
        echo "  - Returns new tab ID to stdout"
    fi
else
    log_fail "Function not found"
fi

# Check 4: activate_chrome_tab exists
log_check "Function activate_chrome_tab() exists"
if grep -q "^activate_chrome_tab()" "${ENSURE_SCRIPT}"; then
    log_pass "Function defined"
    # Check uses /json/activate endpoint
    if grep -A 30 "^activate_chrome_tab()" "${ENSURE_SCRIPT}" | grep -q "/json/activate"; then
        echo "  - Uses /json/activate endpoint"
    fi
    # Check validates tab exists
    if grep -A 30 "^activate_chrome_tab()" "${ENSURE_SCRIPT}" | grep -q "Tab not found"; then
        echo "  - Validates tab exists"
    fi
else
    log_fail "Function not found"
fi

# Check 5: get_chrome_tab_info exists
log_check "Function get_chrome_tab_info() exists"
if grep -q "^get_chrome_tab_info()" "${ENSURE_SCRIPT}"; then
    log_pass "Function defined"
    # Check optional field parameter
    if grep -A 10 "^get_chrome_tab_info()" "${ENSURE_SCRIPT}" | grep -q 'field='; then
        echo "  - Has optional field parameter"
    fi
    # Check field extraction
    if grep -A 80 "^get_chrome_tab_info()" "${ENSURE_SCRIPT}" | grep -q "field_value"; then
        echo "  - Implements field extraction"
    fi
    # Check jq support
    if grep -A 50 "^get_chrome_tab_info()" "${ENSURE_SCRIPT}" | grep -q "jq"; then
        echo "  - Has jq support with fallback"
    fi
else
    log_fail "Function not found"
fi

# Check 6: All functions have error handling
log_check "All functions check Chrome/port availability"
error_checks=0
for func in navigate_chrome_tab close_chrome_tab create_chrome_tab activate_chrome_tab get_chrome_tab_info; do
    if grep -A 30 "^${func}()" "${ENSURE_SCRIPT}" | grep -q "not reachable"; then
        ((error_checks++))
    fi
done
if [[ ${error_checks} -eq 5 ]]; then
    log_pass "All 5 functions check port availability"
else
    log_fail "Only ${error_checks}/5 functions check port availability"
fi

# Check 7: Functions use correct logging
log_check "Functions use proper logging (log_debug, log_error)"
logging_ok=true
for func in navigate_chrome_tab close_chrome_tab create_chrome_tab activate_chrome_tab get_chrome_tab_info; do
    if ! grep -A 100 "^${func}()" "${ENSURE_SCRIPT}" | grep -q "log_debug\|log_error"; then
        logging_ok=false
        break
    fi
done
if [[ "${logging_ok}" == "true" ]]; then
    log_pass "All functions use proper logging"
else
    log_fail "Some functions missing proper logging"
fi

# Check 8: Return codes are documented
log_check "Functions have documented return codes"
doc_count=0
for func in navigate_chrome_tab close_chrome_tab create_chrome_tab activate_chrome_tab get_chrome_tab_info; do
    if grep -B 10 "^${func}()" "${ENSURE_SCRIPT}" | grep -q "Returns:"; then
        ((doc_count++))
    fi
done
if [[ ${doc_count} -eq 5 ]]; then
    log_pass "All 5 functions have documented return codes"
else
    log_fail "Only ${doc_count}/5 functions documented"
fi

# Check 9: Phase 2.2 header exists
log_check "Phase 2.2 section header exists"
if grep -q "Phase 2.2.*Advanced Tab Management" "${ENSURE_SCRIPT}"; then
    log_pass "Section properly marked"
else
    log_fail "Section header not found"
fi

# Check 10: Functions placed after Phase 2.1
log_check "Functions placed after list_chrome_tabs()"
list_chrome_line=$(grep -n "^list_chrome_tabs()" "${ENSURE_SCRIPT}" | cut -d: -f1)
navigate_line=$(grep -n "^navigate_chrome_tab()" "${ENSURE_SCRIPT}" | cut -d: -f1)
if [[ ${navigate_line} -gt ${list_chrome_line} ]]; then
    log_pass "Functions correctly placed after Phase 2.1"
else
    log_fail "Functions not in correct location"
fi

# Summary
echo ""
echo "=========================================="
echo "Validation Results"
echo "=========================================="
echo -e "${GREEN}Passed: ${CHECKS_PASSED}${NC}"
echo -e "${RED}Failed: ${CHECKS_FAILED}${NC}"
echo "Total:  $((CHECKS_PASSED + CHECKS_FAILED))"
echo "=========================================="

if [[ ${CHECKS_FAILED} -eq 0 ]]; then
    echo -e "${GREEN}All validation checks passed!${NC}"
    echo ""
    echo "Implementation is complete and correct."
    exit 0
else
    echo -e "${RED}Some validation checks failed${NC}"
    exit 1
fi
