"""Playwright fetcher plugin for JavaScript-rendered web content.

This plugin provides JavaScript rendering capabilities using Playwright,
extracted from the existing webfetcher.py implementation. It maintains
full backward compatibility while providing proper resource management
and error handling within the plugin architecture.
"""

import time
import logging
from typing import Optional, List

from .base import BaseFetcherPlugin, FetchPriority, FetchContext, FetchResult
from .config import get_plugin_config


class PlaywrightFetcherPlugin(BaseFetcherPlugin):
    """Playwright-based fetcher plugin for JavaScript rendering."""
    
    def __init__(self):
        super().__init__(name="playwright", priority=FetchPriority.NORMAL)
        self._config = get_plugin_config("playwright")
    
    def is_available(self) -> bool:
        """Check if Playwright is available for use."""
        try:
            from playwright.sync_api import sync_playwright
            return True
        except ImportError:
            return False
    
    def get_capabilities(self) -> List[str]:
        """Return capabilities provided by this plugin."""
        return [
            "javascript_rendering",
            "dynamic_content",
            "spa_support",
            "scroll_rendering",
            "mobile_viewport"
        ]
    
    def can_handle(self, context: FetchContext) -> bool:
        """
        Determine if this plugin can handle the fetch request.
        
        This plugin can handle any HTTP(S) URL when Playwright is available.
        Priority and specific handling logic is managed by the registry.
        """
        if not self.is_available():
            return False
            
        url_lower = context.url.lower()
        return url_lower.startswith(('http://', 'https://'))
    
    def fetch(self, context: FetchContext) -> FetchResult:
        """
        Fetch web content using Playwright for JavaScript rendering.
        
        This method implements the core Playwright logic extracted from
        webfetcher.py's try_render_with_metrics function, with proper
        resource management and error handling.
        """
        start_time = time.time()
        
        # Check availability first
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            duration = time.time() - start_time
            return FetchResult(
                success=False,
                error_message=f"Playwright not available: {e}",
                fetch_method=self.name,
                attempts=1,
                duration=duration
            )
        
        # Get configuration with defaults
        timeout_ms = self._config.get("timeout_ms", context.timeout * 1000)
        viewport = self._config.get("viewport", {'width': 390, 'height': 844})
        device_scale_factor = self._config.get("device_scale_factor", 3)
        headless = self._config.get("headless", True)
        wait_strategy = self._config.get("wait_strategy", "domcontentloaded")
        scroll_to_bottom = self._config.get("scroll_to_bottom", True)
        scroll_delay = self._config.get("scroll_delay", 800)
        page_load_delay = self._config.get("page_load_delay", 600)
        
        # Use provided user agent or default mobile user agent
        user_agent = (context.user_agent or 
                     self._config.get("default_user_agent",
                                    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"))
        
        html_content = None
        browser = None
        page = None
        
        try:
            with sync_playwright() as p:
                try:
                    # Launch browser with security flags
                    browser = p.chromium.launch(
                        headless=headless,
                        args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
                    )
                    
                    # Create context with mobile simulation
                    ctx = browser.new_context(
                        user_agent=user_agent,
                        locale=self._config.get("locale", "zh-CN"),
                        viewport=viewport,
                        device_scale_factor=device_scale_factor
                    )
                    
                    page = ctx.new_page()
                    
                    # Set additional headers
                    headers = {'Accept-Language': 'zh-CN,zh;q=0.9'}
                    if context.additional_headers:
                        headers.update(context.additional_headers)
                    page.set_extra_http_headers(headers)
                    
                    # Navigate to page with relaxed waiting strategy
                    page.goto(context.url, wait_until=wait_strategy, timeout=timeout_ms)
                    page.wait_for_load_state('load', timeout=timeout_ms)
                    page.wait_for_timeout(scroll_delay)
                    
                    # Optional scrolling for dynamic content
                    if scroll_to_bottom:
                        try:
                            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                            page.wait_for_timeout(page_load_delay)
                        except Exception as scroll_error:
                            logging.debug(f"Scroll operation failed (non-fatal): {scroll_error}")
                    
                    # Extract content
                    html_content = page.content()
                    
                finally:
                    # Ensure resource cleanup
                    if browser:
                        try:
                            browser.close()
                        except Exception as cleanup_error:
                            logging.warning(f"Failed to cleanup browser: {cleanup_error}")
                
            duration = time.time() - start_time
            return FetchResult(
                success=True,
                html_content=html_content,
                fetch_method=self.name,
                attempts=1,
                duration=duration,
                final_url=page.url if page else context.url,
                metadata={
                    "viewport": viewport,
                    "user_agent": user_agent,
                    "javascript_rendered": True,
                    "scroll_performed": scroll_to_bottom
                }
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return FetchResult(
                success=False,
                error_message=str(e),
                fetch_method=self.name,
                attempts=1,
                duration=duration
            )
    
    def validate_context(self, context: FetchContext) -> bool:
        """Validate context for Playwright fetching."""
        if not super().validate_context(context):
            return False
        
        # Additional validation for Playwright-specific requirements
        url_lower = context.url.lower()
        if not url_lower.startswith(('http://', 'https://')):
            return False
        
        # Check timeout is reasonable (not too small for JS rendering)
        if context.timeout < 5:
            logging.warning("Playwright timeout very low, may cause failures")
        
        return True


# Plugin factory function for registry auto-discovery
def create_plugin() -> PlaywrightFetcherPlugin:
    """Create and return a PlaywrightFetcherPlugin instance."""
    return PlaywrightFetcherPlugin()