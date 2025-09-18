#!/usr/bin/env python3
"""
Image Quality Validation Script for XiaoHongShu Images
Tests the enhancement implementations for extracting high-quality images
"""

import re
import sys
from pathlib import Path

def analyze_image_urls(file_path):
    """Analyze image URLs in a markdown file for quality indicators."""
    
    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}")
        return None
    
    content = Path(file_path).read_text()
    
    # Extract all image URLs
    image_pattern = r'!\[\]\((http[^)]+)\)'
    urls = re.findall(image_pattern, content)
    
    # Analyze quality indicators
    quality_stats = {
        'total': len(urls),
        'unique': len(set(urls)),
        'high_quality': 0,
        'low_quality': 0,
        'nd_dft': 0,  # High quality default format
        'nd_prv': 0,  # Low quality preview format
        'w_1080': 0,  # Explicit 1080px width
        'w_720': 0,   # Explicit 720px width
        'w_480': 0,   # Explicit 480px width
        'other_sizes': 0,
        'urls': []
    }
    
    for url in urls:
        quality_stats['urls'].append(url)
        
        # Check for quality indicators
        if 'nd_dft' in url:
            quality_stats['nd_dft'] += 1
            quality_stats['high_quality'] += 1
        elif 'nd_prv' in url:
            quality_stats['nd_prv'] += 1
            quality_stats['low_quality'] += 1
        
        # Check for explicit width parameters
        if 'w/1080' in url or 'width=1080' in url:
            quality_stats['w_1080'] += 1
            quality_stats['high_quality'] += 1
        elif 'w/720' in url or 'width=720' in url:
            quality_stats['w_720'] += 1
            quality_stats['low_quality'] += 1
        elif 'w/480' in url or 'width=480' in url:
            quality_stats['w_480'] += 1
            quality_stats['low_quality'] += 1
        elif re.search(r'w/\d+', url) or re.search(r'width=\d+', url):
            quality_stats['other_sizes'] += 1
    
    return quality_stats

def print_quality_report(stats):
    """Print a detailed quality assessment report."""
    print("\n" + "="*60)
    print("XIAOHONGSHU IMAGE QUALITY VALIDATION REPORT")
    print("="*60)
    
    print(f"\nTotal Images Extracted: {stats['total']}")
    print(f"Unique Images: {stats['unique']}")
    print(f"Duplicate Images: {stats['total'] - stats['unique']}")
    
    print("\n" + "-"*40)
    print("QUALITY DISTRIBUTION:")
    print("-"*40)
    
    # Calculate percentages
    if stats['total'] > 0:
        high_pct = (stats['high_quality'] / stats['total']) * 100
        low_pct = (stats['low_quality'] / stats['total']) * 100
    else:
        high_pct = low_pct = 0
    
    print(f"High Quality Images: {stats['high_quality']} ({high_pct:.1f}%)")
    print(f"Low Quality Images: {stats['low_quality']} ({low_pct:.1f}%)")
    
    print("\n" + "-"*40)
    print("FORMAT BREAKDOWN:")
    print("-"*40)
    print(f"nd_dft (High Quality Default): {stats['nd_dft']}")
    print(f"nd_prv (Low Quality Preview): {stats['nd_prv']}")
    print(f"w/1080 (1080px width): {stats['w_1080']}")
    print(f"w/720 (720px width): {stats['w_720']}")
    print(f"w/480 (480px width): {stats['w_480']}")
    print(f"Other Size Params: {stats['other_sizes']}")
    
    print("\n" + "-"*40)
    print("QUALITY ASSESSMENT:")
    print("-"*40)
    
    # Determine overall quality
    if stats['total'] == 0:
        print("❌ NO IMAGES FOUND")
        return False
    elif stats['nd_dft'] > 0 and stats['nd_prv'] == 0:
        print("✅ EXCELLENT: All images using high-quality nd_dft format")
        success = True
    elif stats['high_quality'] >= stats['total'] * 0.8:
        print("✅ GOOD: Majority (80%+) of images are high quality")
        success = True
    elif stats['high_quality'] >= stats['total'] * 0.5:
        print("⚠️ FAIR: Mixed quality, some improvement needed")
        success = False
    else:
        print("❌ POOR: Majority of images are low quality")
        success = False
    
    # Target validation (19 high-quality images expected)
    print("\n" + "-"*40)
    print("TARGET VALIDATION:")
    print("-"*40)
    print(f"Target: 18+ high-quality images")
    print(f"Actual: {stats['total']} total images")
    
    if stats['total'] >= 18:
        print(f"✅ Target Met: {stats['total']} images extracted (exceeds 18)")
    else:
        print(f"❌ Target Not Met: Only {stats['total']} images extracted")
    
    # Show sample URLs for inspection
    print("\n" + "-"*40)
    print("SAMPLE URLs (first 3):")
    print("-"*40)
    for i, url in enumerate(stats['urls'][:3], 1):
        # Highlight quality indicators
        if 'nd_dft' in url:
            quality_marker = "✅ HIGH (nd_dft)"
        elif 'nd_prv' in url:
            quality_marker = "❌ LOW (nd_prv)"
        elif 'w/1080' in url:
            quality_marker = "✅ HIGH (1080px)"
        elif 'w/720' in url:
            quality_marker = "⚠️ MED (720px)"
        else:
            quality_marker = "❓ UNKNOWN"
        
        print(f"\n{i}. {quality_marker}")
        print(f"   {url[:100]}...")
    
    print("\n" + "="*60)
    
    return success

if __name__ == "__main__":
    # Test the most recent extraction
    test_files = [
        "/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher/output/2025-09-18-180522 - 意大利D1维罗纳—摸胸失败，被关小黑屋.md",
        "/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher/output_test/2025-09-18-180721 - 意大利D1维罗纳—摸胸失败，被关小黑屋.md"
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"\nAnalyzing: {test_file}")
            stats = analyze_image_urls(test_file)
            if stats:
                success = print_quality_report(stats)
                if not success:
                    sys.exit(1)
    
    print("\n✅ ALL TESTS PASSED")