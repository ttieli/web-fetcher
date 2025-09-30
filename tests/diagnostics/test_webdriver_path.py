#!/usr/bin/env python3
"""测试Selenium寻找ChromeDriver的路径问题"""

import os
import sys
import subprocess

print("ChromeDriver Path Diagnostic")
print("=" * 60)

# 1. 检查系统PATH
print("\n1. System PATH locations:")
path_dirs = os.environ.get('PATH', '').split(':')
for dir in path_dirs[:10]:  # 显示前10个
    print(f"   - {dir}")

# 2. 查找chromedriver
print("\n2. Finding chromedriver in PATH:")
chromedriver_found = False
for dir in path_dirs:
    chromedriver_path = os.path.join(dir, 'chromedriver')
    if os.path.exists(chromedriver_path):
        print(f"   ✓ Found: {chromedriver_path}")
        # 检查权限
        if os.access(chromedriver_path, os.X_OK):
            print(f"     - Executable: YES")
        else:
            print(f"     - Executable: NO")
        chromedriver_found = True

if not chromedriver_found:
    print("   ✗ ChromeDriver not found in PATH")

# 3. 测试which命令
print("\n3. Using 'which' command:")
try:
    result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"   ✓ Found: {result.stdout.strip()}")
    else:
        print("   ✗ Not found by 'which'")
except Exception as e:
    print(f"   ✗ Error: {e}")

# 4. 测试Selenium的Service类
print("\n4. Testing Selenium Service discovery:")
try:
    from selenium.webdriver.chrome.service import Service
    service = Service()
    print(f"   Default executable path: {service.path if hasattr(service, 'path') else 'Not accessible'}")

    # 尝试使用默认Service
    print("\n5. Attempting to use default Service...")
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_experimental_option("debuggerAddress", "localhost:9222")

    # 显式指定chromedriver路径
    service = Service('/usr/local/bin/chromedriver')
    print(f"   Using explicit path: {service.path}")

    try:
        driver = webdriver.Chrome(service=service, options=options)
        print("   ✓ Successfully connected with explicit Service!")
        driver.quit()
    except Exception as e:
        print(f"   ✗ Failed with explicit Service: {e}")

except ImportError as e:
    print(f"   ✗ Selenium import error: {e}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 60)
print("Diagnostic complete")