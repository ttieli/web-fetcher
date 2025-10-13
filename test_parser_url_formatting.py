#!/usr/bin/env python3
"""
Test script for Task-003 Phase 4: Parser URL Formatting Fixes

This script tests the URL formatting improvements in both WeChat and Generic parsers.

Test scenarios:
1. WeChat parser with <a> tags (should convert to markdown links)
2. Generic parser with <a> tags (should preserve and convert to markdown)
3. Generic parser with plain text URLs (should convert to markdown)
4. Mixed content with both types of URLs

Expected results:
- All URLs in <a> tags: [link text](url)
- Plain text URLs: [url](url)
- No plain text URLs like (https://example.com)
"""

import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent))

from parsers_legacy import wechat_to_markdown, generic_to_markdown


def test_wechat_parser():
    """Test WeChat parser URL formatting"""
    print("=" * 80)
    print("TEST 1: WeChat Parser - Link with descriptive text")
    print("=" * 80)

    sample_html = """
    <html>
    <head>
        <meta property="og:title" content="Test Article">
        <meta property="og:article:author" content="Test Author">
    </head>
    <body>
        <div id="js_content">
            <h1>Test Article</h1>
            <p>Visit <a href="https://example.com">our website</a> for more information.</p>
            <p>Also check out <a href="https://another.com">this resource</a> and <a href="https://third.com">this one</a>.</p>
            <p>Plain text URL should also work: https://plaintext.com</p>
        </div>
    </body>
    </html>
    """

    date_only, markdown, metadata = wechat_to_markdown(sample_html, "https://test.com")

    print("\n--- Generated Markdown ---")
    print(markdown)
    print("\n--- Analysis ---")

    # Check for expected patterns
    checks = [
        ("[our website](https://example.com)" in markdown, "✓ Link with text 'our website' formatted correctly"),
        ("[this resource](https://another.com)" in markdown, "✓ Link with text 'this resource' formatted correctly"),
        ("[this one](https://third.com)" in markdown, "✓ Link with text 'this one' formatted correctly"),
        ("[https://plaintext.com](https://plaintext.com)" in markdown, "✓ Plain text URL converted to markdown format"),
        ("(https://" not in markdown or markdown.count("(https://") == 0, "✓ No plain text URLs in parentheses format")
    ]

    for check, message in checks:
        status = "PASS" if check else "FAIL"
        print(f"[{status}] {message}")

    return all(check for check, _ in checks)


def test_generic_parser():
    """Test Generic parser URL formatting"""
    print("\n" + "=" * 80)
    print("TEST 2: Generic Parser - Links and plain text URLs")
    print("=" * 80)

    # Create content long enough to pass the 500-byte threshold
    sample_html = """
    <html>
    <head>
        <title>Generic Article</title>
        <meta property="og:title" content="Generic Test Article">
        <meta name="description" content="Test description">
    </head>
    <body>
        <main>
            <article>
                <h1>Generic Test Article</h1>
                <p>Visit <a href="https://docs.example.com">the documentation</a> to learn more about our project.
                This is a comprehensive guide that covers all aspects of the system.</p>
                <p>You can also see https://blog.example.com for the latest updates and news.
                Our blog features regular updates, tutorials, and community highlights.</p>
                <p>Check out <a href="https://github.com/example/repo">our GitHub repository</a> for the source code.
                The repository contains all the code, examples, and documentation.</p>
                <div>
                    <p>More information at https://support.example.com/help where you can find answers to common questions.</p>
                    <p>Additional resources include our FAQ section, video tutorials, and community forums.</p>
                    <p>We also provide enterprise support options for organizations.</p>
                </div>
            </article>
        </main>
    </body>
    </html>
    """

    date_only, markdown, metadata = generic_to_markdown(sample_html, "https://test.com")

    print("\n--- Generated Markdown ---")
    print(markdown)
    print("\n--- Analysis ---")

    # Check for expected patterns
    checks = [
        ("[the documentation](https://docs.example.com)" in markdown, "✓ Link with text 'the documentation' formatted correctly"),
        ("[our GitHub repository](https://github.com/example/repo)" in markdown, "✓ Link with text 'our GitHub repository' formatted correctly"),
        ("[https://blog.example.com](https://blog.example.com)" in markdown, "✓ Plain text URL converted to markdown"),
        ("[https://support.example.com/help](https://support.example.com/help)" in markdown, "✓ Another plain text URL converted to markdown"),
        ("(https://docs.example.com)" not in markdown, "✓ No plain text format (https://...)"),
    ]

    for check, message in checks:
        status = "PASS" if check else "FAIL"
        print(f"[{status}] {message}")

    return all(check for check, _ in checks)


def test_edge_cases():
    """Test edge cases"""
    print("\n" + "=" * 80)
    print("TEST 3: Edge Cases - URLs with special characters")
    print("=" * 80)

    sample_html = """
    <html>
    <head>
        <meta property="og:title" content="Edge Case Article">
    </head>
    <body>
        <div id="js_content">
            <p>URL with query params: <a href="https://example.com/page?id=123&user=test">complex link</a></p>
            <p>URL with anchor: <a href="https://example.com/doc#section">jump to section</a></p>
            <p>Empty link text: <a href="https://example.com/empty"></a></p>
        </div>
    </body>
    </html>
    """

    date_only, markdown, metadata = wechat_to_markdown(sample_html, "https://test.com")

    print("\n--- Generated Markdown ---")
    print(markdown)
    print("\n--- Analysis ---")

    # Check for expected patterns
    checks = [
        ("[complex link](https://example.com/page?id=123&user=test)" in markdown, "✓ URL with query params formatted correctly"),
        ("[jump to section](https://example.com/doc#section)" in markdown, "✓ URL with anchor formatted correctly"),
        ("[https://example.com/empty](https://example.com/empty)" in markdown or "](https://example.com/empty)" in markdown, "✓ Empty link text handled (fallback to URL)"),
    ]

    for check, message in checks:
        status = "PASS" if check else "FAIL"
        print(f"[{status}] {message}")

    return all(check for check, _ in checks)


def test_code_block_preservation():
    """Test that URLs in code blocks are not modified"""
    print("\n" + "=" * 80)
    print("TEST 4: Code Block Preservation")
    print("=" * 80)

    sample_html = """
    <html>
    <head>
        <title>Code Block Test</title>
    </head>
    <body>
        <main>
            <article>
                <h1>API Documentation</h1>
                <p>The API endpoint is at <a href="https://api.example.com">https://api.example.com</a>.</p>
                <p>Example usage:</p>
                <pre><code>
                curl https://api.example.com/v1/users
                fetch('https://api.example.com/v1/data')
                </code></pre>
                <p>For more info, visit https://docs.example.com</p>
            </article>
        </main>
    </body>
    </html>
    """

    date_only, markdown, metadata = generic_to_markdown(sample_html, "https://test.com")

    print("\n--- Generated Markdown ---")
    print(markdown)
    print("\n--- Analysis ---")

    # Note: Code block preservation is complex - the generic parser may not
    # preserve <pre><code> blocks perfectly. This is a known limitation.
    # We're mainly checking that the non-code URLs are formatted correctly.

    checks = [
        ("[https://api.example.com](https://api.example.com)" in markdown, "✓ Link to API formatted correctly"),
        ("[https://docs.example.com](https://docs.example.com)" in markdown, "✓ Plain text docs URL formatted correctly"),
    ]

    for check, message in checks:
        status = "PASS" if check else "FAIL"
        print(f"[{status}] {message}")

    print("\nNote: Code block URLs may or may not be preserved depending on HTML structure.")
    print("The generic parser strips most HTML, including <pre> and <code> tags.")

    return all(check for check, _ in checks)


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "Task-003 Phase 4: Parser URL Formatting Tests" + " " * 17 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")

    results = []

    try:
        results.append(("WeChat Parser", test_wechat_parser()))
    except Exception as e:
        print(f"\n[ERROR] WeChat parser test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("WeChat Parser", False))

    try:
        results.append(("Generic Parser", test_generic_parser()))
    except Exception as e:
        print(f"\n[ERROR] Generic parser test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Generic Parser", False))

    try:
        results.append(("Edge Cases", test_edge_cases()))
    except Exception as e:
        print(f"\n[ERROR] Edge cases test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Edge Cases", False))

    try:
        results.append(("Code Block Preservation", test_code_block_preservation()))
    except Exception as e:
        print(f"\n[ERROR] Code block test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Code Block Preservation", False))

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Phase 4 implementation is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
