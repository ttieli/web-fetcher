"""HTTP Fetcher Plugin - Standard HTTP/HTTPS fetching using urllib."""

import logging
import time
import urllib.request
import urllib.error
import ssl
from typing import Optional, List

from .base import BaseFetcherPlugin, FetchContext, FetchResult, FetchPriority

logger = logging.getLogger(__name__)


class HTTPFetcherPlugin(BaseFetcherPlugin):
    """Plugin that handles standard HTTP/HTTPS requests using urllib."""
    
    def __init__(self):
        # HIGH priority - should be tried before Safari
        super().__init__("http_fetcher", FetchPriority.HIGH)
    
    def can_handle(self, context: FetchContext) -> bool:
        """Can handle any HTTP/HTTPS URL."""
        url = context.url.lower()
        return url.startswith('http://') or url.startswith('https://')
    
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities."""
        return [
            "http", 
            "https",
            "basic_auth",
            "headers",
            "cookies"
        ]
    
    def fetch(self, context: FetchContext) -> FetchResult:
        """Fetch content using urllib."""
        start_time = time.time()
        
        try:
            # Create request with user agent
            headers = {'User-Agent': context.user_agent} if context.user_agent else {}
            
            # Add any additional headers from context if available
            if hasattr(context, 'headers') and context.headers:
                headers.update(context.headers)
            
            req = urllib.request.Request(context.url, headers=headers)
            
            # Try to fetch with SSL verification
            try:
                with urllib.request.urlopen(req, timeout=context.timeout) as response:
                    html = response.read()
                    
                    # Try to decode as UTF-8
                    try:
                        html_content = html.decode('utf-8')
                    except UnicodeDecodeError:
                        # Fallback to latin-1 or ignore errors
                        html_content = html.decode('utf-8', errors='ignore')
                    
                    duration = time.time() - start_time
                    
                    return FetchResult(
                        success=True,
                        html_content=html_content,
                        fetch_method="urllib",
                        attempts=1,
                        duration=duration,
                        final_url=response.geturl(),
                        metadata={
                            'status_code': response.getcode(),
                            'headers': dict(response.headers),
                            'content_length': len(html_content),
                            'encoding': response.headers.get('Content-Encoding', 'none')
                        }
                    )
                    
            except urllib.error.HTTPError as e:
                # HTTP errors (4xx, 5xx)
                duration = time.time() - start_time
                
                # Special handling for 403 which might need Safari
                if e.code == 403:
                    logger.info(f"HTTP 403 received for {context.url}")
                    
                return FetchResult(
                    success=False,
                    error_message=f"HTTP {e.code}: {e.reason}",
                    fetch_method="urllib",
                    attempts=1,
                    duration=duration,
                    metadata={
                        'status_code': e.code,
                        'error_type': 'http_error'
                    }
                )
                
            except ssl.SSLError as e:
                # SSL errors - might need curl fallback
                logger.warning(f"SSL error for {context.url}: {e}")
                
                # Try without SSL verification as a last resort
                if context.plugin_config.get('allow_insecure', False):
                    logger.info("Retrying without SSL verification")
                    
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    
                    with urllib.request.urlopen(req, timeout=context.timeout, context=ssl_context) as response:
                        html = response.read()
                        html_content = html.decode('utf-8', errors='ignore')
                        
                        duration = time.time() - start_time
                        
                        return FetchResult(
                            success=True,
                            html_content=html_content,
                            fetch_method="urllib_insecure",
                            attempts=1,
                            duration=duration,
                            final_url=response.geturl(),
                            metadata={
                                'status_code': response.getcode(),
                                'ssl_verification': False,
                                'warning': 'SSL verification disabled'
                            }
                        )
                
                # SSL failed and insecure not allowed
                duration = time.time() - start_time
                return FetchResult(
                    success=False,
                    error_message=f"SSL Error: {str(e)}",
                    fetch_method="urllib",
                    attempts=1,
                    duration=duration,
                    metadata={'error_type': 'ssl_error'}
                )
                
        except Exception as e:
            duration = time.time() - start_time
            logger.warning(f"HTTP fetch failed for {context.url}: {e}")
            
            return FetchResult(
                success=False,
                error_message=str(e),
                fetch_method="urllib",
                attempts=1,
                duration=duration,
                metadata={'error_type': type(e).__name__}
            )
    
    def is_available(self) -> bool:
        """HTTP plugin is always available."""
        return True