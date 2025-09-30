# Selenium Dependencies Installation Guide
# Selenium依赖安装指南

## Table of Contents / 目录

1. [Quick Start / 快速开始](#quick-start--快速开始)
2. [Prerequisites Check / 前置条件检查](#prerequisites-check--前置条件检查)
3. [Installation Guide / 安装指南](#installation-guide--安装指南)
4. [Verification Procedures / 验证程序](#verification-procedures--验证程序)
5. [Troubleshooting / 故障排除](#troubleshooting--故障排除)
6. [Testing Checklist / 测试清单](#testing-checklist--测试清单)
7. [Chrome Debug Integration / Chrome调试集成](#chrome-debug-integration--chrome调试集成)

---

## Quick Start / 快速开始

### For macOS Users / macOS用户

```bash
# 1. Install Selenium dependencies / 安装Selenium依赖
pip install -r requirements-selenium.txt

# 2. Start Chrome Debug / 启动Chrome调试
./config/chrome-debug.sh

# 3. Verify installation / 验证安装
python -c "from selenium_fetcher import SeleniumFetcher; print('✓ Selenium ready')"
```

### Common Error Solution / 常见错误解决

If you see "Selenium package not installed" / 如果看到"Selenium包未安装":
```bash
# Quick fix / 快速修复
pip install selenium>=4.15.0 pyyaml>=6.0.0 lxml>=4.9.0
```

---

## Prerequisites Check / 前置条件检查

### 1. Python Version Check / Python版本检查

```bash
# Check Python version (must be 3.7+) / 检查Python版本（必须3.7+）
python --version
# Expected output / 预期输出: Python 3.7.x or higher

# Alternative command / 备选命令
python3 --version
```

**Requirement / 要求**: Python 3.7+ (for dataclasses and typing support / 用于dataclasses和typing支持)

### 2. pip Installation Check / pip安装检查

```bash
# Check pip availability / 检查pip可用性
pip --version
# or / 或
pip3 --version

# Update pip if needed / 如需要则更新pip
python -m pip install --upgrade pip
```

### 3. Chrome Browser Check / Chrome浏览器检查

```bash
# macOS - Check Chrome installation / macOS - 检查Chrome安装
ls -la "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Linux - Check Chrome installation / Linux - 检查Chrome安装
which google-chrome || which chromium-browser

# Check Chrome version (must be 90+) / 检查Chrome版本（必须90+）
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version
```

**Requirement / 要求**: Chrome 90+ (for stable remote debugging / 用于稳定的远程调试)

### 4. Network Port Check / 网络端口检查

```bash
# Check if port 9222 is available / 检查9222端口是否可用
lsof -i :9222

# If port is in use, kill the process / 如果端口被占用，杀死进程
# kill -9 <PID>
```

---

## Installation Guide / 安装指南

### Method 1: Using requirements file (Recommended) / 使用requirements文件（推荐）

```bash
# Navigate to project directory / 导航到项目目录
cd "/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher"

# Install dependencies / 安装依赖
pip install -r requirements-selenium.txt

# Verify installation / 验证安装
pip list | grep -E "selenium|pyyaml|lxml"
```

### Method 2: Direct pip installation / 直接pip安装

```bash
# Install core Selenium package / 安装核心Selenium包
pip install selenium>=4.15.0

# Install configuration support / 安装配置支持
pip install pyyaml>=6.0.0

# Install HTML parsing optimization / 安装HTML解析优化
pip install lxml>=4.9.0
```

### Method 3: Virtual Environment Setup / 虚拟环境设置

```bash
# Create virtual environment / 创建虚拟环境
python -m venv venv_selenium

# Activate virtual environment / 激活虚拟环境
# macOS/Linux:
source venv_selenium/bin/activate
# Windows:
# venv_selenium\Scripts\activate

# Install dependencies in venv / 在虚拟环境中安装依赖
pip install selenium>=4.15.0 pyyaml>=6.0.0 lxml>=4.9.0

# Verify installation / 验证安装
python -c "import selenium; print(f'Selenium {selenium.__version__} installed')"
```

### Method 4: System Package Manager (Alternative) / 系统包管理器（备选）

#### macOS with Homebrew / macOS使用Homebrew

```bash
# Install Python if needed / 如需要则安装Python
brew install python@3.9

# Use pip3 explicitly / 明确使用pip3
pip3 install selenium>=4.15.0 pyyaml>=6.0.0 lxml>=4.9.0
```

#### Ubuntu/Debian Linux / Ubuntu/Debian Linux

```bash
# Install Python pip / 安装Python pip
sudo apt-get update
sudo apt-get install python3-pip

# Install Selenium dependencies / 安装Selenium依赖
pip3 install --user selenium>=4.15.0 pyyaml>=6.0.0 lxml>=4.9.0
```

---

## Verification Procedures / 验证程序

### Step 1: Package Installation Verification / 包安装验证

```python
# verify_selenium.py - Save and run this script / 保存并运行此脚本
import sys
import importlib

def check_package(package_name, min_version=None):
    try:
        module = importlib.import_module(package_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✓ {package_name} {version} installed")
        
        if min_version and version != 'unknown':
            from packaging import version as v
            if v.parse(version) >= v.parse(min_version):
                print(f"  Version check passed (>= {min_version})")
            else:
                print(f"  ⚠ Version too old (need >= {min_version})")
                return False
        return True
    except ImportError:
        print(f"✗ {package_name} NOT installed")
        return False

# Check required packages / 检查必需的包
packages = [
    ('selenium', '4.15.0'),
    ('yaml', '6.0.0'),
    ('lxml', '4.9.0')
]

all_ok = True
for pkg, min_ver in packages:
    if not check_package(pkg, min_ver):
        all_ok = False

if all_ok:
    print("\n✓ All Selenium dependencies installed correctly!")
else:
    print("\n✗ Some dependencies missing or outdated. Run:")
    print("  pip install -r requirements-selenium.txt")
```

Run verification / 运行验证:
```bash
python verify_selenium.py
```

### Step 2: Chrome Debug Port Verification / Chrome调试端口验证

```bash
# Start Chrome debug session / 启动Chrome调试会话
./config/chrome-debug.sh

# In another terminal, verify port is open / 在另一个终端中，验证端口已开放
curl http://localhost:9222/json/version

# Expected output / 预期输出:
# {
#   "Browser": "Chrome/xxx.x.xxxx.xx",
#   "Protocol-Version": "1.3",
#   ...
# }
```

### Step 3: Selenium Connection Test / Selenium连接测试

```python
# test_selenium_connection.py - Save and run / 保存并运行
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def test_debug_connection():
    """Test connection to Chrome debug port / 测试连接到Chrome调试端口"""
    try:
        # Configure for debug connection / 配置调试连接
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        # Connect to existing Chrome / 连接到现有Chrome
        driver = webdriver.Chrome(options=options)
        
        # Test navigation / 测试导航
        driver.get("https://www.google.com")
        title = driver.title
        print(f"✓ Connected to Chrome debug port")
        print(f"✓ Page title: {title}")
        
        # Clean test / 清理测试
        time.sleep(2)
        driver.quit()
        
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

if __name__ == "__main__":
    # Ensure Chrome debug is running first / 确保Chrome调试已运行
    print("Testing Selenium connection to Chrome debug port...")
    print("Make sure chrome-debug.sh is running!")
    
    if test_debug_connection():
        print("\n✓ Selenium is working correctly!")
    else:
        print("\n✗ Selenium connection failed.")
        print("Please check:")
        print("1. Chrome debug is running (./config/chrome-debug.sh)")
        print("2. Port 9222 is accessible")
        print("3. Selenium is installed correctly")
```

### Step 4: Full Integration Test / 完整集成测试

```python
# test_full_integration.py - Complete test / 完整测试
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium_fetcher import SeleniumFetcher

def test_selenium_fetcher():
    """Test SeleniumFetcher functionality / 测试SeleniumFetcher功能"""
    try:
        # Initialize fetcher / 初始化抓取器
        fetcher = SeleniumFetcher(debug=True)
        
        # Test fetch / 测试抓取
        result = fetcher.fetch("https://www.example.com")
        
        if result and result.get('success'):
            print(f"✓ SeleniumFetcher working!")
            print(f"  Content length: {len(result.get('content', ''))}")
            return True
        else:
            print(f"✗ Fetch failed: {result.get('error', 'Unknown error')}")
            return False
            
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("  Make sure selenium_fetcher.py is in the project root")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing full Selenium integration...")
    if test_selenium_fetcher():
        print("\n✓ Full integration test passed!")
    else:
        print("\n✗ Integration test failed.")
```

---

## Troubleshooting / 故障排除

### Issue 1: "ModuleNotFoundError: No module named 'selenium'" / 问题1：找不到selenium模块

**Symptoms / 症状**:
```python
ModuleNotFoundError: No module named 'selenium'
```

**Solutions / 解决方案**:

1. **Check Python path / 检查Python路径**:
```bash
which python
which pip
# Make sure pip matches python / 确保pip匹配python
```

2. **Install with correct pip / 使用正确的pip安装**:
```bash
# Use python -m pip to ensure correct association / 使用python -m pip确保正确关联
python -m pip install selenium>=4.15.0
```

3. **Check virtual environment / 检查虚拟环境**:
```bash
# If using venv, make sure it's activated / 如果使用venv，确保已激活
which python
# Should show path inside venv directory / 应显示venv目录内的路径
```

### Issue 2: Chrome Debug Port Connection Failed / 问题2：Chrome调试端口连接失败

**Symptoms / 症状**:
```
selenium.common.exceptions.WebDriverException: Message: unknown error: cannot connect to chrome at 127.0.0.1:9222
```

**Solutions / 解决方案**:

1. **Verify Chrome debug is running / 验证Chrome调试正在运行**:
```bash
# Check if Chrome debug process exists / 检查Chrome调试进程是否存在
ps aux | grep "remote-debugging-port=9222"

# Check if port is listening / 检查端口是否监听
lsof -i :9222
```

2. **Restart Chrome debug / 重启Chrome调试**:
```bash
# Kill existing Chrome debug / 杀死现有Chrome调试
pkill -f "remote-debugging-port=9222"

# Start fresh / 重新启动
./config/chrome-debug.sh
```

3. **Check firewall / 检查防火墙**:
```bash
# macOS - Check firewall settings / macOS - 检查防火墙设置
sudo pfctl -s rules | grep 9222

# Allow localhost connections / 允许本地连接
# Usually not needed for localhost / 通常本地连接不需要
```

### Issue 3: ChromeDriver Version Mismatch / 问题3：ChromeDriver版本不匹配

**Note / 注意**: This project uses Chrome Debug Protocol, NOT ChromeDriver! / 本项目使用Chrome调试协议，而非ChromeDriver！

**Symptoms / 症状**:
```
selenium.common.exceptions.SessionNotCreatedException: Message: session not created: This version of ChromeDriver only supports Chrome version XX
```

**Solutions / 解决方案**:

1. **You should NOT see this error / 您不应该看到此错误**:
```bash
# This project connects to debug port, not ChromeDriver / 本项目连接到调试端口，而非ChromeDriver
# Make sure you're using debuggerAddress option / 确保使用debuggerAddress选项
```

2. **If you still see it / 如果仍然看到**:
```python
# Wrong approach / 错误方法:
driver = webdriver.Chrome()  # This requires ChromeDriver

# Correct approach / 正确方法:
options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=options)  # Connects to existing Chrome
```

### Issue 4: Permission Denied / 问题4：权限被拒绝

**Symptoms / 症状**:
```bash
Permission denied: '/usr/local/lib/python3.x/site-packages/...'
```

**Solutions / 解决方案**:

1. **Install with --user flag / 使用--user标志安装**:
```bash
pip install --user selenium>=4.15.0 pyyaml>=6.0.0 lxml>=4.9.0
```

2. **Use virtual environment (recommended) / 使用虚拟环境（推荐）**:
```bash
python -m venv ~/selenium_env
source ~/selenium_env/bin/activate
pip install selenium>=4.15.0 pyyaml>=6.0.0 lxml>=4.9.0
```

### Issue 5: SSL Certificate Errors / 问题5：SSL证书错误

**Symptoms / 症状**:
```
pip install fails with SSL certificate verify failed
```

**Solutions / 解决方案**:

1. **Upgrade certificates / 升级证书**:
```bash
# macOS
brew install ca-certificates

# Linux
sudo apt-get install ca-certificates
```

2. **Temporary workaround (NOT recommended for production) / 临时解决方法（不推荐用于生产）**:
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org selenium
```

---

## Testing Checklist / 测试清单

### Pre-Installation Checks / 安装前检查

- [ ] Python version >= 3.7
- [ ] pip is available and updated
- [ ] Chrome browser version >= 90
- [ ] Port 9222 is available
- [ ] Project directory is accessible

### Installation Verification / 安装验证

- [ ] `selenium` package installed (>= 4.15.0)
- [ ] `pyyaml` package installed (>= 6.0.0)
- [ ] `lxml` package installed (>= 4.9.0)
- [ ] No import errors when running `from selenium import webdriver`
- [ ] No import errors when running `from selenium_fetcher import SeleniumFetcher`

### Chrome Debug Connection / Chrome调试连接

- [ ] `chrome-debug.sh` script is executable
- [ ] Chrome starts with debug port 9222
- [ ] `curl http://localhost:9222/json/version` returns JSON
- [ ] No existing Chrome processes blocking the port
- [ ] Chrome profile directory `~/.chrome-wf` is created

### Selenium Functionality / Selenium功能

- [ ] Can connect to Chrome debug port
- [ ] Can navigate to websites
- [ ] Can execute JavaScript
- [ ] Can take screenshots
- [ ] Can handle page timeouts
- [ ] Can extract page content

### Integration Tests / 集成测试

- [ ] `SeleniumFetcher` initializes without errors
- [ ] Can fetch simple websites (e.g., example.com)
- [ ] Can handle JavaScript-heavy sites
- [ ] Proper error handling for failed connections
- [ ] Cleanup works (browser tabs close properly)

---

## Chrome Debug Integration / Chrome调试集成

### Understanding the Architecture / 理解架构

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Python Script  │────▶│ Selenium Library │────▶│  Chrome Debug   │
│ (selenium_      │     │  (No ChromeDriver│     │   Port 9222     │
│  fetcher.py)    │     │     needed)      │     │ (Existing Chrome│
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### Key Points / 关键点

1. **No ChromeDriver Required / 不需要ChromeDriver**:
   - We connect to existing Chrome instance / 我们连接到现有Chrome实例
   - Chrome is started with `--remote-debugging-port` / Chrome使用`--remote-debugging-port`启动
   - Selenium connects via Chrome DevTools Protocol / Selenium通过Chrome DevTools协议连接

2. **Session Persistence / 会话持久性**:
   - Chrome uses profile directory `~/.chrome-wf` / Chrome使用配置目录`~/.chrome-wf`
   - Sessions, cookies, and cache are preserved / 会话、cookies和缓存被保留
   - Multiple scripts can connect to same Chrome / 多个脚本可以连接到同一Chrome

3. **Configuration File / 配置文件**:
   ```yaml
   # config/selenium_defaults.yaml
   debug_port: 9222
   timeout: 30
   wait_for_ready: true
   javascript_enabled: true
   ```

### Starting Chrome Debug / 启动Chrome调试

```bash
# Manual start / 手动启动
./config/chrome-debug.sh

# With specific URL / 使用特定URL
./config/chrome-debug.sh "https://www.example.com"

# Check if running / 检查是否运行
ps aux | grep "remote-debugging-port=9222"
```

### Connecting from Python / 从Python连接

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Configure connection / 配置连接
options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

# Connect to existing Chrome / 连接到现有Chrome
driver = webdriver.Chrome(options=options)

# Use normally / 正常使用
driver.get("https://www.example.com")
print(driver.title)
```

### Best Practices / 最佳实践

1. **Always check if Chrome debug is running / 始终检查Chrome调试是否运行**:
```python
import requests

def is_chrome_debug_running():
    try:
        resp = requests.get("http://localhost:9222/json/version", timeout=1)
        return resp.status_code == 200
    except:
        return False
```

2. **Handle connection failures gracefully / 优雅地处理连接失败**:
```python
def connect_with_retry(max_retries=3):
    for i in range(max_retries):
        try:
            options = Options()
            options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            return webdriver.Chrome(options=options)
        except Exception as e:
            if i == max_retries - 1:
                raise
            time.sleep(2)
```

3. **Clean up properly / 正确清理**:
```python
try:
    driver = connect_to_chrome()
    # Do work / 执行工作
finally:
    # Don't quit() - it would close Chrome / 不要quit() - 它会关闭Chrome
    # Just close the tab if needed / 如需要只关闭标签页
    driver.close()
```

---

## Environment-Specific Notes / 特定环境注意事项

### macOS Specific / macOS特定

```bash
# Chrome location / Chrome位置
CHROME_APP="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Common issues / 常见问题:
# - Security permissions for automation / 自动化的安全权限
# - Gatekeeper blocks unsigned binaries / Gatekeeper阻止未签名的二进制文件

# Solutions / 解决方案:
# System Preferences > Security & Privacy > Privacy > Automation
# Allow Terminal/Python to control Chrome
```

### Linux Specific / Linux特定

```bash
# Chrome might be at different locations / Chrome可能在不同位置:
# /usr/bin/google-chrome
# /usr/bin/chromium-browser
# /snap/bin/chromium

# Start with appropriate binary / 使用适当的二进制文件启动:
google-chrome --remote-debugging-port=9222 --user-data-dir=~/.chrome-wf
```

### Virtual Environment Best Practices / 虚拟环境最佳实践

```bash
# Create dedicated environment / 创建专用环境
python -m venv ~/envs/selenium_env

# Activate / 激活
source ~/envs/selenium_env/bin/activate

# Install all dependencies / 安装所有依赖
pip install -r requirements-selenium.txt

# Create activation script / 创建激活脚本
cat > activate_selenium.sh << 'EOF'
#!/bin/bash
source ~/envs/selenium_env/bin/activate
export PYTHONPATH="/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher:$PYTHONPATH"
echo "Selenium environment activated"
EOF

chmod +x activate_selenium.sh
```

---

## Quick Diagnosis Script / 快速诊断脚本

Save this as `diagnose_selenium.sh` / 保存为`diagnose_selenium.sh`:

```bash
#!/bin/bash

echo "=== Selenium Installation Diagnosis ==="
echo

# Check Python
echo "1. Python Version:"
python --version || python3 --version
echo

# Check pip
echo "2. Pip Version:"
pip --version || pip3 --version
echo

# Check Selenium
echo "3. Selenium Installation:"
python -c "import selenium; print(f'Selenium {selenium.__version__} installed')" 2>&1
echo

# Check Chrome
echo "4. Chrome Installation:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version 2>/dev/null || echo "Chrome not found"
else
    google-chrome --version 2>/dev/null || chromium-browser --version 2>/dev/null || echo "Chrome not found"
fi
echo

# Check port 9222
echo "5. Port 9222 Status:"
lsof -i :9222 2>/dev/null || echo "Port 9222 is free"
echo

# Check Chrome debug
echo "6. Chrome Debug Status:"
curl -s http://localhost:9222/json/version | head -n 1 || echo "Chrome debug not running"
echo

# Test import
echo "7. Testing SeleniumFetcher import:"
cd "/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher"
python -c "from selenium_fetcher import SeleniumFetcher; print('✓ SeleniumFetcher imports successfully')" 2>&1
echo

echo "=== Diagnosis Complete ==="
echo
echo "If any checks failed, refer to the troubleshooting section above."
```

Run diagnosis / 运行诊断:
```bash
chmod +x diagnose_selenium.sh
./diagnose_selenium.sh
```

---

## Summary / 总结

### Key Success Factors / 成功关键因素

1. **Correct Selenium version (>= 4.15.0)** / 正确的Selenium版本
2. **Chrome debug port (9222) running** / Chrome调试端口运行中
3. **No ChromeDriver needed** / 不需要ChromeDriver
4. **Proper Python environment** / 正确的Python环境

### Common Pitfalls to Avoid / 要避免的常见陷阱

1. ❌ Installing ChromeDriver separately / 单独安装ChromeDriver
2. ❌ Using outdated Selenium version / 使用过时的Selenium版本
3. ❌ Not starting Chrome debug first / 未先启动Chrome调试
4. ❌ Wrong Python/pip combination / 错误的Python/pip组合
5. ❌ Forgetting virtual environment activation / 忘记激活虚拟环境

### Support Resources / 支持资源

- Selenium Documentation: https://www.selenium.dev/documentation/
- Chrome DevTools Protocol: https://chromedevtools.github.io/devtools-protocol/
- Project Issues: Check TASKS/SELENIUM_FIX_IMPLEMENTATION_PLAN.md

---

*Last Updated: 2025-01-29*
*最后更新：2025年1月29日*