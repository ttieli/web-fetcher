"""HTTP Fetcher Plugin - wraps the existing HTTP fetch logic from webfetcher.py."""

import logging
import time
import urllib.error
from typing import Optional, List

from .base import BaseFetcherPlugin, FetchContext, FetchResult, FetchPriority
from .domain_config import get_domain_priority_override, should_use_safari_for_domain


logger = logging.getLogger(__name__)


class HTTPFetcherPlugin(BaseFetcherPlugin):
    """Plugin that handles HTTP(S) requests using urllib and curl fallback."""
    
    def __init__(self):
        super().__init__("http_fetcher", FetchPriority.HIGH)
    
    def get_effective_priority(self, url: str) -> FetchPriority:
        """
        Get the effective priority for this plugin based on the URL.
        
        For domains that prefer Safari, HTTP priority might be reduced.
        
        Args:
            url: The URL being fetched
            
        Returns:
            Effective priority value
        """
        # Check if domain has specific Safari requirements
        if should_use_safari_for_domain(url):
            logger.debug(f"HTTP plugin priority reduced for Safari-preferred domain in {url}")
            return FetchPriority.NORMAL  # Reduce priority for Safari-preferred domains
        
        # Check if domain has specific HTTP boost
        priority_override = get_domain_priority_override(url, self.name)
        if priority_override is not None:
            logger.debug(f"HTTP plugin priority boosted to {priority_override} for domain in {url}")
            return priority_override
        
        # Return base priority
        return self.priority
    
    def can_handle(self, context: FetchContext) -> bool:
        """Can handle any HTTP or HTTPS URL."""
        url = context.url.lower()
        return url.startswith('http://') or url.startswith('https://')
    
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities."""
        return ["http", "https", "ssl_fallback", "retry_logic", "curl_fallback"]
    
    def fetch(self, context: FetchContext) -> FetchResult:
        """Fetch content using HTTP methods."""
        start_time = time.time()
        
        try:
            # Import webfetcher functions (import here to avoid circular dependency)
            from webfetcher import (
                fetch_html_original, 
                should_retry_exception,
                calculate_backoff_delay,
                FetchMetrics
            )
            
            # Constants from webfetcher
            MAX_RETRIES = 3
            
            last_exception = None
            total_attempts = 0
            
            # Retry loop similar to fetch_html_with_retry but without Safari logic
            for attempt in range(MAX_RETRIES + 1):  # 0, 1, 2, 3 (4 total attempts)
                total_attempts = attempt + 1
                
                try:
                    if attempt > 0:
                        delay = calculate_backoff_delay(attempt - 1)
                        logger.info(f"HTTP retry attempt {attempt}/{MAX_RETRIES} for {context.url} after {delay:.1f}s delay")
                        time.sleep(delay)
                    
                    # Call the original fetch_html function
                    html, fetch_metrics = fetch_html_original(context.url, context.user_agent, context.timeout)
                    
                    duration = time.time() - start_time
                    
                    return FetchResult(
                        success=True,
                        html_content=html,
                        fetch_method=f"http_urllib{'_ssl_fallback' if fetch_metrics.ssl_fallback_used else ''}",
                        attempts=total_attempts,
                        duration=duration,
                        final_url=context.url,
                        metadata={
                            'ssl_fallback_used': fetch_metrics.ssl_fallback_used,
                            'fallback_method': fetch_metrics.fallback_method
                        }
                    )
                    
                except Exception as e:
                    last_exception = e
                    
                    # Log the error with context
                    if attempt == 0:
                        logger.warning(f"HTTP initial fetch failed for {context.url}: {type(e).__name__}: {e}")
                    else:
                        logger.warning(f"HTTP retry {attempt}/{MAX_RETRIES} failed for {context.url}: {type(e).__name__}: {e}")
                    
                    # Check if we should retry this exception
                    if not should_retry_exception(e):
                        logger.info(f"Non-retryable HTTP error for {context.url}, failing immediately: {type(e).__name__}")
                        break
                    
                    # If this was the last attempt, don't sleep
                    if attempt == MAX_RETRIES:
                        break
            
            # All retry attempts exhausted
            duration = time.time() - start_time
            logger.error(f"All {MAX_RETRIES + 1} HTTP attempts failed for {context.url}, giving up")
            
            return FetchResult(
                success=False,
                error_message=f"HTTP fetch failed after {total_attempts} attempts: {str(last_exception)}",
                fetch_method="http_failed",
                attempts=total_attempts,
                duration=duration,
                metadata={'last_exception_type': type(last_exception).__name__}
            )
            
        except ImportError as e:
            return FetchResult(
                success=False,
                error_message=f"HTTP fetcher dependencies not available: {e}",
                fetch_method="http_import_error",
                attempts=0,
                duration=time.time() - start_time
            )
        except Exception as e:
            return FetchResult(
                success=False,
                error_message=f"HTTP fetcher unexpected error: {e}",
                fetch_method="http_error",
                attempts=0,
                duration=time.time() - start_time
            )
    
    def is_available(self) -> bool:
        """Check if HTTP fetching is available."""
        try:
            # Test if we can import the required functions
            from webfetcher import fetch_html_original
            return True
        except ImportError:
            return False