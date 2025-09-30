#!/usr/bin/env python3
"""
Simple test to verify Selenium can connect to Chrome with proper flags
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def test_connection():
    print("Testing Selenium connection to Chrome debug port...")

    opts = Options()
    opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    try:
        print("Connecting...")
        start = time.time()
        driver = webdriver.Chrome(options=opts)
        elapsed = time.time() - start

        print(f"✅ SUCCESS! Connected in {elapsed:.2f} seconds")

        # Get browser info
        caps = driver.capabilities
        print(f"Chrome: {caps.get('browserVersion')}")
        print(f"ChromeDriver: {caps.get('chrome',{}).get('chromedriverVersion','').split()[0]}")

        # Test navigation
        driver.get("https://example.com")
        print(f"Page title: {driver.title}")

        driver.quit()
        print("✅ All tests passed!")
        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

if __name__ == "__main__":
    import sys
    sys.exit(0 if test_connection() else 1)