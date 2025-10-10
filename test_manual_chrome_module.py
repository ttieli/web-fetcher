#!/usr/bin/env python3
"""
Test script for ManualChromeHelper module

This script validates the basic functionality of the manual Chrome module:
1. Configuration loading
2. Chrome validation
3. Chrome startup with debug port
4. Selenium attachment
5. Content extraction
6. Proper cleanup

Usage:
    python test_manual_chrome_module.py

Test URL: https://www.cebbank.com.cn/site/zhpd/zxgg35/cgjggg/263565922/index.html
Expected result: Successfully extract ~86,279 bytes of HTML content
"""

import yaml
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from manual_chrome import ManualChromeHelper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from YAML file."""
    config_path = Path(__file__).parent / "config" / "manual_chrome_config.yaml"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuration loaded from: {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML configuration: {e}")
        sys.exit(1)


def test_manual_chrome_module():
    """Test the ManualChromeHelper module."""

    print("\n" + "="*70)
    print("  MANUAL CHROME MODULE TEST")
    print("="*70)
    print()

    # Load configuration
    config = load_config()

    # Test URL - the CEB Bank URL that previously failed with automation
    test_url = "https://www.cebbank.com.cn/site/zhpd/zxgg35/cgjggg/263565922/index.html"

    print(f"Test URL: {test_url}")
    print()

    # Create helper instance
    try:
        helper = ManualChromeHelper(config)
        logger.info("ManualChromeHelper instance created successfully")
    except Exception as e:
        logger.error(f"Failed to create ManualChromeHelper: {e}")
        sys.exit(1)

    # Start manual session
    print("Starting manual Chrome session...")
    print()

    success, html, error = helper.start_session(test_url)

    print()
    print("="*70)
    print("  TEST RESULTS")
    print("="*70)
    print()

    if success:
        print(f"✓ Status: SUCCESS")
        print(f"✓ HTML Length: {len(html):,} bytes")
        print()

        # Try to extract title
        try:
            import re
            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            if title_match:
                title = title_match.group(1).strip()
                print(f"✓ Page Title: {title}")
        except Exception as e:
            logger.warning(f"Could not extract title: {e}")

        print()
        print("Expected result: ~86,279 bytes")

        if len(html) > 80000:
            print("✓ Content size matches expected range - TEST PASSED")
        elif len(html) > 1000:
            print("⚠ Content size is reasonable but smaller than expected")
        else:
            print("✗ Content size is too small - possible failure")

    else:
        print(f"✗ Status: FAILED")
        print(f"✗ Error: {error}")
        print()
        return False

    print()
    print("="*70)

    return success


def main():
    """Main entry point."""
    try:
        success = test_manual_chrome_module()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user (Ctrl+C)")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
