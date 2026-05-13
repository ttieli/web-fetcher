"""Tests for user-facing error categorization (B1 + B2)."""
import sys
import os
import urllib.error

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from webfetcher.errors.user_facing import (
    UserErrorCategory,
    UserError,
    classify_user_error,
    format_user_error,
    format_retry_summary,
)


# ============================================================
# Classification tests — one per category
# ============================================================

def test_classify_url_invalid_missing_scheme():
    exc = ValueError("URL missing scheme: not-a-url")
    err = classify_user_error(exc)
    assert err.category == UserErrorCategory.URL_INVALID
    assert "scheme" in err.explanation.lower() or "URL" in err.explanation


def test_classify_url_invalid_unknown_type():
    exc = ValueError("unknown url type: 'wtf://test'")
    err = classify_user_error(exc)
    assert err.category == UserErrorCategory.URL_INVALID


def test_classify_dns_failure_getaddrinfo():
    exc = OSError("[Errno -2] Name or service not known")
    err = classify_user_error(exc)
    assert err.category == UserErrorCategory.DNS_FAILURE


def test_classify_dns_failure_via_urlerror():
    exc = urllib.error.URLError("<urlopen error [Errno 8] nodename nor servname provided>")
    err = classify_user_error(exc)
    assert err.category == UserErrorCategory.DNS_FAILURE


def test_classify_ssl_error_cert():
    exc = Exception("SSL: CERTIFICATE_VERIFY_FAILED certificate has expired")
    err = classify_user_error(exc)
    assert err.category == UserErrorCategory.SSL_ERROR


def test_classify_http_4xx_by_type_and_code():
    """urllib.error.HTTPError 携带 .code 属性，应按 code 分流。"""
    exc = urllib.error.HTTPError(
        url='http://example.com', code=403, msg='Forbidden', hdrs=None, fp=None)
    err = classify_user_error(exc)
    assert err.category == UserErrorCategory.HTTP_4XX
    assert "403" in err.explanation


def test_classify_http_5xx_by_type_and_code():
    exc = urllib.error.HTTPError(
        url='http://example.com', code=503, msg='Service Unavailable', hdrs=None, fp=None)
    err = classify_user_error(exc)
    assert err.category == UserErrorCategory.HTTP_5XX
    assert "503" in err.explanation


def test_classify_http_5xx_by_message_only():
    """无 code 属性时按 message 正则识别。"""
    exc = Exception("got HTTP 502 Bad Gateway")
    err = classify_user_error(exc)
    assert err.category == UserErrorCategory.HTTP_5XX


def test_classify_timeout():
    exc = TimeoutError("Read timed out")
    err = classify_user_error(exc)
    assert err.category == UserErrorCategory.TIMEOUT


def test_classify_cdp_launch_failed():
    exc = Exception("Chrome not found in PATH")
    err = classify_user_error(exc)
    assert err.category == UserErrorCategory.CDP_LAUNCH_FAILED


def test_classify_cdp_port_conflict():
    exc = Exception("CDP cannot connect on port 9222")
    err = classify_user_error(exc)
    assert err.category == UserErrorCategory.CDP_LAUNCH_FAILED


def test_classify_config_error_yaml():
    exc = Exception("YAML parse error at routing.yaml line 12")
    err = classify_user_error(exc)
    assert err.category == UserErrorCategory.CONFIG_ERROR


def test_classify_unknown_fallback():
    exc = RuntimeError("something nobody can predict")
    err = classify_user_error(exc)
    assert err.category == UserErrorCategory.UNKNOWN
    # 原始 message 必须保留供调试
    assert "something nobody can predict" in err.original


# ============================================================
# Formatting tests
# ============================================================

def test_format_user_error_three_sections():
    err = UserError(
        category=UserErrorCategory.URL_INVALID,
        explanation="URL 缺少 scheme",
        suggestion="试试 wf https://example.com",
    )
    out = format_user_error(err)
    assert "错误类型: URL_INVALID" in out
    assert "说明: URL 缺少 scheme" in out
    assert "建议: 试试 wf https://example.com" in out
    # 非 UNKNOWN 不应输出原始 (避免噪音)
    assert "原始:" not in out


def test_format_user_error_unknown_includes_original():
    err = classify_user_error(RuntimeError("specific weird error xyz"))
    out = format_user_error(err)
    assert "错误类型: UNKNOWN" in out
    assert "原始: specific weird error xyz" in out


def test_format_retry_summary():
    summary = format_retry_summary(
        attempts=3,
        final_category=UserErrorCategory.SSL_ERROR,
        final_explanation="证书已过期",
    )
    assert "重试 3 次仍失败" in summary
    assert "SSL_ERROR" in summary
    assert "证书已过期" in summary


# ============================================================
# Cross-category integration
# ============================================================

def test_all_8_categories_are_distinct():
    """8 个非 UNKNOWN 分类都应有独立的 suggestion 文案，避免雷同。"""
    from webfetcher.errors.user_facing import _SUGGESTIONS
    real_categories = [c for c in UserErrorCategory if c != UserErrorCategory.UNKNOWN]
    assert len(real_categories) == 8
    suggestions = [_SUGGESTIONS[c] for c in real_categories]
    assert len(set(suggestions)) == 8, "all 8 suggestions must be distinct"


def test_classify_handles_none_message():
    """退化输入也不应崩溃。"""
    class WeirdErr(Exception):
        def __str__(self):
            return ""
    err = classify_user_error(WeirdErr())
    assert err.category == UserErrorCategory.UNKNOWN
