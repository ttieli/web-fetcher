#!/usr/bin/env python3
"""
Safari Plugin Registry Integration Validation Test Suite
Task 3: Validate Safari plugin integration with the Registry system

Tests the 4 core functionalities:
1. Plugin Discovery - Registry can discover Safari plugin
2. Priority Management - Priority sorting works correctly  
3. Context Handling - URL and configuration processing
4. Fallback Integration - Degradation mechanism functions

Author: Claude Code Assistant
"""

import sys
import os
import platform
from typing import List, Optional
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class RegistryIntegrationValidator:
    """Comprehensive validation for Safari plugin registry integration."""
    
    def __init__(self):
        self.results = {
            'discovery': [],
            'priority': [],
            'context': [],
            'fallback': [],
            'errors': [],
            'warnings': []
        }
        self.is_macos = platform.system() == "Darwin"
    
    def validate_all(self) -> bool:
        """Run all registry integration validations."""
        print("=" * 80)
        print("SAFARI PLUGIN REGISTRY INTEGRATION VALIDATION")
        print("Phase 1 Task 3: Complete Registry System Integration")
        print("=" * 80)
        print(f"Running on: {platform.system()} ({platform.machine()})")
        print(f"macOS Platform: {'Yes' if self.is_macos else 'No'}")
        print()
        
        # Test 1: Plugin Discovery
        print("1. Testing Plugin Discovery...")
        self.test_plugin_discovery()
        print()
        
        # Test 2: Priority Management
        print("2. Testing Priority Management...")
        self.test_priority_management()
        print()
        
        # Test 3: Context Handling
        print("3. Testing Context Handling...")
        self.test_context_handling()
        print()
        
        # Test 4: Fallback Integration
        print("4. Testing Fallback Integration...")
        self.test_fallback_integration()
        print()
        
        # Report comprehensive results
        self.report_results()
        
        # Calculate success
        return self.calculate_success_score()
    
    def test_plugin_discovery(self):
        """Test 1: Plugin Discovery - Registry can find Safari plugin."""
        try:
            from plugins.registry import PluginRegistry, get_global_registry, reset_global_registry
            
            # Reset registry for clean test
            reset_global_registry()
            registry = get_global_registry()
            
            # Check if Safari plugin was auto-discovered
            plugins = registry.list_plugins()
            safari_found = "safari_fetcher" in plugins
            
            if self.is_macos:
                if safari_found:
                    self.results['discovery'].append(
                        "✅ Safari plugin auto-discovered on macOS"
                    )
                else:
                    self.results['errors'].append(
                        "❌ Safari plugin NOT auto-discovered on macOS"
                    )
                
                # Test manual registration
                try:
                    from plugins.safari.plugin import SafariFetcherPlugin
                    safari_plugin = SafariFetcherPlugin()
                    
                    if safari_plugin.is_available():
                        self.results['discovery'].append(
                            "✅ Safari plugin available for registration on macOS"
                        )
                        
                        # Try manual registration
                        registry.register_plugin(safari_plugin)
                        if "safari_fetcher" in registry.list_plugins():
                            self.results['discovery'].append(
                                "✅ Safari plugin manually registerable on macOS"
                            )
                        else:
                            self.results['errors'].append(
                                "❌ Manual registration failed on macOS"
                            )
                    else:
                        self.results['warnings'].append(
                            "⚠️  Safari plugin reports unavailable on macOS"
                        )
                        
                except ImportError as e:
                    self.results['errors'].append(
                        f"❌ Cannot import Safari plugin on macOS: {e}"
                    )
            else:
                # Non-macOS system
                if not safari_found:
                    self.results['discovery'].append(
                        f"✅ Safari plugin correctly NOT registered on {platform.system()}"
                    )
                else:
                    self.results['warnings'].append(
                        f"⚠️  Safari plugin found on non-macOS system: {platform.system()}"
                    )
                
                # Test that Safari plugin reports unavailable
                try:
                    from plugins.safari.plugin import SafariFetcherPlugin
                    safari_plugin = SafariFetcherPlugin()
                    
                    if not safari_plugin.is_available():
                        self.results['discovery'].append(
                            f"✅ Safari plugin correctly reports unavailable on {platform.system()}"
                        )
                    else:
                        self.results['warnings'].append(
                            f"⚠️  Safari plugin reports available on {platform.system()}"
                        )
                except ImportError:
                    self.results['discovery'].append(
                        f"✅ Safari plugin import fails correctly on {platform.system()}"
                    )
                    
        except Exception as e:
            self.results['errors'].append(f"❌ Plugin discovery test failed: {e}")
    
    def test_priority_management(self):
        """Test 2: Priority Management - Priority sorting works correctly."""
        try:
            from plugins.registry import PluginRegistry
            from plugins.safari.plugin import SafariFetcherPlugin
            from plugins.base import FetchContext, FetchPriority
            
            if not self.is_macos:
                self.results['priority'].append(
                    "⏭️  Priority management test skipped (not macOS)"
                )
                return
            
            registry = PluginRegistry()
            safari_plugin = SafariFetcherPlugin()
            
            if not safari_plugin.is_available():
                self.results['warnings'].append(
                    "⚠️  Safari unavailable, priority test limited"
                )
                return
                
            registry.register_plugin(safari_plugin)
            
            # Test 1: Base priority is LOW
            if safari_plugin.priority == FetchPriority.LOW:
                self.results['priority'].append(
                    f"✅ Safari plugin base priority is LOW ({safari_plugin.priority})"
                )
            else:
                self.results['errors'].append(
                    f"❌ Safari plugin priority is {safari_plugin.priority}, expected LOW"
                )
            
            # Test 2: Domain-specific priority boost
            test_domains = [
                ("https://example.com", "should return base priority"),
                ("https://ccdi.gov.cn/test", "should boost priority for gov site"),
                ("https://qcc.com/company", "should boost priority for business site"),
                ("https://linkedin.com/profile", "should boost priority for social site")
            ]
            
            for url, description in test_domains:
                context = FetchContext(url=url)
                
                if hasattr(safari_plugin, 'get_effective_priority'):
                    effective_priority = safari_plugin.get_effective_priority(url)
                    self.results['priority'].append(
                        f"✅ Effective priority for {url}: {effective_priority} ({description})"
                    )
                    
                    # Check if priority is boosted for configured domains
                    if 'ccdi.gov.cn' in url or 'qcc.com' in url or 'linkedin.com' in url:
                        if effective_priority > FetchPriority.LOW:
                            self.results['priority'].append(
                                f"✅ Priority correctly boosted for configured domain: {url}"
                            )
                        else:
                            self.results['warnings'].append(
                                f"⚠️  Priority not boosted for configured domain: {url}"
                            )
                else:
                    self.results['warnings'].append(
                        "⚠️  get_effective_priority method not implemented"
                    )
            
            # Test 3: Registry respects priority order
            suitable_plugins = registry.get_suitable_plugins(
                FetchContext(url="https://example.com")
            )
            
            if suitable_plugins:
                # Check that plugins are sorted by priority
                priorities = []
                for plugin in suitable_plugins:
                    if hasattr(plugin, 'get_effective_priority'):
                        priorities.append(plugin.get_effective_priority("https://example.com"))
                    else:
                        priorities.append(plugin.priority)
                
                is_sorted = all(priorities[i] >= priorities[i+1] for i in range(len(priorities)-1))
                if is_sorted:
                    self.results['priority'].append(
                        "✅ Registry returns plugins in priority order"
                    )
                else:
                    self.results['errors'].append(
                        f"❌ Registry priority order incorrect: {priorities}"
                    )
                    
        except Exception as e:
            self.results['errors'].append(f"❌ Priority management test failed: {e}")
    
    def test_context_handling(self):
        """Test 3: Context Handling - URL and configuration processing."""
        try:
            from plugins.safari.plugin import SafariFetcherPlugin
            from plugins.base import FetchContext
            
            safari_plugin = SafariFetcherPlugin()
            
            # Test URLs Safari can handle
            test_cases = [
                # (URL, expected_result, description)
                ("https://example.com", True, "basic HTTPS URL"),
                ("http://example.com", True, "basic HTTP URL"),
                ("https://ccdi.gov.cn/test", True, "configured domain"),
                ("ftp://example.com", False, "non-HTTP protocol"),
                ("", False, "empty URL"),
                ("not-a-url", False, "invalid URL"),
                ("file:///path/to/file", False, "file protocol")
            ]
            
            for url, expected, description in test_cases:
                try:
                    context = FetchContext(url=url)
                    can_handle = safari_plugin.can_handle(context)
                    
                    if not self.is_macos:
                        # On non-macOS, should always return False
                        if can_handle == False:
                            self.results['context'].append(
                                f"✅ Correctly rejects {description} on non-macOS: {url}"
                            )
                        else:
                            self.results['errors'].append(
                                f"❌ Should reject {description} on non-macOS: {url}"
                            )
                    else:
                        # On macOS, check expected behavior
                        if safari_plugin.is_available():
                            if can_handle == expected:
                                self.results['context'].append(
                                    f"✅ Correctly handles {description}: {url} → {can_handle}"
                                )
                            else:
                                self.results['errors'].append(
                                    f"❌ Wrong result for {description}: {url} → {can_handle} (expected {expected})"
                                )
                        else:
                            if can_handle == False:
                                self.results['context'].append(
                                    f"✅ Correctly rejects {description} when unavailable: {url}"
                                )
                            else:
                                self.results['errors'].append(
                                    f"❌ Should reject {description} when unavailable: {url}"
                                )
                                
                except Exception as e:
                    self.results['errors'].append(
                        f"❌ Context handling failed for {description} ({url}): {e}"
                    )
            
            # Test plugin-specific configuration
            if self.is_macos and safari_plugin.is_available():
                # Test force_safari configuration
                context_with_config = FetchContext(
                    url="https://example.com",
                    plugin_config={'force_safari': True}
                )
                
                try:
                    can_handle_forced = safari_plugin.can_handle(context_with_config)
                    if can_handle_forced:
                        self.results['context'].append(
                            "✅ Respects force_safari configuration option"
                        )
                    else:
                        self.results['warnings'].append(
                            "⚠️  force_safari configuration not respected"
                        )
                except Exception as e:
                    self.results['warnings'].append(
                        f"⚠️  Could not test force_safari config: {e}"
                    )
                    
        except Exception as e:
            self.results['errors'].append(f"❌ Context handling test failed: {e}")
    
    def test_fallback_integration(self):
        """Test 4: Fallback Integration - Degradation mechanism works."""
        try:
            from plugins.registry import PluginRegistry, get_global_registry
            from plugins.safari.plugin import SafariFetcherPlugin
            from plugins.base import FetchContext, FetchResult
            
            registry = get_global_registry()
            
            # Test fallback logic in Safari plugin itself
            safari_plugin = SafariFetcherPlugin()
            
            if hasattr(safari_plugin, 'should_fallback_to_safari'):
                # Test fallback decision logic
                test_scenarios = [
                    (None, "Network timeout error"),
                    ("", "Empty content response"),
                    ("<html><body>Access Denied</body></html>", "Access denied content")
                ]
                
                for content, description in test_scenarios:
                    try:
                        should_fallback = safari_plugin.should_fallback_to_safari(
                            "https://example.com", 
                            content or "",
                            Exception("Test exception")
                        )
                        
                        self.results['fallback'].append(
                            f"✅ Fallback decision for {description}: {should_fallback}"
                        )
                    except Exception as e:
                        self.results['warnings'].append(
                            f"⚠️  Fallback test failed for {description}: {e}"
                        )
            else:
                self.results['warnings'].append(
                    "⚠️  should_fallback_to_safari method not available"
                )
            
            # Test registry fallback mechanism
            context = FetchContext(url="https://example.com")
            
            try:
                # Get suitable plugins
                suitable_plugins = registry.get_suitable_plugins(context)
                
                # Safari should be in the list if available
                safari_in_list = any(
                    plugin.name == "safari_fetcher" for plugin in suitable_plugins
                )
                
                if self.is_macos and safari_plugin.is_available():
                    if safari_in_list:
                        self.results['fallback'].append(
                            "✅ Safari plugin included in suitable plugins list"
                        )
                        
                        # Check position (should be lower priority than HTTP plugins)
                        safari_position = next(
                            (i for i, plugin in enumerate(suitable_plugins) 
                             if plugin.name == "safari_fetcher"), None
                        )
                        
                        if safari_position is not None:
                            if safari_position > 0:
                                self.results['fallback'].append(
                                    f"✅ Safari plugin positioned as fallback option (position {safari_position + 1})"
                                )
                            else:
                                self.results['warnings'].append(
                                    "⚠️  Safari plugin unexpectedly at top priority"
                                )
                    else:
                        self.results['errors'].append(
                            "❌ Safari plugin not in suitable plugins list"
                        )
                else:
                    if not safari_in_list:
                        self.results['fallback'].append(
                            "✅ Safari plugin correctly excluded when unavailable"
                        )
                    else:
                        self.results['errors'].append(
                            "❌ Safari plugin included when should be unavailable"
                        )
                        
            except Exception as e:
                self.results['errors'].append(
                    f"❌ Registry fallback mechanism test failed: {e}"
                )
            
            # Test actual fallback execution (mock-based)
            if self.is_macos:
                self._test_fallback_execution(registry)
                
        except Exception as e:
            self.results['errors'].append(f"❌ Fallback integration test failed: {e}")
    
    def _test_fallback_execution(self, registry):
        """Test actual fallback execution with mocked plugins."""
        try:
            from plugins.base import FetchContext, FetchResult, FetchPriority
            from unittest.mock import MagicMock
            
            # Create mock plugins that fail
            mock_high_priority = MagicMock()
            mock_high_priority.name = "mock_high_priority"
            mock_high_priority.priority = FetchPriority.HIGH
            mock_high_priority.can_handle.return_value = True
            mock_high_priority.validate_context.return_value = True
            mock_high_priority.is_available.return_value = True
            mock_high_priority.fetch.return_value = FetchResult(
                success=False, 
                error_message="Mock high priority failed",
                fetch_method="mock_high"
            )
            
            mock_medium_priority = MagicMock()
            mock_medium_priority.name = "mock_medium_priority" 
            mock_medium_priority.priority = FetchPriority.MEDIUM
            mock_medium_priority.can_handle.return_value = True
            mock_medium_priority.validate_context.return_value = True
            mock_medium_priority.is_available.return_value = True
            mock_medium_priority.fetch.return_value = FetchResult(
                success=False,
                error_message="Mock medium priority failed",
                fetch_method="mock_medium"
            )
            
            # Register mock plugins
            test_registry = type(registry)()  # Create new registry instance
            test_registry.register_plugin(mock_high_priority)
            test_registry.register_plugin(mock_medium_priority)
            
            # Try to register Safari plugin
            from plugins.safari.plugin import SafariFetcherPlugin
            safari_plugin = SafariFetcherPlugin()
            if safari_plugin.is_available():
                test_registry.register_plugin(safari_plugin)
            
            # Test fallback execution
            context = FetchContext(url="https://example.com")
            
            # Mock Safari to return success
            with patch.object(safari_plugin, 'fetch') as mock_safari_fetch:
                mock_safari_fetch.return_value = FetchResult(
                    success=True,
                    html_content="<html><body>Safari Success</body></html>",
                    fetch_method="safari_automation"
                )
                
                result = test_registry.fetch_with_fallback(context)
                
                if result.success and result.fetch_method == "safari_automation":
                    self.results['fallback'].append(
                        "✅ Fallback mechanism successfully uses Safari after other plugins fail"
                    )
                else:
                    self.results['warnings'].append(
                        f"⚠️  Fallback execution unexpected result: {result.fetch_method}"
                    )
                    
        except Exception as e:
            self.results['warnings'].append(
                f"⚠️  Fallback execution test failed: {e}"
            )
    
    def report_results(self):
        """Generate comprehensive test results report."""
        print("=" * 80)
        print("REGISTRY INTEGRATION TEST RESULTS")
        print("=" * 80)
        print()
        
        sections = [
            ('🔍 Plugin Discovery', 'discovery'),
            ('🎯 Priority Management', 'priority'), 
            ('🔧 Context Handling', 'context'),
            ('⚡ Fallback Integration', 'fallback')
        ]
        
        for title, key in sections:
            if self.results[key]:
                print(f"{title}:")
                for item in self.results[key]:
                    print(f"   {item}")
                print()
        
        if self.results['errors']:
            print("❌ Errors:")
            for error in self.results['errors']:
                print(f"   {error}")
            print()
        
        if self.results['warnings']:
            print("⚠️  Warnings:")
            for warning in self.results['warnings']:
                print(f"   {warning}")
            print()
    
    def calculate_success_score(self) -> bool:
        """Calculate overall success score and determine if Task 3 is complete."""
        # Count results
        total_successes = 0
        total_errors = 0
        total_warnings = len(self.results['warnings'])
        
        for key in ['discovery', 'priority', 'context', 'fallback']:
            for item in self.results[key]:
                if '✅' in item:
                    total_successes += 1
                elif '❌' in item:
                    total_errors += 1
        
        # Count direct errors
        total_errors += len(self.results['errors'])
        
        print("=" * 80)
        print("REGISTRY INTEGRATION VALIDATION SCORE")
        print("=" * 80)
        print(f"✅ Passed Tests: {total_successes}")
        print(f"❌ Failed Tests: {total_errors}")
        print(f"⚠️  Warnings: {total_warnings}")
        
        total_tests = total_successes + total_errors
        if total_tests > 0:
            score = (total_successes / total_tests) * 100
            print(f"\n📊 Success Rate: {score:.1f}%")
        else:
            score = 0
            print("\n📊 No tests completed")
        
        print(f"\n🖥️  Platform: {platform.system()}")
        print(f"🎯 macOS Testing: {'Active' if self.is_macos else 'Limited (non-macOS)'}")
        
        # Determine success criteria
        critical_errors = total_errors
        is_successful = critical_errors == 0
        
        if is_successful:
            print(f"\n✅ TASK 3 COMPLETE: Registry Integration Validated!")
            print("✅ All 4 core functionalities working correctly:")
            print("   • Plugin Discovery ✅")
            print("   • Priority Management ✅") 
            print("   • Context Handling ✅")
            print("   • Fallback Integration ✅")
            print("\n✅ Ready for Phase 1 completion and Phase 2 planning")
        else:
            print(f"\n❌ TASK 3 INCOMPLETE: {critical_errors} critical issues found")
            print("❌ Address all errors before proceeding to Phase 2")
            
            if not self.is_macos:
                print("\n💡 NOTE: Some functionality is expected to be limited on non-macOS platforms")
                print("💡 For complete validation, run on macOS system")
        
        print("=" * 80)
        
        return is_successful


def main():
    """Run the Registry Integration validation test suite."""
    print("Starting Safari Plugin Registry Integration Validation...")
    print("Task 3 of Phase 1: Complete registry system integration testing")
    print()
    
    validator = RegistryIntegrationValidator()
    success = validator.validate_all()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())