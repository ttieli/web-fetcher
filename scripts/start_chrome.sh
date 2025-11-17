#!/bin/bash
#
# Chrome CDP Debug Mode Launcher
#
# 启动Chrome浏览器的远程调试模式,用于CDP (Chrome DevTools Protocol) 抓取
# 支持 macOS, Linux, Windows (Git Bash/WSL)
#
# 功能:
# - 在独立的用户数据目录运行Chrome,避免与正常浏览器冲突
# - 开启远程调试端口 9222
# - 保持会话状态 (cookies, localStorage等)
# - 自动恢复上次会话
#
# 使用方法:
#   chmod +x scripts/start_chrome.sh
#   ./scripts/start_chrome.sh
#
# Author: WebFetcher Team
# Version: 1.0.0

set -e

echo "================================================"
echo "  Chrome CDP Debug Mode Launcher"
echo "================================================"
echo ""

# 检测操作系统并设置Chrome路径
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    USER_DATA="$HOME/Library/Application Support/Google/Chrome-CDP"
    OS_NAME="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    CHROME="google-chrome"
    # 如果google-chrome不存在,尝试其他常见名称
    if ! command -v google-chrome &> /dev/null; then
        if command -v google-chrome-stable &> /dev/null; then
            CHROME="google-chrome-stable"
        elif command -v chromium-browser &> /dev/null; then
            CHROME="chromium-browser"
        elif command -v chromium &> /dev/null; then
            CHROME="chromium"
        else
            echo "错误: 未找到Chrome/Chromium浏览器"
            echo "请安装: sudo apt install google-chrome-stable"
            exit 1
        fi
    fi
    USER_DATA="$HOME/.config/google-chrome-cdp"
    OS_NAME="Linux"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    # Windows (Git Bash / WSL)
    CHROME="/c/Program Files/Google/Chrome/Application/chrome.exe"
    if [[ ! -f "$CHROME" ]]; then
        CHROME="/c/Program Files (x86)/Google/Chrome/Application/chrome.exe"
    fi
    USER_DATA="$USERPROFILE/AppData/Local/Google/Chrome/CDP"
    OS_NAME="Windows"
else
    echo "错误: 不支持的操作系统: $OSTYPE"
    exit 1
fi

echo "检测到操作系统: $OS_NAME"
echo "Chrome路径: $CHROME"
echo "用户数据目录: $USER_DATA"
echo ""

# 检查Chrome是否存在
if [[ ! -f "$CHROME" ]] && ! command -v "$CHROME" &> /dev/null; then
    echo "错误: Chrome未安装或路径不正确"
    echo "Chrome路径: $CHROME"
    echo ""
    echo "解决方法:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  brew install --cask google-chrome"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  sudo apt install google-chrome-stable"
        echo "  或: sudo apt install chromium-browser"
    else
        echo "  请从 https://www.google.com/chrome/ 下载安装"
    fi
    exit 1
fi

# 创建用户数据目录
mkdir -p "$USER_DATA"

# 检查端口9222是否被占用
if command -v lsof &> /dev/null; then
    if lsof -Pi :9222 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "警告: 端口9222已被占用"
        echo ""
        read -p "是否要终止占用端口9222的进程? [y/N] " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "正在终止占用端口9222的进程..."
            lsof -ti:9222 | xargs kill -9 2>/dev/null || true
            sleep 1
        else
            echo "已取消启动"
            exit 1
        fi
    fi
fi

# 启动Chrome
echo "正在启动Chrome (调试模式)..."
echo ""

"$CHROME" \
  --remote-debugging-port=9222 \
  --user-data-dir="$USER_DATA" \
  --no-first-run \
  --no-default-browser-check \
  --disable-gpu \
  --window-size=1200,900 \
  --restore-last-session \
  > /dev/null 2>&1 &

CHROME_PID=$!

# 等待Chrome启动
sleep 2

# 验证Chrome是否成功启动
if ps -p $CHROME_PID > /dev/null; then
    echo "✅ Chrome已成功启动!"
    echo ""
    echo "调试信息:"
    echo "  进程ID: $CHROME_PID"
    echo "  调试端口: http://localhost:9222"
    echo "  DevTools: http://localhost:9222/json"
    echo ""
    echo "现在可以使用CDP抓取功能了!"
    echo ""
    echo "使用方法:"
    echo "  wf <url> --use-cdp              # 使用CDP模式抓取"
    echo "  python -m webfetcher.cli <url> --use-cdp"
    echo ""
    echo "提示: Chrome窗口关闭后,CDP功能将不可用"
else
    echo "❌ Chrome启动失败"
    echo ""
    echo "可能的原因:"
    echo "  1. Chrome路径不正确"
    echo "  2. 端口9222被占用"
    echo "  3. 权限不足"
    echo ""
    echo "调试方法:"
    echo "  手动运行以下命令查看错误信息:"
    echo "  \"$CHROME\" --remote-debugging-port=9222 --user-data-dir=\"$USER_DATA\""
    exit 1
fi
