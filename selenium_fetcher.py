"""
Selenium Fetcher for Web_Fetcher

Session-preserving Selenium implementation that connects ONLY to existing Chrome debug instances.
Designed to maintain login states and avoid automation detection.

Architecture: Uses Chrome's debug port (9222) to connect to existing browser sessions
launched by config/chrome-debug.sh, preserving all cookies and login states.

Phase 2 Enhancements:
- Robust Chrome/ChromeDriver version mismatch detection
- Clear, actionable error messages with solutions
- Smart retry logic that avoids retrying version mismatches
- Enhanced Chrome version parsing and tracking
- Improved connection error handling

Author: Cody (Claude Code)
Date: 2025-09-29
Version: 2.0 (Phase 2 - Robust Chrome Connection Enhancement)
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


# Error Message Templates
class ErrorMessages:
    """Centralized error message templates with actionable solutions"""
    
    VERSION_MISMATCH = """
Chrome/ChromeDriver version mismatch detected:
- Chrome version: {chrome_version}
- ChromeDriver version: {chromedriver_version}

SOLUTION: Update ChromeDriver to match Chrome version:
1. Download ChromeDriver from: https://chromedriver.chromium.org/downloads
2. Or install via: brew install --cask chromedriver (macOS)
3. Or install via: npm install -g chromedriver
4. Ensure ChromeDriver is in PATH and matches Chrome version

Current Chrome: {chrome_version}
Required ChromeDriver: {required_version}
"""

    CONNECTION_FAILED = """
Chrome debug connection failed:
{error_details}

SOLUTION: Ensure Chrome debug session is running:
1. Start Chrome with debug port: ./config/chrome-debug.sh
2. Or manually: google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug
3. Verify Chrome is running on port {debug_port}
4. Check that no firewall is blocking localhost:{debug_port}
"""

    DEBUG_SESSION_UNAVAILABLE = """
Chrome debug session not available on port {debug_port}.

SOLUTION: Start Chrome debug session:
1. Run: ./config/chrome-debug.sh
2. Or manually: google-chrome --remote-debugging-port={debug_port} --user-data-dir=/tmp/chrome-debug
3. Wait for Chrome to fully load before retrying
4. Verify browser is responsive at: http://localhost:{debug_port}/json/version

Make sure Chrome is running with debug port enabled before using Selenium fetcher.
"""

    SELENIUM_UNAVAILABLE = """
Selenium dependencies not available.

SOLUTION: Install Selenium requirements:
1. Run: pip install -r requirements-selenium.txt
2. Or install manually: pip install selenium
3. Ensure ChromeDriver is installed and in PATH
4. Restart application after installation
"""


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
        
        # Version tracking for better error handling
        self.chrome_version = None
        self.chrome_version_info = None
        self.chromedriver_version = None
        
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
    
    def _parse_chrome_version(self, version_info: Dict[str, Any]) -> Optional[str]:
        """
        Parse Chrome version from debug session version info.
        
        Args:
            version_info: Response from /json/version endpoint
            
        Returns:
            Chrome version string (e.g., "131.0.6778.108") or None
        """
        try:
            browser_info = version_info.get('Browser', '')
            
            # Parse version from browser string like "Chrome/131.0.6778.108"
            if 'Chrome/' in browser_info:
                version_part = browser_info.split('Chrome/')[1]
                version = version_part.split(' ')[0]  # Take first part before any spaces
                return version
            
            # Fallback: try other version fields
            if 'webKitVersion' in version_info:
                webkit_version = version_info['webKitVersion']
                # Extract version number if format is like "537.36 (@cfede9db2, Chrome/131.0.6778.108)"
                if 'Chrome/' in webkit_version:
                    chrome_part = webkit_version.split('Chrome/')[1]
                    version = chrome_part.split(')')[0]  # Remove closing parenthesis
                    return version
                    
            return None
            
        except Exception as e:
            logging.debug(f"Error parsing Chrome version: {e}")
            return None
    
    def _parse_chromedriver_version(self, error_message: str) -> Optional[str]:
        """
        Extract ChromeDriver version from WebDriverException error message.
        
        Args:
            error_message: WebDriverException message string
            
        Returns:
            ChromeDriver version string or None
        """
        try:
            # Common patterns in ChromeDriver error messages:
            # "session not created: This version of ChromeDriver only supports Chrome version 131"
            # "ChromeDriver 131.0.6778.69"
            # "only supports Chrome version 131"
            
            # Pattern 1: "only supports Chrome version X"
            if "only supports Chrome version" in error_message:
                parts = error_message.split("only supports Chrome version")
                if len(parts) > 1:
                    version_part = parts[1].strip()
                    # Extract just the version number
                    version = version_part.split()[0].split('.')[0]  # Get major version
                    return version
            
            # Pattern 2: "ChromeDriver X.Y.Z.W"
            if "ChromeDriver" in error_message:
                import re
                # Look for version pattern after "ChromeDriver"
                match = re.search(r'ChromeDriver\s+(\d+\.\d+\.\d+\.?\d*)', error_message)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception as e:
            logging.debug(f"Error parsing ChromeDriver version: {e}")
            return None
    
    def _is_version_mismatch_error(self, error_message: str) -> bool:
        """
        Detect if WebDriverException is due to Chrome/ChromeDriver version mismatch.
        
        Args:
            error_message: WebDriverException message string
            
        Returns:
            True if error appears to be version mismatch
        """
        version_mismatch_indicators = [
            "only supports Chrome version",
            "version of ChromeDriver only supports",
            "Current browser version is",
            "ChromeDriver supports Chrome",
            "supports Chrome version",  # Added to catch "ChromeDriver X supports Chrome version Y"
            "session not created",
            "version mismatch"
        ]
        
        error_lower = error_message.lower()
        return any(indicator.lower() in error_lower for indicator in version_mismatch_indicators)
    
    def _get_required_chromedriver_version(self, chrome_version: str) -> str:
        """
        Get the required ChromeDriver version for a given Chrome version.
        
        Args:
            chrome_version: Chrome version string (e.g., "131.0.6778.108")
            
        Returns:
            Required ChromeDriver major version (e.g., "131")
        """
        try:
            # ChromeDriver major version should match Chrome major version
            major_version = chrome_version.split('.')[0]
            return major_version
        except Exception:
            return "unknown"
    
    def is_chrome_debug_available(self) -> bool:
        """
        Check if Chrome debug session is running on configured port.
        
        CRITICAL: This prevents attempting connection to non-existent session.
        Uses Chrome DevTools Protocol to verify session availability.
        
        Enhanced in Phase 2: Now parses and stores Chrome version information
        for better error handling and version mismatch detection.
        
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
                    
                    # Store version information for error handling
                    self.chrome_version_info = version_info
                    self.chrome_version = self._parse_chrome_version(version_info)
                    
                    browser_info = version_info.get('Browser', 'Unknown')
                    logging.debug(f"Chrome debug session detected: {browser_info}")
                    
                    if self.chrome_version:
                        logging.info(f"Chrome version detected: {self.chrome_version}")
                    else:
                        logging.warning("Could not parse Chrome version from debug session")
                    
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
                            
                            # Store version information for error handling
                            self.chrome_version_info = version_info
                            self.chrome_version = self._parse_chrome_version(version_info)
                            
                            browser_info = version_info.get('Browser', 'Unknown')
                            logging.debug(f"Chrome debug session detected: {browser_info}")
                            
                            if self.chrome_version:
                                logging.info(f"Chrome version detected: {self.chrome_version}")
                            else:
                                logging.warning("Could not parse Chrome version from debug session")
                            
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
        
        Enhanced in Phase 2: Improved error handling with version mismatch detection
        and smarter retry logic that doesn't retry on version mismatches.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.is_available():
            return False, ErrorMessages.SELENIUM_UNAVAILABLE.strip()
        
        if not self.is_chrome_debug_available():
            return False, ErrorMessages.DEBUG_SESSION_UNAVAILABLE.format(
                debug_port=self.debug_port
            ).strip()
        
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
                error_msg = str(e)
                logging.warning(f"Chrome connection attempt {attempt + 1} failed: {error_msg}")
                
                # Check if this is a version mismatch error
                if self._is_version_mismatch_error(error_msg):
                    # Parse ChromeDriver version from error message
                    chromedriver_version = self._parse_chromedriver_version(error_msg)
                    self.chromedriver_version = chromedriver_version
                    
                    # Create detailed version mismatch error message
                    chrome_version = self.chrome_version or "unknown"
                    chromedriver_version_display = chromedriver_version or "unknown"
                    required_version = self._get_required_chromedriver_version(chrome_version) if chrome_version != "unknown" else "unknown"
                    
                    version_error = ErrorMessages.VERSION_MISMATCH.format(
                        chrome_version=chrome_version,
                        chromedriver_version=chromedriver_version_display,
                        required_version=required_version
                    )
                    
                    logging.error(f"Version mismatch detected - Chrome: {chrome_version}, ChromeDriver: {chromedriver_version_display}")
                    
                    # Don't retry on version mismatch - it won't succeed
                    return False, version_error.strip()
                
                # For non-version-mismatch errors, continue with retry logic
                if attempt == self.max_connection_attempts - 1:
                    # Last attempt failed - return detailed error
                    connection_error = ErrorMessages.CONNECTION_FAILED.format(
                        error_details=error_msg,
                        debug_port=self.debug_port
                    )
                    return False, connection_error.strip()
                
                # Brief pause before retry (but only for non-version-mismatch errors)
                time.sleep(1)
                
            except Exception as e:
                logging.error(f"Unexpected error connecting to Chrome: {e}")
                unexpected_error = ErrorMessages.CONNECTION_FAILED.format(
                    error_details=f"Unexpected error: {e}",
                    debug_port=self.debug_port
                )
                return False, unexpected_error.strip()
        
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
    
    def get_version_info(self) -> Dict[str, Any]:
        """
        Get Chrome and ChromeDriver version information.
        
        Returns:
            Dictionary with version details
        """
        return {
            'chrome_version': self.chrome_version,
            'chromedriver_version': self.chromedriver_version,
            'chrome_version_info': self.chrome_version_info,
            'version_compatible': (
                self.chrome_version and self.chromedriver_version and
                self.chrome_version.split('.')[0] == self.chromedriver_version.split('.')[0]
            ) if self.chrome_version and self.chromedriver_version else None
        }
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get detailed connection status information.
        
        Enhanced in Phase 2: Now includes version information
        
        Returns:
            Dictionary with connection status details
        """
        status = {
            'selenium_available': self.is_available(),
            'chrome_debug_available': self.is_chrome_debug_available(),
            'connected': self.is_connected(),
            'debug_port': self.debug_port,
            'debug_host': self.debug_host,
            'preserve_session': self.preserve_session,
            'connection_established': self._connection_established
        }
        
        # Add version information
        status.update(self.get_version_info())
        
        return status