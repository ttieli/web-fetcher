#!/usr/bin/env python3
"""
Backward Compatibility Test Template
Architecture-approved test template for webfetcher compatibility validation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Standard test configuration
TEST_URL = "https://www.example.com"
EXPECTED_FUNCTIONS = [
    "fetch_html",
    "fetch_html_with_metrics", 
    "fetch_html_with_plugins",
    "fetch_html_original",
    "fetch_html_with_curl"
]

def test_function_aliases():
    """Test that all backward compatibility aliases are present"""
    import webfetcher
    
    results = {}
    for func_name in EXPECTED_FUNCTIONS:
        exists = hasattr(webfetcher, func_name)
        callable_check = callable(getattr(webfetcher, func_name, None)) if exists else False
        results[func_name] = {
            "exists": exists,
            "callable": callable_check
        }
    
    return results

def test_function_signatures():
    """Test that function signatures remain compatible"""
    import inspect
    import webfetcher
    
    signatures = {}
    for func_name in EXPECTED_FUNCTIONS:
        if hasattr(webfetcher, func_name):
            func = getattr(webfetcher, func_name)
            sig = inspect.signature(func)
            signatures[func_name] = {
                "parameters": list(sig.parameters.keys()),
                "defaults": {k: v.default for k, v in sig.parameters.items() 
                           if v.default is not inspect.Parameter.empty}
            }
    
    return signatures

def test_basic_fetch():
    """Test basic fetch functionality with standard URL"""
    import webfetcher
    
    results = {}
    
    # Test each function variant
    test_functions = [
        ("fetch_html", lambda: webfetcher.fetch_html(TEST_URL)),
        ("fetch_html_with_metrics", lambda: webfetcher.fetch_html_with_metrics(TEST_URL)),
        ("fetch_html_with_plugins", lambda: webfetcher.fetch_html_with_plugins(TEST_URL))
    ]
    
    for func_name, func_call in test_functions:
        try:
            result = func_call()
            if isinstance(result, tuple):
                html, metrics = result
                results[func_name] = {
                    "success": True,
                    "has_content": len(html) > 0,
                    "has_metrics": metrics is not None,
                    "content_length": len(html)
                }
            else:
                # Legacy interface returning only HTML
                results[func_name] = {
                    "success": True,
                    "has_content": len(result) > 0,
                    "content_length": len(result),
                    "legacy_interface": True
                }
        except Exception as e:
            results[func_name] = {
                "success": False,
                "error": str(e)
            }
    
    return results

def main():
    """Run all compatibility tests"""
    print("=" * 60)
    print("WEBFETCHER BACKWARD COMPATIBILITY TEST")
    print("Test URL:", TEST_URL)
    print("=" * 60)
    
    # Test 1: Function Aliases
    print("\n[TEST 1] Function Aliases Check")
    print("-" * 40)
    alias_results = test_function_aliases()
    all_present = True
    for func_name, result in alias_results.items():
        status = "✓" if result["exists"] and result["callable"] else "✗"
        print(f"{status} {func_name}: exists={result['exists']}, callable={result['callable']}")
        if not (result["exists"] and result["callable"]):
            all_present = False
    
    # Test 2: Function Signatures
    print("\n[TEST 2] Function Signatures")
    print("-" * 40)
    signatures = test_function_signatures()
    for func_name, sig in signatures.items():
        print(f"{func_name}({', '.join(sig['parameters'])})")
        if sig['defaults']:
            print(f"  Defaults: {sig['defaults']}")
    
    # Test 3: Basic Fetch
    print("\n[TEST 3] Basic Fetch Operations")
    print("-" * 40)
    fetch_results = test_basic_fetch()
    all_successful = True
    for func_name, result in fetch_results.items():
        if result["success"]:
            print(f"✓ {func_name}: {result['content_length']} bytes fetched")
        else:
            print(f"✗ {func_name}: {result['error']}")
            all_successful = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("-" * 40)
    
    if all_present and all_successful:
        print("✓ ALL TESTS PASSED")
        print("Backward compatibility: CONFIRMED")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        if not all_present:
            print("- Missing function aliases detected")
        if not all_successful:
            print("- Some fetch operations failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())