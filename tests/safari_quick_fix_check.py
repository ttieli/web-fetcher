#!/usr/bin/env python3
"""
Quick diagnostic script to identify exact issues needing fixes
for Safari plugin integration completion.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_priority_enum():
    """Check FetchPriority enum values."""
    print("\n1. Checking FetchPriority Enum:")
    print("-" * 40)
    
    try:
        from plugins.base import FetchPriority
        
        # Check available attributes
        attrs = [attr for attr in dir(FetchPriority) if not attr.startswith('_')]
        print(f"Available FetchPriority values: {attrs}")
        
        # Check for MEDIUM
        has_medium = hasattr(FetchPriority, 'MEDIUM')
        print(f"Has MEDIUM: {has_medium}")
        
        # Show actual values
        for attr in attrs:
            if hasattr(FetchPriority, attr):
                value = getattr(FetchPriority, attr)
                if isinstance(value, int):
                    print(f"  {attr} = {value}")
        
        return not has_medium  # Return True if fix needed
        
    except Exception as e:
        print(f"ERROR: {e}")
        return True

def check_curl_plugin():
    """Check curl plugin registration."""
    print("\n2. Checking Curl Plugin:")
    print("-" * 40)
    
    try:
        # Check if curl.py exists
        curl_path = "plugins/curl.py"
        if not os.path.exists(curl_path):
            print(f"ERROR: {curl_path} not found!")
            return True
        
        # Try to import curl plugin
        from plugins.curl import CurlFetcherPlugin
        print("✓ Curl plugin can be imported")
        
        # Check plugin name
        plugin = CurlFetcherPlugin()
        print(f"Plugin name: {plugin.name}")
        expected_name = "curl_fetcher"
        
        if plugin.name != expected_name:
            print(f"ERROR: Name mismatch! Expected '{expected_name}', got '{plugin.name}'")
            return True
        
        # Check if available
        is_available = plugin.is_available()
        print(f"Curl available: {is_available}")
        
        # Check priority
        print(f"Curl priority: {plugin.priority}")
        
        return False  # No fix needed if we get here
        
    except Exception as e:
        print(f"ERROR importing curl plugin: {e}")
        return True

def check_plugin_registry():
    """Check plugin registry state."""
    print("\n3. Checking Plugin Registry:")
    print("-" * 40)
    
    try:
        from plugins import get_global_registry
        
        registry = get_global_registry()
        plugins = registry.list_plugins()
        
        print(f"Registered plugins: {plugins}")
        
        # Check for expected plugins
        expected = ['http_fetcher', 'curl_fetcher', 'safari_fetcher']
        missing = [p for p in expected if p not in plugins]
        
        if missing:
            print(f"Missing plugins: {missing}")
            return True
        
        # Show plugin details
        plugin_info = registry.get_plugin_info()
        for name, info in plugin_info.items():
            print(f"\n{name}:")
            print(f"  Priority: {info.get('priority')}")
            print(f"  Available: {info.get('available')}")
            print(f"  Capabilities: {info.get('capabilities')}")
        
        return False
        
    except Exception as e:
        print(f"ERROR: {e}")
        return True

def check_safari_extractor():
    """Check Safari extractor module."""
    print("\n4. Checking Safari Extractor:")
    print("-" * 40)
    
    try:
        from plugins.safari.extractor import should_fallback_to_safari, extract_with_safari_fallback
        print("✓ Safari extractor functions available")
        
        # Check if running on macOS
        import platform
        is_macos = platform.system() == "Darwin"
        print(f"Running on macOS: {is_macos}")
        
        return False
        
    except ImportError as e:
        print(f"ERROR: Safari extractor not available: {e}")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return True

def main():
    """Run all diagnostic checks."""
    print("=" * 60)
    print("Safari Integration Quick Diagnostic")
    print("=" * 60)
    
    issues = []
    
    # Run checks
    if check_priority_enum():
        issues.append("FetchPriority enum needs MEDIUM value")
    
    if check_curl_plugin():
        issues.append("Curl plugin needs fixing")
    
    if check_plugin_registry():
        issues.append("Plugin registry has missing plugins")
    
    if check_safari_extractor():
        issues.append("Safari extractor module issues")
    
    # Summary
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    if issues:
        print("\n⚠️  Issues Found:")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")
        
        print("\n📋 Required Fixes:")
        
        if "FetchPriority enum needs MEDIUM value" in issues:
            print("\n1. In plugins/base.py, add:")
            print("   MEDIUM = 50  # Add this line to FetchPriority enum")
        
        if "Curl plugin needs fixing" in issues:
            print("\n2. In plugins/curl.py:")
            print("   - Change plugin name from 'curl' to 'curl_fetcher'")
            print("   - Change FetchPriority.FALLBACK to FetchPriority.LOW")
    else:
        print("\n✅ All checks passed! Safari integration is ready.")
    
    return len(issues)

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)