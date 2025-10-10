#!/usr/bin/env python3
"""Test script to fetch and inspect raw HTML content"""

from selenium_fetcher import SeleniumFetcher
import sys

def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.cebbank.com.cn/site/zhpd/zxgg35/cgjggg/263565922/index.html"

    print(f"Fetching: {url}")

    fetcher = SeleniumFetcher()
    fetcher.connect_to_chrome()

    try:
        html = fetcher.fetch_html_selenium(url)

        print(f"\n=== CONTENT LENGTH ===")
        print(f"{len(html)} characters")

        print(f"\n=== FIRST 2000 CHARACTERS ===")
        print(html[:2000])

        print(f"\n=== KEYWORD SEARCH ===")
        keywords = ['隐私', 'privacy', '错误', 'error', '设置', 'setting']
        for keyword in keywords:
            if keyword in html or keyword.lower() in html.lower():
                print(f"✓ Found: {keyword}")

        # Save to file for inspection
        output_path = "/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher/raw_html_debug.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\n✓ Full HTML saved to: {output_path}")

    finally:
        fetcher.disconnect_from_chrome()

if __name__ == "__main__":
    main()
