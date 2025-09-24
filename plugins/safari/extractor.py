#!/usr/bin/env python3
"""
Safari Extraction Module for Web_Fetcher
=======================================

Main coordinator for Safari-based content extraction.
Provides CAPTCHA bypass via Safari browser automation with
intelligent fallback detection and site-specific routing.

Author: Web_Fetcher Team
Version: 1.0.0
Date: 2025-09-23
"""

import os
import logging
import time
from typing import Optional, Tuple, Dict, Any
from urllib.parse import urlparse

# Import configuration and extractors
from .config import (
    SAFARI_ENABLED, should_use_safari_for_url, detect_captcha_or_block,
    get_site_config, validate_safari_availability, log_safari_config
)
from extractors import get_extractor_for_site

class SafariExtractor:
    """
    Main Safari extraction coordinator.
    
    Handles detection of when Safari extraction is needed,
    routes to appropriate site-specific extractors, and
    converts results to webfetcher-compatible format.
    """
    
    def __init__(self):
        """Initialize the Safari extractor."""
        self.logger = logging.getLogger(__name__)
        self._safari_available = None  # Cache Safari availability check
        
        # Log configuration on first use
        if self.logger.isEnabledFor(logging.INFO):
            log_safari_config()
    
    def is_safari_available(self) -> bool:
        """
        Check if Safari is available (cached).
        
        Returns:
            bool: True if Safari is available for automation
        """
        if self._safari_available is None:
            available, message = validate_safari_availability()
            self._safari_available = available
            
            if available:
                self.logger.info("Safari is available for extraction")
            else:
                self.logger.warning(f"Safari not available: {message}")
        
        return self._safari_available
    
    def should_use_safari(self, url: str, html_content: str = "", 
                         error: Optional[Exception] = None) -> bool:
        """
        Determine if Safari extraction should be used.
        
        Args:
            url (str): Target URL
            html_content (str): HTML content from failed request (if any)
            error (Exception): Error from failed request (if any)
            
        Returns:
            bool: True if Safari extraction should be used
        """
        # Check basic requirements
        if not SAFARI_ENABLED:
            self.logger.debug("Safari extraction disabled by configuration")
            return False
        
        if not self.is_safari_available():
            self.logger.debug("Safari not available on system")
            return False
        
        # Check URL-based rules
        if not should_use_safari_for_url(url):
            self.logger.debug(f"URL not configured for Safari extraction: {url}")
            return False
        
        # Check for CAPTCHA or blocking indicators
        error_msg = str(error) if error else ""
        if detect_captcha_or_block(html_content, error_msg):
            self.logger.info(f"CAPTCHA/block detected for {url}, using Safari")
            return True
        
        # Check if we have a specific site configuration
        site_config = get_site_config(url)
        if site_config:
            self.logger.info(f"Site-specific Safari extraction configured for {url}")
            return True
        
        self.logger.debug(f"No Safari trigger conditions met for {url}")
        return False
    
    def fetch_with_safari(self, url: str) -> Tuple[str, Dict[str, Any]]:
        """
        Execute Safari extraction with appropriate site-specific extractor.
        
        Args:
            url (str): Target URL to extract
            
        Returns:
            Tuple[str, Dict]: (html_content, metadata)
        """
        self.logger.info(f"Starting Safari extraction for: {url}")
        
        # Record start time for duration calculation
        start_time = time.time()
        
        # Initialize metadata
        metadata = {
            'url': url,
            'method': 'safari',
            'extractor': None,
            'success': False,
            'error': None,
            'extraction_time': start_time
        }
        
        try:
            # Get site configuration
            site_config = get_site_config(url)
            timeout = site_config.get('timeout', 60) if site_config else 60
            wait_time = site_config.get('wait_time', 3) if site_config else 3
            
            self.logger.info(f"Using timeout: {timeout}s, wait_time: {wait_time}s")
            
            # Get appropriate extractor
            extractor = get_extractor_for_site(url)
            metadata['extractor'] = extractor.__class__.__name__
            
            self.logger.info(f"Using extractor: {metadata['extractor']}")
            
            # Execute extraction
            success, content, extractor_metadata = extractor.extract(
                timeout=timeout, 
                wait_time=wait_time
            )
            
            # Merge metadata
            metadata.update(extractor_metadata)
            metadata['success'] = success
            
            if success:
                self.logger.info(f"Safari extraction successful: {len(content)} characters")
                
                # Mark content as Safari-extracted for webfetcher
                if hasattr(content, '__class__'):
                    # Create a string subclass to add metadata
                    class SafariExtractedContent(str):
                        def __new__(cls, value):
                            obj = str.__new__(cls, value)
                            obj.__safari_extracted__ = True
                            obj.__safari_metadata__ = metadata
                            return obj
                    
                    content = SafariExtractedContent(content)
                else:
                    # Fallback: add marker in HTML comment
                    content = f"<!-- Safari-extracted by {metadata['extractor']} -->\n{content}"
                
                return content, metadata
            else:
                self.logger.error(f"Safari extraction failed: {content}")
                metadata['error'] = content
                raise Exception(f"Safari extraction failed: {content}")
                
        except Exception as e:
            self.logger.error(f"Safari extraction error for {url}: {e}")
            metadata['error'] = str(e)
            metadata['success'] = False
            raise
        
        finally:
            # Calculate duration - use start_time which is always available
            metadata['duration'] = time.time() - start_time
            self.logger.info(f"Safari extraction completed in {metadata['duration']:.2f}s")
    
    def extract_and_convert_to_webfetcher_format(self, url: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract content and convert to webfetcher-compatible format.
        
        This method provides a bridge between Safari extraction results
        and the expected webfetcher format.
        
        Args:
            url (str): Target URL
            
        Returns:
            Tuple[str, Dict]: (content, metadata) in webfetcher format
        """
        try:
            content, metadata = self.fetch_with_safari(url)
            
            # Convert metadata to webfetcher format
            webfetcher_metadata = {
                'primary_method': 'safari',
                'fallback_method': None,
                'total_attempts': 1,
                'fetch_duration': metadata.get('duration', 0),
                'render_duration': 0,
                'ssl_fallback_used': False,
                'final_status': 'success' if metadata.get('success') else 'failed',
                'error_message': metadata.get('error'),
                'safari_extractor': metadata.get('extractor'),
                'safari_metadata': metadata
            }
            
            return content, webfetcher_metadata
            
        except Exception as e:
            # Return error in webfetcher format
            error_metadata = {
                'primary_method': 'safari',
                'fallback_method': None,
                'total_attempts': 1,
                'fetch_duration': 0,
                'render_duration': 0,
                'ssl_fallback_used': False,
                'final_status': 'failed',
                'error_message': str(e),
                'safari_extractor': None,
                'safari_metadata': None
            }
            
            raise Exception(f"Safari extraction failed: {e}")

def create_safari_extractor() -> Optional[SafariExtractor]:
    """
    Factory function to create Safari extractor if available.
    
    Returns:
        Optional[SafariExtractor]: Extractor instance or None if not available
    """
    if not SAFARI_ENABLED:
        return None
    
    try:
        extractor = SafariExtractor()
        if extractor.is_safari_available():
            return extractor
        return None
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to create Safari extractor: {e}")
        return None

# Integration helpers for webfetcher.py
def should_fallback_to_safari(url: str, html_content: str = "", 
                             error: Optional[Exception] = None) -> bool:
    """
    Helper function for webfetcher.py to determine Safari fallback.
    
    Args:
        url (str): Target URL
        html_content (str): HTML content from failed request
        error (Exception): Error from failed request
        
    Returns:
        bool: True if should fallback to Safari
    """
    if not SAFARI_ENABLED:
        return False
    
    extractor = create_safari_extractor()
    if not extractor:
        return False
    
    return extractor.should_use_safari(url, html_content, error)

def extract_with_safari_fallback(url: str) -> Tuple[str, Dict[str, Any]]:
    """
    Helper function for webfetcher.py Safari fallback extraction.
    
    Args:
        url (str): Target URL
        
    Returns:
        Tuple[str, Dict]: (content, metadata) in webfetcher format
    """
    extractor = create_safari_extractor()
    if not extractor:
        raise Exception("Safari extractor not available")
    
    return extractor.extract_and_convert_to_webfetcher_format(url)

# Module testing
if __name__ == "__main__":
    import logging
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test URLs
    test_urls = [
        "https://www.ccdi.gov.cn/yaowenn/202509/t20250918_448431.html",
        "https://www.qcc.com/firm/test123"
    ]
    
    extractor = SafariExtractor()
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Testing Safari extraction for: {url}")
        print(f"{'='*60}")
        
        try:
            # Test should_use_safari logic
            should_use = extractor.should_use_safari(
                url, 
                html_content="<html><body>seccaptcha detected</body></html>"
            )
            print(f"Should use Safari: {should_use}")
            
            if should_use and extractor.is_safari_available():
                print("Running actual extraction...")
                content, metadata = extractor.fetch_with_safari(url)
                print(f"Extraction result: Success={metadata.get('success')}")
                print(f"Content length: {len(content)}")
                print(f"Extractor used: {metadata.get('extractor')}")
            else:
                print("Skipping extraction (Safari not available or not needed)")
                
        except Exception as e:
            print(f"Test failed: {e}")
    
    print(f"\n{'='*60}")
    print("Safari extractor testing completed")
    print(f"{'='*60}")