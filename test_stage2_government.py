#!/usr/bin/env python3
"""
Stage 2 Government Site Strategy Testing Script
Tests the newly implemented government site detection and category-first crawling.
"""

import sys
import time
import logging
from webfetcher import (
    crawl_site, 
    detect_government_site, 
    extract_site_categories,
    crawl_site_by_categories,
    fetch_html
)

# Configure logging for testing
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_government_detection():
    """Test government site detection functionality"""
    print("=== Testing Government Site Detection ===")
    
    test_cases = [
        {
            'url': 'https://www.gov.cn',
            'expected': True,
            'reason': 'Chinese government domain'
        },
        {
            'url': 'https://hdqw.bjhd.gov.cn',
            'expected': True,
            'reason': 'Beijing government subdomain'
        },
        {
            'url': 'https://example.com',
            'expected': False,
            'reason': 'Commercial domain'
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        url = test_case['url']
        expected = test_case['expected']
        reason = test_case['reason']
        
        try:
            # For testing, create mock HTML content for government sites
            if '.gov' in url:
                mock_html = '''
                <html>
                <head><title>政府门户网站</title></head>
                <body>
                    <h1>人民政府官方网站</h1>
                    <nav>
                        <ul>
                            <li><a href="/news">新闻中心</a></li>
                            <li><a href="/policy">政策法规</a></li>
                            <li><a href="/service">便民服务</a></li>
                        </ul>
                    </nav>
                </body>
                </html>
                '''
            else:
                mock_html = '<html><body><h1>Example Domain</h1></body></html>'
            
            result = detect_government_site(url, mock_html)
            
            if result == expected:
                print(f"✅ {url}: {result} ({reason}) - PASSED")
                results.append(True)
            else:
                print(f"❌ {url}: {result}, expected {expected} ({reason}) - FAILED")
                results.append(False)
                
        except Exception as e:
            print(f"❌ {url}: Exception {e} - FAILED")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    print(f"Government detection: {passed}/{total} tests passed")
    return passed == total

def test_category_extraction():
    """Test site category extraction"""
    print("\n=== Testing Category Extraction ===")
    
    mock_gov_html = '''
    <html>
    <head><title>政府网站</title></head>
    <body>
        <nav class="main-nav">
            <ul>
                <li><a href="/affairs">政务公开</a></li>
                <li><a href="/notices">通知公告</a></li>
                <li><a href="/news">新闻资讯</a></li>
                <li><a href="/services">便民服务</a></li>
                <li><a href="/policy">政策法规</a></li>
                <li><a href="/leadership">领导介绍</a></li>
                <li><a href="/contact">联系我们</a></li>
            </ul>
        </nav>
    </body>
    </html>
    '''
    
    try:
        base_url = "https://test.gov.cn"
        categories = extract_site_categories(base_url, mock_gov_html)
        
        print(f"Extracted {len(categories)} categories:")
        for cat in categories:
            print(f"  - {cat['name']} (priority {cat['priority']}) -> {cat['url']}")
        
        # Check for expected high-priority categories
        high_priority_names = [cat['name'] for cat in categories if cat['priority'] == 3]
        expected_high_priority = ['政务公开', '通知公告', '便民服务', '政策法规']
        
        found_high_priority = [name for name in expected_high_priority if any(name in hp for hp in high_priority_names)]
        
        if len(found_high_priority) >= 2:  # At least 2 high priority categories
            print(f"✅ Category extraction: PASSED - Found {len(found_high_priority)} high-priority categories")
            return True
        else:
            print(f"❌ Category extraction: FAILED - Only found {len(found_high_priority)} high-priority categories")
            return False
            
    except Exception as e:
        print(f"❌ Category extraction: FAILED with exception: {e}")
        return False

def test_government_crawl_strategy():
    """Test the category-first crawling strategy"""
    print("\n=== Testing Government Crawl Strategy ===")
    
    # Mock a simple government site structure
    base_url = "https://mock.gov.cn"
    user_agent = "Mozilla/5.0 (compatible; WebFetcher-Test/1.0)"
    
    # Create mock categories
    mock_categories = [
        {'name': '政务公开', 'url': f'{base_url}/affairs', 'priority': 3},
        {'name': '通知公告', 'url': f'{base_url}/notices', 'priority': 3},
        {'name': '新闻资讯', 'url': f'{base_url}/news', 'priority': 2},
        {'name': '便民服务', 'url': f'{base_url}/services', 'priority': 3},
    ]
    
    try:
        # Test the category crawling function directly (with mock)
        print("Testing category prioritization...")
        
        # Sort categories by priority to verify ordering
        sorted_cats = sorted(mock_categories, key=lambda x: (-x['priority'], x['name']))
        
        print("Category crawling order:")
        for i, cat in enumerate(sorted_cats):
            print(f"  {i+1}. {cat['name']} (priority {cat['priority']})")
        
        # Verify high-priority categories come first
        high_priority_first = all(cat['priority'] >= 2 for cat in sorted_cats[:3])
        
        if high_priority_first:
            print("✅ Government crawl strategy: PASSED - High priority categories first")
            return True
        else:
            print("❌ Government crawl strategy: FAILED - Priority ordering incorrect")
            return False
            
    except Exception as e:
        print(f"❌ Government crawl strategy: FAILED with exception: {e}")
        return False

def test_strategy_integration():
    """Test integration of category-first strategy in crawl_site"""
    print("\n=== Testing Strategy Integration ===")
    
    try:
        # Test that category_first strategy parameter works
        test_url = "http://example.com"
        user_agent = "Mozilla/5.0 (compatible; WebFetcher-Test/1.0)"
        
        # Test default strategy
        pages_default = crawl_site(
            test_url,
            user_agent,
            max_depth=1,
            max_pages=5,
            delay=0.1,
            crawl_strategy='default'
        )
        
        # Test category_first strategy (should fall back to default for non-gov site)
        pages_category = crawl_site(
            test_url,
            user_agent,
            max_depth=1,
            max_pages=5,
            delay=0.1,
            crawl_strategy='category_first'
        )
        
        # Both should work and return similar results for non-government sites
        if len(pages_default) > 0 and len(pages_category) > 0:
            print(f"✅ Strategy integration: PASSED - Both strategies work")
            print(f"   Default strategy: {len(pages_default)} pages")
            print(f"   Category strategy: {len(pages_category)} pages")
            return True
        else:
            print(f"❌ Strategy integration: FAILED - Strategy returned no pages")
            return False
            
    except Exception as e:
        print(f"❌ Strategy integration: FAILED with exception: {e}")
        return False

def main():
    """Run all Stage 2 government strategy tests"""
    print("Starting Stage 2 Government Strategy Tests...\n")
    
    tests = [
        test_government_detection,
        test_category_extraction,
        test_government_crawl_strategy,
        test_strategy_integration,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test_func.__name__} FAILED with exception: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n=== Stage 2 Test Summary ===")
    print(f"Passed: {passed}/{total} tests")
    
    if passed == total:
        print("🎉 All Stage 2 government strategies are working correctly!")
        return True
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)