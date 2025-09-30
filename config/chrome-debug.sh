#!/bin/bash
# 启动带远程调试端口的 Chrome，会复用指定的用户配置目录
# 如果Chrome已经运行，则只打开新标签页而不启动新实例
set -euo pipefail

CHROME_APP="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PROFILE_DIR="${HOME}/.chrome-wf"
PORT="9222"

# 创建用户配置目录
mkdir -p "${PROFILE_DIR}"

# 检查是否已有Chrome debug实例在运行
check_chrome_debug_running() {
    # 检查是否有进程使用了指定的调试端口和用户目录
    if pgrep -f "remote-debugging-port=${PORT}.*user-data-dir=${PROFILE_DIR}" >/dev/null 2>&1; then
        return 0  # 已运行
    else
        return 1  # 未运行
    fi
}

# 如果Chrome debug实例已运行，只打开新标签页
if check_chrome_debug_running; then
    # 如果没有提供URL参数，打开新标签页到空白页
    if [ $# -eq 0 ]; then
        URL="chrome://newtab/"
    else
        URL="$1"
    fi
    
    # 使用osascript通过AppleScript打开新标签页
    osascript -e "
        tell application \"Google Chrome\"
            set targetWindow to first window
            set newTab to make new tab at targetWindow with properties {URL:\"$URL\"}
            activate
        end tell
    " 2>/dev/null || {
        # 如果AppleScript失败，使用open命令
        open -a "Google Chrome" "$URL" 2>/dev/null || true
    }
    
    echo "Chrome debug实例已运行，已打开新标签页"
else
    # Chrome debug实例未运行，启动新实例
    echo "启动Chrome debug实例..."
    exec "${CHROME_APP}" \
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
      "$@"
fi
