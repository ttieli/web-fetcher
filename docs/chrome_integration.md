# Chrome Integration Guide / Chrome集成指南

## Overview / 概述

Web_Fetcher now includes seamless Chrome browser integration for enhanced web scraping capabilities. The system automatically manages Chrome debug instances, providing a reliable foundation for Selenium-based content extraction.

Web_Fetcher现已集成无缝Chrome浏览器支持，增强网页抓取能力。系统自动管理Chrome调试实例，为基于Selenium的内容提取提供可靠基础。

## Table of Contents / 目录

1. [Prerequisites / 前置条件](#prerequisites--前置条件)
2. [Quick Start / 快速开始](#quick-start--快速开始)
3. [Architecture / 架构设计](#architecture--架构设计)
4. [Configuration / 配置](#configuration--配置)
5. [Error Handling / 错误处理](#error-handling--错误处理)
6. [API Reference / API参考](#api-reference--api参考)
7. [Troubleshooting / 故障排除](#troubleshooting--故障排除)
8. [Performance Tuning / 性能优化](#performance-tuning--性能优化)

## Prerequisites / 前置条件

### System Requirements / 系统要求

- **Operating System / 操作系统:**
  - macOS 10.15+ (Catalina or later)
  - Linux (Ubuntu 20.04+, Debian 10+, RHEL 8+)
  - Windows support coming soon / Windows支持即将推出

- **Chrome Browser / Chrome浏览器:**
  - Version 90.0 or higher / 90.0或更高版本
  - Must be installed at standard location / 必须安装在标准位置
  - macOS: `/Applications/Google Chrome.app`
  - Linux: `/usr/bin/google-chrome` or `/usr/bin/chromium`

- **Python Requirements / Python要求:**
  - Python 3.7+
  - selenium >= 4.0
  - urllib3 (standard library)

### macOS Permission Setup / macOS权限设置

On macOS, you may need to grant Terminal/iTerm permission to control Chrome:

在macOS上，您可能需要授予终端控制Chrome的权限：

1. Open **System Settings** / 打开**系统设置**
2. Navigate to **Privacy & Security** → **Automation** / 进入**隐私与安全** → **自动化**
3. Enable Terminal/iTerm to control **Google Chrome** / 允许终端控制**Google Chrome**
4. Navigate to **Privacy & Security** → **Developer Tools** / 进入**隐私与安全** → **开发者工具**
5. Enable **Terminal** or **iTerm** / 启用**终端**或**iTerm**

## Quick Start / 快速开始

### Basic Usage / 基本使用

```bash
# Automatic Chrome mode (default)
# 自动Chrome模式（默认）
./wf.py https://example.com

# Explicitly use Selenium with Chrome
# 明确使用Selenium与Chrome
./wf.py https://example.com --fetch-mode selenium

# Force urllib mode (bypass Chrome)
# 强制urllib模式（绕过Chrome）
./wf.py https://example.com --force-urllib
```

### First Run / 首次运行

On first run, the system will:
首次运行时，系统将：

1. Check for Chrome installation / 检查Chrome安装
2. Start Chrome debug instance / 启动Chrome调试实例
3. Verify connection / 验证连接
4. Begin content extraction / 开始内容提取

Example output:
示例输出：

```
🔍 Checking Chrome debug instance...
✅ Chrome is ready on port 9222
📊 Starting content extraction...
✅ Content saved to output/2025-10-04-120000 - Example.md
```

## Architecture / 架构设计

### Component Overview / 组件概览

```
┌─────────────┐
│   wf.py     │ User Interface / 用户接口
└──────┬──────┘
       │
┌──────▼──────────────┐
│  webfetcher.py      │ Core Engine / 核心引擎
│  ┌────────────────┐ │
│  │ensure_chrome() │ │ Chrome Manager / Chrome管理器
│  └────────┬───────┘ │
└───────────┼─────────┘
            │
┌───────────▼────────────┐
│ ensure-chrome-debug.sh │ Shell Script / Shell脚本
│  ┌──────────────────┐  │
│  │ Health Check     │  │ 健康检查
│  │ Auto Recovery    │  │ 自动恢复
│  │ Process Lock     │  │ 进程锁
│  └──────────────────┘  │
└────────────────────────┘
```

### Chrome Lifecycle Management / Chrome生命周期管理

1. **Cold Start / 冷启动:**
   - No Chrome instance running / 无Chrome实例运行
   - System launches new instance / 系统启动新实例
   - Typical time: 2-3 seconds / 典型耗时：2-3秒

2. **Hot Connect / 热连接:**
   - Chrome already running / Chrome已运行
   - Instant connection / 即时连接
   - Typical time: <100ms / 典型耗时：<100毫秒

3. **Recovery / 恢复:**
   - Detects stale/crashed Chrome / 检测异常Chrome
   - Automatic cleanup and restart / 自动清理并重启
   - Typical time: 3-4 seconds / 典型耗时：3-4秒

## Configuration / 配置

### Environment Variables / 环境变量

```bash
# Chrome debug port (default: 9222)
# Chrome调试端口（默认：9222）
export CHROME_DEBUG_PORT=9222

# Chrome startup timeout in seconds (default: 15)
# Chrome启动超时秒数（默认：15）
export CHROME_STARTUP_TIMEOUT=15

# Disable Chrome auto-launch
# 禁用Chrome自动启动
export WF_DISABLE_AUTO_CHROME=1

# Chrome executable path (auto-detected if not set)
# Chrome可执行文件路径（未设置则自动检测）
export CHROME_EXECUTABLE="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

### Command Line Options / 命令行选项

```bash
# Specify custom debug port
# 指定自定义调试端口
./wf.py https://example.com --debug-port 9333

# Force Chrome restart
# 强制Chrome重启
./wf.py https://example.com --force-restart

# Set connection timeout
# 设置连接超时
./wf.py https://example.com --timeout 30
```

## Error Handling / 错误处理

### Error Categories / 错误类别

The system handles 5 main Chrome-related error categories:
系统处理5个主要Chrome相关错误类别：

1. **ChromeNotFoundError** - Chrome browser not installed / Chrome浏览器未安装
2. **ChromePortOccupiedError** - Debug port already in use / 调试端口已占用
3. **ChromePermissionError** - Insufficient permissions / 权限不足
4. **ChromeTimeoutError** - Startup/connection timeout / 启动/连接超时
5. **ChromeConnectionError** - Unable to connect to Chrome / 无法连接到Chrome

### Error Messages / 错误消息

Each error provides bilingual messages with actionable solutions:
每个错误提供双语消息和可操作的解决方案：

```python
ChromePermissionError:
  Chinese: Chrome启动失败：权限被拒绝
  English: Chrome launch failed: Permission denied

  Solution / 解决方案:
  1. 打开系统设置 → 隐私与安全
  2. 选择开发者工具
  3. 启用Terminal/iTerm
```

### Exit Codes / 退出码

| Code | Meaning / 含义 | Description / 描述 |
|------|---------------|-------------------|
| 0 | Success / 成功 | Chrome ready / Chrome就绪 |
| 1 | Port Occupied / 端口占用 | Another process using port / 其他进程占用端口 |
| 2 | Not Found / 未找到 | Chrome not installed / Chrome未安装 |
| 3 | Permission / 权限 | Access denied / 访问被拒绝 |
| 4 | Timeout / 超时 | Startup timeout / 启动超时 |

## API Reference / API参考

### Python Functions / Python函数

#### ensure_chrome_debug()

```python
def ensure_chrome_debug(config: dict = None) -> tuple[bool, str]:
    """
    Ensure Chrome debug instance is available
    确保Chrome调试实例可用

    Parameters / 参数:
        config (dict): Configuration options / 配置选项
            - debug_port (int): Debug port number / 调试端口号 (default: 9222)
            - timeout (int): Startup timeout / 启动超时 (default: 15)
            - force_restart (bool): Force restart / 强制重启 (default: False)

    Returns / 返回:
        tuple[bool, str]: (success, message)
            - success: Whether Chrome is ready / Chrome是否就绪
            - message: Status or error message / 状态或错误消息

    Example / 示例:
        >>> success, msg = ensure_chrome_debug({'debug_port': 9222})
        >>> if success:
        ...     print(f"Chrome ready: {msg}")
        ... else:
        ...     print(f"Chrome failed: {msg}")
    """
```

#### Chrome Exception Classes / Chrome异常类

```python
class ChromeNotFoundError(Exception):
    """Chrome browser not found / Chrome浏览器未找到"""

class ChromePortOccupiedError(Exception):
    """Chrome debug port occupied / Chrome调试端口被占用"""

class ChromePermissionError(Exception):
    """Chrome permission denied / Chrome权限被拒绝"""

class ChromeTimeoutError(Exception):
    """Chrome operation timeout / Chrome操作超时"""

class ChromeConnectionError(Exception):
    """Chrome connection failed / Chrome连接失败"""
```

### Shell Scripts / Shell脚本

#### ensure-chrome-debug.sh

```bash
# Usage / 使用方法:
./config/ensure-chrome-debug.sh [options]

# Options / 选项:
  --port PORT          Debug port / 调试端口 (default: 9222)
  --timeout SECONDS    Startup timeout / 启动超时 (default: 15)
  --force             Force restart / 强制重启
  --check-only        Only check status / 仅检查状态
  --verbose           Verbose output / 详细输出
  --help              Show help / 显示帮助

# Examples / 示例:
  ./config/ensure-chrome-debug.sh --port 9333
  ./config/ensure-chrome-debug.sh --force --verbose
  ./config/ensure-chrome-debug.sh --check-only
```

## Troubleshooting / 故障排除

### Common Issues / 常见问题

#### 1. Chrome Won't Start / Chrome无法启动

**Symptoms / 症状:**
- Timeout errors / 超时错误
- "Chrome not found" messages / "未找到Chrome"消息

**Solutions / 解决方案:**
```bash
# Check Chrome installation
# 检查Chrome安装
ls -la "/Applications/Google Chrome.app" # macOS
which google-chrome # Linux

# Check Chrome version
# 检查Chrome版本
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version

# Manually test Chrome debug mode
# 手动测试Chrome调试模式
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.chrome-wf"
```

#### 2. Permission Denied / 权限被拒绝

**macOS Specific / macOS特定:**
```bash
# Reset permissions
# 重置权限
tccutil reset All com.apple.Terminal
tccutil reset All com.googlecode.iterm2

# Grant full disk access
# 授予完全磁盘访问权限
# System Settings → Privacy & Security → Full Disk Access
# Add Terminal/iTerm
```

#### 3. Port Already in Use / 端口已被使用

**Diagnosis / 诊断:**
```bash
# Find process using port
# 查找占用端口的进程
lsof -i:9222
netstat -an | grep 9222

# Kill process
# 终止进程
kill -9 $(lsof -t -i:9222)
```

**Prevention / 预防:**
```bash
# Use different port
# 使用不同端口
export CHROME_DEBUG_PORT=9333
./wf.py https://example.com --debug-port 9333
```

#### 4. Slow Startup / 启动缓慢

**Optimization / 优化:**
```bash
# Keep Chrome running between requests
# 在请求之间保持Chrome运行
./config/chrome-debug-launcher.sh

# Pre-warm Chrome cache
# 预热Chrome缓存
curl -s http://localhost:9222/json/version

# Reduce startup flags
# 减少启动标志
# Edit ensure-chrome-debug.sh to remove unnecessary flags
```

### Debug Commands / 调试命令

```bash
# Check Chrome status
# 检查Chrome状态
curl -s http://localhost:9222/json/version | jq .

# List open tabs
# 列出打开的标签
curl -s http://localhost:9222/json | jq .

# View Chrome processes
# 查看Chrome进程
ps aux | grep -E "remote-debugging-port"

# Check lock files
# 检查锁文件
ls -la ~/.chrome-wf/.chrome-debug.*

# View Chrome logs
# 查看Chrome日志
tail -f ~/.chrome-wf/chrome-debug.log

# Test health check
# 测试健康检查
./config/ensure-chrome-debug.sh --check-only --verbose
```

## Performance Tuning / 性能优化

### Benchmarks / 基准测试

| Operation / 操作 | Target / 目标 | Typical / 典型 |
|-----------------|--------------|----------------|
| Cold start / 冷启动 | < 3s | 2-3s |
| Hot connect / 热连接 | < 100ms | 50-80ms |
| Recovery / 恢复 | < 4s | 3-4s |
| Memory usage / 内存使用 | < 200MB | 150-180MB |
| CPU idle / CPU空闲 | < 5% | 2-3% |

### Optimization Tips / 优化建议

1. **Keep Chrome Running / 保持Chrome运行:**
   ```bash
   # Start Chrome in background
   # 后台启动Chrome
   nohup ./config/chrome-debug-launcher.sh &
   ```

2. **Reduce Memory Usage / 减少内存使用:**
   ```bash
   # Add memory limit flags
   # 添加内存限制标志
   --max_old_space_size=512
   --js-flags="--max-old-space-size=512"
   ```

3. **Faster Startup / 更快启动:**
   ```bash
   # Disable unnecessary features
   # 禁用不必要的功能
   --disable-gpu
   --disable-dev-shm-usage
   --no-sandbox
   ```

4. **Connection Pool / 连接池:**
   ```python
   # Reuse Chrome connections
   # 重用Chrome连接
   from selenium_fetcher import SeleniumFetcher
   fetcher = SeleniumFetcher(reuse_driver=True)
   ```

## Advanced Usage / 高级用法

### Custom Chrome Profiles / 自定义Chrome配置文件

```bash
# Use specific user profile
# 使用特定用户配置文件
export CHROME_USER_DATA_DIR="$HOME/my-chrome-profile"
./wf.py https://example.com

# Use incognito mode
# 使用隐身模式
export CHROME_FLAGS="--incognito"
./wf.py https://example.com
```

### Multiple Chrome Instances / 多个Chrome实例

```bash
# Run multiple instances on different ports
# 在不同端口运行多个实例
CHROME_DEBUG_PORT=9222 ./wf.py site1.com &
CHROME_DEBUG_PORT=9333 ./wf.py site2.com &
CHROME_DEBUG_PORT=9444 ./wf.py site3.com &
```

### Headless vs Headful / 无头vs有头模式

```bash
# Headless mode (default)
# 无头模式（默认）
./wf.py https://example.com

# Headful mode (visible browser)
# 有头模式（可见浏览器）
export CHROME_HEADLESS=false
./wf.py https://example.com
```

## Integration with CI/CD / CI/CD集成

### GitHub Actions Example / GitHub Actions示例

```yaml
name: Web Scraping with Chrome
on: [push]

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Chrome
        uses: browser-actions/setup-chrome@latest

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install selenium beautifulsoup4

      - name: Run scraper
        run: |
          export CHROME_EXECUTABLE=$(which google-chrome)
          ./wf.py https://example.com
```

### Docker Example / Docker示例

```dockerfile
FROM python:3.9-slim

# Install Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . /app
WORKDIR /app

# Install Python dependencies
RUN pip install -r requirements.txt

# Run with Chrome
CMD ["./wf.py", "https://example.com"]
```

## Best Practices / 最佳实践

1. **Always Handle Errors / 始终处理错误:**
   ```python
   try:
       success, msg = ensure_chrome_debug()
       if not success:
           logger.warning(f"Chrome failed: {msg}, falling back to urllib")
           use_urllib_mode()
   except Exception as e:
       logger.error(f"Unexpected error: {e}")
       use_urllib_mode()
   ```

2. **Monitor Chrome Health / 监控Chrome健康:**
   ```bash
   # Add to crontab
   */5 * * * * /path/to/config/ensure-chrome-debug.sh --check-only
   ```

3. **Clean Up Resources / 清理资源:**
   ```python
   # Always close Chrome connections
   try:
       # Do work
   finally:
       if driver:
           driver.quit()
   ```

4. **Log Chrome Events / 记录Chrome事件:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   logger = logging.getLogger('chrome')
   ```

## Support / 支持

### Getting Help / 获取帮助

- Check logs / 查看日志: `~/.chrome-wf/chrome-debug.log`
- Run diagnostics / 运行诊断: `./config/ensure-chrome-debug.sh --verbose`
- Review test results / 查看测试结果: `./tests/run_chrome_tests.sh`

### Reporting Issues / 报告问题

When reporting Chrome integration issues, please include:
报告Chrome集成问题时，请包含：

1. System information / 系统信息: `uname -a`
2. Chrome version / Chrome版本: `google-chrome --version`
3. Error messages / 错误消息: Complete output / 完整输出
4. Debug logs / 调试日志: `~/.chrome-wf/*.log`
5. Configuration / 配置: Environment variables / 环境变量

---

**Last Updated / 最后更新:** 2025-10-04
**Version / 版本:** 1.0.0
**Status / 状态:** Production Ready / 生产就绪