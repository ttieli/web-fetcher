#!/usr/bin/env python3
"""
Safari Configuration Module for Web_Fetcher
==========================================

Configuration and detection rules for Safari-based extraction.
Provides site-specific configurations, environment management,
and trigger conditions for Safari fallback extraction.

Author: Web_Fetcher Team
Version: 1.0.0
Date: 2025-09-23
"""

import os
import logging
from typing import Dict, List, Optional
from urllib.parse import urlparse

# Safari enablement - auto-enabled on macOS
import platform
SAFARI_ENABLED = platform.system() == "Darwin"
SAFARI_TIMEOUT = int(os.environ.get('WF_SAFARI_TIMEOUT', '60'))
SAFARI_GOV_ONLY = os.environ.get('WF_SAFARI_GOV_ONLY', '0') == '1'
SAFARI_AUTO_DETECT = os.environ.get('WF_SAFARI_AUTO_DETECT', '1') == '1'
SAFARI_GENERIC = os.environ.get('WF_GENERIC_SAFARI', '0') == '1'

# Log Safari status
if SAFARI_ENABLED:
    logging.getLogger(__name__).info("Safari auto-enabled on macOS")
else:
    logging.getLogger(__name__).info("Safari disabled - not running on macOS")

# Site-specific configurations
SAFARI_SITES = {
    'ccdi.gov.cn': {
        'enabled': os.environ.get('WF_CCDI_ENABLED', '1') == '1',
        'extractor_class': 'CCDIExtractor',
        'timeout': int(os.environ.get('WF_CCDI_TIMEOUT', '60')),
        'min_content_length': 200,
        'requires_user_interaction': False,
        'wait_time': 5,  # Extra wait for dynamic content
        'detection_patterns': [
            'seccaptcha', '验证码', 'security check'
        ]
    },
    'qcc.com': {
        'enabled': os.environ.get('WF_QCC_ENABLED', '1') == '1',
        'extractor_class': 'QCCExtractor',
        'timeout': int(os.environ.get('WF_QCC_TIMEOUT', '45')),
        'min_content_length': 500,
        'requires_user_interaction': True,
        'wait_time': 3,
        'detection_patterns': [
            '滑动验证', 'challenge', 'slider', 'captcha'
        ]
    }
}

# CAPTCHA and block detection patterns
CAPTCHA_INDICATORS = [
    'seccaptcha', 'captcha', '验证码', '滑动验证',
    'security check', 'challenge', 'cloudflare',
    'access denied', 'blocked', 'robot', 'bot',
    'verification', 'human verification', 'ddos'
]

# Error patterns that suggest Safari fallback is needed
ERROR_PATTERNS = [
    'connection refused', 'connection reset', 'timeout',
    'ssl error', 'certificate error', 'network error',
    'http 403', 'http 429', 'http 503', 'http 520'
]

# Government domain patterns (for safety restriction)
GOV_DOMAIN_PATTERNS = [
    '.gov.', '.edu.', '.org.cn', '.ac.cn',
    'gov.cn', 'edu.cn'
]

def get_site_config(url: str) -> Optional[Dict]:
    """
    Get site-specific configuration for a URL.
    
    Args:
        url (str): Target URL
        
    Returns:
        Optional[Dict]: Site configuration or None if not configured
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Check exact domain matches first
        if domain in SAFARI_SITES:
            config = SAFARI_SITES[domain].copy()
            config['domain'] = domain
            return config
        
        # Check if any configured domain is a suffix of the current domain
        for site_domain, config in SAFARI_SITES.items():
            if domain.endswith(site_domain):
                config_copy = config.copy()
                config_copy['domain'] = site_domain
                return config_copy
        
        return None
        
    except Exception as e:
        logging.getLogger(__name__).warning(f"Error parsing URL {url}: {e}")
        return None

def should_use_safari_for_url(url: str) -> bool:
    """
    Determine if Safari extraction should be used for a URL based on configuration.
    
    Args:
        url (str): Target URL
        
    Returns:
        bool: True if Safari should be used
    """
    if not SAFARI_ENABLED:
        return False
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Check government domain restriction
        if SAFARI_GOV_ONLY:
            is_gov_domain = any(pattern in domain for pattern in GOV_DOMAIN_PATTERNS)
            if not is_gov_domain:
                return False
        
        # Check if site is specifically configured
        site_config = get_site_config(url)
        if site_config:
            return site_config.get('enabled', False)
        
        # Allow generic Safari fallback if enabled
        return SAFARI_GENERIC
        
    except Exception as e:
        logging.getLogger(__name__).warning(f"Error checking Safari usage for {url}: {e}")
        return False

def detect_captcha_or_block(html_content: str, error_msg: str = "") -> bool:
    """
    Detect if content contains CAPTCHA or blocking indicators.
    
    Improved version that avoids false positives from JavaScript code.
    
    Args:
        html_content (str): HTML content to analyze
        error_msg (str): Error message from failed request
        
    Returns:
        bool: True if CAPTCHA/block detected
    """
    if not html_content and not error_msg:
        return False
    
    # Remove script and style tags to avoid false positives from code
    import re
    
    # Remove script tags and their content
    clean_html = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    # Remove style tags and their content  
    clean_html = re.sub(r'<style[^>]*>.*?</style>', '', clean_html, flags=re.DOTALL | re.IGNORECASE)
    
    # More specific patterns that indicate actual blocking
    # These patterns check for user-visible blocking messages, not code artifacts
    blocking_patterns = [
        # CAPTCHA-specific patterns (case-insensitive)
        (r'<[^>]*(?:captcha|seccaptcha)[^>]*>', 'CAPTCHA element detected'),
        (r'(?:请|please).*(?:验证|verify|verification)', 'Verification request detected'),
        (r'滑动.*验证|slide.*verify', 'Slider verification detected'),
        (r'security\s+check|human\s+verification', 'Security check detected'),
        
        # Access denial patterns (must be in visible text, not code)
        (r'<(?:h[1-6]|p|div)[^>]*>.*(?:access\s+denied|blocked\s+access|forbidden).*</(?:h[1-6]|p|div)>', 'Access denied message'),
        (r'(?:您的|your).*(?:访问|access).*(?:被拒绝|denied|blocked)', 'Access blocked message'),
        
        # Bot detection patterns
        (r'(?:robot|bot)\s+(?:check|verification|detected)', 'Bot detection'),
        
        # Cloudflare/DDoS protection
        (r'cloudflare.*ray\s*id|cf-ray', 'Cloudflare protection detected'),
        (r'ddos\s+protection|under\s+attack\s+mode', 'DDoS protection detected'),
    ]
    
    # Check patterns on cleaned HTML (without script/style content)
    content_lower = clean_html.lower()
    
    for pattern, description in blocking_patterns:
        if re.search(pattern, content_lower, re.IGNORECASE):
            logging.getLogger(__name__).info(f"Blocking indicator detected: {description}")
            return True
    
    # Check error messages
    if error_msg:
        error_lower = error_msg.lower()
        error_indicators = ['captcha', 'verification', 'challenge', 'blocked', 'denied', 'forbidden']
        for indicator in error_indicators:
            if indicator in error_lower:
                logging.getLogger(__name__).info(f"Error indicator detected in error message: {indicator}")
                return True
    
    # Check for very short content (likely error page) - but only on cleaned HTML
    if clean_html and len(clean_html.strip()) < 500:
        # Look for common error page indicators in the cleaned content
        error_indicators = ['error', 'blocked', 'denied', 'forbidden', 'unauthorized']
        for indicator in error_indicators:
            if indicator in content_lower:
                logging.getLogger(__name__).info(f"Error page detected (short content with indicator): {indicator}")
                return True
    
    return False

def get_extractor_class_name(url: str) -> str:
    """
    Get the extractor class name for a URL.
    
    Args:
        url (str): Target URL
        
    Returns:
        str: Extractor class name
    """
    site_config = get_site_config(url)
    if site_config:
        return site_config.get('extractor_class', 'GenericExtractor')
    return 'GenericExtractor'

def get_safari_timeout(url: str) -> int:
    """
    Get the Safari timeout for a specific URL.
    
    Args:
        url (str): Target URL
        
    Returns:
        int: Timeout in seconds
    """
    site_config = get_site_config(url)
    if site_config:
        return site_config.get('timeout', SAFARI_TIMEOUT)
    return SAFARI_TIMEOUT

def validate_safari_availability() -> tuple[bool, str]:
    """
    Validate that Safari is available for automation.
    
    Returns:
        tuple[bool, str]: (is_available, error_message)
    """
    try:
        import subprocess
        
        # Test basic AppleScript access
        result = subprocess.run([
            'osascript', '-e', 'tell application "Safari" to get name'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return False, "Safari AppleScript permissions not available. Please grant permissions in System Preferences."
        
        return True, "Safari is available"
        
    except subprocess.TimeoutExpired:
        return False, "Safari availability check timed out"
    except FileNotFoundError:
        return False, "AppleScript (osascript) not found on system"
    except Exception as e:
        return False, f"Safari availability check failed: {e}"

def log_safari_config():
    """Log current Safari configuration for debugging."""
    logger = logging.getLogger(__name__)
    logger.info("Safari Configuration:")
    logger.info(f"  SAFARI_ENABLED: {SAFARI_ENABLED}")
    logger.info(f"  SAFARI_TIMEOUT: {SAFARI_TIMEOUT}")
    logger.info(f"  SAFARI_GOV_ONLY: {SAFARI_GOV_ONLY}")
    logger.info(f"  SAFARI_AUTO_DETECT: {SAFARI_AUTO_DETECT}")
    logger.info(f"  SAFARI_GENERIC: {SAFARI_GENERIC}")
    logger.info(f"  Configured sites: {list(SAFARI_SITES.keys())}")

# Module initialization
if __name__ == "__main__":
    # Test configuration
    import logging
    logging.basicConfig(level=logging.INFO)
    
    log_safari_config()
    
    # Test URLs
    test_urls = [
        "https://www.ccdi.gov.cn/yaowenn/202509/t20250918_448431.html",
        "https://www.qcc.com/firm/abc123",
        "https://example.com/test"
    ]
    
    for url in test_urls:
        config = get_site_config(url)
        should_use = should_use_safari_for_url(url)
        extractor_class = get_extractor_class_name(url)
        timeout = get_safari_timeout(url)
        
        print(f"\nURL: {url}")
        print(f"  Config: {config}")
        print(f"  Should use Safari: {should_use}")
        print(f"  Extractor class: {extractor_class}")
        print(f"  Timeout: {timeout}")
    
    # Test Safari availability
    available, message = validate_safari_availability()
    print(f"\nSafari availability: {available}")
    print(f"Message: {message}")