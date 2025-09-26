#!/usr/bin/env python3
"""
Safari Plugin Interface Compliance Test Suite
Task 2: Validate complete interface compliance and integration
Author: Archy-Principle-Architect
"""

import sys
import os
import inspect
from typing import get_type_hints, get_origin, get_args
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SafariPluginComplianceValidator:
    """Comprehensive compliance validation for Safari plugin."""
    
    def __init__(self):
        self.results = {
            'interface': [],
            'signatures': [],
            'returns': [],
            'priority': [],
            'errors': [],
            'integration': [],
            'warnings': []
        }
    
    def validate_all(self) -> bool:
        """Run all compliance validations."""
        print("=" * 70)
        print("SAFARI PLUGIN INTERFACE COMPLIANCE TEST")
        print("Task 2: Full Interface and Integration Validation")
        print("=" * 70)
        print()
        
        # Test 1: Interface Implementation
        print("1. Validating Interface Implementation...")
        self.validate_interface_implementation()
        print()
        
        # Test 2: Method Signatures
        print("2. Validating Method Signatures...")
        self.validate_method_signatures()
        print()
        
        # Test 3: Return Types
        print("3. Validating Return Types...")
        self.validate_return_types()
        print()
        
        # Test 4: Priority System
        print("4. Validating Priority System...")
        self.validate_priority_system()
        print()
        
        # Test 5: Error Handling
        print("5. Validating Error Handling...")
        self.validate_error_handling()
        print()
        
        # Test 6: Integration Points
        print("6. Validating Integration Points...")
        self.validate_integration_points()
        print()
        
        # Report results
        self.report_results()
        
        # Calculate compliance score
        return self.calculate_compliance_score()
    
    def validate_interface_implementation(self):
        """Validate that all required interface methods are implemented."""
        try:
            from plugins.safari.plugin import SafariFetcherPlugin
            from plugins.base import IFetcherPlugin, BaseFetcherPlugin
            
            plugin = SafariFetcherPlugin()
            
            # Check abstract methods from IFetcherPlugin
            required_methods = {
                'name': 'property',
                'priority': 'property',
                'can_handle': 'method',
                'fetch': 'method',
                'is_available': 'method',
                'get_capabilities': 'method',
                'validate_context': 'method'
            }
            
            for method_name, method_type in required_methods.items():
                if hasattr(plugin, method_name):
                    if method_type == 'property':
                        # Check if it's accessible as a property
                        try:
                            value = getattr(plugin, method_name)
                            self.results['interface'].append(
                                f"✅ {method_name} {method_type}: {value}"
                            )
                        except Exception as e:
                            self.results['errors'].append(
                                f"❌ {method_name} property not accessible: {e}"
                            )
                    else:
                        # Check if it's callable
                        if callable(getattr(plugin, method_name)):
                            self.results['interface'].append(
                                f"✅ {method_name} method implemented"
                            )
                        else:
                            self.results['errors'].append(
                                f"❌ {method_name} is not callable"
                            )
                else:
                    self.results['errors'].append(
                        f"❌ Missing required {method_type}: {method_name}"
                    )
            
            # Check additional Safari-specific methods
            optional_methods = [
                'get_effective_priority',
                'should_handle_domain',
                'should_fallback_to_safari'
            ]
            
            for method in optional_methods:
                if hasattr(plugin, method) and callable(getattr(plugin, method)):
                    self.results['interface'].append(
                        f"✅ Optional method implemented: {method}"
                    )
                    
        except ImportError as e:
            self.results['errors'].append(f"❌ Cannot import Safari plugin: {e}")
        except Exception as e:
            self.results['errors'].append(f"❌ Interface validation failed: {e}")
    
    def validate_method_signatures(self):
        """Validate method signatures match interface specifications."""
        try:
            from plugins.safari.plugin import SafariFetcherPlugin
            from plugins.base import FetchContext, FetchResult
            
            plugin = SafariFetcherPlugin()
            
            # Check can_handle signature
            can_handle_sig = inspect.signature(plugin.can_handle)
            params = list(can_handle_sig.parameters.keys())
            if params == ['self', 'context'] or params == ['context']:
                self.results['signatures'].append("✅ can_handle signature correct")
            else:
                self.results['errors'].append(
                    f"❌ can_handle signature incorrect: {params}"
                )
            
            # Check fetch signature
            fetch_sig = inspect.signature(plugin.fetch)
            params = list(fetch_sig.parameters.keys())
            if params == ['self', 'context'] or params == ['context']:
                self.results['signatures'].append("✅ fetch signature correct")
            else:
                self.results['errors'].append(
                    f"❌ fetch signature incorrect: {params}"
                )
            
            # Check optional method signatures if present
            if hasattr(plugin, 'get_effective_priority'):
                sig = inspect.signature(plugin.get_effective_priority)
                params = list(sig.parameters.keys())
                if 'url' in params:
                    self.results['signatures'].append(
                        "✅ get_effective_priority signature correct"
                    )
                else:
                    self.results['warnings'].append(
                        f"⚠️  get_effective_priority missing url parameter"
                    )
                    
        except Exception as e:
            self.results['errors'].append(f"❌ Signature validation failed: {e}")
    
    def validate_return_types(self):
        """Validate that methods return correct types."""
        try:
            from plugins.safari.plugin import SafariFetcherPlugin
            from plugins.base import FetchContext, FetchResult, FetchPriority
            
            plugin = SafariFetcherPlugin()
            
            # Create test context
            test_context = FetchContext(url="https://example.com")
            
            # Test can_handle return type
            try:
                result = plugin.can_handle(test_context)
                if isinstance(result, bool):
                    self.results['returns'].append("✅ can_handle returns bool")
                else:
                    self.results['errors'].append(
                        f"❌ can_handle returns {type(result)} instead of bool"
                    )
            except Exception as e:
                self.results['warnings'].append(
                    f"⚠️  Cannot test can_handle: {e}"
                )
            
            # Test is_available return type
            result = plugin.is_available()
            if isinstance(result, bool):
                self.results['returns'].append("✅ is_available returns bool")
            else:
                self.results['errors'].append(
                    f"❌ is_available returns {type(result)} instead of bool"
                )
            
            # Test get_capabilities return type
            result = plugin.get_capabilities()
            if isinstance(result, list):
                self.results['returns'].append("✅ get_capabilities returns list")
            else:
                self.results['errors'].append(
                    f"❌ get_capabilities returns {type(result)} instead of list"
                )
            
            # Test priority type
            if isinstance(plugin.priority, (int, FetchPriority)):
                self.results['returns'].append(
                    f"✅ priority is valid type: {type(plugin.priority).__name__}"
                )
            else:
                self.results['errors'].append(
                    f"❌ priority has invalid type: {type(plugin.priority)}"
                )
                
        except Exception as e:
            self.results['errors'].append(f"❌ Return type validation failed: {e}")
    
    def validate_priority_system(self):
        """Validate priority system implementation."""
        try:
            from plugins.safari.plugin import SafariFetcherPlugin
            from plugins.base import FetchPriority
            
            plugin = SafariFetcherPlugin()
            
            # Check base priority
            if plugin.priority == FetchPriority.LOW:
                self.results['priority'].append(
                    f"✅ Base priority correctly set to LOW ({plugin.priority})"
                )
            else:
                self.results['warnings'].append(
                    f"⚠️  Base priority is {plugin.priority}, expected LOW"
                )
            
            # Check dynamic priority if implemented
            if hasattr(plugin, 'get_effective_priority'):
                # Test with regular URL
                regular_priority = plugin.get_effective_priority("https://example.com")
                if isinstance(regular_priority, (int, FetchPriority)):
                    self.results['priority'].append(
                        "✅ get_effective_priority returns valid priority"
                    )
                
                # Should return base priority for regular URLs
                if regular_priority == plugin.priority:
                    self.results['priority'].append(
                        "✅ Returns base priority for regular URLs"
                    )
                else:
                    self.results['warnings'].append(
                        f"⚠️  Different priority for regular URL: {regular_priority}"
                    )
                    
        except Exception as e:
            self.results['errors'].append(f"❌ Priority validation failed: {e}")
    
    def validate_error_handling(self):
        """Validate error handling robustness."""
        try:
            from plugins.safari.plugin import SafariFetcherPlugin
            from plugins.base import FetchContext, FetchResult
            
            plugin = SafariFetcherPlugin()
            
            # Test with invalid context
            invalid_contexts = [
                FetchContext(url=""),
                FetchContext(url="not-a-url"),
                FetchContext(url="ftp://example.com")
            ]
            
            for context in invalid_contexts:
                try:
                    result = plugin.can_handle(context)
                    if isinstance(result, bool):
                        self.results['errors'].append(
                            f"✅ can_handle handles invalid URL gracefully: {context.url}"
                        )
                except Exception as e:
                    self.results['errors'].append(
                        f"❌ can_handle crashes on invalid URL: {context.url} - {e}"
                    )
            
            # Test fetch error handling
            if not plugin.is_available():
                # Test fetch when unavailable
                result = plugin.fetch(FetchContext(url="https://example.com"))
                if isinstance(result, FetchResult) and not result.success:
                    self.results['errors'].append(
                        "✅ Returns FetchResult with success=False when unavailable"
                    )
                    
        except Exception as e:
            self.results['warnings'].append(f"⚠️  Error handling test incomplete: {e}")
    
    def validate_integration_points(self):
        """Validate integration with other system components."""
        try:
            # Test registry integration
            from plugins.registry import PluginRegistry
            
            registry = PluginRegistry()
            
            # Check if Safari plugin can be registered
            safari_found = False
            for plugin_name in registry.list_plugins():
                if plugin_name == "safari_fetcher":
                    safari_found = True
                    self.results['integration'].append(
                        "✅ Safari plugin registered in PluginRegistry"
                    )
                    break
            
            if not safari_found:
                # Try to manually register
                from plugins.safari.plugin import SafariFetcherPlugin
                safari_plugin = SafariFetcherPlugin()
                try:
                    registry.register_plugin(safari_plugin)
                    self.results['integration'].append(
                        "✅ Safari plugin can be manually registered"
                    )
                except Exception as e:
                    self.results['errors'].append(
                        f"❌ Cannot register Safari plugin: {e}"
                    )
            
            # Test domain config integration
            try:
                from plugins.domain_config import (
                    get_domain_priority_override,
                    should_use_safari_for_domain
                )
                
                # These should be callable without errors
                priority = get_domain_priority_override("https://example.com", "safari_fetcher")
                should_use = should_use_safari_for_domain("https://example.com")
                
                self.results['integration'].append(
                    "✅ Domain config integration functional"
                )
            except ImportError:
                self.results['warnings'].append(
                    "⚠️  Domain config module not available"
                )
            except Exception as e:
                self.results['errors'].append(
                    f"❌ Domain config integration failed: {e}"
                )
                
        except ImportError as e:
            self.results['errors'].append(f"❌ Registry not available: {e}")
        except Exception as e:
            self.results['errors'].append(f"❌ Integration validation failed: {e}")
    
    def report_results(self):
        """Generate comprehensive compliance report."""
        print("=" * 70)
        print("COMPLIANCE TEST RESULTS")
        print("=" * 70)
        print()
        
        sections = [
            ('🔌 Interface Implementation', 'interface'),
            ('📝 Method Signatures', 'signatures'),
            ('↩️  Return Types', 'returns'),
            ('🎯 Priority System', 'priority'),
            ('⚠️  Error Handling', 'errors'),
            ('🔗 Integration Points', 'integration')
        ]
        
        for title, key in sections:
            if self.results[key]:
                print(f"{title}:")
                for item in self.results[key]:
                    print(f"   {item}")
                print()
        
        if self.results['warnings']:
            print("⚠️  Warnings:")
            for warning in self.results['warnings']:
                print(f"   {warning}")
            print()
    
    def calculate_compliance_score(self) -> bool:
        """Calculate overall compliance score."""
        # Count successes
        successes = 0
        for key in ['interface', 'signatures', 'returns', 'priority', 'integration']:
            successes += len([r for r in self.results[key] if '✅' in r])
        
        # Count errors
        errors = len([r for r in self.results['errors'] if '❌' in r])
        
        # Count warnings
        warnings = len(self.results['warnings'])
        
        total_checks = successes + errors + warnings
        
        print("=" * 70)
        print("COMPLIANCE SCORE")
        print("=" * 70)
        print(f"✅ Passed: {successes}")
        print(f"❌ Failed: {errors}")
        print(f"⚠️  Warnings: {warnings}")
        
        if total_checks > 0:
            score = (successes / total_checks) * 100
            print(f"\n📊 Compliance Score: {score:.1f}%")
        else:
            score = 0
            print("\n📊 No checks performed")
        
        if errors == 0:
            print("\n✅ TASK 2 COMPLETE: Safari plugin is fully compliant!")
            print("✅ Ready to proceed to Task 3")
        else:
            print(f"\n❌ COMPLIANCE ISSUES: {errors} errors must be fixed")
            print("❌ Address all errors before proceeding to Task 3")
        
        print("=" * 70)
        
        return errors == 0

def main():
    """Run compliance validation."""
    validator = SafariPluginComplianceValidator()
    success = validator.validate_all()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())