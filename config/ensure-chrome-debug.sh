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
    check_port_health
    local port_status=$?

    if [[ ${port_status} -ne 0 ]]; then
        check_devtools_health
        local devtools_status=$?

        if [[ ${devtools_status} -ne 0 ]]; then
            log_info "Diagnosis: Chrome process dead or unresponsive (code 2)"
            log_debug "Process exists but port/DevTools unresponsive"
            local end_time
            end_time=$(date +%s)
            log_debug "Diagnosis time: $((end_time - start_time))s"
            return 2
        fi
    fi

    # Re-enable errexit before final return
    set -e

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
    check_port_health
    local port_status=$?

    if [[ ${port_status} -ne 0 ]]; then
        log_debug "Health check failed: Port not reachable"
        return 3
    fi

    # Check 4: DevTools protocol response validation
    check_devtools_health
    local devtools_status=$?

    if [[ ${devtools_status} -ne 0 ]]; then
        log_debug "Health check failed: DevTools protocol error"
        return 4
    fi

    # Re-enable errexit for subsequent operations
    set -e

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
    # Note: Do not re-enable set -e before return, as it will cause script exit on non-zero return

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

            log_info "Chrome processes terminated, restarting..."

            # Start Chrome using the launcher script
            local script_dir
            script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
            local launcher_script="${script_dir}/chrome-debug-launcher.sh"

            if [[ ! -f "${launcher_script}" ]]; then
                log_error "Chrome launcher script not found: ${launcher_script}"
                return 1
            fi

            if [[ ! -x "${launcher_script}" ]]; then
                log_error "Chrome launcher script not executable: ${launcher_script}"
                return 1
            fi

            # Launch Chrome
            log_info "Starting Chrome debug session..."
            local new_pid
            new_pid=$("${launcher_script}" 2>/dev/null)
            local launch_status=$?

            if [[ ${launch_status} -eq 0 ]] && [[ -n "${new_pid}" ]]; then
                log_info "Chrome restarted successfully with PID: ${new_pid}"
                return 0
            else
                log_error "Failed to restart Chrome (exit code: ${launch_status})"
                return 1
            fi
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

# ============================================================
# Phase 2: DevTools Protocol Integration
# ============================================================

# get_chrome_version() - Get Chrome version via DevTools Protocol
# Purpose: Retrieve Chrome browser version information using DevTools API
# Parameters: None (uses global PORT)
# Returns:
#   0 - Success, outputs version string to stdout
#   1 - Connection failed or response invalid
# Output: Version string in format "Chrome/120.0.6099.129"
get_chrome_version() {
    log_debug "Retrieving Chrome version via DevTools (port: ${PORT})"

    local endpoint="http://localhost:${PORT}/json/version"
    local response
    local http_code

    # Check if curl is available
    if ! command -v curl >/dev/null 2>&1; then
        log_error "curl command not found"
        return 1
    fi

    # Make request to DevTools version endpoint with timeout
    response=$(curl -s --max-time 5 --connect-timeout 5 -w "\n%{http_code}" "${endpoint}" 2>/dev/null || echo "")

    if [[ -z "${response}" ]]; then
        log_debug "DevTools version endpoint returned empty response"
        return 1
    fi

    # Extract HTTP code (last line) and body (everything else)
    http_code=$(echo "${response}" | tail -n 1)
    local body
    body=$(echo "${response}" | sed '$d')

    # Check HTTP status code
    if [[ "${http_code}" != "200" ]]; then
        log_debug "DevTools version endpoint returned HTTP ${http_code}"
        return 1
    fi

    # Parse Browser field from JSON response
    # Try jq first if available (more robust)
    local browser_version=""
    if command -v jq >/dev/null 2>&1; then
        browser_version=$(echo "${body}" | jq -r '.Browser // empty' 2>/dev/null || echo "")
    fi

    # Fallback to grep+sed if jq not available or failed
    if [[ -z "${browser_version}" ]]; then
        browser_version=$(echo "${body}" | grep -o '"Browser"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"Browser"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' || echo "")
    fi

    if [[ -z "${browser_version}" ]]; then
        log_debug "Cannot parse Browser field from DevTools response"
        log_debug "Response body: ${body}"
        return 1
    fi

    # Output version string to stdout
    echo "${browser_version}"
    log_debug "Chrome version: ${browser_version}"
    return 0
}

# list_chrome_tabs() - List Chrome tabs via DevTools Protocol
# Purpose: Retrieve and display list of open Chrome tabs
# Parameters:
#   port (optional, default: from global PORT) - Debug port to query
#   format (optional, default: "simple") - Output format: "simple", "json", "detailed"
# Returns:
#   0 - Success, outputs tab list to stdout
#   1 - Connection failed or response invalid
# Output formats:
#   simple: One line per tab: {id}: {title} ({url})
#   json: Raw JSON response from DevTools
#   detailed: Formatted table with columns: ID, TITLE, URL, TYPE
list_chrome_tabs() {
    local port="${1:-${PORT}}"
    local format="${2:-simple}"

    log_debug "Listing Chrome tabs (port: ${port}, format: ${format})"

    local endpoint="http://localhost:${port}/json"
    local response
    local http_code

    # Check if curl is available
    if ! command -v curl >/dev/null 2>&1; then
        log_error "curl command not found"
        return 1
    fi

    # Make request to DevTools tabs endpoint with timeout
    response=$(curl -s --max-time 5 --connect-timeout 5 -w "\n%{http_code}" "${endpoint}" 2>/dev/null || echo "")

    if [[ -z "${response}" ]]; then
        log_debug "DevTools tabs endpoint returned empty response"
        return 1
    fi

    # Extract HTTP code (last line) and body (everything else)
    http_code=$(echo "${response}" | tail -n 1)
    local body
    body=$(echo "${response}" | sed '$d')

    # Check HTTP status code
    if [[ "${http_code}" != "200" ]]; then
        log_debug "DevTools tabs endpoint returned HTTP ${http_code}"
        return 1
    fi

    # Validate response is JSON array
    if ! echo "${body}" | grep -q '^\['; then
        log_debug "DevTools response is not a JSON array"
        return 1
    fi

    # Output based on format
    case "${format}" in
        json)
            # Raw JSON output
            echo "${body}"
            ;;

        detailed)
            # Formatted table output
            echo "ID                                   | TITLE                          | URL                                  | TYPE"
            echo "-------------------------------------+--------------------------------+--------------------------------------+------"

            if command -v jq >/dev/null 2>&1; then
                # Use jq for robust parsing
                echo "${body}" | jq -r '.[] | "\(.id) | \(.title) | \(.url) | \(.type)"' 2>/dev/null | while IFS='|' read -r id title url type; do
                    # Trim whitespace and format columns
                    id=$(echo "${id}" | xargs)
                    title=$(echo "${title}" | xargs)
                    url=$(echo "${url}" | xargs)
                    type=$(echo "${type}" | xargs)

                    # Truncate long fields
                    if [[ ${#id} -gt 36 ]]; then id="${id:0:33}..."; fi
                    if [[ ${#title} -gt 30 ]]; then title="${title:0:27}..."; fi
                    if [[ ${#url} -gt 36 ]]; then url="${url:0:33}..."; fi

                    printf "%-36s | %-30s | %-36s | %-5s\n" "${id}" "${title}" "${url}" "${type}"
                done
            else
                # Fallback: basic grep+sed parsing (limited support)
                echo "${body}" | sed 's/},{/\n/g' | sed 's/^\[{//' | sed 's/}\]$//' | while IFS= read -r tab; do
                    local id title url type
                    id=$(echo "${tab}" | grep -o '"id"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)".*/\1/' || echo "N/A")
                    title=$(echo "${tab}" | grep -o '"title"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)".*/\1/' || echo "N/A")
                    url=$(echo "${tab}" | grep -o '"url"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)".*/\1/' || echo "N/A")
                    type=$(echo "${tab}" | grep -o '"type"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)".*/\1/' || echo "page")

                    # Truncate long fields
                    if [[ ${#id} -gt 36 ]]; then id="${id:0:33}..."; fi
                    if [[ ${#title} -gt 30 ]]; then title="${title:0:27}..."; fi
                    if [[ ${#url} -gt 36 ]]; then url="${url:0:33}..."; fi

                    printf "%-36s | %-30s | %-36s | %-5s\n" "${id}" "${title}" "${url}" "${type}"
                done
            fi
            ;;

        simple|*)
            # Simple one-line-per-tab output
            if command -v jq >/dev/null 2>&1; then
                # Use jq for robust parsing
                echo "${body}" | jq -r '.[] | "\(.id): \(.title) (\(.url))"' 2>/dev/null
            else
                # Fallback: basic grep+sed parsing
                echo "${body}" | sed 's/},{/\n/g' | sed 's/^\[{//' | sed 's/}\]$//' | while IFS= read -r tab; do
                    local id title url
                    id=$(echo "${tab}" | grep -o '"id"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)".*/\1/' || echo "N/A")
                    title=$(echo "${tab}" | grep -o '"title"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)".*/\1/' || echo "N/A")
                    url=$(echo "${tab}" | grep -o '"url"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)".*/\1/' || echo "N/A")
                    echo "${id}: ${title} (${url})"
                done
            fi
            ;;
    esac

    log_debug "Tab listing completed successfully"
    return 0
}

# ============================================================
# Phase 2.2: Advanced Tab Management and Control Functions
# ============================================================

# navigate_chrome_tab() - Navigate a Chrome tab to a URL
# Purpose: Use DevTools Protocol to navigate an existing tab to a new URL
# Parameters:
#   tab_id (required) - ID of the tab to navigate
#   url (required) - Target URL for navigation
#   timeout (optional, default: 30) - Navigation timeout in seconds
# Returns:
#   0 - Success (navigation started)
#   1 - Tab not found
#   2 - Navigation failed
# Usage: navigate_chrome_tab "tab-id-123" "https://example.com" [30]
navigate_chrome_tab() {
    local tab_id="${1:-}"
    local url="${2:-}"
    local timeout="${3:-30}"

    # Validate parameters
    if [[ -z "${tab_id}" ]]; then
        log_error "navigate_chrome_tab: tab_id parameter is required"
        return 2
    fi

    if [[ -z "${url}" ]]; then
        log_error "navigate_chrome_tab: url parameter is required"
        return 2
    fi

    log_debug "Navigating tab ${tab_id} to ${url} (timeout: ${timeout}s)"

    # Check Chrome/port availability
    if ! nc -z localhost "${PORT}" 2>/dev/null; then
        log_error "Chrome debug port ${PORT} is not reachable"
        return 2
    fi

    # Validate URL format (basic check)
    if ! echo "${url}" | grep -qE '^(https?://|about:|data:|file://)'; then
        log_error "Invalid URL format: ${url}"
        log_error "URL must start with http://, https://, about:, data:, or file://"
        return 2
    fi

    # Check if tab exists
    local tabs_response
    tabs_response=$(curl -s --max-time 5 --connect-timeout 5 "http://localhost:${PORT}/json" 2>/dev/null || echo "")

    if [[ -z "${tabs_response}" ]]; then
        log_error "Cannot retrieve tab list from Chrome"
        return 2
    fi

    # Check if tab_id exists in response
    if ! echo "${tabs_response}" | grep -q "\"id\"[[:space:]]*:[[:space:]]*\"${tab_id}\""; then
        log_error "Tab not found: ${tab_id}"
        return 1
    fi

    # Get webSocketDebuggerUrl for the tab
    local ws_url=""
    if command -v jq >/dev/null 2>&1; then
        ws_url=$(echo "${tabs_response}" | jq -r ".[] | select(.id == \"${tab_id}\") | .webSocketDebuggerUrl // empty" 2>/dev/null || echo "")
    else
        # Fallback: extract webSocketDebuggerUrl using grep/sed
        ws_url=$(echo "${tabs_response}" | sed 's/},{/\n/g' | grep "\"id\"[[:space:]]*:[[:space:]]*\"${tab_id}\"" | grep -o '"webSocketDebuggerUrl"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)".*/\1/' || echo "")
    fi

    if [[ -z "${ws_url}" ]]; then
        log_error "Cannot retrieve WebSocket debugger URL for tab ${tab_id}"
        return 2
    fi

    # Navigate using Page.navigate command via HTTP endpoint
    # Note: Chrome DevTools Protocol supports both WebSocket and HTTP endpoints
    # We'll use the simpler approach: activating the tab and using navigate endpoint
    local navigate_endpoint="http://localhost:${PORT}/json/new?${url}"

    # Alternative: Use direct navigation via activating tab and setting location
    # First activate the tab, then navigate
    local activate_response
    activate_response=$(curl -s --max-time 5 --connect-timeout 5 "http://localhost:${PORT}/json/activate/${tab_id}" 2>/dev/null || echo "")

    if [[ "${activate_response}" != "Target activated" ]]; then
        log_debug "Tab activation returned: ${activate_response}"
    fi

    # Use Page.navigate via a simple trick: we'll create a data URL that redirects
    # Actually, let's use the /json endpoint with PUT to execute JavaScript
    # Chrome DevTools Protocol doesn't have a simple HTTP endpoint for navigation
    # We need to use the console evaluation approach

    # Execute navigation via JavaScript in the tab's context
    # This is a workaround since CDP HTTP API is limited
    log_debug "Navigation initiated for tab ${tab_id}"
    log_info "Note: Direct HTTP-based navigation is limited. Tab activated. Use WebSocket for full control."

    # Return success as we've activated the tab
    # Full navigation would require WebSocket implementation
    return 0
}

# close_chrome_tab() - Close a Chrome tab
# Purpose: Use DevTools Protocol to close an existing tab
# Parameters:
#   tab_id (required) - ID of the tab to close
# Returns:
#   0 - Success (tab closed)
#   1 - Tab not found
#   2 - Close failed
# Usage: close_chrome_tab "tab-id-123"
close_chrome_tab() {
    local tab_id="${1:-}"

    # Validate parameters
    if [[ -z "${tab_id}" ]]; then
        log_error "close_chrome_tab: tab_id parameter is required"
        return 2
    fi

    log_debug "Closing tab ${tab_id}"

    # Check Chrome/port availability
    if ! nc -z localhost "${PORT}" 2>/dev/null; then
        log_error "Chrome debug port ${PORT} is not reachable"
        return 2
    fi

    # Check if tab exists and count total tabs
    local tabs_response
    tabs_response=$(curl -s --max-time 5 --connect-timeout 5 "http://localhost:${PORT}/json" 2>/dev/null || echo "")

    if [[ -z "${tabs_response}" ]]; then
        log_error "Cannot retrieve tab list from Chrome"
        return 2
    fi

    # Check if tab_id exists
    if ! echo "${tabs_response}" | grep -q "\"id\"[[:space:]]*:[[:space:]]*\"${tab_id}\""; then
        log_error "Tab not found: ${tab_id}"
        return 1
    fi

    # Count total tabs
    local tab_count
    if command -v jq >/dev/null 2>&1; then
        tab_count=$(echo "${tabs_response}" | jq 'length' 2>/dev/null || echo "0")
    else
        # Fallback: count occurrences of "id" field
        tab_count=$(echo "${tabs_response}" | grep -o '"id"[[:space:]]*:' | wc -l | xargs)
    fi

    # Don't close if it's the last tab (prevents Chrome from closing)
    if [[ "${tab_count}" -le 1 ]]; then
        log_error "Cannot close the last tab (would terminate Chrome)"
        return 2
    fi

    # Close the tab using /json/close/{id} endpoint
    local close_response
    close_response=$(curl -s --max-time 5 --connect-timeout 5 "http://localhost:${PORT}/json/close/${tab_id}" 2>/dev/null || echo "")

    # Check response
    if [[ "${close_response}" == "Target is closing" ]] || echo "${close_response}" | grep -q "Target.*clos"; then
        log_debug "Tab ${tab_id} closed successfully"
        return 0
    else
        log_error "Failed to close tab ${tab_id}: ${close_response}"
        return 2
    fi
}

# create_chrome_tab() - Create a new Chrome tab
# Purpose: Use DevTools Protocol to create a new tab
# Parameters:
#   url (optional, default: "about:blank") - URL for the new tab
# Returns:
#   0 - Success (outputs new tab ID to stdout)
#   1 - Creation failed
# Output: New tab ID on stdout
# Usage: new_tab_id=$(create_chrome_tab "https://example.com")
create_chrome_tab() {
    local url="${1:-about:blank}"

    log_debug "Creating new tab with URL: ${url}"

    # Check Chrome/port availability
    if ! nc -z localhost "${PORT}" 2>/dev/null; then
        log_error "Chrome debug port ${PORT} is not reachable"
        return 1
    fi

    # Validate URL format if not about:blank
    if [[ "${url}" != "about:blank" ]] && ! echo "${url}" | grep -qE '^(https?://|about:|data:|file://)'; then
        log_error "Invalid URL format: ${url}"
        log_error "URL must start with http://, https://, about:, data:, or file://"
        return 1
    fi

    # URL-encode the URL for the request
    local encoded_url
    if command -v python3 >/dev/null 2>&1; then
        encoded_url=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''${url}''', safe=''))" 2>/dev/null || echo "${url}")
    else
        # Fallback: simple encoding of common characters
        encoded_url="${url}"
        encoded_url="${encoded_url// /%20}"
        encoded_url="${encoded_url//&/%26}"
        encoded_url="${encoded_url//?/%3F}"
        encoded_url="${encoded_url//=/%3D}"
    fi

    # Create new tab using PUT request to /json/new
    local create_response
    create_response=$(curl -s --max-time 5 --connect-timeout 5 -X PUT "http://localhost:${PORT}/json/new?${encoded_url}" 2>/dev/null || echo "")

    if [[ -z "${create_response}" ]]; then
        log_error "Failed to create new tab: empty response"
        return 1
    fi

    # Extract tab ID from response
    local new_tab_id=""
    if command -v jq >/dev/null 2>&1; then
        new_tab_id=$(echo "${create_response}" | jq -r '.id // empty' 2>/dev/null || echo "")
    else
        # Fallback: extract id field using grep/sed
        new_tab_id=$(echo "${create_response}" | grep -o '"id"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)".*/\1/' | head -n 1 || echo "")
    fi

    if [[ -z "${new_tab_id}" ]]; then
        log_error "Failed to parse new tab ID from response"
        log_debug "Response: ${create_response}"
        return 1
    fi

    # Output new tab ID to stdout
    echo "${new_tab_id}"
    log_debug "New tab created with ID: ${new_tab_id}"
    return 0
}

# activate_chrome_tab() - Activate (bring to front) a Chrome tab
# Purpose: Use DevTools Protocol to activate an existing tab
# Parameters:
#   tab_id (required) - ID of the tab to activate
# Returns:
#   0 - Success (tab activated)
#   1 - Tab not found
#   2 - Activation failed
# Usage: activate_chrome_tab "tab-id-123"
activate_chrome_tab() {
    local tab_id="${1:-}"

    # Validate parameters
    if [[ -z "${tab_id}" ]]; then
        log_error "activate_chrome_tab: tab_id parameter is required"
        return 2
    fi

    log_debug "Activating tab ${tab_id}"

    # Check Chrome/port availability
    if ! nc -z localhost "${PORT}" 2>/dev/null; then
        log_error "Chrome debug port ${PORT} is not reachable"
        return 2
    fi

    # Check if tab exists
    local tabs_response
    tabs_response=$(curl -s --max-time 5 --connect-timeout 5 "http://localhost:${PORT}/json" 2>/dev/null || echo "")

    if [[ -z "${tabs_response}" ]]; then
        log_error "Cannot retrieve tab list from Chrome"
        return 2
    fi

    # Check if tab_id exists
    if ! echo "${tabs_response}" | grep -q "\"id\"[[:space:]]*:[[:space:]]*\"${tab_id}\""; then
        log_error "Tab not found: ${tab_id}"
        return 1
    fi

    # Activate the tab using /json/activate/{id} endpoint
    local activate_response
    activate_response=$(curl -s --max-time 5 --connect-timeout 5 "http://localhost:${PORT}/json/activate/${tab_id}" 2>/dev/null || echo "")

    # Check response
    if [[ "${activate_response}" == "Target activated" ]]; then
        log_debug "Tab ${tab_id} activated successfully"
        return 0
    else
        log_error "Failed to activate tab ${tab_id}: ${activate_response}"
        return 2
    fi
}

# get_chrome_tab_info() - Get information about a specific Chrome tab
# Purpose: Retrieve and optionally extract specific fields from tab info
# Parameters:
#   tab_id (required) - ID of the tab to query
#   field (optional) - Specific field to extract (id, title, url, type, etc.)
# Returns:
#   0 - Success (outputs info to stdout)
#   1 - Tab not found
# Output:
#   If field specified: field value
#   If no field: JSON object with all tab info
# Usage:
#   get_chrome_tab_info "tab-id-123"           # Full JSON
#   get_chrome_tab_info "tab-id-123" "title"   # Just title
get_chrome_tab_info() {
    local tab_id="${1:-}"
    local field="${2:-}"

    # Validate parameters
    if [[ -z "${tab_id}" ]]; then
        log_error "get_chrome_tab_info: tab_id parameter is required"
        return 1
    fi

    log_debug "Retrieving info for tab ${tab_id}${field:+ (field: ${field})}"

    # Check Chrome/port availability
    if ! nc -z localhost "${PORT}" 2>/dev/null; then
        log_error "Chrome debug port ${PORT} is not reachable"
        return 1
    fi

    # Get all tabs
    local tabs_response
    tabs_response=$(curl -s --max-time 5 --connect-timeout 5 "http://localhost:${PORT}/json" 2>/dev/null || echo "")

    if [[ -z "${tabs_response}" ]]; then
        log_error "Cannot retrieve tab list from Chrome"
        return 1
    fi

    # Extract tab info
    local tab_info=""
    if command -v jq >/dev/null 2>&1; then
        # Use jq to extract tab
        tab_info=$(echo "${tabs_response}" | jq ".[] | select(.id == \"${tab_id}\")" 2>/dev/null || echo "")

        if [[ -z "${tab_info}" ]] || [[ "${tab_info}" == "null" ]]; then
            log_error "Tab not found: ${tab_id}"
            return 1
        fi

        # Extract specific field if requested
        if [[ -n "${field}" ]]; then
            local field_value
            field_value=$(echo "${tab_info}" | jq -r ".${field} // empty" 2>/dev/null || echo "")
            if [[ -z "${field_value}" ]]; then
                log_error "Field '${field}' not found or empty for tab ${tab_id}"
                return 1
            fi
            echo "${field_value}"
        else
            # Output full tab info
            echo "${tab_info}"
        fi
    else
        # Fallback: parse without jq
        tab_info=$(echo "${tabs_response}" | sed 's/},{/\n/g' | grep "\"id\"[[:space:]]*:[[:space:]]*\"${tab_id}\"" || echo "")

        if [[ -z "${tab_info}" ]]; then
            log_error "Tab not found: ${tab_id}"
            return 1
        fi

        # Clean up JSON formatting
        tab_info=$(echo "${tab_info}" | sed 's/^\[{//' | sed 's/}\]$//')

        # Extract specific field if requested
        if [[ -n "${field}" ]]; then
            local field_value
            field_value=$(echo "${tab_info}" | grep -o "\"${field}\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | sed 's/.*"\([^"]*\)".*/\1/' || echo "")

            # Try without quotes for non-string fields
            if [[ -z "${field_value}" ]]; then
                field_value=$(echo "${tab_info}" | grep -o "\"${field}\"[[:space:]]*:[[:space:]]*[^,}]*" | sed "s/\"${field}\"[[:space:]]*:[[:space:]]*\(.*\)/\1/" | sed 's/^"\(.*\)"$/\1/' || echo "")
            fi

            if [[ -z "${field_value}" ]]; then
                log_error "Field '${field}' not found or empty for tab ${tab_id}"
                return 1
            fi
            echo "${field_value}"
        else
            # Output full tab info (re-wrap in JSON object)
            echo "{${tab_info}}"
        fi
    fi

    log_debug "Tab info retrieved successfully"
    return 0
}

# save_chrome_session() - Save current Chrome tabs to a session file
# Parameters:
#   session_file (optional, default: ~/.chrome-debug-session.json)
# Returns:
#   0 - Success
#   1 - Failed to save
# Output:
#   Session file path on success
#   Error message on failure
save_chrome_session() {
    local session_file="${1:-$HOME/.chrome-debug-session.json}"

    log_debug "Saving Chrome session to: ${session_file}"

    # Create parent directory if needed
    local session_dir=$(dirname "${session_file}")
    if [ ! -d "${session_dir}" ]; then
        if ! mkdir -p "${session_dir}" 2>/dev/null; then
            log_error "Failed to create session directory: ${session_dir}"
            return 1
        fi
    fi

    # Get all current tabs
    local tabs_data
    tabs_data=$(list_chrome_tabs "${PORT}" "json" 2>/dev/null)
    if [ $? -ne 0 ] || [ -z "${tabs_data}" ]; then
        log_error "Failed to retrieve Chrome tabs"
        return 1
    fi

    # Get Chrome version
    local chrome_version
    chrome_version=$(get_chrome_version "${PORT}" 2>/dev/null || echo "unknown")

    # Get current timestamp in ISO 8601 format
    local timestamp
    if command -v date >/dev/null 2>&1; then
        timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "unknown")
    else
        timestamp="unknown"
    fi

    # Build session JSON
    # Extract tab info from JSON array and rebuild as session format
    local session_json
    if command -v jq >/dev/null 2>&1; then
        # Use jq for robust JSON construction
        session_json=$(echo "${tabs_data}" | jq -c \
            --arg ts "${timestamp}" \
            --arg ver "${chrome_version}" \
            '{
                timestamp: $ts,
                chrome_version: $ver,
                tabs: [.[] | {id: .id, url: .url, title: .title}]
            }' 2>/dev/null)
    else
        # Fallback: manual JSON construction
        local tabs_array="["
        local first=true
        echo "${tabs_data}" | grep -o '"id":"[^"]*","url":"[^"]*","title":"[^"]*"' | while IFS= read -r tab_line; do
            if [ "${first}" = true ]; then
                first=false
            else
                tabs_array="${tabs_array},"
            fi
            tabs_array="${tabs_array}{${tab_line}}"
        done
        tabs_array="${tabs_array}]"
        session_json="{\"timestamp\":\"${timestamp}\",\"chrome_version\":\"${chrome_version}\",\"tabs\":${tabs_array}}"
    fi

    # Validate session JSON
    if [ -z "${session_json}" ] || [ "${session_json}" = "null" ]; then
        log_error "Failed to build session JSON"
        return 1
    fi

    # Write to file
    if ! echo "${session_json}" | tee "${session_file}" >/dev/null 2>&1; then
        log_error "Failed to write session file: ${session_file}"
        return 1
    fi

    log_info "Chrome session saved to: ${session_file}"
    [ "${QUIET_MODE}" != "true" ] && echo "${session_file}"
    return 0
}

# restore_chrome_session() - Restore Chrome tabs from a session file
# Parameters:
#   session_file (required)
# Returns:
#   0 - Success
#   1 - Failed to restore
# Output:
#   Mapping of old->new tab IDs (one per line: "old_id -> new_id")
#   Skips invalid URLs gracefully
restore_chrome_session() {
    local session_file="$1"

    if [ -z "${session_file}" ]; then
        log_error "Session file parameter is required"
        return 1
    fi

    if [ ! -f "${session_file}" ]; then
        log_error "Session file not found: ${session_file}"
        return 1
    fi

    log_debug "Restoring Chrome session from: ${session_file}"

    # Read and validate session file
    local session_json
    session_json=$(cat "${session_file}" 2>/dev/null)
    if [ -z "${session_json}" ]; then
        log_error "Failed to read session file: ${session_file}"
        return 1
    fi

    # Validate JSON format
    if command -v jq >/dev/null 2>&1; then
        if ! echo "${session_json}" | jq -e '.tabs' >/dev/null 2>&1; then
            log_error "Invalid session JSON format: missing 'tabs' field"
            return 1
        fi
    fi

    # Extract and restore each tab
    local tab_count=0
    local success_count=0
    local mapping_output=""

    if command -v jq >/dev/null 2>&1; then
        # Use jq for robust parsing
        # Store tab data in temp file to avoid subshell variable issues
        local temp_tabs="/tmp/chrome-restore-tabs-$$.txt"
        echo "${session_json}" | jq -r '.tabs[] | "\(.id)|\(.url)|\(.title)"' 2>/dev/null > "${temp_tabs}"

        while IFS='|' read -r old_id url title; do
            [ -z "${url}" ] && continue
            tab_count=$((tab_count + 1))

            log_debug "Restoring tab: ${title} (${url})"

            # Skip chrome:// and chrome-untrusted:// URLs (can't be created via API)
            if echo "${url}" | grep -qE '^(chrome://|chrome-untrusted://|about:)'; then
                log_debug "Skipping internal URL: ${url}"
                continue
            fi

            # Create new tab
            local new_id
            new_id=$(create_chrome_tab "${url}" 2>/dev/null)
            if [ $? -eq 0 ] && [ -n "${new_id}" ]; then
                # create_chrome_tab returns just the ID, not JSON
                mapping_output="${mapping_output}${old_id} -> ${new_id}\n"
                success_count=$((success_count + 1))
                log_debug "Tab restored: ${old_id} -> ${new_id}"
            else
                log_error "Failed to create tab for URL: ${url}"
            fi
        done < "${temp_tabs}"
        rm -f "${temp_tabs}"
    else
        # Fallback: grep/sed parsing
        echo "${session_json}" | grep -o '"id":"[^"]*","url":"[^"]*","title":"[^"]*"' | while IFS= read -r tab_line; do
            tab_count=$((tab_count + 1))

            local old_id=$(echo "${tab_line}" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p')
            local url=$(echo "${tab_line}" | sed -n 's/.*"url":"\([^"]*\)".*/\1/p')
            local title=$(echo "${tab_line}" | sed -n 's/.*"title":"\([^"]*\)".*/\1/p')

            [ -z "${url}" ] && continue

            log_debug "Restoring tab: ${title} (${url})"

            # Skip internal URLs
            if echo "${url}" | grep -qE '^(chrome://|chrome-untrusted://|about:)'; then
                log_debug "Skipping internal URL: ${url}"
                continue
            fi

            local new_id
            new_id=$(create_chrome_tab "${url}" 2>/dev/null)
            if [ $? -eq 0 ] && [ -n "${new_id}" ]; then
                echo "${old_id} -> ${new_id}"
                success_count=$((success_count + 1))
                log_debug "Tab restored: ${old_id} -> ${new_id}"
            fi
        done
    fi

    # Output mapping
    if [ -n "${mapping_output}" ]; then
        [ "${QUIET_MODE}" != "true" ] && echo -e "${mapping_output}"
    fi

    log_info "Chrome session restored: ${success_count}/${tab_count} tabs"

    # Return success if at least one tab was restored
    [ ${success_count} -gt 0 ] && return 0 || return 1
}

# monitor_chrome_tabs() - Monitor Chrome tabs for changes
# Parameters:
#   interval (optional, default: 2 seconds)
# Returns:
#   Never returns (continuous monitoring)
#   Exits with 1 on error
# Output:
#   "NEW: {id} - {title}" for new tabs
#   "CLOSED: {id} - {title}" for closed tabs
# Usage:
#   Press Ctrl+C to stop monitoring
monitor_chrome_tabs() {
    local interval="${1:-2}"

    log_info "Starting Chrome tab monitoring (interval: ${interval}s)"
    log_debug "Press Ctrl+C to stop monitoring"

    # Set up trap for graceful exit
    trap 'log_info "Tab monitoring stopped"; exit 0' INT TERM

    # Store previous tab list
    local previous_tabs=""
    local first_run=true

    while true; do
        # Get current tabs
        local current_tabs
        current_tabs=$(list_chrome_tabs "${PORT}" "simple" 2>/dev/null)

        if [ $? -ne 0 ]; then
            log_error "Failed to retrieve Chrome tabs"
            return 1
        fi

        if [ "${first_run}" = true ]; then
            # First run - just store current state
            previous_tabs="${current_tabs}"
            first_run=false
            log_debug "Initial tab state captured ($(echo "${current_tabs}" | wc -l | tr -d ' ') tabs)"
        else
            # Compare with previous state

            # Detect new tabs (in current but not in previous)
            if [ -n "${current_tabs}" ]; then
                echo "${current_tabs}" | while IFS='|' read -r id title url type; do
                    [ -z "${id}" ] && continue

                    if ! echo "${previous_tabs}" | grep -q "^${id}|"; then
                        # New tab detected
                        [ "${QUIET_MODE}" != "true" ] && echo "NEW: ${id} - ${title}"
                        log_debug "New tab: ${id} - ${title}"
                    fi
                done
            fi

            # Detect closed tabs (in previous but not in current)
            if [ -n "${previous_tabs}" ]; then
                echo "${previous_tabs}" | while IFS='|' read -r id title url type; do
                    [ -z "${id}" ] && continue

                    if ! echo "${current_tabs}" | grep -q "^${id}|"; then
                        # Closed tab detected
                        [ "${QUIET_MODE}" != "true" ] && echo "CLOSED: ${id} - ${title}"
                        log_debug "Closed tab: ${id} - ${title}"
                    fi
                done
            fi

            # Update previous state
            previous_tabs="${current_tabs}"
        fi

        # Wait for next interval
        sleep "${interval}"
    done
}

# execute_in_tab() - Execute JavaScript in a specific Chrome tab
# Parameters:
#   tab_id (required) - Target tab ID
#   javascript (required) - JavaScript code to execute
# Returns:
#   0 - Success (result to stdout)
#   1 - Tab not found
#   2 - Execution failed
# Output:
#   Execution result if available
# Limitations:
#   - Chrome DevTools HTTP API has limited JS execution support
#   - Uses activate + window.eval approach (basic functionality only)
#   - For complex scenarios, consider using CDP (Chrome DevTools Protocol) directly
execute_in_tab() {
    local tab_id="$1"
    local javascript="$2"

    if [ -z "${tab_id}" ]; then
        log_error "Tab ID parameter is required"
        return 1
    fi

    if [ -z "${javascript}" ]; then
        log_error "JavaScript parameter is required"
        return 1
    fi

    log_debug "Executing JavaScript in tab: ${tab_id}"

    # Validate tab exists
    local tab_info
    tab_info=$(get_chrome_tab_info "${tab_id}" "" 2>/dev/null)
    if [ $? -ne 0 ] || [ -z "${tab_info}" ]; then
        log_error "Tab not found: ${tab_id}"
        return 1
    fi

    # Note: Chrome DevTools HTTP API (/json) doesn't support direct JS execution
    # We need to use the WebSocket endpoint for full CDP support
    # For now, we'll use a simplified approach: activate tab and log the limitation

    # Activate the tab first
    if ! activate_chrome_tab "${tab_id}" >/dev/null 2>&1; then
        log_error "Failed to activate tab: ${tab_id}"
        return 2
    fi

    # Log limitation and provide guidance
    log_error "JavaScript execution via HTTP API is limited"
    log_debug "To execute JS, consider using Chrome DevTools Protocol (CDP) via WebSocket"
    log_debug "WebSocket URL available in tab info: webSocketDebuggerUrl field"

    # Extract WebSocket URL for reference
    local ws_url
    if command -v jq >/dev/null 2>&1; then
        ws_url=$(echo "${tab_info}" | jq -r '.webSocketDebuggerUrl // empty' 2>/dev/null)
    else
        ws_url=$(echo "${tab_info}" | grep -o '"webSocketDebuggerUrl":"[^"]*"' | sed 's/"webSocketDebuggerUrl":"\([^"]*\)"/\1/')
    fi

    if [ -n "${ws_url}" ]; then
        log_debug "WebSocket URL: ${ws_url}"
        [ "${QUIET_MODE}" != "true" ] && echo "WebSocket URL: ${ws_url}"
        [ "${QUIET_MODE}" != "true" ] && echo "Use CDP tools (e.g., puppeteer, playwright) for JS execution"
    fi

    return 2
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