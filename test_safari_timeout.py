#!/usr/bin/env python3
"""
Safari Timeout Configuration Test for CCDI Website
==================================================

This script tests the optimal Safari timeout configuration for extracting
content from the CCDI website without hanging issues.

Test Configuration:
- Recommended timeout: 15 seconds
- Test URL: https://www.ccdi.gov.cn/yaowenn/202509/t20250918_448431.html
- Additional test: example.com for regression testing
"""

import os
import sys
import time
import logging
import subprocess
from datetime import datetime
from typing import Dict, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SafariTimeoutTester:
    """Test Safari timeout configuration for CCDI website extraction."""
    
    def __init__(self):
        """Initialize the timeout tester."""
        self.test_results = []
        self.original_env = os.environ.copy()
        
    def set_timeout_configuration(self, timeout_seconds: int):
        """
        Set Safari timeout configuration via environment variables.
        
        Args:
            timeout_seconds: Timeout value in seconds
        """
        logger.info(f"Setting Safari timeout configuration to {timeout_seconds} seconds")
        
        # Set environment variables for optimal timeouts
        os.environ['WF_SAFARI_TIMEOUT'] = str(timeout_seconds)
        os.environ['WF_CCDI_TIMEOUT'] = str(timeout_seconds)
        os.environ['WF_SAFARI_ENABLED'] = '1'
        os.environ['WF_CCDI_ENABLED'] = '1'
        os.environ['WF_SAFARI_AUTO_DETECT'] = '1'
        
        # Log the configuration
        logger.info("Environment variables set:")
        logger.info(f"  WF_SAFARI_TIMEOUT: {os.environ.get('WF_SAFARI_TIMEOUT')}")
        logger.info(f"  WF_CCDI_TIMEOUT: {os.environ.get('WF_CCDI_TIMEOUT')}")
        logger.info(f"  WF_SAFARI_ENABLED: {os.environ.get('WF_SAFARI_ENABLED')}")
        logger.info(f"  WF_CCDI_ENABLED: {os.environ.get('WF_CCDI_ENABLED')}")
        
    def test_url_extraction(self, url: str, test_name: str) -> Dict:
        """
        Test extraction of a specific URL.
        
        Args:
            url: URL to test
            test_name: Name of the test
            
        Returns:
            Dict containing test results
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing: {test_name}")
        logger.info(f"URL: {url}")
        logger.info(f"{'='*60}")
        
        start_time = time.time()
        result = {
            'test_name': test_name,
            'url': url,
            'timeout_config': os.environ.get('WF_SAFARI_TIMEOUT', 'not set'),
            'start_time': datetime.now().isoformat(),
            'success': False,
            'extraction_time': None,
            'content_length': 0,
            'error': None,
            'hung': False
        }
        
        try:
            # Use subprocess with timeout to prevent hanging
            logger.info("Starting extraction...")
            
            # Create a test script that will run the extraction
            test_script = f"""
import sys
import os
sys.path.insert(0, '/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher')

# Set environment variables for the subprocess
os.environ['WF_SAFARI_TIMEOUT'] = '{os.environ.get("WF_SAFARI_TIMEOUT", "15")}'
os.environ['WF_CCDI_TIMEOUT'] = '{os.environ.get("WF_CCDI_TIMEOUT", "15")}'
os.environ['WF_SAFARI_ENABLED'] = '1'
os.environ['WF_CCDI_ENABLED'] = '1'

import subprocess
import json

# Use the wf command-line tool for extraction
url = "{url}"
try:
    result = subprocess.run(
        ['python', '/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher/wf.py', url],
        capture_output=True,
        text=True,
        timeout={int(os.environ.get('WF_SAFARI_TIMEOUT', '15')) + 5},
        env=os.environ
    )
    
    if result.returncode == 0:
        content = result.stdout
        output = {{
            'success': True,
            'content_length': len(content),
            'error': None
        }}
    else:
        output = {{
            'success': False,
            'content_length': 0,
            'error': result.stderr[:500] if result.stderr else 'Unknown error'
        }}
except subprocess.TimeoutExpired:
    output = {{
        'success': False,
        'content_length': 0,
        'error': 'Extraction timeout'
    }}
except Exception as e:
    output = {{
        'success': False,
        'content_length': 0,
        'error': str(e)
    }}

print(json.dumps(output))
"""
            
            # Run the extraction with a hard timeout
            process_timeout = int(os.environ.get('WF_SAFARI_TIMEOUT', '60')) + 10  # Add buffer
            logger.info(f"Running extraction with process timeout: {process_timeout}s")
            
            process = subprocess.run(
                [sys.executable, '-c', test_script],
                capture_output=True,
                text=True,
                timeout=process_timeout,
                env=os.environ.copy()
            )
            
            extraction_time = time.time() - start_time
            result['extraction_time'] = round(extraction_time, 2)
            
            if process.returncode == 0:
                # Parse the result
                import json
                try:
                    extraction_result = json.loads(process.stdout)
                    result.update(extraction_result)
                    
                    if result['success']:
                        logger.info(f"✓ Extraction successful in {extraction_time:.2f}s")
                        logger.info(f"  Content length: {result['content_length']} characters")
                    else:
                        logger.warning(f"✗ Extraction failed: {result['error']}")
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse extraction output: {process.stdout}")
                    result['error'] = f"Output parsing error: {process.stdout[:200]}"
            else:
                logger.error(f"Extraction process failed with code {process.returncode}")
                result['error'] = f"Process error: {process.stderr[:500]}"
                
        except subprocess.TimeoutExpired:
            extraction_time = time.time() - start_time
            result['extraction_time'] = round(extraction_time, 2)
            result['hung'] = True
            result['error'] = f"Process timeout after {process_timeout}s - extraction hung"
            logger.error(f"✗ TIMEOUT: Extraction hung after {extraction_time:.2f}s")
            
        except Exception as e:
            extraction_time = time.time() - start_time
            result['extraction_time'] = round(extraction_time, 2)
            result['error'] = str(e)
            logger.error(f"✗ Error during extraction: {e}")
        
        result['end_time'] = datetime.now().isoformat()
        return result
    
    def validate_content_quality(self, content_length: int, test_name: str) -> bool:
        """
        Validate that extracted content meets quality standards.
        
        Args:
            content_length: Length of extracted content
            test_name: Name of the test
            
        Returns:
            bool: True if content quality is acceptable
        """
        if 'CCDI' in test_name:
            # CCDI articles should have substantial content
            min_length = 1000
        else:
            # Other sites can have shorter content
            min_length = 100
            
        is_valid = content_length >= min_length
        
        if is_valid:
            logger.info(f"✓ Content quality validated: {content_length} chars (min: {min_length})")
        else:
            logger.warning(f"✗ Content too short: {content_length} chars (min: {min_length})")
            
        return is_valid
    
    def run_timeout_test(self, timeout_seconds: int):
        """
        Run complete timeout configuration test.
        
        Args:
            timeout_seconds: Timeout to test
        """
        logger.info(f"\n{'#'*70}")
        logger.info(f"# TESTING SAFARI TIMEOUT CONFIGURATION: {timeout_seconds} seconds")
        logger.info(f"{'#'*70}")
        
        # Set the timeout configuration
        self.set_timeout_configuration(timeout_seconds)
        
        # Test URLs
        test_cases = [
            (
                "https://www.ccdi.gov.cn/yaowenn/202509/t20250918_448431.html",
                "CCDI Article Extraction"
            ),
            (
                "https://example.com",
                "Example.com (Regression Test)"
            )
        ]
        
        results = []
        for url, test_name in test_cases:
            result = self.test_url_extraction(url, test_name)
            
            # Validate content quality if extraction succeeded
            if result['success']:
                result['quality_valid'] = self.validate_content_quality(
                    result['content_length'], 
                    test_name
                )
            else:
                result['quality_valid'] = False
            
            results.append(result)
            self.test_results.append(result)
            
            # Add delay between tests
            time.sleep(2)
        
        # Summary
        self.print_test_summary(results, timeout_seconds)
        
    def print_test_summary(self, results: list, timeout_seconds: int):
        """Print test summary."""
        logger.info(f"\n{'='*70}")
        logger.info(f"TIMEOUT TEST SUMMARY - {timeout_seconds}s Configuration")
        logger.info(f"{'='*70}")
        
        for result in results:
            logger.info(f"\n{result['test_name']}:")
            logger.info(f"  Status: {'✓ SUCCESS' if result['success'] else '✗ FAILED'}")
            logger.info(f"  Extraction Time: {result['extraction_time']}s")
            logger.info(f"  Content Length: {result['content_length']} chars")
            logger.info(f"  Quality Valid: {'✓' if result['quality_valid'] else '✗'}")
            logger.info(f"  Hung: {'YES - CRITICAL' if result['hung'] else 'No'}")
            if result['error']:
                logger.info(f"  Error: {result['error'][:100]}")
        
        # Overall assessment
        all_passed = all(r['success'] and not r['hung'] for r in results)
        no_hangs = all(not r['hung'] for r in results)
        
        logger.info(f"\n{'='*70}")
        if all_passed:
            logger.info(f"✓ ALL TESTS PASSED with {timeout_seconds}s timeout")
        elif no_hangs:
            logger.info(f"⚠ Some tests failed but NO HANGING with {timeout_seconds}s timeout")
        else:
            logger.info(f"✗ HANGING DETECTED with {timeout_seconds}s timeout - NOT RECOMMENDED")
        logger.info(f"{'='*70}")
        
    def test_multiple_configurations(self):
        """Test multiple timeout configurations."""
        logger.info("\n" + "="*80)
        logger.info("SAFARI TIMEOUT CONFIGURATION TESTING")
        logger.info("Testing different timeout values to find optimal configuration")
        logger.info("="*80)
        
        # Test different timeout values
        timeout_values = [15, 30, 60]  # Start with recommended 15s
        
        for timeout in timeout_values:
            self.run_timeout_test(timeout)
            # Reset environment for next test
            os.environ.update(self.original_env)
            time.sleep(3)  # Delay between configurations
            
        # Final recommendation
        self.print_final_recommendation()
        
    def print_final_recommendation(self):
        """Print final recommendation based on all tests."""
        logger.info(f"\n{'#'*80}")
        logger.info("# FINAL RECOMMENDATION")
        logger.info(f"{'#'*80}")
        
        # Analyze results
        timeout_performance = {}
        for result in self.test_results:
            timeout = int(result['timeout_config'])
            if timeout not in timeout_performance:
                timeout_performance[timeout] = {
                    'successes': 0,
                    'failures': 0,
                    'hangs': 0,
                    'avg_time': []
                }
            
            if result['hung']:
                timeout_performance[timeout]['hangs'] += 1
            elif result['success']:
                timeout_performance[timeout]['successes'] += 1
                timeout_performance[timeout]['avg_time'].append(result['extraction_time'])
            else:
                timeout_performance[timeout]['failures'] += 1
                
        # Find best configuration
        best_timeout = None
        for timeout, stats in timeout_performance.items():
            logger.info(f"\nTimeout {timeout}s:")
            logger.info(f"  Successes: {stats['successes']}")
            logger.info(f"  Failures: {stats['failures']}")
            logger.info(f"  Hangs: {stats['hangs']}")
            if stats['avg_time']:
                avg_time = sum(stats['avg_time']) / len(stats['avg_time'])
                logger.info(f"  Average extraction time: {avg_time:.2f}s")
            
            # Determine best based on no hangs and most successes
            if stats['hangs'] == 0 and (best_timeout is None or 
                                       stats['successes'] > timeout_performance[best_timeout]['successes']):
                best_timeout = timeout
        
        if best_timeout:
            logger.info(f"\n{'='*80}")
            logger.info(f"RECOMMENDED CONFIGURATION: {best_timeout} seconds")
            logger.info(f"{'='*80}")
            logger.info("\nTo apply this configuration, set these environment variables:")
            logger.info(f"  export WF_SAFARI_TIMEOUT={best_timeout}")
            logger.info(f"  export WF_CCDI_TIMEOUT={best_timeout}")
            logger.info("\nOr add to your shell configuration file (~/.bashrc or ~/.zshrc)")
        else:
            logger.warning("\n⚠ No optimal configuration found - manual investigation needed")

def main():
    """Main test execution."""
    tester = SafariTimeoutTester()
    
    # Test the recommended 15-second configuration first
    logger.info("Starting Safari timeout configuration test...")
    logger.info("This will test extraction with different timeout values.")
    logger.info("Please wait while tests are running...\n")
    
    # Run single configuration test (15 seconds as recommended)
    tester.run_timeout_test(15)
    
    # Optionally test multiple configurations
    # Uncomment the following line to test multiple timeout values:
    # tester.test_multiple_configurations()
    
    logger.info("\nTest completed successfully!")

if __name__ == "__main__":
    main()