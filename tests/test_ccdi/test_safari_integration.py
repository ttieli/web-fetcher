#!/usr/bin/env python3
"""
Safari Fallback Integration Test Suite
======================================

Comprehensive test suite to validate the Safari fallback integration
with various URL types and failure scenarios.

Author: Archy-Principle-Architect
Date: 2025-09-23
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import json

# Setup paths
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR.parent))

# Configure test environment
os.environ['WF_ENABLE_SAFARI_FALLBACK'] = '1'
os.environ['WF_SAFARI_TIMEOUT'] = '30'
os.environ['WF_MIN_CONTENT_LENGTH'] = '500'

# Import modules
from safari_fallback_wrapper import (
    should_use_safari_fallback,
    install_safari_fallback,
    safari_extraction_fallback
)
import webfetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SafariFallbackTester:
    """Test harness for Safari fallback integration."""
    
    def __init__(self):
        self.results = []
        self.test_urls = [
            {
                'url': 'https://www.ccdi.gov.cn/yaowenn/202509/t20250918_448431.html',
                'type': 'government_captcha',
                'expected_fallback': True,
                'description': 'CCDI article with CAPTCHA protection'
            },
            {
                'url': 'https://example.com',
                'type': 'normal',
                'expected_fallback': False,
                'description': 'Normal site without protection'
            },
            {
                'url': 'https://httpstat.us/403',
                'type': 'http_403',
                'expected_fallback': True,
                'description': 'HTTP 403 Forbidden response'
            },
            {
                'url': 'https://httpstat.us/503',
                'type': 'http_503',
                'expected_fallback': True,
                'description': 'HTTP 503 Service Unavailable'
            }
        ]
    
    def test_trigger_detection(self):
        """Test the trigger detection logic."""
        logger.info("=" * 60)
        logger.info("Testing trigger detection logic")
        logger.info("=" * 60)
        
        test_cases = [
            {
                'name': 'CAPTCHA in content',
                'html': '<div class="seccaptcha">Please verify</div>',
                'url': 'http://example.com',
                'should_trigger': True
            },
            {
                'name': 'Short content',
                'html': 'Short',
                'url': 'http://example.com',
                'should_trigger': True
            },
            {
                'name': 'Normal content',
                'html': 'A' * 1000,
                'url': 'http://example.com',
                'should_trigger': False
            },
            {
                'name': 'Government site',
                'html': 'A' * 100,
                'url': 'http://example.gov.cn',
                'should_trigger': True
            }
        ]
        
        for case in test_cases:
            result = should_use_safari_fallback(
                exception=None,
                url=case['url'],
                html_content=case['html']
            )
            
            status = "✓" if result == case['should_trigger'] else "✗"
            logger.info(f"{status} {case['name']}: "
                       f"Expected={case['should_trigger']}, Got={result}")
            
            self.results.append({
                'test': f"trigger_{case['name']}",
                'passed': result == case['should_trigger']
            })
    
    def test_safari_extraction(self):
        """Test Safari extraction directly."""
        logger.info("=" * 60)
        logger.info("Testing Safari extraction")
        logger.info("=" * 60)
        
        # Test with CCDI URL
        test_url = "https://www.ccdi.gov.cn/yaowenn/202509/t20250918_448431.html"
        
        try:
            logger.info(f"Testing Safari extraction for: {test_url}")
            start_time = time.time()
            
            html, metrics = safari_extraction_fallback(test_url)
            
            duration = time.time() - start_time
            logger.info(f"✓ Safari extraction successful")
            logger.info(f"  Content length: {len(html)} chars")
            logger.info(f"  Duration: {duration:.2f}s")
            logger.info(f"  Metrics: {metrics.to_dict()}")
            
            # Validate content
            has_captcha = 'captcha' in html.lower() or '验证' in html.lower()
            if has_captcha:
                logger.warning("  CAPTCHA indicators still present in content")
            
            self.results.append({
                'test': 'safari_extraction',
                'passed': len(html) > 1000,
                'content_length': len(html),
                'duration': duration
            })
            
        except Exception as e:
            logger.error(f"✗ Safari extraction failed: {e}")
            self.results.append({
                'test': 'safari_extraction',
                'passed': False,
                'error': str(e)
            })
    
    def test_integration(self):
        """Test the full integration with webfetcher."""
        logger.info("=" * 60)
        logger.info("Testing full integration")
        logger.info("=" * 60)
        
        # Install Safari fallback
        install_safari_fallback()
        
        for test_case in self.test_urls:
            logger.info(f"\nTesting: {test_case['description']}")
            logger.info(f"URL: {test_case['url']}")
            
            try:
                start_time = time.time()
                html, metrics = webfetcher.fetch_html(test_case['url'])
                duration = time.time() - start_time
                
                # Check if Safari was used
                safari_used = (
                    metrics.primary_method == 'safari' or
                    metrics.fallback_method == 'safari'
                )
                
                expected = test_case['expected_fallback']
                status = "✓" if safari_used == expected else "✗"
                
                logger.info(f"{status} Result:")
                logger.info(f"  Content length: {len(html)} chars")
                logger.info(f"  Duration: {duration:.2f}s")
                logger.info(f"  Primary method: {metrics.primary_method}")
                logger.info(f"  Fallback method: {metrics.fallback_method}")
                logger.info(f"  Safari expected: {expected}, Used: {safari_used}")
                
                self.results.append({
                    'test': f"integration_{test_case['type']}",
                    'url': test_case['url'],
                    'passed': safari_used == expected,
                    'safari_used': safari_used,
                    'content_length': len(html),
                    'duration': duration,
                    'metrics': metrics.to_dict()
                })
                
            except Exception as e:
                logger.error(f"✗ Test failed: {e}")
                self.results.append({
                    'test': f"integration_{test_case['type']}",
                    'url': test_case['url'],
                    'passed': False,
                    'error': str(e)
                })
    
    def generate_report(self):
        """Generate test report."""
        logger.info("=" * 60)
        logger.info("Test Report")
        logger.info("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.get('passed', False))
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Save detailed report
        report_path = SCRIPT_DIR / 'safari_integration_test_report.json'
        with open(report_path, 'w') as f:
            json.dump({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'summary': {
                    'total': total_tests,
                    'passed': passed_tests,
                    'failed': total_tests - passed_tests
                },
                'results': self.results
            }, f, indent=2)
        
        logger.info(f"\nDetailed report saved to: {report_path}")
        
        return passed_tests == total_tests
    
    def run_all_tests(self):
        """Run all test suites."""
        logger.info("Starting Safari Fallback Integration Tests")
        logger.info("=" * 60)
        
        # Run test suites
        self.test_trigger_detection()
        
        # Only test Safari extraction on macOS
        import platform
        if platform.system() == 'Darwin':
            self.test_safari_extraction()
            self.test_integration()
        else:
            logger.warning("Skipping Safari-specific tests on non-macOS platform")
        
        # Generate report
        all_passed = self.generate_report()
        
        if all_passed:
            logger.info("\n✅ All tests passed!")
        else:
            logger.warning("\n⚠️ Some tests failed. Check the report for details.")
        
        return all_passed


def main():
    """Main test runner."""
    tester = SafariFallbackTester()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())