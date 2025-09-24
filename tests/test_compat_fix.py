#!/usr/bin/env python3
"""
Test to verify the required function aliases exist in webfetcher
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Checking webfetcher function exports...")

# Check what functions are actually available
import webfetcher
import inspect

# Get all functions in webfetcher module
functions = [name for name, obj in inspect.getmembers(webfetcher) if inspect.isfunction(obj)]

print("\nAvailable functions in webfetcher:")
for func in sorted(functions):
    if 'fetch' in func.lower():
        print(f"  - {func}")

# Check for required functions
required = [
    'fetch_html',
    'fetch_html_with_metrics', 
    'fetch_html_with_curl',
    'fetch_html_with_curl_metrics'
]

print("\nChecking required functions:")
missing = []
for func_name in required:
    if hasattr(webfetcher, func_name):
        func = getattr(webfetcher, func_name)
        actual_name = func.__name__ if hasattr(func, '__name__') else 'unknown'
        print(f"  ✓ {func_name} -> {actual_name}")
    else:
        print(f"  ✗ {func_name} MISSING")
        missing.append(func_name)

if missing:
    print(f"\n❌ Missing functions: {', '.join(missing)}")
    print("\nNeed to add these aliases to webfetcher.py:")
    print("  fetch_html_with_metrics = fetch_html_with_plugins")
else:
    print("\n✅ All required functions present")