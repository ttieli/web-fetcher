#!/usr/bin/env python3
"""
Restart Chrome with proper debugging flags
"""

import subprocess
import time
import json
import urllib.request

def kill_chrome():
    """Kill existing Chrome processes"""
    print("Killing existing Chrome processes...")
    subprocess.run(["pkill", "-f", "Google Chrome"], capture_output=True)
    time.sleep(2)

def start_chrome_with_flags():
    """Start Chrome with proper debugging flags"""
    chrome_cmd = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "--remote-debugging-port=9222",
        "--user-data-dir=/Users/tieli/.chrome-wf",
        "--no-first-run",
        "--no-default-browser-check",
        "--remote-allow-origins=*",  # Important for remote connections
        "--enable-automation",        # Important for automation
        "--disable-blink-features=AutomationControlled"  # Prevent detection
    ]

    print("Starting Chrome with proper flags:")
    print(f"  Command: {' '.join(chrome_cmd)}")

    # Start Chrome in background
    process = subprocess.Popen(chrome_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Chrome started with PID: {process.pid}")

    # Wait for Chrome to be ready
    print("Waiting for Chrome to be ready...")
    for i in range(10):
        try:
            response = urllib.request.urlopen("http://localhost:9222/json/version")
            version_info = json.loads(response.read())
            print(f"✅ Chrome is ready: {version_info.get('Browser')}")
            return True
        except:
            time.sleep(1)

    print("❌ Chrome failed to start properly")
    return False

def test_selenium_connection():
    """Test Selenium connection after Chrome restart"""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    print("\n" + "="*60)
    print("Testing Selenium Connection")
    print("="*60)

    opts = Options()
    opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    try:
        print("Attempting to connect...")
        driver = webdriver.Chrome(options=opts)
        print("✅ Connection SUCCESSFUL!")

        caps = driver.capabilities
        print(f"Chrome: {caps.get('browserVersion')}")
        print(f"ChromeDriver: {caps.get('chrome',{}).get('chromedriverVersion','').split()[0]}")

        # Test navigation
        print("\nTesting navigation...")
        driver.get("http://example.com")
        print(f"Current URL: {driver.current_url}")
        print(f"Page Title: {driver.title}")

        driver.quit()
        print("✅ All tests passed!")
        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    print("Chrome Restart and Connection Test")
    print("="*60)

    # Step 1: Kill existing Chrome
    kill_chrome()

    # Step 2: Start Chrome with proper flags
    if start_chrome_with_flags():
        # Step 3: Test Selenium connection
        test_selenium_connection()
    else:
        print("Failed to start Chrome properly")