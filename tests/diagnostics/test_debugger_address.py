#!/usr/bin/env python3
"""
Test Selenium connection to Chrome via debuggerAddress
Tests if the connection hangs when using debuggerAddress option
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import signal
import sys
import os
import time
from datetime import datetime

def timeout_handler(signum, frame):
    print(f"❌ TIMEOUT: Connection hung after 30 seconds!")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sys.exit(1)

def test_debugger_address_connection():
    """Test connecting to existing Chrome instance via debuggerAddress"""

    print("="*60)
    print("Testing debuggerAddress Connection")
    print("="*60)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Set 30-second timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)

    try:
        # Configure Chrome options
        opts = Options()
        opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

        # Get ChromeDriver path - use system chromedriver
        chromedriver_path = "/usr/local/bin/chromedriver"

        if not os.path.exists(chromedriver_path):
            print(f"❌ ChromeDriver not found at: {chromedriver_path}")
            sys.exit(1)

        service = Service(executable_path=chromedriver_path)

        print("\nAttempting to connect to Chrome at 127.0.0.1:9222...")
        print("Using ChromeDriver:", chromedriver_path)
        print("\nInitializing WebDriver...")

        # Try to connect - THIS IS WHERE IT MIGHT HANG
        start_time = time.time()
        driver = webdriver.Chrome(service=service, options=opts)
        connect_time = time.time() - start_time

        # Cancel timeout if successful
        signal.alarm(0)

        print(f"\n✅ Connection SUCCESSFUL!")
        print(f"Connection time: {connect_time:.2f} seconds")

        # Get browser information
        caps = driver.capabilities
        print("\n" + "="*40)
        print("Browser Information:")
        print("="*40)
        print(f"Chrome Version: {caps.get('browserVersion', 'Unknown')}")

        chrome_info = caps.get('chrome', {})
        chromedriver_version = chrome_info.get('chromedriverVersion', 'Unknown')
        if chromedriver_version != 'Unknown':
            chromedriver_version = chromedriver_version.split(' ')[0]
        print(f"ChromeDriver Version: {chromedriver_version}")

        # Try to get current URL
        try:
            current_url = driver.current_url
            print(f"Current URL: {current_url}")
        except Exception as e:
            print(f"Could not get current URL: {e}")

        # Try to get title
        try:
            title = driver.title
            print(f"Page Title: {title}")
        except Exception as e:
            print(f"Could not get page title: {e}")

        print("\nClosing connection...")
        driver.quit()
        print("✅ Connection closed successfully")

        return True

    except Exception as e:
        signal.alarm(0)  # Cancel timeout
        print(f"\n❌ Connection FAILED!")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")

        # Check if it's a timeout-related error
        if "timeout" in str(e).lower():
            print("\n⚠️  This appears to be a timeout issue!")
            print("The driver is unable to connect to the existing Chrome instance.")

        return False

    finally:
        signal.alarm(0)  # Ensure timeout is cancelled

def test_new_instance_connection():
    """Test creating a new Chrome instance (for comparison)"""

    print("\n" + "="*60)
    print("Testing New Chrome Instance (Control Test)")
    print("="*60)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")

        chromedriver_path = "/usr/local/bin/chromedriver"
        service = Service(executable_path=chromedriver_path)

        print("\nStarting new Chrome instance...")
        start_time = time.time()
        driver = webdriver.Chrome(service=service, options=opts)
        connect_time = time.time() - start_time

        print(f"\n✅ New instance created SUCCESSFULLY!")
        print(f"Creation time: {connect_time:.2f} seconds")

        caps = driver.capabilities
        print(f"Chrome Version: {caps.get('browserVersion', 'Unknown')}")

        driver.quit()
        print("✅ Instance closed successfully")

        return True

    except Exception as e:
        print(f"\n❌ Failed to create new instance!")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Chrome Selenium Connection Test")
    print("================================\n")

    # First test: Connect to existing Chrome via debuggerAddress
    print("Test 1: debuggerAddress Connection")
    debugger_result = test_debugger_address_connection()

    # Second test: Create new instance (control)
    print("\n" + "="*60)
    print("\nTest 2: New Instance Creation (Control)")
    new_instance_result = test_new_instance_connection()

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"debuggerAddress Connection: {'✅ PASSED' if debugger_result else '❌ FAILED'}")
    print(f"New Instance Creation: {'✅ PASSED' if new_instance_result else '❌ FAILED'}")

    if not debugger_result and new_instance_result:
        print("\n⚠️  DIAGNOSIS: The issue is specifically with debuggerAddress connection!")
        print("New instances work fine, but connecting to existing Chrome fails.")
        print("\nPossible causes:")
        print("1. Chrome needs to be started with specific flags")
        print("2. Security/firewall blocking local connections")
        print("3. ChromeDriver/Chrome version mismatch for debug connections")
        print("4. macOS security policies preventing attachment")

    sys.exit(0 if (debugger_result and new_instance_result) else 1)