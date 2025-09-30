#!/usr/bin/env python3
"""
Test script for Task 1 Phase 1: Failure report generation functions
"""

import sys
import os
import datetime
from dataclasses import dataclass

# Add the parent directory to the path to import webfetcher
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webfetcher import generate_failure_markdown, get_failure_filename, FetchMetrics

def test_generate_failure_markdown():
    """Test the generate_failure_markdown function"""
    print("Testing generate_failure_markdown()...")

    # Create a test metrics object
    metrics = FetchMetrics()
    metrics.primary_method = "selenium"
    metrics.final_status = "failed"
    metrics.fetch_duration = 5.234
    metrics.total_attempts = 3
    metrics.error_message = "Connection refused to Chrome debug port"

    # Test with Selenium error
    class ChromeConnectionError(Exception):
        pass

    exception = ChromeConnectionError("Could not connect to Chrome")

    # Test English version
    os.environ['LANG'] = 'en_US.UTF-8'
    markdown_en = generate_failure_markdown(
        url="https://example.com/test",
        metrics=metrics,
        exception=exception
    )

    print("\n=== English Version ===")
    print(markdown_en)

    # Test Chinese version
    os.environ['LANG'] = 'zh_CN.UTF-8'
    markdown_zh = generate_failure_markdown(
        url="https://example.com/test",
        metrics=metrics,
        exception=exception
    )

    print("\n=== Chinese Version ===")
    print(markdown_zh)

    # Verify key components are present
    assert "⚠️" in markdown_en
    assert "Chrome" in markdown_en
    assert "9222" in markdown_en
    assert "example.com" in markdown_en

    print("\n✅ generate_failure_markdown tests passed!")

def test_get_failure_filename():
    """Test the get_failure_filename function"""
    print("\nTesting get_failure_filename()...")

    # Test with various URLs
    test_cases = [
        ("2025-01-30-143052", "https://example.com", "FAILED_2025-01-30-143052 - example.com"),
        ("2025-01-30-143052", "https://docs.python.org/3/", "FAILED_2025-01-30-143052 - docs.python.org"),
        ("2025-01-30-143052", "invalid-url", "FAILED_2025-01-30-143052 - unknown"),
    ]

    for timestamp, url, expected_prefix in test_cases:
        result = get_failure_filename(timestamp, url)
        print(f"  URL: {url}")
        print(f"  Result: {result}")
        assert result.startswith(expected_prefix[:20]), f"Expected to start with {expected_prefix[:20]}, got {result}"

    print("\n✅ get_failure_filename tests passed!")

def test_integration():
    """Test integration between both functions"""
    print("\nTesting integration...")

    # Simulate a failed fetch
    metrics = FetchMetrics()
    metrics.primary_method = "urllib"
    metrics.fallback_method = "selenium"
    metrics.final_status = "failed"
    metrics.fetch_duration = 2.5
    metrics.total_attempts = 2
    metrics.error_message = "Network timeout"
    metrics.chrome_connected = False
    metrics.selenium_wait_time = 1.5

    url = "https://github.com/test/repo"
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')

    # Generate filename
    filename = get_failure_filename(timestamp, url)
    print(f"Generated filename: {filename}")

    # Generate markdown content
    os.environ['LANG'] = 'en_US.UTF-8'
    markdown = generate_failure_markdown(url, metrics)

    # Verify integration
    assert "github.com" in filename.lower()
    assert "Network timeout" in markdown
    assert "urllib" in markdown or "fallback" in markdown.lower()

    print("\n✅ Integration test passed!")

if __name__ == "__main__":
    print("=" * 60)
    print("Task 1 Phase 1: Failure Report Generation Functions Test")
    print("=" * 60)

    test_generate_failure_markdown()
    test_get_failure_filename()
    test_integration()

    print("\n" + "=" * 60)
    print("All tests completed successfully! ✅")
    print("=" * 60)