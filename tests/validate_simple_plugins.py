#!/usr/bin/env python3
"""
Simple validation script for personal tool plugin architecture.
简化版个人工具插件架构验证脚本。

This script validates the simplified plugin implementation without 
enterprise features like sandboxing, complex monitoring, etc.
"""

import os
import sys
import subprocess
from pathlib import Path
import platform

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_environment():
    """Check basic environment setup"""
    """检查基础环境设置"""
    
    print("Environment Check / 环境检查")
    print("=" * 50)
    
    checks = []
    
    # Check Python version
    python_version = sys.version_info
    checks.append((
        "Python 3.6+",
        python_version >= (3, 6),
        f"Python {python_version.major}.{python_version.minor}"
    ))
    
    # Check curl availability
    try:
        result = subprocess.run(['curl', '--version'], 
                              capture_output=True, timeout=5)
        curl_available = result.returncode == 0
    except:
        curl_available = False
    checks.append(("curl installed", curl_available, "curl"))
    
    # Check platform for Safari
    is_macos = platform.system() == 'Darwin'
    checks.append(("macOS (for Safari)", is_macos, platform.system()))
    
    # Check project structure
    plugin_dir = project_root / 'plugins'
    checks.append(("plugins/ directory", plugin_dir.exists(), str(plugin_dir)))
    
    # Print results
    for name, result, info in checks:
        status = "✓" if result else "✗"
        print(f"  {status} {name}: {info}")
    
    print()
    return all(result for _, result, _ in checks)


def validate_simple_plugin_structure():
    """Validate simplified plugin structure"""
    """验证简化的插件结构"""
    
    print("Plugin Structure Validation / 插件结构验证")
    print("=" * 50)
    
    validations = []
    
    # Check for base plugin
    base_file = project_root / 'plugins' / 'base.py'
    if base_file.exists():
        with open(base_file, 'r') as f:
            content = f.read()
            # Check for minimal interface
            has_simple = 'SimplePlugin' in content or 'IFetcherPlugin' in content
            validations.append(("Base plugin interface", has_simple))
    else:
        validations.append(("Base plugin file", False))
    
    # Check for NO complex features (this is good!)
    no_yaml = not (project_root / 'config' / 'plugins.yml').exists()
    validations.append(("No YAML config (good!)", no_yaml))
    
    no_sandbox = True  # We don't want sandboxing
    sandbox_file = project_root / 'plugins' / 'sandbox.py'
    if sandbox_file.exists():
        no_sandbox = False
    validations.append(("No sandbox complexity (good!)", no_sandbox))
    
    # Check for actual plugin implementations
    curl_exists = (project_root / 'plugins' / 'curl_plugin.py').exists() or \
                 (project_root / 'plugins' / 'curl.py').exists()
    validations.append(("Curl plugin exists", curl_exists))
    
    # Print results
    for name, result in validations:
        status = "✓" if result else "✗"
        print(f"  {status} {name}")
    
    print()
    return all(result for _, result in validations)


def test_simple_curl_plugin():
    """Test simplified curl plugin if it exists"""
    """测试简化的curl插件（如果存在）"""
    
    print("Curl Plugin Test / Curl插件测试")
    print("=" * 50)
    
    # Try to import and test curl plugin
    try:
        # Check multiple possible locations
        curl_imported = False
        
        # Try plugins.curl_plugin
        try:
            from plugins.curl_plugin import CurlPlugin
            curl_imported = True
            plugin = CurlPlugin()
        except ImportError:
            pass
        
        # Try plugins.curl
        if not curl_imported:
            try:
                from plugins.curl import CurlPlugin
                curl_imported = True
                plugin = CurlPlugin()
            except ImportError:
                pass
        
        if not curl_imported:
            print("  ✗ Curl plugin not found (expected during migration)")
            return False
        
        print("  ✓ Curl plugin imported successfully")
        
        # Test basic functionality
        test_url = 'https://httpbin.org/html'
        print(f"  Testing fetch of {test_url}")
        
        if hasattr(plugin, 'fetch'):
            success, content, error = plugin.fetch(test_url, timeout=10)
            
            if success and content:
                print(f"  ✓ Fetch successful ({len(content)} bytes)")
                return True
            else:
                print(f"  ✗ Fetch failed: {error}")
                return False
        else:
            print("  ✗ Plugin missing fetch method")
            return False
            
    except Exception as e:
        print(f"  ✗ Error testing curl plugin: {e}")
        return False


def check_webfetcher_integration():
    """Check if webfetcher.py has plugin integration"""
    """检查webfetcher.py是否有插件集成"""
    
    print("\nWebfetcher Integration / Webfetcher集成")
    print("=" * 50)
    
    webfetcher_file = project_root / 'webfetcher.py'
    
    if not webfetcher_file.exists():
        print("  ✗ webfetcher.py not found")
        return False
    
    with open(webfetcher_file, 'r') as f:
        content = f.read()
    
    checks = []
    
    # Check for plugin imports (new or existing)
    has_plugin_import = ('from plugins' in content or 
                        'import plugins' in content or
                        'PluginRegistry' in content)
    checks.append(("Plugin imports", has_plugin_import))
    
    # Check if urllib is still core (not a plugin)
    has_urllib = 'urllib.request' in content or 'urlopen' in content
    checks.append(("urllib still core (good!)", has_urllib))
    
    # Check for simple fallback logic
    has_fallback = ('curl' in content.lower() and 'ssl' in content.lower())
    checks.append(("SSL fallback logic", has_fallback))
    
    # Print results
    for name, result in checks:
        status = "✓" if result else "✗"
        print(f"  {status} {name}")
    
    return all(result for _, result in checks)


def create_example_curl_plugin():
    """Create example curl plugin implementation"""
    """创建示例curl插件实现"""
    
    print("\nExample Curl Plugin / 示例Curl插件")
    print("=" * 50)
    
    example_code = '''"""Simple curl plugin for SSL fallback - NO COMPLEXITY!"""
import subprocess
import logging

class CurlPlugin:
    """Dead simple curl plugin"""
    
    def __init__(self):
        self.name = 'curl'
        self.enabled = True
    
    def can_fetch(self, url):
        """Can handle any HTTP/HTTPS URL"""
        return url.startswith(('http://', 'https://'))
    
    def fetch(self, url, timeout=30):
        """Simple curl fetch with SSL bypass"""
        try:
            cmd = [
                'curl', '-L',           # Follow redirects
                '--insecure',          # Bypass SSL (for GitHub raw etc)
                '--max-time', str(timeout),
                '--compressed',        # Accept compression
                '--silent',           # No progress bar
                url
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout + 5  # Buffer for curl timeout
            )
            
            if result.returncode == 0:
                return True, result.stdout, None
            else:
                return False, None, f"Curl failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, None, f"Timeout after {timeout}s"
        except Exception as e:
            return False, None, str(e)

# That's it! No more complexity needed for personal use.
'''
    
    print("Example curl plugin code (save to plugins/curl_plugin.py):")
    print("-" * 50)
    print(example_code)
    print("-" * 50)


def main():
    """Run all validation checks"""
    """运行所有验证检查"""
    
    print("\n" + "=" * 60)
    print("Web Fetcher Simple Plugin Validation")
    print("个人工具插件架构验证")
    print("=" * 60 + "\n")
    
    # Run checks
    env_ok = check_environment()
    
    if not env_ok:
        print("\n⚠️  Fix environment issues first")
        sys.exit(1)
    
    structure_ok = validate_simple_plugin_structure()
    integration_ok = check_webfetcher_integration()
    
    # Try to test curl if it exists
    curl_ok = test_simple_curl_plugin()
    
    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary / 验证摘要")
    print("=" * 60)
    
    if structure_ok and integration_ok:
        print("\n✅ Plugin structure looks good for personal use!")
        print("   插件结构适合个人使用！")
    elif not structure_ok:
        print("\n📝 Plugin structure not yet implemented")
        print("   插件结构尚未实施")
        print("\n   Next steps / 下一步:")
        print("   1. Create plugins/ directory")
        print("   2. Add simple base.py with minimal interface")
        print("   3. Implement curl_plugin.py (see example below)")
    else:
        print("\n⚠️  Partial implementation detected")
        print("   检测到部分实施")
    
    if not curl_ok:
        print("\n💡 Curl plugin not working yet. Example implementation:")
        print("   Curl插件尚未工作。示例实现：")
        create_example_curl_plugin()
    
    print("\nRemember: This is YOUR tool - keep it simple! 🚀")
    print("记住：这是你的工具 - 保持简单！\n")


if __name__ == '__main__':
    main()