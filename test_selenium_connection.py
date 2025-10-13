#!/usr/bin/env python3
"""
Test Selenium connection with version checking

Author: Cody (Claude Code)
Date: 2025-10-13
Task: Task-011 Phase 2
"""

import logging
import sys
import os

# Configure logging to show INFO and above
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium_fetcher import SeleniumFetcher

def test_connection():
    """Test Selenium connection with version checking"""
    print("\n" + "="*80)
    print("Testing Selenium Connection with Version Checking")
    print("="*80 + "\n")

    try:
        # Initialize fetcher
        fetcher = SeleniumFetcher()

        print("Step 1: Checking if Selenium is available...")
        if not fetcher.is_available():
            print("✗ Selenium not available")
            return

        print("✓ Selenium is available\n")

        print("Step 2: Attempting connection to Chrome debug session...")
        success, message = fetcher.connect_to_chrome()

        if success:
            print("\n✓ Connection successful!")
            print(f"Message: {message}")

            # Get version info
            version_info = fetcher.get_version_info()
            print("\nVersion Information:")
            print(f"  Chrome: {version_info.get('chrome_version', 'unknown')}")
            print(f"  ChromeDriver: {version_info.get('chromedriver_version', 'unknown')}")
            print(f"  Compatible: {version_info.get('version_compatible', 'unknown')}")

        else:
            print("\n✗ Connection failed")
            print(f"Message: {message}")

        # Cleanup
        fetcher.cleanup()

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()
