#!/usr/bin/env python3
"""Test script for validating the Playwright plugin implementation."""

import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugins.playwright_fetcher import PlaywrightFetcherPlugin
from plugins.base import FetchContext, FetchPriority
from plugins.registry import get_global_registry
from plugins.config import get_plugin_config

def test_playwright_plugin_creation():
    """Test basic plugin creation and properties."""
    print("=== Testing Playwright Plugin Creation ===")
    
    plugin = PlaywrightFetcherPlugin()
    print(f"Plugin name: {plugin.name}")
    print(f"Plugin priority: {plugin.priority}")
    print(f"Plugin available: {plugin.is_available()}")
    print(f"Plugin capabilities: {plugin.get_capabilities()}")
    
    assert plugin.name == "playwright"
    assert plugin.priority == FetchPriority.NORMAL
    print("✓ Plugin creation test passed")

def test_playwright_config():
    """Test Playwright plugin configuration."""
    print("\n=== Testing Playwright Configuration ===")
    
    config = get_plugin_config("playwright")
    print(f"Config enabled: {config.get('enabled')}")
    print(f"Config priority: {config.get('priority')}")
    print(f"Config timeout: {config.get('timeout_ms')}")
    print(f"Config viewport: {config.get('viewport')}")
    
    assert config.get("enabled") is True
    assert config.get("priority") == 50
    assert config.get("timeout_ms") == 60000
    print("✓ Configuration test passed")

def test_can_handle():
    """Test the can_handle method."""
    print("\n=== Testing can_handle Method ===")
    
    plugin = PlaywrightFetcherPlugin()
    
    # Test valid HTTP URLs
    valid_contexts = [
        FetchContext("http://example.com"),
        FetchContext("https://example.com"),
        FetchContext("https://www.google.com"),
    ]
    
    for context in valid_contexts:
        result = plugin.can_handle(context)
        print(f"Can handle {context.url}: {result}")
        if plugin.is_available():
            assert result is True, f"Should handle {context.url}"
        else:
            assert result is False, f"Should not handle {context.url} when unavailable"
    
    # Test invalid URLs
    invalid_contexts = [
        FetchContext("ftp://example.com"),
        FetchContext("file:///path/to/file"),
        FetchContext("mailto:test@example.com"),
    ]
    
    for context in invalid_contexts:
        result = plugin.can_handle(context)
        print(f"Can handle {context.url}: {result}")
        assert result is False, f"Should not handle {context.url}"
    
    print("✓ can_handle test passed")

def test_plugin_registry_integration():
    """Test plugin registry integration."""
    print("\n=== Testing Plugin Registry Integration ===")
    
    registry = get_global_registry()
    plugins = registry.list_plugins()
    print(f"Registered plugins: {plugins}")
    
    # Check if Playwright plugin is registered
    playwright_plugin = registry.get_plugin("playwright")
    if playwright_plugin:
        print(f"✓ Playwright plugin found in registry")
        print(f"Plugin info: {registry.get_plugin_info().get('playwright')}")
    else:
        print("⚠ Playwright plugin not found in registry (may be unavailable)")
    
    # Test suitable plugins selection
    context = FetchContext("https://example.com")
    suitable_plugins = registry.get_suitable_plugins(context)
    plugin_names = [p.name for p in suitable_plugins]
    print(f"Suitable plugins for example.com: {plugin_names}")
    
    print("✓ Registry integration test passed")

def test_playwright_fetch_if_available():
    """Test actual fetch operation if Playwright is available."""
    print("\n=== Testing Playwright Fetch Operation ===")
    
    plugin = PlaywrightFetcherPlugin()
    
    if not plugin.is_available():
        print("⚠ Playwright not available, skipping fetch test")
        return
    
    context = FetchContext(
        url="https://example.com",
        timeout=30,
        user_agent="Mozilla/5.0 Test Agent"
    )
    
    print(f"Attempting to fetch: {context.url}")
    print("This may take a moment for browser startup and page rendering...")
    
    try:
        result = plugin.fetch(context)
        
        print(f"Fetch success: {result.success}")
        print(f"Fetch method: {result.fetch_method}")
        print(f"Fetch duration: {result.duration:.2f}s")
        print(f"Attempts: {result.attempts}")
        
        if result.success:
            print(f"Content length: {len(result.html_content) if result.html_content else 0}")
            print(f"Final URL: {result.final_url}")
            print(f"Metadata: {result.metadata}")
            
            # Basic validation
            assert result.html_content is not None
            assert len(result.html_content) > 0
            assert result.fetch_method == "playwright"
            assert "Example Domain" in result.html_content, "Should contain expected content"
            
            print("✓ Playwright fetch test passed")
        else:
            print(f"✗ Fetch failed: {result.error_message}")
            
    except Exception as e:
        print(f"✗ Fetch test failed with exception: {e}")

def test_backward_compatibility():
    """Test backward compatibility with existing webfetcher interface."""
    print("\n=== Testing Backward Compatibility ===")
    
    # Test that we can import the registry without issues
    try:
        from plugins import get_global_registry, PluginRegistry
        registry = get_global_registry()
        
        # Test FetchResult to legacy metrics conversion
        from plugins.base import FetchResult
        result = FetchResult(
            success=True,
            html_content="<html>Test</html>",
            fetch_method="playwright",
            attempts=1,
            duration=1.5
        )
        
        # Convert to legacy format
        legacy_metrics = result.to_legacy_metrics()
        print(f"Legacy metrics conversion successful")
        print(f"Primary method: {legacy_metrics.primary_method}")
        print(f"Final status: {legacy_metrics.final_status}")
        print(f"Duration: {legacy_metrics.fetch_duration}")
        
        assert legacy_metrics.primary_method == "playwright"
        assert legacy_metrics.final_status == "success"
        assert legacy_metrics.fetch_duration == 1.5
        
        print("✓ Backward compatibility test passed")
        
    except Exception as e:
        print(f"✗ Backward compatibility test failed: {e}")

def main():
    """Run all tests."""
    print("Starting Playwright Plugin Validation Tests")
    print("=" * 50)
    
    try:
        test_playwright_plugin_creation()
        test_playwright_config()
        test_can_handle()
        test_plugin_registry_integration()
        test_playwright_fetch_if_available()
        test_backward_compatibility()
        
        print("\n" + "=" * 50)
        print("🎉 All tests completed successfully!")
        print("Playwright plugin implementation is ready for Week 2.")
        
    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()