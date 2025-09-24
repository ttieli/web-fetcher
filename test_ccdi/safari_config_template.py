#!/usr/bin/env python3
"""
Safari Extraction Configuration for Web_Fetcher
================================================

Centralized configuration for Safari-based content extraction.
This module defines all settings, patterns, and rules for Safari fallback.

Configuration can be overridden via environment variables for flexibility
in different deployment environments.

Author: Web_Fetcher Team
Version: 1.0
Date: 2025-09-23
"""

import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


# ==============================================================================
# CORE SAFARI SETTINGS
# ==============================================================================

# Master switch for Safari extraction
SAFARI_ENABLED = os.environ.get('WF_ENABLE_SAFARI', '1') == '1'

# Timeout for Safari page loading (seconds)
SAFARI_TIMEOUT = int(os.environ.get('WF_SAFARI_TIMEOUT', '60'))

# Minimum content length to consider valid (bytes)
MIN_CONTENT_LENGTH = int(os.environ.get('WF_MIN_CONTENT_LENGTH', '1000'))

# Restrict Safari to government sites only
SAFARI_GOV_ONLY = os.environ.get('WF_SAFARI_GOV_ONLY', '0') == '1'

# Auto-detect when to use Safari based on content/errors
SAFARI_AUTO_DETECT = os.environ.get('WF_SAFARI_AUTO_DETECT', '1') == '1'

# Maximum retries for Safari extraction
SAFARI_MAX_RETRIES = int(os.environ.get('WF_SAFARI_MAX_RETRIES', '2'))

# Wait time between Safari retries (seconds)
SAFARI_RETRY_DELAY = int(os.environ.get('WF_SAFARI_RETRY_DELAY', '5'))

# Debug mode for verbose logging
SAFARI_DEBUG = os.environ.get('WF_SAFARI_DEBUG', '0') == '1'

# ==============================================================================
# SITE-SPECIFIC CONFIGURATIONS
# ==============================================================================

@dataclass
class SiteConfig:
    """Configuration for a specific site"""
    enabled: bool = True
    extractor_class: str = "GenericExtractor"
    timeout: int = SAFARI_TIMEOUT
    min_content_length: int = MIN_CONTENT_LENGTH
    captcha_indicators: List[str] = field(default_factory=list)
    content_markers: List[str] = field(default_factory=list)
    wait_for_elements: List[str] = field(default_factory=list)
    requires_login: bool = False
    custom_headers: Dict[str, str] = field(default_factory=dict)
    notes: str = ""


# Site-specific configurations
SAFARI_SITES: Dict[str, SiteConfig] = {
    'ccdi.gov.cn': SiteConfig(
        enabled=os.environ.get('WF_CCDI_ENABLED', '1') == '1',
        extractor_class='CCDIExtractor',
        timeout=60,
        min_content_length=2000,
        captcha_indicators=['seccaptcha', '验证码', '滑块验证'],
        content_markers=['class="content"', 'class="article"', '正文'],
        wait_for_elements=['div.content', 'article', '.text'],
        notes="Chinese government anti-corruption site with CAPTCHA"
    ),
    
    'qcc.com': SiteConfig(
        enabled=os.environ.get('WF_QCC_ENABLED', '1') == '1',
        extractor_class='QCCExtractor',
        timeout=45,
        min_content_length=500,
        captcha_indicators=['滑动验证', 'slide-verify', 'challenge'],
        content_markers=['company-name', 'basic-info', '企业信息'],
        wait_for_elements=['.company-header', '.detail-content'],
        notes="Chinese business information site with anti-bot measures"
    ),
    
    'www.qichacha.com': SiteConfig(
        enabled=os.environ.get('WF_QICHACHA_ENABLED', '0') == '1',
        extractor_class='QCCExtractor',  # Can reuse QCC extractor
        timeout=45,
        min_content_length=500,
        captcha_indicators=['验证码', '机器人验证'],
        content_markers=['企业名称', '统一社会信用代码'],
        notes="Alternative business information site"
    ),
    
    # Add more sites as needed
    # 'example.gov.cn': SiteConfig(...)
}

# ==============================================================================
# CAPTCHA AND BOT DETECTION INDICATORS
# ==============================================================================

# Universal CAPTCHA/bot detection indicators
CAPTCHA_INDICATORS: List[str] = [
    # English indicators
    'captcha', 'recaptcha', 'hcaptcha', 'grecaptcha',
    'security check', 'robot', 'bot detection',
    'challenge', 'verify', 'human',
    'cloudflare', 'cf-ray', 'challenge-form',
    'access denied', 'forbidden', 'blocked',
    '403 forbidden', 'rate limit',
    
    # Chinese indicators
    '验证码', '安全验证', '滑块验证', '滑动验证',
    '点击验证', '拖动滑块', '请完成验证',
    '机器人验证', '人机验证', '安全检查',
    '访问受限', '访问被拒绝',
    
    # Technical indicators
    'seccaptcha', 'geetest', 'slidecaptcha',
    'challenge-platform', 'antibot',
    '_guard', 'jsl-', 'acw_sc',
]

# HTTP status codes that indicate blocking
BLOCKING_STATUS_CODES: List[int] = [
    403,  # Forbidden
    429,  # Too Many Requests
    503,  # Service Unavailable (often used for bot protection)
    520,  # Cloudflare: Web server returns unknown error
    521,  # Cloudflare: Web server is down
    522,  # Cloudflare: Connection timed out
]

# ==============================================================================
# ERROR PATTERNS AND RECOVERY
# ==============================================================================

# Error patterns that should trigger Safari fallback
ERROR_PATTERNS: List[str] = [
    'ssl certificate', 'certificate verify failed',
    'connection reset', 'connection refused',
    'timeout', 'timed out',
    'rate limit', 'too many requests',
    'access denied', 'permission denied',
    'cloudflare', 'cf-ray',
]

# Error patterns that should NOT trigger Safari (permanent failures)
PERMANENT_ERROR_PATTERNS: List[str] = [
    '404 not found', 'page not found',
    'domain not found', 'dns resolution',
    'invalid url', 'malformed url',
]

# ==============================================================================
# CONTENT VALIDATION RULES
# ==============================================================================

@dataclass
class ContentValidationRules:
    """Rules for validating extracted content"""
    min_length: int = MIN_CONTENT_LENGTH
    max_length: int = 10_000_000  # 10MB
    required_elements: List[str] = field(default_factory=list)
    forbidden_patterns: List[str] = field(default_factory=list)
    encoding: str = 'utf-8'


# Default validation rules
DEFAULT_VALIDATION_RULES = ContentValidationRules(
    required_elements=['<body', '<div', '<p'],  # Basic HTML structure
    forbidden_patterns=['<error>', '404', 'not found'],  # Error indicators
)

# Site-specific validation rules
SITE_VALIDATION_RULES: Dict[str, ContentValidationRules] = {
    'ccdi.gov.cn': ContentValidationRules(
        min_length=2000,
        required_elements=['<article', 'class="content"', '正文'],
        forbidden_patterns=['验证码', 'captcha', '请先完成验证'],
    ),
    'qcc.com': ContentValidationRules(
        min_length=500,
        required_elements=['company', '企业', '公司'],
        forbidden_patterns=['滑动验证', '机器人验证'],
    ),
}

# ==============================================================================
# PERFORMANCE SETTINGS
# ==============================================================================

# Maximum concurrent Safari windows
MAX_SAFARI_WINDOWS = int(os.environ.get('WF_MAX_SAFARI_WINDOWS', '3'))

# Safari window cleanup interval (seconds)
SAFARI_CLEANUP_INTERVAL = int(os.environ.get('WF_SAFARI_CLEANUP_INTERVAL', '300'))

# Memory limit for Safari process (MB)
SAFARI_MEMORY_LIMIT = int(os.environ.get('WF_SAFARI_MEMORY_LIMIT', '1024'))

# ==============================================================================
# PATHS AND DIRECTORIES
# ==============================================================================

# Base directory for Web_Fetcher
BASE_DIR = Path(__file__).parent.parent

# Directory for temporary files
TEMP_DIR = Path(os.environ.get('WF_TEMP_DIR', '/tmp/safari_extraction'))
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Log directory
LOG_DIR = Path(os.environ.get('WF_LOG_DIR', BASE_DIR / 'logs'))
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Cache directory for Safari sessions
CACHE_DIR = Path(os.environ.get('WF_CACHE_DIR', '/tmp/safari_cache'))
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_site_config(url: str) -> Optional[SiteConfig]:
    """
    Get configuration for a specific URL.
    
    Args:
        url: Target URL
        
    Returns:
        SiteConfig object or None if not configured
    """
    for site_pattern, config in SAFARI_SITES.items():
        if site_pattern in url:
            return config
    return None


def is_government_site(url: str) -> bool:
    """
    Check if URL is a government site.
    
    Args:
        url: URL to check
        
    Returns:
        bool: True if government site
    """
    gov_patterns = [
        '.gov', '.gov.cn', '.govt', '.gob', 
        '.gouv', '.government', '.mil'
    ]
    url_lower = url.lower()
    return any(pattern in url_lower for pattern in gov_patterns)


def should_retry_error(error: Exception) -> bool:
    """
    Determine if an error is retryable.
    
    Args:
        error: Exception to check
        
    Returns:
        bool: True if error is retryable
    """
    error_str = str(error).lower()
    
    # Check for permanent errors (don't retry)
    for pattern in PERMANENT_ERROR_PATTERNS:
        if pattern in error_str:
            return False
    
    # Check for retryable errors
    for pattern in ERROR_PATTERNS:
        if pattern in error_str:
            return True
    
    # Default: don't retry unknown errors
    return False


def get_captcha_indicators_for_site(url: str) -> List[str]:
    """
    Get CAPTCHA indicators for a specific site.
    
    Args:
        url: Target URL
        
    Returns:
        List of CAPTCHA indicator strings
    """
    config = get_site_config(url)
    if config and config.captcha_indicators:
        return config.captcha_indicators + CAPTCHA_INDICATORS
    return CAPTCHA_INDICATORS


def validate_configuration() -> bool:
    """
    Validate current configuration settings.
    
    Returns:
        bool: True if configuration is valid
    """
    errors = []
    
    # Check timeout values
    if SAFARI_TIMEOUT <= 0:
        errors.append("SAFARI_TIMEOUT must be positive")
    
    if MIN_CONTENT_LENGTH <= 0:
        errors.append("MIN_CONTENT_LENGTH must be positive")
    
    # Check paths
    if not TEMP_DIR.exists():
        try:
            TEMP_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create TEMP_DIR: {e}")
    
    # Log any errors
    if errors:
        for error in errors:
            logger.error(f"Configuration error: {error}")
        return False
    
    return True


def get_config_summary() -> Dict[str, Any]:
    """
    Get summary of current configuration.
    
    Returns:
        Dictionary of configuration values
    """
    return {
        'safari_enabled': SAFARI_ENABLED,
        'timeout': SAFARI_TIMEOUT,
        'min_content_length': MIN_CONTENT_LENGTH,
        'gov_only': SAFARI_GOV_ONLY,
        'auto_detect': SAFARI_AUTO_DETECT,
        'debug': SAFARI_DEBUG,
        'sites_configured': len(SAFARI_SITES),
        'active_sites': sum(1 for s in SAFARI_SITES.values() if s.enabled),
        'temp_dir': str(TEMP_DIR),
        'log_dir': str(LOG_DIR),
    }


# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

if SAFARI_DEBUG:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_DIR / 'safari_extraction.log'),
            logging.StreamHandler()
        ]
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def main():
    """CLI interface for configuration management"""
    import json
    
    print("Safari Extraction Configuration")
    print("=" * 50)
    
    # Validate configuration
    if validate_configuration():
        print("✓ Configuration is valid")
    else:
        print("✗ Configuration has errors (see above)")
    
    # Show summary
    print("\nConfiguration Summary:")
    summary = get_config_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Show configured sites
    print(f"\nConfigured Sites ({len(SAFARI_SITES)}):")
    for site, config in SAFARI_SITES.items():
        status = "✓" if config.enabled else "✗"
        print(f"  {status} {site} - {config.notes}")
    
    # Export configuration if requested
    if '--export' in os.sys.argv:
        export_file = LOG_DIR / 'safari_config.json'
        with open(export_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"\nConfiguration exported to: {export_file}")


if __name__ == '__main__':
    main()