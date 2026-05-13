"""
User-facing error categorization and formatting.

This module produces structured error messages for end users (and AI agents)
instead of Python tracebacks. It complements (but does not replace) the
existing retry-oriented ErrorClassifier in classifier.py.

Two responsibilities:
1. UserErrorCategory enum — 8 broad categories AI agents can route on
2. format_user_error(...) — produces a 3-line block (type/explanation/suggestion)

Usage at top-level CLI try/except:

    try:
        run_cli(...)
    except KeyboardInterrupt:
        print('\\n已取消')
        sys.exit(130)
    except Exception as e:
        err = classify_user_error(e)
        print(format_user_error(err), file=sys.stderr)
        if debug_mode:
            traceback.print_exc()
        sys.exit(err.exit_code)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class UserErrorCategory(str, Enum):
    """End-user-facing error categories (8 + 1 fallback).

    Stable string values; AI agents can pattern-match on these.
    """
    URL_INVALID = "URL_INVALID"
    DNS_FAILURE = "DNS_FAILURE"
    SSL_ERROR = "SSL_ERROR"
    HTTP_4XX = "HTTP_4XX"
    HTTP_5XX = "HTTP_5XX"
    TIMEOUT = "TIMEOUT"
    CDP_LAUNCH_FAILED = "CDP_LAUNCH_FAILED"
    CONFIG_ERROR = "CONFIG_ERROR"
    UNKNOWN = "UNKNOWN"


@dataclass
class UserError:
    """Structured error report for end-user display."""
    category: UserErrorCategory
    explanation: str
    suggestion: str
    original: str = ""
    exit_code: int = 1


# ============================================================
# Suggestions per category (display-friendly, AI-routable)
# ============================================================
_SUGGESTIONS = {
    UserErrorCategory.URL_INVALID: "URL 缺少 scheme 或格式错误。试试 wf https://example.com",
    UserErrorCategory.DNS_FAILURE: "域名解析失败。检查 URL 拼写或网络连接",
    UserErrorCategory.SSL_ERROR: "SSL 握手失败。可能证书已过期、被 MITM 或代理问题；可尝试 --insecure（如可用）",
    UserErrorCategory.HTTP_4XX: "服务器拒绝请求（4xx）。常见原因：403=反爬可换 fetcher、404=URL 错、429=被限速",
    UserErrorCategory.HTTP_5XX: "服务端错误（5xx）。稍后重试或换网络",
    UserErrorCategory.TIMEOUT: "请求超时。增大 --timeout 或换 fetcher",
    UserErrorCategory.CDP_LAUNCH_FAILED: "headless Chrome 启动失败。检查 Chrome 是否安装、9222 端口是否冲突",
    UserErrorCategory.CONFIG_ERROR: "配置文件解析失败。检查 routing.yaml / template.yaml 语法",
    UserErrorCategory.UNKNOWN: "未知错误（错误分类器未识别）。把这段输出反馈给 wf 项目组",
}


# ============================================================
# Classification heuristics
# ============================================================

# Pattern → category mapping (first match wins)
# Each entry is (regex_pattern, category, explanation_template)
# explanation_template can use {msg} placeholder for the original message
_PATTERNS: list[tuple[re.Pattern, UserErrorCategory, str]] = [
    # URL_INVALID: missing scheme, malformed URL
    (re.compile(r"missing scheme|URL.*scheme|no scheme|invalid url", re.I),
     UserErrorCategory.URL_INVALID,
     "URL 缺少 scheme (http:// 或 https://) 或格式错误"),
    (re.compile(r"unknown url type", re.I),
     UserErrorCategory.URL_INVALID,
     "URL 类型未知，可能 scheme 拼写错误"),

    # DNS_FAILURE
    (re.compile(r"name or service not known|nodename nor servname|getaddrinfo failed|name resolution", re.I),
     UserErrorCategory.DNS_FAILURE,
     "域名解析失败，DNS 无法找到该主机"),
    (re.compile(r"temporary failure in name resolution", re.I),
     UserErrorCategory.DNS_FAILURE,
     "DNS 临时故障，稍后重试"),

    # SSL_ERROR
    (re.compile(r"ssl|certificate|cert.*verify|tls.*handshake|wrong version number", re.I),
     UserErrorCategory.SSL_ERROR,
     "SSL/TLS 握手或证书验证失败"),

    # CDP_LAUNCH_FAILED (CDP/Chrome 相关优先匹配，避免 "Chrome not found" 被 HTTP_4XX 抢)
    (re.compile(r"chrome.*not found|chromedriver|cdp[ _.].*connect|cannot connect on port|9222|debugger.*port|chrome.*launch.*fail", re.I),
     UserErrorCategory.CDP_LAUNCH_FAILED,
     "headless Chrome / CDP 连接失败"),

    # HTTP_5XX (检查在 4XX 之前，避免 50x 被 [4-5] 模式漏掉)
    (re.compile(r"\bhttp[ _.]?5\d\d\b|5\d\d.*server error|internal server error|bad gateway|service unavailable|gateway timeout", re.I),
     UserErrorCategory.HTTP_5XX,
     "服务端返回 5xx 错误"),

    # HTTP_4XX (用 \b...\b 边界，避免 "Chrome not found" 命中)
    (re.compile(r"\bhttp[ _.]?4\d\d\b|4\d\d.*client error|\bforbidden\b|http.*not found|too many requests|\bunauthorized\b", re.I),
     UserErrorCategory.HTTP_4XX,
     "服务端返回 4xx 错误（客户端问题）"),

    # TIMEOUT
    (re.compile(r"timeout|timed out|read timed out", re.I),
     UserErrorCategory.TIMEOUT,
     "请求超时"),

    # CONFIG_ERROR
    (re.compile(r"yaml|routing\.yaml|template\.yaml|config.*invalid|schema.*validation", re.I),
     UserErrorCategory.CONFIG_ERROR,
     "配置文件解析或验证失败"),
]


def classify_user_error(exc: BaseException) -> UserError:
    """Classify a raw Python exception into a UserError for display.

    Order of attempts:
    1. Exception type → direct mapping (ValueError on URL, urllib.error.URLError, etc.)
    2. Exception message regex → mapping
    3. Fallback → UNKNOWN with original message preserved
    """
    msg = str(exc) if exc else ""
    exc_type_name = type(exc).__name__

    # Type-based fast path
    if exc_type_name in ("HTTPError",):
        # urllib.error.HTTPError has .code attribute
        code = getattr(exc, 'code', 0)
        if isinstance(code, int):
            if 400 <= code < 500:
                cat = UserErrorCategory.HTTP_4XX
                explanation = f"HTTP {code} 客户端错误"
                return UserError(cat, explanation, _SUGGESTIONS[cat], original=msg)
            if 500 <= code < 600:
                cat = UserErrorCategory.HTTP_5XX
                explanation = f"HTTP {code} 服务端错误"
                return UserError(cat, explanation, _SUGGESTIONS[cat], original=msg)

    if exc_type_name in ("URLError",) and "ssl" not in msg.lower():
        # urllib URLError 经常是 DNS 或连接问题
        if "name or service" in msg.lower() or "nodename" in msg.lower():
            cat = UserErrorCategory.DNS_FAILURE
            return UserError(cat, _SUGGESTIONS[cat], _SUGGESTIONS[cat], original=msg)

    if exc_type_name in ("TimeoutError", "socket.timeout"):
        cat = UserErrorCategory.TIMEOUT
        return UserError(cat, "请求超时", _SUGGESTIONS[cat], original=msg)

    if exc_type_name.startswith("Chrome") or "Chrome" in exc_type_name:
        cat = UserErrorCategory.CDP_LAUNCH_FAILED
        return UserError(cat, "Chrome 启动/连接失败", _SUGGESTIONS[cat], original=msg)

    if exc_type_name in ("YAMLError", "ScannerError", "ParserError"):
        cat = UserErrorCategory.CONFIG_ERROR
        return UserError(cat, "YAML 配置文件解析失败", _SUGGESTIONS[cat], original=msg)

    # Message-based regex matching
    for pattern, cat, explanation in _PATTERNS:
        if pattern.search(msg):
            return UserError(cat, explanation, _SUGGESTIONS[cat], original=msg)

    # Fallback: UNKNOWN
    return UserError(
        category=UserErrorCategory.UNKNOWN,
        explanation="未识别的错误类型",
        suggestion=_SUGGESTIONS[UserErrorCategory.UNKNOWN],
        original=msg or exc_type_name,
    )


def format_user_error(err: UserError) -> str:
    """Format a UserError as a 3-section display block.

    Format:
        错误类型: <CATEGORY>
        说明: <explanation>
        建议: <suggestion>
        原始: <original>          # only if UNKNOWN

    Stable format so AI agents can grep on the section names.
    """
    lines = [
        f"错误类型: {err.category.value}",
        f"说明: {err.explanation}",
        f"建议: {err.suggestion}",
    ]
    # For UNKNOWN, also surface the original message so user/AI can debug
    if err.category == UserErrorCategory.UNKNOWN and err.original:
        lines.append(f"原始: {err.original}")
    return "\n".join(lines)


def format_retry_summary(
    attempts: int,
    final_category: UserErrorCategory,
    final_explanation: str,
) -> str:
    """One-line summary when retry exhausted.

    Format: 重试 N 次仍失败，最终错误: <CATEGORY> — <explanation>
    """
    return (f"重试 {attempts} 次仍失败，最终错误: "
            f"{final_category.value} — {final_explanation}")
