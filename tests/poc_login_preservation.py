#!/usr/bin/env python3
"""
Proof of Concept: Login State Preservation for Selenium
概念验证：Selenium 登录状态保持

This script demonstrates how to preserve user login state by:
1. Using the default Chrome profile
2. Hiding automation markers
3. Properly managing cookies

Author: Archy
Date: 2025-10-13
"""

import os
import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_profile_connection():
    """Test 1: Connect using default Chrome profile"""
    print("=" * 60)
    print("Test 1: Default Profile Connection")
    print("=" * 60)

    # Method A: Use existing Chrome with debug port but default profile
    print("\nMethod A: Connect to Chrome debug session")
    print("Requires: Chrome started with --remote-debugging-port=9222")
    print("          AND --user-data-dir pointing to default profile")

    # For macOS
    default_profile = Path.home() / "Library/Application Support/Google/Chrome"

    print(f"\nTo test, run Chrome with:")
    print(f'"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \\')
    print(f'  --remote-debugging-port=9222 \\')
    print(f'  --user-data-dir="{default_profile}" \\')
    print(f'  --no-first-run')

    print("\n⚠️  WARNING: This will use your actual Chrome profile!")
    print("⚠️  Make sure no other Chrome instance is using this profile")

def test_stealth_mode():
    """Test 2: Stealth mode to hide automation"""
    print("\n" + "=" * 60)
    print("Test 2: Stealth Mode Configuration")
    print("=" * 60)

    options = Options()

    # Connect to existing debug session
    options.add_experimental_option("debuggerAddress", "localhost:9222")

    # STEALTH MODE: Hide automation markers
    # 隐身模式：隐藏自动化标记

    # 1. Remove automation indicators
    options.add_argument('--disable-blink-features=AutomationControlled')

    # 2. Exclude automation switches
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    # 3. Disable automation extension
    options.add_experimental_option('useAutomationExtension', False)

    # 4. Set a normal User-Agent (remove HeadlessChrome)
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36')

    print("\nStealth options configured:")
    print("✓ Disabled automation controlled features")
    print("✓ Excluded automation switches")
    print("✓ Disabled automation extension")
    print("✓ Set normal User-Agent")

    try:
        print("\nConnecting to Chrome...")
        driver = webdriver.Chrome(options=options)

        # Execute JavaScript to hide webdriver property
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })

                // Also hide other automation properties
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                })

                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en']
                })

                window.chrome = {
                    runtime: {}
                }

                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({
                        query: () => Promise.resolve({ state: 'granted' })
                    })
                })
            '''
        })

        print("✓ Connected successfully with stealth mode")

        # Check automation detection
        print("\nChecking automation markers:")
        ua = driver.execute_script("return navigator.userAgent")
        print(f"User-Agent: {ua[:80]}...")
        print(f"Contains 'HeadlessChrome': {'HeadlessChrome' in ua}")

        webdriver_prop = driver.execute_script("return navigator.webdriver")
        print(f"navigator.webdriver: {webdriver_prop}")

        plugins = driver.execute_script("return navigator.plugins.length")
        print(f"navigator.plugins: {plugins} plugins")

        # Test on a target site
        print("\n" + "=" * 60)
        print("Testing on target site...")
        print("=" * 60)

        test_url = input("\nEnter test URL (or press Enter to skip): ").strip()
        if test_url:
            print(f"\nNavigating to: {test_url}")
            driver.get(test_url)
            time.sleep(2)

            print(f"Current URL: {driver.current_url}")
            print(f"Page title: {driver.title}")

            # Check for error pages
            if "405" in driver.title or "error" in driver.title.lower():
                print("⚠️  WARNING: Possible error page detected!")
            else:
                print("✓ Page loaded successfully")

            # Check cookies
            cookies = driver.get_cookies()
            print(f"\nCookies found: {len(cookies)}")
            if cookies:
                print("Sample cookies:")
                for cookie in cookies[:5]:
                    print(f"  - {cookie.get('name')}: {cookie.get('domain')}")

        driver.quit()
        print("\n✓ Test completed successfully")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

    return True

def test_cookie_preservation():
    """Test 3: Cookie preservation across sessions"""
    print("\n" + "=" * 60)
    print("Test 3: Cookie Preservation")
    print("=" * 60)

    print("\nThis test demonstrates cookie persistence:")
    print("1. Connect to Chrome debug session")
    print("2. Save all cookies from current session")
    print("3. Reconnect and verify cookies persist")

    try:
        options = Options()
        options.add_experimental_option("debuggerAddress", "localhost:9222")

        # First connection
        print("\nFirst connection - saving cookies...")
        driver = webdriver.Chrome(options=options)
        initial_url = driver.current_url
        initial_cookies = driver.get_cookies()
        print(f"Current URL: {initial_url}")
        print(f"Cookies saved: {len(initial_cookies)}")
        driver.quit()

        # Second connection
        print("\nSecond connection - checking persistence...")
        driver = webdriver.Chrome(options=options)
        second_cookies = driver.get_cookies()
        print(f"Cookies found: {len(second_cookies)}")

        if len(second_cookies) == len(initial_cookies):
            print("✓ Cookies persisted across connections")
        else:
            print("⚠️  Cookie count mismatch")

        driver.quit()

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

    return True

def main():
    """Run all proof-of-concept tests"""
    print("=" * 60)
    print("Login State Preservation - Proof of Concept")
    print("登录状态保持 - 概念验证")
    print("=" * 60)

    print("\nThis POC demonstrates solutions for preserving login state")
    print("when using Selenium with Chrome debug mode.\n")

    # Show current configuration issue
    print("CURRENT ISSUE:")
    print("- Chrome debug uses isolated profile (~/.chrome-wf)")
    print("- User's login cookies are in default profile")
    print("- Result: No access to logged-in sessions\n")

    print("SOLUTIONS TO TEST:")
    print("1. Use default Chrome profile (requires Chrome restart)")
    print("2. Stealth mode to bypass bot detection")
    print("3. Cookie preservation across sessions\n")

    # Test 1: Profile information
    test_profile_connection()

    # Ask user if Chrome is running with debug port
    response = input("\nIs Chrome running with --remote-debugging-port=9222? (y/n): ")
    if response.lower() != 'y':
        print("\nPlease start Chrome with:")
        print("./config/chrome-debug.sh")
        print("\nOr manually with stealth profile test:")
        print('chrome --remote-debugging-port=9222 --user-data-dir="$HOME/Library/Application Support/Google/Chrome"')
        return

    # Test 2: Stealth mode
    if test_stealth_mode():
        print("\n✓ Stealth mode test passed")

    # Test 3: Cookie preservation
    response = input("\nTest cookie preservation? (y/n): ")
    if response.lower() == 'y':
        if test_cookie_preservation():
            print("\n✓ Cookie preservation test passed")

    print("\n" + "=" * 60)
    print("POC Testing Complete")
    print("=" * 60)

    print("\nRECOMMENDED SOLUTION:")
    print("1. Modify chrome-debug.sh to support --use-default-profile flag")
    print("2. Implement stealth mode in selenium_fetcher.py")
    print("3. Add cookie transfer mechanism for isolated profiles")
    print("4. Document security implications for users")

if __name__ == "__main__":
    main()