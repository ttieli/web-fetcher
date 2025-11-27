#!/bin/bash
# Chrome Debug Background Launcher
# Implements reliable background Chrome launch with process management and concurrency control
#
# Interface Contract:
# - Input: No parameters
# - Output (success): Exit code 0, outputs PID to stdout
# - Output (failure): Exit code non-zero, error message to stderr
# - Side effects: Creates PID/lock files, launches Chrome
#
# Error Codes:
# 0 - Success
# 1 - General error
# 2 - Lock acquisition failed
# 3 - Chrome launch failed
# 4 - Permission error
# 5 - Port already in use

set -euo pipefail

# Configuration
CHROME_APP="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PROFILE_DIR="${HOME}/.chrome-wf"
PORT="9222"
PID_FILE="${PROFILE_DIR}/.chrome-debug.pid"
LOCK_FILE="${PROFILE_DIR}/.chrome-debug.lock"
LOCK_FD=200

# Logging functions
log_info() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') $*" >&2
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') $*" >&2
}

# Ensure working directory exists
ensure_working_directory() {
    if ! mkdir -p "${PROFILE_DIR}" 2>/dev/null; then
        log_error "Failed to create profile directory: ${PROFILE_DIR}"
        exit 4
    fi
}

# acquire_lock() - Non-blocking lock using mkdir (atomic on POSIX)
# Returns: 0 on success, 2 on failure
acquire_lock() {
    local lock_dir="${LOCK_FILE}.d"
    local max_age=300  # 5 minutes

    # Check if lock directory exists and is stale
    if [[ -d "${lock_dir}" ]]; then
        local lock_age
        lock_age=$(( $(date +%s) - $(stat -f %m "${lock_dir}" 2>/dev/null || echo 0) ))

        if [[ ${lock_age} -gt ${max_age} ]]; then
            log_info "Removing stale lock (age: ${lock_age}s)"
            rmdir "${lock_dir}" 2>/dev/null || true
        fi
    fi

    # Try to acquire lock using atomic mkdir
    if mkdir "${lock_dir}" 2>/dev/null; then
        log_info "Lock acquired successfully"
        # Store our PID in the lock directory
        echo $$ > "${lock_dir}/pid"
        return 0
    else
        log_error "Failed to acquire lock. Another launcher process may be running."
        return 2
    fi
}

# release_lock() - Release the lock
release_lock() {
    local lock_dir="${LOCK_FILE}.d"
    if [[ -d "${lock_dir}" ]]; then
        rm -rf "${lock_dir}"
        log_info "Lock released"
    fi
}

# check_existing_chrome() - Verify Chrome process is running
# Returns: 0 if valid Chrome process exists, 1 otherwise
check_existing_chrome() {
    if [[ ! -f "${PID_FILE}" ]]; then
        log_info "No PID file found"
        return 1
    fi

    local pid
    pid=$(cat "${PID_FILE}" 2>/dev/null || echo "")

    if [[ -z "${pid}" ]]; then
        log_info "PID file is empty"
        return 1
    fi

    # Validate PID is numeric
    if ! [[ "${pid}" =~ ^[0-9]+$ ]]; then
        log_error "Invalid PID format in file: ${pid}"
        return 1
    fi

    # Check if process exists
    if ! kill -0 "${pid}" 2>/dev/null; then
        log_info "Process ${pid} is not running"
        return 1
    fi

    # Verify it's actually a Chrome process with our debug port
    if pgrep -f "remote-debugging-port=${PORT}.*user-data-dir=${PROFILE_DIR}" | grep -q "^${pid}$"; then
        log_info "Valid Chrome debug process found: ${pid}"
        return 0
    else
        log_info "Process ${pid} exists but is not our Chrome debug instance"
        return 1
    fi
}

# cleanup_stale_pid() - Clean up invalid PID file
cleanup_stale_pid() {
    if [[ -f "${PID_FILE}" ]]; then
        local old_pid
        old_pid=$(cat "${PID_FILE}" 2>/dev/null || echo "unknown")
        log_info "Cleaning up stale PID file (PID: ${old_pid})"
        rm -f "${PID_FILE}"
    fi
}

# check_port_available() - Check if debug port is available
check_port_available() {
    if lsof -Pi :${PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_error "Port ${PORT} is already in use by another process"
        return 5
    fi
    return 0
}

# launch_chrome_background() - Launch Chrome in background
# Returns: 0 on success, 3 on failure
# Outputs: PID to stdout on success
launch_chrome_background() {
    log_info "Launching Chrome in background..."

    # Check if Chrome executable exists
    if [[ ! -x "${CHROME_APP}" ]]; then
        log_error "Chrome executable not found or not executable: ${CHROME_APP}"
        return 3
    fi

    # Check if port is available
    if ! check_port_available; then
        return 5
    fi

    # Launch Chrome in background using nohup
    local log_file="${PROFILE_DIR}/chrome-debug.log"

    nohup "${CHROME_APP}" \
        --remote-debugging-port="${PORT}" \
        --user-data-dir="${PROFILE_DIR}" \
        --remote-allow-origins=* \
        --no-first-run \
        --no-default-browser-check \
        --disable-popup-blocking \
        --disable-translate \
        --disable-background-timer-throttling \
        --disable-renderer-backgrounding \
        --disable-device-discovery-notifications \
        --headless=new \
        > "${log_file}" 2>&1 &

    local chrome_pid=$!

    # Verify PID is valid
    if ! kill -0 "${chrome_pid}" 2>/dev/null; then
        log_error "Chrome process failed to start or exited immediately"
        return 3
    fi

    log_info "Chrome launched with PID: ${chrome_pid}"
    echo "${chrome_pid}" > "${PID_FILE}"

    return 0
}

# verify_chrome_started() - Verify Chrome debug endpoint is accessible
# Returns: 0 on success, 3 on failure
verify_chrome_started() {
    local max_retries=10
    local retry_interval=0.5
    local retry_count=0

    log_info "Verifying Chrome debug endpoint..."

    while [[ ${retry_count} -lt ${max_retries} ]]; do
        if curl -s "http://localhost:${PORT}/json/version" >/dev/null 2>&1; then
            log_info "Chrome debug endpoint is accessible"
            return 0
        fi

        retry_count=$((retry_count + 1))
        log_info "Retry ${retry_count}/${max_retries}..."
        sleep ${retry_interval}
    done

    log_error "Chrome debug endpoint not accessible after ${max_retries} retries"
    cleanup_stale_pid
    return 3
}

# Main execution
main() {
    # Ensure working directory exists
    ensure_working_directory

    # Acquire lock
    if ! acquire_lock; then
        exit 2
    fi

    # Set trap to release lock on exit
    trap release_lock EXIT

    # Check if Chrome is already running
    if check_existing_chrome; then
        # Chrome is running, return existing PID
        local existing_pid
        existing_pid=$(cat "${PID_FILE}")
        log_info "Chrome already running with PID: ${existing_pid}"
        echo "${existing_pid}"
        exit 0
    fi

    # Clean up stale PID if exists
    cleanup_stale_pid

    # Launch Chrome
    if ! launch_chrome_background; then
        exit $?
    fi

    # Verify Chrome started successfully
    if ! verify_chrome_started; then
        exit 3
    fi

    # Output PID and exit successfully
    local chrome_pid
    chrome_pid=$(cat "${PID_FILE}")
    echo "${chrome_pid}"
    exit 0
}

# Execute main function
main "$@"