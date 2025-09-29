"""
Selenium Fetcher for Web_Fetcher

Session-preserving Selenium implementation that connects ONLY to existing Chrome debug instances.
Designed to maintain login states and avoid automation detection.

Architecture: Uses Chrome's debug port (9222) to connect to existing browser sessions
launched by config/chrome-debug.sh, preserving all cookies and login states.

Author: Cody (Claude Code)
Date: 2025-09-29
Version: 1.0 (Phase 1)
"""

import logging
import time
import json
import urllib.request
import urllib.error
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass

# Conditional import for requests with urllib fallback
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logging.debug("requests not available, using urllib.request fallback")

# Conditional imports - graceful degradation when Selenium not available
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        WebDriverException, 
        TimeoutException, 
        NoSuchElementException
    )
    SELENIUM_AVAILABLE = True
except ImportError as e:
    logging.debug(f"Selenium not available: {e}")
    SELENIUM_AVAILABLE = False
    # Create dummy classes to prevent import errors
    class Options: pass
    class WebDriverException(Exception): pass
    class TimeoutException(Exception): pass
    class NoSuchElementException(Exception): pass


class ChromeConnectionError(Exception):
    """Chrome debug connection failed"""
    pass


class SeleniumNotAvailableError(Exception):
    """Selenium dependencies not installed"""
    pass


class SeleniumFetchError(Exception):
    """Selenium fetch operation failed"""
    pass


class SeleniumTimeoutError(Exception):
    """Selenium page load timeout"""
    pass


@dataclass
class SeleniumMetrics:
    """Metrics for Selenium fetch operations"""
    selenium_wait_time: float = 0.0
    chrome_connected: bool = False
    js_detection_used: bool = False
    method: str = "selenium_debug_port"
    connection_time: float = 0.0
    page_load_time: float = 0.0
    error_message: Optional[str] = None
    debug_port: int = 9222
    session_preserved: bool = True


class SeleniumFetcher:
    """
    Session-preserving Selenium fetcher that connects ONLY to existing Chrome debug instances.
    
    Key Features:
    - Connects to existing Chrome debug sessions (port 9222)
    - Preserves all login states and cookies
    - Avoids automation detection
    - Graceful degradation when dependencies unavailable
    - No ChromeDriver management needed
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize SeleniumFetcher with configuration.
        
        Args:
            config: Configuration dictionary (from selenium_config.py)
                   If None, uses default settings
        """
        self.config = config or {}
        self.driver = None
        self._connection_established = False
        
        # Extract configuration values
        chrome_config = self.config.get('chrome', {})
        self.debug_port = chrome_config.get('debug_port', 9222)
        self.debug_host = chrome_config.get('debug_host', 'localhost')
        
        connection_config = self.config.get('connection', {})
        self.max_connection_attempts = connection_config.get('max_connection_attempts', 3)
        self.connection_timeout = connection_config.get('connection_timeout', 10)
        self.preserve_session = connection_config.get('preserve_session', True)
        
        timeouts_config = self.config.get('timeouts', {})
        self.page_load_timeout = timeouts_config.get('page_load', 30)
        self.script_timeout = timeouts_config.get('script', 10)
        self.implicit_wait = timeouts_config.get('implicit_wait', 5)
        self.element_wait_timeout = timeouts_config.get('element_wait', 15)
        
        logging.info(f"SeleniumFetcher initialized - debug port: {self.debug_port}")
    
    def is_available(self) -> bool:
        """
        Check if Selenium dependencies are available.
        
        Returns:
            True if Selenium is installed and importable
        """
        return SELENIUM_AVAILABLE
    
    def is_chrome_debug_available(self) -> bool:
        """
        Check if Chrome debug session is running on configured port.
        
        CRITICAL: This prevents attempting connection to non-existent session.
        Uses Chrome DevTools Protocol to verify session availability.
        
        Returns:
            True if Chrome debug session is responsive
        """
        try:
            debug_url = f"http://{self.debug_host}:{self.debug_port}/json/version"
            
            if REQUESTS_AVAILABLE:
                # Use requests library if available
                response = requests.get(debug_url, timeout=2)
                if response.status_code == 200:
                    version_info = response.json()
                    logging.debug(f"Chrome debug session detected: {version_info.get('Browser', 'Unknown')}")
                    return True
                else:
                    logging.debug(f"Chrome debug port {self.debug_port} not responsive: {response.status_code}")
                    return False
            else:
                # Fallback to urllib.request
                request = urllib.request.Request(debug_url)
                try:
                    with urllib.request.urlopen(request, timeout=2) as response:
                        if response.getcode() == 200:
                            response_data = response.read().decode('utf-8')
                            version_info = json.loads(response_data)
                            logging.debug(f"Chrome debug session detected: {version_info.get('Browser', 'Unknown')}")
                            return True
                        else:
                            logging.debug(f"Chrome debug port {self.debug_port} not responsive: {response.getcode()}")
                            return False
                except urllib.error.URLError as e:
                    logging.debug(f"Chrome debug session check failed (urllib): {e}")
                    return False
                    
        except Exception as e:
            logging.debug(f"Unexpected error checking Chrome debug session: {e}")
            return False
    
    def get_chrome_tabs(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get list of open Chrome tabs from debug session.
        
        Returns:
            List of tab information dictionaries, or None if unavailable
        """
        try:
            if not self.is_chrome_debug_available():
                return None
                
            tabs_url = f"http://{self.debug_host}:{self.debug_port}/json"
            
            if REQUESTS_AVAILABLE:
                # Use requests library if available
                response = requests.get(tabs_url, timeout=2)
                if response.status_code == 200:
                    tabs = response.json()
                    logging.debug(f"Found {len(tabs)} Chrome tabs")
                    return tabs
                else:
                    logging.debug(f"Failed to get Chrome tabs: {response.status_code}")
                    return None
            else:
                # Fallback to urllib.request
                request = urllib.request.Request(tabs_url)
                try:
                    with urllib.request.urlopen(request, timeout=2) as response:
                        if response.getcode() == 200:
                            response_data = response.read().decode('utf-8')
                            tabs = json.loads(response_data)
                            logging.debug(f"Found {len(tabs)} Chrome tabs")
                            return tabs
                        else:
                            logging.debug(f"Failed to get Chrome tabs: {response.getcode()}")
                            return None
                except urllib.error.URLError as e:
                    logging.debug(f"Error getting Chrome tabs (urllib): {e}")
                    return None
                
        except Exception as e:
            logging.debug(f"Error getting Chrome tabs: {e}")
            return None
    
    def connect_to_chrome(self) -> Tuple[bool, str]:
        """
        Connect ONLY to existing Chrome debug instance - NEVER start new instance.
        
        This method implements the core session-preservation strategy by connecting
        to an existing Chrome browser launched by config/chrome-debug.sh.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.is_available():
            return False, "Selenium dependencies not available - install requirements-selenium.txt"
        
        if not self.is_chrome_debug_available():
            return False, (
                "Chrome debug session not available on port {port}. "
                "Start Chrome debug session with: ./config/chrome-debug.sh"
            ).format(port=self.debug_port)
        
        connection_start = time.time()
        
        for attempt in range(self.max_connection_attempts):
            try:
                logging.info(f"Attempting Chrome connection (attempt {attempt + 1}/{self.max_connection_attempts})")
                
                # Configure Chrome options for debug port connection
                options = Options()
                
                # CRITICAL: Connect to existing Chrome via debuggerAddress
                debugger_address = f"{self.debug_host}:{self.debug_port}"
                options.add_experimental_option("debuggerAddress", debugger_address)
                
                # Additional stability options
                chrome_options = self.config.get('chrome_options', [])
                for option in chrome_options:
                    options.add_argument(option)
                
                # NO ChromeDriver service needed - connects to existing debug port
                self.driver = webdriver.Chrome(options=options)
                
                # Configure timeouts
                self.driver.set_page_load_timeout(self.page_load_timeout)
                self.driver.set_script_timeout(self.script_timeout)
                self.driver.implicitly_wait(self.implicit_wait)
                
                connection_time = time.time() - connection_start
                self._connection_established = True
                
                logging.info(f"✓ Connected to Chrome debug session on {debugger_address} in {connection_time:.2f}s")
                return True, f"Connected to Chrome debug session (port {self.debug_port})"
                
            except WebDriverException as e:
                logging.warning(f"Chrome connection attempt {attempt + 1} failed: {e}")
                if attempt == self.max_connection_attempts - 1:
                    return False, f"Failed to connect to Chrome debug session after {self.max_connection_attempts} attempts: {e}"
                time.sleep(1)  # Brief pause before retry
                
            except Exception as e:
                logging.error(f"Unexpected error connecting to Chrome: {e}")
                return False, f"Unexpected Chrome connection error: {e}"
        
        return False, "Maximum connection attempts exceeded"
    
    def fetch_html_selenium(self, url: str, ua: Optional[str] = None, 
                           timeout: Optional[int] = None) -> Tuple[str, SeleniumMetrics]:
        """
        Fetch HTML using existing Chrome session - preserves all login states.
        
        Args:
            url: Target URL to fetch
            ua: User agent string (ignored - uses existing Chrome UA)
            timeout: Page load timeout in seconds (uses config default if None)
            
        Returns:
            Tuple of (html_content: str, metrics: SeleniumMetrics)
            
        Raises:
            ChromeConnectionError: If not connected to Chrome debug session
            SeleniumFetchError: If fetch operation fails
            SeleniumTimeoutError: If page load times out
        """
        if not self._connection_established or not self.driver:
            raise ChromeConnectionError("Not connected to Chrome debug session - call connect_to_chrome() first")
        
        # Use provided timeout or default from config
        fetch_timeout = timeout or self.page_load_timeout
        
        # Initialize metrics
        metrics = SeleniumMetrics(
            debug_port=self.debug_port,
            chrome_connected=True,
            js_detection_used=True,
            session_preserved=self.preserve_session
        )
        
        fetch_start = time.time()
        
        try:
            # Set timeout for this specific request
            original_timeout = self.driver.timeouts.page_load
            self.driver.set_page_load_timeout(fetch_timeout)
            
            logging.info(f"Fetching URL with Selenium: {url}")
            page_load_start = time.time()
            
            # Navigate to URL
            self.driver.get(url)
            
            # Wait for basic page load completion
            wait_conditions = self.config.get('wait_conditions', {})
            default_selector = wait_conditions.get('default_selector', 'body')
            
            try:
                WebDriverWait(self.driver, self.element_wait_timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, default_selector))
                )
                logging.debug(f"Page load completed - {default_selector} element found")
            except TimeoutException:
                logging.warning(f"Timeout waiting for {default_selector} element, continuing with available content")
            
            # Wait for JavaScript completion if configured
            js_complete_script = wait_conditions.get('js_complete', "return document.readyState === 'complete'")
            try:
                WebDriverWait(self.driver, self.script_timeout).until(
                    lambda driver: driver.execute_script(js_complete_script)
                )
                logging.debug("JavaScript execution completed")
            except TimeoutException:
                logging.warning("Timeout waiting for JavaScript completion, continuing")
            
            # Extract page content
            html_content = self.driver.page_source
            page_load_time = time.time() - page_load_start
            total_fetch_time = time.time() - fetch_start
            
            # Update metrics
            metrics.page_load_time = page_load_time
            metrics.selenium_wait_time = total_fetch_time
            
            # Restore original timeout
            self.driver.set_page_load_timeout(original_timeout)
            
            logging.info(f"✓ Selenium fetch completed in {total_fetch_time:.2f}s - content length: {len(html_content)}")
            
            return html_content, metrics
            
        except TimeoutException as e:
            fetch_duration = time.time() - fetch_start
            metrics.selenium_wait_time = fetch_duration
            metrics.error_message = f"Page load timeout ({fetch_timeout}s): {str(e)}"
            
            logging.error(f"Selenium fetch timeout for {url}: {e}")
            raise SeleniumTimeoutError(f"Page load timeout after {fetch_timeout}s: {e}")
            
        except WebDriverException as e:
            fetch_duration = time.time() - fetch_start
            metrics.selenium_wait_time = fetch_duration
            metrics.error_message = f"WebDriver error: {str(e)}"
            
            logging.error(f"Selenium WebDriver error for {url}: {e}")
            raise SeleniumFetchError(f"WebDriver error: {e}")
            
        except Exception as e:
            fetch_duration = time.time() - fetch_start
            metrics.selenium_wait_time = fetch_duration
            metrics.error_message = f"Unexpected error: {str(e)}"
            
            logging.error(f"Unexpected Selenium error for {url}: {e}")
            raise SeleniumFetchError(f"Unexpected error: {e}")
    
    def execute_script(self, script: str, *args) -> Any:
        """
        Execute JavaScript in the current Chrome session.
        
        Args:
            script: JavaScript code to execute
            *args: Arguments to pass to the script
            
        Returns:
            Result of script execution
            
        Raises:
            ChromeConnectionError: If not connected to Chrome
        """
        if not self._connection_established or not self.driver:
            raise ChromeConnectionError("Not connected to Chrome debug session")
        
        try:
            result = self.driver.execute_script(script, *args)
            logging.debug(f"Script executed successfully: {script[:50]}...")
            return result
        except Exception as e:
            logging.error(f"Script execution failed: {e}")
            raise SeleniumFetchError(f"Script execution failed: {e}")
    
    def get_page_info(self) -> Optional[Dict[str, Any]]:
        """
        Get current page information from Chrome session.
        
        Returns:
            Dictionary with page title, URL, and other metadata
        """
        if not self._connection_established or not self.driver:
            return None
        
        try:
            return {
                'title': self.driver.title,
                'url': self.driver.current_url,
                'page_source_length': len(self.driver.page_source),
                'window_handles': len(self.driver.window_handles)
            }
        except Exception as e:
            logging.error(f"Error getting page info: {e}")
            return None
    
    def cleanup(self) -> None:
        """
        Clean up browser resources while preserving the Chrome session.
        
        IMPORTANT: This does NOT quit the Chrome browser to preserve user sessions.
        It only disconnects the Selenium WebDriver connection.
        """
        if self.driver:
            try:
                # DON'T call driver.quit() - this would close the user's Chrome session
                # and lose all login states. Instead, just disconnect our WebDriver.
                self.driver = None
                self._connection_established = False
                
                logging.info("✓ Disconnected from Chrome debug session (browser session preserved)")
                
            except Exception as e:
                logging.warning(f"Error during cleanup: {e}")
                self.driver = None
                self._connection_established = False
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup"""
        self.cleanup()
    
    def is_connected(self) -> bool:
        """
        Check if currently connected to Chrome debug session.
        
        Returns:
            True if connected and ready for operations
        """
        return self._connection_established and self.driver is not None
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get detailed connection status information.
        
        Returns:
            Dictionary with connection status details
        """
        return {
            'selenium_available': self.is_available(),
            'chrome_debug_available': self.is_chrome_debug_available(),
            'connected': self.is_connected(),
            'debug_port': self.debug_port,
            'debug_host': self.debug_host,
            'preserve_session': self.preserve_session,
            'connection_established': self._connection_established
        }