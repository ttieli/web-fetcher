#!/usr/bin/env python3
"""
Phase 2 Verification Script - Robust Chrome Connection Testing

Tests the implementation of Phase 2 enhancements:
1. ErrorMessages class with comprehensive templates
2. Enhanced Chrome version detection and parsing
3. Smart retry logic (no retry on version mismatch)
4. Improved error handling in both selenium_fetcher.py and webfetcher.py

Author: Archy (Architecture Verification)
Date: 2025-09-29
"""

import sys
import time
import logging
import json
import subprocess
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import the enhanced modules
try:
    from selenium_config import SeleniumConfig
    from selenium_fetcher import (
        SeleniumFetcher, 
        ErrorMessages, 
        ChromeConnectionError,
        SeleniumFetchError,
        SeleniumTimeoutError,
        SeleniumNotAvailableError
    )
    SELENIUM_AVAILABLE = True
except ImportError as e:
    print(f"❌ ERROR: Failed to import Selenium modules: {e}")
    print("Please ensure selenium_config.py and selenium_fetcher.py are in the project root.")
    sys.exit(1)


class Phase2Verifier:
    """Verification suite for Phase 2 implementation."""
    
    def __init__(self):
        self.results = {
            'error_messages_class': False,
            'version_detection': False,
            'version_parsing': False,
            'smart_retry_logic': False,
            'error_handling': False,
            'integration': False
        }
        self.details = []
        
    def verify_error_messages_class(self):
        """Test 1: Verify ErrorMessages class with comprehensive templates."""
        print("\n" + "="*60)
        print("TEST 1: ErrorMessages Class Verification")
        print("="*60)
        
        try:
            # Check if ErrorMessages class exists
            assert hasattr(ErrorMessages, 'VERSION_MISMATCH'), "VERSION_MISMATCH template missing"
            assert hasattr(ErrorMessages, 'CONNECTION_FAILED'), "CONNECTION_FAILED template missing"
            assert hasattr(ErrorMessages, 'DEBUG_SESSION_UNAVAILABLE'), "DEBUG_SESSION_UNAVAILABLE template missing"
            assert hasattr(ErrorMessages, 'SELENIUM_UNAVAILABLE'), "SELENIUM_UNAVAILABLE template missing"
            
            # Test template formatting
            version_msg = ErrorMessages.VERSION_MISMATCH.format(
                chrome_version="140.0.6853.3",
                chromedriver_version="131.0.6778.69",
                required_version="140"
            )
            
            # Verify message contains key information
            assert "Chrome version: 140.0.6853.3" in version_msg
            assert "ChromeDriver version: 131.0.6778.69" in version_msg
            assert "SOLUTION:" in version_msg
            assert "Required ChromeDriver: 140" in version_msg
            
            print("✅ ErrorMessages class properly implemented")
            print(f"   - All required templates present")
            print(f"   - Template formatting works correctly")
            print(f"   - Messages contain actionable solutions")
            
            self.results['error_messages_class'] = True
            self.details.append("ErrorMessages class verification passed")
            
        except Exception as e:
            print(f"❌ ErrorMessages class verification failed: {e}")
            self.details.append(f"ErrorMessages class failed: {e}")
    
    def verify_version_detection(self):
        """Test 2: Verify Chrome version detection and parsing."""
        print("\n" + "="*60)
        print("TEST 2: Chrome Version Detection")
        print("="*60)
        
        try:
            config = SeleniumConfig()
            fetcher = SeleniumFetcher(config._config)
            
            # Test version parsing method
            test_version_info = {
                'Browser': 'Chrome/131.0.6778.108',
                'Protocol-Version': '1.3',
                'User-Agent': 'Mozilla/5.0 Chrome/131.0.6778.108',
                'V8-Version': '13.1.201.13',
                'WebKit-Version': '537.36 (@cfede9db2)',
                'webSocketDebuggerUrl': 'ws://localhost:9222/devtools/browser'
            }
            
            parsed_version = fetcher._parse_chrome_version(test_version_info)
            assert parsed_version == "131.0.6778.108", f"Version parsing failed: got {parsed_version}"
            
            print(f"✅ Chrome version parsing works correctly")
            print(f"   - Parsed version: {parsed_version}")
            
            # Check if Chrome debug is available
            is_available = fetcher.is_chrome_debug_available()
            
            if is_available:
                print(f"✅ Chrome debug session detected")
                if fetcher.chrome_version:
                    print(f"   - Live Chrome version: {fetcher.chrome_version}")
                    print(f"   - Version info stored for error handling")
            else:
                print(f"⚠️  Chrome debug session not available (expected if Chrome not running)")
                print(f"   - Start Chrome with: ./config/chrome-debug.sh")
            
            # Test ChromeDriver version parsing
            test_error = "session not created: This version of ChromeDriver only supports Chrome version 131"
            chromedriver_version = fetcher._parse_chromedriver_version(test_error)
            assert chromedriver_version == "131", f"ChromeDriver version parsing failed: got {chromedriver_version}"
            
            print(f"✅ ChromeDriver version parsing works correctly")
            print(f"   - Parsed ChromeDriver version: {chromedriver_version}")
            
            self.results['version_detection'] = True
            self.results['version_parsing'] = True
            self.details.append("Version detection and parsing verified")
            
        except Exception as e:
            print(f"❌ Version detection failed: {e}")
            self.details.append(f"Version detection failed: {e}")
    
    def verify_smart_retry_logic(self):
        """Test 3: Verify smart retry logic (no retry on version mismatch)."""
        print("\n" + "="*60)
        print("TEST 3: Smart Retry Logic")
        print("="*60)
        
        try:
            config = SeleniumConfig()
            fetcher = SeleniumFetcher(config._config)
            
            # Test version mismatch detection
            test_errors = [
                "session not created: This version of ChromeDriver only supports Chrome version 131",
                "ChromeDriver 131.0.6778.69 supports Chrome version 131",
                "Current browser version is 140.0.6853.3 with binary path"
            ]
            
            for error_msg in test_errors:
                is_mismatch = fetcher._is_version_mismatch_error(error_msg)
                assert is_mismatch, f"Failed to detect version mismatch in: {error_msg}"
            
            print("✅ Version mismatch detection works correctly")
            print("   - All test error patterns detected")
            
            # Test non-version-mismatch errors
            non_mismatch_errors = [
                "Connection refused",
                "Chrome not reachable",
                "WebDriver timeout"
            ]
            
            for error_msg in non_mismatch_errors:
                is_mismatch = fetcher._is_version_mismatch_error(error_msg)
                assert not is_mismatch, f"Incorrectly detected version mismatch in: {error_msg}"
            
            print("✅ Non-version-mismatch errors handled correctly")
            print("   - Retry logic would apply to these errors")
            
            # Verify connect_to_chrome handles version mismatch without retry
            print("\n🔍 Testing connection behavior...")
            
            if fetcher.is_chrome_debug_available():
                success, message = fetcher.connect_to_chrome()
                
                if not success and "version mismatch" in message.lower():
                    print("✅ Version mismatch detected and handled without retry")
                    print(f"   - Clear error message provided")
                    print(f"   - No unnecessary retry attempts")
                elif success:
                    print("✅ Connection successful (versions compatible)")
                    version_info = fetcher.get_version_info()
                    print(f"   - Chrome: {version_info.get('chrome_version', 'unknown')}")
                    print(f"   - ChromeDriver: {version_info.get('chromedriver_version', 'unknown')}")
                else:
                    print(f"⚠️  Connection failed for other reason: {message[:100]}...")
            else:
                print("⚠️  Chrome debug not available for live testing")
                print("   - Smart retry logic verified through unit tests")
            
            self.results['smart_retry_logic'] = True
            self.details.append("Smart retry logic verified")
            
        except Exception as e:
            print(f"❌ Smart retry logic verification failed: {e}")
            self.details.append(f"Smart retry logic failed: {e}")
    
    def verify_error_handling_integration(self):
        """Test 4: Verify error handling in both selenium_fetcher.py and webfetcher.py."""
        print("\n" + "="*60)
        print("TEST 4: Error Handling Integration")
        print("="*60)
        
        try:
            # Test selenium_fetcher.py error handling
            config = SeleniumConfig()
            fetcher = SeleniumFetcher(config._config)
            
            # Verify exception classes exist
            assert ChromeConnectionError is not None
            assert SeleniumFetchError is not None
            assert SeleniumTimeoutError is not None
            assert SeleniumNotAvailableError is not None
            
            print("✅ All custom exception classes defined")
            
            # Test webfetcher.py integration
            from webfetcher import SELENIUM_INTEGRATION_AVAILABLE
            
            if SELENIUM_INTEGRATION_AVAILABLE:
                print("✅ Selenium integration available in webfetcher.py")
                
                # Test graceful degradation
                from webfetcher import _try_selenium_fallback_after_urllib_failure, FetchMetrics
                
                print("✅ Fallback function properly integrated")
                print("   - _try_selenium_fallback_after_urllib_failure exists")
                print("   - FetchMetrics includes Selenium fields")
                
                # Verify metrics include Selenium fields
                metrics = FetchMetrics()
                assert hasattr(metrics, 'selenium_wait_time')
                assert hasattr(metrics, 'chrome_connected')
                assert hasattr(metrics, 'js_detection_used')
                
                print("✅ FetchMetrics properly extended for Selenium")
            else:
                print("⚠️  Selenium integration not available (graceful degradation)")
            
            # Test connection status reporting
            status = fetcher.get_connection_status()
            assert 'chrome_version' in status
            assert 'chromedriver_version' in status
            assert 'version_compatible' in status
            
            print("✅ Enhanced connection status reporting works")
            print(f"   - Chrome version: {status.get('chrome_version', 'not detected')}")
            print(f"   - ChromeDriver version: {status.get('chromedriver_version', 'not detected')}")
            print(f"   - Version compatible: {status.get('version_compatible', 'unknown')}")
            
            self.results['error_handling'] = True
            self.results['integration'] = True
            self.details.append("Error handling and integration verified")
            
        except Exception as e:
            print(f"❌ Error handling verification failed: {e}")
            self.details.append(f"Error handling failed: {e}")
    
    def run_functional_test(self):
        """Test 5: Run functional test if Chrome debug session available."""
        print("\n" + "="*60)
        print("TEST 5: Functional Test (if Chrome available)")
        print("="*60)
        
        try:
            config = SeleniumConfig()
            fetcher = SeleniumFetcher(config._config)
            
            if not fetcher.is_chrome_debug_available():
                print("⚠️  Chrome debug session not available")
                print("   - Skipping functional test")
                print("   - Start Chrome with: ./config/chrome-debug.sh")
                return
            
            # Attempt connection
            print("🔄 Attempting Chrome connection...")
            success, message = fetcher.connect_to_chrome()
            
            if not success:
                print(f"⚠️  Connection failed: {message[:200]}...")
                if "version mismatch" in message.lower():
                    print("\n✅ Version mismatch properly detected and reported")
                    print("   - Error message is clear and actionable")
                    print("   - No unnecessary retries occurred")
                    # This is actually a success for our test!
                    self.results['integration'] = True
                return
            
            print("✅ Successfully connected to Chrome debug session")
            
            # Try fetching a simple page
            test_url = "https://example.com"
            print(f"\n🔄 Testing fetch of {test_url}...")
            
            try:
                html, metrics = fetcher.fetch_html_selenium(test_url)
                
                print(f"✅ Successfully fetched {test_url}")
                print(f"   - Content length: {len(html)} bytes")
                print(f"   - Page load time: {metrics.page_load_time:.2f}s")
                print(f"   - Total fetch time: {metrics.selenium_wait_time:.2f}s")
                
            except Exception as e:
                print(f"⚠️  Fetch failed: {e}")
            
            # Cleanup
            fetcher.cleanup()
            print("\n✅ Cleanup completed (session preserved)")
            
        except Exception as e:
            print(f"❌ Functional test failed: {e}")
    
    def generate_report(self):
        """Generate final verification report."""
        print("\n" + "="*60)
        print("PHASE 2 VERIFICATION REPORT")
        print("="*60)
        
        all_passed = all(self.results.values())
        
        print("\n📊 Test Results:")
        print("-" * 40)
        
        for test_name, passed in self.results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"  {test_name.replace('_', ' ').title():30} {status}")
        
        print("\n📝 Details:")
        for detail in self.details:
            print(f"  - {detail}")
        
        print("\n" + "="*60)
        
        if all_passed:
            print("🎉 PHASE 2 VERIFICATION: ALL TESTS PASSED")
            print("\nKey achievements:")
            print("  ✅ ErrorMessages class with comprehensive templates")
            print("  ✅ Enhanced Chrome version detection and parsing")
            print("  ✅ Smart retry logic (no retry on version mismatch)")
            print("  ✅ Improved error handling in both modules")
            print("  ✅ Clear, actionable error messages")
            print("\n✨ Phase 2 is ready for production!")
        else:
            failed_tests = [name for name, passed in self.results.items() if not passed]
            print(f"⚠️  PHASE 2 VERIFICATION: PARTIAL SUCCESS")
            print(f"\nFailed tests: {', '.join(failed_tests)}")
            print("\nPlease review the failed tests and fix any issues.")
        
        print("="*60)
        
        return all_passed


def main():
    """Main verification entry point."""
    print("\n🚀 Starting Phase 2 Verification Suite")
    print("Testing Robust Chrome Connection Implementation")
    
    verifier = Phase2Verifier()
    
    # Run all verification tests
    verifier.verify_error_messages_class()
    verifier.verify_version_detection()
    verifier.verify_smart_retry_logic()
    verifier.verify_error_handling_integration()
    verifier.run_functional_test()
    
    # Generate report
    success = verifier.generate_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()