#!/usr/bin/env python3
"""
Safari Extraction Module for Web_Fetcher
=========================================

This module provides Safari-based content extraction as a fallback mechanism
when standard HTTP fetching fails due to CAPTCHA or anti-bot measures.

The module integrates with Web_Fetcher's existing architecture while maintaining
complete backward compatibility through feature flags and minimal core changes.

Author: Web_Fetcher Team
Version: 1.0
Date: 2025-09-23
"""

import os
import sys
import logging
import time
from typing import Optional, Tuple, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass, field

# Import configuration
from plugins.safari.config import (
    SAFARI_ENABLED, 
    SAFARI_SITES, 
    CAPTCHA_INDICATORS,
    SAFARI_TIMEOUT
)

# Import site-specific extractors
from extractors import get_extractor_for_site

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class SafariExtractionResult:
    """Container for Safari extraction results"""
    success: bool
    html_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    extraction_time: float = 0.0
    extractor_used: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        """Check if extraction result is valid for use"""
        return (
            self.success and 
            self.html_content and 
            len(self.html_content) >= MIN_CONTENT_LENGTH
        )


class SafariExtractor:
    """
    Main Safari extraction coordinator for Web_Fetcher.
    
    This class manages the detection, routing, and execution of Safari-based
    content extraction when standard HTTP methods fail.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Safari extractor with optional configuration.
        
        Args:
            config: Optional configuration override dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.enabled = self.config.get('enabled', SAFARI_ENABLED)
        self._validate_environment()
    
    def _validate_environment(self) -> None:
        """Validate that Safari extraction can work in current environment"""
        if not self.enabled:
            self.logger.info("Safari extraction is disabled")
            return
            
        # Check platform
        import platform
        if platform.system() != 'Darwin':
            self.logger.warning("Safari extraction only works on macOS")
            self.enabled = False
            return
            
        # Check Safari availability (basic check)
        try:
            import subprocess
            result = subprocess.run(
                ['osascript', '-e', 'tell application "Safari" to name'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                self.logger.warning("Safari not available or permissions not granted")
                self.enabled = False
        except Exception as e:
            self.logger.warning(f"Cannot verify Safari availability: {e}")
            self.enabled = False
    
    def should_use_safari(
        self,
        url: str,
        html_content: str = "",
        error: Optional[Exception] = None,
        fetch_metrics: Optional[Any] = None
    ) -> bool:
        """
        Determine if Safari extraction should be used for this request.
        
        Decision factors:
        1. Safari extraction is enabled
        2. URL matches configured sites OR
        3. CAPTCHA/bot detection indicators present OR
        4. Content is insufficient/invalid OR
        5. Specific errors indicate blocking
        
        Args:
            url: The URL being fetched
            html_content: HTML content from standard fetch (if any)
            error: Exception from standard fetch (if any)
            fetch_metrics: Metrics from standard fetch attempt
            
        Returns:
            bool: True if Safari extraction should be attempted
        """
        if not self.enabled:
            return False
            
        # Check if URL is in configured sites
        for site_pattern, site_config in SAFARI_SITES.items():
            if site_pattern in url and site_config.get('enabled', True):
                self.logger.info(f"URL matches configured Safari site: {site_pattern}")
                return True
        
        # Check for CAPTCHA/bot detection indicators
        if html_content:
            content_lower = html_content.lower()
            for indicator in CAPTCHA_INDICATORS:
                if indicator.lower() in content_lower:
                    self.logger.info(f"CAPTCHA indicator detected: {indicator}")
                    return True
            
            # Check content quality
            if len(html_content.strip()) < MIN_CONTENT_LENGTH:
                self.logger.info(f"Content too short ({len(html_content)} bytes)")
                return True
        
        # Check error conditions
        if error:
            error_str = str(error).lower()
            error_indicators = ['403', '429', '503', 'forbidden', 'blocked', 'captcha']
            for indicator in error_indicators:
                if indicator in error_str:
                    self.logger.info(f"Error indicates blocking: {indicator}")
                    return True
        
        return False
    
    def fetch_with_safari(
        self,
        url: str,
        timeout: Optional[int] = None,
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Fetch content using Safari browser automation.
        
        This method:
        1. Identifies appropriate site-specific extractor
        2. Executes Safari-based extraction
        3. Validates and converts results
        4. Returns in Web_Fetcher expected format
        
        Args:
            url: URL to fetch
            timeout: Optional timeout override
            **kwargs: Additional parameters for extractors
            
        Returns:
            Tuple of (html_content, metadata_dict)
            
        Raises:
            Exception: If extraction fails completely
        """
        start_time = time.time()
        timeout = timeout or SAFARI_TIMEOUT
        
        self.logger.info(f"Starting Safari extraction for: {url}")
        
        # Get appropriate extractor
        extractor = get_extractor_for_site(url)
        if not extractor:
            self.logger.warning("No extractor found for URL, using generic")
            from extractors.generic_extractor import GenericExtractor
            extractor = GenericExtractor()
        
        self.logger.info(f"Using extractor: {extractor.__class__.__name__}")
        
        try:
            # Execute extraction
            result = extractor.extract(url, timeout=timeout, **kwargs)
            
            # Validate result
            if not result.success:
                raise Exception(f"Extraction failed: {result.error_message}")
            
            if not result.html_content:
                raise Exception("No content extracted")
                
            # Add Safari marker to content
            marked_html = self._mark_safari_content(result.html_content)
            
            # Prepare metadata
            metadata = {
                'safari_extracted': True,
                'extractor': extractor.__class__.__name__,
                'extraction_time': time.time() - start_time,
                'url': url,
                **result.metadata
            }
            
            self.logger.info(
                f"Safari extraction successful in {metadata['extraction_time']:.2f}s"
            )
            
            return marked_html, metadata
            
        except Exception as e:
            self.logger.error(f"Safari extraction failed: {e}")
            # Re-raise to trigger standard error handling
            raise
        
        finally:
            # Cleanup
            try:
                extractor.cleanup()
            except:
                pass
    
    def _mark_safari_content(self, html: str) -> str:
        """
        Mark HTML content as Safari-extracted for downstream processing.
        
        Args:
            html: Original HTML content
            
        Returns:
            HTML with Safari extraction marker
        """
        # Add invisible marker that can be detected by parser
        marker = "<!-- __safari_extracted__ -->\n"
        return marker + html
    
    def validate_extraction(
        self,
        html_content: str,
        url: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate extracted content quality.
        
        Args:
            html_content: Extracted HTML
            url: Original URL
            
        Returns:
            Tuple of (is_valid, warnings_list)
        """
        warnings = []
        
        # Check content length
        if len(html_content) < MIN_CONTENT_LENGTH:
            warnings.append(f"Content shorter than minimum ({len(html_content)} bytes)")
        
        # Check for remaining CAPTCHA indicators
        content_lower = html_content.lower()
        for indicator in ['captcha', 'security check', '验证码']:
            if indicator in content_lower:
                warnings.append(f"Possible remaining CAPTCHA: {indicator}")
        
        # Check for error pages
        error_indicators = ['404', '403', '500', 'not found', 'access denied']
        for indicator in error_indicators:
            if indicator in content_lower[:1000]:  # Check first 1000 chars
                warnings.append(f"Possible error page: {indicator}")
        
        # Determine overall validity
        is_valid = len(warnings) == 0 or (
            len(warnings) == 1 and 'shorter than minimum' in warnings[0]
        )
        
        return is_valid, warnings
    
    def get_extraction_metrics(self) -> Dict[str, Any]:
        """
        Get current extraction metrics for monitoring.
        
        Returns:
            Dictionary of metrics
        """
        # This would connect to actual metrics collection in production
        return {
            'enabled': self.enabled,
            'total_extractions': 0,  # Would track actual count
            'success_rate': 0.0,     # Would calculate from history
            'average_time': 0.0,     # Would track timing
            'sites_configured': len(SAFARI_SITES)
        }


def create_safari_extractor(**config) -> SafariExtractor:
    """
    Factory function to create Safari extractor instance.
    
    Args:
        **config: Configuration parameters
        
    Returns:
        Configured SafariExtractor instance
    """
    return SafariExtractor(config)


# Integration helper for webfetcher.py
def should_use_safari_fallback(
    url: str,
    html: str = "",
    error: Exception = None,
    metrics: Any = None
) -> bool:
    """
    Helper function for webfetcher integration.
    
    This function can be called from webfetcher.py to determine
    if Safari fallback should be used.
    
    Args:
        url: Target URL
        html: HTML from standard fetch (if any)
        error: Error from standard fetch (if any)
        metrics: Fetch metrics object
        
    Returns:
        bool: True if Safari should be used
    """
    if not SAFARI_ENABLED:
        return False
        
    extractor = SafariExtractor()
    return extractor.should_use_safari(url, html, error, metrics)


def fetch_with_safari_fallback(
    url: str,
    **kwargs
) -> Tuple[str, Dict[str, Any]]:
    """
    Helper function for webfetcher integration.
    
    This function can be called from webfetcher.py to execute
    Safari-based extraction.
    
    Args:
        url: Target URL
        **kwargs: Additional parameters
        
    Returns:
        Tuple of (html_content, metadata)
    """
    extractor = SafariExtractor()
    return extractor.fetch_with_safari(url, **kwargs)


def main():
    """CLI interface for testing Safari extraction"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Safari Extraction Module for Web_Fetcher'
    )
    parser.add_argument('url', nargs='?', help='URL to extract')
    parser.add_argument('--test', action='store_true', help='Run tests')
    parser.add_argument('--validate-env', action='store_true', 
                       help='Validate Safari environment')
    parser.add_argument('--metrics', action='store_true',
                       help='Show extraction metrics')
    
    args = parser.parse_args()
    
    # Configure logging for CLI
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if args.validate_env:
        extractor = SafariExtractor()
        if extractor.enabled:
            print("✓ Safari extraction environment is ready")
        else:
            print("✗ Safari extraction is not available")
        return
    
    if args.metrics:
        extractor = SafariExtractor()
        metrics = extractor.get_extraction_metrics()
        for key, value in metrics.items():
            print(f"{key}: {value}")
        return
    
    if args.test:
        # Run basic tests
        print("Running Safari extraction tests...")
        test_urls = [
            "https://www.ccdi.gov.cn/yaowen/202509/t20250920_123456.html",
            "https://www.qcc.com/firm/1234567890.html"
        ]
        
        extractor = SafariExtractor()
        for test_url in test_urls:
            print(f"\nTesting: {test_url}")
            should_use = extractor.should_use_safari(test_url)
            print(f"Should use Safari: {should_use}")
        return
    
    if args.url:
        # Extract specific URL
        print(f"Extracting: {args.url}")
        extractor = SafariExtractor()
        
        try:
            html, metadata = extractor.fetch_with_safari(args.url)
            print(f"\n✓ Extraction successful")
            print(f"Content length: {len(html)} bytes")
            print(f"Extraction time: {metadata.get('extraction_time', 0):.2f}s")
            print(f"Extractor used: {metadata.get('extractor', 'unknown')}")
            
            # Validate
            is_valid, warnings = extractor.validate_extraction(html, args.url)
            if is_valid:
                print("✓ Content validation passed")
            else:
                print("⚠ Content validation warnings:")
                for warning in warnings:
                    print(f"  - {warning}")
                    
        except Exception as e:
            print(f"\n✗ Extraction failed: {e}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()