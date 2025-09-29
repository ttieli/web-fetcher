#!/usr/bin/env python3
"""
Selenium Installation Verification Script
Selenium安装验证脚本

This script verifies that all Selenium dependencies are correctly installed.
此脚本验证所有Selenium依赖是否正确安装。
"""

import sys
import importlib
from typing import Tuple, Optional

def check_package(package_name: str, min_version: Optional[str] = None) -> bool:
    """
    Check if a package is installed and meets version requirements.
    检查包是否已安装并满足版本要求。
    
    Args:
        package_name: Name of the package to check / 要检查的包名
        min_version: Minimum required version / 最低要求版本
    
    Returns:
        True if package is installed and meets requirements / 如果包已安装并满足要求则返回True
    """
    try:
        # Special handling for PyYAML (imports as yaml)
        import_name = 'yaml' if package_name == 'pyyaml' else package_name
        module = importlib.import_module(import_name)
        
        # Get version
        if import_name == 'yaml':
            import yaml
            version = yaml.__version__ if hasattr(yaml, '__version__') else 'unknown'
        else:
            version = getattr(module, '__version__', 'unknown')
        
        print(f"✓ {package_name} {version} installed")
        
        # Check version if specified
        if min_version and version != 'unknown':
            try:
                from packaging import version as v
                if v.parse(version) >= v.parse(min_version):
                    print(f"  Version check passed (>= {min_version})")
                else:
                    print(f"  ⚠ Version too old (need >= {min_version})")
                    return False
            except ImportError:
                # packaging not installed, skip version check
                print(f"  Version: {version} (min required: {min_version})")
        
        return True
        
    except ImportError:
        print(f"✗ {package_name} NOT installed")
        return False
    except Exception as e:
        print(f"✗ Error checking {package_name}: {e}")
        return False


def check_chrome_debug() -> bool:
    """
    Check if Chrome debug port is accessible.
    检查Chrome调试端口是否可访问。
    
    Returns:
        True if Chrome debug port is responding / 如果Chrome调试端口响应则返回True
    """
    try:
        import requests
        resp = requests.get("http://localhost:9222/json/version", timeout=2)
        if resp.status_code == 200:
            print("✓ Chrome debug port (9222) is accessible")
            return True
        else:
            print(f"✗ Chrome debug port returned status {resp.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Chrome debug port (9222) is not accessible")
        print("  Run: ./config/chrome-debug.sh")
        return False
    except requests.exceptions.Timeout:
        print("✗ Chrome debug port (9222) timed out")
        return False
    except ImportError:
        print("⚠ requests library not installed, skipping Chrome debug check")
        return True  # Don't fail if requests not installed
    except Exception as e:
        print(f"✗ Error checking Chrome debug port: {e}")
        return False


def check_selenium_import() -> bool:
    """
    Test importing Selenium components.
    测试导入Selenium组件。
    
    Returns:
        True if all imports succeed / 如果所有导入成功则返回True
    """
    imports_to_test = [
        ("selenium.webdriver", "WebDriver base"),
        ("selenium.webdriver.chrome.options", "Chrome options"),
        ("selenium.webdriver.common.by", "Locator strategies"),
        ("selenium.webdriver.support.wait", "Wait utilities"),
    ]
    
    all_ok = True
    print("\nTesting Selenium imports:")
    
    for module_path, description in imports_to_test:
        try:
            importlib.import_module(module_path)
            print(f"  ✓ {description} ({module_path})")
        except ImportError as e:
            print(f"  ✗ {description} ({module_path}): {e}")
            all_ok = False
    
    return all_ok


def check_project_structure() -> bool:
    """
    Check if project files are accessible.
    检查项目文件是否可访问。
    
    Returns:
        True if project structure is correct / 如果项目结构正确则返回True
    """
    import os
    
    project_root = "/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher"
    
    required_files = [
        "selenium_fetcher.py",
        "requirements-selenium.txt",
        "config/chrome-debug.sh",
        "config/selenium_defaults.yaml",
    ]
    
    print("\nChecking project structure:")
    all_ok = True
    
    for file_path in required_files:
        full_path = os.path.join(project_root, file_path)
        if os.path.exists(full_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} not found")
            all_ok = False
    
    return all_ok


def main():
    """Main verification routine / 主验证程序"""
    print("=" * 60)
    print("Selenium Dependencies Verification")
    print("Selenium依赖验证")
    print("=" * 60)
    
    # Track overall status
    all_checks_passed = True
    
    # 1. Check Python version
    print(f"\nPython version: {sys.version}")
    if sys.version_info < (3, 7):
        print("✗ Python 3.7+ required")
        all_checks_passed = False
    else:
        print("✓ Python version OK")
    
    # 2. Check required packages
    print("\nChecking required packages:")
    packages = [
        ('selenium', '4.15.0'),
        ('pyyaml', '6.0.0'),
        ('lxml', '4.9.0')
    ]
    
    for pkg, min_ver in packages:
        if not check_package(pkg, min_ver):
            all_checks_passed = False
    
    # 3. Test Selenium imports
    if not check_selenium_import():
        all_checks_passed = False
    
    # 4. Check project structure
    if not check_project_structure():
        all_checks_passed = False
    
    # 5. Check Chrome debug port
    print("\nChecking Chrome debug connection:")
    check_chrome_debug()  # Don't fail overall if Chrome not running
    
    # 6. Try importing SeleniumFetcher
    print("\nTesting SeleniumFetcher import:")
    try:
        # Add project root to path
        import os
        project_root = "/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher"
        if os.path.exists(project_root):
            sys.path.insert(0, project_root)
            from selenium_fetcher import SeleniumFetcher
            print("✓ SeleniumFetcher imports successfully")
        else:
            print("✗ Project directory not found")
            all_checks_passed = False
    except ImportError as e:
        print(f"✗ SeleniumFetcher import failed: {e}")
        all_checks_passed = False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        all_checks_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_checks_passed:
        print("✓ All Selenium dependencies verified successfully!")
        print("✓ 所有Selenium依赖验证成功！")
        print("\nNext steps / 下一步:")
        print("1. Start Chrome debug: ./config/chrome-debug.sh")
        print("2. Run integration tests: python tests/test_selenium_integration.py")
    else:
        print("✗ Some dependencies missing or misconfigured.")
        print("✗ 某些依赖缺失或配置错误。")
        print("\nTo fix / 修复方法:")
        print("1. Install missing packages / 安装缺失的包:")
        print("   pip install -r requirements-selenium.txt")
        print("2. Check the installation guide / 查看安装指南:")
        print("   TASKS/SELENIUM_DEPENDENCIES_INSTALLATION_GUIDE.md")
    
    print("=" * 60)
    
    return 0 if all_checks_passed else 1


if __name__ == "__main__":
    sys.exit(main())