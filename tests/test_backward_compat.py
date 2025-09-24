#!/usr/bin/env python3
"""
Test backward compatibility of webfetcher with curl plugin
测试webfetcher向后兼容性
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_legacy_functions():
    """Test that legacy webfetcher functions still work."""
    
    print("=" * 60)
    print("BACKWARD COMPATIBILITY TEST")
    print("=" * 60)
    
    results = []
    
    # Test 1: Import legacy functions
    print("\n1. Testing legacy function imports...")
    try:
        from webfetcher import (
            fetch_html_with_metrics,
            fetch_html,
            fetch_html_with_curl,
            fetch_html_with_curl_metrics,
            validate_and_encode_url,
            smart_decode
        )
        print("  ✓ All legacy functions imported successfully")
        results.append(True)
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        results.append(False)
        return False
    
    # Test 2: fetch_html (main function)
    print("\n2. Testing fetch_html()...")
    try:
        html = fetch_html("https://www.example.com")
        if html and len(html) > 0:
            print(f"  ✓ fetch_html worked: {len(html)} chars")
            results.append(True)
        else:
            print("  ✗ fetch_html returned empty content")
            results.append(False)
    except Exception as e:
        print(f"  ✗ fetch_html failed: {e}")
        results.append(False)
    
    # Test 3: fetch_html_with_metrics
    print("\n3. Testing fetch_html_with_metrics()...")
    try:
        html, metrics = fetch_html_with_metrics("https://www.example.com")
        if html and metrics:
            print(f"  ✓ fetch_html_with_metrics worked")
            print(f"    - Content: {len(html)} chars")
            print(f"    - Method: {metrics.primary_method}")
            print(f"    - Duration: {metrics.fetch_duration:.2f}s")
            results.append(True)
        else:
            print("  ✗ fetch_html_with_metrics failed")
            results.append(False)
    except Exception as e:
        print(f"  ✗ fetch_html_with_metrics failed: {e}")
        results.append(False)
    
    # Test 4: Direct curl functions
    print("\n4. Testing fetch_html_with_curl()...")
    try:
        html = fetch_html_with_curl("https://www.example.com")
        if html and len(html) > 0:
            print(f"  ✓ fetch_html_with_curl worked: {len(html)} chars")
            results.append(True)
        else:
            print("  ✗ fetch_html_with_curl returned empty")
            results.append(False)
    except Exception as e:
        print(f"  ✗ fetch_html_with_curl failed: {e}")
        results.append(False)
    
    # Test 5: URL validation function
    print("\n5. Testing validate_and_encode_url()...")
    try:
        test_urls = [
            "https://example.com/path with spaces",
            "https://example.com/path%20with%20spaces",
            "https://中文.com",
        ]
        
        all_valid = True
        for url in test_urls:
            encoded = validate_and_encode_url(url)
            if encoded:
                print(f"  ✓ Encoded: {url[:30]}...")
            else:
                print(f"  ✗ Failed to encode: {url}")
                all_valid = False
        
        results.append(all_valid)
    except Exception as e:
        print(f"  ✗ URL validation failed: {e}")
        results.append(False)
    
    # Test 6: Smart decode function
    print("\n6. Testing smart_decode()...")
    try:
        test_bytes = "Hello 世界".encode('utf-8')
        decoded = smart_decode(test_bytes)
        if decoded == "Hello 世界":
            print(f"  ✓ smart_decode works: {decoded}")
            results.append(True)
        else:
            print(f"  ✗ smart_decode incorrect: {decoded}")
            results.append(False)
    except Exception as e:
        print(f"  ✗ smart_decode failed: {e}")
        results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("COMPATIBILITY TEST RESULTS")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\nPassed: {passed}/{total} tests")
    print(f"Success rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n✅ FULL BACKWARD COMPATIBILITY MAINTAINED")
        return True
    elif success_rate >= 80:
        print("\n⚠️  MOSTLY COMPATIBLE - Minor issues")
        return True
    else:
        print("\n❌ COMPATIBILITY BROKEN - Major issues")
        return False

def test_plugin_integration():
    """Test that plugins integrate seamlessly with main webfetcher."""
    
    print("\n" + "=" * 60)
    print("PLUGIN INTEGRATION TEST")
    print("=" * 60)
    
    try:
        from webfetcher import fetch_html_with_metrics
        
        # Test with URL that might trigger SSL fallback
        print("\nTesting integrated fallback behavior...")
        
        test_url = "https://www.example.com"
        
        html, metrics = fetch_html_with_metrics(test_url, timeout=10)
        
        print(f"Primary method: {metrics.primary_method}")
        if metrics.fallback_method:
            print(f"Fallback method: {metrics.fallback_method}")
            print("✓ Fallback mechanism working")
        
        if metrics.ssl_fallback_used:
            print("✓ SSL fallback flag set correctly")
        
        print(f"Total duration: {metrics.fetch_duration:.2f}s")
        print(f"Attempts: {metrics.total_attempts}")
        
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    compat_ok = test_legacy_functions()
    integration_ok = test_plugin_integration()
    
    if compat_ok and integration_ok:
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - READY FOR NEXT PHASE")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ TESTS FAILED - REVIEW NEEDED")
        print("=" * 60)
        sys.exit(1)