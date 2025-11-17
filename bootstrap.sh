#!/usr/bin/env bash
#
# WebFetcher Bootstrap Script for macOS/Linux
# 一键部署开发环境
#

set -e  # Exit on error

echo "======================================"
echo "WebFetcher Bootstrap / 环境部署"
echo "======================================"
echo ""

# 1. Create virtual environment / 创建虚拟环境
echo "▸ Creating virtual environment / 创建虚拟环境..."
python3 -m venv .venv

# 2. Activate virtual environment / 激活虚拟环境
echo "▸ Activating virtual environment / 激活虚拟环境..."
source .venv/bin/activate

# 3. Upgrade pip / 升级 pip
echo "▸ Upgrading pip / 升级 pip..."
pip install -U pip

# 4. Install webfetcher in editable mode with selenium support
# 以开发模式安装 webfetcher（含 Selenium 支持）
echo "▸ Installing webfetcher[selenium] in editable mode / 以开发模式安装..."
pip install -e .[selenium]

# 5. Run ChromeDriver management (if scripts exist)
# 运行 ChromeDriver 管理（如果脚本存在）
if [ -f "scripts/manage_chromedriver.py" ]; then
    echo "▸ Checking ChromeDriver compatibility / 检查 ChromeDriver 兼容性..."
    python scripts/manage_chromedriver.py || echo "⚠️  ChromeDriver check skipped / 跳过 ChromeDriver 检查"
fi

# 6. Create config directory if needed / 创建配置目录（如果需要）
echo "▸ Setting up config directory / 设置配置目录..."
mkdir -p ~/.config/webfetcher

# Copy default config if it doesn't exist / 复制默认配置（如果不存在）
if [ -f "config/routing.yaml" ] && [ ! -f ~/.config/webfetcher/routing.yaml ]; then
    cp config/routing.yaml ~/.config/webfetcher/routing.yaml
    echo "  ✓ Copied default routing config / 已复制默认路由配置"
fi

# 7. Make sure output directory exists / 确保输出目录存在
mkdir -p output

echo ""
echo "======================================"
echo "✓ Bootstrap Complete / 部署完成"
echo "======================================"
echo ""
echo "Next steps / 后续步骤:"
echo ""
echo "  1. Activate environment / 激活环境:"
echo "     source .venv/bin/activate"
echo ""
echo "  2. Test wf command / 测试 wf 命令:"
echo "     wf --help"
echo ""
echo "  3. (Optional) Start Chrome debug session / （可选）启动 Chrome 调试会话:"
echo "     ./config/chrome-debug.sh"
echo ""
echo "  4. Fetch a web page / 抓取网页:"
echo "     wf https://mp.weixin.qq.com/s/xxxxx"
echo ""
