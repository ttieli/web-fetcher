#!/bin/bash
# Chrome Debug Health Check and Recovery Script
# Phase 1: Core Health Check Logic with Diagnostics and Recovery
#
# Interface Contract:
# - Usage: ensure-chrome-debug.sh [OPTIONS]
# - Options:
#   --port PORT          Debug port (default: 9222)
#   --timeout SECONDS    Health check timeout (default: 5)
#   --retry COUNT        Recovery retry count (default: 3)
#   --quiet              Quiet mode
#   --force              Force restart mode
#   --diagnose           Diagnostic mode (identify failure type)
#
# Return Codes:
# 0 - Chrome instance healthy or recovery successful
# 1 - Recovery failed
# 2 - Parameter error
# 3 - Permission error
#
# Failure Codes (diagnostic mode):
# 1 - Port occupied by non-Chrome process
# 2 - Chrome process dead or unresponsive
# 3 - Chrome zombie process
# 4 - Configuration file corrupted
# 5 - Permission denied
# 0 - Unable to diagnose

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
DIAGNOSE_MODE=false

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
            --diagnose)
                DIAGNOSE_MODE=true
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
  --diagnose           Diagnostic mode (identify failure type)
  -h, --help           Show this help message

RETURN CODES:
  0 - Chrome instance healthy or recovery successful
  1 - Recovery failed
  2 - Parameter error
  3 - Permission error

FAILURE CODES (diagnostic mode):
  1 - Port occupied by non-Chrome process
  2 - Chrome process dead or unresponsive
  3 - Chrome zombie process
  4 - Configuration file corrupted
  5 - Permission denied
  0 - Unable to diagnose

EXAMPLES:
  $(basename "$0")                    # Check with default settings
  $(basename "$0") --port 9223        # Check on custom port
  $(basename "$0") --quiet            # Silent mode
  $(basename "$0") --force            # Force restart
  $(basename "$0") --diagnose         # Diagnose failure type
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

# diagnose_chrome_failure() - Identify Chrome failure type
# Returns:
#   1 - Port occupied by non-Chrome process
#   2 - Chrome process dead or unresponsive
#   3 - Chrome zombie process
#   4 - Configuration file corrupted
#   5 - Permission denied
#   0 - Unable to diagnose
diagnose_chrome_failure() {
    log_debug "Starting failure diagnosis..."
    local start_time
    # macOS doesn't support %N, use seconds only
    start_time=$(date +%s)

    # Check 1: Permission issues with profile directory
    if [[ ! -r "${PROFILE_DIR}" ]] || [[ ! -w "${PROFILE_DIR}" ]]; then
        log_info "Diagnosis: Permission denied (code 5)"
        log_debug "Profile directory: ${PROFILE_DIR}"
        local end_time
        end_time=$(date +%s)
        log_debug "Diagnosis time: $((end_time - start_time))s"
        return 5
    fi

    # Check 2: Port occupation
    local port_occupied=false
    local port_pid=""

    # Try lsof first (most reliable on macOS)
    if command -v lsof >/dev/null 2>&1; then
        # On macOS, lsof might work without sudo for user processes
        port_pid=$(lsof -ti:${PORT} 2>/dev/null || echo "")
        if [[ -n "${port_pid}" ]]; then
            port_occupied=true
            log_debug "Port ${PORT} is occupied by PID: ${port_pid}"

            # Check if it's a Chrome process
            local cmd_line
            cmd_line=$(ps -p "${port_pid}" -o command= 2>/dev/null || echo "")

            if [[ -n "${cmd_line}" ]] && ! echo "${cmd_line}" | grep -q "Chrome\|Chromium"; then
                log_info "Diagnosis: Port occupied by non-Chrome process (code 1)"
                log_debug "Process command: ${cmd_line}"
                local end_time
                end_time=$(date +%s)
                log_debug "Diagnosis time: $((end_time - start_time))s"
                return 1
            fi
        fi
    fi

    # Fallback: Try netstat or nc for port check
    if [[ "${port_occupied}" == "false" ]]; then
        if command -v netstat >/dev/null 2>&1; then
            if netstat -an 2>/dev/null | grep -q "\.${PORT}.*LISTEN"; then
                port_occupied=true
                log_debug "Port ${PORT} is occupied (detected via netstat)"
            fi
        elif nc -z localhost "${PORT}" 2>/dev/null; then
            port_occupied=true
            log_debug "Port ${PORT} is occupied (detected via nc)"
        fi
    fi

    # Check 3: Zombie process detection
    local zombie_pids
    zombie_pids=$(ps aux | grep -i "chrome" | grep -i "defunct" | grep -v grep | awk '{print $2}' || echo "")

    if [[ -n "${zombie_pids}" ]]; then
        # Check if any zombie is related to our debug port
        for zpid in ${zombie_pids}; do
            local parent_cmd
            parent_cmd=$(ps -o ppid= -p "${zpid}" 2>/dev/null | xargs ps -p 2>/dev/null | grep "${PORT}" || echo "")
            if [[ -n "${parent_cmd}" ]]; then
                log_info "Diagnosis: Chrome zombie process detected (code 3)"
                log_debug "Zombie PID: ${zpid}"
                local end_time
                end_time=$(date +%s)
                log_debug "Diagnosis time: $((end_time - start_time))s"
                return 3
            fi
        done
    fi

    # Check 4: Process health (dead or unresponsive)
    # Temporarily disable errexit to capture return code
    set +e
    check_process_health
    local process_status=$?
    set -e

    if [[ ${process_status} -eq 2 ]]; then
        # PID file is corrupted
        log_info "Diagnosis: Configuration file corrupted (code 4)"
        log_debug "PID file: ${PID_FILE}"
        local end_time
        end_time=$(date +%s)
        log_debug "Diagnosis time: $((end_time - start_time))s"
        return 4
    elif [[ ${process_status} -eq 1 ]]; then
        # Process is dead
        log_info "Diagnosis: Chrome process dead or unresponsive (code 2)"
        local end_time
        end_time=$(date +%s)
        log_debug "Diagnosis time: $((end_time - start_time))s"
        log_debug "About to return 2 from diagnose_chrome_failure"
        return 2
    fi

    # Check 5: Port/DevTools responsiveness
    set +e
    check_port_health
    local port_status=$?
    set -e

    if [[ ${port_status} -ne 0 ]]; then
        set +e
        check_devtools_health
        local devtools_status=$?
        set -e

        if [[ ${devtools_status} -ne 0 ]]; then
            log_info "Diagnosis: Chrome process dead or unresponsive (code 2)"
            log_debug "Process exists but port/DevTools unresponsive"
            local end_time
            end_time=$(date +%s)
            log_debug "Diagnosis time: $((end_time - start_time))s"
            return 2
        fi
    fi

    # Unable to diagnose specific failure
    log_info "Diagnosis: Unable to identify specific failure type (code 0)"
    log_debug "All diagnostic checks completed without identifying issue"
    local end_time
    end_time=$(date +%s)
    log_debug "Diagnosis time: $((end_time - start_time))s"
    return 0
}

# check_chrome_health() - Comprehensive Chrome health check
# Parameters:
#   port (default: from global PORT)
#   timeout (default: from global TIMEOUT)
# Returns:
#   0 - Chrome instance is healthy
#   1 - Process does not exist
#   2 - Process is unresponsive (zombie)
#   3 - Port not reachable
#   4 - DevTools protocol error
check_chrome_health() {
    local port="${1:-${PORT}}"
    local timeout="${2:-${TIMEOUT}}"

    log_debug "Running comprehensive health check (port: ${port}, timeout: ${timeout}s)"

    # Check 1: Chrome process exists
    set +e
    check_process_health
    local process_status=$?
    set -e

    if [[ ${process_status} -eq 2 ]]; then
        log_debug "Health check failed: PID file corrupted"
        return 1
    elif [[ ${process_status} -eq 1 ]]; then
        log_debug "Health check failed: Process does not exist"
        return 1
    fi

    # Check 2: Process is responsive (not zombie)
    if [[ -f "${PID_FILE}" ]]; then
        local pid
        pid=$(cat "${PID_FILE}" 2>/dev/null || echo "")
        if [[ -n "${pid}" ]]; then
            local state
            state=$(ps -o state= -p "${pid}" 2>/dev/null || echo "")
            if [[ "${state}" == "Z" ]]; then
                log_debug "Health check failed: Process is zombie"
                return 2
            fi
        fi
    fi

    # Check 3: Debug port connectivity
    set +e
    check_port_health
    local port_status=$?
    set -e

    if [[ ${port_status} -ne 0 ]]; then
        log_debug "Health check failed: Port not reachable"
        return 3
    fi

    # Check 4: DevTools protocol response validation
    set +e
    check_devtools_health
    local devtools_status=$?
    set -e

    if [[ ${devtools_status} -ne 0 ]]; then
        log_debug "Health check failed: DevTools protocol error"
        return 4
    fi

    # Verify response contains webSocketDebuggerUrl
    local endpoint="http://localhost:${port}/json"
    local response
    response=$(curl -s --max-time "${timeout}" --connect-timeout "${timeout}" "${endpoint}" 2>/dev/null || echo "")

    if [[ -n "${response}" ]] && ! echo "${response}" | grep -q "webSocketDebuggerUrl"; then
        log_debug "Health check failed: DevTools response missing webSocketDebuggerUrl"
        return 4
    fi

    log_debug "Health check passed: Chrome instance is healthy"
    return 0
}

# diagnose_failure() - Identify specific failure type
# Parameters:
#   port (default: from global PORT)
#   pid (optional: specific PID to check)
# Returns:
#   1 - Port occupied by non-Chrome process
#   2 - Chrome process dead or unresponsive
#   3 - Chrome zombie process
#   4 - Configuration file corrupted
#   5 - Permission denied
#   0 - Unable to diagnose
diagnose_failure() {
    local port="${1:-${PORT}}"
    local pid="${2:-}"

    log_debug "Diagnosing failure (port: ${port}, pid: ${pid:-auto})"

    # Delegate to existing comprehensive diagnosis function
    set +e
    diagnose_chrome_failure
    local failure_code=$?
    set -e

    return ${failure_code}
}

# attempt_recovery() - Execute recovery strategy based on failure code
# Parameters:
#   failure_code (1-5)
#   port (default: from global PORT)
#   retry_count (default: from global RETRY_COUNT)
# Returns:
#   0 - Recovery successful
#   1 - Recovery failed
attempt_recovery() {
    local failure_code=$1
    local port="${2:-${PORT}}"
    local retry_count="${3:-${RETRY_COUNT}}"

    log_info "Attempting recovery for failure code ${failure_code} (port: ${port})"

    case ${failure_code} in
        1)
            # Port occupied by non-Chrome process
            log_info "Recovery: Killing non-Chrome process on port ${port}"

            # Find PID on port
            local port_pid
            if command -v lsof >/dev/null 2>&1; then
                port_pid=$(lsof -ti:${port} 2>/dev/null || echo "")
            fi

            if [[ -n "${port_pid}" ]]; then
                log_debug "Found process ${port_pid} on port ${port}"

                # Verify it's not Chrome
                local cmd_line
                cmd_line=$(ps -p "${port_pid}" -o command= 2>/dev/null || echo "")

                if [[ -n "${cmd_line}" ]] && ! echo "${cmd_line}" | grep -q "Chrome\|Chromium"; then
                    log_info "Killing non-Chrome process: ${port_pid}"
                    if kill -9 "${port_pid}" 2>/dev/null; then
                        sleep 1
                        log_info "Recovery successful: Non-Chrome process terminated"
                        return 0
                    else
                        log_error "Recovery failed: Cannot kill process ${port_pid}"
                        return 1
                    fi
                fi
            fi

            log_error "Recovery failed: Cannot identify process on port"
            return 1
            ;;

        2)
            # Chrome dead/unresponsive
            log_info "Recovery: Killing and restarting Chrome"

            # Kill existing process if PID file exists
            if [[ -f "${PID_FILE}" ]]; then
                local pid
                pid=$(cat "${PID_FILE}" 2>/dev/null || echo "")
                if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
                    log_debug "Killing unresponsive Chrome process ${pid}"
                    kill -9 "${pid}" 2>/dev/null || true
                    sleep 1
                fi
                rm -f "${PID_FILE}"
            fi

            # Kill any remaining Chrome processes on this port
            if command -v lsof >/dev/null 2>&1; then
                local remaining_pids
                remaining_pids=$(lsof -ti:${port} 2>/dev/null || echo "")
                if [[ -n "${remaining_pids}" ]]; then
                    for rpid in ${remaining_pids}; do
                        log_debug "Killing remaining process ${rpid}"
                        kill -9 "${rpid}" 2>/dev/null || true
                    done
                    sleep 1
                fi
            fi

            log_info "Recovery successful: Chrome processes terminated (restart required)"
            return 0
            ;;

        3)
            # Chrome zombie process
            log_info "Recovery: Force killing zombie and cleaning profile"

            # Find zombie processes
            local zombie_pids
            zombie_pids=$(ps aux | grep -i "chrome" | grep -i "defunct" | grep -v grep | awk '{print $2}' || echo "")

            if [[ -n "${zombie_pids}" ]]; then
                for zpid in ${zombie_pids}; do
                    log_debug "Force killing zombie process ${zpid}"
                    kill -9 "${zpid}" 2>/dev/null || true
                done
            fi

            # Clean PID file
            if [[ -f "${PID_FILE}" ]]; then
                rm -f "${PID_FILE}"
                log_debug "Cleaned PID file"
            fi

            # Clean lock files
            if [[ -d "${PROFILE_DIR}" ]]; then
                rm -f "${PROFILE_DIR}/SingletonLock" 2>/dev/null || true
                rm -f "${PROFILE_DIR}/SingletonCookie" 2>/dev/null || true
                log_debug "Cleaned profile lock files"
            fi

            log_info "Recovery successful: Zombie processes cleaned"
            return 0
            ;;

        4)
            # Configuration corrupted
            log_info "Recovery: Rebuilding configuration"

            # Remove corrupted PID file
            if [[ -f "${PID_FILE}" ]]; then
                rm -f "${PID_FILE}"
                log_debug "Removed corrupted PID file"
            fi

            # Ensure profile directory exists with correct permissions
            if [[ ! -d "${PROFILE_DIR}" ]]; then
                mkdir -p "${PROFILE_DIR}"
                log_debug "Created profile directory"
            fi

            # Clean lock files
            rm -f "${PROFILE_DIR}/SingletonLock" 2>/dev/null || true
            rm -f "${PROFILE_DIR}/SingletonCookie" 2>/dev/null || true

            log_info "Recovery successful: Configuration rebuilt"
            return 0
            ;;

        5)
            # Permission denied
            log_info "Recovery: Checking permissions"

            if [[ ! -d "${PROFILE_DIR}" ]]; then
                log_info "Creating profile directory: ${PROFILE_DIR}"
                if mkdir -p "${PROFILE_DIR}" 2>/dev/null; then
                    log_info "Recovery successful: Directory created"
                    return 0
                else
                    log_error "Recovery failed: Cannot create directory (try with sudo)"
                    return 1
                fi
            fi

            # Check if we can write to the directory
            if [[ -w "${PROFILE_DIR}" ]]; then
                log_info "Recovery successful: Permissions are correct"
                return 0
            else
                log_error "Recovery failed: No write permission for ${PROFILE_DIR}"
                log_error "Run: chmod u+w '${PROFILE_DIR}'"
                return 1
            fi
            ;;

        0|*)
            # Unknown failure - try generic recovery
            log_info "Recovery: Generic recovery for unknown failure"

            # Clean up PID file and locks
            if [[ -f "${PID_FILE}" ]]; then
                rm -f "${PID_FILE}"
            fi

            if [[ -d "${PROFILE_DIR}" ]]; then
                rm -f "${PROFILE_DIR}/SingletonLock" 2>/dev/null || true
                rm -f "${PROFILE_DIR}/SingletonCookie" 2>/dev/null || true
            fi

            log_info "Recovery successful: Generic cleanup completed"
            return 0
            ;;
    esac
}

# select_recovery_strategy() - Map failure code to recovery level
# Input: failure_code (0-5)
# Output: recovery_level (1-4)
# Mapping:
#   1 (Port occupied) -> Level 2
#   2 (Chrome crashed) -> Level 3
#   3 (Zombie process) -> Level 3
#   4 (Config corrupted) -> Level 4
#   5 (Permission) -> Level 1
#   0 (Unknown) -> Level 3 (default)
select_recovery_strategy() {
    local failure_code=$1
    local recovery_level

    case ${failure_code} in
        1)
            recovery_level=2
            log_debug "Failure code 1 (Port occupied) -> Recovery Level 2"
            ;;
        2)
            recovery_level=3
            log_debug "Failure code 2 (Chrome crashed) -> Recovery Level 3"
            ;;
        3)
            recovery_level=3
            log_debug "Failure code 3 (Zombie process) -> Recovery Level 3"
            ;;
        4)
            recovery_level=4
            log_debug "Failure code 4 (Config corrupted) -> Recovery Level 4"
            ;;
        5)
            recovery_level=1
            log_debug "Failure code 5 (Permission) -> Recovery Level 1"
            ;;
        0|*)
            recovery_level=3
            log_debug "Failure code ${failure_code} (Unknown) -> Recovery Level 3 (default)"
            ;;
    esac

    echo "${recovery_level}"
    return 0
}

# Main function (Phase 1: Core Health Check with Diagnostics and Recovery)
main() {
    # Parse arguments
    if ! parse_arguments "$@"; then
        exit 2
    fi

    # Diagnostic mode: identify failure type only (no recovery)
    if [[ "${DIAGNOSE_MODE}" == "true" ]]; then
        log_info "Starting Chrome failure diagnosis (port: ${PORT})"

        # Check if profile directory exists
        if [[ ! -d "${PROFILE_DIR}" ]]; then
            log_info "Profile directory does not exist: ${PROFILE_DIR}"
            log_info "Diagnosis: Configuration file corrupted (code 4)"
            exit 4
        fi

        # Run diagnosis
        set +e
        diagnose_failure "${PORT}"
        local failure_code=$?
        set -e
        log_debug "Captured failure code: ${failure_code}"

        # Select recovery strategy (output only, no recovery in diagnose mode)
        local recovery_level
        recovery_level=$(select_recovery_strategy ${failure_code})
        log_debug "Selected recovery level: ${recovery_level}"

        log_info "Recommended recovery strategy: Level ${recovery_level}"
        log_info "Diagnosis complete"
        exit ${failure_code}
    fi

    # Force mode: aggressive recovery without health check
    if [[ "${FORCE_MODE}" == "true" ]]; then
        log_info "Force mode: Performing aggressive recovery (port: ${PORT})"

        # Diagnose to determine recovery strategy
        set +e
        diagnose_failure "${PORT}"
        local failure_code=$?
        set -e

        if [[ ${failure_code} -eq 0 ]]; then
            # No specific failure, use generic recovery (code 2)
            failure_code=2
            log_debug "No specific failure detected, using generic recovery"
        fi

        # Attempt recovery
        set +e
        attempt_recovery ${failure_code} "${PORT}" "${RETRY_COUNT}"
        local recovery_status=$?
        set -e

        if [[ ${recovery_status} -eq 0 ]]; then
            log_info "Force recovery completed successfully"
            exit 0
        else
            log_error "Force recovery failed"
            exit 1
        fi
    fi

    # Normal mode: Health check with automatic recovery
    log_info "Starting Chrome health check (port: ${PORT}, timeout: ${TIMEOUT}s)"

    # Check if profile directory exists
    if [[ ! -d "${PROFILE_DIR}" ]]; then
        log_error "Profile directory does not exist: ${PROFILE_DIR}"
        log_error "Chrome may not have been started yet"

        # Attempt to create and recover
        log_info "Attempting to create profile directory"
        set +e
        attempt_recovery 4 "${PORT}" "${RETRY_COUNT}"
        local recovery_status=$?
        set -e

        if [[ ${recovery_status} -eq 0 ]]; then
            log_info "Profile directory created, but Chrome needs to be started"
        fi
        exit 1
    fi

    # Perform comprehensive health check
    set +e
    check_chrome_health "${PORT}" "${TIMEOUT}"
    local health_status=$?
    set -e

    if [[ ${health_status} -eq 0 ]]; then
        log_info "Chrome instance is healthy"
        exit 0
    fi

    # Health check failed - diagnose and attempt recovery
    log_info "Health check failed (code: ${health_status}), diagnosing issue..."

    set +e
    diagnose_failure "${PORT}"
    local failure_code=$?
    set -e

    log_info "Diagnosis completed: failure code ${failure_code}"

    # Attempt recovery with retries
    local attempt=1
    local recovery_success=false

    while [[ ${attempt} -le ${RETRY_COUNT} ]]; do
        log_info "Recovery attempt ${attempt}/${RETRY_COUNT}"

        set +e
        attempt_recovery ${failure_code} "${PORT}" "${RETRY_COUNT}"
        local recovery_status=$?
        set -e

        if [[ ${recovery_status} -eq 0 ]]; then
            log_info "Recovery successful on attempt ${attempt}"

            # Verify health after recovery
            sleep 1
            set +e
            check_chrome_health "${PORT}" "${TIMEOUT}"
            local post_recovery_health=$?
            set -e

            if [[ ${post_recovery_health} -eq 0 ]]; then
                log_info "Chrome instance is healthy after recovery"
                recovery_success=true
                break
            else
                log_info "Health check still failing after recovery, will retry"
            fi
        else
            log_info "Recovery failed on attempt ${attempt}"
        fi

        attempt=$((attempt + 1))

        if [[ ${attempt} -le ${RETRY_COUNT} ]]; then
            log_debug "Waiting before next retry attempt"
            sleep 2
        fi
    done

    if [[ "${recovery_success}" == "true" ]]; then
        log_info "Chrome instance recovered successfully"
        exit 0
    else
        log_error "Recovery failed after ${RETRY_COUNT} attempts"
        log_error "Manual intervention may be required"
        exit 1
    fi
}

# Execute main function
main "$@"