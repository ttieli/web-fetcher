"""Safari Fetcher Plugin - wraps Safari automation functionality."""

import logging
import platform
import time
import urllib.error
from typing import Optional, List

from ..base import BaseFetcherPlugin, FetchContext, FetchResult, FetchPriority
from ..domain_config import get_domain_priority_override, should_use_safari_for_domain, get_domain_config


logger = logging.getLogger(__name__)


class SafariFetcherPlugin(BaseFetcherPlugin):
    """Plugin that handles requests using Safari browser automation."""
    
    def __init__(self):
        super().__init__("safari_fetcher", FetchPriority.LOW)
        self._safari_available = self._check_safari_availability()
    
    def _check_safari_availability(self) -> bool:
        """Check if Safari functionality is available."""
        try:
            # Safari only available on macOS
            if platform.system() != "Darwin":
                logger.debug("Safari plugin disabled - not running on macOS")
                return False
            
            # Try to import Safari functions
            from .extractor import should_fallback_to_safari, extract_with_safari_fallback
            logger.debug("Safari plugin dependencies available")
            return True
            
        except ImportError as e:
            logger.debug(f"Safari plugin dependencies not available: {e}")
            return False
    
    def get_effective_priority(self, url: str) -> FetchPriority:
        """
        Get the effective priority for this plugin based on the URL.
        
        Args:
            url: The URL being fetched
            
        Returns:
            Effective priority value, potentially boosted for certain domains
        """
        # Check if domain has specific Safari requirements
        priority_override = get_domain_priority_override(url, self.name)
        if priority_override is not None:
            logger.info(f"Safari plugin priority boosted to {priority_override} for domain in {url}")
            return priority_override
        
        # Return base priority
        return self.priority
    
    def should_handle_domain(self, url: str) -> bool:
        """
        Check if this domain should be handled by Safari based on configuration.
        
        Args:
            url: The URL to check
            
        Returns:
            True if Safari should handle this domain preemptively
        """
        return should_use_safari_for_domain(url)
    
    def can_handle(self, context: FetchContext) -> bool:
        """
        Can handle HTTP/HTTPS URLs, with preference for problematic sites.
        
        Safari is typically used as a fallback or for sites that block regular HTTP clients.
        """
        if not self._safari_available:
            return False
            
        url = context.url.lower()
        if not (url.startswith('http://') or url.startswith('https://')):
            return False
        
        try:
            # Check domain-specific configuration first
            if self.should_handle_domain(context.url):
                logger.info(f"Safari plugin will handle {context.url} due to domain configuration")
                return True
            
            # Check if this URL requires preemptive Safari usage (legacy support)
            from webfetcher import requires_safari_preemptively
            if requires_safari_preemptively(context.url):
                return True
            
            # Also handle if explicitly configured for Safari in plugin config
            if context.plugin_config.get('force_safari', False):
                return True
            
            # Otherwise, Safari can handle any HTTP URL but with lower priority
            # (it will be used as fallback by the registry system)
            return True
            
        except ImportError:
            # If webfetcher functions not available, check domain config
            if self.should_handle_domain(context.url):
                return True
            # Can still handle basic URLs as fallback
            return True
    
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities."""
        return [
            "javascript_rendering", 
            "browser_automation",
            "cookie_support",
            "anti_bot_bypass",
            "dynamic_content"
        ]
    
    def fetch(self, context: FetchContext) -> FetchResult:
        """Fetch content using Safari browser automation."""
        if not self._safari_available:
            return FetchResult(
                success=False,
                error_message="Safari functionality not available",
                fetch_method="safari_unavailable",
                attempts=0
            )
        
        start_time = time.time()
        
        try:
            from .extractor import extract_with_safari_fallback
            
            logger.info(f"Using Safari to fetch: {context.url}")
            
            # Call Safari extractor
            html, safari_metrics = extract_with_safari_fallback(context.url)
            
            duration = time.time() - start_time
            
            if html:
                return FetchResult(
                    success=True,
                    html_content=html,
                    fetch_method="safari_automation",
                    attempts=1,
                    duration=duration,
                    final_url=context.url,
                    metadata={
                        'safari_metrics': safari_metrics if safari_metrics else {},
                        'browser_automation': True
                    }
                )
            else:
                return FetchResult(
                    success=False,
                    error_message="Safari returned empty content",
                    fetch_method="safari_empty",
                    attempts=1,
                    duration=duration
                )
                
        except ImportError as e:
            return FetchResult(
                success=False,
                error_message=f"Safari dependencies not available: {e}",
                fetch_method="safari_import_error",
                attempts=0,
                duration=time.time() - start_time
            )
        except Exception as e:
            duration = time.time() - start_time
            logger.warning(f"Safari fetch failed for {context.url}: {e}")
            return FetchResult(
                success=False,
                error_message=f"Safari automation failed: {str(e)}",
                fetch_method="safari_failed",
                attempts=1,
                duration=duration,
                metadata={'exception_type': type(e).__name__}
            )
    
    def is_available(self) -> bool:
        """Check if Safari plugin is available."""
        return self._safari_available
    
    def should_fallback_to_safari(self, url: str, html_content: str, 
                                 exception: Optional[Exception] = None) -> bool:
        """
        Determine if Safari should be used as a fallback for this request.
        
        Args:
            url: The URL that failed
            html_content: Any HTML content retrieved (may be empty)
            exception: The exception that occurred during fetch
            
        Returns:
            True if Safari should be used as fallback
        """
        if not self._safari_available:
            return False
            
        try:
            from .extractor import should_fallback_to_safari
            return should_fallback_to_safari(url, html_content, exception)
        except ImportError:
            # Basic fallback logic if safari_extractor not available
            if isinstance(exception, urllib.error.HTTPError):
                # Fallback on certain HTTP errors
                return exception.status in [403, 429, 503]
            return False