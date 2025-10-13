#!/usr/bin/env python3
"""
Quick test script for browser notification functionality
"""
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Import the selenium fetcher
from selenium_fetcher import SeleniumFetcher

def test_notification():
    """Test the browser notification feature"""
    print("Testing browser notification feature...")

    # Create a fetcher instance
    fetcher = SeleniumFetcher()

    # Check if available
    if not fetcher.is_available():
        print("ERROR: Selenium is not available")
        return False

    # Try to connect to Chrome
    print("Connecting to Chrome debug session...")
    success, message = fetcher.connect_to_chrome()

    if not success:
        print(f"ERROR: Failed to connect to Chrome: {message}")
        return False

    print(f"SUCCESS: {message}")
    print("Browser notification should have been displayed")

    # Keep browser open for a moment to see the notification
    import time
    print("Waiting 5 seconds to inspect the notification...")
    time.sleep(5)

    # Cleanup
    if fetcher.driver:
        fetcher.driver.quit()

    return True

if __name__ == "__main__":
    try:
        result = test_notification()
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
