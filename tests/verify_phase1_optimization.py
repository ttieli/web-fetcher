#!/usr/bin/env python3
"""
Phase 1 Verification Script - Generic Parser Optimization
Tests the parser directly without ContentFilter interference
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium_fetcher import SeleniumFetcher
from parsers import generic_to_markdown, extract_from_modern_selectors
import re

def test_direct_parser():
    """Test parser directly without any filtering"""
    print("=" * 70)
    print("PHASE 1 VERIFICATION: Generic Parser Optimization")
    print("=" * 70)

    # Step 1: Fetch HTML
    print("\n1. Fetching HTML from react.dev...")
    fetcher = SeleniumFetcher()
    try:
        # Connect to Chrome first
        fetcher.connect_to_chrome()
        html, metrics = fetcher.fetch_html_selenium('https://react.dev/')
        print(f"   ✓ HTML fetched: {len(html)} bytes")
        fetcher.cleanup()
    except Exception as e:
        print(f"   ✗ Failed to fetch: {e}")
        return False

    # Step 2: Test selector extraction directly
    print("\n2. Testing extract_from_modern_selectors() directly...")
    extracted_content = extract_from_modern_selectors(html)
    print(f"   ✓ Extracted content: {len(extracted_content)} bytes")

    # Step 3: Analyze what was extracted
    print("\n3. Analyzing extracted content...")
    if extracted_content:
        # Check for React-specific content
        react_keywords = ['React', 'component', 'useState', 'useEffect', 'props', 'JSX']
        found_keywords = [kw for kw in react_keywords if kw in extracted_content]
        print(f"   ✓ Found React keywords: {found_keywords}")

        # Show first 500 chars
        print("\n   Content preview (first 500 chars):")
        print("   " + "-" * 50)
        preview = extracted_content[:500].replace('\n', '\n   ')
        print(f"   {preview}")
        print("   " + "-" * 50)
    else:
        print("   ✗ No content extracted!")

    # Step 4: Test full parser
    print("\n4. Testing full generic_to_markdown() parser...")
    date, markdown_content, metadata = generic_to_markdown(html, 'https://react.dev/', 'none', False)
    print(f"   ✓ Markdown output: {len(markdown_content)} bytes")
    print(f"   ✓ Metadata: {metadata.get('page_type', 'unknown')} page")

    # Step 5: Check what selectors matched
    print("\n5. Checking which selectors matched...")
    selectors_to_test = [
        (r'<main[^>]*>', 'main'),
        (r'<article[^>]*>', 'article'),
        (r'<div[^>]*id=["\']root["\']', 'div#root'),
        (r'<div[^>]*id=["\']app["\']', 'div#app'),
        (r'<div[^>]*id=["\']__next["\']', 'div#__next'),
        (r'<div[^>]*role=["\']main["\']', 'div[role="main"]'),
    ]

    for pattern, name in selectors_to_test:
        if re.search(pattern, html, re.I):
            print(f"   ✓ Found: {name}")
            # Check if content exists (simplified to avoid regex errors)
            tag_name = name.split('[')[0].split('#')[0]
            try:
                full_pattern = pattern[:-1] + r'>(.*?)</' + re.escape(tag_name) + '>'
                match = re.search(full_pattern, html, re.I | re.S)
                if match:
                    content_len = len(match.group(1))
                    print(f"     Content length: {content_len} bytes")
            except:
                pass  # Skip if pattern has issues
        else:
            print(f"   ✗ Not found: {name}")

    # Step 6: Verify threshold logic
    print("\n6. Verifying content validation threshold...")
    print(f"   Current threshold: 500 bytes (Phase 1 optimization)")
    print(f"   Extracted content: {len(extracted_content)} bytes")
    if len(extracted_content) >= 500:
        print("   ✓ Content passes validation threshold")
    else:
        print("   ✗ Content below threshold - would be rejected")

    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    success = len(extracted_content) > 500
    if success:
        print("✅ Phase 1 Optimization SUCCESSFUL")
        print(f"   - Parser extracted {len(extracted_content)} bytes directly")
        print(f"   - Content validation threshold (500 bytes) passed")
        print(f"   - React-specific content found: {len(found_keywords)} keywords")
    else:
        print("❌ Phase 1 Optimization FAILED")
        print(f"   - Insufficient content extracted: {len(extracted_content)} bytes")
        print("   - Below validation threshold of 500 bytes")

    return success

if __name__ == "__main__":
    success = test_direct_parser()
    sys.exit(0 if success else 1)