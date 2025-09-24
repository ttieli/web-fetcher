#!/usr/bin/env python3
"""
Safari Integration Validation Suite
===================================

Comprehensive testing and validation of Safari integration fixes.
Tests all required scenarios and provides detailed performance metrics.

Author: Architecture Team
Version: 1.0.0
Date: 2025-09-23
"""

import os
import sys
import time
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import modules
import webfetcher
from plugins.safari import config as safari_config
from plugins.safari.config import SAFARI_ENABLED, validate_safari_availability

class SafariIntegrationValidator:
    """Validates Safari integration implementation."""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'platform': sys.platform,
            'python_version': sys.version,
            'tests': [],
            'summary': {}
        }
    
    def run_validation(self) -> Dict:
        """Run complete validation suite."""
        logger.info("=" * 60)
        logger.info("Safari Integration Validation Suite")
        logger.info("=" * 60)
        
        # 1. Environment validation
        self.validate_environment()
        
        # 2. Configuration validation
        self.validate_configuration()
        
        # 3. Functional tests
        self.run_functional_tests()
        
        # 4. Performance tests
        self.run_performance_tests()
        
        # 5. Generate summary
        self.generate_summary()
        
        return self.results
    
    def validate_environment(self):
        """Validate environment setup."""
        test_result = {
            'test_name': 'Environment Validation',
            'status': 'PASS',
            'details': {}
        }
        
        try:
            # Check platform
            is_macos = sys.platform == 'darwin'
            test_result['details']['platform'] = {
                'value': sys.platform,
                'is_macos': is_macos,
                'status': 'PASS' if is_macos else 'WARN'
            }
            
            # Check Safari availability
            safari_available, message = validate_safari_availability()
            test_result['details']['safari_availability'] = {
                'available': safari_available,
                'message': message,
                'status': 'PASS' if safari_available else 'FAIL'
            }
            
            # Check environment variables
            env_vars = {
                'WF_ENABLE_SAFARI': os.environ.get('WF_ENABLE_SAFARI'),
                'WF_SAFARI_GOV_ONLY': os.environ.get('WF_SAFARI_GOV_ONLY'),
                'WF_SAFARI_TIMEOUT': os.environ.get('WF_SAFARI_TIMEOUT'),
                'WF_SAFARI_AUTO_DETECT': os.environ.get('WF_SAFARI_AUTO_DETECT')
            }
            test_result['details']['environment_variables'] = env_vars
            
            # Check module imports
            try:
                from plugins.safari.extractor import extract_with_safari_fallback
                test_result['details']['safari_module'] = {
                    'imported': True,
                    'status': 'PASS'
                }
            except ImportError as e:
                test_result['details']['safari_module'] = {
                    'imported': False,
                    'error': str(e),
                    'status': 'FAIL'
                }
                test_result['status'] = 'FAIL'
            
            logger.info(f"Environment validation: {test_result['status']}")
            
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['error'] = str(e)
            logger.error(f"Environment validation error: {e}")
        
        self.results['tests'].append(test_result)
    
    def validate_configuration(self):
        """Validate Safari configuration."""
        test_result = {
            'test_name': 'Configuration Validation',
            'status': 'PASS',
            'details': {}
        }
        
        try:
            # Check auto-enablement
            test_result['details']['safari_enabled'] = {
                'value': SAFARI_ENABLED,
                'expected': sys.platform == 'darwin',
                'status': 'PASS' if SAFARI_ENABLED == (sys.platform == 'darwin') else 'FAIL'
            }
            
            # Check problematic domains
            problematic_domains = ['ccdi.gov.cn', 'qcc.com', 'tianyancha.com', 'gsxt.gov.cn']
            domain_checks = []
            
            for domain in problematic_domains:
                url = f"https://{domain}/test"
                requires_safari = webfetcher.requires_safari_preemptively(url)
                domain_checks.append({
                    'domain': domain,
                    'requires_safari': requires_safari,
                    'status': 'PASS' if requires_safari else 'WARN'
                })
            
            test_result['details']['problematic_domains'] = domain_checks
            
            # Check site configurations
            site_configs = []
            for site, config in safari_config.SAFARI_SITES.items():
                site_configs.append({
                    'site': site,
                    'enabled': config.get('enabled', False),
                    'extractor_class': config.get('extractor_class'),
                    'timeout': config.get('timeout')
                })
            
            test_result['details']['site_configurations'] = site_configs
            
            logger.info(f"Configuration validation: {test_result['status']}")
            
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['error'] = str(e)
            logger.error(f"Configuration validation error: {e}")
        
        self.results['tests'].append(test_result)
    
    def run_functional_tests(self):
        """Run functional tests on actual URLs."""
        test_scenarios = [
            {
                'name': 'CCDI Website (Preemptive Safari)',
                'url': 'https://www.ccdi.gov.cn/yaowenn/202509/t20250918_448431.html',
                'expected_method': 'safari',
                'expected_fallback': 'preemptive_safari'
            },
            {
                'name': 'QCC Website (Preemptive Safari)',
                'url': 'https://news.qcc.com/postnews/7588330b53d07872c37bd92842647deb.html',
                'expected_method': 'safari',
                'expected_fallback': 'preemptive_safari'
            },
            {
                'name': 'Normal Website (Standard Method)',
                'url': 'https://example.com',
                'expected_method': 'urllib',
                'expected_fallback': None
            }
        ]
        
        for scenario in test_scenarios:
            test_result = {
                'test_name': f"Functional: {scenario['name']}",
                'status': 'PASS',
                'details': {
                    'url': scenario['url'],
                    'expected_method': scenario['expected_method'],
                    'expected_fallback': scenario['expected_fallback']
                }
            }
            
            try:
                start_time = time.time()
                html, metrics = webfetcher.fetch_html_with_retry(scenario['url'])
                duration = time.time() - start_time
                
                test_result['details']['actual_method'] = metrics.primary_method
                test_result['details']['actual_fallback'] = metrics.fallback_method
                test_result['details']['duration'] = f"{duration:.2f}s"
                test_result['details']['success'] = metrics.final_status == 'success'
                
                # Validate expectations
                if metrics.primary_method != scenario['expected_method']:
                    test_result['status'] = 'FAIL'
                    test_result['details']['mismatch'] = 'method'
                
                if metrics.fallback_method != scenario['expected_fallback']:
                    if not (scenario['expected_fallback'] is None and metrics.fallback_method == 'None'):
                        test_result['status'] = 'FAIL'
                        test_result['details']['mismatch'] = 'fallback'
                
                logger.info(f"{scenario['name']}: {test_result['status']} "
                           f"(Method: {metrics.primary_method}, Duration: {duration:.2f}s)")
                
            except Exception as e:
                test_result['status'] = 'ERROR'
                test_result['error'] = str(e)
                logger.error(f"{scenario['name']} error: {e}")
            
            self.results['tests'].append(test_result)
    
    def run_performance_tests(self):
        """Run performance tests."""
        test_result = {
            'test_name': 'Performance Metrics',
            'status': 'PASS',
            'details': {
                'scenarios': []
            }
        }
        
        try:
            # Test preemptive Safari performance
            ccdi_url = 'https://www.ccdi.gov.cn/yaowenn/202509/t20250918_448431.html'
            
            logger.info("Testing preemptive Safari performance...")
            start = time.time()
            _, metrics = webfetcher.fetch_html_with_retry(ccdi_url)
            preemptive_duration = time.time() - start
            
            test_result['details']['scenarios'].append({
                'scenario': 'Preemptive Safari (CCDI)',
                'duration': f"{preemptive_duration:.2f}s",
                'attempts': metrics.total_attempts,
                'method': metrics.primary_method
            })
            
            # Test standard method performance
            logger.info("Testing standard method performance...")
            start = time.time()
            _, metrics = webfetcher.fetch_html_with_retry('https://example.com')
            standard_duration = time.time() - start
            
            test_result['details']['scenarios'].append({
                'scenario': 'Standard Method (example.com)',
                'duration': f"{standard_duration:.2f}s",
                'attempts': metrics.total_attempts,
                'method': metrics.primary_method
            })
            
            # Performance thresholds
            if preemptive_duration > 120:  # 2 minutes
                test_result['status'] = 'WARN'
                test_result['details']['warning'] = 'Preemptive Safari took over 2 minutes'
            
            if standard_duration > 30:  # 30 seconds
                test_result['status'] = 'WARN'
                test_result['details']['warning'] = 'Standard method took over 30 seconds'
            
            logger.info(f"Performance tests: {test_result['status']}")
            
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['error'] = str(e)
            logger.error(f"Performance test error: {e}")
        
        self.results['tests'].append(test_result)
    
    def generate_summary(self):
        """Generate test summary."""
        total_tests = len(self.results['tests'])
        passed = sum(1 for t in self.results['tests'] if t['status'] == 'PASS')
        failed = sum(1 for t in self.results['tests'] if t['status'] == 'FAIL')
        errors = sum(1 for t in self.results['tests'] if t['status'] == 'ERROR')
        warnings = sum(1 for t in self.results['tests'] if t['status'] == 'WARN')
        
        self.results['summary'] = {
            'total_tests': total_tests,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'warnings': warnings,
            'overall_status': 'PASS' if failed == 0 and errors == 0 else 'FAIL'
        }
        
        logger.info("=" * 60)
        logger.info("Validation Summary")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Errors: {errors}")
        logger.info(f"Warnings: {warnings}")
        logger.info(f"Overall Status: {self.results['summary']['overall_status']}")
    
    def save_results(self, filename: Optional[str] = None):
        """Save results to JSON file."""
        if filename is None:
            filename = f"safari_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = project_root / filename
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Results saved to: {filepath}")
        return filepath

def main():
    """Main execution function."""
    validator = SafariIntegrationValidator()
    results = validator.run_validation()
    
    # Save results
    output_file = validator.save_results()
    
    # Print key findings
    print("\n" + "=" * 60)
    print("Key Findings")
    print("=" * 60)
    
    # Check auto-enablement
    env_test = next((t for t in results['tests'] if t['test_name'] == 'Environment Validation'), None)
    if env_test:
        safari_enabled = env_test['details'].get('safari_availability', {}).get('available', False)
        print(f"✓ Safari auto-enabled on macOS: {safari_enabled}")
    
    # Check preemptive triggers
    func_tests = [t for t in results['tests'] if 'Functional:' in t['test_name']]
    for test in func_tests:
        status_icon = "✓" if test['status'] == 'PASS' else "✗"
        print(f"{status_icon} {test['test_name']}: {test['status']}")
    
    print("\n" + "=" * 60)
    print(f"Full results saved to: {output_file}")
    
    # Return exit code
    return 0 if results['summary']['overall_status'] == 'PASS' else 1

if __name__ == "__main__":
    sys.exit(main())