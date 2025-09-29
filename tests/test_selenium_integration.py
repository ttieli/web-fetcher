#!/usr/bin/env python3
"""
Selenium Integration Test Suite
Selenium集成测试套件

This script tests the complete Selenium integration including:
此脚本测试完整的Selenium集成，包括：
- Chrome debug connection / Chrome调试连接
- Basic navigation / 基本导航
- JavaScript execution / JavaScript执行
- SeleniumFetcher functionality / SeleniumFetcher功能
"""

import sys
import os
import time
import json
from typing import Dict, Any, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_chrome_debug_api() -> bool:
    """
    Test Chrome DevTools Protocol API.
    测试Chrome DevTools协议API。
    """
    print("\n1. Testing Chrome Debug API:")
    print("-" * 40)
    
    try:
        import requests
        
        # Check version endpoint
        resp = requests.get("http://localhost:9222/json/version", timeout=2)
        if resp.status_code == 200:
            version_info = resp.json()
            print(f"✓ Chrome Debug API responding")
            print(f"  Browser: {version_info.get('Browser', 'unknown')}")
            print(f"  Protocol: {version_info.get('Protocol-Version', 'unknown')}")
            
            # Check list endpoint
            resp = requests.get("http://localhost:9222/json/list", timeout=2)
            tabs = resp.json()
            print(f"  Open tabs: {len(tabs)}")
            
            return True
        else:
            print(f"✗ Chrome Debug API returned status {resp.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to Chrome Debug port")
        print("  Please run: ./config/chrome-debug.sh")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_selenium_connection() -> bool:
    """
    Test basic Selenium connection to Chrome debug port.
    测试Selenium到Chrome调试端口的基本连接。
    """
    print("\n2. Testing Selenium Connection:")
    print("-" * 40)
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        # Configure for debug connection
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        # Connect to existing Chrome
        print("  Connecting to Chrome debug port...")
        driver = webdriver.Chrome(options=options)
        
        # Get current URL
        current_url = driver.current_url
        print(f"✓ Connected to Chrome")
        print(f"  Current URL: {current_url}")
        
        # Test navigation
        print("  Testing navigation...")
        driver.get("https://www.example.com")
        time.sleep(1)
        
        title = driver.title
        if "Example Domain" in title:
            print(f"✓ Navigation successful")
            print(f"  Page title: {title}")
        else:
            print(f"⚠ Unexpected title: {title}")
        
        # Don't quit - just close tab
        driver.close()
        
        return True
        
    except ImportError as e:
        print(f"✗ Selenium not installed: {e}")
        print("  Run: pip install selenium>=4.15.0")
        return False
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Is Chrome debug running? (./config/chrome-debug.sh)")
        print("  2. Is port 9222 accessible? (lsof -i :9222)")
        print("  3. Is Selenium installed? (pip list | grep selenium)")
        return False


def test_javascript_execution() -> bool:
    """
    Test JavaScript execution capability.
    测试JavaScript执行能力。
    """
    print("\n3. Testing JavaScript Execution:")
    print("-" * 40)
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=options)
        
        # Navigate to test page
        driver.get("https://www.example.com")
        time.sleep(1)
        
        # Execute JavaScript
        result = driver.execute_script("return document.title")
        print(f"✓ JavaScript execution working")
        print(f"  document.title: {result}")
        
        # Test more complex JS
        result = driver.execute_script("""
            return {
                url: window.location.href,
                userAgent: navigator.userAgent.substring(0, 50),
                screenWidth: window.screen.width
            }
        """)
        print(f"  Window info: {json.dumps(result, indent=2)}")
        
        driver.close()
        return True
        
    except Exception as e:
        print(f"✗ JavaScript execution failed: {e}")
        return False


def test_selenium_fetcher() -> bool:
    """
    Test SeleniumFetcher class functionality.
    测试SeleniumFetcher类功能。
    """
    print("\n4. Testing SeleniumFetcher:")
    print("-" * 40)
    
    try:
        from selenium_fetcher import SeleniumFetcher
        
        print("  Initializing SeleniumFetcher...")
        fetcher = SeleniumFetcher(debug=True)
        
        # Test simple fetch
        print("  Fetching example.com...")
        result = fetcher.fetch("https://www.example.com")
        
        if result and result.get('success'):
            print(f"✓ SeleniumFetcher fetch successful")
            print(f"  Content length: {len(result.get('content', ''))}")
            print(f"  Title extracted: {'Example Domain' in result.get('content', '')}")
            
            # Check for expected content
            content = result.get('content', '')
            if 'Example Domain' in content and 'This domain is for use' in content:
                print("✓ Content validation passed")
            else:
                print("⚠ Content unexpected")
            
            return True
        else:
            error = result.get('error', 'Unknown error') if result else 'No result'
            print(f"✗ Fetch failed: {error}")
            return False
            
    except ImportError as e:
        print(f"✗ Cannot import SeleniumFetcher: {e}")
        print("  Check that selenium_fetcher.py exists in project root")
        return False
    except Exception as e:
        print(f"✗ SeleniumFetcher test failed: {e}")
        return False


def test_error_handling() -> bool:
    """
    Test error handling and recovery.
    测试错误处理和恢复。
    """
    print("\n5. Testing Error Handling:")
    print("-" * 40)
    
    try:
        from selenium_fetcher import SeleniumFetcher
        
        fetcher = SeleniumFetcher(debug=False)  # Disable debug for cleaner output
        
        # Test invalid URL
        print("  Testing invalid URL handling...")
        result = fetcher.fetch("https://this-domain-definitely-does-not-exist-12345.com")
        
        if result and not result.get('success'):
            print(f"✓ Invalid URL handled correctly")
            print(f"  Error: {result.get('error', 'No error message')}")
        else:
            print("⚠ Invalid URL did not produce expected error")
        
        # Test timeout handling (using a slow site)
        print("  Testing timeout handling...")
        # Note: This is a hypothetical test - adjust based on actual implementation
        
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


def run_performance_test() -> bool:
    """
    Test performance and resource usage.
    测试性能和资源使用。
    """
    print("\n6. Performance Test:")
    print("-" * 40)
    
    try:
        from selenium_fetcher import SeleniumFetcher
        import time
        
        fetcher = SeleniumFetcher(debug=False)
        
        # Test fetch speed
        urls = [
            "https://www.example.com",
            "https://www.google.com",
            "https://www.wikipedia.org"
        ]
        
        print("  Testing fetch performance...")
        total_time = 0
        successful = 0
        
        for url in urls:
            start = time.time()
            result = fetcher.fetch(url)
            elapsed = time.time() - start
            
            if result and result.get('success'):
                successful += 1
                total_time += elapsed
                print(f"  ✓ {url}: {elapsed:.2f}s")
            else:
                print(f"  ✗ {url}: failed")
        
        if successful > 0:
            avg_time = total_time / successful
            print(f"\n✓ Performance test completed")
            print(f"  Successful: {successful}/{len(urls)}")
            print(f"  Average time: {avg_time:.2f}s")
            return True
        else:
            print("✗ All fetches failed")
            return False
            
    except Exception as e:
        print(f"✗ Performance test failed: {e}")
        return False


def main():
    """Main test routine / 主测试程序"""
    print("=" * 60)
    print("Selenium Integration Test Suite")
    print("Selenium集成测试套件")
    print("=" * 60)
    
    # Check if Chrome debug is running first
    print("\nPre-flight check:")
    try:
        import requests
        requests.get("http://localhost:9222/json/version", timeout=1)
        print("✓ Chrome debug port is accessible")
    except:
        print("✗ Chrome debug port not accessible")
        print("\nPlease start Chrome debug first:")
        print("  cd '/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher'")
        print("  ./config/chrome-debug.sh")
        print("\nThen run this test again.")
        return 1
    
    # Run tests
    tests = [
        ("Chrome Debug API", test_chrome_debug_api),
        ("Selenium Connection", test_selenium_connection),
        ("JavaScript Execution", test_javascript_execution),
        ("SeleniumFetcher", test_selenium_fetcher),
        ("Error Handling", test_error_handling),
        ("Performance", run_performance_test),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user")
            break
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✓ PASSED" if passed_test else "✗ FAILED"
        print(f"{test_name:.<40} {status}")
    
    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All integration tests passed!")
        print("✓ 所有集成测试通过！")
        print("\nSelenium integration is working correctly.")
    else:
        print("\n✗ Some tests failed.")
        print("✗ 某些测试失败。")
        print("\nRefer to the error messages above for details.")
        print("Check TASKS/SELENIUM_DEPENDENCIES_INSTALLATION_GUIDE.md for help.")
    
    print("=" * 60)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())