# API Reference / API参考文档

## Overview / 概述

This document provides comprehensive API documentation for Web_Fetcher, including Chrome integration functions, error handling classes, and core fetching interfaces.

本文档提供Web_Fetcher的全面API文档，包括Chrome集成函数、错误处理类和核心抓取接口。

## Table of Contents / 目录

1. [Chrome Integration Functions / Chrome集成函数](#chrome-integration-functions--chrome集成函数)
2. [Exception Classes / 异常类](#exception-classes--异常类)
3. [Core Fetcher Classes / 核心抓取器类](#core-fetcher-classes--核心抓取器类)
4. [Utility Functions / 工具函数](#utility-functions--工具函数)
5. [Command Line Interface / 命令行接口](#command-line-interface--命令行接口)

---

## Chrome Integration Functions / Chrome集成函数

### ensure_chrome_debug()

Ensures Chrome debug instance is available for Selenium operations.

确保Chrome调试实例可用于Selenium操作。

```python
def ensure_chrome_debug(config: dict = None) -> tuple[bool, str]
```

**Parameters / 参数:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| config | dict | None | Configuration dictionary / 配置字典 |
| config.debug_port | int | 9222 | Chrome debug port / Chrome调试端口 |
| config.timeout | int | 15 | Startup timeout in seconds / 启动超时秒数 |
| config.force_restart | bool | False | Force Chrome restart / 强制Chrome重启 |
| config.check_only | bool | False | Only check status / 仅检查状态 |

**Returns / 返回:**

- `tuple[bool, str]`: (success, message)
  - `success`: Whether Chrome is ready / Chrome是否就绪
  - `message`: Status message or error description / 状态消息或错误描述

**Example / 示例:**

```python
from webfetcher import ensure_chrome_debug

# Basic usage / 基本用法
success, msg = ensure_chrome_debug()
if success:
    print(f"Chrome ready: {msg}")
else:
    print(f"Chrome failed: {msg}")

# Custom configuration / 自定义配置
config = {
    'debug_port': 9333,
    'timeout': 30,
    'force_restart': True
}
success, msg = ensure_chrome_debug(config)
```

### check_chrome_health()

Checks the health status of Chrome debug instance.

检查Chrome调试实例的健康状态。

```python
def check_chrome_health(port: int = 9222) -> dict
```

**Parameters / 参数:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| port | int | 9222 | Chrome debug port / Chrome调试端口 |

**Returns / 返回:**

```python
{
    'healthy': bool,          # Overall health status / 整体健康状态
    'reachable': bool,        # Port is reachable / 端口可达
    'responsive': bool,       # Chrome is responsive / Chrome响应正常
    'version': str,           # Chrome version / Chrome版本
    'process_id': int,        # Chrome process ID / Chrome进程ID
    'uptime': float,          # Uptime in seconds / 运行时间（秒）
    'tabs_count': int,        # Open tabs count / 打开的标签数
    'memory_usage': int       # Memory usage in MB / 内存使用（MB）
}
```

**Example / 示例:**

```python
from webfetcher import check_chrome_health

health = check_chrome_health(9222)
if health['healthy']:
    print(f"Chrome v{health['version']} is healthy")
    print(f"Uptime: {health['uptime']}s, Tabs: {health['tabs_count']}")
else:
    print("Chrome is unhealthy, needs recovery")
```

---

## Exception Classes / 异常类

### Chrome-Specific Exceptions / Chrome特定异常

#### ChromeNotFoundError

Raised when Chrome browser is not installed or cannot be found.

当Chrome浏览器未安装或无法找到时抛出。

```python
class ChromeNotFoundError(Exception):
    """Chrome browser not found on the system"""

    def __init__(self, message: str = None, details: dict = None):
        self.message = message or "Chrome浏览器未找到 / Chrome browser not found"
        self.details = details or {}
        self.error_code = 2
```

#### ChromePortOccupiedError

Raised when Chrome debug port is already in use.

当Chrome调试端口已被占用时抛出。

```python
class ChromePortOccupiedError(Exception):
    """Chrome debug port is occupied by another process"""

    def __init__(self, port: int, pid: int = None):
        self.port = port
        self.pid = pid
        self.message = f"端口{port}被占用 / Port {port} occupied"
        self.error_code = 1
```

#### ChromePermissionError

Raised when insufficient permissions to control Chrome.

当权限不足无法控制Chrome时抛出。

```python
class ChromePermissionError(Exception):
    """Permission denied to control Chrome"""

    def __init__(self, operation: str = None):
        self.operation = operation
        self.message = "Chrome权限被拒绝 / Chrome permission denied"
        self.error_code = 3
        self.solution = """
        macOS解决方案:
        1. 打开系统设置 → 隐私与安全
        2. 选择开发者工具
        3. 启用Terminal/iTerm
        """
```

#### ChromeTimeoutError

Raised when Chrome operations timeout.

当Chrome操作超时时抛出。

```python
class ChromeTimeoutError(Exception):
    """Chrome operation timed out"""

    def __init__(self, timeout: int, operation: str = "startup"):
        self.timeout = timeout
        self.operation = operation
        self.message = f"Chrome {operation}超时({timeout}秒) / Chrome {operation} timeout ({timeout}s)"
        self.error_code = 4
```

#### ChromeConnectionError

Raised when unable to establish connection to Chrome.

当无法建立到Chrome的连接时抛出。

```python
class ChromeConnectionError(Exception):
    """Failed to connect to Chrome debug port"""

    def __init__(self, port: int, reason: str = None):
        self.port = port
        self.reason = reason
        self.message = f"无法连接到Chrome端口{port} / Cannot connect to Chrome port {port}"
        self.error_code = 5
```

### Usage Example / 使用示例

```python
from webfetcher import (
    ChromeNotFoundError,
    ChromePermissionError,
    ensure_chrome_debug
)

try:
    success, msg = ensure_chrome_debug()
    if not success:
        raise ChromeConnectionError(9222, msg)
except ChromeNotFoundError as e:
    print(f"Error {e.error_code}: {e.message}")
    print("Please install Chrome browser")
except ChromePermissionError as e:
    print(f"Error {e.error_code}: {e.message}")
    print(e.solution)
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Core Fetcher Classes / 核心抓取器类

### WebFetcher

Main class for web content fetching with Chrome integration.

带Chrome集成的网页内容抓取主类。

```python
class WebFetcher:
    def __init__(self,
                 output_dir: str = "./output",
                 verbose: bool = False,
                 fetch_mode: str = "auto",
                 chrome_config: dict = None):
        """
        Initialize WebFetcher

        Parameters:
            output_dir: Output directory for saved content
            verbose: Enable verbose logging
            fetch_mode: "auto", "selenium", or "urllib"
            chrome_config: Chrome configuration dictionary
        """
```

#### Key Methods / 主要方法

##### fetch()

```python
def fetch(self,
          url: str,
          output_format: str = "markdown",
          custom_headers: dict = None,
          timeout: int = 30) -> dict
```

**Parameters / 参数:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| url | str | required | Target URL / 目标URL |
| output_format | str | "markdown" | Output format: "markdown" or "html" / 输出格式 |
| custom_headers | dict | None | Custom HTTP headers / 自定义HTTP头 |
| timeout | int | 30 | Request timeout in seconds / 请求超时秒数 |

**Returns / 返回:**

```python
{
    'success': bool,           # Fetch success status / 抓取成功状态
    'content': str,            # Fetched content / 抓取的内容
    'title': str,              # Page title / 页面标题
    'output_path': str,        # Saved file path / 保存的文件路径
    'fetch_mode': str,         # Used fetch mode / 使用的抓取模式
    'chrome_used': bool,       # Whether Chrome was used / 是否使用了Chrome
    'metrics': FetchMetrics    # Performance metrics / 性能指标
}
```

**Example / 示例:**

```python
from webfetcher import WebFetcher

# Initialize fetcher / 初始化抓取器
fetcher = WebFetcher(
    output_dir="./output",
    fetch_mode="auto",
    chrome_config={'debug_port': 9222}
)

# Fetch content / 抓取内容
result = fetcher.fetch(
    url="https://example.com",
    output_format="markdown",
    timeout=30
)

if result['success']:
    print(f"Content saved to: {result['output_path']}")
    print(f"Used mode: {result['fetch_mode']}")
else:
    print(f"Fetch failed: {result.get('error')}")
```

### SeleniumFetcher

Selenium-based fetcher for dynamic content.

基于Selenium的动态内容抓取器。

```python
class SeleniumFetcher:
    def __init__(self,
                 headless: bool = True,
                 debug_port: int = 9222,
                 reuse_driver: bool = False):
        """
        Initialize Selenium fetcher

        Parameters:
            headless: Run Chrome in headless mode
            debug_port: Chrome debug port
            reuse_driver: Reuse existing driver instance
        """
```

#### Key Methods / 主要方法

##### connect_to_chrome()

```python
def connect_to_chrome(self, max_retries: int = 3) -> bool
```

Connects to existing Chrome debug instance.

连接到现有的Chrome调试实例。

**Parameters / 参数:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| max_retries | int | 3 | Maximum connection retries / 最大重试次数 |

**Returns / 返回:**

- `bool`: Connection success status / 连接成功状态

##### fetch_with_selenium()

```python
def fetch_with_selenium(self,
                       url: str,
                       wait_time: int = 5,
                       scroll_pause: float = 1.0) -> dict
```

**Parameters / 参数:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| url | str | required | Target URL / 目标URL |
| wait_time | int | 5 | Page load wait time / 页面加载等待时间 |
| scroll_pause | float | 1.0 | Pause between scrolls / 滚动间隔时间 |

**Example / 示例:**

```python
from selenium_fetcher import SeleniumFetcher

fetcher = SeleniumFetcher(headless=True, debug_port=9222)
if fetcher.connect_to_chrome():
    result = fetcher.fetch_with_selenium(
        url="https://example.com",
        wait_time=10
    )
    print(f"Title: {result['title']}")
    print(f"Content length: {len(result['content'])}")
```

---

## Utility Functions / 工具函数

### FetchMetrics

Performance metrics tracking class.

性能指标跟踪类。

```python
@dataclass
class FetchMetrics:
    start_time: float
    end_time: float = None
    chrome_startup_time: float = None
    chrome_connection_time: float = None
    page_load_time: float = None
    content_extraction_time: float = None
    total_time: float = None
    chrome_healthy: bool = False
    chrome_pid: int = None
    memory_usage_mb: float = None

    def calculate_total(self):
        """Calculate total execution time"""
        if self.end_time and self.start_time:
            self.total_time = self.end_time - self.start_time
```

### get_chrome_executable()

Finds Chrome executable path on the system.

在系统上查找Chrome可执行文件路径。

```python
def get_chrome_executable() -> str
```

**Returns / 返回:**

- `str`: Chrome executable path / Chrome可执行文件路径
- `None`: If Chrome not found / 如果未找到Chrome

**Example / 示例:**

```python
from webfetcher import get_chrome_executable

chrome_path = get_chrome_executable()
if chrome_path:
    print(f"Chrome found at: {chrome_path}")
else:
    print("Chrome not installed")
```

### kill_chrome_debug_processes()

Terminates all Chrome debug instances.

终止所有Chrome调试实例。

```python
def kill_chrome_debug_processes(port: int = 9222) -> int
```

**Parameters / 参数:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| port | int | 9222 | Chrome debug port / Chrome调试端口 |

**Returns / 返回:**

- `int`: Number of processes terminated / 终止的进程数

**Example / 示例:**

```python
from webfetcher import kill_chrome_debug_processes

killed = kill_chrome_debug_processes(9222)
print(f"Terminated {killed} Chrome processes")
```

---

## Command Line Interface / 命令行接口

### wf.py

Main command-line interface for Web_Fetcher.

Web_Fetcher的主命令行接口。

```bash
usage: wf.py [-h] [--format {markdown,md,html}] [-o OUTPUT_DIR]
             [--fetch-mode {auto,selenium,urllib}] [--force-urllib]
             [--debug-port PORT] [--force-restart] [--timeout SECONDS]
             [--verbose] [--version]
             url
```

#### Arguments / 参数

##### Positional Arguments / 位置参数

| Name | Description |
|------|-------------|
| url | Target URL to fetch / 要抓取的目标URL |

##### Optional Arguments / 可选参数

| Name | Short | Default | Description |
|------|-------|---------|-------------|
| --help | -h | - | Show help message / 显示帮助信息 |
| --format | -f | markdown | Output format / 输出格式 |
| --output-dir | -o | ./output | Output directory / 输出目录 |
| --fetch-mode | - | auto | Fetch mode / 抓取模式 |
| --force-urllib | - | False | Force urllib mode / 强制urllib模式 |
| --debug-port | - | 9222 | Chrome debug port / Chrome调试端口 |
| --force-restart | - | False | Force Chrome restart / 强制Chrome重启 |
| --timeout | - | 30 | Request timeout / 请求超时 |
| --verbose | -v | False | Verbose output / 详细输出 |
| --version | - | - | Show version / 显示版本 |

#### Examples / 示例

```bash
# Basic usage / 基本用法
./wf.py https://example.com

# Specify output format and directory / 指定输出格式和目录
./wf.py https://example.com --format html -o ./downloads

# Use Selenium mode with custom port / 使用Selenium模式和自定义端口
./wf.py https://example.com --fetch-mode selenium --debug-port 9333

# Force urllib mode for quick fetch / 强制urllib模式快速抓取
./wf.py https://example.com --force-urllib

# Verbose mode with timeout / 详细模式和超时设置
./wf.py https://example.com --verbose --timeout 60

# Force Chrome restart / 强制Chrome重启
./wf.py https://example.com --force-restart
```

### webfetcher.py

Can also be run directly as a script.

也可以直接作为脚本运行。

```bash
python3 webfetcher.py [options] url
```

Options are the same as wf.py.

选项与wf.py相同。

---

## Error Codes / 错误码

### Exit Codes / 退出码

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | Operation completed successfully / 操作成功完成 |
| 1 | Port Occupied | Chrome port already in use / Chrome端口已被占用 |
| 2 | Not Found | Chrome not installed / Chrome未安装 |
| 3 | Permission Denied | Insufficient permissions / 权限不足 |
| 4 | Timeout | Operation timeout / 操作超时 |
| 5 | Connection Failed | Cannot connect to Chrome / 无法连接Chrome |
| 10 | General Error | Other errors / 其他错误 |

### Error Handling Example / 错误处理示例

```python
import sys
from webfetcher import WebFetcher, ChromePermissionError

fetcher = WebFetcher()

try:
    result = fetcher.fetch("https://example.com")
    if result['success']:
        print(f"Success: {result['output_path']}")
        sys.exit(0)
    else:
        print(f"Failed: {result.get('error')}")
        sys.exit(10)
except ChromePermissionError as e:
    print(e.message)
    print(e.solution)
    sys.exit(e.error_code)
except Exception as e:
    print(f"Unexpected error: {e}")
    sys.exit(10)
```

---

## Advanced Usage / 高级用法

### Custom Chrome Configuration / 自定义Chrome配置

```python
from webfetcher import WebFetcher

# Custom Chrome configuration / 自定义Chrome配置
chrome_config = {
    'debug_port': 9333,
    'timeout': 30,
    'force_restart': False,
    'headless': True,
    'user_data_dir': '/tmp/chrome-profile',
    'extra_flags': [
        '--disable-gpu',
        '--no-sandbox',
        '--disable-dev-shm-usage'
    ]
}

fetcher = WebFetcher(chrome_config=chrome_config)
result = fetcher.fetch("https://example.com")
```

### Batch Processing / 批量处理

```python
from webfetcher import WebFetcher
import concurrent.futures

def fetch_url(url):
    fetcher = WebFetcher()
    return fetcher.fetch(url)

urls = [
    "https://example1.com",
    "https://example2.com",
    "https://example3.com"
]

# Parallel fetching / 并行抓取
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    results = executor.map(fetch_url, urls)
    for result in results:
        if result['success']:
            print(f"✓ {result['output_path']}")
        else:
            print(f"✗ Failed: {result.get('error')}")
```

### Context Manager Usage / 上下文管理器用法

```python
from contextlib import contextmanager
from selenium_fetcher import SeleniumFetcher

@contextmanager
def chrome_session(port=9222):
    """Context manager for Chrome session"""
    fetcher = SeleniumFetcher(debug_port=port)
    try:
        if fetcher.connect_to_chrome():
            yield fetcher
        else:
            raise ChromeConnectionError(port)
    finally:
        if fetcher.driver:
            fetcher.driver.quit()

# Usage / 用法
with chrome_session(9222) as fetcher:
    result = fetcher.fetch_with_selenium("https://example.com")
    print(f"Fetched: {result['title']}")
```

---

## Version History / 版本历史

| Version | Date | Changes |
|---------|------|---------|
| 1.1.0 | 2025-10-04 | Added Chrome integration APIs / 添加Chrome集成API |
| 1.0.0 | 2025-09-30 | Initial API documentation / 初始API文档 |

---

**Last Updated / 最后更新:** 2025-10-04
**API Version / API版本:** 1.1.0
**Status / 状态:** Stable / 稳定