#!/bin/bash
# 启动Chrome远程调试模式（支持CDP连接）
# 用于WebFetcher的CDP采集功能

set -e

echo "=================================================="
echo " 启动 Chrome 远程调试模式（CDP）"
echo "=================================================="

# 检测操作系统并设置Chrome路径
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    USER_DATA="$HOME/Library/Application Support/Google/Chrome-CDP"
    echo "检测到 macOS 系统"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    CHROME="google-chrome"
    USER_DATA="$HOME/.config/google-chrome-cdp"
    echo "检测到 Linux 系统"
else
    # Windows (Git Bash / WSL)
    CHROME="/c/Program Files/Google/Chrome/Application/chrome.exe"
    USER_DATA="$USERPROFILE/AppData/Local/Google/Chrome/CDP"
    echo "检测到 Windows 系统"
fi

# 创建用户数据目录
mkdir -p "$USER_DATA"

# 远程调试端口
DEBUG_PORT=9222

# 检查Chrome是否已经在运行
if lsof -Pi :$DEBUG_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✓ Chrome调试端口 $DEBUG_PORT 已在使用"
    echo "  Chrome可能已经在调试模式下运行"
    echo "  如需重启，请先关闭Chrome进程"
    echo ""
    echo "当前监听端口的进程："
    lsof -Pi :$DEBUG_PORT -sTCP:LISTEN
    echo ""
    echo "访问: http://localhost:$DEBUG_PORT"
    exit 0
fi

# 检查Chrome可执行文件是否存在
if [[ ! -x "$CHROME" ]]; then
    echo "❌ 错误: 未找到Chrome可执行文件"
    echo "   路径: $CHROME"
    echo ""
    echo "请安装Google Chrome或修改脚本中的CHROME变量"
    exit 1
fi

echo ""
echo "配置信息:"
echo "  Chrome路径: $CHROME"
echo "  数据目录: $USER_DATA"
echo "  调试端口: $DEBUG_PORT"
echo ""

# 启动Chrome（后台模式）
echo "正在启动Chrome..."

"$CHROME" \
  --remote-debugging-port=$DEBUG_PORT \
  --remote-allow-origins=* \
  --user-data-dir="$USER_DATA" \
  --no-first-run \
  --no-default-browser-check \
  --disable-gpu \
  --window-size=1200,900 \
  --restore-last-session \
  > /dev/null 2>&1 &

CHROME_PID=$!

# 等待Chrome启动
echo "等待Chrome启动..."
sleep 2

# 验证Chrome是否成功启动
if lsof -Pi :$DEBUG_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo ""
    echo "=================================================="
    echo "✓ Chrome已成功启动！"
    echo "=================================================="
    echo ""
    echo "调试端点:"
    echo "  http://localhost:$DEBUG_PORT"
    echo ""
    echo "查看所有标签页:"
    echo "  http://localhost:$DEBUG_PORT/json"
    echo ""
    echo "DevTools界面:"
    echo "  chrome://inspect"
    echo ""
    echo "进程ID: $CHROME_PID"
    echo ""
    echo "停止Chrome:"
    echo "  kill $CHROME_PID"
    echo "  或直接关闭Chrome窗口"
    echo ""
    echo "=================================================="
else
    echo ""
    echo "❌ Chrome启动失败"
    echo "   端口 $DEBUG_PORT 未被监听"
    echo ""
    echo "可能的原因:"
    echo "  1. Chrome路径错误"
    echo "  2. 端口被占用"
    echo "  3. 权限不足"
    echo ""
    echo "请检查错误日志"
    exit 1
fi
