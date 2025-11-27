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

    # 启动标志说明 / Launch Flags Explanation:
    #
    # --remote-debugging-port=${PORT}
    #   启用Chrome DevTools协议的远程调试端口
    #   Enable Chrome DevTools Protocol remote debugging port
    #
    # --user-data-dir="${PROFILE_DIR}"
    #   指定Chrome用户配置目录，确保使用独立的配置文件
    #   Specify Chrome user data directory for isolated profile
    #
    # --remote-allow-origins=*  【关键标志 / CRITICAL FLAG】
    #   允许所有来源访问远程调试端口，解决CORS限制
    #   这是Selenium WebDriver连接成功的必需标志
    #   Allow all origins to access remote debugging port, resolving CORS restrictions
    #   Required for Selenium WebDriver to successfully connect
    #
    # --no-first-run
    #   跳过首次运行向导，避免弹出欢迎页面
    #   Skip first-run wizard and welcome page
    #
    # --no-default-browser-check
    #   禁用默认浏览器检查提示
    #   Disable default browser check prompt
    #
    # --disable-popup-blocking
    #   禁用弹窗阻止功能，确保自动化测试中的弹窗正常显示
    #   Disable popup blocking for automated testing
    #
    # --disable-translate
    #   禁用页面翻译提示，减少不必要的界面干扰
    #   Disable translation prompts
    #
    # --disable-background-timer-throttling
    #   禁用后台标签页的定时器节流，确保后台脚本正常运行
    #   Disable background tab timer throttling for consistent script execution
    #
    # --disable-renderer-backgrounding
    #   禁用渲染器后台化，确保后台标签页的渲染正常进行
    #   Disable renderer backgrounding for consistent rendering
    #
    # --disable-device-discovery-notifications
    #   禁用设备发现通知（如投屏设备提示）
    #   Disable device discovery notifications
fi
