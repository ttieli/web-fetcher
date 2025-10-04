# 故障排除手册 / Troubleshooting Manual

Web_Fetcher错误处理框架故障排除完整指南

## 目录 / Table of Contents

1. [网络连接错误](#1-网络连接错误--network-connection-errors)
2. [浏览器初始化错误](#2-浏览器初始化错误--browser-initialization-errors)
3. [Chrome集成错误](#3-chrome集成错误--chrome-integration-errors) **[新增/NEW]**
4. [页面加载错误](#4-页面加载错误--page-loading-errors)
5. [权限错误](#5-权限错误--permission-errors)
6. [依赖缺失错误](#6-依赖缺失错误--missing-dependency-errors)
7. [超时错误](#7-超时错误--timeout-errors)
8. [未知错误](#8-未知错误--unknown-errors)
9. [调试技巧](#9-调试技巧--debugging-tips)
10. [紧急响应流程](#10-紧急响应流程--emergency-response-procedures)

---

## 1. 网络连接错误 / Network Connection Errors

### 错误标识 / Error Identification

**错误类别：** `NETWORK_CONNECTION`

**典型错误消息：**
```
ConnectionRefusedError: [Errno 61] Connection refused
SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
socket.gaierror: [Errno 8] nodename nor servname provided
```

### 详细排查步骤 / Detailed Troubleshooting Steps

#### 步骤 1: 验证基本网络连接 / Verify Basic Network Connectivity

```bash
# 测试网络连接
ping google.com

# 测试DNS解析
nslookup example.com

# 测试HTTP连接
curl -I https://example.com
```

**预期结果：** 网络正常响应，无超时或连接拒绝

#### 步骤 2: 检查SSL证书 / Check SSL Certificates

```bash
# 验证SSL证书
openssl s_client -connect example.com:443 -servername example.com

# 检查证书过期时间
echo | openssl s_client -connect example.com:443 2>/dev/null | openssl x509 -noout -dates
```

**常见问题：**
- 证书过期
- 证书域名不匹配
- 自签名证书未信任

**解决方案：**
```python
# Python中禁用SSL验证（仅用于测试）
import ssl
import urllib.request

context = ssl._create_unverified_context()
urllib.request.urlopen(url, context=context)
```

#### 步骤 3: 检查防火墙和代理 / Check Firewall and Proxy

```bash
# 检查系统代理设置
echo $http_proxy
echo $https_proxy

# macOS检查防火墙状态
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# 测试代理连接
curl -x http://proxy.example.com:8080 https://example.com
```

**配置代理：**
```python
# 在Python中设置代理
import os
os.environ['http_proxy'] = 'http://proxy.example.com:8080'
os.environ['https_proxy'] = 'https://proxy.example.com:8080'
```

#### 步骤 4: 检查端口可用性 / Check Port Availability

```bash
# 检查端口是否开放
nc -zv example.com 443

# 检查本地端口占用
lsof -i :9222  # Chrome调试端口
```

### 常见场景及解决方案 / Common Scenarios and Solutions

| 场景 | 症状 | 解决方案 |
|------|------|----------|
| 企业网络 | Connection timeout | 配置公司代理 |
| VPN环境 | DNS resolution failed | 使用VPN DNS服务器 |
| 本地开发 | Certificate error | 添加自签名证书到信任列表 |
| 云服务器 | Connection refused | 检查安全组规则 |

### 预防措施 / Prevention Measures

1. **配置重试机制**：网络请求添加自动重试
2. **设置合理超时**：避免长时间等待
3. **使用连接池**：复用HTTP连接
4. **监控网络质量**：记录延迟和丢包率

---

## 2. 浏览器初始化错误 / Browser Initialization Errors

### 错误标识 / Error Identification

**错误类别：** `BROWSER_INIT`

**典型错误消息：**
```
selenium.common.exceptions.WebDriverException: Message: 'chromedriver' executable needs to be in PATH
selenium.common.exceptions.SessionNotCreatedException: session not created: This version of ChromeDriver only supports Chrome version 120
```

### 详细排查步骤 / Detailed Troubleshooting Steps

#### 步骤 1: 验证Chrome安装 / Verify Chrome Installation

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version

# Linux
google-chrome --version
chromium-browser --version

# Windows
reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version
```

**预期输出：** `Google Chrome 120.0.6099.109`

#### 步骤 2: 检查ChromeDriver版本匹配 / Check ChromeDriver Version Match

```bash
# 检查ChromeDriver版本
chromedriver --version

# 下载匹配的ChromeDriver
# 访问: https://chromedriver.chromium.org/downloads
```

**版本对应关系：**
```
Chrome 120.x  →  ChromeDriver 120.x
Chrome 119.x  →  ChromeDriver 119.x
Chrome 118.x  →  ChromeDriver 118.x
```

#### 步骤 3: 验证ChromeDriver在PATH中 / Verify ChromeDriver in PATH

```bash
# 检查PATH
echo $PATH

# 查找chromedriver位置
which chromedriver

# 如果不在PATH中，添加
export PATH=$PATH:/path/to/chromedriver/directory
```

**永久添加到PATH (macOS/Linux):**
```bash
# 编辑 ~/.bashrc 或 ~/.zshrc
echo 'export PATH=$PATH:/usr/local/bin' >> ~/.zshrc
source ~/.zshrc
```

#### 步骤 4: 测试浏览器启动 / Test Browser Launch

```python
# 测试脚本
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

# 方法1: 使用PATH中的chromedriver
driver = webdriver.Chrome()

# 方法2: 指定chromedriver路径
service = Service('/path/to/chromedriver')
driver = webdriver.Chrome(service=service)

driver.quit()
```

#### 步骤 5: 检查Chrome远程调试端口 / Check Chrome Remote Debugging Port

```bash
# 检查9222端口是否被占用
lsof -i :9222

# 如果被占用，杀死进程
kill -9 <PID>

# 手动启动Chrome调试模式
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome_debug
```

### 常见问题快速修复 / Quick Fixes for Common Issues

#### 问题 1: ChromeDriver版本不匹配

**症状：**
```
session not created: This version of ChromeDriver only supports Chrome version X
```

**快速修复：**
```bash
# 使用webdriver-manager自动管理驱动
pip install webdriver-manager

# 在代码中使用
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
```

#### 问题 2: Chrome进程残留

**症状：**
```
chrome not reachable
```

**快速修复：**
```bash
# macOS/Linux
pkill -f chrome

# 清理Chrome临时文件
rm -rf /tmp/.com.google.Chrome.*
```

#### 问题 3: 权限不足

**症状：**
```
Permission denied: 'chromedriver'
```

**快速修复：**
```bash
# 添加执行权限
chmod +x /path/to/chromedriver

# 如果是macOS安全限制
xattr -d com.apple.quarantine /path/to/chromedriver
```

### 环境特定配置 / Environment-Specific Configurations

#### Docker环境

```dockerfile
# Dockerfile配置
FROM python:3.9-slim

# 安装Chrome和ChromeDriver
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# Chrome选项
RUN echo '--no-sandbox\n--disable-dev-shm-usage\n--headless' > /etc/chrome_options
```

#### CI/CD环境 (GitHub Actions)

```yaml
# .github/workflows/test.yml
- name: Setup Chrome
  uses: browser-actions/setup-chrome@latest

- name: Setup ChromeDriver
  uses: nanasess/setup-chromedriver@master
```

---

## 3. Chrome集成错误 / Chrome Integration Errors

### 错误标识 / Error Identification

**错误类别：** `CHROME_INTEGRATION`

**典型错误消息：**
```
ChromeNotFoundError: Chrome浏览器未找到 / Chrome browser not found
ChromePortOccupiedError: 端口9222被占用 / Port 9222 occupied
ChromePermissionError: Chrome权限被拒绝 / Chrome permission denied
ChromeTimeoutError: Chrome启动超时 / Chrome startup timeout
ChromeConnectionError: 无法连接到Chrome端口9222 / Cannot connect to Chrome port 9222
```

### 详细排查步骤 / Detailed Troubleshooting Steps

#### 步骤 1: 验证Chrome安装 / Verify Chrome Installation

```bash
# macOS
ls -la "/Applications/Google Chrome.app"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version

# Linux
which google-chrome || which chromium
google-chrome --version || chromium --version

# Windows
where chrome
"C:\Program Files\Google\Chrome\Application\chrome.exe" --version
```

**如果Chrome未安装：**
- macOS: 从 https://www.google.com/chrome/ 下载安装
- Linux: `sudo apt-get install google-chrome-stable`
- Windows: 从官网下载安装

#### 步骤 2: 检查并解决端口占用 / Check and Resolve Port Conflicts

```bash
# 检查9222端口占用情况
lsof -i:9222  # macOS/Linux
netstat -ano | findstr :9222  # Windows

# 查看占用进程详情
ps -p <PID>  # macOS/Linux

# 终止占用进程
kill -9 <PID>  # macOS/Linux
taskkill /F /PID <PID>  # Windows

# 或使用不同端口
export CHROME_DEBUG_PORT=9333
./wf.py https://example.com --debug-port 9333
```

#### 步骤 3: 解决权限问题 (macOS) / Resolve Permission Issues (macOS)

**症状：** Chrome启动失败，提示权限被拒绝

**解决方案：**

1. **系统设置方法：**
   ```
   1. 打开 系统设置
   2. 进入 隐私与安全 → 开发者工具
   3. 启用 Terminal.app 或 iTerm.app
   4. 进入 隐私与安全 → 自动化
   5. 允许终端控制 Google Chrome
   ```

2. **命令行重置方法：**
   ```bash
   # 重置Terminal权限
   tccutil reset All com.apple.Terminal

   # 重置iTerm权限
   tccutil reset All com.googlecode.iterm2

   # 重新运行命令，系统会提示授权
   ./wf.py https://example.com
   ```

3. **完全磁盘访问：**
   ```
   系统设置 → 隐私与安全 → 完全磁盘访问
   添加 Terminal 或 iTerm
   ```

#### 步骤 4: 解决Chrome启动超时 / Resolve Chrome Startup Timeout

**可能原因：**
- 系统资源不足
- Chrome正在更新
- 防火墙阻止
- Chrome配置文件损坏

**解决方案：**

```bash
# 1. 增加超时时间
export CHROME_STARTUP_TIMEOUT=30
./wf.py https://example.com --timeout 30

# 2. 清理Chrome缓存和配置
rm -rf ~/.chrome-wf/*
rm -rf /tmp/chrome_debug

# 3. 手动测试Chrome启动
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.chrome-wf" \
  --no-first-run \
  --no-default-browser-check

# 4. 检查系统资源
top  # 查看CPU和内存使用
df -h  # 查看磁盘空间

# 5. 禁用不必要的Chrome功能
export CHROME_FLAGS="--disable-gpu --disable-dev-shm-usage --no-sandbox"
```

#### 步骤 5: 解决连接失败 / Resolve Connection Failures

```bash
# 1. 验证Chrome调试端口可访问
curl -s http://localhost:9222/json/version

# 2. 检查防火墙设置
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate  # macOS
sudo iptables -L  # Linux

# 3. 测试Chrome健康状态
./config/ensure-chrome-debug.sh --check-only --verbose

# 4. 查看Chrome进程状态
ps aux | grep -E "remote-debugging-port"

# 5. 检查日志文件
tail -f ~/.chrome-wf/chrome-debug.log
```

### Chrome集成常见问题快速修复 / Quick Fixes for Chrome Integration

#### 问题 1: Chrome自动启动失败

**快速修复：**
```bash
# 禁用自动启动，使用手动模式
export WF_DISABLE_AUTO_CHROME=1

# 手动启动Chrome
./config/chrome-debug-launcher.sh

# 然后运行wf
./wf.py https://example.com
```

#### 问题 2: Chrome版本不兼容

**快速修复：**
```bash
# 检查Chrome版本
google-chrome --version

# 更新Chrome到最新版本
# macOS: 打开Chrome → 帮助 → 关于Google Chrome
# Linux: sudo apt-get update && sudo apt-get upgrade google-chrome-stable

# 使用兼容的Selenium版本
pip install selenium==4.15.0
```

#### 问题 3: 多个Chrome实例冲突

**快速修复：**
```bash
# 终止所有Chrome调试实例
pkill -f "remote-debugging-port"

# 清理锁文件
rm -f ~/.chrome-wf/.chrome-debug.lock
rm -f ~/.chrome-wf/.chrome-debug.pid

# 重新启动
./wf.py https://example.com --force-restart
```

#### 问题 4: Chrome内存占用过高

**快速修复：**
```bash
# 限制Chrome内存使用
export CHROME_FLAGS="--max_old_space_size=512 --js-flags=--max-old-space-size=512"

# 定期重启Chrome
./wf.py https://example.com --force-restart

# 或使用urllib模式避免Chrome
./wf.py https://example.com --force-urllib
```

### Chrome调试命令集 / Chrome Debug Commands

```bash
# 基础状态检查
curl -s http://localhost:9222/json/version | jq .

# 列出所有打开的标签
curl -s http://localhost:9222/json | jq '.[] | {id, url, title}'

# 关闭特定标签
curl -X GET "http://localhost:9222/json/close/<TAB_ID>"

# 激活特定标签
curl -X GET "http://localhost:9222/json/activate/<TAB_ID>"

# 创建新标签
curl -X PUT "http://localhost:9222/json/new?url=https://example.com"

# 获取Chrome性能指标
curl -s http://localhost:9222/json/version | jq '.["User-Agent"]'

# 监控Chrome资源使用
while true; do
  ps aux | grep -E "remote-debugging-port" | grep -v grep
  sleep 5
done
```

### Chrome环境变量参考 / Chrome Environment Variables

```bash
# 核心配置
export CHROME_DEBUG_PORT=9222           # 调试端口
export CHROME_STARTUP_TIMEOUT=15        # 启动超时(秒)
export WF_DISABLE_AUTO_CHROME=1         # 禁用自动启动
export CHROME_EXECUTABLE="/path/to/chrome"  # Chrome路径

# Chrome启动标志
export CHROME_FLAGS="--headless --disable-gpu --no-sandbox"
export CHROME_USER_DATA_DIR="$HOME/.chrome-wf"  # 用户数据目录
export CHROME_HEADLESS=true             # 无头模式
export CHROME_WINDOW_SIZE="1920,1080"   # 窗口大小

# 调试选项
export CHROME_VERBOSE=true              # 详细日志
export CHROME_LOG_FILE="$HOME/.chrome-wf/chrome.log"  # 日志文件
export CHROME_ENABLE_LOGGING=true       # 启用日志
```

---

## 4. 页面加载错误 / Page Loading Errors

### 错误标识 / Error Identification

**错误类别：** `PAGE_LOAD`

**典型错误消息：**
```
selenium.common.exceptions.TimeoutException: Message: timeout: Timed out receiving message from renderer
Navigation timeout of 30000 ms exceeded
Page crash: Renderer timeout
```

### 详细排查步骤 / Detailed Troubleshooting Steps

#### 步骤 1: 验证页面可访问性 / Verify Page Accessibility

```bash
# 使用curl测试页面响应
curl -I https://example.com

# 测试完整页面加载时间
curl -w "@curl-format.txt" -o /dev/null -s https://example.com
```

**curl-format.txt内容：**
```
time_namelookup:  %{time_namelookup}s
time_connect:     %{time_connect}s
time_appconnect:  %{time_appconnect}s
time_pretransfer: %{time_pretransfer}s
time_starttransfer: %{time_starttransfer}s
time_total:       %{time_total}s
```

#### 步骤 2: 分析页面复杂度 / Analyze Page Complexity

```python
# 检查页面资源加载
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get("https://example.com")

# 统计页面资源
scripts = driver.find_elements(By.TAG_NAME, "script")
images = driver.find_elements(By.TAG_NAME, "img")
stylesheets = driver.find_elements(By.TAG_NAME, "link")

print(f"Scripts: {len(scripts)}")
print(f"Images: {len(images)}")
print(f"Stylesheets: {len(stylesheets)}")

# 检查页面大小
page_source = driver.page_source
print(f"Page size: {len(page_source)} bytes")
```

#### 步骤 3: 优化加载策略 / Optimize Loading Strategy

```python
from selenium.webdriver.chrome.options import Options

options = Options()

# 禁用图片加载
prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)

# 设置页面加载策略
options.page_load_strategy = 'eager'  # 或 'none'

# 禁用JavaScript（如果不需要）
options.add_argument('--disable-javascript')

# 禁用CSS
options.add_argument('--disable-css')

driver = webdriver.Chrome(options=options)
```

#### 步骤 4: 增加超时时间 / Increase Timeout Values

```python
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

driver = webdriver.Chrome()

# 设置页面加载超时
driver.set_page_load_timeout(60)  # 60秒

# 设置脚本执行超时
driver.set_script_timeout(30)

# 设置隐式等待
driver.implicitly_wait(10)

# 使用显式等待
wait = WebDriverWait(driver, 30)
```

#### 步骤 5: 处理动态内容 / Handle Dynamic Content

```python
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# 等待特定元素加载
element = wait.until(
    EC.presence_of_element_located((By.ID, "content"))
)

# 等待JavaScript完成
driver.execute_script("return document.readyState") == "complete"

# 等待AJAX请求完成
driver.execute_script("return jQuery.active == 0")  # 如果使用jQuery
```

### 性能优化建议 / Performance Optimization Recommendations

1. **预加载策略**
   - 使用`eager`模式仅等待DOM加载
   - 使用`none`模式不等待页面加载完成

2. **资源过滤**
   - 禁用不需要的资源类型（图片、字体、视频）
   - 使用请求拦截器过滤特定域名

3. **缓存利用**
   - 保持浏览器会话以复用缓存
   - 使用持久化用户数据目录

4. **并发控制**
   - 限制同时打开的标签页数量
   - 使用资源池管理浏览器实例

---

## 5. 权限错误 / Permission Errors

### 错误标识 / Error Identification

**错误类别：** `PERMISSION`

**典型错误消息：**
```
PermissionError: [Errno 13] Permission denied: '/path/to/file'
403 Forbidden
401 Unauthorized
Access denied
```

### 详细排查步骤 / Detailed Troubleshooting Steps

#### 步骤 1: 检查文件系统权限 / Check File System Permissions

```bash
# 查看文件权限
ls -la /path/to/file

# 查看目录权限
ls -ld /path/to/directory

# 检查当前用户
whoami
id

# 修改文件权限
chmod 755 /path/to/file
chmod 644 /path/to/config.json

# 修改所有者
chown $USER:$USER /path/to/file
```

#### 步骤 2: 验证输出目录权限 / Verify Output Directory Permissions

```python
import os
import stat

output_dir = "/path/to/output"

# 检查目录是否存在
if not os.path.exists(output_dir):
    os.makedirs(output_dir, exist_ok=True)

# 检查是否可写
if os.access(output_dir, os.W_OK):
    print("Directory is writable")
else:
    print("Permission denied: cannot write to directory")

# 检查详细权限
stat_info = os.stat(output_dir)
print(f"Permissions: {oct(stat_info.st_mode)[-3:]}")
```

#### 步骤 3: 处理HTTP认证 / Handle HTTP Authentication

```python
# Basic Authentication
import requests
from requests.auth import HTTPBasicAuth

response = requests.get(
    'https://example.com',
    auth=HTTPBasicAuth('username', 'password')
)

# Bearer Token认证
headers = {'Authorization': 'Bearer YOUR_TOKEN'}
response = requests.get('https://api.example.com', headers=headers)

# Cookie认证
cookies = {'session_id': 'YOUR_SESSION_ID'}
response = requests.get('https://example.com', cookies=cookies)
```

#### 步骤 4: 处理Selenium认证 / Handle Selenium Authentication

```python
from selenium import webdriver

# 方法1: URL中包含凭据
url = "https://username:password@example.com"
driver.get(url)

# 方法2: 使用Alert处理认证弹窗
from selenium.webdriver.common.alert import Alert

driver.get("https://example.com")
alert = Alert(driver)
alert.authenticate('username', 'password')

# 方法3: 添加认证header
capabilities = webdriver.DesiredCapabilities.CHROME.copy()
capabilities['chromeOptions'] = {
    'args': ['--auth-server-whitelist=*'],
    'extensions': []
}
```

#### 步骤 5: 处理macOS安全限制 / Handle macOS Security Restrictions

```bash
# 允许应用访问
xattr -cr /path/to/application

# 检查Gatekeeper状态
spctl --status

# 临时禁用Gatekeeper（不推荐）
sudo spctl --master-disable

# 添加应用到白名单
spctl --add /path/to/application

# 授予完整磁盘访问权限
# 系统偏好设置 > 安全性与隐私 > 隐私 > 完整磁盘访问权限
```

### 权限问题速查表 / Permission Issues Quick Reference

| 错误代码 | 含义 | 解决方案 |
|---------|------|----------|
| 401 | 未授权 | 提供有效的身份验证凭据 |
| 403 | 禁止访问 | 检查用户权限和访问控制列表 |
| EACCES | 访问被拒绝 | 修改文件/目录权限 |
| EPERM | 操作不允许 | 使用sudo或管理员权限 |

---

## 6. 依赖缺失错误 / Missing Dependency Errors

### 错误标识 / Error Identification

**错误类别：** `DEPENDENCY`

**典型错误消息：**
```
ModuleNotFoundError: No module named 'selenium'
ImportError: cannot import name 'webdriver' from 'selenium'
ImportError: libpython3.9.so.1.0: cannot open shared object file
```

### 详细排查步骤 / Detailed Troubleshooting Steps

#### 步骤 1: 验证Python环境 / Verify Python Environment

```bash
# 检查Python版本
python --version
python3 --version

# 检查pip版本
pip --version
pip3 --version

# 检查Python路径
which python
which python3

# 检查已安装的包
pip list
pip show selenium
```

#### 步骤 2: 检查虚拟环境 / Check Virtual Environment

```bash
# 检查是否在虚拟环境中
echo $VIRTUAL_ENV

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

# 验证虚拟环境激活
which python  # 应指向venv/bin/python
```

#### 步骤 3: 安装缺失依赖 / Install Missing Dependencies

```bash
# 安装项目依赖
pip install -r requirements.txt

# 安装特定版本
pip install selenium==4.15.0

# 升级现有包
pip install --upgrade selenium

# 检查依赖冲突
pip check

# 查看依赖树
pip install pipdeptree
pipdeptree
```

#### 步骤 4: 验证系统库 / Verify System Libraries

```bash
# macOS: 检查系统库
otool -L /path/to/library.so

# Linux: 检查共享库
ldd /path/to/library.so

# 查找缺失的库
ldconfig -p | grep libpython

# 安装系统依赖 (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    build-essential \
    libssl-dev \
    libffi-dev

# 安装系统依赖 (macOS)
brew install python@3.9
brew install openssl
```

#### 步骤 5: 解决导入错误 / Resolve Import Errors

```python
# 检查模块路径
import sys
print(sys.path)

# 添加自定义路径
sys.path.insert(0, '/path/to/module')

# 检查模块是否可导入
try:
    import selenium
    print(f"Selenium version: {selenium.__version__}")
    print(f"Selenium location: {selenium.__file__}")
except ImportError as e:
    print(f"Import error: {e}")

# 动态导入
import importlib
try:
    module = importlib.import_module('selenium')
except ImportError as e:
    print(f"Module not found: {e}")
```

### 依赖管理最佳实践 / Dependency Management Best Practices

1. **使用requirements.txt**
```bash
# 生成依赖列表
pip freeze > requirements.txt

# 按类别组织依赖
# requirements.txt
selenium>=4.15.0,<5.0.0
beautifulsoup4>=4.12.0
requests>=2.31.0

# requirements-dev.txt (开发依赖)
pytest>=7.4.0
black>=23.0.0
```

2. **使用pyproject.toml (推荐)**
```toml
[project]
name = "web_fetcher"
version = "1.0.0"
dependencies = [
    "selenium>=4.15.0",
    "beautifulsoup4>=4.12.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "black>=23.0.0",
]
```

3. **依赖锁定**
```bash
# 使用pip-tools
pip install pip-tools
pip-compile requirements.in > requirements.txt

# 或使用poetry
poetry lock
```

---

## 7. 超时错误 / Timeout Errors

### 错误标识 / Error Identification

**错误类别：** `TIMEOUT`

**典型错误消息：**
```
TimeoutError: [Errno 60] Operation timed out
selenium.common.exceptions.TimeoutException
requests.exceptions.ReadTimeout
socket.timeout: timed out
```

### 详细排查步骤 / Detailed Troubleshooting Steps

#### 步骤 1: 诊断超时原因 / Diagnose Timeout Cause

```bash
# 测试网络延迟
ping -c 5 example.com

# 测试响应时间
time curl https://example.com

# 使用traceroute诊断
traceroute example.com

# 检查服务器响应时间
curl -o /dev/null -s -w "Total: %{time_total}s\nConnect: %{time_connect}s\nStartTransfer: %{time_starttransfer}s\n" https://example.com
```

#### 步骤 2: 调整超时配置 / Adjust Timeout Configuration

```python
# Selenium超时配置
from selenium import webdriver

driver = webdriver.Chrome()

# 页面加载超时 (秒)
driver.set_page_load_timeout(120)

# 脚本执行超时
driver.set_script_timeout(60)

# 元素查找隐式等待
driver.implicitly_wait(30)

# requests超时配置
import requests

# 连接超时和读取超时
response = requests.get(
    'https://example.com',
    timeout=(10, 60)  # (connect_timeout, read_timeout)
)

# urllib超时配置
import urllib.request

response = urllib.request.urlopen(
    'https://example.com',
    timeout=60
)
```

#### 步骤 3: 实现重试机制 / Implement Retry Logic

```python
import time
from selenium.common.exceptions import TimeoutException

def fetch_with_retry(url, max_retries=3, backoff_factor=2):
    """带指数退避的重试机制"""
    for attempt in range(max_retries):
        try:
            driver.get(url)
            return True
        except TimeoutException as e:
            if attempt == max_retries - 1:
                raise
            wait_time = backoff_factor ** attempt
            print(f"Timeout on attempt {attempt + 1}, retrying in {wait_time}s...")
            time.sleep(wait_time)
    return False

# 使用requests-retry
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)
```

#### 步骤 4: 优化资源加载 / Optimize Resource Loading

```python
from selenium.webdriver.chrome.options import Options

options = Options()

# 启用快速页面加载
options.page_load_strategy = 'eager'

# 禁用图片
prefs = {
    'profile.default_content_setting_values': {
        'images': 2,
        'plugins': 2,
        'popups': 2,
        'geolocation': 2,
        'notifications': 2,
        'auto_select_certificate': 2,
        'fullscreen': 2,
        'mouselock': 2,
        'media_stream': 2,
    }
}
options.add_experimental_option('prefs', prefs)

# 禁用扩展
options.add_argument('--disable-extensions')

# 禁用GPU
options.add_argument('--disable-gpu')
```

#### 步骤 5: 使用异步和并发 / Use Async and Concurrency

```python
# 异步请求
import asyncio
import aiohttp

async def fetch_async(url, timeout=60):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=timeout) as response:
                return await response.text()
        except asyncio.TimeoutError:
            print(f"Timeout fetching {url}")
            return None

# 并发处理
import concurrent.futures

urls = ['https://example1.com', 'https://example2.com']

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(fetch_page, url): url for url in urls}
    for future in concurrent.futures.as_completed(futures):
        url = futures[future]
        try:
            result = future.result(timeout=60)
        except concurrent.futures.TimeoutError:
            print(f"Timeout: {url}")
```

### 超时优化策略 / Timeout Optimization Strategies

| 场景 | 推荐超时 | 优化建议 |
|------|---------|---------|
| API调用 | 10-30s | 使用连接池，启用keep-alive |
| 页面加载 | 30-60s | 使用eager模式，禁用不必要资源 |
| 大文件下载 | 300-600s | 分块下载，显示进度 |
| 数据库查询 | 5-15s | 添加索引，优化查询 |
| 长时间任务 | 600s+ | 使用异步处理，提供进度反馈 |

---

## 8. 未知错误 / Unknown Errors

### 错误标识 / Error Identification

**错误类别：** `UNKNOWN`

**特征：** 无法匹配其他已知错误类别的异常

### 通用排查流程 / General Troubleshooting Process

#### 步骤 1: 收集详细错误信息 / Collect Detailed Error Information

```python
import traceback
import sys

try:
    # 可能出错的代码
    risky_operation()
except Exception as e:
    # 获取完整堆栈跟踪
    exc_type, exc_value, exc_traceback = sys.exc_info()

    # 打印详细信息
    print("Exception Type:", exc_type.__name__)
    print("Exception Message:", str(e))
    print("\nFull Traceback:")
    traceback.print_exc()

    # 获取格式化的堆栈跟踪
    tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print("\nFormatted Traceback:")
    print(tb_str)

    # 保存到文件
    with open('error_log.txt', 'a') as f:
        f.write(f"\n--- Error at {datetime.now()} ---\n")
        f.write(tb_str)
```

#### 步骤 2: 启用详细日志 / Enable Verbose Logging

```python
import logging

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

# 为特定模块启用DEBUG级别
logging.getLogger('selenium').setLevel(logging.DEBUG)
logging.getLogger('urllib3').setLevel(logging.DEBUG)

# 使用日志记录
logger = logging.getLogger(__name__)
logger.debug("Starting operation")
logger.info("Processing URL: %s", url)
logger.error("Operation failed", exc_info=True)
```

#### 步骤 3: 隔离问题 / Isolate the Problem

```python
# 二分法定位问题
def test_step_1():
    print("Step 1: Basic initialization")
    # 测试代码

def test_step_2():
    print("Step 2: Load configuration")
    # 测试代码

def test_step_3():
    print("Step 3: Connect to service")
    # 测试代码

# 逐步执行，找出出错的步骤
steps = [test_step_1, test_step_2, test_step_3]
for i, step in enumerate(steps, 1):
    try:
        step()
        print(f"✓ Step {i} completed successfully")
    except Exception as e:
        print(f"✗ Step {i} failed: {e}")
        break
```

#### 步骤 4: 检查环境差异 / Check Environment Differences

```python
import sys
import os
import platform

def print_environment_info():
    """打印环境信息用于调试"""
    print("=== Environment Information ===")
    print(f"Python Version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Python Path: {sys.executable}")
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"PATH: {os.environ.get('PATH')}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")

    print("\n=== Installed Packages ===")
    import pkg_resources
    installed = [f"{pkg.key}=={pkg.version}" for pkg in pkg_resources.working_set]
    for pkg in sorted(installed):
        print(pkg)

    print("\n=== System Information ===")
    import psutil
    print(f"CPU Count: {psutil.cpu_count()}")
    print(f"Memory: {psutil.virtual_memory().total / (1024**3):.2f} GB")
    print(f"Disk Usage: {psutil.disk_usage('/').percent}%")

print_environment_info()
```

#### 步骤 5: 尝试最小可复现示例 / Create Minimal Reproducible Example

```python
# 创建最小示例，去除所有非必要代码
def minimal_example():
    """最小化的问题复现代码"""
    # 只包含能复现问题的最少代码
    pass

# 测试最小示例
try:
    minimal_example()
    print("Minimal example succeeded")
except Exception as e:
    print(f"Minimal example failed: {e}")
    traceback.print_exc()
```

### 高级调试技巧 / Advanced Debugging Techniques

#### 使用pdb调试器

```python
import pdb

def problematic_function():
    x = 10
    y = 0
    pdb.set_trace()  # 设置断点
    result = x / y
    return result

# 或者在异常处进入调试器
import sys

def debug_on_exception(type, value, tb):
    import traceback
    traceback.print_exception(type, value, tb)
    pdb.post_mortem(tb)

sys.excepthook = debug_on_exception
```

#### 使用装饰器捕获异常

```python
import functools

def catch_and_log_exceptions(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(
                f"Exception in {func.__name__}: {e}",
                exc_info=True,
                extra={
                    'args': args,
                    'kwargs': kwargs
                }
            )
            raise
    return wrapper

@catch_and_log_exceptions
def my_function():
    # 函数代码
    pass
```

---

## 9. 调试技巧 / Debugging Tips

### 8.1 使用浏览器DevTools

```python
# 启用Chrome DevTools Protocol
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--auto-open-devtools-for-tabs')

driver = webdriver.Chrome(options=options)

# 获取控制台日志
logs = driver.get_log('browser')
for log in logs:
    print(log)

# 执行DevTools命令
driver.execute_cdp_cmd('Network.enable', {})
driver.execute_cdp_cmd('Network.setUserAgentOverride', {
    'userAgent': 'Custom User Agent'
})
```

### 8.2 截图和页面源码保存

```python
def debug_save_artifacts(driver, prefix="debug"):
    """保存调试文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 保存截图
    screenshot_path = f"{prefix}_screenshot_{timestamp}.png"
    driver.save_screenshot(screenshot_path)
    print(f"Screenshot saved: {screenshot_path}")

    # 保存页面源码
    source_path = f"{prefix}_source_{timestamp}.html"
    with open(source_path, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print(f"Page source saved: {source_path}")

    # 保存控制台日志
    log_path = f"{prefix}_console_{timestamp}.log"
    with open(log_path, 'w') as f:
        for log in driver.get_log('browser'):
            f.write(f"{log['level']}: {log['message']}\n")
    print(f"Console log saved: {log_path}")
```

### 8.3 网络请求监控

```python
# 监控网络请求
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

caps = DesiredCapabilities.CHROME.copy()
caps['goog:loggingPrefs'] = {'performance': 'ALL'}

driver = webdriver.Chrome(desired_capabilities=caps)
driver.get("https://example.com")

# 获取性能日志
logs = driver.get_log('performance')
for log in logs:
    print(log)
```

### 8.4 性能分析

```python
import time
import functools

def measure_time(func):
    """测量函数执行时间"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.2f} seconds")
        return result
    return wrapper

@measure_time
def slow_operation():
    # 慢操作
    pass
```

---

## 10. 紧急响应流程 / Emergency Response Procedures

### 9.1 生产环境故障响应 / Production Failure Response

#### 第一步：立即响应 (0-5分钟)

1. **确认故障**
   - 检查错误报告和日志
   - 验证故障范围（局部/全局）
   - 记录首次发现时间

2. **快速缓解**
   ```bash
   # 重启服务
   sudo systemctl restart webfetcher

   # 检查服务状态
   sudo systemctl status webfetcher

   # 查看最近日志
   tail -100 /var/log/webfetcher/error.log
   ```

3. **通知相关人员**
   - 通知团队成员
   - 更新状态页面
   - 记录故障票据

#### 第二步：诊断问题 (5-15分钟)

1. **收集诊断信息**
   ```bash
   # 系统资源
   top
   free -h
   df -h

   # 网络连接
   netstat -tuln
   ss -tulpn

   # 进程状态
   ps aux | grep webfetcher
   lsof -p <PID>
   ```

2. **分析日志**
   ```bash
   # 错误日志
   grep -i error /var/log/webfetcher/*.log

   # 最近的异常
   grep -i exception /var/log/webfetcher/*.log | tail -50

   # 按时间过滤
   awk '/2025-09-30 17:00/,/2025-09-30 18:00/' /var/log/webfetcher/app.log
   ```

#### 第三步：实施修复 (15-30分钟)

1. **应用临时修复**
   ```bash
   # 回滚到上一个版本
   git checkout <previous_commit>
   ./deploy.sh

   # 调整配置
   vi /etc/webfetcher/config.yaml
   sudo systemctl reload webfetcher
   ```

2. **验证修复**
   ```bash
   # 测试基本功能
   python test_basic.py

   # 健康检查
   curl http://localhost:8080/health
   ```

#### 第四步：恢复和验证 (30-60分钟)

1. **完全恢复服务**
2. **监控关键指标**
3. **执行完整测试套件**
4. **通知故障解决**

#### 第五步：事后分析 (1-2天内)

1. **编写故障报告**
   - 故障时间线
   - 根本原因
   - 影响范围
   - 解决措施
   - 预防方案

2. **改进措施**
   - 更新监控告警
   - 改进测试覆盖
   - 更新文档
   - 培训团队

### 9.2 故障升级矩阵 / Escalation Matrix

| 严重程度 | 响应时间 | 升级条件 | 联系人 |
|---------|---------|---------|--------|
| P0 - 严重 | 立即 | 所有用户受影响 | 技术主管 + 值班工程师 |
| P1 - 高 | 15分钟 | 部分用户受影响 | 值班工程师 |
| P2 - 中 | 1小时 | 功能降级 | 开发团队 |
| P3 - 低 | 1天 | 小问题 | 通过工单系统 |

### 9.3 应急工具包 / Emergency Toolkit

```bash
# 创建应急脚本 emergency_toolkit.sh
#!/bin/bash

# 快速诊断脚本
function quick_diag() {
    echo "=== System Status ==="
    uptime
    free -h
    df -h

    echo -e "\n=== Service Status ==="
    systemctl status webfetcher

    echo -e "\n=== Recent Errors ==="
    tail -50 /var/log/webfetcher/error.log

    echo -e "\n=== Network ==="
    netstat -tuln | grep LISTEN

    echo -e "\n=== Process ==="
    ps aux | grep webfetcher
}

# 快速修复脚本
function quick_fix() {
    echo "Attempting quick fixes..."

    # 清理临时文件
    rm -rf /tmp/webfetcher_*

    # 重启服务
    systemctl restart webfetcher

    # 验证
    sleep 5
    systemctl is-active webfetcher
}

# 收集诊断日志
function collect_logs() {
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    DIAG_DIR="/tmp/webfetcher_diag_${TIMESTAMP}"

    mkdir -p $DIAG_DIR

    # 复制日志
    cp /var/log/webfetcher/*.log $DIAG_DIR/

    # 系统信息
    uname -a > $DIAG_DIR/system_info.txt
    free -h >> $DIAG_DIR/system_info.txt
    df -h >> $DIAG_DIR/system_info.txt

    # 打包
    tar -czf "webfetcher_diag_${TIMESTAMP}.tar.gz" -C /tmp "webfetcher_diag_${TIMESTAMP}"

    echo "Diagnostic package created: webfetcher_diag_${TIMESTAMP}.tar.gz"
}

# 根据参数执行
case "$1" in
    diag)
        quick_diag
        ;;
    fix)
        quick_fix
        ;;
    collect)
        collect_logs
        ;;
    *)
        echo "Usage: $0 {diag|fix|collect}"
        exit 1
        ;;
esac
```

---

## 附录 / Appendix

### A. 常用命令参考 / Common Commands Reference

```bash
# Python环境
python --version
pip list
pip show <package>

# 系统诊断
top
htop
iostat
vmstat

# 网络
ping <host>
traceroute <host>
curl -v <url>
nslookup <domain>

# 日志
tail -f <logfile>
grep -i error <logfile>
less <logfile>

# 进程管理
ps aux | grep <process>
kill -9 <PID>
pkill -f <process_name>

# 文件系统
ls -la
du -sh
df -h
chmod 755 <file>
```

### B. 有用的资源链接 / Useful Resource Links

- [Selenium文档](https://www.selenium.dev/documentation/)
- [ChromeDriver下载](https://chromedriver.chromium.org/downloads)
- [Python文档](https://docs.python.org/3/)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/selenium)

---

最后更新：2025-09-30
版本：1.0.0
文档维护：WebFetcher Team