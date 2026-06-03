"""
SSL Problematic Domains Configuration
SSL问题域名配置

This module maintains a list of domains with SSL/TLS configuration issues
(specifically UNSAFE_LEGACY_RENEGOTIATION_DISABLED errors) that cause urllib
to fail. These domains are routed directly to Selenium to avoid SSL errors.

本模块维护具有SSL/TLS配置问题的域名列表（特别是UNSAFE_LEGACY_RENEGOTIATION_DISABLED错误），
这些问题导致urllib失败。这些域名直接路由到Selenium以避免SSL错误。

SCOPE: SSL/TLS compatibility issues ONLY. Do not add domains for other reasons
(e.g., JavaScript rendering requirements - those should use normal render flow).

适用范围：仅限SSL/TLS兼容性问题。不要因其他原因添加域名
（例如JavaScript渲染需求 - 应使用正常渲染流程）。

Author: Archy
Created: 2025-10-09
Updated: 2025-10-09 - Task 10: Removed xiaohongshu.com (not an SSL issue)
"""

from typing import Set, Optional
from urllib.parse import urlparse
import logging

# Immediate problematic domains that must use Selenium
# 必须使用Selenium的问题域名
SSL_PROBLEMATIC_DOMAINS: Set[str] = set()  # 域名清单已移除


def should_use_selenium_directly(url: str) -> bool:
    """
    Check if URL should bypass urllib and go directly to Selenium.
    检查URL是否应该绕过urllib直接使用Selenium。

    Args:
        url: The URL to check

    Returns:
        True if domain is in problematic list, False otherwise
        如果域名在问题列表中返回True，否则返回False
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove www. prefix for comparison
        # 移除www.前缀进行比较
        if domain.startswith('www.'):
            domain = domain[4:]

        # Check each problematic domain
        for prob_domain in SSL_PROBLEMATIC_DOMAINS:
            if prob_domain in domain:
                logging.debug(f"🎯 Domain '{domain}' matches problematic domain '{prob_domain}'")
                return True

        return False

    except Exception as e:
        logging.error(f"Error parsing URL for domain check: {e}")
        return False


def add_problematic_domain(domain: str) -> None:
    """
    Add a new problematic domain at runtime.
    运行时添加新的问题域名。

    Args:
        domain: Domain to add (without www prefix)
    """
    SSL_PROBLEMATIC_DOMAINS.add(domain.lower())
    logging.info(f"Added problematic domain: {domain}")


def get_problematic_domains() -> Set[str]:
    """
    Get current list of problematic domains.
    获取当前问题域名列表。

    Returns:
        Set of problematic domain strings
    """
    return SSL_PROBLEMATIC_DOMAINS.copy()
