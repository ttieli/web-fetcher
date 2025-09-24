#!/usr/bin/env python3
"""
Safari Extractors Package for Web_Fetcher
========================================

Site-specific extractors for Safari-based content extraction.
Provides a modular architecture for handling different websites
with specialized extraction logic.

Author: Web_Fetcher Team
Version: 1.0.0
"""

from .base_extractor import BaseExtractor

def get_extractor_for_site(url: str) -> 'BaseExtractor':
    """
    Factory function to get the appropriate extractor for a URL.
    
    Args:
        url (str): Target URL
        
    Returns:
        BaseExtractor: Appropriate extractor instance
    """
    from plugins.safari.config import get_extractor_class_name
    
    extractor_class_name = get_extractor_class_name(url)
    
    if extractor_class_name == 'CCDIExtractor':
        from .ccdi_extractor import CCDIExtractor
        return CCDIExtractor(url)
    elif extractor_class_name == 'QCCExtractor':
        from .qcc_extractor import QCCExtractor
        return QCCExtractor(url)
    else:
        from .generic_extractor import GenericExtractor
        return GenericExtractor(url)

__all__ = ['BaseExtractor', 'get_extractor_for_site']