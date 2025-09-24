#!/usr/bin/env python3
"""
Safari Fallback Wrapper for WebFetcher
======================================

Non-intrusive integration layer that adds Safari extraction as an intelligent
fallback mechanism when urllib fails, without modifying core webfetcher files.

This wrapper uses monkey patching to enhance the fetch_html_with_retry function
with Safari-based extraction capabilities for bypassing CAPTCHA and anti-bot measures.

Author: Archy-Principle-Architect
Version: 1.0
Date: 2025-09-23
"""

import os
import sys
import logging
import time
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass

# Configure module paths
SCRIPT_DIR = Path(__file__).parent
WEBFETCHER_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(WEBFETCHER_DIR))

# Import webfetcher BEFORE any modifications
import webfetcher

# Import Safari extractor
from ccdi_production_extractor import CCDIProductionExtractor

# Store original functions for fallback
_original_fetch_html_with_retry = webfetcher.fetch_html_with_retry
_original_fetch_html_original = webfetcher.fetch_html_original

# Configuration from environment
SAFARI_ENABLED = os.environ.get('WF_ENABLE_SAFARI_FALLBACK', '1') == '1'
SAFARI_TIMEOUT = int(os.environ.get('WF_SAFARI_TIMEOUT', '60'))
MIN_CONTENT_LENGTH = int(os.environ.get('WF_MIN_CONTENT_LENGTH', '1000'))
SAFARI_GOV_ONLY = os.environ.get('WF_SAFARI_GOV_ONLY', '0') == '1'

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('safari_fallback')


class EnhancedCCDIExtractor(CCDIProductionExtractor):
    """Enhanced version that can return raw HTML for integration."""
    
    def extract_html_only(self) -> Tuple[bool, Optional[str]]:
        """
        Lightweight extraction for HTML content only (for integration).
        
        Returns:
            Tuple[bool, Optional[str]]: (success, html_content)
        """
        try:
            # Step 1: Check Safari availability
            if not self.check_safari_availability():
                return False, None
            
            # Step 2: Navigate to URL
            if not self.navigate_to_url():
                return False, None
            
            # Step 3: Wait for page load
            if not self.wait_for_page_load(timeout=SAFARI_TIMEOUT):
                self.logger.warning("Page load timeout - proceeding anyway")
            
            # Step 4: Additional wait for dynamic content
            self.logger.info("Waiting for dynamic content...")
            time.sleep(5)
            
            # Step 5: Extract HTML
            html_content = self.extract_html_content()
            if not html_content:
                return False, None
            
            # Store for later use if needed
            self.last_html_content = html_content
            
            # Step 6: Quick validation
            validation = self.validate_content_quality(html_content)
            if validation['has_captcha']:
                self.logger.info("CAPTCHA detected but Safari may have bypassed it")
            
            return True, html_content
            
        except Exception as e:
            self.logger.error(f"HTML extraction failed: {e}")
            return False, None


def should_use_safari_fallback(
    exception: Optional[Exception] = None,
    url: str = "",
    html_content: Optional[str] = None,
    metrics: Optional[Any] = None
) -> bool:
    """
    Determine if Safari fallback should be triggered.
    
    Trigger conditions:
    1. CAPTCHA/bot detection in error or content
    2. HTTP 403/503 errors (common bot detection)
    3. Empty or insufficient content (<MIN_CONTENT_LENGTH chars)
    4. Government sites with fetch failures (if not GOV_ONLY mode)
    5. Specific error patterns indicating blocking
    """
    if not SAFARI_ENABLED:
        return False
    
    # If GOV_ONLY mode, check if government site
    if SAFARI_GOV_ONLY:
        gov_patterns = ['.gov.cn', '.gov', '.govt', '.gob', '.gouv']
        if not any(pattern in url.lower() for pattern in gov_patterns):
            logger.debug(f"Skipping Safari fallback for non-government site: {url}")
            return False
    
    # Check for CAPTCHA/bot detection indicators
    captcha_indicators = [
        'seccaptcha', 'captcha', '验证码', '滑动验证',
        'security check', 'robot', 'bot detection',
        'cloudflare', 'cf-ray', 'challenge-form',
        'access denied', 'forbidden', 'blocked'
    ]
    
    # Check exception for indicators
    if exception:
        error_str = str(exception).lower()
        for indicator in captcha_indicators:
            if indicator in error_str:
                logger.info(f"Safari fallback triggered by error indicator: {indicator}")
                return True
        
        # Check specific HTTP error codes
        if hasattr(exception, 'status'):
            if exception.status in [403, 503, 429]:  # Forbidden, Service Unavailable, Too Many Requests
                logger.info(f"Safari fallback triggered by HTTP {exception.status}")
                return True
    
    # Check HTML content quality
    if html_content is not None:
        # Check for insufficient content
        if len(html_content) < MIN_CONTENT_LENGTH:
            logger.info(f"Safari fallback triggered by short content: {len(html_content)} chars")
            return True
        
        # Check for CAPTCHA in content
        content_lower = html_content.lower()
        for indicator in captcha_indicators:
            if indicator in content_lower:
                logger.info(f"Safari fallback triggered by content indicator: {indicator}")
                return True
        
        # Check for common error pages
        error_patterns = [
            '<title>404', '<title>403', '<title>503',
            'page not found', 'access denied', 'service unavailable'
        ]
        for pattern in error_patterns:
            if pattern in content_lower:
                logger.info(f"Safari fallback triggered by error pattern: {pattern}")
                return True
    
    # Check if government site and any failure occurred
    if exception and '.gov' in url.lower():
        logger.info("Safari fallback triggered for government site with failure")
        return True
    
    return False


def safari_extraction_fallback(url: str) -> Tuple[str, 'webfetcher.FetchMetrics']:
    """
    Perform Safari-based extraction as fallback.
    
    Args:
        url: Target URL to extract
        
    Returns:
        Tuple[str, FetchMetrics]: (html_content, metrics)
    """
    logger.info(f"Initiating Safari fallback extraction for: {url}")
    
    # Create metrics object
    metrics = webfetcher.FetchMetrics()
    metrics.primary_method = "safari"
    start_time = time.time()
    
    try:
        # Use temporary directory for Safari extractor output
        output_dir = Path("/tmp") / "safari_fallback"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create enhanced extractor
        extractor = EnhancedCCDIExtractor(url, str(output_dir))
        
        # Extract HTML only (not full article processing)
        success, html_content = extractor.extract_html_only()
        
        if success and html_content:
            metrics.fetch_duration = time.time() - start_time
            metrics.final_status = "success"
            metrics.fallback_method = "safari_applescript"
            logger.info(f"Safari extraction successful: {len(html_content)} chars in {metrics.fetch_duration:.2f}s")
            return html_content, metrics
        else:
            error_msg = "Safari extraction returned no content"
            metrics.final_status = "failed"
            metrics.error_message = error_msg
            logger.error(error_msg)
            raise Exception(error_msg)
            
    except Exception as e:
        metrics.fetch_duration = time.time() - start_time
        metrics.final_status = "failed"
        metrics.error_message = str(e)
        logger.error(f"Safari extraction failed: {e}")
        raise


def enhanced_fetch_html_with_retry(
    url: str,
    ua: Optional[str] = None,
    timeout: int = 30
) -> Tuple[str, 'webfetcher.FetchMetrics']:
    """
    Enhanced fetch with Safari fallback integration.
    
    This function wraps the original fetch_html_with_retry to add
    Safari-based fallback for CAPTCHA and bot detection scenarios.
    """
    logger.debug(f"Enhanced fetch initiated for: {url}")
    
    try:
        # Try original fetch chain first
        html, metrics = _original_fetch_html_with_retry(url, ua, timeout)
        
        # Validate content quality
        if should_use_safari_fallback(None, url, html, metrics):
            logger.info("Content validation suggests Safari fallback needed")
            try:
                # Try Safari extraction
                html_safari, metrics_safari = safari_extraction_fallback(url)
                
                # Update metrics to show Safari was used
                metrics_safari.primary_method = metrics.primary_method
                metrics_safari.fallback_method = "safari"
                
                return html_safari, metrics_safari
                
            except Exception as safari_error:
                logger.warning(f"Safari fallback failed, returning original: {safari_error}")
                # Return original content if Safari fails
                return html, metrics
        
        # Content is valid, return as-is
        return html, metrics
        
    except Exception as e:
        logger.warning(f"Primary fetch failed with {type(e).__name__}: {e}")
        
        # Check if we should try Safari fallback
        if should_use_safari_fallback(e, url):
            logger.info("Error analysis suggests Safari fallback needed")
            try:
                # Try Safari extraction
                return safari_extraction_fallback(url)
                
            except Exception as safari_error:
                logger.error(f"Safari fallback also failed: {safari_error}")
                # Re-raise original error if Safari also fails
                raise e
        else:
            # Not eligible for Safari fallback, re-raise
            logger.debug("Error not eligible for Safari fallback")
            raise


def install_safari_fallback():
    """
    Install the Safari fallback enhancement into webfetcher.
    
    This function monkey-patches the webfetcher module to add
    Safari extraction capabilities without modifying the original files.
    """
    if not SAFARI_ENABLED:
        logger.info("Safari fallback is disabled via environment variable")
        return
    
    logger.info("Installing Safari fallback enhancement")
    
    # Check platform compatibility
    import platform
    if platform.system() != 'Darwin':
        logger.warning("Safari fallback only available on macOS, skipping installation")
        return
    
    # Monkey patch the fetch functions
    webfetcher.fetch_html_with_retry = enhanced_fetch_html_with_retry
    webfetcher.fetch_html = enhanced_fetch_html_with_retry  # Also patch the alias
    
    logger.info("Safari fallback enhancement installed successfully")
    
    # Log configuration
    logger.info(f"Configuration: ENABLED={SAFARI_ENABLED}, TIMEOUT={SAFARI_TIMEOUT}s, "
                f"MIN_CONTENT={MIN_CONTENT_LENGTH}, GOV_ONLY={SAFARI_GOV_ONLY}")


def main():
    """
    Main entry point when used as a standalone wrapper.
    
    This allows the wrapper to be used as a drop-in replacement for webfetcher.
    """
    # Install Safari fallback
    install_safari_fallback()
    
    # Run original webfetcher main
    return webfetcher.main()


if __name__ == "__main__":
    sys.exit(main())