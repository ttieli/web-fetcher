#!/usr/bin/env python3
"""
Test CDP connection with SSL bypass
Handle certificate errors programmatically
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sys

def test_cdp_with_ssl_bypass():
    """Connect to existing Chrome and handle SSL errors"""
    print("=" * 80)
    print("Testing CDP Connection with SSL Error Bypass")
    print("=" * 80)
    print("\nConnecting to Chrome debug session on port 9222...")

    options = Options()
    options.debugger_address = "127.0.0.1:9222"

    # These options might help but won't work fully with debugger_address
    # because we're connecting to existing Chrome, not launching new one
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        print(f"✓ Connected successfully")

        # Navigate to CEB Bank test URL
        url = "https://www.cebbank.com.cn/site/zhpd/zxgg35/cgjggg/263565922/index.html"
        print(f"\n{'=' * 80}")
        print(f"Navigating to CEB Bank URL:")
        print(f"  {url}")
        print(f"{'=' * 80}")
        driver.get(url)

        # Wait a bit for initial load
        time.sleep(3)

        # Check if we hit SSL error page
        page_title = driver.title
        print(f"\nInitial page title: {page_title}")

        if '隐私设置错误' in page_title or 'ERR_CERT' in driver.page_source:
            print("\n⚠️  SSL Certificate Error detected!")
            print("Attempting to bypass using CDP commands...")

            # Try to bypass using CDP sendCommand
            try:
                # This tells Chrome to ignore certificate errors for this session
                driver.execute_cdp_cmd('Security.setIgnoreCertificateErrors', {'ignore': True})
                print("✓ Certificate error bypass enabled via CDP")

                # Reload the page
                print("Reloading page...")
                driver.get(url)
                time.sleep(5)

            except Exception as e:
                print(f"✗ CDP bypass failed: {e}")
                print("\nTrying alternative: clicking through the warning...")

                # Alternative: try to find and click the "Advanced" button
                try:
                    # Look for the "Advanced" button (高级)
                    advanced_button = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.ID, "details-button"))
                    )
                    advanced_button.click()
                    print("✓ Clicked 'Advanced' button")
                    time.sleep(1)

                    # Look for the "Proceed" link
                    proceed_link = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.ID, "proceed-link"))
                    )
                    proceed_link.click()
                    print("✓ Clicked 'Proceed' link")
                    time.sleep(5)

                except Exception as e2:
                    print(f"✗ Click-through bypass failed: {e2}")

        # Wait for page load
        print("\nWaiting for page to fully load...")
        time.sleep(10)

        # Extract content
        print("\nExtracting content...")
        page_source = driver.page_source
        body_text = driver.execute_script("return document.body.innerText;")
        page_title = driver.title
        current_url = driver.current_url

        print(f"\n{'=' * 80}")
        print(f"EXTRACTION RESULTS")
        print(f"{'=' * 80}")
        print(f"Page Title: {page_title}")
        print(f"Current URL: {current_url}")
        print(f"Page source length: {len(page_source):,} bytes")
        print(f"Body text length: {len(body_text):,} bytes")

        # Show preview
        print(f"\n{'=' * 80}")
        print(f"CONTENT PREVIEW - First 1000 characters")
        print(f"{'=' * 80}")
        print(f"\n--- Body Text ---")
        print(body_text[:1000])

        # Analysis
        is_empty = len(page_source) < 100
        is_error = '隐私设置错误' in page_title or 'ERR_' in page_title
        has_substantial_content = len(body_text) > 1000
        has_bank_content = '光大银行' in page_source or '中国光大银行' in page_source or '采购结果公告' in page_source

        # Take screenshot
        screenshot_path = '/tmp/cebbank_cdp_ssl_bypass_test.png'
        driver.save_screenshot(screenshot_path)
        print(f"\n{'=' * 80}")
        print(f"Screenshot saved: {screenshot_path}")
        print(f"{'=' * 80}")

        print(f"\n{'=' * 80}")
        print(f"ANALYSIS")
        print(f"{'=' * 80}")
        print(f"Is Empty: {is_empty}")
        print(f"Is Error Page: {is_error}")
        print(f"Has Substantial Content: {has_substantial_content}")
        print(f"Contains Bank Content: {has_bank_content}")

        success = has_substantial_content and not is_error

        result = {
            'success': success,
            'is_empty': is_empty,
            'is_error': is_error,
            'has_substantial_content': has_substantial_content,
            'has_bank_content': has_bank_content,
            'page_length': len(page_source),
            'text_length': len(body_text),
            'title': page_title,
            'url': current_url,
            'screenshot': screenshot_path
        }

        return result

    except Exception as e:
        print(f"\n{'=' * 80}")
        print(f"✗ ERROR OCCURRED")
        print(f"{'=' * 80}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

    finally:
        print(f"\n{'=' * 80}")
        print(f"Keeping Chrome session open for manual inspection...")
        print(f"{'=' * 80}")

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("Chrome CDP SSL Bypass Test")
    print("=" * 80 + "\n")

    result = test_cdp_with_ssl_bypass()

    print(f"\n\n{'=' * 80}")
    print(f"TEST SUMMARY")
    print(f"{'=' * 80}")

    if result.get('success'):
        print(f"✅ TEST PASSED - Successfully extracted content")
        print(f"\n   Page Length: {result['page_length']:,} bytes")
        print(f"   Text Length: {result['text_length']:,} bytes")
        print(f"   Has Bank Content: {result['has_bank_content']}")
        print(f"   Screenshot: {result['screenshot']}")
        print(f"\n   CONCLUSION: Real Chrome with CDP + SSL bypass works!")
        sys.exit(0)
    elif 'error' in result:
        print(f"❌ TEST FAILED - Error occurred")
        print(f"\n   Error: {result['error']}")
        sys.exit(1)
    else:
        print(f"⚠️  TEST INCONCLUSIVE")
        print(f"\n   Page Length: {result.get('page_length', 0):,} bytes")
        print(f"   Text Length: {result.get('text_length', 0):,} bytes")
        print(f"   Is Error Page: {result.get('is_error', False)}")
        print(f"   Has Bank Content: {result.get('has_bank_content', False)}")

        if result.get('is_error'):
            print(f"\n   CONCLUSION: Still hitting SSL error - bypass didn't work")
        else:
            print(f"\n   CONCLUSION: Need manual investigation")
        sys.exit(2)
