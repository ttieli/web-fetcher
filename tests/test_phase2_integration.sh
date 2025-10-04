#!/bin/bash
#
# Integration tests for Phase 2: Chrome Error Handling Enhancement
#
# Tests error handling in real-world scenarios:
# - Permission errors
# - Port conflicts
# - Timeout handling
# - Error message display
#
# Author: Cody (Claude Code)
# Date: 2025-10-04

# set -e  # Exit on error - disabled for complete test run

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
print_header() {
    echo -e "\n${YELLOW}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((TESTS_PASSED++))
}

print_failure() {
    echo -e "${RED}✗ $1${NC}"
    ((TESTS_FAILED++))
}

run_test() {
    ((TESTS_RUN++))
    local test_name="$1"
    shift
    echo -e "\nTest ${TESTS_RUN}: ${test_name}"
    if "$@"; then
        print_success "${test_name}"
        return 0
    else
        print_failure "${test_name}"
        return 1
    fi
}

# Test 1: Exception classes are importable
test_exception_imports() {
    print_header "Test 1: Exception Class Imports"

    python3 -c "
from error_handler import (
    ChromeDebugError,
    ChromePortConflictError,
    ChromePermissionError,
    ChromeTimeoutError,
    ChromeLaunchError,
    ChromeErrorMessages
)
print('All Chrome exception classes imported successfully')
" 2>&1

    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        return 0
    else
        echo "Failed to import Chrome exception classes"
        return 1
    fi
}

# Test 2: ErrorCategory includes Chrome categories
test_error_categories() {
    print_header "Test 2: Chrome Error Categories"

    python3 -c "
from error_handler import ErrorCategory

# Check Chrome-specific categories exist
categories = [
    ErrorCategory.CHROME_LAUNCH,
    ErrorCategory.CHROME_PERMISSION,
    ErrorCategory.CHROME_PORT_CONFLICT,
    ErrorCategory.CHROME_TIMEOUT
]

print(f'Found {len(categories)} Chrome error categories')
for cat in categories:
    print(f'  - {cat.name}: {cat.value}')
" 2>&1

    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        return 0
    else
        echo "Failed to verify Chrome error categories"
        return 1
    fi
}

# Test 3: Error message templates are accessible
test_error_messages() {
    print_header "Test 3: Error Message Templates"

    python3 -c "
from error_handler import ChromeErrorMessages

# Test each message type
templates = {
    'permission': ChromeErrorMessages.PERMISSION_DENIED_MACOS,
    'port_conflict': ChromeErrorMessages.PORT_CONFLICT,
    'timeout': ChromeErrorMessages.TIMEOUT_ERROR,
    'launch_failed': ChromeErrorMessages.LAUNCH_FAILED
}

for name, template in templates.items():
    if template and len(template) > 0:
        print(f'✓ {name}: {len(template)} characters')
    else:
        raise ValueError(f'{name} template is empty')

print(f'All {len(templates)} message templates are valid')
" 2>&1

    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        return 0
    else
        echo "Failed to verify error message templates"
        return 1
    fi
}

# Test 4: Message formatting works correctly
test_message_formatting() {
    print_header "Test 4: Error Message Formatting"

    python3 -c "
from error_handler import ChromeErrorMessages

# Test permission message (no parameters)
perm_msg = ChromeErrorMessages.get_message('permission')
assert 'Permission Error' in perm_msg, 'Permission message missing title'
assert 'chmod' in perm_msg, 'Permission message missing chmod command'
print('✓ Permission message formatted correctly')

# Test port conflict message (with parameters)
port_msg = ChromeErrorMessages.get_message(
    'port_conflict',
    port=9222,
    diagnostic_info='Port occupied by PID 12345'
)
assert '9222' in port_msg, 'Port number not in message'
assert 'PID 12345' in port_msg, 'Diagnostic info not in message'
print('✓ Port conflict message formatted correctly')

# Test timeout message (with parameters)
timeout_msg = ChromeErrorMessages.get_message('timeout', timeout=15)
assert '15' in timeout_msg, 'Timeout value not in message'
print('✓ Timeout message formatted correctly')

# Test launch failed message (with parameters)
launch_msg = ChromeErrorMessages.get_message(
    'launch_failed',
    error_details='Chrome executable not found'
)
assert 'Chrome executable not found' in launch_msg, 'Error details not in message'
print('✓ Launch failed message formatted correctly')

print('All message formatting tests passed')
" 2>&1

    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        return 0
    else
        echo "Failed message formatting tests"
        return 1
    fi
}

# Test 5: Error classifier recognizes Chrome patterns
test_error_classifier() {
    print_header "Test 5: Error Pattern Classification"

    python3 -c "
from error_handler import ErrorClassifier, ErrorCategory

classifier = ErrorClassifier()

# Test Chrome-specific patterns
test_cases = [
    ('Chrome launch failed', ErrorCategory.CHROME_LAUNCH),
    ('Chrome permission denied', ErrorCategory.CHROME_PERMISSION),
    ('port 9222 already in use', ErrorCategory.CHROME_PORT_CONFLICT),
    ('Chrome debug session timeout', ErrorCategory.CHROME_TIMEOUT),
]

for error_msg, expected_category in test_cases:
    exception = Exception(error_msg)
    actual_category = classifier.classify(exception)

    if actual_category == expected_category:
        print(f'✓ \"{error_msg}\" -> {expected_category.name}')
    else:
        raise AssertionError(
            f'Pattern mismatch: \"{error_msg}\" classified as {actual_category.name}, '
            f'expected {expected_category.name}'
        )

print(f'All {len(test_cases)} pattern classification tests passed')
" 2>&1

    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        return 0
    else
        echo "Failed error pattern classification tests"
        return 1
    fi
}

# Test 6: Exception hierarchy is correct
test_exception_hierarchy() {
    print_header "Test 6: Exception Class Hierarchy"

    python3 -c "
from error_handler import (
    ChromeDebugError,
    ChromePortConflictError,
    ChromePermissionError,
    ChromeTimeoutError,
    ChromeLaunchError
)

# Test inheritance
exceptions = [
    ChromePortConflictError,
    ChromePermissionError,
    ChromeTimeoutError,
    ChromeLaunchError
]

for exc_class in exceptions:
    if not issubclass(exc_class, ChromeDebugError):
        raise AssertionError(f'{exc_class.__name__} does not inherit from ChromeDebugError')
    print(f'✓ {exc_class.__name__} inherits from ChromeDebugError')

# Test exception attributes
error = ChromePortConflictError(
    'Test error',
    error_code=1,
    guidance='Test guidance'
)

assert error.message == 'Test error', 'message attribute not set'
assert error.error_code == 1, 'error_code attribute not set'
assert error.guidance == 'Test guidance', 'guidance attribute not set'

print('✓ Exception attributes work correctly')
print('All exception hierarchy tests passed')
" 2>&1

    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        return 0
    else
        echo "Failed exception hierarchy tests"
        return 1
    fi
}

# Test 7: Bilingual message support
test_bilingual_messages() {
    print_header "Test 7: Bilingual Message Support"

    python3 -c "
from error_handler import ChromeErrorMessages

# Test that messages include both English and Chinese
templates = [
    ('permission', 'Permission Error', '权限错误'),
    ('port_conflict', 'Port Conflict', '端口冲突'),
    ('timeout', 'Timeout Error', '超时错误'),
    ('launch_failed', 'Launch Failed', '启动失败'),
]

for msg_type, english_text, chinese_text in templates:
    msg = ChromeErrorMessages.get_message(msg_type, port=9222, timeout=15, error_details='test', diagnostic_info='test')

    if english_text in msg and chinese_text in msg:
        print(f'✓ {msg_type} is bilingual')
    else:
        raise AssertionError(
            f'{msg_type} missing translations - '
            f'English: {english_text in msg}, Chinese: {chinese_text in msg}'
        )

print('All bilingual message tests passed')
" 2>&1

    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        return 0
    else
        echo "Failed bilingual message tests"
        return 1
    fi
}

# Test 8: Verify webfetcher imports
test_webfetcher_imports() {
    print_header "Test 8: Webfetcher Chrome Exception Imports"

    # Check if webfetcher.py imports Chrome exceptions
    if grep -q "from error_handler import" "webfetcher.py"; then
        echo "✓ webfetcher.py imports from error_handler"

        # Check specific imports
        if grep -q "ChromeDebugError" "webfetcher.py" && \
           grep -q "ChromeErrorMessages" "webfetcher.py"; then
            echo "✓ Chrome exception classes imported in webfetcher.py"
            return 0
        else
            echo "✗ Chrome exception classes not fully imported in webfetcher.py"
            return 1
        fi
    else
        echo "✗ webfetcher.py does not import from error_handler"
        return 1
    fi
}

# Main test execution
main() {
    print_header "Phase 2 Integration Tests"
    echo "Testing Chrome Error Handling Enhancement"

    # Change to project root directory
    cd "$(dirname "$0")/.."

    # Run all tests
    run_test "Exception Class Imports" test_exception_imports
    run_test "Chrome Error Categories" test_error_categories
    run_test "Error Message Templates" test_error_messages
    run_test "Message Formatting" test_message_formatting
    run_test "Error Pattern Classification" test_error_classifier
    run_test "Exception Hierarchy" test_exception_hierarchy
    run_test "Bilingual Message Support" test_bilingual_messages
    run_test "Webfetcher Chrome Imports" test_webfetcher_imports

    # Print summary
    echo ""
    print_header "Test Summary"
    echo "Tests run: ${TESTS_RUN}"
    echo -e "${GREEN}Tests passed: ${TESTS_PASSED}${NC}"

    if [ ${TESTS_FAILED} -gt 0 ]; then
        echo -e "${RED}Tests failed: ${TESTS_FAILED}${NC}"
        exit 1
    else
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    fi
}

# Run main function
main
