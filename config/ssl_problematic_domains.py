"""
SSL Problematic Domains Configuration
SSL问题域名配置

This module maintains a list of domains known to have SSL configuration issues
that cause urllib to fail repeatedly. These domains should be routed directly
to Selenium to avoid wasting ~20 seconds on failed urllib attempts.

维护已知SSL配置问题域名列表，这些域名会导致urllib重复失败。
这些域名应直接路由到Selenium，避免浪费约20秒在失败的urllib尝试上。

Author: Archy
Created: 2025-10-09
"""

from typing import Set, Optional
from urllib.parse import urlparse
import logging

# Immediate problematic domains that must use Selenium
# 必须使用Selenium的问题域名
SSL_PROBLEMATIC_DOMAINS: Set[str] = {
    # Chinese Banks - UNSAFE_LEGACY_RENEGOTIATION_DISABLED
    # 中国银行 - SSL遗留重协商禁用问题
    'cebbank.com.cn',  # 中国光大银行 - Confirmed SSL error
    'icbc.com.cn',     # 中国工商银行 - Potential SSL issues
    'ccb.com',         # 中国建设银行 - Potential SSL issues
    'boc.cn',          # 中国银行 - Potential SSL issues

    # JavaScript-heavy sites that always need Selenium anyway
    # JavaScript密集型网站，总是需要Selenium
    'xiaohongshu.com',  # 小红书 - Heavy JS rendering
    'xhslink.com',      # 小红书链接 - Redirect service with JS
}


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
