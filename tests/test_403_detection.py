#!/usr/bin/env python3
"""
Test script to analyze 403 error detection and Safari fallback behavior.
"""

import os
import sys
import logging

# Set up verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Check environment variables
print("\n=== Environment Variable Check ===")
print(f"WF_ENABLE_SAFARI: {os.environ.get('WF_ENABLE_SAFARI', 'not set')}")
print(f"WF_SAFARI_GOV_ONLY: {os.environ.get('WF_SAFARI_GOV_ONLY', 'not set')}")
print(f"WF_CCDI_ENABLED: {os.environ.get('WF_CCDI_ENABLED', 'not set')}")
print(f"WF_SAFARI_AUTO_DETECT: {os.environ.get('WF_SAFARI_AUTO_DETECT', 'not set')}")

# Test Safari module availability
print("\n=== Safari Module Availability ===")
try:
    # Try importing Safari modules
    if os.environ.get('WF_ENABLE_SAFARI', '1') == '1':
        from plugins.safari.extractor import should_fallback_to_safari, extract_with_safari_fallback
        print("✓ Safari extractor module imported successfully")
        SAFARI_AVAILABLE = True
    else:
        print("✗ Safari disabled by WF_ENABLE_SAFARI environment variable")
        SAFARI_AVAILABLE = False
except ImportError as e:
    print(f"✗ Safari extractor import failed: {e}")
    SAFARI_AVAILABLE = False

# Test Safari configuration
if SAFARI_AVAILABLE:
    print("\n=== Safari Configuration Test ===")
    from plugins.safari.config import (
        SAFARI_ENABLED, SAFARI_GOV_ONLY, SAFARI_AUTO_DETECT,
        get_site_config, should_use_safari_for_url, 
        detect_captcha_or_block, validate_safari_availability
    )
    
    print(f"SAFARI_ENABLED: {SAFARI_ENABLED}")
    print(f"SAFARI_GOV_ONLY: {SAFARI_GOV_ONLY}")
    print(f"SAFARI_AUTO_DETECT: {SAFARI_AUTO_DETECT}")
    
    # Test CCDI URL
    test_url = "https://www.ccdi.gov.cn/yaowenn/202509/t20250918_448431.html"
    print(f"\nTesting URL: {test_url}")
    
    # Get site config
    site_config = get_site_config(test_url)
    print(f"Site config: {site_config}")
    
    # Check if Safari should be used
    should_use = should_use_safari_for_url(test_url)
    print(f"Should use Safari for URL: {should_use}")
    
    # Test error detection
    print("\n=== Error Detection Test ===")
    
    # Simulate a 403 error
    from urllib.error import HTTPError
    from urllib.request import Request
    
    # Create a mock 403 error
    req = Request(test_url)
    mock_error = HTTPError(test_url, 403, "Forbidden", {}, None)
    
    # Test if 403 triggers Safari fallback
    error_msg = f"HTTP error {mock_error.code} for {test_url}"
    print(f"Testing error message: {error_msg}")
    
    # Check CAPTCHA/block detection
    captcha_detected = detect_captcha_or_block("", error_msg)
    print(f"CAPTCHA/block detected from error: {captcha_detected}")
    
    # Check if Safari fallback would trigger
    if hasattr(should_fallback_to_safari, '__call__'):
        fallback_triggered = should_fallback_to_safari(test_url, "", mock_error)
        print(f"Safari fallback would trigger: {fallback_triggered}")
    
    # Validate Safari availability
    print("\n=== Safari Availability Check ===")
    available, message = validate_safari_availability()
    print(f"Safari available: {available}")
    print(f"Message: {message}")

# Check if 403 is in retryable status codes
print("\n=== Retry Logic Check ===")
from webfetcher import RETRYABLE_HTTP_STATUS_CODES, should_retry_exception

print(f"Retryable HTTP status codes: {RETRYABLE_HTTP_STATUS_CODES}")
print(f"Is 403 retryable: {403 in RETRYABLE_HTTP_STATUS_CODES}")

# Create a real HTTPError to test
from urllib.error import HTTPError
from urllib.request import Request

try:
    # Create a mock request
    req = Request("https://www.ccdi.gov.cn/test")
    # Create actual HTTPError with 403 status
    error_403 = HTTPError(req.full_url, 403, "Forbidden", {}, None)
    is_retryable = should_retry_exception(error_403)
    print(f"403 error considered retryable: {is_retryable}")
except Exception as e:
    print(f"Error creating test HTTPError: {e}")

print("\n=== Analysis Complete ===")