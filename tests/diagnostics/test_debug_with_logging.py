#!/usr/bin/env python3
"""
Test debuggerAddress connection with verbose logging
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import os
import time
import threading
import subprocess

def test_with_verbose_logging():
    """Test debuggerAddress with ChromeDriver verbose logging"""

    print("="*60)
    print("debuggerAddress Test with Verbose Logging")
    print("="*60)

    # Create log directory
    log_dir = "/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher/logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"chromedriver_{int(time.time())}.log")

    print(f"ChromeDriver log will be saved to: {log_file}")

    # Configure Chrome options
    opts = Options()
    opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    # Configure service with verbose logging
    service = Service(
        executable_path="/usr/local/bin/chromedriver",
        log_path=log_file,
        service_args=["--verbose", "--log-level=ALL"]
    )

    print("\nStarting connection attempt with 10-second timeout...")

    # Use threading to implement timeout
    driver = None
    error = None

    def connect():
        nonlocal driver, error
        try:
            driver = webdriver.Chrome(service=service, options=opts)
        except Exception as e:
            error = e

    thread = threading.Thread(target=connect)
    thread.start()
    thread.join(timeout=10)

    if thread.is_alive():
        print("\n❌ Connection HUNG after 10 seconds!")
        print("\nAttempting to kill ChromeDriver process...")

        # Find and kill chromedriver
        subprocess.run(["pkill", "-f", "chromedriver"], capture_output=True)

        print("\nChecking last 50 lines of ChromeDriver log:")
        print("-"*40)

        # Read and display log
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-50:]:  # Last 50 lines
                    print(line.strip())

        return False

    if error:
        print(f"\n❌ Connection failed with error: {error}")
        return False

    if driver:
        print("\n✅ Connection successful!")
        driver.quit()
        return True

    print("\n❌ Unknown error occurred")
    return False

def test_chrome_remote_interface():
    """Test if Chrome DevTools Protocol is accessible"""

    print("\n" + "="*60)
    print("Chrome DevTools Protocol Test")
    print("="*60)

    import json
    import urllib.request

    try:
        # Test /json/version endpoint
        response = urllib.request.urlopen("http://localhost:9222/json/version")
        version_info = json.loads(response.read())
        print("✅ DevTools Protocol is accessible")
        print(f"Browser: {version_info.get('Browser')}")
        print(f"Protocol Version: {version_info.get('Protocol-Version')}")

        # Test /json/list endpoint
        response = urllib.request.urlopen("http://localhost:9222/json/list")
        tabs = json.loads(response.read())
        print(f"\nOpen tabs: {len(tabs)}")

        for i, tab in enumerate(tabs[:3]):  # Show first 3 tabs
            print(f"  Tab {i+1}: {tab.get('title', 'Untitled')[:50]}")

        return True

    except Exception as e:
        print(f"❌ Failed to access DevTools Protocol: {e}")
        return False

def check_chrome_startup_flags():
    """Check how Chrome was started"""

    print("\n" + "="*60)
    print("Chrome Process Analysis")
    print("="*60)

    result = subprocess.run(
        ["ps", "aux"],
        capture_output=True,
        text=True
    )

    chrome_processes = [line for line in result.stdout.split('\n')
                        if 'Google Chrome' in line or 'chrome' in line.lower()]

    for proc in chrome_processes:
        if '--remote-debugging-port' in proc:
            print("Found Chrome with debugging port:")
            # Extract just the command part
            parts = proc.split()
            if len(parts) > 10:
                cmd_start = 10
                cmd = ' '.join(parts[cmd_start:])
                print(f"  Command: {cmd[:200]}")

                # Check for important flags
                if '--remote-allow-origins' in cmd:
                    print("  ✅ Has --remote-allow-origins flag")
                else:
                    print("  ⚠️  Missing --remote-allow-origins flag")

                if '--enable-automation' in cmd:
                    print("  ✅ Has --enable-automation flag")
                else:
                    print("  ⚠️  Missing --enable-automation flag")
            break
    else:
        print("❌ No Chrome process found with --remote-debugging-port")

if __name__ == "__main__":
    # Test 1: Check Chrome startup
    check_chrome_startup_flags()

    # Test 2: Check DevTools Protocol
    test_chrome_remote_interface()

    # Test 3: Try connection with logging
    test_with_verbose_logging()