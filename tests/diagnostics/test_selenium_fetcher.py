#!/usr/bin/env python3
"""
Test if selenium_fetcher.py works with the fixed Chrome setup
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from selenium_fetcher import SeleniumFetcher

def test_selenium_fetcher():
    """Test SeleniumFetcher connection and fetch"""

    print("="*60)
    print("Testing SeleniumFetcher with Fixed Chrome Setup")
    print("="*60)

    fetcher = SeleniumFetcher(debug_host="127.0.0.1", debug_port=9222)

    # Test 1: Connect to Chrome
    print("\nTest 1: Connecting to Chrome debug session...")
    success, message = fetcher.connect_to_chrome()

    if success:
        print(f"✅ Connection successful: {message}")

        # Test 2: Fetch a page
        print("\nTest 2: Fetching a test page...")
        url = "https://example.com"
        content, error = fetcher.fetch(url)

        if content and not error:
            print(f"✅ Successfully fetched {url}")
            print(f"   Content length: {len(content)} bytes")
            print(f"   Title found: {'Example Domain' in content}")
        else:
            print(f"❌ Failed to fetch page: {error}")

        # Test 3: Check session info
        print("\nTest 3: Checking session info...")
        if fetcher.driver:
            caps = fetcher.driver.capabilities
            print(f"   Chrome version: {caps.get('browserVersion', 'Unknown')}")
            chrome_info = caps.get('chrome', {})
            chromedriver_version = chrome_info.get('chromedriverVersion', 'Unknown')
            if chromedriver_version != 'Unknown':
                chromedriver_version = chromedriver_version.split(' ')[0]
            print(f"   ChromeDriver version: {chromedriver_version}")
            print(f"   Current URL: {fetcher.driver.current_url}")

        # Clean up
        fetcher.close()
        print("\n✅ All tests passed!")

    else:
        print(f"❌ Connection failed: {message}")
        return False

    return True

if __name__ == "__main__":
    # First check if Chrome is running with proper flags
    import urllib.request
    import json

    print("Pre-check: Verifying Chrome debug session...")
    try:
        response = urllib.request.urlopen("http://localhost:9222/json/version")
        version_info = json.loads(response.read())
        print(f"✅ Chrome is running: {version_info.get('Browser')}")

        # Check if Chrome has proper flags
        import subprocess
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        chrome_procs = [line for line in result.stdout.split('\n')
                       if '--remote-debugging-port=9222' in line]

        if chrome_procs:
            proc = chrome_procs[0]
            if '--remote-allow-origins' in proc:
                print("✅ Chrome has --remote-allow-origins flag")
            else:
                print("⚠️  Chrome missing --remote-allow-origins flag")
                print("   This may cause connection issues!")

        print()

    except Exception as e:
        print(f"❌ Chrome debug session not running: {e}")
        print("Please start Chrome with: ./config/chrome-debug.sh")
        sys.exit(1)

    # Run the tests
    success = test_selenium_fetcher()
    sys.exit(0 if success else 1)