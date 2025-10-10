#!/usr/bin/env python3
"""
Simple CDP connection test - no extra options that might cause conflicts
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import sys

def test_cdp_simple():
    """Connect to existing Chrome - minimal configuration"""
    print("=" * 80)
    print("Simple CDP Connection Test")
    print("=" * 80)

    options = Options()
    options.debugger_address = "127.0.0.1:9222"

    driver = None
    try:
        print("\nConnecting to Chrome on port 9222...")
        driver = webdriver.Chrome(options=options)
        print(f"✓ Connected")

        # Navigate to CEB Bank
        url = "https://www.cebbank.com.cn/site/zhpd/zxgg35/cgjggg/263565922/index.html"
        print(f"\nNavigating to: {url}")
        driver.get(url)

        # Wait for load
        print("Waiting 15 seconds...")
        time.sleep(15)

        # Extract
        page_source = driver.page_source
        body_text = driver.execute_script("return document.body.innerText;")
        page_title = driver.title

        print(f"\n{'=' * 80}")
        print(f"RESULTS")
        print(f"{'=' * 80}")
        print(f"Title: {page_title}")
        print(f"Page source: {len(page_source):,} bytes")
        print(f"Body text: {len(body_text):,} bytes")

        print(f"\n--- First 1000 chars of body text ---")
        print(body_text[:1000])

        # Screenshot
        screenshot = '/tmp/cebbank_simple_test.png'
        driver.save_screenshot(screenshot)
        print(f"\nScreenshot: {screenshot}")

        # Analysis
        is_error = '隐私设置错误' in page_title or 'ERR_' in page_title
        has_content = len(body_text) > 1000
        has_bank = '光大银行' in page_source or '采购结果公告' in page_source

        success = has_content and not is_error

        return {
            'success': success,
            'is_error': is_error,
            'has_content': has_content,
            'has_bank': has_bank,
            'page_length': len(page_source),
            'text_length': len(body_text),
            'title': page_title,
            'screenshot': screenshot
        }

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    result = test_cdp_simple()

    print(f"\n{'=' * 80}")
    print(f"SUMMARY")
    print(f"{'=' * 80}")

    if result.get('success'):
        print(f"✅ SUCCESS")
        print(f"   Text: {result['text_length']:,} bytes")
        print(f"   Has bank content: {result['has_bank']}")
        sys.exit(0)
    elif 'error' in result:
        print(f"❌ ERROR")
        print(f"   {result['error']}")
        sys.exit(1)
    else:
        print(f"⚠️  PARTIAL")
        print(f"   Is error page: {result.get('is_error')}")
        print(f"   Has content: {result.get('has_content')}")
        print(f"   Has bank: {result.get('has_bank')}")
        sys.exit(2)
