#!/usr/bin/env python3
"""
Quick Fix Validation Script
Rapid validation for backward compatibility fix
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def validate_fix():
    """Quick validation of the compatibility fix"""
    
    print("\n" + "="*60)
    print("QUICK FIX VALIDATION")
    print("="*60)
    
    # Step 1: Check if fetch_html_with_metrics exists
    print("\n[1] Checking fetch_html_with_metrics alias...")
    try:
        import webfetcher
        if hasattr(webfetcher, 'fetch_html_with_metrics'):
            print("✓ fetch_html_with_metrics exists")
            
            # Check if it's callable
            if callable(webfetcher.fetch_html_with_metrics):
                print("✓ fetch_html_with_metrics is callable")
                
                # Check if it points to the right function
                if webfetcher.fetch_html_with_metrics == webfetcher.fetch_html_with_plugins:
                    print("✓ fetch_html_with_metrics correctly aliased to fetch_html_with_plugins")
                else:
                    print("✗ fetch_html_with_metrics not properly aliased")
                    return False
            else:
                print("✗ fetch_html_with_metrics is not callable")
                return False
        else:
            print("✗ fetch_html_with_metrics does not exist")
            print("\nFIX REQUIRED:")
            print("Add the following line to webfetcher.py after line 1462:")
            print("fetch_html_with_metrics = fetch_html_with_plugins")
            return False
    except Exception as e:
        print(f"✗ Error checking alias: {e}")
        return False
    
    # Step 2: Test with example.com
    print("\n[2] Testing with https://www.example.com...")
    test_url = "https://www.example.com"
    
    try:
        start_time = time.time()
        html, metrics = webfetcher.fetch_html_with_metrics(test_url)
        elapsed = time.time() - start_time
        
        if html and len(html) > 0:
            print(f"✓ Successfully fetched {len(html)} bytes in {elapsed:.2f}s")
            print(f"✓ Method used: {metrics.primary_method}")
            
            # Check content validity
            if "Example Domain" in html or "example" in html.lower():
                print("✓ Content validation passed")
            else:
                print("⚠ Content might be unexpected")
        else:
            print("✗ No content returned")
            return False
            
    except Exception as e:
        print(f"✗ Error fetching content: {e}")
        return False
    
    # Step 3: Verify all aliases work
    print("\n[3] Testing all function aliases...")
    test_functions = [
        "fetch_html",
        "fetch_html_with_metrics",
        "fetch_html_with_plugins"
    ]
    
    for func_name in test_functions:
        if hasattr(webfetcher, func_name):
            try:
                func = getattr(webfetcher, func_name)
                result = func(test_url)
                if isinstance(result, tuple):
                    html, _ = result
                else:
                    html = result
                    
                if html and len(html) > 0:
                    print(f"✓ {func_name}: OK ({len(html)} bytes)")
                else:
                    print(f"✗ {func_name}: No content")
                    return False
            except Exception as e:
                print(f"✗ {func_name}: {e}")
                return False
        else:
            print(f"✗ {func_name}: Not found")
            return False
    
    print("\n" + "="*60)
    print("✓ ALL VALIDATIONS PASSED")
    print("Backward compatibility: RESTORED")
    print("="*60)
    return True

if __name__ == "__main__":
    success = validate_fix()
    sys.exit(0 if success else 1)