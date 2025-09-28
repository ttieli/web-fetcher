#!/usr/bin/env python3
"""
Phase 2 Validation Test Suite
Comprehensive tests to verify urllib-only functionality after Safari/plugin removal
"""

import sys
import json
import traceback
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_import_sanity():
    """Test 1: Verify webfetcher imports without errors"""
    print("\n=== Test 1: Import Sanity Check ===")
    try:
        import webfetcher
        print("✓ webfetcher module imports successfully")
        
        # Check that fetch_html exists
        if hasattr(webfetcher, 'fetch_html'):
            print("✓ fetch_html function exists")
        else:
            print("✗ fetch_html function missing")
            return False
            
        # Check that Safari is disabled
        if hasattr(webfetcher, 'SAFARI_AVAILABLE'):
            if webfetcher.SAFARI_AVAILABLE:
                print("✗ SAFARI_AVAILABLE is True (should be False or removed)")
                return False
            else:
                print("✓ SAFARI_AVAILABLE is False")
        else:
            print("✓ SAFARI_AVAILABLE not found (removed)")
            
        # Check that plugin system is disabled
        if hasattr(webfetcher, 'PLUGIN_SYSTEM_AVAILABLE'):
            if webfetcher.PLUGIN_SYSTEM_AVAILABLE:
                print("✗ PLUGIN_SYSTEM_AVAILABLE is True (should be False or removed)")
                return False
            else:
                print("✓ PLUGIN_SYSTEM_AVAILABLE is False")
        else:
            print("✓ PLUGIN_SYSTEM_AVAILABLE not found (removed)")
            
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        traceback.print_exc()
        return False


def test_urllib_functionality():
    """Test 2: Verify urllib fetch works for test URLs"""
    print("\n=== Test 2: Urllib Fetch Functionality ===")
    
    try:
        from webfetcher import fetch_html
        
        # Test with a reliable URL
        test_url = "https://example.com"
        print(f"Testing fetch for {test_url}...")
        
        html, metrics = fetch_html(test_url)
        
        if html and len(html) > 0:
            print(f"✓ Fetched {len(html)} bytes")
            print(f"  Method used: {metrics.primary_method}")
            print(f"  Status: {metrics.final_status}")
            
            # Verify it's using urllib or curl, not Safari/plugins
            if metrics.primary_method in ['urllib', 'curl']:
                print(f"✓ Using correct fetch method: {metrics.primary_method}")
                return True
            else:
                print(f"✗ Using unexpected method: {metrics.primary_method}")
                return False
        else:
            print("✗ No content fetched")
            return False
            
    except Exception as e:
        print(f"✗ Fetch failed: {e}")
        traceback.print_exc()
        return False


def test_curl_fallback():
    """Test 3: Verify curl fallback mechanism"""
    print("\n=== Test 3: Curl Fallback Mechanism ===")
    
    try:
        from webfetcher import fetch_html_with_curl_metrics
        
        # Test curl directly
        test_url = "https://example.com"
        print(f"Testing curl fetch for {test_url}...")
        
        html, metrics = fetch_html_with_curl_metrics(test_url)
        
        if html and len(html) > 0:
            print(f"✓ Curl fetched {len(html)} bytes")
            print(f"  Method: {metrics.primary_method}")
            
            if metrics.primary_method == 'curl':
                print("✓ Curl fallback works correctly")
                return True
            else:
                print(f"✗ Unexpected method: {metrics.primary_method}")
                return False
        else:
            print("✗ No content fetched via curl")
            return False
            
    except Exception as e:
        print(f"✗ Curl test failed: {e}")
        traceback.print_exc()
        return False


def test_core_sites():
    """Test 4: Verify core sites can be fetched"""
    print("\n=== Test 4: Core Sites Fetch Test ===")
    
    try:
        from webfetcher import fetch_html
        
        # Note: Using example.com as proxy since real sites may block
        # In production, test with actual URLs
        test_sites = {
            "WeChat proxy": "https://example.com",  # Simulating mp.weixin.qq.com
            "XHS proxy": "https://example.org",     # Simulating xiaohongshu.com  
            "News proxy": "https://example.net"     # Simulating news.cn
        }
        
        results = {}
        for site_name, url in test_sites.items():
            try:
                print(f"\nTesting {site_name}: {url}")
                html, metrics = fetch_html(url, timeout=10)
                
                if html and len(html) > 0:
                    print(f"  ✓ Fetched {len(html)} bytes")
                    print(f"    Method: {metrics.primary_method}")
                    print(f"    Duration: {metrics.fetch_duration:.2f}s")
                    results[site_name] = "success"
                else:
                    print(f"  ✗ No content fetched")
                    results[site_name] = "no_content"
                    
            except Exception as e:
                print(f"  ✗ Failed: {e}")
                results[site_name] = f"error: {str(e)}"
        
        # Check if all succeeded
        success_count = sum(1 for v in results.values() if v == "success")
        print(f"\n{success_count}/{len(test_sites)} sites fetched successfully")
        
        return success_count == len(test_sites)
        
    except Exception as e:
        print(f"✗ Core sites test failed: {e}")
        traceback.print_exc()
        return False


def test_no_safari_references():
    """Test 5: Verify no Safari references remain in code"""
    print("\n=== Test 5: Safari Reference Check ===")
    
    try:
        webfetcher_path = Path(__file__).parent.parent / "webfetcher.py"
        content = webfetcher_path.read_text()
        
        safari_patterns = [
            "SAFARI_AVAILABLE",
            "should_fallback_to_safari",
            "extract_with_safari_fallback",
            "requires_safari_preemptively",
            "plugins.safari",
            "from plugins.safari"
        ]
        
        found_references = []
        for pattern in safari_patterns:
            if pattern in content:
                # Count occurrences
                count = content.count(pattern)
                found_references.append(f"{pattern} ({count} occurrences)")
        
        if found_references:
            print("✗ Found Safari references:")
            for ref in found_references:
                print(f"  - {ref}")
            return False
        else:
            print("✓ No Safari references found")
            return True
            
    except Exception as e:
        print(f"✗ Reference check failed: {e}")
        return False


def test_no_plugin_references():
    """Test 6: Verify no plugin system references remain"""
    print("\n=== Test 6: Plugin System Reference Check ===")
    
    try:
        webfetcher_path = Path(__file__).parent.parent / "webfetcher.py"
        content = webfetcher_path.read_text()
        
        plugin_patterns = [
            "PLUGIN_SYSTEM_AVAILABLE",
            "fetch_html_with_plugins",
            "get_global_registry",
            "FetchContext",
            "from plugins import"
        ]
        
        found_references = []
        for pattern in plugin_patterns:
            if pattern in content:
                count = content.count(pattern)
                found_references.append(f"{pattern} ({count} occurrences)")
        
        if found_references:
            print("✗ Found plugin system references:")
            for ref in found_references:
                print(f"  - {ref}")
            return False
        else:
            print("✓ No plugin system references found")
            return True
            
    except Exception as e:
        print(f"✗ Reference check failed: {e}")
        return False


def generate_report(results):
    """Generate a JSON report of test results"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "phase": "Phase 2 - Urllib Only Transition",
        "tests": results,
        "overall_status": "PASS" if all(results.values()) else "FAIL",
        "summary": {
            "total_tests": len(results),
            "passed": sum(1 for v in results.values() if v),
            "failed": sum(1 for v in results.values() if not v)
        }
    }
    
    report_path = Path(__file__).parent / f"phase2_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport saved to: {report_path}")
    return report


def main():
    """Run all validation tests"""
    print("=" * 60)
    print("Phase 2 Validation Test Suite")
    print("Testing urllib-only functionality")
    print("=" * 60)
    
    results = {}
    
    # Run tests in sequence
    tests = [
        ("Import Sanity", test_import_sanity),
        ("Urllib Functionality", test_urllib_functionality),
        ("Curl Fallback", test_curl_fallback),
        ("Core Sites", test_core_sites),
        ("No Safari References", test_no_safari_references),
        ("No Plugin References", test_no_plugin_references)
    ]
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Generate summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    # Generate report
    report = generate_report(results)
    
    # Overall result
    if all(results.values()):
        print("\n✓ ALL TESTS PASSED - Phase 2 transition successful!")
        return 0
    else:
        failed_count = sum(1 for v in results.values() if not v)
        print(f"\n✗ {failed_count} TEST(S) FAILED - Review and fix issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())