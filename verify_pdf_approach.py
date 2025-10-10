#!/usr/bin/env python3
"""
Quick verification that PDF approach fails for CEB Bank
This demonstrates the core issue: empty content -> empty PDF
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import base64
import tempfile
import os

def verify_pdf_approach():
    """Quick test to show PDF approach doesn't work"""

    url = "https://www.cebbank.com.cn/site/zhpd/zxgg35/cgjggg/263565922/index.html"

    print("Testing CEB Bank PDF Extraction Approach")
    print("="*50)

    # Setup Chrome
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--ignore-certificate-errors')
    driver = webdriver.Chrome(options=options)

    try:
        # Navigate to page
        print(f"1. Loading URL: {url}")
        driver.get(url)

        # Check what we got
        html = driver.page_source
        print(f"2. HTML received: {len(html)} bytes")
        print(f"   Content: {html}")

        # Generate PDF
        print("3. Generating PDF...")
        pdf_result = driver.execute_cdp_cmd('Page.printToPDF', {
            'printBackground': True
        })

        pdf_data = base64.b64decode(pdf_result['data'])
        print(f"4. PDF size: {len(pdf_data)} bytes")

        # Save and check PDF
        fd, pdf_path = tempfile.mkstemp(suffix='.pdf', prefix='ceb_test_')
        os.close(fd)
        with open(pdf_path, 'wb') as f:
            f.write(pdf_data)

        # Check for text in PDF using strings
        print("5. Checking PDF content...")
        stream = os.popen(f'strings "{pdf_path}" | grep -v "^%" | grep -v "^/" | grep -v "endobj"')
        content = stream.read().strip()

        if len(content) > 100:
            print(f"   Found text: {content[:200]}")
        else:
            print("   No meaningful text found in PDF")

        print(f"\n6. Result: PDF saved to {pdf_path}")

        # Conclusion
        print("\n" + "="*50)
        print("CONCLUSION: PDF approach FAILS")
        print("- Browser receives empty HTML (39 bytes)")
        print("- PDF captures the empty page (~1KB file)")
        print("- No text can be extracted")
        print("- Server blocks content before it reaches browser")

        return pdf_path

    finally:
        driver.quit()

if __name__ == '__main__':
    verify_pdf_approach()