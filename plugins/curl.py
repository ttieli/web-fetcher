"""Curl fetcher plugin for handling SSL-problematic sites."""

import subprocess
import logging
import time
from typing import Optional
from .base import BaseFetcherPlugin, FetchContext, FetchResult, FetchPriority

logger = logging.getLogger(__name__)


class CurlFetcherPlugin(BaseFetcherPlugin):
    """Plugin that uses curl command-line tool for fetching, particularly useful for SSL-problematic sites."""
    
    def __init__(self):
        super().__init__("curl_fetcher", FetchPriority.MEDIUM)
    
    def can_handle(self, context: FetchContext) -> bool:
        """
        Can handle any HTTP/HTTPS URL.
        This plugin is primarily used as a fallback for SSL issues.
        """
        url = context.url.lower()
        return url.startswith('http://') or url.startswith('https://')
    
    def is_available(self) -> bool:
        """Check if curl command is available on the system."""
        try:
            result = subprocess.run(['curl', '--version'], 
                                  capture_output=True, 
                                  timeout=5)
            return result.returncode == 0
        except Exception:
            return False
    
    def get_capabilities(self) -> list[str]:
        """Return list of capabilities."""
        return ["ssl_bypass", "redirect_follow", "compression", "custom_headers"]
    
    def fetch(self, context: FetchContext) -> FetchResult:
        """
        Fetch content using curl command.
        Based on fetch_html_with_curl_metrics from webfetcher.py.
        """
        start_time = time.time()
        attempts = 1
        
        try:
            # Import validation and decoding functions from webfetcher
            from webfetcher import validate_and_encode_url, smart_decode
        except ImportError as e:
            return self._create_result(
                success=False,
                error_message=f"Cannot import required functions from webfetcher: {e}",
                attempts=attempts
            )
        
        try:
            # Validate and encode URL for safe subprocess execution
            validated_url = validate_and_encode_url(context.url)
            
            # Build curl command
            ua = context.user_agent or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36"
            
            cmd = [
                'curl', '-k', '-s', '-L',  # -k ignores SSL, -s silent, -L follow redirects
                '--max-time', str(context.timeout),
                '-H', f'User-Agent: {ua}',
                '-H', 'Accept-Language: zh-CN,zh;q=0.9',
                '--compressed',  # Accept compressed responses
                validated_url
            ]
            
            # Add custom headers if provided
            if context.additional_headers:
                for key, value in context.additional_headers.items():
                    cmd.extend(['-H', f'{key}: {value}'])
            
            logger.debug(f"Executing curl command for URL: {validated_url}")
            result = subprocess.run(cmd, capture_output=True, text=False, timeout=context.timeout+5)
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                # Use smart decode to handle curl-fetched byte data
                html_content = smart_decode(result.stdout)
                
                fetch_result = self._create_result(
                    success=True,
                    html_content=html_content,
                    attempts=attempts
                )
                fetch_result.duration = duration
                fetch_result.metadata['ssl_fallback_used'] = True
                fetch_result.metadata['fallback_method'] = 'curl'
                
                return fetch_result
            else:
                # Log curl error details for debugging
                error_msg = f"curl failed with code {result.returncode}"
                if result.stderr:
                    error_msg += f": {result.stderr.decode('utf-8', errors='ignore')}"
                
                logger.error(f"curl failed for {validated_url}: return code {result.returncode}")
                
                fetch_result = self._create_result(
                    success=False,
                    error_message=error_msg,
                    attempts=attempts
                )
                fetch_result.duration = duration
                return fetch_result
                
        except ValueError as e:
            # URL validation error
            duration = time.time() - start_time
            error_msg = f"Invalid URL for curl: {e}"
            logger.error(f"URL validation failed for curl: {e}")
            
            fetch_result = self._create_result(
                success=False,
                error_message=error_msg,
                attempts=attempts
            )
            fetch_result.duration = duration
            return fetch_result
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            error_msg = f"curl timeout for {context.url}"
            logger.error(error_msg)
            
            fetch_result = self._create_result(
                success=False,
                error_message=error_msg,
                attempts=attempts
            )
            fetch_result.duration = duration
            return fetch_result
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Failed to fetch with curl from {context.url}: {e}"
            logger.error(error_msg)
            
            fetch_result = self._create_result(
                success=False,
                error_message=error_msg,
                attempts=attempts
            )
            fetch_result.duration = duration
            return fetch_result