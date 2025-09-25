#!/usr/bin/env python3
"""
Safari Plugin Integration Test Suite
Uses https://www.example.com for all tests as specified in requirements.

This test suite validates:
1. Plugin system integration
2. Safari fallback behavior
3. Priority ordering
4. Backward compatibility
5. End-to-end fetch operations
"""

import os
import sys
import time
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
TEST_URL = "https://www.example.com"
EXPECTED_TITLE = "Example Domain"
EXPECTED_CONTENT_MARKERS = [
    "This domain is for use in illustrative examples",
    "More information..."
]


@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    passed: bool
    message: str
    duration: float = 0.0
    details: Dict = None


class SafariExampleComTester:
    """Comprehensive test suite for Safari plugin with example.com."""
    
    def __init__(self):
        self.test_url = TEST_URL
        self.results = []
    
    def test_plugin_system_available(self) -> TestResult:
        """Test 1: Verify plugin system is available."""
        start = time.time()
        
        try:
            from plugins import get_global_registry, FetchContext
            registry = get_global_registry()
            
            plugins = registry.list_plugins()
            
            return TestResult(
                name="Plugin System Available",
                passed=len(plugins) > 0,
                message=f"Found {len(plugins)} plugins: {plugins}",
                duration=time.time() - start,
                details={'plugins': plugins}
            )
        except ImportError as e:
            return TestResult(
                name="Plugin System Available",
                passed=False,
                message=f"Plugin system not available: {e}",
                duration=time.time() - start
            )
    
    def test_safari_plugin_registered(self) -> TestResult:
        """Test 2: Verify Safari plugin is registered."""
        start = time.time()
        
        try:
            from plugins import get_global_registry
            registry = get_global_registry()
            
            safari_plugin = registry.get_plugin('safari_fetcher')
            
            if safari_plugin:
                details = {
                    'name': safari_plugin.name,
                    'priority': safari_plugin.priority,
                    'available': safari_plugin.is_available()
                }
                return TestResult(
                    name="Safari Plugin Registered",
                    passed=True,
                    message="Safari plugin found and registered",
                    duration=time.time() - start,
                    details=details
                )
            else:
                return TestResult(
                    name="Safari Plugin Registered",
                    passed=False,
                    message="Safari plugin not found in registry",
                    duration=time.time() - start
                )
        except Exception as e:
            return TestResult(
                name="Safari Plugin Registered",
                passed=False,
                message=f"Error checking Safari plugin: {e}",
                duration=time.time() - start
            )
    
    def test_plugin_priority_order(self) -> TestResult:
        """Test 3: Verify correct plugin priority ordering."""
        start = time.time()
        
        try:
            from plugins import get_global_registry, FetchContext
            registry = get_global_registry()
            
            context = FetchContext(url=self.test_url)
            suitable = registry.get_suitable_plugins(context)
            
            plugin_order = [(p.name, p.priority) for p in suitable]
            
            # Safari should be lowest priority (at the end)
            if 'safari_fetcher' in [p[0] for p in plugin_order]:
                safari_index = next(
                    i for i, (name, _) in enumerate(plugin_order)
                    if name == 'safari_fetcher'
                )
                is_last = safari_index == len(plugin_order) - 1
                
                return TestResult(
                    name="Plugin Priority Order",
                    passed=is_last,
                    message=f"Safari at position {safari_index+1}/{len(plugin_order)}",
                    duration=time.time() - start,
                    details={'plugin_order': plugin_order}
                )
            else:
                return TestResult(
                    name="Plugin Priority Order",
                    passed=False,
                    message="Safari plugin not in suitable plugins list",
                    duration=time.time() - start,
                    details={'plugin_order': plugin_order}
                )
                
        except Exception as e:
            return TestResult(
                name="Plugin Priority Order",
                passed=False,
                message=f"Error checking priority: {e}",
                duration=time.time() - start
            )
    
    def test_fetch_with_plugin_system(self) -> TestResult:
        """Test 4: Fetch example.com using plugin system."""
        start = time.time()
        
        try:
            from plugins import get_global_registry, FetchContext
            registry = get_global_registry()
            
            context = FetchContext(url=self.test_url)
            result = registry.fetch_with_fallback(context)
            
            if result.success and result.html_content:
                # Check for expected content
                has_title = EXPECTED_TITLE.lower() in result.html_content.lower()
                has_content = any(
                    marker.lower() in result.html_content.lower()
                    for marker in EXPECTED_CONTENT_MARKERS
                )
                
                return TestResult(
                    name="Fetch with Plugin System",
                    passed=has_title and has_content,
                    message=f"Fetched via {result.fetch_method}",
                    duration=time.time() - start,
                    details={
                        'method': result.fetch_method,
                        'has_title': has_title,
                        'has_content': has_content,
                        'content_length': len(result.html_content)
                    }
                )
            else:
                return TestResult(
                    name="Fetch with Plugin System",
                    passed=False,
                    message=f"Fetch failed: {result.error_message}",
                    duration=time.time() - start,
                    details={'error': result.error_message}
                )
                
        except Exception as e:
            return TestResult(
                name="Fetch with Plugin System",
                passed=False,
                message=f"Exception during fetch: {e}",
                duration=time.time() - start
            )
    
    def test_safari_forced_fetch(self) -> TestResult:
        """Test 5: Force fetch with Safari plugin."""
        start = time.time()
        
        try:
            import platform
            
            # Skip on non-macOS
            if platform.system() != "Darwin":
                return TestResult(
                    name="Safari Forced Fetch",
                    passed=True,
                    message="Skipped on non-macOS platform",
                    duration=time.time() - start,
                    details={'platform': platform.system()}
                )
            
            from plugins import get_global_registry, FetchContext
            registry = get_global_registry()
            
            safari = registry.get_plugin('safari_fetcher')
            if not safari or not safari.is_available():
                return TestResult(
                    name="Safari Forced Fetch",
                    passed=False,
                    message="Safari plugin not available",
                    duration=time.time() - start
                )
            
            # Force Safari usage
            context = FetchContext(
                url=self.test_url,
                plugin_config={'force_safari': True}
            )
            
            # Check if Safari can handle
            can_handle = safari.can_handle(context)
            
            return TestResult(
                name="Safari Forced Fetch",
                passed=can_handle,
                message="Safari can handle forced request" if can_handle else "Safari cannot handle",
                duration=time.time() - start,
                details={'can_handle': can_handle}
            )
            
        except Exception as e:
            return TestResult(
                name="Safari Forced Fetch",
                passed=False,
                message=f"Exception: {e}",
                duration=time.time() - start
            )
    
    def test_backward_compatibility(self) -> TestResult:
        """Test 6: Test backward compatibility with webfetcher.py."""
        start = time.time()
        
        try:
            # Test legacy imports
            import webfetcher
            
            # Check for expected functions
            has_fetch = hasattr(webfetcher, 'fetch_html_with_metrics')
            has_fallback = hasattr(webfetcher, 'fetch_with_fallback')
            
            # Try to fetch using legacy method
            if has_fetch:
                try:
                    from webfetcher import FetchMetrics
                    metrics = FetchMetrics()
                    html = webfetcher.fetch_html_with_metrics(self.test_url, metrics)
                    
                    success = html and len(html) > 0
                    
                    return TestResult(
                        name="Backward Compatibility",
                        passed=success,
                        message="Legacy fetch method works",
                        duration=time.time() - start,
                        details={
                            'has_fetch': has_fetch,
                            'has_fallback': has_fallback,
                            'content_length': len(html) if html else 0
                        }
                    )
                except Exception as e:
                    return TestResult(
                        name="Backward Compatibility",
                        passed=False,
                        message=f"Legacy fetch failed: {e}",
                        duration=time.time() - start
                    )
            else:
                return TestResult(
                    name="Backward Compatibility",
                    passed=False,
                    message="Legacy fetch methods not found",
                    duration=time.time() - start,
                    details={'has_fetch': has_fetch}
                )
                
        except ImportError as e:
            return TestResult(
                name="Backward Compatibility",
                passed=False,
                message=f"Cannot import webfetcher: {e}",
                duration=time.time() - start
            )
    
    def test_cli_integration(self) -> TestResult:
        """Test 7: Test CLI integration with example.com."""
        start = time.time()
        
        try:
            import subprocess
            
            # Test webfetcher CLI
            result = subprocess.run(
                ['python', 'webfetcher.py', self.test_url, '--no-output'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            
            # Check output for expected content
            output = result.stdout + result.stderr
            has_fetch_info = 'fetch' in output.lower() or 'retrieved' in output.lower()
            
            return TestResult(
                name="CLI Integration",
                passed=success,
                message="CLI fetch successful" if success else "CLI fetch failed",
                duration=time.time() - start,
                details={
                    'return_code': result.returncode,
                    'has_output': len(output) > 0,
                    'has_fetch_info': has_fetch_info
                }
            )
            
        except subprocess.TimeoutExpired:
            return TestResult(
                name="CLI Integration",
                passed=False,
                message="CLI fetch timed out",
                duration=time.time() - start
            )
        except Exception as e:
            return TestResult(
                name="CLI Integration",
                passed=False,
                message=f"CLI test failed: {e}",
                duration=time.time() - start
            )
    
    def test_plugin_cooperation(self) -> TestResult:
        """Test 8: Test multi-plugin cooperation."""
        start = time.time()
        
        try:
            from plugins import get_global_registry
            registry = get_global_registry()
            
            all_plugins = registry.list_plugins()
            
            # Check minimum required plugins
            required = {'http_fetcher', 'safari_fetcher'}
            present = set(all_plugins)
            missing = required - present
            
            if missing:
                return TestResult(
                    name="Plugin Cooperation",
                    passed=False,
                    message=f"Missing required plugins: {missing}",
                    duration=time.time() - start,
                    details={'required': list(required), 'present': all_plugins}
                )
            
            # Check plugin count (should have at least 2 for fallback)
            has_fallback = len(all_plugins) >= 2
            
            return TestResult(
                name="Plugin Cooperation",
                passed=has_fallback,
                message=f"{len(all_plugins)} plugins available for cooperation",
                duration=time.time() - start,
                details={'plugins': all_plugins, 'count': len(all_plugins)}
            )
            
        except Exception as e:
            return TestResult(
                name="Plugin Cooperation",
                passed=False,
                message=f"Error checking cooperation: {e}",
                duration=time.time() - start
            )
    
    def run_all_tests(self) -> List[TestResult]:
        """Run all tests and return results."""
        tests = [
            ("Plugin System", self.test_plugin_system_available),
            ("Safari Registration", self.test_safari_plugin_registered),
            ("Priority Order", self.test_plugin_priority_order),
            ("Plugin Fetch", self.test_fetch_with_plugin_system),
            ("Safari Forced", self.test_safari_forced_fetch),
            ("Backward Compat", self.test_backward_compatibility),
            ("CLI Integration", self.test_cli_integration),
            ("Plugin Cooperation", self.test_plugin_cooperation)
        ]
        
        print("\n" + "=" * 60)
        print("Safari Integration Test Suite - example.com")
        print("=" * 60)
        
        for name, test_func in tests:
            print(f"\n▶ Running: {name}")
            result = test_func()
            self.results.append(result)
            
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"  {status}: {result.message}")
            if result.details:
                print(f"  Details: {json.dumps(result.details, indent=4)}")
        
        return self.results
    
    def generate_report(self) -> Dict:
        """Generate test report."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        report = {
            'test_url': self.test_url,
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'success_rate': f"{(passed/total*100):.1f}%" if total > 0 else "0%",
            'results': [
                {
                    'name': r.name,
                    'passed': r.passed,
                    'message': r.message,
                    'duration': f"{r.duration:.3f}s",
                    'details': r.details
                }
                for r in self.results
            ]
        }
        
        return report


def main():
    """Main test runner."""
    tester = SafariExampleComTester()
    results = tester.run_all_tests()
    report = tester.generate_report()
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {report['total_tests']}")
    print(f"Passed: {report['passed']}")
    print(f"Failed: {report['failed']}")
    print(f"Success Rate: {report['success_rate']}")
    
    if report['failed'] > 0:
        print("\n⚠️  Failed Tests:")
        for r in results:
            if not r.passed:
                print(f"  - {r.name}: {r.message}")
    
    # Save report
    report_file = 'safari_example_com_test_report.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\n📄 Report saved to: {report_file}")
    
    # Exit code based on results
    sys.exit(0 if report['failed'] == 0 else 1)


if __name__ == "__main__":
    main()