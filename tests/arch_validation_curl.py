#!/usr/bin/env python3
"""
Architecture Validation Test for Curl Plugin Implementation
架构验证测试 - Curl插件实施
"""

import sys
import os
import subprocess
import importlib.util

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def validate_curl_plugin():
    """Comprehensive validation of curl plugin implementation."""
    
    print("=" * 60)
    print("ARCHITECTURE VALIDATION: CURL PLUGIN")
    print("架构验证：Curl插件")
    print("=" * 60)
    
    results = {
        "structure": [],
        "integration": [],
        "functionality": [],
        "quality": []
    }
    
    # 1. STRUCTURE VALIDATION
    print("\n1. STRUCTURE VALIDATION / 结构验证")
    print("-" * 50)
    
    # Check plugin files exist
    plugin_files = [
        "plugins/curl.py",
        "plugins/config.py",
        "plugins/base.py",
        "plugins/registry.py"
    ]
    
    for file in plugin_files:
        if os.path.exists(file):
            print(f"  ✓ {file} exists")
            results["structure"].append((True, f"{file} exists"))
        else:
            print(f"  ✗ {file} missing")
            results["structure"].append((False, f"{file} missing"))
    
    # 2. INTEGRATION VALIDATION
    print("\n2. INTEGRATION VALIDATION / 集成验证")
    print("-" * 50)
    
    try:
        # Import and check curl plugin
        from plugins.curl import CurlFetcherPlugin
        print("  ✓ CurlFetcherPlugin imported successfully")
        results["integration"].append((True, "Plugin imports correctly"))
        
        # Check plugin instantiation
        plugin = CurlFetcherPlugin()
        print(f"  ✓ Plugin instantiated: {plugin.name}")
        results["integration"].append((True, "Plugin instantiates"))
        
        # Check availability
        is_available = plugin.is_available()
        if is_available:
            print("  ✓ Curl command available on system")
            results["integration"].append((True, "Curl available"))
        else:
            print("  ✗ Curl command not available")
            results["integration"].append((False, "Curl not available"))
            
        # Check priority
        from plugins.base import FetchPriority
        if plugin.priority == FetchPriority.FALLBACK:
            print(f"  ✓ Correct priority: FALLBACK ({plugin.priority})")
            results["integration"].append((True, "Correct priority"))
        else:
            print(f"  ✗ Wrong priority: {plugin.priority}")
            results["integration"].append((False, f"Wrong priority: {plugin.priority}"))
            
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        results["integration"].append((False, f"Import error: {e}"))
    except Exception as e:
        print(f"  ✗ Integration error: {e}")
        results["integration"].append((False, f"Integration error: {e}"))
    
    # 3. FUNCTIONALITY VALIDATION
    print("\n3. FUNCTIONALITY VALIDATION / 功能验证")
    print("-" * 50)
    
    try:
        from plugins.curl import CurlFetcherPlugin
        from plugins.base import FetchContext
        
        plugin = CurlFetcherPlugin()
        
        # Test can_handle
        test_urls = [
            "https://example.com",
            "http://example.com",
            "ftp://example.com",  # Should NOT handle
        ]
        
        for url in test_urls:
            context = FetchContext(url=url)
            can_handle = plugin.can_handle(context)
            expected = url.startswith(('http://', 'https://'))
            
            if can_handle == expected:
                print(f"  ✓ can_handle({url}): {can_handle} (correct)")
                results["functionality"].append((True, f"can_handle {url}"))
            else:
                print(f"  ✗ can_handle({url}): {can_handle} (expected {expected})")
                results["functionality"].append((False, f"can_handle {url}"))
        
        # Test capabilities
        capabilities = plugin.get_capabilities()
        expected_capabilities = ["ssl_bypass", "redirect_follow", "compression"]
        for cap in expected_capabilities:
            if cap in capabilities:
                print(f"  ✓ Capability: {cap}")
                results["functionality"].append((True, f"Has {cap}"))
            else:
                print(f"  ✗ Missing capability: {cap}")
                results["functionality"].append((False, f"Missing {cap}"))
                
        # Test actual fetch (safe URL)
        print("\n  Testing actual fetch...")
        context = FetchContext(url="https://httpbin.org/html", timeout=10)
        result = plugin.fetch(context)
        
        if result.success and result.html_content:
            print(f"  ✓ Fetch successful: {len(result.html_content)} chars")
            results["functionality"].append((True, "Fetch works"))
            
            # Check metadata
            if result.metadata.get('ssl_fallback_used'):
                print("  ✓ Metadata includes ssl_fallback_used")
                results["functionality"].append((True, "Metadata correct"))
            
            if result.duration > 0:
                print(f"  ✓ Duration tracked: {result.duration:.2f}s")
                results["functionality"].append((True, "Duration tracked"))
        else:
            print(f"  ✗ Fetch failed: {result.error_message}")
            results["functionality"].append((False, f"Fetch failed: {result.error_message}"))
            
    except Exception as e:
        print(f"  ✗ Functionality test error: {e}")
        results["functionality"].append((False, f"Test error: {e}"))
    
    # 4. CODE QUALITY VALIDATION
    print("\n4. CODE QUALITY VALIDATION / 代码质量验证")
    print("-" * 50)
    
    try:
        # Check for proper error handling
        with open("plugins/curl.py", "r") as f:
            code = f.read()
            
        # Check for key quality indicators
        quality_checks = [
            ("try/except blocks", "try:" in code and "except" in code),
            ("logging usage", "logger" in code or "logging" in code),
            ("timeout handling", "timeout" in code.lower()),
            ("error messages", "error_message" in code),
            ("docstrings", '"""' in code),
            ("type hints", "-> FetchResult" in code),
        ]
        
        for check_name, condition in quality_checks:
            if condition:
                print(f"  ✓ {check_name}")
                results["quality"].append((True, check_name))
            else:
                print(f"  ✗ Missing: {check_name}")
                results["quality"].append((False, f"Missing {check_name}"))
                
    except Exception as e:
        print(f"  ✗ Quality check error: {e}")
        results["quality"].append((False, f"Check error: {e}"))
    
    # 5. REGISTRY INTEGRATION
    print("\n5. REGISTRY INTEGRATION / 注册表集成")
    print("-" * 50)
    
    try:
        from plugins.registry import get_global_registry
        from plugins.base import FetchContext
        
        registry = get_global_registry()
        
        # Check if curl plugin is registered
        curl_plugin = registry.get_plugin("curl")
        if curl_plugin:
            print("  ✓ Curl plugin registered in global registry")
            results["integration"].append((True, "Registry integration"))
            
            # Test registry fetch with fallback
            context = FetchContext(url="https://httpbin.org/html", timeout=10)
            suitable = registry.get_suitable_plugins(context)
            plugin_names = [p.name for p in suitable]
            
            print(f"  ✓ Suitable plugins: {plugin_names}")
            
            if "curl" in plugin_names:
                print("  ✓ Curl available as fallback")
                results["integration"].append((True, "Curl in fallback chain"))
        else:
            print("  ⚠ Curl plugin not in registry (may need manual registration)")
            results["integration"].append((False, "Not in registry"))
            
    except Exception as e:
        print(f"  ✗ Registry test error: {e}")
        results["integration"].append((False, f"Registry error: {e}"))
    
    # FINAL SUMMARY
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY / 验证总结")
    print("=" * 60)
    
    categories = {
        "Structure": results["structure"],
        "Integration": results["integration"],
        "Functionality": results["functionality"],
        "Quality": results["quality"]
    }
    
    total_pass = 0
    total_fail = 0
    
    for category, tests in categories.items():
        passed = sum(1 for success, _ in tests if success)
        failed = sum(1 for success, _ in tests if not success)
        total_pass += passed
        total_fail += failed
        
        if failed == 0:
            status = "✅ PASS"
        elif passed > failed:
            status = "⚠️  PARTIAL"
        else:
            status = "❌ FAIL"
            
        print(f"\n{category}: {status}")
        print(f"  Passed: {passed}/{len(tests)}")
        
        if failed > 0:
            print("  Issues:")
            for success, msg in tests:
                if not success:
                    print(f"    - {msg}")
    
    # OVERALL VERDICT
    print("\n" + "=" * 60)
    print("ARCHITECTURAL APPROVAL / 架构批准")
    print("=" * 60)
    
    success_rate = total_pass / (total_pass + total_fail) * 100 if (total_pass + total_fail) > 0 else 0
    
    if success_rate >= 90:
        print("✅ APPROVED: Curl plugin implementation meets architectural standards")
        print(f"   Success rate: {success_rate:.1f}%")
        print("   Ready for production use")
        return True
    elif success_rate >= 70:
        print("⚠️  CONDITIONAL APPROVAL: Minor improvements needed")
        print(f"   Success rate: {success_rate:.1f}%")
        print("   Address issues before next phase")
        return True
    else:
        print("❌ NOT APPROVED: Significant issues found")
        print(f"   Success rate: {success_rate:.1f}%")
        print("   Requires rework before proceeding")
        return False

if __name__ == "__main__":
    try:
        approved = validate_curl_plugin()
        sys.exit(0 if approved else 1)
    except KeyboardInterrupt:
        print("\nValidation interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"Validation error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)