#!/usr/bin/env python3
"""
Test SSL fallback functionality with curl plugin
测试curl插件的SSL回退功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugins.registry import get_global_registry
from plugins.base import FetchContext

def test_ssl_fallback():
    """Test fetching from URLs with known SSL issues."""
    
    print("=" * 60)
    print("SSL FALLBACK TEST WITH CURL PLUGIN")
    print("=" * 60)
    
    # Test URLs (including those known to have SSL issues)
    test_cases = [
        {
            "url": "https://httpbin.org/html",
            "name": "Normal HTTPS",
            "expect_success": True
        },
        {
            "url": "https://raw.githubusercontent.com/urllib3/urllib3/main/README.md",
            "name": "GitHub Raw (SSL issues)",
            "expect_success": True
        },
        {
            "url": "https://self-signed.badssl.com/",
            "name": "Self-signed cert",
            "expect_success": True  # Curl with -k should handle this
        },
        {
            "url": "https://expired.badssl.com/",
            "name": "Expired cert",
            "expect_success": True  # Curl with -k should handle this
        }
    ]
    
    registry = get_global_registry()
    
    for test in test_cases:
        print(f"\nTesting: {test['name']}")
        print(f"URL: {test['url']}")
        print("-" * 40)
        
        context = FetchContext(url=test['url'], timeout=15)
        
        # Get suitable plugins
        plugins = registry.get_suitable_plugins(context)
        plugin_names = [p.name for p in plugins]
        print(f"Available plugins: {plugin_names}")
        
        # Try fetching with fallback
        result = registry.fetch_with_fallback(context)
        
        if result.success:
            print(f"✓ Success with {result.fetch_method}")
            print(f"  Content length: {len(result.html_content)} chars")
            if result.metadata.get('ssl_fallback_used'):
                print("  ✓ SSL fallback was used")
            print(f"  Duration: {result.duration:.2f}s")
        else:
            if test['expect_success']:
                print(f"✗ Failed: {result.error_message}")
            else:
                print(f"✓ Failed as expected: {result.error_message}")
        
        # Check if result matches expectation
        if result.success == test['expect_success']:
            print(f"✅ Test PASSED")
        else:
            print(f"❌ Test FAILED - Expected {'success' if test['expect_success'] else 'failure'}")
    
    print("\n" + "=" * 60)
    print("SSL FALLBACK TEST COMPLETE")
    print("=" * 60)

def test_plugin_priority():
    """Test that curl is used as fallback, not primary."""
    
    print("\n" + "=" * 60)
    print("PLUGIN PRIORITY TEST")
    print("=" * 60)
    
    registry = get_global_registry()
    
    # Normal URL should use HTTP plugin first
    context = FetchContext(url="https://httpbin.org/html")
    plugins = registry.get_suitable_plugins(context)
    
    print("Plugin order for normal HTTPS:")
    for i, plugin in enumerate(plugins):
        print(f"  {i+1}. {plugin.name} (priority: {plugin.priority})")
    
    # Curl should NOT be first
    if plugins and plugins[0].name != "curl":
        print("✅ Curl is correctly positioned as fallback")
    else:
        print("❌ Curl should not be the primary plugin")
    
    # Test actual fetch order
    print("\nFetching with plugin chain...")
    result = registry.fetch_with_fallback(context)
    
    if result.success:
        print(f"✓ Fetched with: {result.fetch_method}")
        if result.fetch_method != "curl":
            print("✅ Primary plugin worked, curl not needed")
        else:
            print("⚠️  Curl was used (primary plugins may have failed)")

if __name__ == "__main__":
    test_ssl_fallback()
    test_plugin_priority()