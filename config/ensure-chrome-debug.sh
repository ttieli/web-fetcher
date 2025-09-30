#!/bin/bash
# Chrome Debug Health Check and Recovery Script
# Phase 2.1: Core Health Check Mechanism
#
# Interface Contract:
# - Usage: ensure-chrome-debug.sh [OPTIONS]
# - Options:
#   --port PORT          Debug port (default: 9222)
#   --timeout SECONDS    Health check timeout (default: 5)
#   --retry COUNT        Recovery retry count (default: 3)
#   --quiet              Quiet mode
#   --force              Force restart mode
#
# Return Codes:
# 0 - Chrome instance healthy or recovery successful
# 1 - Recovery failed
# 2 - Parameter error
# 3 - Permission error

set -euo pipefail

# Configuration
DEFAULT_PORT="9222"
DEFAULT_TIMEOUT=5
DEFAULT_RETRY=3
PROFILE_DIR="${HOME}/.chrome-wf"
PID_FILE="${PROFILE_DIR}/.chrome-debug.pid"

# Command line options (with defaults)
PORT="${DEFAULT_PORT}"
TIMEOUT="${DEFAULT_TIMEOUT}"
RETRY_COUNT="${DEFAULT_RETRY}"
QUIET_MODE=false
FORCE_MODE=false

# Logging functions
log_info() {
    if [[ "${QUIET_MODE}" != "true" ]]; then
        echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') $*" >&2
    fi
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') $*" >&2
}

log_debug() {
    if [[ "${QUIET_MODE}" != "true" ]]; then
        echo "[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') $*" >&2
    fi
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --port)
                if [[ -z "${2:-}" ]] || [[ "${2}" =~ ^-- ]]; then
                    log_error "Option --port requires a value"
                    return 2
                fi
                if ! [[ "${2}" =~ ^[0-9]+$ ]] || [[ "${2}" -lt 1 ]] || [[ "${2}" -gt 65535 ]]; then
                    log_error "Invalid port number: ${2}"
                    return 2
                fi
                PORT="${2}"
                shift 2
                ;;
            --timeout)
                if [[ -z "${2:-}" ]] || [[ "${2}" =~ ^-- ]]; then
                    log_error "Option --timeout requires a value"
                    return 2
                fi
                if ! [[ "${2}" =~ ^[0-9]+$ ]] || [[ "${2}" -lt 1 ]]; then
                    log_error "Invalid timeout value: ${2}"
                    return 2
                fi
                TIMEOUT="${2}"
                shift 2
                ;;
            --retry)
                if [[ -z "${2:-}" ]] || [[ "${2}" =~ ^-- ]]; then
                    log_error "Option --retry requires a value"
                    return 2
                fi
                if ! [[ "${2}" =~ ^[0-9]+$ ]] || [[ "${2}" -lt 0 ]]; then
                    log_error "Invalid retry count: ${2}"
                    return 2
                fi
                RETRY_COUNT="${2}"
                shift 2
                ;;
            --quiet)
                QUIET_MODE=true
                shift
                ;;
            --force)
                FORCE_MODE=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                return 2
                ;;
        esac
    done
    return 0
}

show_usage() {
    cat >&2 <<EOF
Usage: $(basename "$0") [OPTIONS]

Chrome Debug Health Check and Recovery Script

OPTIONS:
  --port PORT          Debug port (default: ${DEFAULT_PORT})
  --timeout SECONDS    Health check timeout (default: ${DEFAULT_TIMEOUT})
  --retry COUNT        Recovery retry count (default: ${DEFAULT_RETRY})
  --quiet              Quiet mode
  --force              Force restart mode
  -h, --help           Show this help message

RETURN CODES:
  0 - Chrome instance healthy or recovery successful
  1 - Recovery failed
  2 - Parameter error
  3 - Permission error

EXAMPLES:
  $(basename "$0")                    # Check with default settings
  $(basename "$0") --port 9223        # Check on custom port
  $(basename "$0") --quiet            # Silent mode
  $(basename "$0") --force            # Force restart
EOF
}

# check_process_health() - Verify process liveness
# Returns:
#   0 - Process is healthy
#   1 - Process is dead
#   2 - PID file is corrupted
check_process_health() {
    log_debug "Checking process health..."

    # Check if PID file exists
    if [[ ! -f "${PID_FILE}" ]]; then
        log_debug "PID file not found: ${PID_FILE}"
        return 1
    fi

    # Read PID from file
    local pid
    pid=$(cat "${PID_FILE}" 2>/dev/null || echo "")

    if [[ -z "${pid}" ]]; then
        log_error "PID file is empty"
        return 2
    fi

    # Validate PID format
    if ! [[ "${pid}" =~ ^[0-9]+$ ]]; then
        log_error "Invalid PID format in file: ${pid}"
        return 2
    fi

    # Check if process exists using kill -0
    if ! kill -0 "${pid}" 2>/dev/null; then
        log_debug "Process ${pid} is not running"
        return 1
    fi

    # Verify it's actually Chrome with our debug port
    local cmd_line
    cmd_line=$(ps -p "${pid}" -o command= 2>/dev/null || echo "")

    if [[ -z "${cmd_line}" ]]; then
        log_debug "Cannot retrieve command line for PID ${pid}"
        return 1
    fi

    # Check if command line contains our debug port
    if ! echo "${cmd_line}" | grep -q "remote-debugging-port=${PORT}"; then
        log_debug "Process ${pid} is not Chrome debug instance (wrong port)"
        return 1
    fi

    # Additional verification using pgrep
    if ! pgrep -f "remote-debugging-port=${PORT}.*user-data-dir=${PROFILE_DIR}" | grep -q "^${pid}$"; then
        log_debug "Process ${pid} exists but doesn't match our Chrome instance"
        return 1
    fi

    log_debug "Process ${pid} is healthy"
    return 0
}

# check_port_health() - Verify port reachability
# Returns:
#   0 - Port is reachable
#   1 - Connection refused
#   2 - Timeout
check_port_health() {
    log_debug "Checking port health on localhost:${PORT}..."

    # Try to connect to the port using nc (netcat)
    # macOS nc: -z for zero-I/O mode, -w for timeout, -G for connection timeout
    if command -v nc >/dev/null 2>&1; then
        # Use macOS nc with -G for connection timeout
        if nc -z -G "${TIMEOUT}" localhost "${PORT}" 2>/dev/null; then
            log_debug "Port ${PORT} is reachable via nc"
            return 0
        else
            log_debug "Port connection failed (refused or timed out)"
            return 1
        fi
    fi

    # Fallback 1: Try using curl as a port checker
    if command -v curl >/dev/null 2>&1; then
        # Use curl to check if we can connect to the port
        if curl -s --max-time "${TIMEOUT}" --connect-timeout "${TIMEOUT}" \
            "http://localhost:${PORT}" >/dev/null 2>&1; then
            log_debug "Port ${PORT} is reachable via curl"
            return 0
        else
            local exit_code=$?
            # Exit code 28 is timeout in curl
            if [[ ${exit_code} -eq 28 ]]; then
                log_debug "Port connection timed out"
                return 2
            else
                log_debug "Port connection refused or failed"
                return 1
            fi
        fi
    fi

    # Fallback 2: Try using telnet
    if command -v telnet >/dev/null 2>&1; then
        # Use telnet with timeout
        if echo "" | timeout "${TIMEOUT}" telnet localhost "${PORT}" 2>/dev/null | grep -q "Connected"; then
            log_debug "Port ${PORT} is reachable via telnet"
            return 0
        else
            log_debug "Port connection refused via telnet"
            return 1
        fi
    fi

    log_error "No suitable port checking tool found (tried: nc, curl, telnet)"
    return 1
}

# check_devtools_health() - Verify DevTools protocol response
# Returns:
#   0 - DevTools protocol is healthy
#   1 - Protocol error
#   2 - Response abnormal
check_devtools_health() {
    log_debug "Checking DevTools protocol health..."

    local endpoint="http://localhost:${PORT}/json/version"
    local response
    local http_code

    # Make request to DevTools endpoint with timeout
    if ! command -v curl >/dev/null 2>&1; then
        log_error "curl command not found"
        return 1
    fi

    # Perform the request and capture both response and HTTP code
    response=$(curl -s --max-time "${TIMEOUT}" --connect-timeout "${TIMEOUT}" -w "\n%{http_code}" "${endpoint}" 2>/dev/null || echo "")

    if [[ -z "${response}" ]]; then
        log_debug "DevTools endpoint returned empty response"
        return 1
    fi

    # Extract HTTP code (last line) and body (everything else)
    http_code=$(echo "${response}" | tail -n 1)
    local body
    body=$(echo "${response}" | sed '$d')

    # Check HTTP status code
    if [[ "${http_code}" != "200" ]]; then
        log_debug "DevTools endpoint returned HTTP ${http_code}"
        return 1
    fi

    # Verify response is valid JSON with expected fields
    if ! echo "${body}" | grep -q '"Browser"' || ! echo "${body}" | grep -q '"Protocol-Version"'; then
        log_debug "DevTools response missing expected fields"
        return 2
    fi

    # Try to extract Browser field to verify JSON is valid
    local browser_info
    browser_info=$(echo "${body}" | grep -o '"Browser"[[:space:]]*:[[:space:]]*"[^"]*"' || echo "")

    if [[ -z "${browser_info}" ]]; then
        log_debug "Cannot parse Browser field from DevTools response"
        log_debug "Response body: ${body}"
        return 2
    fi

    log_debug "DevTools protocol is healthy: ${browser_info}"
    return 0
}

# Main function (Phase 2.1: Health checks only, no recovery)
main() {
    # Parse arguments
    if ! parse_arguments "$@"; then
        exit 2
    fi

    log_info "Starting Chrome health check (port: ${PORT}, timeout: ${TIMEOUT}s)"

    # Check if profile directory exists
    if [[ ! -d "${PROFILE_DIR}" ]]; then
        log_error "Profile directory does not exist: ${PROFILE_DIR}"
        log_error "Chrome may not have been started yet"
        exit 1
    fi

    # Perform health checks
    local process_status=0
    local port_status=0
    local devtools_status=0

    # Check 1: Process Health
    check_process_health
    process_status=$?

    if [[ ${process_status} -eq 2 ]]; then
        log_error "Health check failed: PID file is corrupted"
        exit 1
    elif [[ ${process_status} -eq 1 ]]; then
        log_error "Health check failed: Chrome process is dead"
        exit 1
    fi

    log_info "✓ Process health check passed"

    # Check 2: Port Health
    check_port_health
    port_status=$?

    if [[ ${port_status} -eq 2 ]]; then
        log_error "Health check failed: Port connection timed out"
        exit 1
    elif [[ ${port_status} -eq 1 ]]; then
        log_error "Health check failed: Port connection refused"
        exit 1
    fi

    log_info "✓ Port health check passed"

    # Check 3: DevTools Health
    check_devtools_health
    devtools_status=$?

    if [[ ${devtools_status} -eq 2 ]]; then
        log_error "Health check failed: DevTools response abnormal"
        exit 1
    elif [[ ${devtools_status} -eq 1 ]]; then
        log_error "Health check failed: DevTools protocol error"
        exit 1
    fi

    log_info "✓ DevTools protocol health check passed"

    # All checks passed
    log_info "Chrome instance is healthy"
    exit 0
}

# Execute main function
main "$@"