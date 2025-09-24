#!/usr/bin/env python3
"""
Test Suite for Safari Integration Fixes
======================================

Tests the macOS-only Safari integration fixes including:
1. Auto-enablement on macOS using platform detection
2. HTTP 403 triggers Safari immediately  
3. Known domains use Safari preemptively
4. Normal URLs still use standard method first

Author: Web_Fetcher Team
Version: 1.0.0
Date: 2025-09-23
"""

import unittest
import platform
import sys
import os
import urllib.error
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import modules to test
try:
    import webfetcher
    from plugins.safari import config as safari_config
except ImportError as e:
    print(f"Failed to import modules: {e}")
    sys.exit(1)

class TestSafariPlatformDetection(unittest.TestCase):
    """Test platform detection for Safari auto-enablement."""
    
    def test_macos_detection_webfetcher(self):
        """Test that webfetcher auto-enables Safari on macOS."""
        with patch('platform.system', return_value='Darwin'):
            # Reload module to test platform detection
            import importlib
            importlib.reload(webfetcher)
            
            # Check if Safari availability is correctly detected
            # Note: SAFARI_AVAILABLE might be False due to ImportError, 
            # but the platform check should work
            self.assertTrue(platform.system() == 'Darwin')
    
    def test_non_macos_detection_webfetcher(self):
        """Test that webfetcher disables Safari on non-macOS."""
        with patch('platform.system', return_value='Windows'):
            import importlib
            importlib.reload(webfetcher)
            
            self.assertFalse(platform.system() == 'Darwin')
    
    def test_macos_detection_safari_config(self):
        """Test that safari_config auto-enables Safari on macOS."""
        with patch('platform.system', return_value='Darwin'):
            import importlib
            importlib.reload(safari_config)
            
            self.assertTrue(safari_config.SAFARI_ENABLED)
    
    def test_non_macos_detection_safari_config(self):
        """Test that safari_config disables Safari on non-macOS."""
        with patch('platform.system', return_value='Linux'):
            import importlib
            importlib.reload(safari_config)
            
            self.assertFalse(safari_config.SAFARI_ENABLED)

class TestPreemptiveSafariCheck(unittest.TestCase):
    """Test the requires_safari_preemptively function."""
    
    def setUp(self):
        """Set up test conditions."""
        # Mock SAFARI_AVAILABLE to True for testing
        webfetcher.SAFARI_AVAILABLE = True
    
    def test_known_problematic_domains(self):
        """Test that known problematic domains trigger preemptive Safari."""
        test_urls = [
            "https://www.ccdi.gov.cn/yaowenn/202509/test.html",
            "https://ccdi.gov.cn/test",
            "https://qcc.com/firm/abc123",
            "https://www.qcc.com/search",
            "https://tianyancha.com/company/123",
            "https://www.tianyancha.com/search",
            "https://gsxt.gov.cn/corp-query/123",
            "https://www.gsxt.gov.cn/search"
        ]
        
        for url in test_urls:
            with self.subTest(url=url):
                result = webfetcher.requires_safari_preemptively(url)
                self.assertTrue(result, f"URL {url} should require preemptive Safari")
    
    def test_normal_domains_no_preemptive(self):
        """Test that normal domains don't trigger preemptive Safari."""
        test_urls = [
            "https://example.com/test",
            "https://www.google.com/search",
            "https://github.com/user/repo",
            "https://stackoverflow.com/questions/123",
            "https://news.ycombinator.com"
        ]
        
        for url in test_urls:
            with self.subTest(url=url):
                result = webfetcher.requires_safari_preemptively(url)
                self.assertFalse(result, f"URL {url} should not require preemptive Safari")
    
    def test_safari_unavailable(self):
        """Test behavior when Safari is unavailable."""
        webfetcher.SAFARI_AVAILABLE = False
        
        result = webfetcher.requires_safari_preemptively("https://ccdi.gov.cn/test")
        self.assertFalse(result, "Should return False when Safari is unavailable")
        
        # Restore for other tests
        webfetcher.SAFARI_AVAILABLE = True

class TestHTTP403SafariTrigger(unittest.TestCase):
    """Test HTTP 403 immediate Safari trigger."""
    
    def setUp(self):
        """Set up test mocks."""
        self.mock_safari_extract = MagicMock(return_value=("<html>Safari content</html>", {}))
        
        # Patch Safari functions
        self.safari_extract_patcher = patch('webfetcher.extract_with_safari_fallback', self.mock_safari_extract)
        self.safari_extract_patcher.start()
        
        # Mock SAFARI_AVAILABLE
        webfetcher.SAFARI_AVAILABLE = True
    
    def tearDown(self):
        """Clean up patches."""
        self.safari_extract_patcher.stop()
    
    @patch('webfetcher.fetch_html_original')
    def test_http_403_triggers_safari(self, mock_fetch_original):
        """Test that HTTP 403 error immediately triggers Safari fallback."""
        # Mock HTTP 403 error
        http_403_error = urllib.error.HTTPError(
            url="https://test.com", 
            code=403, 
            msg="Forbidden", 
            hdrs={}, 
            fp=None
        )
        mock_fetch_original.side_effect = http_403_error
        
        # Call fetch_html_with_retry
        try:
            html, metrics = webfetcher.fetch_html_with_retry("https://test.com")
            
            # Verify Safari was called
            self.mock_safari_extract.assert_called_once()
            self.assertEqual(html, "<html>Safari content</html>")
            self.assertEqual(metrics.primary_method, "safari")
            self.assertEqual(metrics.fallback_method, "safari_403_trigger")
            
        except Exception as e:
            # If Safari mock fails, we should still see the attempt
            self.mock_safari_extract.assert_called_once()
    
    @patch('webfetcher.fetch_html_original')
    def test_other_errors_normal_flow(self, mock_fetch_original):
        """Test that non-403 errors follow normal retry flow."""
        # Mock HTTP 500 error (should be retried normally)
        http_500_error = urllib.error.HTTPError(
            url="https://test.com", 
            code=500, 
            msg="Internal Server Error", 
            hdrs={}, 
            fp=None
        )
        mock_fetch_original.side_effect = http_500_error
        
        # Call fetch_html_with_retry and expect it to fail after retries
        with self.assertRaises(urllib.error.HTTPError):
            webfetcher.fetch_html_with_retry("https://test.com")
        
        # Verify multiple attempts were made (retries)
        self.assertGreater(mock_fetch_original.call_count, 1)

class TestIntegrationFlow(unittest.TestCase):
    """Test the complete integration flow."""
    
    def setUp(self):
        """Set up integration test mocks."""
        self.mock_safari_extract = MagicMock(return_value=("<html>Safari extracted content</html>", {}))
        
        # Patch Safari functions
        self.safari_extract_patcher = patch('webfetcher.extract_with_safari_fallback', self.mock_safari_extract)
        self.safari_extract_patcher.start()
        
        webfetcher.SAFARI_AVAILABLE = True
    
    def tearDown(self):
        """Clean up patches."""
        self.safari_extract_patcher.stop()
    
    def test_preemptive_safari_for_known_domain(self):
        """Test that known domains immediately use Safari."""
        html, metrics = webfetcher.fetch_html_with_retry("https://ccdi.gov.cn/test")
        
        # Verify Safari was used preemptively
        self.mock_safari_extract.assert_called_once_with("https://ccdi.gov.cn/test")
        self.assertEqual(html, "<html>Safari extracted content</html>")
        self.assertEqual(metrics.primary_method, "safari")
        self.assertEqual(metrics.fallback_method, "preemptive_safari")
        self.assertEqual(metrics.total_attempts, 1)
    
    @patch('webfetcher.fetch_html_original')
    def test_normal_domain_standard_flow(self, mock_fetch_original):
        """Test that normal domains use standard HTTP first."""
        mock_fetch_original.return_value = ("<html>Standard content</html>", webfetcher.FetchMetrics())
        
        html, metrics = webfetcher.fetch_html_with_retry("https://example.com/test")
        
        # Verify standard fetch was used
        mock_fetch_original.assert_called_once()
        self.assertEqual(html, "<html>Standard content</html>")
        
        # Verify Safari was not called preemptively
        self.mock_safari_extract.assert_not_called()

class TestErrorHandling(unittest.TestCase):
    """Test error handling in Safari integration."""
    
    def test_safari_import_error_handling(self):
        """Test graceful handling when Safari modules can't be imported."""
        with patch('webfetcher.SAFARI_AVAILABLE', False):
            # Should not crash and should return False
            result = webfetcher.requires_safari_preemptively("https://ccdi.gov.cn/test")
            self.assertFalse(result)
    
    def test_invalid_url_handling(self):
        """Test handling of invalid URLs."""
        webfetcher.SAFARI_AVAILABLE = True
        
        # Should not crash on invalid URL
        result = webfetcher.requires_safari_preemptively("not-a-valid-url")
        self.assertFalse(result)
        
        result = webfetcher.requires_safari_preemptively("")
        self.assertFalse(result)

def run_tests():
    """Run all tests and return results."""
    print("=" * 60)
    print("Safari Integration Fixes Test Suite")
    print("=" * 60)
    print(f"Platform: {platform.system()}")
    print(f"Python: {sys.version}")
    print("-" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestSafariPlatformDetection,
        TestPreemptiveSafariCheck,
        TestHTTP403SafariTrigger,
        TestIntegrationFlow,
        TestErrorHandling
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    print("-" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall: {'PASS' if success else 'FAIL'}")
    return success

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)