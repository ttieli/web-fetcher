#!/usr/bin/env python3
"""
urllib vs CDP Comparison Test Script

This script compares the performance and results of urllib and CDP (Chrome DevTools Protocol)
fetching methods. It reads URLs from the output folder and tests both methods.

Usage:
    python tests/compare_urllib_cdp.py [--output-dir PATH] [--sample SIZE] [--detailed]
"""

import sys
import os
import time
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
import re

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from webfetcher.core import fetch_html_original, create_url_metadata
from webfetcher.fetchers.cdp_fetcher import fetch_with_cdp, CDP_AVAILABLE


@dataclass
class ComparisonResult:
    """Result of comparing urllib vs CDP for a single URL"""
    url: str
    urllib_success: bool
    urllib_duration: float
    urllib_html_length: int
    urllib_error: str = None
    cdp_success: bool = False
    cdp_duration: float = 0.0
    cdp_html_length: int = 0
    cdp_error: str = None
    html_diff_percent: float = 0.0
    winner: str = "tie"  # "urllib", "cdp", "tie", "both_failed"


def extract_urls_from_markdown_files(output_dir: str) -> List[str]:
    """
    Extract URLs from markdown files in output directory.

    Looks for URL metadata section in markdown files to extract original URLs.

    Args:
        output_dir: Path to output directory containing markdown files

    Returns:
        List of unique URLs
    """
    urls = set()
    output_path = Path(output_dir)

    if not output_path.exists():
        print(f"❌ Output directory not found: {output_dir}")
        return []

    # Find all markdown files
    md_files = list(output_path.glob("**/*.md"))
    print(f"📁 Found {len(md_files)} markdown files in {output_dir}")

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')

            # Extract URL from metadata section
            # Look for patterns like "Original Request: [URL](URL)"
            url_matches = re.findall(r'Original Request[^:]*:\s*\[([^\]]+)\]', content)
            for url in url_matches:
                urls.add(url.strip())

            # Also look for "Final Location:" pattern
            url_matches = re.findall(r'Final Location[^:]*:\s*\[([^\]]+)\]', content)
            for url in url_matches:
                urls.add(url.strip())

            # Also try to extract from markdown links directly
            url_matches = re.findall(r'\[https?://[^\]]+\]\((https?://[^\)]+)\)', content)
            for url in url_matches:
                # Skip image URLs
                if not any(ext in url.lower() for ext in ['.jpg', '.png', '.gif', '.webp', '.jpeg']):
                    urls.add(url.strip())

        except Exception as e:
            print(f"⚠️  Error reading {md_file}: {e}")

    return sorted(list(urls))


def test_urllib_fetch(url: str, timeout: int = 30) -> Tuple[bool, float, int, str]:
    """
    Test URL with urllib method.

    Returns:
        Tuple of (success, duration, html_length, error_message)
    """
    start_time = time.time()

    try:
        html, metrics, final_url = fetch_html_original(url, ua=None, timeout=timeout)
        duration = time.time() - start_time
        return True, duration, len(html), None
    except Exception as e:
        duration = time.time() - start_time
        return False, duration, 0, str(e)


def test_cdp_fetch(url: str, wait_time: float = 3.0) -> Tuple[bool, float, int, str]:
    """
    Test URL with CDP method.

    Returns:
        Tuple of (success, duration, html_length, error_message)
    """
    if not CDP_AVAILABLE:
        return False, 0.0, 0, "CDP not available (pychrome not installed)"

    start_time = time.time()

    try:
        html, final_url, metadata = fetch_with_cdp(url, wait_time=wait_time)
        duration = time.time() - start_time
        return True, duration, len(html), None
    except Exception as e:
        duration = time.time() - start_time
        return False, duration, 0, str(e)


def compare_url(url: str, verbose: bool = False) -> ComparisonResult:
    """
    Compare urllib and CDP methods for a single URL.

    Args:
        url: URL to test
        verbose: Print detailed progress

    Returns:
        ComparisonResult object
    """
    if verbose:
        print(f"\n{'='*70}")
        print(f"Testing: {url}")
        print(f"{'='*70}")

    # Test urllib
    if verbose:
        print("  📡 Testing urllib...")
    urllib_success, urllib_duration, urllib_html_len, urllib_error = test_urllib_fetch(url)

    if verbose:
        if urllib_success:
            print(f"     ✓ Success: {urllib_html_len} chars in {urllib_duration:.2f}s")
        else:
            print(f"     ✗ Failed: {urllib_error}")

    # Test CDP
    if verbose:
        print("  🔌 Testing CDP...")
    cdp_success, cdp_duration, cdp_html_len, cdp_error = test_cdp_fetch(url)

    if verbose:
        if cdp_success:
            print(f"     ✓ Success: {cdp_html_len} chars in {cdp_duration:.2f}s")
        else:
            print(f"     ✗ Failed: {cdp_error}")

    # Calculate differences
    html_diff_percent = 0.0
    if urllib_success and cdp_success:
        max_len = max(urllib_html_len, cdp_html_len)
        if max_len > 0:
            html_diff_percent = abs(urllib_html_len - cdp_html_len) / max_len * 100

    # Determine winner
    winner = "tie"
    if urllib_success and cdp_success:
        if urllib_duration < cdp_duration * 0.9:  # urllib significantly faster
            winner = "urllib"
        elif cdp_duration < urllib_duration * 0.9:  # CDP significantly faster
            winner = "cdp"
        else:
            winner = "tie"
    elif urllib_success:
        winner = "urllib"
    elif cdp_success:
        winner = "cdp"
    else:
        winner = "both_failed"

    return ComparisonResult(
        url=url,
        urllib_success=urllib_success,
        urllib_duration=urllib_duration,
        urllib_html_length=urllib_html_len,
        urllib_error=urllib_error,
        cdp_success=cdp_success,
        cdp_duration=cdp_duration,
        cdp_html_length=cdp_html_len,
        cdp_error=cdp_error,
        html_diff_percent=html_diff_percent,
        winner=winner
    )


def generate_report(results: List[ComparisonResult], output_file: str = None):
    """
    Generate comparison report.

    Args:
        results: List of ComparisonResult objects
        output_file: Optional file path to save report
    """
    total_urls = len(results)

    # Calculate statistics
    urllib_success_count = sum(1 for r in results if r.urllib_success)
    cdp_success_count = sum(1 for r in results if r.cdp_success)
    both_success_count = sum(1 for r in results if r.urllib_success and r.cdp_success)
    both_failed_count = sum(1 for r in results if not r.urllib_success and not r.cdp_success)

    urllib_only_count = sum(1 for r in results if r.urllib_success and not r.cdp_success)
    cdp_only_count = sum(1 for r in results if r.cdp_success and not r.urllib_success)

    urllib_wins = sum(1 for r in results if r.winner == "urllib")
    cdp_wins = sum(1 for r in results if r.winner == "cdp")
    ties = sum(1 for r in results if r.winner == "tie")

    # Average durations (for successful fetches)
    urllib_durations = [r.urllib_duration for r in results if r.urllib_success]
    cdp_durations = [r.cdp_duration for r in results if r.cdp_success]

    avg_urllib_duration = sum(urllib_durations) / len(urllib_durations) if urllib_durations else 0
    avg_cdp_duration = sum(cdp_durations) / len(cdp_durations) if cdp_durations else 0

    # Generate report
    report = []
    report.append("=" * 80)
    report.append("urllib vs CDP Comparison Report")
    report.append("=" * 80)
    report.append("")

    report.append(f"Total URLs tested: {total_urls}")
    report.append("")

    report.append("## Success Rates")
    report.append("-" * 80)
    report.append(f"urllib success:     {urllib_success_count}/{total_urls} ({urllib_success_count/total_urls*100:.1f}%)")
    report.append(f"CDP success:        {cdp_success_count}/{total_urls} ({cdp_success_count/total_urls*100:.1f}%)")
    report.append(f"Both successful:    {both_success_count}/{total_urls} ({both_success_count/total_urls*100:.1f}%)")
    report.append(f"Both failed:        {both_failed_count}/{total_urls} ({both_failed_count/total_urls*100:.1f}%)")
    report.append(f"urllib only:        {urllib_only_count}/{total_urls} ({urllib_only_count/total_urls*100:.1f}%)")
    report.append(f"CDP only:           {cdp_only_count}/{total_urls} ({cdp_only_count/total_urls*100:.1f}%)")
    report.append("")

    report.append("## Performance (Speed)")
    report.append("-" * 80)
    report.append(f"Average urllib duration:  {avg_urllib_duration:.2f}s")
    report.append(f"Average CDP duration:     {avg_cdp_duration:.2f}s")
    report.append(f"Speed winner:             {'urllib' if avg_urllib_duration < avg_cdp_duration else 'CDP'}")
    report.append("")

    report.append("## Head-to-Head Results")
    report.append("-" * 80)
    report.append(f"urllib wins (faster):  {urllib_wins}/{both_success_count}")
    report.append(f"CDP wins (faster):     {cdp_wins}/{both_success_count}")
    report.append(f"Ties:                  {ties}/{both_success_count}")
    report.append("")

    report.append("## Detailed Results")
    report.append("-" * 80)
    for i, result in enumerate(results, 1):
        report.append(f"\n{i}. {result.url}")
        report.append(f"   urllib: {'✓' if result.urllib_success else '✗'} "
                     f"{result.urllib_duration:.2f}s "
                     f"{result.urllib_html_length} chars")
        if result.urllib_error:
            report.append(f"   urllib error: {result.urllib_error[:100]}")

        report.append(f"   CDP:    {'✓' if result.cdp_success else '✗'} "
                     f"{result.cdp_duration:.2f}s "
                     f"{result.cdp_html_length} chars")
        if result.cdp_error:
            report.append(f"   CDP error: {result.cdp_error[:100]}")

        if result.urllib_success and result.cdp_success:
            report.append(f"   HTML diff: {result.html_diff_percent:.1f}%")
            report.append(f"   Winner: {result.winner}")

    report.append("")
    report.append("=" * 80)

    # Print report
    report_text = "\n".join(report)
    print(report_text)

    # Save to file if requested
    if output_file:
        Path(output_file).write_text(report_text, encoding='utf-8')
        print(f"\n✓ Report saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Compare urllib and CDP fetch methods",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--output-dir',
        default='/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher/output',
        help='Output directory containing markdown files (default: ./output)'
    )

    parser.add_argument(
        '--sample',
        type=int,
        help='Number of URLs to sample (default: all)'
    )

    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed progress for each URL'
    )

    parser.add_argument(
        '--report',
        help='Save report to file (default: print to stdout only)'
    )

    args = parser.parse_args()

    # Check CDP availability
    if not CDP_AVAILABLE:
        print("❌ CDP not available. Install with: pip install pychrome")
        print("   Or: pip install -r requirements-cdp.txt")
        sys.exit(1)

    # Extract URLs from output directory
    print(f"📁 Scanning output directory: {args.output_dir}")
    urls = extract_urls_from_markdown_files(args.output_dir)

    if not urls:
        print("❌ No URLs found in output directory")
        sys.exit(1)

    print(f"✓ Found {len(urls)} unique URLs")

    # Sample if requested
    if args.sample and args.sample < len(urls):
        import random
        urls = random.sample(urls, args.sample)
        print(f"📊 Sampling {len(urls)} URLs for testing")

    # Run comparison tests
    print(f"\n{'='*80}")
    print(f"Starting Comparison Tests")
    print(f"{'='*80}")

    results = []
    for i, url in enumerate(urls, 1):
        if not args.detailed:
            print(f"\n[{i}/{len(urls)}] Testing {url}...")

        result = compare_url(url, verbose=args.detailed)
        results.append(result)

        if not args.detailed:
            status = f"urllib: {'✓' if result.urllib_success else '✗'} | "
            status += f"CDP: {'✓' if result.cdp_success else '✗'} | "
            status += f"Winner: {result.winner}"
            print(f"        {status}")

    # Generate report
    print("\n")
    generate_report(results, output_file=args.report)


if __name__ == '__main__':
    main()
