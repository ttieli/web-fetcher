#!/usr/bin/env python3
"""最小化ChromeDriver测试 - 带超时控制"""

import sys
import time
import signal

def timeout_handler(signum, frame):
    print("\n✗ Test timed out after 10 seconds!")
    sys.exit(1)

# 设置10秒超时
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(10)

print("Starting minimal ChromeDriver test...")
print("-" * 40)

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    print("✓ Selenium imported successfully")

    # 测试基本连接
    options = Options()
    options.add_experimental_option("debuggerAddress", "localhost:9222")
    print("✓ Options configured")

    print("Attempting to create Chrome driver...")
    start = time.time()

    driver = webdriver.Chrome(options=options)

    elapsed = time.time() - start
    print(f"✓ Driver created in {elapsed:.2f} seconds")

    driver.quit()
    print("✓ Driver quit successfully")

except Exception as e:
    print(f"✗ Test failed: {e}")
    sys.exit(1)
finally:
    signal.alarm(0)  # 取消定时器

print("-" * 40)
print("Test completed successfully!")