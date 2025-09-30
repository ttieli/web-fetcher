#!/usr/bin/env python3
"""
ChromeDriver Connection Diagnostic Test
测试ChromeDriver是否能正常连接到Chrome调试会话
"""

import sys
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def test_chrome_connection():
    """测试ChromeDriver连接到调试端口"""
    print("=" * 60)
    print("ChromeDriver Connection Test")
    print("=" * 60)

    # Step 1: 验证调试端口
    import urllib.request
    print("\n1. Testing Chrome Debug Port (9222)...")
    try:
        with urllib.request.urlopen("http://localhost:9222/json/version", timeout=2) as response:
            version_info = response.read().decode()
            print("✓ Chrome debug port is responsive")
            print(f"  Response preview: {version_info[:200]}...")
    except Exception as e:
        print(f"✗ Chrome debug port test failed: {e}")
        return False

    # Step 2: 配置ChromeDriver选项
    print("\n2. Configuring ChromeDriver options...")
    options = Options()
    options.add_experimental_option("debuggerAddress", "localhost:9222")
    print("✓ Options configured with debuggerAddress")

    # Step 3: 尝试连接
    print("\n3. Attempting ChromeDriver connection...")
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        print("✓ ChromeDriver connected successfully!")

        # Step 4: 验证连接
        print("\n4. Validating connection...")
        current_url = driver.current_url
        print(f"✓ Current URL: {current_url}")

        # Step 5: 获取浏览器版本
        version = driver.execute_script("return navigator.userAgent")
        print(f"✓ User Agent: {version}")

        return True

    except Exception as e:
        print(f"\n✗ ChromeDriver connection failed!")
        print(f"  Error type: {type(e).__name__}")
        print(f"  Error message: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False

    finally:
        if driver:
            try:
                # 不关闭浏览器，只断开连接
                driver.quit()
                print("\n✓ Driver cleaned up (browser remains open)")
            except:
                pass

if __name__ == "__main__":
    success = test_chrome_connection()
    print("\n" + "=" * 60)
    print(f"Test Result: {'SUCCESS' if success else 'FAILED'}")
    print("=" * 60)
    sys.exit(0 if success else 1)