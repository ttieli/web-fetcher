#!/bin/bash
# Health Check Performance Test
# Tests the speed and efficiency of health checks

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HEALTH_CHECK_SCRIPT="${PROJECT_ROOT}/config/ensure-chrome-debug.sh"
PROFILE_DIR="${HOME}/.chrome-wf"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

# Cleanup function
cleanup() {
    pkill -f "remote-debugging-port=9222" 2>/dev/null || true
    rm -f "${PROFILE_DIR}/.chrome-debug.pid" 2>/dev/null || true
}

# Start Chrome
start_chrome() {
    cleanup
    mkdir -p "${PROFILE_DIR}"

    /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
        --remote-debugging-port=9222 \
        --user-data-dir="${PROFILE_DIR}" \
        --no-first-run \
        --no-default-browser-check \
        --headless \
        >/dev/null 2>&1 &

    local chrome_pid=$!
    echo "${chrome_pid}" > "${PROFILE_DIR}/.chrome-debug.pid"
    sleep 3
    echo "${chrome_pid}"
}

# Test performance
test_performance() {
    echo "========================================"
    echo "Health Check Performance Test"
    echo "========================================"
    echo

    # Start Chrome
    echo -e "${YELLOW}Starting Chrome...${NC}"
    local chrome_pid=$(start_chrome)

    # Test 1: Single health check timing
    echo -e "${YELLOW}\nTest 1: Single health check speed${NC}"
    local start_time=$(date +%s.%N)
    "${HEALTH_CHECK_SCRIPT}" --quiet
    local end_time=$(date +%s.%N)
    local duration=$(echo "${end_time} - ${start_time}" | bc)
    echo -e "${GREEN}Health check completed in: ${duration} seconds${NC}"

    # Test 2: Multiple consecutive checks
    echo -e "${YELLOW}\nTest 2: 10 consecutive health checks${NC}"
    local total_start=$(date +%s.%N)
    for i in {1..10}; do
        "${HEALTH_CHECK_SCRIPT}" --quiet
    done
    local total_end=$(date +%s.%N)
    local total_duration=$(echo "${total_end} - ${total_start}" | bc)
    local avg_duration=$(echo "scale=3; ${total_duration} / 10" | bc)
    echo -e "${GREEN}Total time: ${total_duration} seconds${NC}"
    echo -e "${GREEN}Average per check: ${avg_duration} seconds${NC}"

    # Test 3: Health check with custom timeout
    echo -e "${YELLOW}\nTest 3: Health check with 1-second timeout${NC}"
    local fast_start=$(date +%s.%N)
    "${HEALTH_CHECK_SCRIPT}" --timeout 1 --quiet
    local fast_end=$(date +%s.%N)
    local fast_duration=$(echo "${fast_end} - ${fast_start}" | bc)
    echo -e "${GREEN}Fast timeout check: ${fast_duration} seconds${NC}"

    # Test 4: Failure detection speed (kill Chrome)
    echo -e "${YELLOW}\nTest 4: Failure detection speed${NC}"
    kill "${chrome_pid}" 2>/dev/null || true
    sleep 1

    local fail_start=$(date +%s.%N)
    "${HEALTH_CHECK_SCRIPT}" --quiet 2>/dev/null || true
    local fail_end=$(date +%s.%N)
    local fail_duration=$(echo "${fail_end} - ${fail_start}" | bc)
    echo -e "${GREEN}Failure detection time: ${fail_duration} seconds${NC}"

    # Summary
    echo -e "\n${GREEN}========================================"
    echo "Performance Summary"
    echo "========================================"
    echo "Single check: ${duration}s"
    echo "Average (10 checks): ${avg_duration}s"
    echo "Fast timeout: ${fast_duration}s"
    echo "Failure detection: ${fail_duration}s"
    echo -e "========================================${NC}"

    # Performance criteria
    echo -e "\n${YELLOW}Performance Criteria:${NC}"
    if (( $(echo "${duration} < 1" | bc -l) )); then
        echo -e "${GREEN}✓ Single check < 1 second${NC}"
    else
        echo -e "${GREEN}✗ Single check >= 1 second (may need optimization)${NC}"
    fi

    if (( $(echo "${avg_duration} < 0.5" | bc -l) )); then
        echo -e "${GREEN}✓ Average check < 0.5 seconds${NC}"
    else
        echo -e "${GREEN}✗ Average check >= 0.5 seconds (may need optimization)${NC}"
    fi

    cleanup
}

# Main
main() {
    # Verify script exists
    if [[ ! -f "${HEALTH_CHECK_SCRIPT}" ]]; then
        echo "Error: Health check script not found"
        exit 1
    fi

    chmod +x "${HEALTH_CHECK_SCRIPT}"
    test_performance
}

main "$@"