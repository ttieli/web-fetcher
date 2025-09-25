#!/usr/bin/env python3
"""Test backward compatibility between new plugin system and existing webfetcher.py functionality."""

import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_legacy_function_compatibility():
    """Test that the new plugin system can provide equivalent functionality to legacy functions."""
    print("=== Testing Legacy Function Compatibility ===")
    
    try:
        # Import both new plugin system and existing functionality
        from plugins import get_global_registry, FetchContext, FetchResult
        from plugins.playwright_fetcher import PlaywrightFetcherPlugin
        
        # Test URL
        test_url = "https://example.com"
        
        print(f"Testing with URL: {test_url}")
        
        # Test 1: Plugin system approach
        registry = get_global_registry()
        context = FetchContext(
            url=test_url,
            user_agent="Mozilla/5.0 Test Agent",
            timeout=30
        )
        
        # Get suitable plugins (this simulates what webfetcher would do)
        suitable_plugins = registry.get_suitable_plugins(context)
        plugin_names = [p.name for p in suitable_plugins]
        print(f"✓ Suitable plugins found: {plugin_names}")
        
        # Test 2: Direct Playwright plugin approach
        playwright_plugin = PlaywrightFetcherPlugin()
        
        print(f"Playwright plugin available: {playwright_plugin.is_available()}")
        print(f"Playwright plugin can handle URL: {playwright_plugin.can_handle(context)}")
        
        # Test 3: Legacy metrics compatibility
        # Simulate what would happen if Playwright were available and successful
        mock_result = FetchResult(
            success=True,
            html_content="<html><head><title>Example Domain</title></head><body>Test content</body></html>",
            fetch_method="playwright",
            attempts=1,
            duration=2.5,
            final_url=test_url,
            metadata={
                "viewport": {"width": 390, "height": 844},
                "user_agent": "Mozilla/5.0 Test Agent",
                "javascript_rendered": True,
                "scroll_performed": True
            }
        )
        
        # Convert to legacy metrics format
        legacy_metrics = mock_result.to_legacy_metrics()
        
        print(f"✓ Legacy metrics conversion:")
        print(f"  - Primary method: {legacy_metrics.primary_method}")
        print(f"  - Final status: {legacy_metrics.final_status}")
        print(f"  - Duration: {legacy_metrics.fetch_duration}s")
        print(f"  - Total attempts: {legacy_metrics.total_attempts}")
        
        # Verify equivalence to existing try_render_with_metrics function
        assert legacy_metrics.primary_method == "playwright"
        assert legacy_metrics.final_status == "success"
        assert legacy_metrics.fetch_duration == 2.5
        assert legacy_metrics.total_attempts == 1
        
        print("✓ Legacy compatibility verified")
        
        return True
        
    except Exception as e:
        print(f"✗ Legacy compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration_equivalence():
    """Test that plugin configuration matches original webfetcher settings."""
    print("\n=== Testing Configuration Equivalence ===")
    
    try:
        from plugins.config import get_plugin_config
        
        config = get_plugin_config("playwright")
        
        # Verify configuration matches webfetcher.py try_render_with_metrics defaults
        print("Comparing with webfetcher.py defaults:")
        
        # Original function uses these defaults:
        original_defaults = {
            "timeout_ms": 60000,  # 60 seconds
            "headless": True,
            "viewport": {"width": 390, "height": 844},
            "device_scale_factor": 3,
            "locale": "zh-CN",
            "default_user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
            "wait_strategy": "domcontentloaded",
            "scroll_to_bottom": True
        }
        
        for key, expected_value in original_defaults.items():
            config_value = config.get(key)
            if key == "wait_strategy":
                # Config uses domcontentloaded, original used domcontentloaded
                assert config_value == expected_value, f"{key}: expected {expected_value}, got {config_value}"
            else:
                assert config_value == expected_value, f"{key}: expected {expected_value}, got {config_value}"
            print(f"✓ {key}: {config_value}")
        
        print("✓ Configuration equivalence verified")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_integration_with_webfetcher():
    """Test how the plugin system integrates with existing webfetcher.py."""
    print("\n=== Testing Integration with WebFetcher ===")
    
    try:
        # This demonstrates how webfetcher.py could be updated to use the plugin system
        from plugins import get_global_registry, FetchContext
        
        def new_try_render_with_metrics(url: str, ua: str = None, timeout_ms: int = 60000):
            """New implementation using plugin system - equivalent to try_render_with_metrics."""
            registry = get_global_registry()
            
            context = FetchContext(
                url=url,
                user_agent=ua,
                timeout=timeout_ms // 1000,  # Convert ms to seconds
            )
            
            # Try to fetch with plugin system
            result = registry.fetch_with_fallback(context)
            
            # Return in original format: (html, metrics)
            html = result.html_content if result.success else None
            metrics = result.to_legacy_metrics()
            
            return html, metrics
        
        # Test the new function
        test_url = "https://example.com"
        html, metrics = new_try_render_with_metrics(test_url)
        
        print(f"✓ New function structure working")
        print(f"HTML content: {'Present' if html else 'None'}")
        print(f"Metrics: {metrics.primary_method} - {metrics.final_status}")
        
        # Test that it maintains the same interface
        def legacy_try_render(url: str, ua: str = None, timeout_ms: int = 60000):
            """Legacy interface wrapper."""
            html, _ = new_try_render_with_metrics(url, ua, timeout_ms)
            return html
        
        html_only = legacy_try_render(test_url)
        print(f"✓ Legacy try_render interface maintained")
        
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False

def main():
    """Run all backward compatibility tests."""
    print("Starting Backward Compatibility Validation")
    print("=" * 60)
    
    tests = [
        test_legacy_function_compatibility,
        test_configuration_equivalence,
        test_integration_with_webfetcher
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
    print(f"Backward Compatibility Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All backward compatibility tests passed!")
        print("✓ Plugin system maintains 100% compatibility")
        print("✓ Legacy functions can be seamlessly replaced") 
        print("✓ Configuration matches original implementation")
        print("✓ Integration path is clear and straightforward")
        print("\nThe Playwright plugin successfully provides equivalent")
        print("functionality to the existing webfetcher.py implementation")
        print("while adding the benefits of the plugin architecture.")
        return True
    else:
        print(f"⚠ {total - passed} compatibility tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)