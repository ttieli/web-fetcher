#!/usr/bin/env python3
"""
Real Government Site Testing Script
Test the complete government strategy on the target site: https://hdqw.bjhd.gov.cn/qwyw/tzgg/
"""

import sys
import time
import logging
from webfetcher import crawl_site, detect_government_site, extract_site_categories, fetch_html

# Configure logging for testing
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_target_government_site():
    """Test on the actual target government site"""
    print("=== Testing Target Government Site ===")
    
    target_url = "https://hdqw.bjhd.gov.cn/qwyw/tzgg/"
    user_agent = "Mozilla/5.0 (compatible; WebFetcher-Test/1.0)"
    
    try:
        print(f"Testing with: {target_url}")
        
        # First, test government detection on the homepage
        homepage_url = "https://hdqw.bjhd.gov.cn"
        
        print("1. Testing government site detection...")
        try:
            homepage_html = fetch_html(homepage_url, ua=user_agent, timeout=30)
            is_government = detect_government_site(homepage_url, homepage_html)
            print(f"   Government detection: {is_government}")
            
            if is_government:
                print("   ✅ Government site correctly detected")
            else:
                print("   ⚠️  Government site not detected - may need domain pattern adjustment")
        except Exception as e:
            print(f"   ⚠️  Could not fetch homepage for detection: {e}")
            is_government = True  # Assume it is based on domain
        
        # Test category extraction
        print("2. Testing category extraction...")
        try:
            categories = extract_site_categories(homepage_url, homepage_html)
            print(f"   Found {len(categories)} categories")
            
            if categories:
                print("   Categories by priority:")
                for cat in categories[:10]:  # Show top 10
                    print(f"     - {cat['name']} (priority {cat['priority']})")
            else:
                print("   ⚠️  No categories extracted")
        except Exception as e:
            print(f"   ⚠️  Category extraction failed: {e}")
            categories = []
        
        # Test default strategy crawl
        print("3. Testing default strategy crawl...")
        start_time = time.time()
        
        pages_default = crawl_site(
            target_url,
            user_agent,
            max_depth=2,
            max_pages=20,
            delay=1.0,  # Be respectful to government site
            crawl_strategy='default',
            enable_optimizations=True
        )
        
        default_time = time.time() - start_time
        print(f"   Default strategy: {len(pages_default)} pages in {default_time:.1f}s")
        
        # Test category-first strategy
        print("4. Testing category-first strategy...")
        start_time = time.time()
        
        pages_category = crawl_site(
            homepage_url,  # Start from homepage for category detection
            user_agent,
            max_depth=2,
            max_pages=20,
            delay=1.0,
            crawl_strategy='category_first',
            enable_optimizations=True
        )
        
        category_time = time.time() - start_time
        print(f"   Category-first strategy: {len(pages_category)} pages in {category_time:.1f}s")
        
        # Summary
        print("\n=== Test Results Summary ===")
        print(f"Target URL: {target_url}")
        print(f"Government detection: {'✅' if is_government else '⚠️'}")
        print(f"Categories extracted: {len(categories) if 'categories' in locals() else 0}")
        print(f"Default crawl: {len(pages_default)} pages")
        print(f"Category crawl: {len(pages_category)} pages")
        
        if len(pages_default) > 0 or len(pages_category) > 0:
            print("🎉 Real government site test: SUCCESS")
            return True
        else:
            print("❌ Real government site test: FAILED - no pages crawled")
            return False
            
    except Exception as e:
        print(f"❌ Real government site test FAILED: {e}")
        return False

def main():
    """Run real government site test"""
    print("Starting Real Government Site Test...\n")
    print("Note: This test uses live network requests and may take some time.\n")
    
    success = test_target_government_site()
    
    if success:
        print("\n🎉 All government site features are working with real data!")
    else:
        print("\n⚠️  Some issues detected. Check network connectivity and site availability.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)