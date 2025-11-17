# WebFetcher Bootstrap Script for Windows
# 一键部署开发环境

$ErrorActionPreference = "Stop"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "WebFetcher Bootstrap / 环境部署" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 1. Create virtual environment / 创建虚拟环境
Write-Host "▸ Creating virtual environment / 创建虚拟环境..." -ForegroundColor Yellow
python -m venv .venv

# 2. Activate virtual environment / 激活虚拟环境
Write-Host "▸ Activating virtual environment / 激活虚拟环境..." -ForegroundColor Yellow
. .venv\Scripts\Activate.ps1

# 3. Upgrade pip / 升级 pip
Write-Host "▸ Upgrading pip / 升级 pip..." -ForegroundColor Yellow
pip install -U pip

# 4. Install webfetcher in editable mode with selenium support
# 以开发模式安装 webfetcher（含 Selenium 支持）
Write-Host "▸ Installing webfetcher[selenium] in editable mode / 以开发模式安装..." -ForegroundColor Yellow
pip install -e .[selenium]

# 5. Run ChromeDriver management (if scripts exist)
# 运行 ChromeDriver 管理（如果脚本存在）
if (Test-Path "scripts\manage_chromedriver.py") {
    Write-Host "▸ Checking ChromeDriver compatibility / 检查 ChromeDriver 兼容性..." -ForegroundColor Yellow
    python scripts\manage_chromedriver.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  ChromeDriver check skipped / 跳过 ChromeDriver 检查" -ForegroundColor Yellow
    }
}

# 6. Create config directory if needed / 创建配置目录（如果需要）
Write-Host "▸ Setting up config directory / 设置配置目录..." -ForegroundColor Yellow
$configDir = "$env:USERPROFILE\.config\webfetcher"
if (!(Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

# Copy default config if it doesn't exist / 复制默认配置（如果不存在）
if ((Test-Path "config\routing.yaml") -and !(Test-Path "$configDir\routing.yaml")) {
    Copy-Item "config\routing.yaml" "$configDir\routing.yaml"
    Write-Host "  ✓ Copied default routing config / 已复制默认路由配置" -ForegroundColor Green
}

# 7. Make sure output directory exists / 确保输出目录存在
if (!(Test-Path "output")) {
    New-Item -ItemType Directory -Path "output" -Force | Out-Null
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host "✓ Bootstrap Complete / 部署完成" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps / 后续步骤:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Activate environment / 激活环境:"
Write-Host "     .venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "  2. Test wf command / 测试 wf 命令:"
Write-Host "     wf --help" -ForegroundColor White
Write-Host ""
Write-Host "  3. Fetch a web page / 抓取网页:"
Write-Host "     wf https://mp.weixin.qq.com/s/xxxxx" -ForegroundColor White
Write-Host ""
