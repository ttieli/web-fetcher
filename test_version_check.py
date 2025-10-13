#!/usr/bin/env python3
"""
Test script for Task-011 Phase 2: ChromeDriver Version Management

This script tests the version detection and compatibility checking functionality.

Author: Cody (Claude Code)
Date: 2025-10-13
Task: Task-011 Phase 2
"""

import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the version check functions
from selenium_fetcher import check_chromedriver_compatibility, check_version_compatibility_with_chrome

def test_chromedriver_detection():
    """Test ChromeDriver version detection"""
    print("\n" + "="*80)
    print("TEST 1: ChromeDriver Version Detection")
    print("="*80)

    is_compatible, message, chrome_ver, driver_ver = check_chromedriver_compatibility()

    print(f"\nResults:")
    print(f"  ChromeDriver version: {driver_ver}")
    print(f"  Chrome version (pending): {chrome_ver}")
    print(f"  Initial compatibility: {is_compatible}")

    if message:
        print(f"\nMessage:")
        print(message)

    return driver_ver


def test_version_compatibility(chrome_ver, driver_ver):
    """Test version compatibility checking with known versions"""
    print("\n" + "="*80)
    print("TEST 2: Version Compatibility Check")
    print("="*80)

    print(f"\nTesting with:")
    print(f"  Chrome version: {chrome_ver}")
    print(f"  ChromeDriver version: {driver_ver}")

    is_compatible, message = check_version_compatibility_with_chrome(chrome_ver, driver_ver)

    print(f"\nCompatibility result: {is_compatible}")

    if message:
        print(f"\nMessage:")
        print(message)

    return is_compatible


def test_version_scenarios():
    """Test different version mismatch scenarios"""
    print("\n" + "="*80)
    print("TEST 3: Version Mismatch Scenarios")
    print("="*80)

    test_cases = [
        ("141.0.7390.76", "141.0.7339.207", "Compatible - Same major version"),
        ("141.0.7390.76", "140.0.7339.207", "Minor mismatch - Differ by 1"),
        ("143.0.0.0", "140.0.0.0", "Major mismatch - Differ by 3"),
        ("130.0.0.0", "131.0.0.0", "Minor mismatch - Differ by 1 (reversed)"),
    ]

    for chrome_v, driver_v, description in test_cases:
        print(f"\n--- {description} ---")
        print(f"Chrome: {chrome_v}, ChromeDriver: {driver_v}")

        is_compatible, message = check_version_compatibility_with_chrome(chrome_v, driver_v)
        print(f"Result: {'✓ Compatible' if is_compatible else '✗ Incompatible'}")

        if message:
            # Show first line of message
            first_line = message.split('\n')[0]
            print(f"Message: {first_line}")


def main():
    """Main test execution"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "Task-011 Phase 2: Version Management Test" + " "*15 + "║")
    print("╚" + "="*78 + "╝")

    try:
        # Test 1: ChromeDriver detection
        driver_ver = test_chromedriver_detection()

        # Test 2: Check compatibility with actual Chrome version
        if driver_ver not in ["unknown", "not_found", "pending"]:
            # Use actual Chrome version from debug session
            chrome_ver = "141.0.7390.76"  # Current Chrome version
            test_version_compatibility(chrome_ver, driver_ver)

        # Test 3: Test different scenarios
        test_version_scenarios()

        print("\n" + "="*80)
        print("ALL TESTS COMPLETED")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
