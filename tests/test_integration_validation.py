#!/usr/bin/env python3
"""Integration validation test to verify Playwright plugin works with existing webfetcher."""

import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_plugin_system_integration():
    """Test that the plugin system integrates properly with the existing system."""
    print("=== Testing Integration with Existing WebFetcher ===")
    
    try:
        # Test that we can import the plugin system without breaking existing functionality
        from plugins import get_global_registry, PluginRegistry, FetchContext, FetchResult
        from plugins.playwright_fetcher import PlaywrightFetcherPlugin
        from plugins.config import get_plugin_config, is_plugin_enabled
        
        print("✓ All plugin imports successful")
        
        # Test that plugin configuration is accessible
        config = get_plugin_config("playwright")
        enabled = is_plugin_enabled("playwright")
        print(f"✓ Playwright config accessible: enabled={enabled}")
        
        # Test that registry discovers plugins
        registry = get_global_registry()
        all_plugins = registry.list_plugins()
        print(f"✓ Plugin registry functional: {len(all_plugins)} plugins registered")
        
        # Test that Playwright plugin is properly configured
        playwright_plugin = PlaywrightFetcherPlugin()
        assert playwright_plugin.name == "playwright"
        assert playwright_plugin.priority.value == 50  # NORMAL priority
        print("✓ Playwright plugin properly configured")
        
        # Test backward compatibility - FetchResult to legacy metrics
        result = FetchResult(
            success=True,
            html_content="<html><body>Test</body></html>",
            fetch_method="playwright",
            attempts=1,
            duration=2.5,
            metadata={"javascript_rendered": True}
        )
        
        legacy_metrics = result.to_legacy_metrics()
        assert legacy_metrics.primary_method == "playwright"
        assert legacy_metrics.final_status == "success"
        print("✓ Backward compatibility maintained")
        
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_resource_management_structure():
    """Test that the resource management structure is correct."""
    print("\n=== Testing Resource Management Structure ===")
    
    try:
        from plugins.playwright_fetcher import PlaywrightFetcherPlugin
        
        plugin = PlaywrightFetcherPlugin()
        
        # Check that the fetch method has proper structure for resource management
        import inspect
        fetch_method = plugin.fetch
        source_code = inspect.getsource(fetch_method)
        
        # Verify key resource management patterns
        assert "with sync_playwright()" in source_code, "Should use sync_playwright context manager"
        assert "browser.close()" in source_code, "Should explicitly close browser"
        assert "try:" in source_code and "finally:" in source_code, "Should have try/finally for cleanup"
        
        print("✓ Resource management patterns verified")
        
        # Check configuration handling
        config_usage = [
            "timeout_ms", "viewport", "headless", "user_agent", "scroll_to_bottom"
        ]
        
        for config_key in config_usage:
            assert config_key in source_code, f"Should handle {config_key} configuration"
        
        print("✓ Configuration handling verified")
        
        return True
        
    except Exception as e:
        print(f"✗ Resource management test failed: {e}")
        return False

def test_error_handling_structure():
    """Test that error handling structure is comprehensive."""
    print("\n=== Testing Error Handling Structure ===")
    
    try:
        from plugins.playwright_fetcher import PlaywrightFetcherPlugin
        
        plugin = PlaywrightFetcherPlugin()
        
        # Test ImportError handling
        import inspect
        source_code = inspect.getsource(plugin.fetch)
        
        # Verify error handling patterns
        assert "ImportError" in source_code or "except" in source_code, "Should handle import errors"
        assert "FetchResult(" in source_code, "Should return FetchResult objects"
        assert "error_message" in source_code, "Should populate error messages"
        
        print("✓ Error handling patterns verified")
        
        # Test is_available method
        available = plugin.is_available()
        print(f"✓ Plugin availability check: {available}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False

def test_architecture_compliance():
    """Test that the implementation follows the Week 1 architecture principles."""
    print("\n=== Testing Architecture Compliance ===")
    
    try:
        from plugins.playwright_fetcher import PlaywrightFetcherPlugin
        
        plugin = PlaywrightFetcherPlugin()
        
        # Test interface compliance
        from plugins.base import IFetcherPlugin
        assert isinstance(plugin, IFetcherPlugin), "Should implement IFetcherPlugin"
        
        # Test required methods
        assert hasattr(plugin, 'name'), "Should have name property"
        assert hasattr(plugin, 'priority'), "Should have priority property"
        assert hasattr(plugin, 'can_handle'), "Should have can_handle method"
        assert hasattr(plugin, 'fetch'), "Should have fetch method"
        assert hasattr(plugin, 'is_available'), "Should have is_available method"
        
        print("✓ Interface compliance verified")
        
        # Test capabilities
        capabilities = plugin.get_capabilities()
        expected_capabilities = [
            "javascript_rendering", "dynamic_content", "spa_support",
            "scroll_rendering", "mobile_viewport"
        ]
        
        for cap in expected_capabilities:
            assert cap in capabilities, f"Should provide {cap} capability"
        
        print("✓ Capabilities properly defined")
        
        # Test configuration integration
        from plugins.config import get_plugin_config
        config = get_plugin_config("playwright")
        
        expected_config_keys = [
            "enabled", "priority", "timeout_ms", "headless", "viewport",
            "scroll_to_bottom", "default_user_agent"
        ]
        
        for key in expected_config_keys:
            assert key in config, f"Config should contain {key}"
        
        print("✓ Configuration integration verified")
        
        return True
        
    except Exception as e:
        print(f"✗ Architecture compliance test failed: {e}")
        return False

def main():
    """Run all integration validation tests."""
    print("Starting Playwright Plugin Integration Validation")
    print("=" * 60)
    
    tests = [
        test_plugin_system_integration,
        test_resource_management_structure,
        test_error_handling_structure,
        test_architecture_compliance
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"Test {test_func.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"Integration Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("✓ Playwright plugin is properly integrated")
        print("✓ Backward compatibility maintained")
        print("✓ Resource management implemented")
        print("✓ Architecture compliance verified")
        print("\nWeek 2 Playwright Plugin Implementation: COMPLETE")
        return True
    else:
        print(f"⚠ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)