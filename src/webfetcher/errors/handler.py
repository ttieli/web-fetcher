#!/usr/bin/env python3
"""
Unified Error Handling Framework
统一错误处理框架

This module provides centralized error classification, analysis, and reporting capabilities.
本模块提供集中式的错误分类、分析和报告生成功能。

Features / 功能：
- Error categorization with pattern matching / 基于模式匹配的错误分类
- Error chain extraction / 错误链提取
- Root cause analysis / 根因分析
- Markdown report generation / Markdown报告生成
- Troubleshooting guides / 故障排除指南
"""

__version__ = "1.0.0"
__author__ = "WebFetcher Team"

import re
import traceback
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime


class ErrorCategory(Enum):
    """
    Error classification categories / 错误分类类别

    Categories are used to group similar errors and provide targeted troubleshooting.
    类别用于对相似错误进行分组，并提供针对性的故障排除。
    """
    NETWORK_CONNECTION = "network_connection"  # 网络连接问题
    BROWSER_INIT = "browser_init"              # 浏览器初始化问题
    PAGE_LOAD = "page_load"                    # 页面加载问题
    PERMISSION = "permission"                  # 权限拒绝问题
    DEPENDENCY = "dependency"                  # 缺失依赖问题
    TIMEOUT = "timeout"                        # 操作超时问题
    CHROME_LAUNCH = "chrome_launch"            # Chrome启动问题
    CHROME_PERMISSION = "chrome_permission"    # Chrome权限问题
    CHROME_PORT_CONFLICT = "chrome_port"       # Chrome端口冲突
    CHROME_TIMEOUT = "chrome_timeout"          # Chrome超时问题
    UNKNOWN = "unknown"                        # 未知错误


class ErrorClassifier:
    """
    Classifier for categorizing exceptions into error categories
    异常分类器，将异常分类到错误类别

    Uses pattern matching on error messages and exception types to determine
    the appropriate error category.
    使用错误消息和异常类型的模式匹配来确定适当的错误类别。
    """

    def __init__(self):
        """Initialize the error classifier with pattern mappings / 使用模式映射初始化错误分类器"""
        self._init_error_patterns()

    def _init_error_patterns(self) -> None:
        """
        Define error message patterns mapped to categories
        定义映射到类别的错误消息模式

        Patterns are checked in order, with the first match determining the category.
        模式按顺序检查，第一个匹配决定类别。
        """
        # NOTE: Pattern order matters! More specific patterns MUST come before general ones.
        # Chrome-specific patterns are checked before generic BROWSER_INIT to avoid false matches.
        self.error_patterns: Dict[ErrorCategory, List[str]] = {
            ErrorCategory.NETWORK_CONNECTION: [
                r"connection\s+refused",
                r"connection\s+reset",
                r"connection\s+timed\s+out",
                r"failed\s+to\s+establish\s+connection",
                r"ssl",
                r"certificate",
                r"handshake",
                r"network\s+unreachable",
                r"host\s+unreachable",
                r"no\s+route\s+to\s+host",
                r"connection\s+error",
                r"socket\s+error",
            ],
            # Chrome-specific categories (must come before BROWSER_INIT)
            ErrorCategory.CHROME_LAUNCH: [
                r"chrome\s+launch",
                r"chrome\s+startup",
                r"failed\s+to\s+start\s+chrome",
                r"chrome\s+not\s+responding",
                r"chrome\s+crash",
                r"chrome\s+recovery\s+failed",
            ],
            ErrorCategory.CHROME_PERMISSION: [
                r"chrome\s+permission",
                r"permission.*chrome",
                r"access.*denied.*chrome",
                r"operation\s+not\s+permitted.*chrome",
                r"sandbox.*permission",
            ],
            ErrorCategory.CHROME_PORT_CONFLICT: [
                r"port.*9222",
                r"port.*conflict",
                r"port.*already\s+in\s+use",
                r"address\s+already\s+in\s+use",
                r"bind.*failed.*port",
                r"debug.*port.*occupied",
            ],
            ErrorCategory.CHROME_TIMEOUT: [
                r"chrome.*timeout",
                r"chrome.*timed\s+out",
                r"debug\s+session.*timeout",
                r"chrome.*not\s+responding",
                r"chrome.*health\s+check.*timeout",
            ],
            # Generic browser category (after Chrome-specific ones)
            ErrorCategory.BROWSER_INIT: [
                r"chrome",
                r"chromedriver",
                r"webdriver",
                r"browser",
                r"selenium",
                r"driver\s+executable",
                r"browser\s+initialization",
                r"failed\s+to\s+start\s+browser",
                r"browser\s+not\s+found",
                r"driver\s+not\s+found",
            ],
            ErrorCategory.PAGE_LOAD: [
                r"page\s+load",
                r"navigate",
                r"navigation",
                r"page\s+not\s+found",
                r"404",
                r"failed\s+to\s+load",
                r"document\s+not\s+ready",
                r"page\s+crash",
                r"renderer\s+timeout",
            ],
            ErrorCategory.PERMISSION: [
                r"permission\s+denied",
                r"access\s+denied",
                r"forbidden",
                r"403",
                r"unauthorized",
                r"401",
                r"authentication\s+failed",
                r"not\s+authorized",
            ],
            ErrorCategory.DEPENDENCY: [
                r"no\s+module\s+named",
                r"cannot\s+import",
                r"import\s+error",
                r"module\s+not\s+found",
                r"missing\s+dependency",
                r"package\s+not\s+found",
                r"library\s+not\s+found",
            ],
            ErrorCategory.TIMEOUT: [
                r"timeout",
                r"timed\s+out",
                r"deadline\s+exceeded",
                r"operation\s+timed\s+out",
                r"time\s+limit\s+exceeded",
                r"timeout\s+waiting",
            ],
        }

        # Compile patterns for efficiency / 编译模式以提高效率
        self.compiled_patterns: Dict[ErrorCategory, List[re.Pattern]] = {
            category: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for category, patterns in self.error_patterns.items()
        }

    def classify(self, exception: Exception) -> ErrorCategory:
        """
        Classify an exception into an error category
        将异常分类到错误类别

        Args:
            exception: The exception to classify / 要分类的异常

        Returns:
            ErrorCategory: The determined error category / 确定的错误类别
        """
        # Get error message from exception / 从异常获取错误消息
        error_message = str(exception)
        exception_type = type(exception).__name__

        # Combine message and type for pattern matching / 组合消息和类型进行模式匹配
        search_text = f"{exception_type}: {error_message}"

        # Check exception type first for common Python exceptions
        # 首先检查常见Python异常的异常类型
        if isinstance(exception, TimeoutError):
            return ErrorCategory.TIMEOUT
        elif isinstance(exception, (ConnectionError, ConnectionRefusedError, ConnectionResetError)):
            return ErrorCategory.NETWORK_CONNECTION
        elif isinstance(exception, (PermissionError, OSError)) and "permission" in error_message.lower():
            return ErrorCategory.PERMISSION
        elif isinstance(exception, (ImportError, ModuleNotFoundError)):
            return ErrorCategory.DEPENDENCY

        # Pattern matching against error messages / 根据错误消息进行模式匹配
        for category, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(search_text):
                    return category

        # Default to UNKNOWN if no pattern matches / 如果没有模式匹配，默认为UNKNOWN
        return ErrorCategory.UNKNOWN

    def get_error_chain(self, exception: Exception) -> List[Exception]:
        """
        Extract the complete error chain from an exception
        从异常中提取完整的错误链

        Args:
            exception: The exception to extract chain from / 要提取链的异常

        Returns:
            List[Exception]: List of exceptions in the chain, from outermost to innermost
                            错误链中的异常列表，从最外层到最内层
        """
        chain = []
        current = exception

        # Traverse the exception chain / 遍历异常链
        while current is not None:
            chain.append(current)
            # Check for __cause__ (explicit chaining) and __context__ (implicit chaining)
            # 检查__cause__（显式链接）和__context__（隐式链接）
            current = getattr(current, '__cause__', None) or getattr(current, '__context__', None)

            # Prevent infinite loops / 防止无限循环
            if current in chain:
                break

        return chain

    def extract_root_cause(self, exception: Exception) -> str:
        """
        Extract the root cause from an exception chain
        从异常链中提取根因

        Args:
            exception: The exception to analyze / 要分析的异常

        Returns:
            str: Description of the root cause / 根因描述
        """
        chain = self.get_error_chain(exception)

        if not chain:
            return "Unknown error"

        # The root cause is typically the last (innermost) exception
        # 根因通常是最后一个（最内层）异常
        root_exception = chain[-1]
        exception_type = type(root_exception).__name__
        error_message = str(root_exception)

        return f"{exception_type}: {error_message}"


class ErrorReporter:
    """
    Generator for detailed error reports in Markdown format
    Markdown格式的详细错误报告生成器

    Provides comprehensive error analysis with troubleshooting guidance.
    提供全面的错误分析和故障排除指导。
    """

    def __init__(self, classifier: Optional[ErrorClassifier] = None):
        """
        Initialize the error reporter
        初始化错误报告器

        Args:
            classifier: Optional ErrorClassifier instance. If None, creates a new one.
                       可选的ErrorClassifier实例。如果为None，则创建新实例。
        """
        self.classifier = classifier or ErrorClassifier()
        self._init_troubleshooting_guides()

    def _init_troubleshooting_guides(self) -> None:
        """
        Initialize troubleshooting guides for each error category
        初始化每个错误类别的故障排除指南
        """
        self.troubleshooting_guides: Dict[ErrorCategory, Dict[str, Any]] = {
            ErrorCategory.NETWORK_CONNECTION: {
                "title": "Network Connection Issues / 网络连接问题",
                "steps": [
                    "1. Check your internet connection / 检查您的网络连接",
                    "2. Verify the target URL is accessible / 验证目标URL可访问",
                    "3. Check firewall and proxy settings / 检查防火墙和代理设置",
                    "4. Verify SSL certificates if using HTTPS / 如果使用HTTPS，验证SSL证书",
                    "5. Try increasing timeout values / 尝试增加超时值",
                    "6. Check for DNS resolution issues / 检查DNS解析问题",
                ],
                "common_causes": [
                    "Network connectivity problems / 网络连接问题",
                    "Firewall blocking connections / 防火墙阻止连接",
                    "Invalid or expired SSL certificates / 无效或过期的SSL证书",
                    "DNS resolution failures / DNS解析失败",
                    "Proxy configuration issues / 代理配置问题",
                ]
            },
            ErrorCategory.BROWSER_INIT: {
                "title": "Browser Initialization Problems / 浏览器初始化问题",
                "steps": [
                    "1. Verify Chrome/Chromium is installed / 验证Chrome/Chromium已安装",
                    "2. Check ChromeDriver version matches Chrome version / 检查ChromeDriver版本与Chrome版本匹配",
                    "3. Ensure ChromeDriver is in PATH or specified correctly / 确保ChromeDriver在PATH中或正确指定",
                    "4. Try updating Chrome and ChromeDriver / 尝试更新Chrome和ChromeDriver",
                    "5. Check for port conflicts (default: 9222) / 检查端口冲突（默认：9222）",
                    "6. Verify sufficient system resources / 验证系统资源充足",
                ],
                "common_causes": [
                    "Chrome/Chromium not installed / Chrome/Chromium未安装",
                    "Version mismatch between Chrome and ChromeDriver / Chrome和ChromeDriver版本不匹配",
                    "ChromeDriver not found in PATH / ChromeDriver未在PATH中找到",
                    "Port conflicts with other services / 与其他服务的端口冲突",
                    "Insufficient system memory / 系统内存不足",
                ]
            },
            ErrorCategory.PAGE_LOAD: {
                "title": "Page Loading Issues / 页面加载问题",
                "steps": [
                    "1. Verify the URL is valid and accessible / 验证URL有效且可访问",
                    "2. Check for JavaScript errors in the page / 检查页面中的JavaScript错误",
                    "3. Increase page load timeout / 增加页面加载超时",
                    "4. Try disabling JavaScript if not required / 如果不需要，尝试禁用JavaScript",
                    "5. Check for dynamic content loading / 检查动态内容加载",
                    "6. Verify browser rendering capabilities / 验证浏览器渲染能力",
                ],
                "common_causes": [
                    "Slow page loading / 页面加载缓慢",
                    "JavaScript execution errors / JavaScript执行错误",
                    "Dynamic content not fully loaded / 动态内容未完全加载",
                    "Network latency / 网络延迟",
                    "Page requires authentication / 页面需要身份验证",
                ]
            },
            ErrorCategory.PERMISSION: {
                "title": "Permission and Access Issues / 权限和访问问题",
                "steps": [
                    "1. Check file system permissions / 检查文件系统权限",
                    "2. Verify authentication credentials / 验证身份验证凭据",
                    "3. Check if resource requires login / 检查资源是否需要登录",
                    "4. Verify user agent is not blocked / 验证用户代理未被阻止",
                    "5. Check for IP-based restrictions / 检查基于IP的限制",
                    "6. Try using different credentials or tokens / 尝试使用不同的凭据或令牌",
                ],
                "common_causes": [
                    "Insufficient file system permissions / 文件系统权限不足",
                    "Authentication required / 需要身份验证",
                    "Access denied by server / 服务器拒绝访问",
                    "IP address blocked or rate limited / IP地址被阻止或限流",
                    "Invalid credentials / 凭据无效",
                ]
            },
            ErrorCategory.DEPENDENCY: {
                "title": "Missing Dependencies / 缺失依赖",
                "steps": [
                    "1. Check if required packages are installed / 检查所需包是否已安装",
                    "2. Verify Python version compatibility / 验证Python版本兼容性",
                    "3. Install missing dependencies using pip / 使用pip安装缺失的依赖",
                    "4. Check virtual environment activation / 检查虚拟环境激活",
                    "5. Verify PYTHONPATH configuration / 验证PYTHONPATH配置",
                    "6. Review requirements.txt / 检查requirements.txt",
                ],
                "common_causes": [
                    "Required package not installed / 所需包未安装",
                    "Wrong Python version / Python版本错误",
                    "Virtual environment not activated / 虚拟环境未激活",
                    "Package version conflicts / 包版本冲突",
                    "PYTHONPATH misconfiguration / PYTHONPATH配置错误",
                ]
            },
            ErrorCategory.TIMEOUT: {
                "title": "Timeout Issues / 超时问题",
                "steps": [
                    "1. Increase timeout values in configuration / 增加配置中的超时值",
                    "2. Check network speed and latency / 检查网络速度和延迟",
                    "3. Verify server response time / 验证服务器响应时间",
                    "4. Consider implementing retry logic / 考虑实现重试逻辑",
                    "5. Check for long-running operations / 检查长时间运行的操作",
                    "6. Optimize resource-intensive operations / 优化资源密集型操作",
                ],
                "common_causes": [
                    "Network latency / 网络延迟",
                    "Slow server response / 服务器响应缓慢",
                    "Insufficient timeout values / 超时值不足",
                    "Resource-intensive operations / 资源密集型操作",
                    "Server overload / 服务器过载",
                ]
            },
            ErrorCategory.UNKNOWN: {
                "title": "Unknown Error / 未知错误",
                "steps": [
                    "1. Review the full error traceback / 检查完整的错误堆栈跟踪",
                    "2. Check application logs for more details / 检查应用程序日志以获取更多详细信息",
                    "3. Verify input parameters / 验证输入参数",
                    "4. Try reproducing the error / 尝试重现错误",
                    "5. Check for recent code changes / 检查最近的代码更改",
                    "6. Consult documentation and community resources / 查阅文档和社区资源",
                ],
                "common_causes": [
                    "Unexpected application state / 意外的应用程序状态",
                    "Edge case not handled / 未处理的边界情况",
                    "Data corruption / 数据损坏",
                    "Undocumented behavior / 未记录的行为",
                    "External system failure / 外部系统故障",
                ]
            }
        }

    def get_troubleshooting_guide(self, category: ErrorCategory) -> Dict[str, Any]:
        """
        Get the troubleshooting guide for a specific error category
        获取特定错误类别的故障排除指南

        Args:
            category: The error category / 错误类别

        Returns:
            Dict[str, Any]: Dictionary containing troubleshooting information
                           包含故障排除信息的字典
        """
        return self.troubleshooting_guides.get(category, self.troubleshooting_guides[ErrorCategory.UNKNOWN])

    def generate_markdown_report(
        self,
        url: str,
        metrics: Dict[str, Any],
        exception: Optional[Exception] = None
    ) -> str:
        """
        Generate a comprehensive Markdown error report
        生成全面的Markdown错误报告

        Args:
            url: The URL that was being processed / 正在处理的URL
            metrics: Dictionary containing performance metrics / 包含性能指标的字典
            exception: The exception that occurred, if any / 发生的异常（如有）

        Returns:
            str: Markdown-formatted error report / Markdown格式的错误报告
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Initialize report sections / 初始化报告部分
        report_lines = [
            "# ⚠️ Error Report / 错误报告",
            "",
            f"**Generated:** {timestamp}",
            f"**URL:** {url}",
            "",
        ]

        # Error classification section / 错误分类部分
        # Check if there's an error (either through exception or metrics)
        has_error = exception is not None or metrics.get('final_status') == 'failed'

        if has_error:
            # Extract error information from exception or metrics
            if exception:
                category = self.classifier.classify(exception)
                root_cause = self.classifier.extract_root_cause(exception)
                error_chain = self.classifier.get_error_chain(exception)
                error_type = type(exception).__name__
                error_message = str(exception)
            else:
                # Classify based on error_message from metrics
                error_message = metrics.get('error_message', 'Unknown error')
                error_type = metrics.get('primary_method', 'Unknown')

                # Create a mock exception for classification
                try:
                    raise Exception(error_message)
                except Exception as mock_exc:
                    category = self.classifier.classify(mock_exc)
                    root_cause = error_message
                    error_chain = []

            report_lines.extend([
                "## Error Summary / 错误摘要",
                "",
                f"**Error Type:** {error_type}",
                f"**Error Message:** {error_message}",
                "",
                "## Error Classification / 错误分类",
                "",
                f"**Category:** {category.value}",
                f"**Category Name:** {category.name}",
                "",
                "## Root Cause Analysis / 根因分析",
                "",
                f"**Root Cause:** {root_cause}",
                "",
            ])

            # Error chain section / 错误链部分
            if exception and len(error_chain) > 1:
                report_lines.extend([
                    "## Error Chain / 错误链",
                    "",
                ])
                for i, exc in enumerate(error_chain, 1):
                    report_lines.append(f"{i}. `{type(exc).__name__}`: {str(exc)}")
                report_lines.append("")

            # Troubleshooting guide / 故障排除指南
            guide = self.get_troubleshooting_guide(category)
            report_lines.extend([
                f"## {guide['title']}",
                "",
                "### Troubleshooting Steps / 故障排除步骤",
                "",
            ])
            for step in guide['steps']:
                report_lines.append(step)

            report_lines.extend([
                "",
                "### Common Causes / 常见原因",
                "",
            ])
            for cause in guide['common_causes']:
                report_lines.append(f"- {cause}")
            report_lines.append("")

            # Technical details / 技术详情 (only include traceback if exception exists)
            if exception:
                report_lines.extend([
                    "## Technical Details / 技术详情",
                    "",
                    "### Full Traceback / 完整堆栈跟踪",
                    "",
                    "```",
                    traceback.format_exc().strip(),
                    "```",
                    "",
                ])
        else:
            report_lines.extend([
                "## Status / 状态",
                "",
                "No errors occurred during processing.",
                "处理过程中未发生错误。",
                "",
            ])

        # Metrics section / 指标部分
        report_lines.extend([
            "## Metrics / 指标",
            "",
        ])

        for key, value in metrics.items():
            # Format metric key / 格式化指标键
            formatted_key = key.replace('_', ' ').title()
            report_lines.append(f"- **{formatted_key}:** {value}")

        report_lines.append("")
        report_lines.append("---")
        report_lines.append("*Report generated by WebFetcher Error Handler*")

        return "\n".join(report_lines)


# Chrome Debug Mode Exception Classes
# Chrome调试模式异常类

class ChromeDebugError(Exception):
    """
    Base exception for Chrome debug mode errors
    Chrome调试模式错误的基础异常类

    Args:
        message: Human-readable error description / 人类可读的错误描述
        error_code: Optional numeric error code / 可选的数字错误代码
        guidance: Optional troubleshooting guidance / 可选的故障排除指导
    """
    def __init__(self, message: str, error_code: Optional[int] = None, guidance: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        self.guidance = guidance
        super().__init__(self.message)


class ChromePortConflictError(ChromeDebugError):
    """
    Port 9222 or specified debug port is occupied
    端口9222或指定的调试端口被占用

    Raised when the Chrome debug port is already in use by another process.
    当Chrome调试端口已被其他进程使用时引发。
    """
    pass


class ChromePermissionError(ChromeDebugError):
    """
    macOS permission denied for Chrome operations
    macOS权限被拒绝，无法执行Chrome操作

    Raised when macOS security restrictions prevent Chrome operations.
    当macOS安全限制阻止Chrome操作时引发。
    """
    pass


class ChromeTimeoutError(ChromeDebugError):
    """
    Chrome failed to respond within timeout period
    Chrome在超时时间内未响应

    Raised when Chrome doesn't become available within the expected timeframe.
    当Chrome在预期时间内未可用时引发。
    """
    pass


class ChromeLaunchError(ChromeDebugError):
    """
    General Chrome launch failure
    通用Chrome启动失败

    Raised for Chrome startup failures that don't fit other specific categories.
    对于不属于其他特定类别的Chrome启动失败引发。
    """
    pass


class ChromeErrorMessages:
    """
    User-friendly error message templates for Chrome debug mode errors
    Chrome调试模式错误的用户友好错误消息模板

    Provides platform-specific (primarily macOS) error messages with actionable guidance.
    提供平台特定（主要是macOS）的错误消息和可操作的指导。
    """

    # macOS Permission Error Template
    PERMISSION_DENIED_MACOS = """
Chrome Permission Error (macOS)
Chrome权限错误 (macOS)

The system denied permission to access Chrome debugging features.
系统拒绝了访问Chrome调试功能的权限。

Common Causes / 常见原因:
- macOS security restrictions on Chrome user data directory
  macOS对Chrome用户数据目录的安全限制
- Insufficient file permissions on ~/.chrome-wf/
  ~/.chrome-wf/ 目录的文件权限不足

Solutions / 解决方案:

1. Check and fix directory permissions / 检查并修复目录权限:
   chmod -R u+rwX ~/.chrome-wf/

2. Verify Chrome has necessary macOS permissions / 验证Chrome具有必要的macOS权限:
   - Open System Preferences > Security & Privacy
   - Grant Chrome "Full Disk Access" if needed
   打开"系统偏好设置" > "安全性与隐私"
   如需要，授予Chrome"完全磁盘访问权限"

3. Try resetting the Chrome debug directory / 尝试重置Chrome调试目录:
   rm -rf ~/.chrome-wf/
   Then restart the fetch operation
   然后重新启动抓取操作

4. Manually launch Chrome in debug mode / 手动以调试模式启动Chrome:
   ./config/chrome-debug-launcher.sh
"""

    # Port Conflict Error Template
    PORT_CONFLICT = """
Chrome Port Conflict (Port {port})
Chrome端口冲突 (端口 {port})

The Chrome debug port ({port}) is already in use by another process.
Chrome调试端口 ({port}) 已被另一个进程占用。

Diagnostic / 诊断:
{diagnostic_info}

Solutions / 解决方案:

1. Find and stop the process using the port / 查找并停止占用端口的进程:
   lsof -ti:{port} | xargs kill -9

2. Or use a different debug port / 或使用不同的调试端口:
   export WF_CHROME_DEBUG_PORT=9223
   Then retry the operation
   然后重试操作

3. Check for stuck Chrome processes / 检查是否有卡住的Chrome进程:
   ps aux | grep -E "remote-debugging-port={port}"
   pkill -f "remote-debugging-port={port}"

4. Restart the ensure-chrome-debug script / 重启ensure-chrome-debug脚本:
   ./config/ensure-chrome-debug.sh
"""

    # Timeout Error Template
    TIMEOUT_ERROR = """
Chrome Timeout Error
Chrome超时错误

Chrome failed to become ready within the expected time ({timeout}s).
Chrome在预期时间内 ({timeout}秒) 未能准备就绪。

Possible Causes / 可能原因:
- Chrome is taking longer than usual to start
  Chrome启动时间超过正常时间
- System resources are constrained (CPU, memory)
  系统资源受限 (CPU、内存)
- Network issues preventing Chrome initialization
  网络问题阻止Chrome初始化

Solutions / 解决方案:

1. Increase the timeout value / 增加超时值:
   export WF_CHROME_TIMEOUT=30
   Then retry the operation
   然后重试操作

2. Check system resources / 检查系统资源:
   Check CPU: top
   Check memory: vm_stat (macOS) or free -h (Linux)
   检查CPU: top
   检查内存: vm_stat (macOS) 或 free -h (Linux)

3. Verify Chrome can start manually / 验证Chrome可以手动启动:
   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --version

4. Check Chrome debug logs / 检查Chrome调试日志:
   cat ~/.chrome-wf/chrome-debug.log

5. Try killing any existing Chrome processes / 尝试终止现有的Chrome进程:
   pkill -f "Google Chrome"
   Then retry the operation
   然后重试操作
"""

    # Launch Failed Error Template
    LAUNCH_FAILED = """
Chrome Launch Failed
Chrome启动失败

Chrome could not be started in debug mode.
无法以调试模式启动Chrome。

Error Details / 错误详情:
{error_details}

Common Causes / 常见原因:
- Chrome is not installed or not in expected location
  Chrome未安装或不在预期位置
- Chrome executable permissions issue
  Chrome可执行文件权限问题
- Missing required Chrome components
  缺少必需的Chrome组件
- Conflicting Chrome instances
  冲突的Chrome实例

Solutions / 解决方案:

1. Verify Chrome installation / 验证Chrome安装:
   which google-chrome-stable || which google-chrome || which chromium
   ls -la /Applications/Google\\ Chrome.app (macOS)

2. Check Chrome can launch normally / 检查Chrome是否可以正常启动:
   open -a "Google Chrome" (macOS)
   google-chrome --version (Linux)

3. Review the Chrome debug launcher script / 查看Chrome调试启动器脚本:
   cat ./config/chrome-debug-launcher.sh
   Check for any error messages
   检查是否有任何错误消息

4. Check Chrome debug logs for details / 查看Chrome调试日志了解详情:
   tail -n 50 ~/.chrome-wf/chrome-debug.log

5. Try manual launch to diagnose / 尝试手动启动以诊断:
   ./config/chrome-debug-launcher.sh
   Watch for any error messages
   观察是否有任何错误消息

6. Ensure no Chrome instances are running / 确保没有Chrome实例在运行:
   pkill -f "Google Chrome"
   Wait 5 seconds, then retry
   等待5秒，然后重试
"""

    @classmethod
    def get_message(cls, error_type: str, **kwargs) -> str:
        """
        Get formatted error message for specific error type
        获取特定错误类型的格式化错误消息

        Args:
            error_type: Type of error (permission, port_conflict, timeout, launch_failed)
                       错误类型 (permission, port_conflict, timeout, launch_failed)
            **kwargs: Additional formatting parameters / 额外的格式化参数

        Returns:
            str: Formatted error message / 格式化的错误消息
        """
        templates = {
            'permission': cls.PERMISSION_DENIED_MACOS,
            'port_conflict': cls.PORT_CONFLICT,
            'timeout': cls.TIMEOUT_ERROR,
            'launch_failed': cls.LAUNCH_FAILED,
        }

        template = templates.get(error_type, cls.LAUNCH_FAILED)

        try:
            return template.format(**kwargs)
        except KeyError:
            # If formatting fails, return template as-is
            # 如果格式化失败，按原样返回模板
            return template