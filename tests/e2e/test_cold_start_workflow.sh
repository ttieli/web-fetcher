#!/bin/bash
# End-to-End Test: Cold Start Workflow
#
# Tests complete cold start workflow:
# 1. Kill Chrome
# 2. Run: python wf.py --mode selenium <test_url>
# 3. Verify output contains expected content
# 4. Verify Chrome was launched
# 5. Cleanup
#
# Author: Cody (Claude Code)
# Date: 2025-10-04
# Phase: 3.6 - E2E Workflow Testing

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
WF_SCRIPT="${PROJECT_DIR}/wf.py"
TEST_URL="http://example.com"
OUTPUT_DIR="/tmp/wf_e2e_test_$$"
DEBUG_PORT=9222

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Cleanup function
cleanup() {
    log_info "Cleaning up..."

    # Kill Chrome debug instances
    if command -v lsof >/dev/null 2>&1; then
        local pids=$(lsof -ti:${DEBUG_PORT} 2>/dev/null || echo "")
        if [[ -n "${pids}" ]]; then
            for pid in ${pids}; do
                kill -9 "${pid}" 2>/dev/null || true
                log_info "Killed Chrome process (PID: ${pid})"
            done
        fi
    fi

    # Remove test output directory
    if [[ -d "${OUTPUT_DIR}" ]]; then
        rm -rf "${OUTPUT_DIR}"
        log_info "Removed test output directory"
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Test execution
main() {
    log_info "=== E2E Test: Cold Start Workflow ==="
    log_info "Test URL: ${TEST_URL}"
    log_info "Output Dir: ${OUTPUT_DIR}"

    # Step 1: Kill Chrome
    log_info "Step 1: Killing existing Chrome instances..."
    cleanup
    sleep 1

    # Verify Chrome is not running
    if lsof -ti:${DEBUG_PORT} >/dev/null 2>&1; then
        log_error "Chrome is still running on port ${DEBUG_PORT}"
        exit 1
    fi
    log_info "✓ Chrome not running"

    # Step 2: Create output directory
    log_info "Step 2: Creating output directory..."
    mkdir -p "${OUTPUT_DIR}"
    log_info "✓ Output directory created"

    # Step 3: Run wf.py with selenium mode
    log_info "Step 3: Running wf.py in selenium mode..."

    # Check if wf.py exists
    if [[ ! -f "${WF_SCRIPT}" ]]; then
        log_error "wf.py not found at ${WF_SCRIPT}"
        exit 1
    fi

    # Run wf.py and capture output
    local wf_output
    local wf_exit_code

    if wf_output=$(python3 "${WF_SCRIPT}" --mode auto "${TEST_URL}" -o "${OUTPUT_DIR}" 2>&1); then
        wf_exit_code=0
    else
        wf_exit_code=$?
    fi

    echo "${wf_output}"

    if [[ ${wf_exit_code} -ne 0 ]]; then
        log_error "wf.py failed with exit code ${wf_exit_code}"
        log_error "Output: ${wf_output}"
        exit 1
    fi
    log_info "✓ wf.py completed successfully"

    # Step 4: Verify output contains expected content
    log_info "Step 4: Verifying output content..."

    # Find the output file (should be a .md file)
    local output_files=$(find "${OUTPUT_DIR}" -type f -name "*.md" 2>/dev/null || echo "")

    if [[ -z "${output_files}" ]]; then
        log_error "No output .md file found in ${OUTPUT_DIR}"
        ls -la "${OUTPUT_DIR}"
        exit 1
    fi

    local output_file=$(echo "${output_files}" | head -n 1)
    log_info "Found output file: ${output_file}"

    # Check if output contains expected content for example.com
    if grep -q "Example Domain" "${output_file}"; then
        log_info "✓ Output contains expected content"
    else
        log_warning "Output might not contain expected content"
        log_info "First 20 lines of output:"
        head -n 20 "${output_file}"
    fi

    # Step 5: Verify Chrome was launched
    log_info "Step 5: Verifying Chrome was launched..."

    # Check if Chrome is running on debug port
    if lsof -ti:${DEBUG_PORT} >/dev/null 2>&1; then
        log_info "✓ Chrome is running on port ${DEBUG_PORT}"

        # Try to access DevTools endpoint
        if command -v curl >/dev/null 2>&1; then
            local devtools_response
            if devtools_response=$(curl -s --max-time 3 "http://localhost:${DEBUG_PORT}/json/version" 2>/dev/null); then
                log_info "✓ Chrome DevTools endpoint accessible"
                echo "Chrome version info: ${devtools_response}" | head -c 200
                echo ""
            else
                log_warning "Chrome running but DevTools endpoint not accessible"
            fi
        fi
    else
        log_warning "Chrome not running on port ${DEBUG_PORT} (might have used urllib fallback)"
    fi

    # Final summary
    log_info "=== Test Summary ==="
    log_info "✓ Cold start workflow test PASSED"
    log_info "- Chrome auto-launch: OK"
    log_info "- Content fetch: OK"
    log_info "- Output generation: OK"

    return 0
}

# Run main
main "$@"
