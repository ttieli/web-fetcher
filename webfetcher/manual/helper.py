"""
Manual Chrome Helper

Core module for managing manual Chrome sessions and automated content extraction.
This module handles Chrome startup, user guidance, CDP attachment, and cleanup.
"""

import os
import subprocess
import time
import logging
from typing import Tuple, Optional, Dict, Any

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

from .exceptions import (
    ChromeNotFoundError,
    PortInUseError,
    AttachmentError,
    TimeoutError,
    NavigationError
)

# Configure logger
logger = logging.getLogger(__name__)


class ManualChromeHelper:
    """
    Helper class for manual Chrome hybrid approach.

    This class manages the workflow of:
    1. Starting Chrome with remote debugging enabled
    2. Guiding user to navigate to target URL
    3. Attaching via Selenium to extract content
    4. Cleaning up resources properly

    Attributes:
        config (Dict): Configuration dictionary
        driver (webdriver.Chrome): Selenium WebDriver instance
        chrome_process (subprocess.Popen): Chrome process handle
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ManualChromeHelper.

        Args:
            config: Configuration dictionary with structure:
                {
                    'chrome': {
                        'path': '/path/to/Chrome',  # Optional
                        'debug_port': 9222,
                        'user_data_dir': '/tmp/web-fetcher-manual'
                    },
                    'ux': {
                        'auto_copy_url': True,
                        'show_notification': False,
                        'wait_timeout': 300
                    }
                }
        """
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None
        self.chrome_process: Optional[subprocess.Popen] = None

        # Validate configuration
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate that required configuration keys exist."""
        required_keys = ['chrome', 'ux']
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required config key: {key}")

        if 'debug_port' not in self.config['chrome']:
            raise ValueError("Missing required config key: chrome.debug_port")

    def start_session(self, url: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Start a manual Chrome session to fetch content.

        This is the main entry point for the manual Chrome workflow.

        Args:
            url: Target URL to fetch

        Returns:
            Tuple of (success: bool, html: str, error: str)

        Example:
            >>> helper = ManualChromeHelper(config)
            >>> success, html, error = helper.start_session(url)
            >>> if success:
            ...     print(f"Extracted {len(html)} bytes")
        """
        try:
            # Step 1: Validate Chrome installation
            self._validate_chrome_installation()

            # Step 2: Check if debug port is available
            self._check_debug_port()

            # Step 3: Start Chrome with debug port
            self._start_chrome()

            # Step 4: Display instructions and prepare UI
            self._prepare_ui(url)

            # Step 5: Wait for user to navigate
            self._wait_for_navigation()

            # Step 6: Attach to Chrome and extract content
            html = self._attach_and_extract()

            # Step 7: Cleanup
            self._cleanup(force=False)

            return True, html, None

        except Exception as e:
            logger.error(f"Manual Chrome session failed: {str(e)}")
            self._cleanup(force=True)
            return False, None, str(e)

    def _validate_chrome_installation(self) -> None:
        """
        Validate that Chrome is installed at the expected location.

        Raises:
            ChromeNotFoundError: If Chrome is not found
        """
        # Get Chrome path from config, or use default macOS path
        chrome_path = self.config.get('chrome', {}).get(
            'path',
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        )

        if not os.path.exists(chrome_path):
            raise ChromeNotFoundError(
                f"Chrome not found at: {chrome_path}\n\n"
                f"Please install Chrome or set custom path in:\n"
                f"  config/manual_chrome_config.yaml\n\n"
                f"Example config:\n"
                f"  chrome:\n"
                f"    path: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'"
            )

        logger.info(f"Chrome found at: {chrome_path}")
        self.chrome_path = chrome_path

    def _check_debug_port(self) -> None:
        """
        Check if the debug port is available.

        Raises:
            PortInUseError: If port is already in use
        """
        port = self.config['chrome']['debug_port']

        # Check if port is in use using lsof
        try:
            result = subprocess.run(
                ['lsof', '-ti', f':{port}'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.stdout.strip():
                # Port is in use
                pids = result.stdout.strip().split('\n')
                raise PortInUseError(
                    port,
                    f"Port {port} is already in use by process(es): {', '.join(pids)}\n\n"
                    f"Solutions:\n"
                    f"1. Close existing Chrome debug session\n"
                    f"2. Kill process(es): kill -9 {' '.join(pids)}\n"
                    f"3. Configure a different port in manual_chrome_config.yaml"
                )

            logger.info(f"Port {port} is available")

        except subprocess.TimeoutExpired:
            logger.warning(f"Port check timed out, proceeding anyway")
        except FileNotFoundError:
            logger.warning("lsof command not found, skipping port check")

    def _start_chrome(self) -> None:
        """
        Start Chrome with remote debugging enabled.

        Raises:
            Exception: If Chrome fails to start
        """
        port = self.config['chrome']['debug_port']
        user_data_dir = self.config['chrome'].get('user_data_dir', '/tmp/web-fetcher-manual')

        # Ensure user data dir exists
        os.makedirs(user_data_dir, exist_ok=True)

        # Build Chrome command
        cmd = [
            self.chrome_path,
            f'--remote-debugging-port={port}',
            f'--user-data-dir={user_data_dir}',
            '--no-first-run',
            '--no-default-browser-check'
        ]

        logger.info(f"Starting Chrome with debug port {port}...")

        try:
            # Start Chrome process
            self.chrome_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Wait a bit for Chrome to start
            time.sleep(2)

            # Check if process is still alive
            if self.chrome_process.poll() is not None:
                raise Exception("Chrome process terminated immediately after start")

            logger.info(f"Chrome started successfully (PID: {self.chrome_process.pid})")

        except Exception as e:
            raise Exception(f"Failed to start Chrome: {str(e)}")

    def _prepare_ui(self, url: str) -> None:
        """
        Prepare user interface and display instructions.

        Args:
            url: Target URL to display in instructions
        """
        print("\n" + "="*70)
        print("  MANUAL CHROME MODE - USER ACTION REQUIRED")
        print("="*70)
        print()
        print("Chrome has been launched with remote debugging enabled.")
        print()
        print("Please follow these steps:")
        print()
        print("  1. Navigate to this URL in the Chrome window:")
        print(f"     {url}")
        print()
        print("  2. Complete any challenges (CAPTCHA, login, SSL warnings, etc.)")
        print()
        print("  3. Wait for the page to fully load")
        print()
        print("  4. Press ENTER in this terminal when ready")
        print()
        print("-"*70)

        # Optional: Auto-copy URL to clipboard
        if self.config['ux'].get('auto_copy_url', True):
            try:
                import pyperclip
                pyperclip.copy(url)
                print("✓ URL copied to clipboard (⌘+V to paste)")
                print()
            except ImportError:
                print("⚠️  pyperclip not available - please manually copy URL from above")
                print("   Install with: pip install pyperclip")
                print()
            except Exception as e:
                logger.warning(f"Failed to copy to clipboard: {e}")
                print("⚠️  Could not copy to clipboard - please manually copy URL")
                print()

    def _wait_for_navigation(self) -> None:
        """
        Wait for user to complete navigation.

        Raises:
            TimeoutError: If user doesn't respond within timeout period
        """
        timeout = self.config['ux'].get('wait_timeout', 300)

        print(f"Waiting for user (timeout: {timeout}s)...")
        print()

        try:
            # Use input() with no timeout - user presses Enter when ready
            input("Press ENTER when you have navigated to the page: ")
            print()
            logger.info("User confirmed navigation complete")

        except KeyboardInterrupt:
            raise TimeoutError(
                timeout,
                "User cancelled operation (Ctrl+C)"
            )

    def _attach_and_extract(self) -> str:
        """
        Attach to Chrome via Selenium and extract page content.

        Returns:
            str: Page HTML content

        Raises:
            AttachmentError: If unable to attach to Chrome
            NavigationError: If page is in error state
        """
        port = self.config['chrome']['debug_port']

        try:
            # Configure Selenium to attach to existing Chrome
            options = Options()
            options.debugger_address = f"127.0.0.1:{port}"

            logger.info(f"Attaching to Chrome on port {port}...")

            # Let Selenium Manager handle chromedriver automatically
            self.driver = webdriver.Chrome(options=options)

            logger.info("Successfully attached to Chrome")

            # Get current URL and title for logging
            current_url = self.driver.current_url
            title = self.driver.title

            logger.info(f"Current URL: {current_url}")
            logger.info(f"Page title: {title}")

            # Extract HTML content
            html = self.driver.page_source

            if not html or len(html) < 100:
                raise NavigationError(
                    current_url,
                    f"Page content too short ({len(html)} bytes). "
                    f"Page may not have loaded properly."
                )

            logger.info(f"Extracted {len(html)} bytes of HTML content")

            return html

        except WebDriverException as e:
            error_msg = str(e)

            # Provide helpful error messages
            if "chromedriver" in error_msg.lower():
                raise AttachmentError(
                    f"ChromeDriver issue: {error_msg}\n\n"
                    f"Solution: Ensure Selenium is up to date:\n"
                    f"  pip install --upgrade selenium"
                )
            else:
                raise AttachmentError(f"Failed to attach to Chrome: {error_msg}")

        except Exception as e:
            raise AttachmentError(f"Unexpected error during attachment: {str(e)}")

    def _cleanup(self, force: bool = False) -> None:
        """
        Clean up resources.

        Args:
            force: If True, forcefully terminate Chrome process.
                   If False, only quit the driver (Chrome window stays open).
        """
        # ALWAYS quit driver to release resources
        if self.driver:
            try:
                logger.info("Closing Selenium driver...")
                self.driver.quit()
                logger.info("Driver closed successfully")
            except Exception as e:
                logger.warning(f"Error closing driver: {e}")
            finally:
                self.driver = None

        # Only terminate Chrome if explicitly requested
        if force and self.chrome_process:
            try:
                logger.info("Terminating Chrome process...")
                self.chrome_process.terminate()

                # Wait up to 5 seconds for graceful termination
                try:
                    self.chrome_process.wait(timeout=5)
                    logger.info("Chrome terminated gracefully")
                except subprocess.TimeoutExpired:
                    logger.warning("Chrome didn't terminate gracefully, killing...")
                    self.chrome_process.kill()
                    logger.info("Chrome killed")

            except Exception as e:
                logger.warning(f"Error terminating Chrome: {e}")
            finally:
                self.chrome_process = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - always cleanup."""
        self._cleanup(force=True)
