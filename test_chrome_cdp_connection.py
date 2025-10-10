#!/usr/bin/env python3
"""
Test connecting to real Chrome via CDP debugging port
This Chrome has NO automation markers - it's a real browser instance
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import sys

def test_cdp_connection():
    """Connect to existing Chrome debug session"""
    print("=" * 80)
    print("Testing CDP Connection to Real Chrome Browser")
    print("=" * 80)
    print("\nConnecting to Chrome debug session on port 9222...")

    options = Options()
    # THIS is the magic - connect to existing Chrome instead of launching new one
    options.debugger_address = "127.0.0.1:9222"

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        print(f"✓ Connected successfully")
        print(f"Current URL: {driver.current_url}")
        print(f"Title: {driver.title}")

        # Navigate to CEB Bank test URL
        url = "https://www.cebbank.com.cn/site/zhpd/zxgg35/cgjggg/263565922/index.html"
        print(f"\n{'=' * 80}")
        print(f"Navigating to CEB Bank URL:")
        print(f"  {url}")
        print(f"{'=' * 80}")
        driver.get(url)

        # Wait for page load
        print("\nWaiting 10 seconds for page to fully load...")
        time.sleep(10)

        # Extract content using multiple methods
        print("\nExtracting content...")
        page_source = driver.page_source
        body_text = driver.execute_script("return document.body.innerText;")
        page_title = driver.title
        current_url = driver.current_url

        # Also try to get HTML content
        html_content = driver.execute_script("return document.documentElement.outerHTML;")

        print(f"\n{'=' * 80}")
        print(f"EXTRACTION RESULTS")
        print(f"{'=' * 80}")
        print(f"Page Title: {page_title}")
        print(f"Current URL: {current_url}")
        print(f"Page source length: {len(page_source):,} bytes")
        print(f"Body text length: {len(body_text):,} bytes")
        print(f"HTML content length: {len(html_content):,} bytes")

        # Show preview of content
        print(f"\n{'=' * 80}")
        print(f"CONTENT PREVIEW - First 800 characters")
        print(f"{'=' * 80}")
        print(f"\n--- Page Source ---")
        print(page_source[:800])
        print(f"\n--- Body Text ---")
        print(body_text[:800])

        # Check for success indicators
        is_empty = len(page_source) < 100
        is_error = '隐私设置错误' in page_title or '隐私错误' in page_source or 'ERR_' in page_title
        has_substantial_content = len(body_text) > 1000
        has_bank_content = '光大银行' in page_source or '中国光大银行' in page_source

        # Take screenshot
        screenshot_path = '/tmp/cebbank_cdp_test.png'
        driver.save_screenshot(screenshot_path)
        print(f"\n{'=' * 80}")
        print(f"Screenshot saved: {screenshot_path}")
        print(f"{'=' * 80}")

        # Analysis
        print(f"\n{'=' * 80}")
        print(f"ANALYSIS")
        print(f"{'=' * 80}")
        print(f"✓ Is Empty (< 100 bytes): {is_empty}")
        print(f"✓ Is Error Page: {is_error}")
        print(f"✓ Has Substantial Content (> 1000 bytes): {has_substantial_content}")
        print(f"✓ Contains Bank Content: {has_bank_content}")

        success = has_substantial_content and not is_error

        result = {
            'success': success,
            'is_empty': is_empty,
            'is_error': is_error,
            'has_substantial_content': has_substantial_content,
            'has_bank_content': has_bank_content,
            'page_length': len(page_source),
            'text_length': len(body_text),
            'html_length': len(html_content),
            'title': page_title,
            'url': current_url,
            'screenshot': screenshot_path
        }

        return result

    except Exception as e:
        print(f"\n{'=' * 80}")
        print(f"✗ ERROR OCCURRED")
        print(f"{'=' * 80}")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

    finally:
        # Don't close the driver - we want to keep the Chrome session open for inspection
        print(f"\n{'=' * 80}")
        print(f"Keeping Chrome session open for manual inspection...")
        print(f"You can view the browser window and DevTools")
        print(f"{'=' * 80}")

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("Chrome CDP Connection Test")
    print("Testing if real Chrome can bypass anti-bot detection")
    print("=" * 80 + "\n")

    result = test_cdp_connection()

    print(f"\n\n{'=' * 80}")
    print(f"TEST SUMMARY")
    print(f"{'=' * 80}")

    if result.get('success'):
        print(f"✅ TEST PASSED - Successfully extracted content")
        print(f"\n   Page Length: {result['page_length']:,} bytes")
        print(f"   Text Length: {result['text_length']:,} bytes")
        print(f"   Has Bank Content: {result['has_bank_content']}")
        print(f"   Title: {result['title']}")
        print(f"   Screenshot: {result['screenshot']}")
        print(f"\n   CONCLUSION: Real Chrome with CDP bypasses anti-bot detection!")
        sys.exit(0)
    elif 'error' in result:
        print(f"❌ TEST FAILED - Error occurred")
        print(f"\n   Error: {result['error']}")
        print(f"\n   CONCLUSION: Technical error, need to debug")
        sys.exit(1)
    else:
        print(f"⚠️  TEST INCONCLUSIVE - Content extracted but insufficient")
        print(f"\n   Page Length: {result.get('page_length', 0):,} bytes")
        print(f"   Text Length: {result.get('text_length', 0):,} bytes")
        print(f"   Is Empty: {result.get('is_empty', False)}")
        print(f"   Is Error Page: {result.get('is_error', False)}")
        print(f"   Has Bank Content: {result.get('has_bank_content', False)}")
        print(f"   Title: {result.get('title', 'N/A')}")

        if result.get('is_empty'):
            print(f"\n   CONCLUSION: Still returning empty content - anti-bot may detect CDP")
        elif result.get('is_error'):
            print(f"\n   CONCLUSION: Error page returned - need to investigate")
        else:
            print(f"\n   CONCLUSION: Partial success - need further analysis")
        sys.exit(2)
