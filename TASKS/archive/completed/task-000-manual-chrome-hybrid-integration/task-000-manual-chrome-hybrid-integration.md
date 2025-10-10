# Task 000: Manual Chrome Hybrid Integration
# 任务000: 手动Chrome混合模式集成

**Priority**: HIGHEST / 最高优先级
**Status**: DESIGN / 设计阶段
**Created**: 2025-10-09
**Updated**: 2025-10-09 - Applied macOS-focused simplifications
**Estimated Effort**: 10-14 hours
**Success Criteria**: Successfully integrated as universal fallback for all failed fetches

---

## Executive Summary / 执行摘要

Integrate the proven manual Chrome + CDP hybrid approach as a universal fallback mechanism that:
- Activates automatically when all automated methods fail
- Requires minimal user intervention (only manual navigation)
- Works universally for any website regardless of protection type
- Provides excellent user experience with clear guidance
- **Optimized for macOS single-user environment**

This solution leverages the successful proof-of-concept from `test_manual_chrome_selenium.py` and extends it into a production-ready fallback system.

---

## 1. System Architecture Design / 系统架构设计

### 1.1 Current Architecture / 当前架构
```
webfetcher.py
    ↓
fetch_html_with_retry()
    ↓
[requests] → [selenium] → [error/empty response]
```

### 1.2 Enhanced Architecture with Manual Fallback / 增强架构
```
webfetcher.py
    ↓
fetch_html_with_retry()
    ↓
[requests] → [selenium] → [manual_chrome_fallback] → [final_error]
                             ↓
                    ManualChromeHelper
                             ↓
                   ┌──────────────────┐
                   │ Validate Chrome  │
                   │ (os.path.exists) │
                   └────────┬─────────┘
                            ↓
                   ┌──────────────────┐
                   │ Start Chrome     │
                   │ (debug port)     │
                   └────────┬─────────┘
                            ↓
                   ┌──────────────────┐
                   │ Try copy URL     │
                   │ (graceful fail)  │
                   └────────┬─────────┘
                            ↓
                   ┌──────────────────┐
                   │ User navigates   │
                   │ manually         │
                   └────────┬─────────┘
                            ↓
                   ┌──────────────────┐
                   │ Selenium Manager │
                   │ Auto-attach CDP  │
                   └────────┬─────────┘
                            ↓
                       [Success]
```

---

## 2. Module Structure / 模块结构

### 2.1 File Organization / 文件组织

```
Web_Fetcher/
├── manual_chrome/                    # New directory for manual mode
│   ├── __init__.py
│   ├── helper.py                    # Main ManualChromeHelper class
│   ├── detector.py                  # Challenge detection logic
│   ├── ui_manager.py               # User interface and guidance
│   └── exceptions.py               # Custom exceptions
│
├── config/
│   └── manual_chrome_config.yaml    # Configuration file (macOS-focused)
│
├── webfetcher.py                    # Modified to integrate fallback
│
├── scripts/
│   └── manual_mode_cli.py          # Standalone CLI tool with --diagnose
│
└── tests/
    └── manual_chrome/
        ├── test_helper.py
        ├── test_detector.py
        └── test_integration.py
```

### 2.2 Module Responsibilities / 模块职责

| Module | Responsibility | Key Functions |
|--------|---------------|---------------|
| `helper.py` | Core Chrome management | Validate Chrome, start with debug, extract content |
| `detector.py` | Challenge detection | Identify anti-bot patterns, SSL errors, etc. |
| `ui_manager.py` | User interaction | Display instructions, optional clipboard/notifications |
| `exceptions.py` | Error handling | Custom exceptions with helpful messages |

---

## 3. Platform Support / 平台支持

### 3.1 Supported Platforms / 支持的平台
- ✅ **macOS**: Primary platform (tested and supported)
- ❌ Linux: Not currently supported (may add in future)
- ❌ Windows: Not currently supported (may add in future)

### 3.2 Chrome Path Configuration / Chrome路径配置

Default path: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`

If Chrome is installed in a different location, configure in `config/manual_chrome_config.yaml`:

```yaml
chrome:
  path: "/path/to/your/Google Chrome"  # Optional: override default path
  debug_port: 9222
```

**Error Handling**:
- If default path doesn't exist → Show clear error with config instructions
- If custom path invalid → Validate on startup and fail fast with helpful message

---

## 4. Integration Points / 集成点

### 4.1 Detection Logic / 检测逻辑

```python
# manual_chrome/detector.py

class FallbackDetector:
    """
    Determines when to trigger manual Chrome fallback
    """

    def __init__(self, config):
        self.config = config
        self.trigger_patterns = {
            'empty_response': lambda r: len(r.text) < 100,
            'anti_bot_codes': lambda r: r.status_code in [400, 403, 412],
            'ssl_error': lambda r: 'SSL' in str(r.reason),
            'cloudflare': lambda r: 'cloudflare' in r.text.lower(),
            'login_required': lambda r: self._detect_login(r),
            'captcha': lambda r: self._detect_captcha(r)
        }

    def should_use_fallback(self, url, response, retries_exhausted):
        """
        Determine if manual fallback should be triggered

        Args:
            url: Target URL
            response: Last response object
            retries_exhausted: Boolean if all retries used

        Returns:
            (should_fallback, reason)
        """
        # Check if enabled
        if not self.config.get('enabled', True):
            return False, None

        # Must have exhausted retries
        if not retries_exhausted:
            return False, None

        # Check each trigger pattern
        for pattern_name, check_func in self.trigger_patterns.items():
            try:
                if check_func(response):
                    return True, pattern_name
            except:
                continue

        # Check known problematic domains
        if self._is_known_challenge_site(url):
            return True, 'known_challenge_site'

        return False, None

    def _is_known_challenge_site(self, url):
        """Check if URL is a known problematic site"""
        challenge_domains = [
            'cebbank.com',
            'icbc.com.cn',
            'xiaohongshu.com',
            # Add more as discovered
        ]

        for domain in challenge_domains:
            if domain in url:
                return True
        return False
```

### 4.2 Integration into webfetcher.py / 集成到主模块

```python
# Modifications to webfetcher.py

from manual_chrome.helper import ManualChromeHelper
from manual_chrome.detector import FallbackDetector
import yaml

# Load manual Chrome configuration
def load_manual_chrome_config():
    config_path = 'config/manual_chrome_config.yaml'
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {'enabled': False}

# Initialize components
MANUAL_CONFIG = load_manual_chrome_config()
manual_helper = ManualChromeHelper(MANUAL_CONFIG) if MANUAL_CONFIG['enabled'] else None
fallback_detector = FallbackDetector(MANUAL_CONFIG) if MANUAL_CONFIG['enabled'] else None

def fetch_html_with_retry(url, max_retries=3, delay=5, ...):
    """
    Enhanced with manual Chrome fallback
    """
    metrics = FetchMetrics()

    # ... existing retry logic ...

    # After all automated methods fail
    if manual_helper and fallback_detector:
        should_fallback, reason = fallback_detector.should_use_fallback(
            url, last_response, retries_exhausted=True
        )

        if should_fallback:
            logger.info(f"Triggering manual fallback (reason: {reason})")

            try:
                html_content = manual_helper.fetch_with_manual_intervention(
                    url=url,
                    challenge_type=reason
                )

                if html_content:
                    metrics.method_used = 'manual_chrome'
                    metrics.success = True
                    logger.info(f"Manual fallback succeeded: {len(html_content)} bytes")
                    return html_content, metrics

            except Exception as e:
                logger.error(f"Manual fallback failed: {e}")
                metrics.error = str(e)

    # Final failure
    return "", metrics
```

---

## 5. Core Implementation / 核心实现

### 5.1 ManualChromeHelper Class / 手动Chrome助手类

```python
# manual_chrome/helper.py

import subprocess
import time
import sys
import select
import os
import socket
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import logging

class ChromeNotFoundError(Exception):
    """Chrome installation not found"""
    pass

class PortInUseError(Exception):
    """Debug port already in use"""
    pass

class ManualChromeHelper:
    """
    Helper class for manual Chrome intervention when automated methods fail
    macOS-optimized implementation
    """

    def __init__(self, config):
        self.config = config
        self.chrome_process = None
        self.driver = None
        self.logger = logging.getLogger(__name__)

    def fetch_with_manual_intervention(self, url, challenge_type=None):
        """
        Main entry point for manual Chrome fallback

        Args:
            url: Target URL to fetch
            challenge_type: Type of challenge detected (for guidance)

        Returns:
            HTML content or None if failed
        """
        try:
            # Phase 1: Validate Chrome installation
            chrome_path = self._validate_chrome_installation()

            # Phase 2: Check debug port availability
            self._check_debug_port()

            # Phase 3: Prepare UI and user
            self._prepare_user_intervention(url, challenge_type)

            # Phase 4: Start Chrome with debugging
            self._start_chrome_debug_mode(chrome_path)

            # Phase 5: Wait for user navigation
            if not self._wait_for_user_navigation():
                return None

            # Phase 6: Attach and extract
            html_content = self._attach_and_extract()

            # Phase 7: Cleanup
            self._cleanup(force=False)

            return html_content

        except Exception as e:
            self.logger.error(f"Manual intervention failed: {e}")
            self._cleanup(force=True)
            raise

    def _validate_chrome_installation(self):
        """
        Validate Chrome installation (macOS only)
        """
        chrome_path = self.config.get('chrome', {}).get('path',
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')

        if not os.path.exists(chrome_path):
            raise ChromeNotFoundError(
                f"Chrome not found at: {chrome_path}\n\n"
                f"Please install Chrome or set custom path in:\n"
                f"  config/manual_chrome_config.yaml\n\n"
                f"Example config:\n"
                f"  chrome:\n"
                f"    path: '/path/to/Google Chrome'\n"
            )

        self.logger.debug(f"Chrome found at: {chrome_path}")
        return chrome_path

    def _check_debug_port(self):
        """
        Check if debug port is available
        """
        port = self.config.get('chrome', {}).get('debug_port', 9222)

        # Check if port is in use
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) == 0:
                raise PortInUseError(
                    f"Port {port} is already in use!\n\n"
                    f"Solutions:\n"
                    f"  1. Close existing Chrome with debug port:\n"
                    f"     pkill -f 'remote-debugging-port={port}'\n"
                    f"  2. Change port in config/manual_chrome_config.yaml\n"
                )

        self.logger.debug(f"Port {port} is available")

    def _prepare_user_intervention(self, url, challenge_type):
        """Prepare everything for user intervention with graceful fallback"""

        # Essential: Terminal instructions (always shown)
        self._display_instructions(url, challenge_type)

        # Optional: Clipboard (graceful fallback)
        if self.config.get('ux', {}).get('auto_copy_url', True):
            try:
                import pyperclip
                pyperclip.copy(url)
                print("✓ URL copied to clipboard")
            except ImportError:
                print("⚠️  pyperclip not available")
                print("   Please manually copy URL from above")
            except Exception as e:
                self.logger.debug(f"Clipboard copy failed: {e}")
                print("   Please manually copy URL from above")

        # Optional: System notification (graceful fallback)
        if self.config.get('ux', {}).get('show_notification', True):
            try:
                self._show_notification(url)
            except Exception as e:
                self.logger.debug(f"Notification failed: {e}")
                # Silently fail - not critical

    def _display_instructions(self, url, challenge_type):
        """Display clear instructions to user"""

        # Challenge-specific guidance
        guidance = {
            'ssl_error': "⚠️  SSL Certificate Issue - Click 'Advanced' then 'Proceed'",
            'anti_bot_codes': "🤖 Anti-Bot Protection - Complete any challenges",
            'cloudflare': "☁️  Cloudflare Protection - Complete the check",
            'login_required': "🔐 Login Required - Sign in first",
            'captcha': "🔢 CAPTCHA Required - Solve the puzzle",
            'known_challenge_site': "🌐 Known Protected Site - Manual navigation needed"
        }

        specific_guidance = guidance.get(challenge_type, "❓ Manual navigation required")

        print("\n" + "="*60)
        print("🔧 MANUAL CHROME FALLBACK ACTIVATED")
        print("="*60)
        print(f"\n{specific_guidance}")
        print(f"\n📋 URL to navigate to:")
        print(f"🔗 {url[:80]}..." if len(url) > 80 else f"🔗 {url}")
        print("\n" + "─"*60)
        print("📝 INSTRUCTIONS:")
        print("─"*60)
        print("1. Chrome will open automatically")
        print("2. Paste the URL (Cmd+V) in address bar")
        print("3. Navigate and complete any challenges")
        print("4. Once page loads fully, press ENTER here")
        print("─"*60)
        print("\n⏳ Starting Chrome...\n")

    def _start_chrome_debug_mode(self, chrome_path):
        """Start Chrome with remote debugging enabled"""

        port = self.config.get('chrome', {}).get('debug_port', 9222)
        user_data_dir = self.config.get('chrome', {}).get('user_data_dir', '/tmp/web-fetcher-manual')

        # Build command
        cmd = [
            chrome_path,
            f'--remote-debugging-port={port}',
            f'--user-data-dir={user_data_dir}',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-popup-blocking',
            '--disable-extensions',
            '--disable-default-apps',
            '--disable-sync'
        ]

        # Add custom flags
        custom_flags = self.config.get('chrome', {}).get('flags', [])
        cmd.extend(custom_flags)

        # Start Chrome
        self.logger.info(f"Starting Chrome with debug port {port}")
        self.chrome_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Wait for Chrome to start
        time.sleep(3)

        # Verify Chrome started
        if self.chrome_process.poll() is not None:
            raise RuntimeError("Chrome failed to start")

        print("✅ Chrome started successfully")
        print(f"   Debug port: {port}")
        print("   Please navigate to the target page\n")

    def _wait_for_user_navigation(self):
        """Wait for user to complete manual navigation"""

        timeout = self.config.get('ux', {}).get('wait_timeout', 300)  # 5 minutes
        start_time = time.time()

        print("⏳ Waiting for you to complete navigation...")
        print("   Press ENTER when the page is fully loaded")
        print(f"   Timeout: {timeout} seconds\n")

        # Use select for non-blocking input with timeout
        while time.time() - start_time < timeout:
            # Check for user input (1 second intervals)
            ready = select.select([sys.stdin], [], [], 1)[0]
            if ready:
                sys.stdin.readline()  # Consume the enter press
                print("\n✅ User confirmed page is ready")
                return True

            # Show progress
            elapsed = int(time.time() - start_time)
            if elapsed % 30 == 0 and elapsed > 0:
                remaining = timeout - elapsed
                print(f"   ⏰ {remaining} seconds remaining...")

        print("\n❌ Timeout reached")
        return False

    def _attach_and_extract(self):
        """
        Attach to Chrome and extract content using Selenium Manager
        """
        port = self.config.get('chrome', {}).get('debug_port', 9222)

        print("\n🔗 Attaching to Chrome...")

        try:
            options = Options()
            options.debugger_address = f"127.0.0.1:{port}"

            # Let Selenium Manager handle chromedriver automatically
            self.driver = webdriver.Chrome(options=options)

            # Get current tab info
            current_url = self.driver.current_url
            title = self.driver.title

            print(f"✅ Attached successfully")
            print(f"   URL: {current_url}")
            print(f"   Title: {title}")

            # Extract content
            print("\n📥 Extracting page content...")

            # Try multiple extraction methods
            html_content = None

            # Method 1: Direct page_source
            try:
                html_content = self.driver.page_source
                if html_content and len(html_content) > 1000:
                    print(f"   ✅ Extracted via page_source: {len(html_content)} bytes")
                    return html_content
            except:
                pass

            # Method 2: JavaScript extraction
            try:
                html_content = self.driver.execute_script(
                    "return document.documentElement.outerHTML;"
                )
                if html_content and len(html_content) > 1000:
                    print(f"   ✅ Extracted via JavaScript: {len(html_content)} bytes")
                    return html_content
            except:
                pass

            # Method 3: CDP extraction
            try:
                html_content = self.driver.execute_cdp_cmd(
                    'Runtime.evaluate',
                    {'expression': 'document.documentElement.outerHTML'}
                )['result']['value']
                if html_content and len(html_content) > 1000:
                    print(f"   ✅ Extracted via CDP: {len(html_content)} bytes")
                    return html_content
            except:
                pass

            # If we got here, extraction failed
            print("   ❌ Content extraction failed")
            return None

        except WebDriverException as e:
            self.logger.error(f"Failed to attach to Chrome: {e}")
            print("\nTroubleshooting:")
            print("  Run: python scripts/manual_mode_cli.py --diagnose")
            print("  This will check your Selenium and Chrome setup")
            raise

    def _cleanup(self, force=False):
        """
        Cleanup resources

        Args:
            force: If True, also terminate Chrome process
        """
        print("\n🧹 Cleaning up...")

        # ALWAYS quit driver to release resources
        if self.driver:
            try:
                self.driver.quit()
                print("   ✅ Driver cleaned up")
                self.logger.debug("Driver cleaned up")
            except Exception as e:
                self.logger.warning(f"Driver cleanup error: {e}")
            finally:
                self.driver = None

        # Only terminate Chrome if explicitly requested
        if force and self.chrome_process:
            try:
                self.chrome_process.terminate()
                self.chrome_process.wait(timeout=5)
                print("   ✅ Chrome process terminated")
                self.logger.debug("Chrome process terminated")
            except Exception as e:
                self.logger.warning(f"Chrome termination error: {e}")
                try:
                    self.chrome_process.kill()
                except:
                    pass
            finally:
                self.chrome_process = None

    def _show_notification(self, url):
        """Show OS notification (macOS only)"""
        try:
            subprocess.run([
                'osascript', '-e',
                f'display notification "URL copied! Chrome starting..." '
                f'with title "Web Fetcher - Manual Mode" '
                f'sound name "Glass"'
            ])
        except:
            pass  # Notifications are optional
```

---

## 6. Configuration Management / 配置管理

### 6.1 Configuration File / 配置文件

```yaml
# config/manual_chrome_config.yaml
# macOS-optimized configuration

manual_chrome:
  enabled: true

  # Platform: macOS only (for now)
  platform: macos

  # Chrome configuration
  chrome:
    # Optional: Custom Chrome path (if not in default location)
    # path: "/path/to/Google Chrome"

    # Debug port for remote debugging
    debug_port: 9222

    # User data directory
    user_data_dir: /tmp/web-fetcher-manual

    # Chrome flags
    flags:
      - --no-first-run
      - --disable-extensions

  # Trigger conditions for manual fallback
  trigger_conditions:
    all_retries_exhausted: true
    content_size_below: 100
    status_codes: [400, 403, 412]

    # Known problematic domains
    challenge_domains:
      - cebbank.com
      - icbc.com.cn
      - xiaohongshu.com

  # User experience settings
  ux:
    auto_copy_url: true        # Try to copy URL (graceful fallback if pyperclip unavailable)
    show_notification: false   # macOS notifications (optional)
    wait_timeout: 300          # 5 minutes

  # Logging
  log_level: INFO
```

---

## 7. Diagnostic Tool / 诊断工具

### 7.1 CLI Diagnostic Mode Implementation

```python
# scripts/manual_mode_cli.py --diagnose implementation

import os
import sys
import subprocess
import socket
import platform

def diagnose_environment():
    """
    Diagnostic tool for manual Chrome setup
    """
    print("=" * 60)
    print("Manual Chrome Mode - Environment Diagnosis")
    print("=" * 60)

    # 1. Check platform
    print("\n1. Platform Check:")
    system = platform.system()
    if system == 'Darwin':
        print(f"   ✓ macOS detected ({platform.mac_ver()[0]})")
    else:
        print(f"   ⚠️  {system} detected - only macOS is officially supported")

    # 2. Check Chrome installation
    print("\n2. Chrome Installation:")
    chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    if os.path.exists(chrome_path):
        print(f"   ✓ Found: {chrome_path}")
        # Try to get version
        try:
            result = subprocess.run([chrome_path, '--version'],
                                   capture_output=True, text=True)
            print(f"   ✓ Version: {result.stdout.strip()}")
        except Exception as e:
            print(f"   ⚠️  Cannot get version: {e}")
    else:
        print(f"   ✗ Not found: {chrome_path}")
        print(f"   → Set custom path in config/manual_chrome_config.yaml")

    # 3. Check Selenium
    print("\n3. Selenium Setup:")
    try:
        import selenium
        version = selenium.__version__
        print(f"   ✓ Selenium version: {version}")

        # Check if version supports Selenium Manager
        major, minor = map(int, version.split('.')[:2])
        if major > 4 or (major == 4 and minor >= 6):
            print(f"   ✓ Selenium Manager supported (auto driver management)")
        else:
            print(f"   ⚠️  Selenium Manager requires 4.6+ (manual driver needed)")

    except ImportError:
        print("   ✗ Selenium not installed")
        print("   → Run: pip install selenium")

    # 4. Check port availability
    print("\n4. Debug Port (9222):")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('127.0.0.1', 9222)) == 0:
            print("   ⚠️  Port 9222 is IN USE")
            print("   → Close old Chrome: pkill -f 'remote-debugging-port=9222'")
        else:
            print("   ✓ Port 9222 is available")

    # 5. Check optional dependencies
    print("\n5. Optional Dependencies:")

    # pyperclip
    try:
        import pyperclip
        print("   ✓ pyperclip: Available (clipboard support)")
    except ImportError:
        print("   ⚠️  pyperclip: Not installed (manual URL copy required)")
        print("      This is OK - core functionality will still work")

    # 6. Test Chrome startup
    print("\n6. Test Chrome Startup:")
    print("   Attempting to start Chrome with debug port...")

    try:
        # Try to start Chrome
        test_cmd = [
            chrome_path,
            '--remote-debugging-port=9223',  # Use different port for test
            '--user-data-dir=/tmp/web-fetcher-test',
            '--headless'
        ]

        test_process = subprocess.Popen(
            test_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait a moment
        import time
        time.sleep(2)

        # Check if it started
        if test_process.poll() is None:
            print("   ✓ Chrome can start successfully")
            test_process.terminate()
            test_process.wait()
        else:
            print("   ✗ Chrome failed to start")
            stderr = test_process.stderr.read().decode()
            print(f"   Error: {stderr[:200]}")

    except Exception as e:
        print(f"   ✗ Chrome startup test failed: {e}")

    # 7. Test Selenium attachment
    print("\n7. Selenium Chrome Attachment:")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        # Try to create a simple Chrome instance
        options = Options()
        options.add_argument('--headless')

        print("   Testing Selenium Manager...")
        driver = webdriver.Chrome(options=options)
        driver.quit()
        print("   ✓ Selenium can create Chrome instances")

    except Exception as e:
        print(f"   ✗ Selenium Chrome test failed: {e}")
        print("   This might be a chromedriver issue")

    print("\n" + "=" * 60)
    print("Diagnosis complete!")
    print("\nSummary:")
    print("  - If all checks pass: System ready for manual mode")
    print("  - If Chrome not found: Install or set custom path")
    print("  - If port in use: Close existing Chrome instances")
    print("  - If Selenium fails: Update to 4.6+ for auto driver management")
    print("=" * 60)

# Add to main() function in manual_mode_cli.py
def main():
    parser = argparse.ArgumentParser(
        description='Manual Chrome fallback mode for Web Fetcher'
    )

    # Add diagnose argument
    parser.add_argument('--diagnose', action='store_true',
                       help='Run environment diagnosis')

    parser.add_argument('--url', help='URL to fetch')
    parser.add_argument('--output', help='Save HTML to file')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--config', help='Custom config file path')
    parser.add_argument('--port', type=int, help='Chrome debug port (default: 9222)')

    args = parser.parse_args()

    # Run diagnosis if requested
    if args.diagnose:
        diagnose_environment()
        sys.exit(0)

    # URL is required if not diagnosing
    if not args.url:
        parser.error("--url is required (unless using --diagnose)")

    # ... rest of implementation ...
```

---

## 8. Testing Strategy / 测试策略

### 8.1 Unit Tests / 单元测试

```python
# tests/manual_chrome/test_helper.py

import unittest
import os
import socket
from unittest.mock import Mock, patch, MagicMock
from manual_chrome.helper import ManualChromeHelper, ChromeNotFoundError, PortInUseError

class TestManualChromeHelper(unittest.TestCase):
    """Test ManualChromeHelper functionality"""

    def setUp(self):
        self.config = {
            'chrome': {'debug_port': 9222},
            'ux': {'auto_copy_url': True, 'wait_timeout': 300}
        }
        self.helper = ManualChromeHelper(self.config)

    @patch('os.path.exists')
    def test_validate_chrome_installation(self, mock_exists):
        """Test Chrome validation using os.path.exists"""
        # Test successful validation
        mock_exists.return_value = True
        path = self.helper._validate_chrome_installation()
        self.assertEqual(path, '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')

        # Test missing Chrome
        mock_exists.return_value = False
        with self.assertRaises(ChromeNotFoundError) as ctx:
            self.helper._validate_chrome_installation()

        # Check error message contains helpful instructions
        self.assertIn('config/manual_chrome_config.yaml', str(ctx.exception))

    @patch('socket.socket')
    def test_check_debug_port(self, mock_socket_class):
        """Test debug port availability check"""
        mock_socket = Mock()
        mock_socket_class.return_value.__enter__.return_value = mock_socket

        # Test port available
        mock_socket.connect_ex.return_value = 1  # Port not in use
        self.helper._check_debug_port()  # Should not raise

        # Test port in use
        mock_socket.connect_ex.return_value = 0  # Port in use
        with self.assertRaises(PortInUseError) as ctx:
            self.helper._check_debug_port()

        # Check error message contains solutions
        self.assertIn('pkill', str(ctx.exception))

    @patch('subprocess.Popen')
    @patch('os.path.exists')
    def test_start_chrome_debug_mode(self, mock_exists, mock_popen):
        """Test Chrome starts with correct parameters"""
        mock_exists.return_value = True
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        self.helper._start_chrome_debug_mode(chrome_path)

        # Verify Chrome started with macOS path
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]

        # Check Chrome binary path
        self.assertEqual(args[0], chrome_path)
        # Check debug port
        self.assertIn('--remote-debugging-port=9222', args)

    def test_cleanup_logic(self):
        """Test cleanup always quits driver"""
        # Mock driver
        mock_driver = Mock()
        self.helper.driver = mock_driver

        # Mock Chrome process
        mock_process = Mock()
        self.helper.chrome_process = mock_process

        # Test cleanup without force - driver quit, Chrome stays
        self.helper._cleanup(force=False)
        mock_driver.quit.assert_called_once()
        mock_process.terminate.assert_not_called()
        self.assertIsNone(self.helper.driver)

        # Reset mocks
        self.helper.driver = mock_driver
        self.helper.chrome_process = mock_process
        mock_driver.reset_mock()
        mock_process.reset_mock()

        # Test cleanup with force - both cleaned
        self.helper._cleanup(force=True)
        mock_driver.quit.assert_called_once()
        mock_process.terminate.assert_called_once()
        self.assertIsNone(self.helper.driver)
        self.assertIsNone(self.helper.chrome_process)

    @patch('selenium.webdriver.Chrome')
    def test_selenium_manager_usage(self, mock_chrome):
        """Test that Selenium Manager is used (no chromedriver path)"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        mock_driver.page_source = '<html>Test</html>'
        mock_driver.current_url = 'https://example.com'
        mock_driver.title = 'Test'

        html = self.helper._attach_and_extract()

        # Verify Chrome was called without chromedriver_executable_path
        call_args = mock_chrome.call_args
        # Should only have options, no executable_path
        self.assertEqual(len(call_args[0]), 0)  # No positional args
        self.assertIn('options', call_args[1])
        self.assertNotIn('executable_path', call_args[1])

    @patch('pyperclip.copy')
    def test_graceful_clipboard_fallback(self, mock_copy):
        """Test clipboard fails gracefully if pyperclip unavailable"""
        # Test successful copy
        self.helper._prepare_user_intervention('https://example.com', None)
        mock_copy.assert_called_once()

        # Test import error handling
        mock_copy.side_effect = ImportError("No module named 'pyperclip'")
        # Should not raise, just print warning
        try:
            self.helper._prepare_user_intervention('https://example.com', None)
        except ImportError:
            self.fail("Should handle ImportError gracefully")
```

---

## 9. Implementation Roadmap / 实施路线图

### Phase 1: Core Infrastructure (4-6 hours)
**Objective**: Build the foundation for manual Chrome integration

#### Tasks:
- [ ] Create directory structure: `/manual_chrome/`
- [ ] Implement `ManualChromeHelper` class with macOS-focused functionality
- [ ] Implement `FallbackDetector` for trigger logic
- [ ] Create `manual_chrome_config.yaml` configuration file (macOS defaults)
- [ ] Add Chrome validation with os.path.exists
- [ ] Add port availability check
- [ ] Implement Selenium Manager usage (no manual driver)

#### Validation:
- Chrome path validation works correctly
- Port availability check prevents conflicts
- Selenium Manager auto-downloads chromedriver
- Can attach to Chrome and extract content

### Phase 2: Integration (2-3 hours)
**Objective**: Integrate manual fallback into main fetcher

#### Tasks:
- [ ] Modify `webfetcher.py` to include fallback logic
- [ ] Add configuration loading with macOS defaults
- [ ] Integrate detection logic
- [ ] Test on known problematic sites
- [ ] Add metrics tracking

#### Validation:
- Fallback triggers correctly on failures
- No impact on successful automated fetches
- Clear error messages when Chrome not found
- Metrics properly recorded

### Phase 3: User Experience (2-3 hours)
**Objective**: Enhance user interaction with graceful fallbacks

#### Tasks:
- [ ] Implement simplified `UIManager` class
- [ ] Add clipboard with try/except fallback
- [ ] Add optional OS notifications
- [ ] Create challenge-specific guidance
- [ ] Ensure core works without optional dependencies

#### Validation:
- Clear instructions always displayed
- Works without pyperclip installed
- Helpful error messages guide users
- User can complete flow in < 30 seconds

### Phase 4: Diagnostic Tool (1-2 hours)
**Objective**: Create diagnostic capability

#### Tasks:
- [ ] Implement `--diagnose` flag in CLI
- [ ] Check Chrome installation
- [ ] Check Selenium version and Manager support
- [ ] Check port availability
- [ ] Test Chrome startup
- [ ] Check optional dependencies

#### Validation:
- Diagnosis identifies all common issues
- Provides actionable solutions
- Works on fresh macOS install

### Phase 5: Testing & Documentation (2-3 hours)
**Objective**: Ensure reliability and maintainability

#### Tasks:
- [ ] Write comprehensive unit tests
- [ ] Create integration tests
- [ ] Test on 5+ different challenge types
- [ ] Test without optional dependencies
- [ ] Write user documentation
- [ ] Create troubleshooting guide

#### Validation:
- All tests passing
- Works with only required dependencies
- Documentation complete
- Successfully tested on problematic sites

---

## 10. Risk Assessment / 风险评估

| Change | Benefit | Risk | Mitigation |
|--------|---------|------|------------|
| macOS-only | Simpler, focused | Can't use on Linux/Windows | Document limitation, easy to extend later |
| os.path.exists | More reliable | None | ✓ Accept |
| Selenium Manager | Less config | Requires newer Selenium (4.6+) | Check version on startup |
| Always quit driver | Better cleanup | None | ✓ Accept |
| Optional dependencies | More robust | Reduced UX without them | Acceptable - core functionality preserved |

---

## 11. Success Metrics / 成功指标

### Functional Metrics:
- [ ] **100% Fallback Rate**: Triggers for all failed automated fetches
- [ ] **95% Success Rate**: Successfully extracts content when user completes navigation
- [ ] **< 30 seconds**: Average time for user to complete manual intervention
- [ ] **Zero Impact**: No performance degradation for successful automated fetches

### Quality Metrics:
- [ ] **80%+ Test Coverage**: Comprehensive unit and integration tests
- [ ] **< 5 seconds**: Chrome startup time
- [ ] **< 2 seconds**: Content extraction time after user confirmation
- [ ] **100% macOS Support**: Works reliably on macOS

### User Experience Metrics:
- [ ] **Clear Error Messages**: Users understand issues without confusion
- [ ] **Minimal Configuration**: Works with zero config for most users
- [ ] **Graceful Degradation**: Works without optional dependencies
- [ ] **Helpful Diagnostics**: --diagnose identifies and explains all issues

---

## Document Metadata

**Version**: 2.0
**Created**: 2025-10-09
**Updated**: 2025-10-09 - Applied macOS simplifications
**Author**: Architecture Team
**Status**: READY FOR IMPLEMENTATION
**Review**: Approved for macOS-focused implementation

---

## Summary of Key Changes (v2.0)

1. **Platform**: Focused on macOS only, removed Linux/Windows complexity
2. **Chrome Detection**: Uses `os.path.exists()` instead of `which` command
3. **Selenium**: Leverages Selenium Manager for automatic driver management
4. **Cleanup**: Always quits driver, Chrome termination only when forced
5. **Dependencies**: Optional features wrapped in try/except for graceful fallback
6. **Diagnostics**: Added comprehensive `--diagnose` mode for troubleshooting
7. **Configuration**: Simplified with macOS defaults and optional chrome_path

---

*End of Document*