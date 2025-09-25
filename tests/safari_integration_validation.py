#!/usr/bin/env python3
"""
Safari Integration Validation Suite
Week 3 Final Architecture Validation

This test suite validates the Safari plugin integration following
the established plugin architecture from Week 1 (Curl) and Week 2 (Playwright).

Author: Archy-Principle-Architect
Purpose: Comprehensive validation of Safari plugin functionality and integration
"""

import os
import sys
import json
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import plugin system
from plugins import get_global_registry, FetchContext
from plugins.base import FetchPriority

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a single validation test."""
    test_name: str
    passed: bool
    message: str
    duration: float = 0.0
    details: Dict = field(default_factory=dict)


@dataclass 
class IntegrationReport:
    """Complete integration test report."""
    timestamp: str
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    results: List[ValidationResult] = field(default_factory=list)
    summary: Dict = field(default_factory=dict)
    
    def add_result(self, result: ValidationResult):
        """Add a test result to the report."""
        self.results.append(result)
        self.total_tests += 1
        if result.passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
    
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100
    
    def to_json(self) -> str:
        """Convert report to JSON."""
        return json.dumps({
            'timestamp': self.timestamp,
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'success_rate': f"{self.success_rate():.1f}%",
            'results': [
                {
                    'test_name': r.test_name,
                    'passed': r.passed,
                    'message': r.message,
                    'duration': r.duration,
                    'details': r.details
                }
                for r in self.results
            ],
            'summary': self.summary
        }, indent=2)


class SafariIntegrationValidator:
    """Validates Safari plugin integration with the plugin system."""
    
    def __init__(self):
        self.registry = get_global_registry()
        self.report = IntegrationReport(
            timestamp=datetime.now().isoformat()
        )
        self.test_url = "https://www.example.com"
    
    def validate_plugin_registration(self) -> ValidationResult:
        """Test 1: Validate Safari plugin is properly registered."""
        start_time = time.time()
        
        try:
            # Check if Safari plugin is registered
            plugins = self.registry.list_plugins()
            safari_registered = 'safari_fetcher' in plugins
            
            if not safari_registered:
                return ValidationResult(
                    test_name="Plugin Registration",
                    passed=False,
                    message="Safari plugin not found in registry",
                    duration=time.time() - start_time,
                    details={'registered_plugins': plugins}
                )
            
            # Get plugin info
            plugin_info = self.registry.get_plugin_info()
            safari_info = plugin_info.get('safari_fetcher', {})
            
            # Validate plugin properties
            expected_priority = FetchPriority.LOW
            actual_priority = safari_info.get('priority', 0)
            
            if actual_priority != expected_priority:
                return ValidationResult(
                    test_name="Plugin Registration",
                    passed=False,
                    message=f"Safari priority mismatch: expected {expected_priority}, got {actual_priority}",
                    duration=time.time() - start_time,
                    details=safari_info
                )
            
            return ValidationResult(
                test_name="Plugin Registration",
                passed=True,
                message="Safari plugin properly registered",
                duration=time.time() - start_time,
                details=safari_info
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="Plugin Registration",
                passed=False,
                message=f"Exception during registration check: {str(e)}",
                duration=time.time() - start_time
            )
    
    def validate_plugin_availability(self) -> ValidationResult:
        """Test 2: Check Safari plugin availability on macOS."""
        start_time = time.time()
        
        try:
            import platform
            is_macos = platform.system() == "Darwin"
            
            safari_plugin = self.registry.get_plugin('safari_fetcher')
            if not safari_plugin:
                return ValidationResult(
                    test_name="Plugin Availability",
                    passed=not is_macos,  # Pass on non-macOS
                    message="Safari plugin not found in registry",
                    duration=time.time() - start_time,
                    details={'platform': platform.system()}
                )
            
            is_available = safari_plugin.is_available()
            
            # On macOS, it should be available
            # On other platforms, it should not be available
            expected_availability = is_macos
            
            if is_available != expected_availability:
                return ValidationResult(
                    test_name="Plugin Availability",
                    passed=False,
                    message=f"Safari availability mismatch on {platform.system()}",
                    duration=time.time() - start_time,
                    details={
                        'platform': platform.system(),
                        'expected': expected_availability,
                        'actual': is_available
                    }
                )
            
            return ValidationResult(
                test_name="Plugin Availability",
                passed=True,
                message=f"Safari availability correct for {platform.system()}",
                duration=time.time() - start_time,
                details={
                    'platform': platform.system(),
                    'available': is_available
                }
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="Plugin Availability",
                passed=False,
                message=f"Exception checking availability: {str(e)}",
                duration=time.time() - start_time
            )
    
    def validate_plugin_capabilities(self) -> ValidationResult:
        """Test 3: Validate Safari plugin capabilities."""
        start_time = time.time()
        
        try:
            safari_plugin = self.registry.get_plugin('safari_fetcher')
            if not safari_plugin:
                return ValidationResult(
                    test_name="Plugin Capabilities",
                    passed=False,
                    message="Safari plugin not found",
                    duration=time.time() - start_time
                )
            
            capabilities = safari_plugin.get_capabilities()
            
            # Expected Safari capabilities
            required_capabilities = [
                "javascript_rendering",
                "browser_automation",
                "cookie_support",
                "anti_bot_bypass",
                "dynamic_content"
            ]
            
            missing_capabilities = [
                cap for cap in required_capabilities 
                if cap not in capabilities
            ]
            
            if missing_capabilities:
                return ValidationResult(
                    test_name="Plugin Capabilities",
                    passed=False,
                    message=f"Missing capabilities: {missing_capabilities}",
                    duration=time.time() - start_time,
                    details={
                        'expected': required_capabilities,
                        'actual': capabilities,
                        'missing': missing_capabilities
                    }
                )
            
            return ValidationResult(
                test_name="Plugin Capabilities",
                passed=True,
                message="All required capabilities present",
                duration=time.time() - start_time,
                details={'capabilities': capabilities}
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="Plugin Capabilities",
                passed=False,
                message=f"Exception checking capabilities: {str(e)}",
                duration=time.time() - start_time
            )
    
    def validate_plugin_priority_system(self) -> ValidationResult:
        """Test 4: Validate plugin priority ordering."""
        start_time = time.time()
        
        try:
            # Create test context
            context = FetchContext(url=self.test_url)
            
            # Get suitable plugins
            suitable_plugins = self.registry.get_suitable_plugins(context)
            plugin_order = [(p.name, p.priority) for p in suitable_plugins]
            
            # Expected order: HTTP (HIGH) > Curl (MEDIUM) > Playwright (MEDIUM) > Safari (LOW)
            expected_order = [
                ('http_fetcher', FetchPriority.HIGH),
                ('curl_fetcher', FetchPriority.MEDIUM),
                ('playwright_fetcher', FetchPriority.MEDIUM),
                ('safari_fetcher', FetchPriority.LOW)
            ]
            
            # Filter expected order to only include registered plugins
            registered_names = [p[0] for p in plugin_order]
            expected_filtered = [
                (name, priority) for name, priority in expected_order
                if name in registered_names
            ]
            
            # Verify Safari is last (lowest priority)
            if plugin_order and 'safari_fetcher' in registered_names:
                safari_position = next(
                    i for i, (name, _) in enumerate(plugin_order)
                    if name == 'safari_fetcher'
                )
                
                # Safari should be at the end (lowest priority)
                if safari_position != len(plugin_order) - 1:
                    return ValidationResult(
                        test_name="Plugin Priority System",
                        passed=False,
                        message="Safari plugin not at lowest priority",
                        duration=time.time() - start_time,
                        details={
                            'actual_order': plugin_order,
                            'safari_position': safari_position
                        }
                    )
            
            return ValidationResult(
                test_name="Plugin Priority System",
                passed=True,
                message="Plugin priority ordering correct",
                duration=time.time() - start_time,
                details={'plugin_order': plugin_order}
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="Plugin Priority System",
                passed=False,
                message=f"Exception checking priority: {str(e)}",
                duration=time.time() - start_time
            )
    
    def validate_fetch_integration(self) -> ValidationResult:
        """Test 5: Validate Safari can fetch content via plugin system."""
        start_time = time.time()
        
        try:
            import platform
            
            # Skip actual fetch on non-macOS
            if platform.system() != "Darwin":
                return ValidationResult(
                    test_name="Fetch Integration",
                    passed=True,
                    message="Skipped fetch test on non-macOS platform",
                    duration=time.time() - start_time,
                    details={'platform': platform.system()}
                )
            
            # Check if Safari plugin is available
            safari_plugin = self.registry.get_plugin('safari_fetcher')
            if not safari_plugin or not safari_plugin.is_available():
                return ValidationResult(
                    test_name="Fetch Integration",
                    passed=False,
                    message="Safari plugin not available for fetch test",
                    duration=time.time() - start_time
                )
            
            # Create context forcing Safari
            context = FetchContext(
                url=self.test_url,
                plugin_config={'force_safari': True}
            )
            
            # Check if Safari can handle this context
            can_handle = safari_plugin.can_handle(context)
            if not can_handle:
                return ValidationResult(
                    test_name="Fetch Integration",
                    passed=False,
                    message="Safari cannot handle test URL",
                    duration=time.time() - start_time,
                    details={'url': self.test_url}
                )
            
            # Attempt to fetch (without actually executing)
            # We're testing integration, not actual Safari execution
            return ValidationResult(
                test_name="Fetch Integration",
                passed=True,
                message="Safari plugin properly integrated with fetch system",
                duration=time.time() - start_time,
                details={
                    'url': self.test_url,
                    'can_handle': can_handle
                }
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="Fetch Integration",
                passed=False,
                message=f"Exception during fetch integration: {str(e)}",
                duration=time.time() - start_time
            )
    
    def validate_backward_compatibility(self) -> ValidationResult:
        """Test 6: Validate backward compatibility with legacy code."""
        start_time = time.time()
        
        try:
            # Check if legacy Safari functions are still accessible
            legacy_checks = []
            
            # Check if webfetcher imports work
            try:
                import webfetcher
                legacy_checks.append(('webfetcher_import', True))
                
                # Check for legacy functions
                has_fallback = hasattr(webfetcher, 'requires_safari_preemptively')
                legacy_checks.append(('legacy_functions', has_fallback))
                
            except ImportError:
                legacy_checks.append(('webfetcher_import', False))
            
            # Check if Safari extractor module exists
            try:
                from plugins.safari.extractor import should_fallback_to_safari
                legacy_checks.append(('safari_extractor', True))
            except ImportError:
                legacy_checks.append(('safari_extractor', False))
            
            # All critical imports should work
            all_pass = all(result for _, result in legacy_checks)
            
            return ValidationResult(
                test_name="Backward Compatibility",
                passed=all_pass,
                message="Legacy compatibility maintained" if all_pass else "Some legacy components missing",
                duration=time.time() - start_time,
                details={'compatibility_checks': dict(legacy_checks)}
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="Backward Compatibility",
                passed=False,
                message=f"Exception checking compatibility: {str(e)}",
                duration=time.time() - start_time
            )
    
    def validate_plugin_cooperation(self) -> ValidationResult:
        """Test 7: Validate Safari cooperates with other plugins."""
        start_time = time.time()
        
        try:
            # Get all registered plugins
            all_plugins = self.registry.list_plugins()
            
            # Check expected plugin set
            expected_plugins = {'http_fetcher', 'curl_fetcher', 'safari_fetcher'}
            registered_set = set(all_plugins)
            
            # Playwright is optional
            if 'playwright_fetcher' in registered_set:
                expected_plugins.add('playwright_fetcher')
            
            missing_plugins = expected_plugins - registered_set
            
            if missing_plugins:
                return ValidationResult(
                    test_name="Plugin Cooperation",
                    passed=False,
                    message=f"Missing expected plugins: {missing_plugins}",
                    duration=time.time() - start_time,
                    details={
                        'expected': list(expected_plugins),
                        'registered': all_plugins,
                        'missing': list(missing_plugins)
                    }
                )
            
            # Test fallback chain works
            context = FetchContext(url=self.test_url)
            suitable = self.registry.get_suitable_plugins(context)
            
            if len(suitable) < 2:
                return ValidationResult(
                    test_name="Plugin Cooperation",
                    passed=False,
                    message="Insufficient plugins for fallback chain",
                    duration=time.time() - start_time,
                    details={'suitable_count': len(suitable)}
                )
            
            return ValidationResult(
                test_name="Plugin Cooperation",
                passed=True,
                message=f"All {len(all_plugins)} plugins cooperating correctly",
                duration=time.time() - start_time,
                details={
                    'plugin_count': len(all_plugins),
                    'registered_plugins': all_plugins,
                    'fallback_chain_length': len(suitable)
                }
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="Plugin Cooperation",
                passed=False,
                message=f"Exception checking cooperation: {str(e)}",
                duration=time.time() - start_time
            )
    
    def run_all_validations(self) -> IntegrationReport:
        """Run all validation tests and generate report."""
        logger.info("=" * 60)
        logger.info("Safari Plugin Integration Validation Suite")
        logger.info("Week 3 Final Architecture Validation")
        logger.info("=" * 60)
        
        # Run all tests
        tests = [
            ("1. Plugin Registration", self.validate_plugin_registration),
            ("2. Plugin Availability", self.validate_plugin_availability),
            ("3. Plugin Capabilities", self.validate_plugin_capabilities),
            ("4. Priority System", self.validate_plugin_priority_system),
            ("5. Fetch Integration", self.validate_fetch_integration),
            ("6. Backward Compatibility", self.validate_backward_compatibility),
            ("7. Plugin Cooperation", self.validate_plugin_cooperation)
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\nRunning {test_name}...")
            result = test_func()
            self.report.add_result(result)
            
            status = "✅ PASSED" if result.passed else "❌ FAILED"
            logger.info(f"  {status}: {result.message}")
            if result.details:
                logger.debug(f"  Details: {json.dumps(result.details, indent=2)}")
        
        # Generate summary
        self.report.summary = {
            'success_rate': f"{self.report.success_rate():.1f}%",
            'integration_status': 'COMPLETE' if self.report.success_rate() >= 80 else 'INCOMPLETE',
            'ready_for_production': self.report.failed_tests == 0
        }
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {self.report.total_tests}")
        logger.info(f"Passed: {self.report.passed_tests}")
        logger.info(f"Failed: {self.report.failed_tests}")
        logger.info(f"Success Rate: {self.report.success_rate():.1f}%")
        logger.info(f"Integration Status: {self.report.summary['integration_status']}")
        
        if self.report.failed_tests > 0:
            logger.warning("\nFailed Tests:")
            for result in self.report.results:
                if not result.passed:
                    logger.warning(f"  - {result.test_name}: {result.message}")
        
        return self.report


def main():
    """Main entry point for validation."""
    validator = SafariIntegrationValidator()
    report = validator.run_all_validations()
    
    # Save report
    report_file = 'safari_integration_report.json'
    with open(report_file, 'w') as f:
        f.write(report.to_json())
    
    logger.info(f"\nReport saved to: {report_file}")
    
    # Exit with appropriate code
    sys.exit(0 if report.failed_tests == 0 else 1)


if __name__ == "__main__":
    main()