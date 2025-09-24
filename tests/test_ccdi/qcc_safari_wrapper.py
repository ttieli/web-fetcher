#!/usr/bin/env python3
"""
QCC-Enhanced Safari Fallback Wrapper for WebFetcher
====================================================

Extended Safari fallback wrapper that includes support for QCC.com websites
along with existing CCDI support. This wrapper enables Safari extraction
for both government sites and business data platforms that implement
anti-scraping measures.

This is a non-intrusive integration that does not modify core webfetcher files.

Supported Sites:
- CCDI (ccdi.gov.cn) - Government anti-corruption site
- QCC (qcc.com) - Business information platform with JavaScript protection

Author: Archy-Principle-Architect
Version: 1.1
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
SAFARI_DYNAMIC_WAIT = int(os.environ.get('WF_SAFARI_DYNAMIC_WAIT', '10'))  # Extended for QCC

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('safari_fallback_qcc')


@dataclass
class SiteConfig:
    """Configuration for specific site extraction"""
    domain_patterns: list
    wait_time: int  # Additional wait time for dynamic content
    content_selectors: list  # CSS selectors to find content
    requires_login_check: bool
    javascript_heavy: bool


# Site-specific configurations
SITE_CONFIGS = {
    'qcc': SiteConfig(
        domain_patterns=['qcc.com', 'news.qcc.com', 'r.qcc.com', 'www.qcc.com'],
        wait_time=10,  # QCC requires longer wait for dynamic content
        content_selectors=[
            'article',
            '[class*="article"]',
            '[class*="news-detail"]',
            '[class*="detail-content"]',
            '[class*="main-content"]',
            '.article-content',
            '.news-content',
            '#article-content',
            'main'
        ],
        requires_login_check=False,
        javascript_heavy=True
    ),
    'ccdi': SiteConfig(
        domain_patterns=['ccdi.gov.cn', '.gov.cn'],
        wait_time=5,
        content_selectors=[
            '.content',
            '[class*="content"]',
            'article',
            '.article',
            'main'
        ],
        requires_login_check=False,
        javascript_heavy=False
    )
}


class EnhancedMultiSiteExtractor(CCDIProductionExtractor):
    """Enhanced extractor supporting multiple sites including QCC"""
    
    def __init__(self, url: str, output_dir: str):
        super().__init__(url, output_dir)
        self.site_config = self._detect_site_config(url)
        if self.site_config:
            self.logger.info(f"Detected site configuration for: {self._get_site_name(url)}")
    
    def _detect_site_config(self, url: str) -> Optional[SiteConfig]:
        """Detect which site configuration to use based on URL"""
        url_lower = url.lower()
        for site_name, config in SITE_CONFIGS.items():
            for pattern in config.domain_patterns:
                if pattern in url_lower:
                    return config
        return None
    
    def _get_site_name(self, url: str) -> str:
        """Get site name from URL"""
        url_lower = url.lower()
        for site_name, config in SITE_CONFIGS.items():
            for pattern in config.domain_patterns:
                if pattern in url_lower:
                    return site_name
        return 'unknown'
    
    def extract_html_only(self) -> Tuple[bool, Optional[str]]:
        """
        Enhanced extraction with site-specific handling
        
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
            timeout = SAFARI_TIMEOUT
            if self.site_config and self.site_config.javascript_heavy:
                timeout = max(timeout, 90)  # Extended timeout for JS-heavy sites
            
            if not self.wait_for_page_load(timeout=timeout):
                self.logger.warning("Page load timeout - proceeding anyway")
            
            # Step 4: Site-specific dynamic content wait
            wait_time = SAFARI_DYNAMIC_WAIT
            if self.site_config:
                wait_time = max(wait_time, self.site_config.wait_time)
            
            self.logger.info(f"Waiting {wait_time}s for dynamic content...")
            time.sleep(wait_time)
            
            # Step 5: Additional wait for QCC dynamic loading
            if self.site_config and 'qcc' in self._get_site_name(self.target_url):
                # Check if article content has loaded
                self.logger.info("Checking for QCC article content...")
                self._wait_for_qcc_content()
            
            # Step 6: Extract HTML
            html_content = self.extract_html_content()
            if not html_content:
                return False, None
            
            # Store for later use if needed
            self.last_html_content = html_content
            
            # Step 7: Validation
            validation = self.validate_content_quality(html_content)
            if validation['has_captcha']:
                self.logger.info("CAPTCHA detected but Safari may have bypassed it")
            
            # Step 8: Check for QCC-specific indicators
            if self.site_config and 'qcc' in self._get_site_name(self.target_url):
                if self._is_qcc_content_loaded(html_content):
                    self.logger.info("QCC article content successfully loaded")
                else:
                    self.logger.warning("QCC page loaded but article content may be incomplete")
            
            return True, html_content
            
        except Exception as e:
            self.logger.error(f"HTML extraction failed: {e}")
            return False, None
    
    def _wait_for_qcc_content(self):
        """Wait for QCC-specific content to load"""
        try:
            # Check for article content multiple times
            for i in range(3):
                check_script = '''
                tell application "Safari"
                    set hasArticle to do JavaScript "
                        var found = false;
                        var selectors = ['article', '.article-content', '.news-detail', '.detail-content'];
                        for (var i = 0; i < selectors.length; i++) {
                            var el = document.querySelector(selectors[i]);
                            if (el && el.textContent.length > 100) {
                                found = true;
                                break;
                            }
                        }
                        found;
                    " in current tab of window 1
                    return hasArticle
                end tell
                '''
                
                import subprocess
                result = subprocess.run(['osascript', '-e', check_script], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0 and result.stdout.strip() == 'true':
                    self.logger.info("QCC article content detected")
                    return
                
                self.logger.info(f"Waiting for QCC content... attempt {i+1}/3")
                time.sleep(5)
                
        except Exception as e:
            self.logger.warning(f"Error checking QCC content: {e}")
    
    def _is_qcc_content_loaded(self, html_content: str) -> bool:
        """Check if QCC article content is present in HTML"""
        # QCC articles should have substantial content beyond navigation
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for article content
        if self.site_config:
            for selector in self.site_config.content_selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    # Article should have more than just navigation text
                    if len(text) > 500 and not text.startswith('缔造有远见'):
                        return True
        
        return False


def should_use_safari_fallback(
    exception: Optional[Exception] = None,
    url: str = "",
    html_content: Optional[str] = None,
    metrics: Optional[Any] = None
) -> bool:
    """
    Enhanced detection including QCC.com patterns
    
    Trigger conditions:
    1. QCC.com domains (known JavaScript protection)
    2. CCDI/government sites with failures
    3. CAPTCHA/bot detection indicators
    4. HTTP 403/503 errors
    5. Empty or insufficient content
    6. JavaScript-heavy obfuscation patterns
    """
    if not SAFARI_ENABLED:
        return False
    
    url_lower = url.lower()
    
    # Priority 1: Known problematic sites
    # QCC.com - Business data platform with heavy JS protection
    qcc_patterns = ['qcc.com', 'news.qcc.com', 'r.qcc.com', 'www.qcc.com']
    for pattern in qcc_patterns:
        if pattern in url_lower:
            logger.info(f"Safari fallback triggered for QCC site: {url}")
            return True
    
    # Government sites
    gov_patterns = ['.gov.cn', '.gov', '.govt', '.gob', '.gouv', 'ccdi.gov.cn']
    is_gov_site = any(pattern in url_lower for pattern in gov_patterns)
    
    # Check for anti-bot indicators
    captcha_indicators = [
        'seccaptcha', 'captcha', '验证码', '滑动验证',
        'security check', 'robot', 'bot detection',
        'cloudflare', 'cf-ray', 'challenge-form',
        'access denied', 'forbidden', 'blocked',
        'acw_sc__v2',  # QCC cookie check
        'aliyun_waf',  # Aliyun WAF protection
        'document.cookie'  # Cookie-based verification
    ]
    
    # JavaScript obfuscation patterns (common in QCC)
    js_obfuscation_patterns = [
        'function()', 'eval(', 'unescape(',
        'String.fromCharCode', 'parseInt(',
        'setTimeout(', 'setInterval(',
        'window.location.reload'
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
            if exception.status in [403, 503, 429]:
                logger.info(f"Safari fallback triggered by HTTP {exception.status}")
                return True
    
    # Check HTML content quality
    if html_content is not None:
        content_lower = html_content.lower()
        
        # Check for insufficient content
        if len(html_content) < MIN_CONTENT_LENGTH:
            logger.info(f"Safari fallback triggered by short content: {len(html_content)} chars")
            return True
        
        # Check for CAPTCHA/protection in content
        for indicator in captcha_indicators:
            if indicator in content_lower:
                logger.info(f"Safari fallback triggered by content indicator: {indicator}")
                return True
        
        # Check for heavy JavaScript obfuscation (QCC pattern)
        obfuscation_count = sum(1 for pattern in js_obfuscation_patterns if pattern in content_lower)
        if obfuscation_count >= 3:
            logger.info(f"Safari fallback triggered by JS obfuscation (found {obfuscation_count} patterns)")
            return True
        
        # Check for QCC-specific protection
        if 'renderdata' in content_lower and 'aliyunwaf' in content_lower:
            logger.info("Safari fallback triggered by QCC WAF protection")
            return True
        
        # Check for error pages
        error_patterns = [
            '<title>404', '<title>403', '<title>503',
            'page not found', 'access denied', 'service unavailable'
        ]
        for pattern in error_patterns:
            if pattern in content_lower:
                logger.info(f"Safari fallback triggered by error pattern: {pattern}")
                return True
    
    # Check if government site with any failure
    if exception and is_gov_site:
        logger.info("Safari fallback triggered for government site with failure")
        return True
    
    return False


def safari_extraction_fallback(url: str) -> Tuple[str, 'webfetcher.FetchMetrics']:
    """
    Perform Safari-based extraction with multi-site support
    
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
        
        # Create enhanced multi-site extractor
        extractor = EnhancedMultiSiteExtractor(url, str(output_dir))
        
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
    Enhanced fetch with Safari fallback for multiple sites
    
    This function wraps the original fetch_html_with_retry to add
    Safari-based fallback for sites with anti-scraping measures.
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
    Install the enhanced Safari fallback with QCC support
    
    This function monkey-patches the webfetcher module to add
    Safari extraction capabilities for multiple sites.
    """
    if not SAFARI_ENABLED:
        logger.info("Safari fallback is disabled via environment variable")
        return
    
    logger.info("Installing enhanced Safari fallback with QCC support")
    
    # Check platform compatibility
    import platform
    if platform.system() != 'Darwin':
        logger.warning("Safari fallback only available on macOS, skipping installation")
        return
    
    # Monkey patch the fetch functions
    webfetcher.fetch_html_with_retry = enhanced_fetch_html_with_retry
    webfetcher.fetch_html = enhanced_fetch_html_with_retry  # Also patch the alias
    
    logger.info("Enhanced Safari fallback installed successfully")
    
    # Log configuration
    logger.info(f"Configuration: ENABLED={SAFARI_ENABLED}, TIMEOUT={SAFARI_TIMEOUT}s, "
                f"MIN_CONTENT={MIN_CONTENT_LENGTH}, DYNAMIC_WAIT={SAFARI_DYNAMIC_WAIT}s")
    logger.info(f"Supported sites: QCC.com, CCDI.gov.cn, and other government sites")


def main():
    """
    Main entry point when used as standalone or wrapper
    
    This allows the wrapper to be used as a drop-in replacement for webfetcher.
    """
    # Install Safari fallback
    install_safari_fallback()
    
    # Run original webfetcher main
    return webfetcher.main()


if __name__ == "__main__":
    sys.exit(main()
    