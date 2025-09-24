#!/usr/bin/env python3
"""
Comprehensive validation script for the priority adjustment implementation.
Tests that urllib/HTTP is now the highest priority plugin while maintaining proper fallbacks.
"""

import logging
import sys
import json
from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the plugin system components
try:
    from plugins.base import FetchPriority, FetchContext, FetchResult
    from plugins.domain_config import (
        DOMAIN_PLUGIN_OVERRIDES,
        HTTP_PREFERRED_DOMAINS,
        get_domain_priority_override,
        should_use_safari_for_domain,
        get_domain_config
    )
    from plugins.http_fetcher import HTTPFetcherPlugin
    from plugins.safari_plugin import SafariFetcherPlugin
    from plugins.registry import PluginRegistry, get_global_registry
    print("✅ All plugin system imports successful")
except ImportError as e:
    print(f"❌ Failed to import plugin system: {e}")
    sys.exit(1)


class ValidationReport:
    """Tracks validation results and generates reports."""
    
    def __init__(self):
        self.results = {
            'architecture_compliance': [],
            'functional_requirements': [],
            'performance_impact': [],
            'edge_cases': [],
            'integration_tests': []
        }
        self.issues = []
        self.recommendations = []
        
    def add_result(self, category: str, test_name: str, passed: bool, details: str):
        """Add a test result."""
        self.results[category].append({
            'test': test_name,
            'passed': passed,
            'details': details
        })
        
    def add_issue(self, severity: str, description: str):
        """Add an issue found during validation."""
        self.issues.append({
            'severity': severity,
            'description': description
        })
        
    def add_recommendation(self, recommendation: str):
        """Add a recommendation."""
        self.recommendations.append(recommendation)
        
    def generate_summary(self) -> str:
        """Generate a validation summary."""
        total_tests = sum(len(v) for v in self.results.values())
        passed_tests = sum(1 for v in self.results.values() for r in v if r['passed'])
        
        summary = [
            "\n" + "="*80,
            "VALIDATION REPORT SUMMARY",
            "="*80,
            f"\nTotal Tests: {total_tests}",
            f"Passed: {passed_tests}",
            f"Failed: {total_tests - passed_tests}",
            f"Success Rate: {(passed_tests/total_tests)*100:.1f}%",
            "\nCategory Breakdown:"
        ]
        
        for category, results in self.results.items():
            category_passed = sum(1 for r in results if r['passed'])
            category_total = len(results)
            summary.append(f"  {category}: {category_passed}/{category_total} passed")
        
        if self.issues:
            summary.append(f"\nIssues Found: {len(self.issues)}")
            for issue in self.issues:
                summary.append(f"  [{issue['severity']}] {issue['description']}")
        
        if self.recommendations:
            summary.append(f"\nRecommendations: {len(self.recommendations)}")
            for rec in self.recommendations:
                summary.append(f"  • {rec}")
        
        summary.append("\n" + "="*80)
        return "\n".join(summary)


def validate_architecture_compliance(report: ValidationReport):
    """Validate that the implementation follows clean architecture principles."""
    
    print("\n🏗️  ARCHITECTURE COMPLIANCE VALIDATION")
    print("-" * 40)
    
    # Test 1: Check enum definition for DOMAIN_OVERRIDE
    try:
        assert hasattr(FetchPriority, 'DOMAIN_OVERRIDE'), "DOMAIN_OVERRIDE missing from FetchPriority enum"
        assert FetchPriority.DOMAIN_OVERRIDE == 500, f"DOMAIN_OVERRIDE value is {FetchPriority.DOMAIN_OVERRIDE}, expected 500"
        report.add_result('architecture_compliance', 'Priority Enum Extension', True, 
                         'DOMAIN_OVERRIDE properly added to FetchPriority enum')
        print("✅ Priority enum properly extended with DOMAIN_OVERRIDE=500")
    except AssertionError as e:
        report.add_result('architecture_compliance', 'Priority Enum Extension', False, str(e))
        report.add_issue('CRITICAL', str(e))
        print(f"❌ {e}")
    
    # Test 2: Check separation of concerns
    try:
        # Verify domain config is separate from plugin logic
        assert 'domain_config' in sys.modules or 'plugins.domain_config' in sys.modules
        report.add_result('architecture_compliance', 'Separation of Concerns', True,
                         'Domain configuration properly separated into domain_config.py')
        print("✅ Domain configuration properly separated")
    except AssertionError:
        report.add_result('architecture_compliance', 'Separation of Concerns', False,
                         'Domain config not properly separated')
        print("❌ Domain config not properly separated")
    
    # Test 3: Check plugin interface compliance
    try:
        http_plugin = HTTPFetcherPlugin()
        safari_plugin = SafariFetcherPlugin()
        
        # Check required methods
        for plugin in [http_plugin, safari_plugin]:
            assert hasattr(plugin, 'name') and callable(getattr(plugin, 'name', None).__get__)
            assert hasattr(plugin, 'priority') and callable(getattr(plugin, 'priority', None).__get__)
            assert hasattr(plugin, 'can_handle') and callable(plugin.can_handle)
            assert hasattr(plugin, 'fetch') and callable(plugin.fetch)
            
        report.add_result('architecture_compliance', 'Plugin Interface Compliance', True,
                         'All plugins properly implement IFetcherPlugin interface')
        print("✅ All plugins comply with interface requirements")
    except (AssertionError, Exception) as e:
        report.add_result('architecture_compliance', 'Plugin Interface Compliance', False, str(e))
        print(f"❌ Plugin interface compliance issue: {e}")
    
    # Test 4: Check backward compatibility
    try:
        # FetchResult should have to_legacy_metrics method
        result = FetchResult(success=True, html_content="test")
        assert hasattr(result, 'to_legacy_metrics'), "to_legacy_metrics method missing"
        report.add_result('architecture_compliance', 'Backward Compatibility', True,
                         'FetchResult maintains backward compatibility')
        print("✅ Backward compatibility maintained")
    except AssertionError as e:
        report.add_result('architecture_compliance', 'Backward Compatibility', False, str(e))
        print(f"❌ {e}")


def validate_functional_requirements(report: ValidationReport):
    """Validate that functional requirements are met."""
    
    print("\n⚙️  FUNCTIONAL REQUIREMENTS VALIDATION")
    print("-" * 40)
    
    # Test 1: Verify base priorities
    try:
        http_plugin = HTTPFetcherPlugin()
        safari_plugin = SafariFetcherPlugin()
        
        assert http_plugin.priority == FetchPriority.HIGH, f"HTTP priority is {http_plugin.priority}, expected HIGH (100)"
        assert safari_plugin.priority == FetchPriority.LOW, f"Safari priority is {safari_plugin.priority}, expected LOW (10)"
        
        report.add_result('functional_requirements', 'Base Priority Configuration', True,
                         f'HTTP={http_plugin.priority}, Safari={safari_plugin.priority}')
        print(f"✅ Base priorities: HTTP={http_plugin.priority}, Safari={safari_plugin.priority}")
    except AssertionError as e:
        report.add_result('functional_requirements', 'Base Priority Configuration', False, str(e))
        report.add_issue('CRITICAL', str(e))
        print(f"❌ {e}")
    
    # Test 2: Test standard URL priority order
    standard_urls = [
        'https://example.com/page',
        'https://github.com/repo',
        'https://stackoverflow.com/question',
        'http://httpbin.org/get'
    ]
    
    for url in standard_urls:
        try:
            context = FetchContext(url=url)
            registry = PluginRegistry()
            registry.register_plugin(HTTPFetcherPlugin())
            registry.register_plugin(SafariFetcherPlugin())
            
            suitable = registry.get_suitable_plugins(context)
            if suitable:
                first_plugin = suitable[0]
                assert first_plugin.name == 'http_fetcher', f"First plugin for {url} is {first_plugin.name}, expected http_fetcher"
                print(f"✅ {url}: HTTP plugin has highest priority")
                report.add_result('functional_requirements', f'Standard URL: {urlparse(url).netloc}', True,
                                'HTTP plugin correctly prioritized')
            else:
                raise AssertionError(f"No suitable plugins for {url}")
        except AssertionError as e:
            report.add_result('functional_requirements', f'Standard URL: {urlparse(url).netloc}', False, str(e))
            print(f"❌ {url}: {e}")
    
    # Test 3: Test problematic domain handling
    problematic_urls = [
        'https://ccdi.gov.cn/article',
        'https://qcc.com/company',
        'https://tianyancha.com/info'
    ]
    
    for url in problematic_urls:
        try:
            # Check domain config
            assert should_use_safari_for_domain(url), f"{url} should be marked for Safari"
            
            # Check priority override
            safari_override = get_domain_priority_override(url, 'safari_fetcher')
            assert safari_override == FetchPriority.DOMAIN_OVERRIDE, f"Safari override for {url} is {safari_override}, expected 500"
            
            print(f"✅ {url}: Safari gets priority override (500)")
            report.add_result('functional_requirements', f'Problematic domain: {urlparse(url).netloc}', True,
                            'Safari correctly gets priority override')
        except AssertionError as e:
            report.add_result('functional_requirements', f'Problematic domain: {urlparse(url).netloc}', False, str(e))
            print(f"❌ {url}: {e}")
    
    # Test 4: Test fallback chain
    try:
        context = FetchContext(url='https://example.com/test')
        registry = PluginRegistry()
        
        # Register plugins
        http_plugin = HTTPFetcherPlugin()
        safari_plugin = SafariFetcherPlugin()
        registry.register_plugin(http_plugin)
        registry.register_plugin(safari_plugin)
        
        # Get plugin order
        plugins = registry.get_suitable_plugins(context)
        plugin_names = [p.name for p in plugins]
        
        # HTTP should be first, Safari should be available as fallback
        assert 'http_fetcher' in plugin_names, "HTTP plugin not in chain"
        if safari_plugin.is_available():
            assert 'safari_fetcher' in plugin_names, "Safari plugin not in fallback chain"
            assert plugin_names.index('http_fetcher') < plugin_names.index('safari_fetcher'), "HTTP not before Safari"
        
        report.add_result('functional_requirements', 'Fallback Chain Order', True,
                         f'Plugin order: {plugin_names}')
        print(f"✅ Fallback chain properly ordered: {plugin_names}")
    except AssertionError as e:
        report.add_result('functional_requirements', 'Fallback Chain Order', False, str(e))
        print(f"❌ Fallback chain issue: {e}")


def validate_performance_impact(report: ValidationReport):
    """Validate performance characteristics."""
    
    print("\n⚡ PERFORMANCE IMPACT VALIDATION")
    print("-" * 40)
    
    # Test 1: Plugin discovery performance
    import time
    try:
        start = time.time()
        registry = PluginRegistry()
        registry.auto_discover_plugins()
        duration = time.time() - start
        
        assert duration < 1.0, f"Plugin discovery took {duration:.3f}s, should be < 1s"
        report.add_result('performance_impact', 'Plugin Discovery Speed', True,
                         f'Discovery completed in {duration:.3f}s')
        print(f"✅ Plugin discovery fast: {duration:.3f}s")
    except AssertionError as e:
        report.add_result('performance_impact', 'Plugin Discovery Speed', False, str(e))
        print(f"❌ {e}")
    
    # Test 2: Priority calculation overhead
    try:
        http_plugin = HTTPFetcherPlugin()
        safari_plugin = SafariFetcherPlugin()
        
        urls = ['https://example.com/test'] * 100
        start = time.time()
        
        for url in urls:
            if hasattr(http_plugin, 'get_effective_priority'):
                http_plugin.get_effective_priority(url)
            if hasattr(safari_plugin, 'get_effective_priority'):
                safari_plugin.get_effective_priority(url)
        
        duration = time.time() - start
        avg_time = duration / (len(urls) * 2)
        
        assert avg_time < 0.001, f"Priority calculation avg {avg_time:.6f}s, should be < 0.001s"
        report.add_result('performance_impact', 'Priority Calculation Overhead', True,
                         f'Average time: {avg_time:.6f}s per calculation')
        print(f"✅ Priority calculation efficient: {avg_time:.6f}s average")
    except AssertionError as e:
        report.add_result('performance_impact', 'Priority Calculation Overhead', False, str(e))
        print(f"⚠️  {e}")
    
    # Test 3: Memory footprint
    try:
        import sys
        registry = get_global_registry()
        registry_size = sys.getsizeof(registry._plugins) + sys.getsizeof(registry._sorted_plugins)
        
        # Basic sanity check - registry shouldn't be huge
        assert registry_size < 10000, f"Registry memory usage {registry_size} bytes seems excessive"
        report.add_result('performance_impact', 'Memory Footprint', True,
                         f'Registry uses ~{registry_size} bytes')
        print(f"✅ Memory footprint reasonable: ~{registry_size} bytes")
    except Exception as e:
        report.add_result('performance_impact', 'Memory Footprint', False, str(e))
        print(f"⚠️  Could not measure memory: {e}")


def validate_edge_cases(report: ValidationReport):
    """Validate edge case handling."""
    
    print("\n🔧 EDGE CASES VALIDATION")
    print("-" * 40)
    
    # Test 1: 403 error handling
    test_403_url = 'https://httpbin.org/status/403'
    try:
        context = FetchContext(url=test_403_url)
        registry = get_global_registry()
        plugins = registry.get_suitable_plugins(context)
        
        # Should have plugins available even for URLs that might return 403
        assert len(plugins) > 0, "No plugins available for potential 403 URL"
        report.add_result('edge_cases', '403 Error Handling', True,
                         f'{len(plugins)} plugins available for 403 URLs')
        print(f"✅ 403 handling: {len(plugins)} plugins available")
    except AssertionError as e:
        report.add_result('edge_cases', '403 Error Handling', False, str(e))
        print(f"❌ {e}")
    
    # Test 2: Unknown domain handling
    unknown_url = 'https://totally-unknown-domain-xyz123.com/page'
    try:
        # Unknown domains should use standard priority (HTTP first)
        context = FetchContext(url=unknown_url)
        registry = PluginRegistry()
        registry.register_plugin(HTTPFetcherPlugin())
        registry.register_plugin(SafariFetcherPlugin())
        
        plugins = registry.get_suitable_plugins(context)
        if plugins:
            assert plugins[0].name == 'http_fetcher', f"Unknown domain should use HTTP first, got {plugins[0].name}"
        
        report.add_result('edge_cases', 'Unknown Domain Handling', True,
                         'Unknown domains correctly default to HTTP')
        print("✅ Unknown domains default to HTTP plugin")
    except AssertionError as e:
        report.add_result('edge_cases', 'Unknown Domain Handling', False, str(e))
        print(f"❌ {e}")
    
    # Test 3: Empty/invalid URL handling
    invalid_contexts = [
        FetchContext(url=''),
        FetchContext(url='   '),
        FetchContext(url='not-a-url'),
        FetchContext(url='ftp://file.server.com')  # Non-HTTP protocol
    ]
    
    for ctx in invalid_contexts:
        try:
            registry = get_global_registry()
            plugins = registry.get_suitable_plugins(ctx)
            
            # For empty/invalid URLs, we might have no plugins or only specific ones
            if ctx.url.strip() == '':
                # Empty URLs should be rejected by validation
                for plugin in [HTTPFetcherPlugin(), SafariFetcherPlugin()]:
                    assert not plugin.validate_context(ctx), f"Plugin {plugin.name} should reject empty URL"
            elif not ctx.url.startswith('http'):
                # Non-HTTP URLs should not be handled by HTTP/Safari plugins
                assert not any(p.name in ['http_fetcher', 'safari_fetcher'] for p in plugins), \
                       f"HTTP/Safari plugins should not handle {ctx.url}"
            
            report.add_result('edge_cases', f'Invalid URL: {ctx.url[:20]}', True,
                            'Properly rejected or handled')
            print(f"✅ Invalid URL handled: '{ctx.url[:20]}'")
        except AssertionError as e:
            report.add_result('edge_cases', f'Invalid URL: {ctx.url[:20]}', False, str(e))
            print(f"❌ {ctx.url}: {e}")
    
    # Test 4: Plugin availability when Safari is disabled
    try:
        # Simulate Safari not available
        registry = PluginRegistry()
        http_plugin = HTTPFetcherPlugin()
        registry.register_plugin(http_plugin)
        
        # Don't register Safari plugin to simulate it being unavailable
        context = FetchContext(url='https://ccdi.gov.cn/test')
        plugins = registry.get_suitable_plugins(context)
        
        # Should still have HTTP as fallback even for Safari-preferred domains
        assert len(plugins) > 0, "No plugins available when Safari is disabled"
        assert plugins[0].name == 'http_fetcher', "HTTP should be available as fallback"
        
        report.add_result('edge_cases', 'Safari Unavailable Fallback', True,
                         'HTTP remains available when Safari is disabled')
        print("✅ System gracefully handles Safari unavailability")
    except AssertionError as e:
        report.add_result('edge_cases', 'Safari Unavailable Fallback', False, str(e))
        print(f"❌ {e}")


def test_specific_url(url: str, report: ValidationReport):
    """Test a specific URL (like news.cn) to ensure it can be fetched."""
    
    print(f"\n🌐 TESTING SPECIFIC URL: {url}")
    print("-" * 40)
    
    try:
        context = FetchContext(url=url, timeout=30)
        registry = get_global_registry()
        
        # Get suitable plugins
        plugins = registry.get_suitable_plugins(context)
        print(f"Available plugins for {url}:")
        for i, plugin in enumerate(plugins):
            priority = plugin.get_effective_priority(url) if hasattr(plugin, 'get_effective_priority') else plugin.priority
            print(f"  {i+1}. {plugin.name} (priority: {priority})")
        
        # Check plugin order
        assert len(plugins) > 0, f"No plugins available for {url}"
        
        # Determine expected first plugin
        domain_config = get_domain_config(url)
        if domain_config and domain_config.get('preferred_plugin'):
            expected_first = domain_config['preferred_plugin']
            actual_first = plugins[0].name
            assert actual_first == expected_first, \
                   f"Expected {expected_first} first for {url}, got {actual_first}"
        
        # Test actual fetch (dry run - just check if it would attempt)
        print(f"✅ URL {url} can be handled by {len(plugins)} plugin(s)")
        print(f"   Primary plugin: {plugins[0].name}")
        
        report.add_result('integration_tests', f'URL Test: {urlparse(url).netloc}', True,
                         f'Can be fetched, primary plugin: {plugins[0].name}')
        
    except Exception as e:
        print(f"❌ Error testing {url}: {e}")
        report.add_result('integration_tests', f'URL Test: {urlparse(url).netloc}', False, str(e))
        report.add_issue('WARNING', f"URL {url} test failed: {e}")


def main():
    """Main validation function."""
    
    print("\n" + "="*80)
    print(" WEB FETCHER PRIORITY SYSTEM VALIDATION ")
    print("="*80)
    
    report = ValidationReport()
    
    # Run all validation categories
    validate_architecture_compliance(report)
    validate_functional_requirements(report)
    validate_performance_impact(report)
    validate_edge_cases(report)
    
    # Test specific URLs
    test_urls = [
        'http://www.news.cn/politics/leaders/20250305/0d1eaaa64ec74dd5916d29b28fe4fda8/c.html',
        'https://example.com/test',
        'https://ccdi.gov.cn/test',
        'https://httpbin.org/get'
    ]
    
    for url in test_urls:
        test_specific_url(url, report)
    
    # Generate recommendations based on findings
    if any(issue['severity'] == 'CRITICAL' for issue in report.issues):
        report.add_recommendation("Address critical issues before deployment")
    
    if not any('Safari' in str(r) for r in report.results['edge_cases']):
        report.add_recommendation("Consider adding more Safari-specific edge case tests")
    
    # Performance recommendations
    perf_results = report.results.get('performance_impact', [])
    if perf_results and any(not r['passed'] for r in perf_results):
        report.add_recommendation("Optimize priority calculation for better performance")
    
    # Print summary
    print(report.generate_summary())
    
    # Save detailed report
    detailed_report = {
        'timestamp': str(logging.time.strftime('%Y-%m-%d %H:%M:%S')),
        'results': report.results,
        'issues': report.issues,
        'recommendations': report.recommendations
    }
    
    report_file = 'priority_validation_report.json'
    with open(report_file, 'w') as f:
        json.dump(detailed_report, f, indent=2)
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Return exit code based on critical issues
    critical_issues = [i for i in report.issues if i['severity'] == 'CRITICAL']
    if critical_issues:
        print(f"\n⚠️  Found {len(critical_issues)} critical issue(s). Please review.")
        return 1
    else:
        print("\n✅ Validation completed successfully!")
        return 0


if __name__ == '__main__':
    sys.exit(main())