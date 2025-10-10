#!/usr/bin/env python3
"""
Non-interactive validation test for ManualChromeHelper module

This script validates that the module can be imported and initialized
without requiring user interaction.

Tests:
1. Module import
2. Configuration loading
3. Helper initialization
4. Chrome path validation
5. Port checking utilities

Usage:
    python test_manual_chrome_import.py
"""

import sys
import yaml
from pathlib import Path

print("\n" + "="*70)
print("  MANUAL CHROME MODULE - NON-INTERACTIVE VALIDATION")
print("="*70)
print()

# Test 1: Module import
print("Test 1: Importing manual_chrome module...")
try:
    from manual_chrome import ManualChromeHelper
    from manual_chrome.exceptions import (
        ManualChromeError,
        ChromeNotFoundError,
        PortInUseError,
        AttachmentError,
        TimeoutError
    )
    print("✓ Module imported successfully")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Configuration loading
print("\nTest 2: Loading configuration...")
config_path = Path(__file__).parent / "config" / "manual_chrome_config.yaml"
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    print(f"✓ Configuration loaded from: {config_path}")
    print(f"  - Platform: {config.get('platform', 'N/A')}")
    print(f"  - Debug port: {config.get('chrome', {}).get('debug_port', 'N/A')}")
    print(f"  - Auto-copy URL: {config.get('ux', {}).get('auto_copy_url', 'N/A')}")
except Exception as e:
    print(f"✗ Configuration loading failed: {e}")
    sys.exit(1)

# Test 3: Helper initialization
print("\nTest 3: Initializing ManualChromeHelper...")
try:
    helper = ManualChromeHelper(config)
    print("✓ ManualChromeHelper initialized successfully")
except Exception as e:
    print(f"✗ Initialization failed: {e}")
    sys.exit(1)

# Test 4: Chrome path validation
print("\nTest 4: Validating Chrome installation...")
try:
    helper._validate_chrome_installation()
    print(f"✓ Chrome found at: {helper.chrome_path}")
except ChromeNotFoundError as e:
    print(f"✗ Chrome not found: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Validation failed: {e}")
    sys.exit(1)

# Test 5: Port checking
print("\nTest 5: Checking debug port availability...")
try:
    helper._check_debug_port()
    port = config['chrome']['debug_port']
    print(f"✓ Port {port} is available")
except PortInUseError as e:
    print(f"⚠ Port check failed (this is OK if Chrome is running): {e}")
except Exception as e:
    print(f"⚠ Port check warning: {e}")

# Test 6: Exception classes
print("\nTest 6: Testing exception classes...")
try:
    exceptions = [
        ManualChromeError("test"),
        ChromeNotFoundError("test"),
        PortInUseError(9222),
        AttachmentError("test"),
        TimeoutError(300),
    ]
    print(f"✓ All {len(exceptions)} exception classes instantiated successfully")
except Exception as e:
    print(f"✗ Exception test failed: {e}")
    sys.exit(1)

# Summary
print("\n" + "="*70)
print("  VALIDATION RESULTS")
print("="*70)
print()
print("✓ All non-interactive tests passed!")
print()
print("The manual_chrome module is ready for interactive testing.")
print()
print("To run interactive test (requires user navigation):")
print("  python test_manual_chrome_module.py")
print()
print("="*70)
print()
