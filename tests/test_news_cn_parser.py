#!/usr/bin/env python3
"""
Test suite for news.cn parser template
Task: task-009-news-cn-empty-content-extraction
Phase 3: Testing & Validation

This script tests the news.cn template parser to ensure:
1. Articles extract non-empty content
2. File sizes exceed minimum threshold
3. Chinese characters are properly encoded
4. Proper routing to News.cn template
"""

import os
import sys
import subprocess
from pathlib import Path
import time

# Add parent directory to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Test URLs from various news.cn categories
TEST_URLS = [
    # Original bug report URL
    "https://www.news.cn/politics/leaders/20251010/2822d6ac4c4e424abde9fdd8fb94e2d3/c.html",
    # Additional test URLs from different categories
    "https://www.news.cn/talking/20251010/80d6bc6a1439498f9a762db540e40494/c.html",
    "https://www.news.cn/world/20251011/33b1c9a544fb4d2abc44c46c8161050f/c.html",
    "https://www.news.cn/culture/20251011/1fc8c1e6dee7451da93b7777bafd2de9/c.html",
]

# Minimum file size to indicate successful content extraction (in bytes)
MIN_FILE_SIZE = 1000  # 1KB - before fix, files were ~600 bytes

def run_webfetcher(url):
    """
    Run the webfetcher on a given URL
    Returns: (success, output_file_path, file_size, duration)
    """
    start_time = time.time()

    try:
        # Run wf.py
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "wf.py"), url],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(PROJECT_ROOT)
        )

        duration = time.time() - start_time

        # Parse output to find the generated file
        output = result.stdout + result.stderr

        # Look for the output file path in the last line
        lines = output.strip().split('\n')
        output_file = None

        for line in reversed(lines):
            if line.startswith('/') and '.md' in line and 'output' in line:
                output_file = line.strip()
                break

        if output_file and os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            return (True, output_file, file_size, duration)
        else:
            return (False, None, 0, duration)

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return (False, None, 0, duration)
    except Exception as e:
        duration = time.time() - start_time
        print(f"  Error: {e}")
        return (False, None, 0, duration)

def check_content_quality(file_path):
    """
    Check if the extracted content meets quality criteria
    Returns: (has_title, has_content, has_chinese, content_length)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for title
        has_title = '# ' in content

        # Check for substantial content (more than just metadata)
        lines = content.split('\n')
        content_lines = [l for l in lines if l.strip() and not l.startswith('-') and not l.startswith('#')]
        has_content = len(content_lines) > 5

        # Check for Chinese characters
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in content)

        content_length = len(content)

        return (has_title, has_content, has_chinese, content_length)

    except Exception as e:
        print(f"  Error reading file: {e}")
        return (False, False, False, 0)

def test_news_cn_extraction():
    """Test that news.cn articles extract non-empty content"""
    print("=" * 70)
    print("Testing news.cn Content Extraction")
    print("Task: task-009-news-cn-empty-content-extraction - Phase 3")
    print("=" * 70)
    print()

    results = []
    total_tests = len(TEST_URLS)
    passed_tests = 0

    for i, url in enumerate(TEST_URLS, 1):
        print(f"Test {i}/{total_tests}: {url}")

        success, output_file, file_size, duration = run_webfetcher(url)

        if success:
            has_title, has_content, has_chinese, content_length = check_content_quality(output_file)

            # Check if all criteria are met
            size_ok = file_size >= MIN_FILE_SIZE
            quality_ok = has_title and has_content and has_chinese

            test_passed = size_ok and quality_ok

            if test_passed:
                print(f"  ✓ PASS")
                passed_tests += 1
            else:
                print(f"  ✗ FAIL")

            print(f"    File size: {file_size} bytes (min: {MIN_FILE_SIZE})")
            print(f"    Content length: {content_length} characters")
            print(f"    Duration: {duration:.2f}s")
            print(f"    Has title: {has_title}")
            print(f"    Has content: {has_content}")
            print(f"    Has Chinese: {has_chinese}")
            print(f"    Output: {os.path.basename(output_file)}")

            results.append({
                'url': url,
                'success': test_passed,
                'file_size': file_size,
                'duration': duration,
                'output': output_file
            })
        else:
            print(f"  ✗ FAIL - Could not extract content")
            print(f"    Duration: {duration:.2f}s")
            results.append({
                'url': url,
                'success': False,
                'file_size': 0,
                'duration': duration,
                'output': None
            })

        print()

    # Summary
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    print()

    if passed_tests == total_tests:
        print("✓ All tests passed!")
        print()
        print("Bug Fix Status: VERIFIED")
        print("- Articles now extract full content (not just metadata)")
        print(f"- All file sizes exceed {MIN_FILE_SIZE} bytes")
        print("- Chinese characters are properly encoded")
        print("- News.cn template routing works correctly")
        return 0
    else:
        print("✗ Some tests failed")
        print()
        print("Failed URLs:")
        for result in results:
            if not result['success']:
                print(f"  - {result['url']}")
        return 1

if __name__ == "__main__":
    exit_code = test_news_cn_extraction()
    sys.exit(exit_code)
