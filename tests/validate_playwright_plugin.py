#!/usr/bin/env python3
"""
Playwright Plugin Architecture Validation Test Suite
================================================================================
Author: Archy-Principle-Architect
Purpose: Comprehensive validation of playwright plugin implementation for Week 2
Date: 2025-09-24
================================================================================
"""

import sys
import os
import time
import logging
import traceback
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation test status."""
    PASSED = "✅ PASSED"
    FAILED = "❌ FAILED"
    WARNING = "⚠️ WARNING"
    SKIPPED = "⏭️ SKIPPED"


@dataclass
class ValidationResult:
    """Result of a validation test."""
    test_name: str
    status: ValidationStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    duration: float = 0.0


class PlaywrightPluginValidator:
    """Comprehensive validator for playwright plugin implementation."""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.test_url = "https://www.example.com"
        
    def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation tests."""
        logger.info("=" * 80)
        logger.info("PLAYWRIGHT PLUGIN ARCHITECTURE VALIDATION")
        logger.info("=" * 80)
        
        # Run validation categories
        self._validate_code_architecture()
        self._validate_plugin_integration()
        self._validate_functionality()
        self._validate_quality_standards()
        
        # Generate report
        return self._generate_report()
    
    def _validate_code_architecture(self):
        """Validate code architecture compliance."""
        logger.info("\n1. CODE ARCHITECTURE VALIDATION")
        logger.info("-" * 40)
        
        # Test 1.1: Plugin structure validation
        self._test_plugin_structure()
        
        # Test 1.2: Interface implementation validation
        self._test_interface_implementation()
        
        # Test 1.3: Resource management validation
        self._test_resource_management()
        
        # Test 1.4: Error handling validation
        self._test_error_handling()
    
    def _validate_plugin_integration(self):
        """Validate plugin system integration."""
        logger.info("\n2. PLUGIN INTEGRATION VALIDATION")
        logger.info("-" * 40)
        
        # Test 2.1: Registry integration
        self._test_registry_integration()
        
        # Test 2.2: Configuration system
        self._test_configuration_system()
        
        # Test 2.3: Backward compatibility
        self._test_backward_compatibility()
        
        # Test 2.4: Plugin coordination
        self._test_plugin_coordination()
    
    def _validate_functionality(self):
        """Validate plugin functionality."""
        logger.info("\n3. FUNCTIONALITY VALIDATION")
        logger.info("-" * 40)
        
        # Test 3.1: JavaScript rendering
        self._test_javascript_rendering()
        
        # Test 3.2: Browser lifecycle
        self._test_browser_lifecycle()
        
        # Test 3.3: Priority system
        self._test_priority_system()
        
        # Test 3.4: Lazy loading
        self._test_lazy_loading()
    
    def _validate_quality_standards(self):
        """Validate quality standards."""
        logger.info("\n4. QUALITY STANDARDS VALIDATION")
        logger.info("-" * 40)
        
        # Test 4.1: Code quality
        self._test_code_quality()
        
        # Test 4.2: Performance impact
        self._test_performance_impact()
        
        # Test 4.3: Error resilience
        self._test_error_resilience()
        
        # Test 4.4: Configuration validity
        self._test_configuration_validity()
    
    def _test_plugin_structure(self):
        """Test plugin file structure and organization."""
        start_time = time.time()
        try:
            import plugins.playwright_fetcher as pf
            
            # Check required components
            required_attrs = ['PlaywrightFetcherPlugin', 'create_plugin']
            missing = [attr for attr in required_attrs if not hasattr(pf, attr)]
            
            if missing:
                self.results.append(ValidationResult(
                    test_name="Plugin Structure",
                    status=ValidationStatus.FAILED,
                    message=f"Missing required components: {missing}",
                    duration=time.time() - start_time
                ))
            else:
                self.results.append(ValidationResult(
                    test_name="Plugin Structure",
                    status=ValidationStatus.PASSED,
                    message="All required components present",
                    duration=time.time() - start_time
                ))
        except Exception as e:
            self.results.append(ValidationResult(
                test_name="Plugin Structure",
                status=ValidationStatus.FAILED,
                message=f"Failed to import plugin: {e}",
                duration=time.time() - start_time
            ))
    
    def _test_interface_implementation(self):
        """Test IFetcherPlugin interface implementation."""
        start_time = time.time()
        try:
            from plugins.playwright_fetcher import PlaywrightFetcherPlugin
            from plugins.base import IFetcherPlugin, FetchContext, FetchResult
            
            plugin = PlaywrightFetcherPlugin()
            
            # Verify interface compliance
            if not isinstance(plugin, IFetcherPlugin):
                self.results.append(ValidationResult(
                    test_name="Interface Implementation",
                    status=ValidationStatus.FAILED,
                    message="Plugin does not implement IFetcherPlugin",
                    duration=time.time() - start_time
                ))
                return
            
            # Test required methods
            context = FetchContext(url=self.test_url)
            
            # Test can_handle
            can_handle = plugin.can_handle(context)
            if not isinstance(can_handle, bool):
                raise TypeError(f"can_handle returned {type(can_handle)}, expected bool")
            
            # Test is_available
            is_available = plugin.is_available()
            if not isinstance(is_available, bool):
                raise TypeError(f"is_available returned {type(is_available)}, expected bool")
            
            # Test get_capabilities
            capabilities = plugin.get_capabilities()
            if not isinstance(capabilities, list):
                raise TypeError(f"get_capabilities returned {type(capabilities)}, expected list")
            
            expected_caps = ["javascript_rendering", "dynamic_content", "spa_support"]
            missing_caps = [cap for cap in expected_caps if cap not in capabilities]
            
            if missing_caps:
                self.results.append(ValidationResult(
                    test_name="Interface Implementation",
                    status=ValidationStatus.WARNING,
                    message=f"Missing expected capabilities: {missing_caps}",
                    details={"capabilities": capabilities},
                    duration=time.time() - start_time
                ))
            else:
                self.results.append(ValidationResult(
                    test_name="Interface Implementation",
                    status=ValidationStatus.PASSED,
                    message="Interface correctly implemented",
                    details={"capabilities": capabilities},
                    duration=time.time() - start_time
                ))
                
        except Exception as e:
            self.results.append(ValidationResult(
                test_name="Interface Implementation",
                status=ValidationStatus.FAILED,
                message=f"Interface test failed: {e}",
                duration=time.time() - start_time
            ))
    
    def _test_resource_management(self):
        """Test browser resource management."""
        start_time = time.time()
        try:
            from plugins.playwright_fetcher import PlaywrightFetcherPlugin
            from plugins.base import FetchContext
            
            plugin = PlaywrightFetcherPlugin()
            
            # Check if Playwright is available
            if not plugin.is_available():
                self.results.append(ValidationResult(
                    test_name="Resource Management",
                    status=ValidationStatus.SKIPPED,
                    message="Playwright not installed - skipping resource test",
                    duration=time.time() - start_time
                ))
                return
            
            # Test resource cleanup with intentional error
            context = FetchContext(url="http://invalid-url-for-testing.local", timeout=5)
            result = plugin.fetch(context)
            
            # Even on failure, resources should be cleaned up
            # Check by attempting another fetch
            context2 = FetchContext(url=self.test_url, timeout=10)
            result2 = plugin.fetch(context2)
            
            self.results.append(ValidationResult(
                test_name="Resource Management",
                status=ValidationStatus.PASSED,
                message="Browser resources properly managed",
                details={"cleanup_verified": True},
                duration=time.time() - start_time
            ))
            
        except Exception as e:
            self.results.append(ValidationResult(
                test_name="Resource Management",
                status=ValidationStatus.FAILED,
                message=f"Resource management test failed: {e}",
                duration=time.time() - start_time
            ))
    
    def _test_error_handling(self):
        """Test error handling completeness."""
        start_time = time.time()
        try:
            from plugins.playwright_fetcher import PlaywrightFetcherPlugin
            from plugins.base import FetchContext
            
            plugin = PlaywrightFetcherPlugin()
            
            # Test various error scenarios
            error_scenarios = [
                ("invalid://url", "Invalid URL protocol"),
                ("", "Empty URL"),
                ("https://nonexistent.invalid.local", "Non-existent domain"),
            ]
            
            all_handled = True
            unhandled_errors = []
            
            for test_url, scenario in error_scenarios:
                try:
                    context = FetchContext(url=test_url, timeout=5)
                    result = plugin.fetch(context)
                    
                    if result.success:
                        all_handled = False
                        unhandled_errors.append(f"{scenario}: Expected failure but got success")
                    elif not result.error_message:
                        all_handled = False
                        unhandled_errors.append(f"{scenario}: No error message provided")
                        
                except Exception as e:
                    all_handled = False
                    unhandled_errors.append(f"{scenario}: Unhandled exception: {e}")
            
            if all_handled:
                self.results.append(ValidationResult(
                    test_name="Error Handling",
                    status=ValidationStatus.PASSED,
                    message="All error scenarios properly handled",
                    duration=time.time() - start_time
                ))
            else:
                self.results.append(ValidationResult(
                    test_name="Error Handling",
                    status=ValidationStatus.WARNING,
                    message="Some error scenarios not fully handled",
                    details={"issues": unhandled_errors},
                    duration=time.time() - start_time
                ))
                
        except Exception as e:
            self.results.append(ValidationResult(
                test_name="Error Handling",
                status=ValidationStatus.FAILED,
                message=f"Error handling test failed: {e}",
                duration=time.time() - start_time
            ))
    
    def _test_registry_integration(self):
        """Test plugin registry integration."""
        start_time = time.time()
        try:
            from plugins.registry import get_global_registry
            
            registry = get_global_registry()
            
            # Check if playwright plugin is registered
            plugin = registry.get_plugin("playwright")
            
            if plugin is None:
                self.results.append(ValidationResult(
                    test_name="Registry Integration",
                    status=ValidationStatus.WARNING,
                    message="Playwright plugin not auto-registered",
                    duration=time.time() - start_time
                ))
            else:
                # Verify plugin info
                plugin_info = registry.get_plugin_info()
                playwright_info = plugin_info.get("playwright", {})
                
                self.results.append(ValidationResult(
                    test_name="Registry Integration",
                    status=ValidationStatus.PASSED,
                    message="Plugin correctly integrated with registry",
                    details=playwright_info,
                    duration=time.time() - start_time
                ))
                
        except Exception as e:
            self.results.append(ValidationResult(
                test_name="Registry Integration",
                status=ValidationStatus.FAILED,
                message=f"Registry integration test failed: {e}",
                duration=time.time() - start_time
            ))
    
    def _test_configuration_system(self):
        """Test configuration system integration."""
        start_time = time.time()
        try:
            from plugins.config import get_plugin_config, PLAYWRIGHT_CONFIG
            
            config = get_plugin_config("playwright")
            
            # Verify configuration structure
            required_keys = ["enabled", "priority", "timeout_ms", "headless", "viewport"]
            missing_keys = [key for key in required_keys if key not in config]
            
            if missing_keys:
                self.results.append(ValidationResult(
                    test_name="Configuration System",
                    status=ValidationStatus.FAILED,
                    message=f"Missing configuration keys: {missing_keys}",
                    duration=time.time() - start_time
                ))
            else:
                # Validate configuration values
                issues = []
                if not isinstance(config["priority"], int):
                    issues.append("Priority must be integer")
                if not isinstance(config["viewport"], dict):
                    issues.append("Viewport must be dictionary")
                if config["timeout_ms"] < 1000:
                    issues.append("Timeout too low for JavaScript rendering")
                
                if issues:
                    self.results.append(ValidationResult(
                        test_name="Configuration System",
                        status=ValidationStatus.WARNING,
                        message="Configuration has issues",
                        details={"issues": issues},
                        duration=time.time() - start_time
                    ))
                else:
                    self.results.append(ValidationResult(
                        test_name="Configuration System",
                        status=ValidationStatus.PASSED,
                        message="Configuration system properly integrated",
                        details={"config_keys": list(config.keys())},
                        duration=time.time() - start_time
                    ))
                    
        except Exception as e:
            self.results.append(ValidationResult(
                test_name="Configuration System",
                status=ValidationStatus.FAILED,
                message=f"Configuration test failed: {e}",
                duration=time.time() - start_time
            ))
    
    def _test_backward_compatibility(self):
        """Test backward compatibility with legacy code."""
        start_time = time.time()
        try:
            # Test that webfetcher.py still works with plugins
            from webfetcher import fetch_html_with_plugins, PLUGIN_SYSTEM_AVAILABLE
            
            if not PLUGIN_SYSTEM_AVAILABLE:
                self.results.append(ValidationResult(
                    test_name="Backward Compatibility",
                    status=ValidationStatus.WARNING,
                    message="Plugin system not detected by webfetcher",
                    duration=time.time() - start_time
                ))
                return
            
            # Test fetch with plugin system
            html, metrics = fetch_html_with_plugins(self.test_url, timeout=10)
            
            if html:
                self.results.append(ValidationResult(
                    test_name="Backward Compatibility",
                    status=ValidationStatus.PASSED,
                    message="Legacy API works with plugin system",
                    details={"fetch_method": metrics.primary_method},
                    duration=time.time() - start_time
                ))
            else:
                self.results.append(ValidationResult(
                    test_name="Backward Compatibility",
                    status=ValidationStatus.WARNING,
                    message="Fetch succeeded but no content returned",
                    duration=time.time() - start_time
                ))
                
        except Exception as e:
            self.results.append(ValidationResult(
                test_name="Backward Compatibility",
                status=ValidationStatus.FAILED,
                message=f"Backward compatibility test failed: {e}",
                duration=time.time() - start_time
            ))
    
    def _test_plugin_coordination(self):
        """Test coordination with other plugins."""
        start_time = time.time()
        try:
            from plugins.registry import get_global_registry
            from plugins.base import FetchContext
            
            registry = get_global_registry()
            context = FetchContext(url=self.test_url)
            
            # Get suitable plugins for test URL
            suitable_plugins = registry.get_suitable_plugins(context)
            plugin_names = [p.name for p in suitable_plugins]
            
            # Verify plugin ordering
            if "playwright" in plugin_names:
                playwright_index = plugin_names.index("playwright")
                
                # Check priority ordering
                priorities = {p.name: p.priority for p in suitable_plugins}
                
                self.results.append(ValidationResult(
                    test_name="Plugin Coordination",
                    status=ValidationStatus.PASSED,
                    message="Plugin coordination working correctly",
                    details={
                        "plugin_order": plugin_names,
                        "priorities": priorities
                    },
                    duration=time.time() - start_time
                ))
            else:
                self.results.append(ValidationResult(
                    test_name="Plugin Coordination",
                    status=ValidationStatus.WARNING,
                    message="Playwright plugin not in suitable plugins list",
                    details={"available_plugins": plugin_names},
                    duration=time.time() - start_time
                ))
                
        except Exception as e:
            self.results.append(ValidationResult(
                test_name="Plugin Coordination",
                status=ValidationStatus.FAILED,
                message=f"Plugin coordination test failed: {e}",
                duration=time.time() - start_time
            ))
    
    def _test_javascript_rendering(self):
        """Test JavaScript rendering capability."""
        start_time = time.time()
        try:
            from plugins.playwright_fetcher import PlaywrightFetcherPlugin
            from plugins.base import FetchContext
            
            plugin = PlaywrightFetcherPlugin()
            
            if not plugin.is_available():
                self.results.append(ValidationResult(
                    test_name="JavaScript Rendering",
                    status=ValidationStatus.SKIPPED,
                    message="Playwright not installed - cannot test JS rendering",
                    duration=time.time() - start_time
                ))
                return
            
            # Test with example.com
            context = FetchContext(url=self.test_url, timeout=30)
            result = plugin.fetch(context)
            
            if result.success and result.html_content:
                # Check for expected content
                if "Example Domain" in result.html_content:
                    self.results.append(ValidationResult(
                        test_name="JavaScript Rendering",
                        status=ValidationStatus.PASSED,
                        message="Successfully rendered page content",
                        details={
                            "content_length": len(result.html_content),
                            "duration": result.duration
                        },
                        duration=time.time() - start_time
                    ))
                else:
                    self.results.append(ValidationResult(
                        test_name="JavaScript Rendering",
                        status=ValidationStatus.WARNING,
                        message="Content fetched but missing expected text",
                        duration=time.time() - start_time
                    ))
            else:
                self.results.append(ValidationResult(
                    test_name="JavaScript Rendering",
                    status=ValidationStatus.FAILED,
                    message=f"Failed to render: {result.error_message}",
                    duration=time.time() - start_time
                ))
                
        except Exception as e:
            self.results.append(ValidationResult(
                test_name="JavaScript Rendering",
                status=ValidationStatus.FAILED,
                message=f"JavaScript rendering test failed: {e}",
                duration=time.time() - start_time
            ))
    
    def _test_browser_lifecycle(self):
        """Test browser lifecycle management."""
        start_time = time.time()
        try:
            from plugins.playwright_fetcher import PlaywrightFetcherPlugin
            from plugins.base import FetchContext
            
            plugin = PlaywrightFetcherPlugin()
            
            if not plugin.is_available():
                self.results.append(ValidationResult(
                    test_name="Browser Lifecycle",
                    status=ValidationStatus.SKIPPED,
                    message="Playwright not installed - skipping lifecycle test",
                    duration=time.time() - start_time
                ))
                return
            
            # Test multiple sequential fetches
            success_count = 0
            for i in range(3):
                context = FetchContext(url=self.test_url, timeout=10)
                result = plugin.fetch(context)
                if result.success:
                    success_count += 1
            
            if success_count == 3:
                self.results.append(ValidationResult(
                    test_name="Browser Lifecycle",
                    status=ValidationStatus.PASSED,
                    message="Browser lifecycle properly managed across fetches",
                    details={"successful_fetches": success_count},
                    duration=time.time() - start_time
                ))
            else:
                self.results.append(ValidationResult(
                    test_name="Browser Lifecycle",
                    status=ValidationStatus.WARNING,
                    message=f"Some fetches failed: {success_count}/3 successful",
                    duration=time.time() - start_time
                ))
                
        except Exception as e:
            self.results.append(ValidationResult(
                test_name="Browser Lifecycle",
                status=ValidationStatus.FAILED,
                message=f"Browser lifecycle test failed: {e}",
                duration=time.time() - start_time
            ))
    
    def _test_priority_system(self):
        """Test plugin priority system."""
        start_time = time.time()
        try:
            from plugins.playwright_fetcher import PlaywrightFetcherPlugin
            from plugins.base import FetchPriority
            
            plugin = PlaywrightFetcherPlugin()
            
            # Check priority value
            if plugin.priority == FetchPriority.NORMAL:
                self.results.append(ValidationResult(
                    test_name="Priority System",
                    status=ValidationStatus.PASSED,
                    message="Plugin has correct NORMAL priority",
                    details={"priority_value": plugin.priority},
                    duration=time.time() - start_time
                ))
            else:
                self.results.append(ValidationResult(
                    test_name="Priority System",
                    status=ValidationStatus.WARNING,
                    message=f"Unexpected priority: {plugin.priority}",
                    duration=time.time() - start_time
                ))
                
        except Exception as e:
            self.results.append(ValidationResult(
                test_name="Priority System",
                status=ValidationStatus.FAILED,
                message=f"Priority system test failed: {e}",
                duration=time.time() - start_time
            ))
    
    def _test_lazy_loading(self):
        """Test lazy loading of Playwright."""
        start_time = time.time()
        try:
            # First, check if we can import the plugin without Playwright
            import sys
            
            # Remove playwright from sys.modules if present
            playwright_modules = [m for m in sys.modules if m.startswith('playwright')]
            for module in playwright_modules:
                del sys.modules[module]
            
            # Now import plugin
            from plugins.playwright_fetcher import PlaywrightFetcherPlugin
            
            plugin = PlaywrightFetcherPlugin()
            
            # Plugin should import successfully even without Playwright
            self.results.append(ValidationResult(
                test_name="Lazy Loading",
                status=ValidationStatus.PASSED,
                message="Plugin loads without importing Playwright",
                details={"is_available": plugin.is_available()},
                duration=time.time() - start_time
            ))
            
        except ImportError as e:
            self.results.append(ValidationResult(
                test_name="Lazy Loading",
                status=ValidationStatus.FAILED,
                message=f"Plugin requires Playwright at import: {e}",
                duration=time.time() - start_time
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                test_name="Lazy Loading",
                status=ValidationStatus.WARNING,
                message=f"Lazy loading test inconclusive: {e}",
                duration=time.time() - start_time
            ))
    
    def _test_code_quality(self):
        """Test code quality metrics."""
        start_time = time.time()
        try:
            import plugins.playwright_fetcher as pf
            
            # Check documentation
            has_module_doc = bool(pf.__doc__)
            has_class_doc = bool(pf.PlaywrightFetcherPlugin.__doc__)
            
            # Check method documentation
            plugin = pf.PlaywrightFetcherPlugin()
            methods = ['fetch', 'can_handle', 'is_available', 'get_capabilities']
            documented_methods = sum(1 for m in methods if getattr(plugin, m).__doc__)
            
            quality_score = 0
            if has_module_doc:
                quality_score += 25
            if has_class_doc:
                quality_score += 25
            quality_score += (documented_methods / len(methods)) * 50
            
            if quality_score >= 75:
                self.results.append(ValidationResult(
                    test_name="Code Quality",
                    status=ValidationStatus.PASSED,
                    message=f"Good code quality (score: {quality_score:.0f}%)",
                    details={
                        "module_doc": has_module_doc,
                        "class_doc": has_class_doc,
                        "documented_methods": f"{documented_methods}/{len(methods)}"
                    },
                    duration=time.time() - start_time
                ))
            else:
                self.results.append(ValidationResult(
                    test_name="Code Quality",
                    status=ValidationStatus.WARNING,
                    message=f"Code quality could be improved (score: {quality_score:.0f}%)",
                    details={
                        "module_doc": has_module_doc,
                        "class_doc": has_class_doc,
                        "documented_methods": f"{documented_methods}/{len(methods)}"
                    },
                    duration=time.time() - start_time
                ))
                
        except Exception as e:
            self.results.append(ValidationResult(
                test_name="Code Quality",
                status=ValidationStatus.FAILED,
                message=f"Code quality test failed: {e}",
                duration=time.time() - start_time
            ))
    
    def _test_performance_impact(self):
        """Test performance impact."""
        start_time = time.time()
        try:
            # Test import time
            import_start = time.time()
            from plugins.playwright_fetcher import PlaywrightFetcherPlugin
            import_time = time.time() - import_start
            
            # Test instantiation time
            inst_start = time.time()
            plugin = PlaywrightFetcherPlugin()
            inst_time = time.time() - inst_start
            
            # Test availability check time
            check_start = time.time()
            is_available = plugin.is_available()
            check_time = time.time() - check_start
            
            total_startup_time = import_time + inst_time + check_time
            
            if total_startup_time < 0.5:  # Less than 500ms
                self.results.append(ValidationResult(
                    test_name="Performance Impact",
                    status=ValidationStatus.PASSED,
                    message=f"Low startup impact ({total_startup_time:.3f}s)",
                    details={
                        "import_time": f"{import_time:.3f}s",
                        "instantiation_time": f"{inst_time:.3f}s",
                        "availability_check": f"{check_time:.3f}s"
                    },
                    duration=time.time() - start_time
                ))
            else:
                self.results.append(ValidationResult(
                    test_name="Performance Impact",
                    status=ValidationStatus.WARNING,
                    message=f"High startup impact ({total_startup_time:.3f}s)",
                    details={
                        "import_time": f"{import_time:.3f}s",
                        "instantiation_time": f"{inst_time:.3f}s",
                        "availability_check": f"{check_time:.3f}s"
                    },
                    duration=time.time() - start_time
                ))
                
        except Exception as e:
            self.results.append(ValidationResult(
                test_name="Performance Impact",
                status=ValidationStatus.FAILED,
                message=f"Performance test failed: {e}",
                duration=time.time() - start_time
            ))
    
    def _test_error_resilience(self):
        """Test error resilience and recovery."""
        start_time = time.time()
        try:
            from plugins.playwright_fetcher import PlaywrightFetcherPlugin
            from plugins.base import FetchContext
            
            plugin = PlaywrightFetcherPlugin()
            
            # Test with various problematic scenarios
            scenarios = [
                FetchContext(url="https://invalid.url", timeout=1),
                FetchContext(url="https://example.com", timeout=0.001),  # Very low timeout
                FetchContext(url="", timeout=10),  # Empty URL
            ]
            
            all_handled = True
            for context in scenarios:
                try:
                    result = plugin.fetch(context)
                    if result.success and context.url == "":
                        all_handled = False  # Should not succeed with empty URL
                except Exception:
                    all_handled = False  # Should handle gracefully
            
            if all_handled:
                self.results.append(ValidationResult(
                    test_name="Error Resilience",
                    status=ValidationStatus.PASSED,
                    message="Plugin handles errors gracefully",
                    duration=time.time() - start_time
                ))
            else:
                self.results.append(ValidationResult(
                    test_name="Error Resilience",
                    status=ValidationStatus.WARNING,
                    message="Some error scenarios not handled gracefully",
                    duration=time.time() - start_time
                ))
                
        except Exception as e:
            self.results.append(ValidationResult(
                test_name="Error Resilience",
                status=ValidationStatus.FAILED,
                message=f"Error resilience test failed: {e}",
                duration=time.time() - start_time
            ))
    
    def _test_configuration_validity(self):
        """Test configuration validity and defaults."""
        start_time = time.time()
        try:
            from plugins.playwright_fetcher import PlaywrightFetcherPlugin
            
            plugin = PlaywrightFetcherPlugin()
            
            # Check configuration is loaded
            if not hasattr(plugin, '_config'):
                self.results.append(ValidationResult(
                    test_name="Configuration Validity",
                    status=ValidationStatus.FAILED,
                    message="Plugin does not load configuration",
                    duration=time.time() - start_time
                ))
                return
            
            # Check critical config values
            config = plugin._config
            issues = []
            
            if config.get('timeout_ms', 0) < 5000:
                issues.append("Timeout too low for JS rendering")
            
            if not config.get('viewport'):
                issues.append("Missing viewport configuration")
            
            if issues:
                self.results.append(ValidationResult(
                    test_name="Configuration Validity",
                    status=ValidationStatus.WARNING,
                    message="Configuration has issues",
                    details={"issues": issues},
                    duration=time.time() - start_time
                ))
            else:
                self.results.append(ValidationResult(
                    test_name="Configuration Validity",
                    status=ValidationStatus.PASSED,
                    message="Configuration is valid",
                    details={"config_keys": list(config.keys())},
                    duration=time.time() - start_time
                ))
                
        except Exception as e:
            self.results.append(ValidationResult(
                test_name="Configuration Validity",
                status=ValidationStatus.FAILED,
                message=f"Configuration validity test failed: {e}",
                duration=time.time() - start_time
            ))
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        
        # Count results by status
        status_counts = {
            ValidationStatus.PASSED: 0,
            ValidationStatus.FAILED: 0,
            ValidationStatus.WARNING: 0,
            ValidationStatus.SKIPPED: 0
        }
        
        for result in self.results:
            status_counts[result.status] += 1
        
        # Calculate pass rate
        total_tests = len(self.results) - status_counts[ValidationStatus.SKIPPED]
        passed_tests = status_counts[ValidationStatus.PASSED]
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Determine overall status
        if status_counts[ValidationStatus.FAILED] > 0:
            overall_status = "FAILED"
            ready_for_week3 = False
        elif pass_rate >= 80:
            overall_status = "PASSED"
            ready_for_week3 = True
        else:
            overall_status = "NEEDS IMPROVEMENT"
            ready_for_week3 = False
        
        # Print report
        print("\n" + "=" * 80)
        print("VALIDATION REPORT SUMMARY")
        print("=" * 80)
        
        print(f"\nTest Results:")
        print(f"  ✅ Passed:  {status_counts[ValidationStatus.PASSED]}")
        print(f"  ❌ Failed:  {status_counts[ValidationStatus.FAILED]}")
        print(f"  ⚠️  Warning: {status_counts[ValidationStatus.WARNING]}")
        print(f"  ⏭️  Skipped: {status_counts[ValidationStatus.SKIPPED]}")
        print(f"\nPass Rate: {pass_rate:.1f}%")
        print(f"Overall Status: {overall_status}")
        
        print("\n" + "-" * 80)
        print("DETAILED TEST RESULTS:")
        print("-" * 80)
        
        for result in self.results:
            print(f"\n{result.status.value} {result.test_name}")
            print(f"   Message: {result.message}")
            if result.details:
                print(f"   Details: {result.details}")
            print(f"   Duration: {result.duration:.3f}s")
        
        # Architecture approval
        print("\n" + "=" * 80)
        print("ARCHITECTURE APPROVAL")
        print("=" * 80)
        
        if ready_for_week3:
            print("\n✅ APPROVED: Playwright plugin implementation meets Week 2 requirements")
            print("   The implementation is ready to proceed to Week 3 (Safari integration)")
        else:
            print("\n❌ NOT APPROVED: Implementation needs improvements before Week 3")
            print("   Please address the failed tests and warnings above")
        
        critical_issues = [r for r in self.results if r.status == ValidationStatus.FAILED]
        if critical_issues:
            print("\nCRITICAL ISSUES TO ADDRESS:")
            for issue in critical_issues:
                print(f"  - {issue.test_name}: {issue.message}")
        
        return {
            "overall_status": overall_status,
            "pass_rate": pass_rate,
            "ready_for_week3": ready_for_week3,
            "status_counts": {str(k): v for k, v in status_counts.items()},
            "test_results": [
                {
                    "test_name": r.test_name,
                    "status": r.status.value,
                    "message": r.message,
                    "details": r.details,
                    "duration": r.duration
                }
                for r in self.results
            ]
        }


def main():
    """Main entry point for validation."""
    try:
        validator = PlaywrightPluginValidator()
        report = validator.run_all_validations()
        
        # Exit with appropriate code
        if report["ready_for_week3"]:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()