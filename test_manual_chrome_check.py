#!/usr/bin/env python3
"""
Test: Check what tabs are open and get their current state
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def check_chrome_tabs():
    """Connect and inspect what's in the browser"""
    print("=" * 80)
    print("Checking Chrome Tabs and State")
    print("=" * 80)

    options = Options()
    options.debugger_address = "127.0.0.1:9222"

    driver = webdriver.Chrome(options=options)

    try:
        # Get all window handles
        handles = driver.window_handles
        print(f"\nFound {len(handles)} window(s)")

        for i, handle in enumerate(handles):
            driver.switch_to.window(handle)
            print(f"\n--- Window {i+1} ---")
            print(f"Title: {driver.title}")
            print(f"URL: {driver.current_url}")
            print(f"Page source length: {len(driver.page_source)} bytes")

        # Switch back to first window
        driver.switch_to.window(handles[0])

        print(f"\n{'=' * 80}")
        print("Now let's try to manually navigate in the FIRST window")
        print("=" * 80)

        url = "https://www.cebbank.com.cn/site/zhpd/zxgg35/cgjggg/263565922/index.html"
        print(f"\n1. Current URL: {driver.current_url}")
        print(f"2. Navigating to: {url}")

        driver.get(url)
        print(f"3. Navigation command sent")

        # Check immediately
        print(f"4. Immediate check - Title: {driver.title}")
        print(f"5. Immediate check - URL: {driver.current_url}")

        # Wait and check progress
        for i in range(5):
            time.sleep(3)
            print(f"\n--- After {(i+1)*3} seconds ---")
            print(f"   Title: {driver.title}")
            print(f"   URL: {driver.current_url}")
            print(f"   Page source: {len(driver.page_source)} bytes")

            # Check if we can get network state
            try:
                ready_state = driver.execute_script("return document.readyState;")
                print(f"   Ready state: {ready_state}")
            except:
                print(f"   Ready state: ERROR")

        # Final check
        print(f"\n{'=' * 80}")
        print("FINAL STATE")
        print(f"{'=' * 80}")
        page_source = driver.page_source
        print(f"Page source: {len(page_source)} bytes")
        print(f"\nFirst 500 chars:")
        print(page_source[:500])

        # Screenshot
        screenshot = '/tmp/chrome_manual_check.png'
        driver.save_screenshot(screenshot)
        print(f"\nScreenshot: {screenshot}")

        # Check console logs
        try:
            logs = driver.get_log('browser')
            if logs:
                print(f"\n{'=' * 80}")
                print("BROWSER CONSOLE LOGS")
                print(f"{'=' * 80}")
                for log in logs[:20]:  # Show first 20 logs
                    print(f"{log['level']}: {log['message']}")
        except:
            print("\nCouldn't retrieve console logs")

    finally:
        print(f"\n{'=' * 80}")
        print("Keeping browser open for manual inspection")
        print(f"{'=' * 80}")

if __name__ == '__main__':
    check_chrome_tabs()
