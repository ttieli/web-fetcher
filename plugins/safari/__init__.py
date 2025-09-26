"""
Safari Module for Web_Fetcher
============================

Consolidated Safari automation and configuration module.
Provides unified access to Safari configuration, extraction logic,
and plugin integration for CAPTCHA bypass and content extraction.

This module consolidates all Safari-related functionality including:
- Configuration management (config.py)
- Safari automation and extraction logic (extractor.py)  
- Plugin system integration (plugin.py)

Author: Web_Fetcher Team
Version: 1.0.0
Date: 2025-09-24
"""

# Import main Safari components for unified access
from .config import (
    SAFARI_ENABLED,
    SAFARI_TIMEOUT,
    SAFARI_GOV_ONLY,
    SAFARI_AUTO_DETECT,
    SAFARI_GENERIC,
    SAFARI_SITES,
    get_site_config,
    should_use_safari_for_url,
    detect_captcha_or_block,
    get_extractor_class_name,
    get_safari_timeout,
    validate_safari_availability,
    log_safari_config
)

from .extractor import (
    SafariExtractor,
    create_safari_extractor,
    should_fallback_to_safari,
    extract_with_safari_fallback
)

from .plugin import SafariFetcherPlugin

# Backward compatibility alias
SafariPlugin = SafariFetcherPlugin

# Expose key components for external use
__all__ = [
    # Configuration
    'SAFARI_ENABLED',
    'SAFARI_TIMEOUT', 
    'get_site_config',
    'should_use_safari_for_url',
    'detect_captcha_or_block',
    'validate_safari_availability',
    
    # Extraction
    'SafariExtractor',
    'create_safari_extractor',
    'should_fallback_to_safari',
    'extract_with_safari_fallback',
    
    # Plugin
    'SafariFetcherPlugin',
    'SafariPlugin'  # Backward compatibility alias
]