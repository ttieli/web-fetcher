#!/usr/bin/env python3
"""仅测试导入和基本操作"""

import sys
import time

print("Step 1: Import selenium")
from selenium import webdriver
print("✓ Selenium imported")

print("\nStep 2: Import Options")
from selenium.webdriver.chrome.options import Options
print("✓ Options imported")

print("\nStep 3: Import Service")
from selenium.webdriver.chrome.service import Service
print("✓ Service imported")

print("\nStep 4: Create Options object")
options = Options()
print("✓ Options object created")

print("\nStep 5: Add debuggerAddress")
options.add_experimental_option("debuggerAddress", "localhost:9222")
print("✓ debuggerAddress added")

print("\nStep 6: Create Service with explicit path")
service = Service('/usr/local/bin/chromedriver')
print(f"✓ Service created with path: {service.path}")

print("\nStep 7: Attempting webdriver.Chrome()...")
print("(This may hang if there's a connection issue)")
sys.stdout.flush()

start = time.time()
try:
    # 这里可能会挂起
    driver = webdriver.Chrome(service=service, options=options)
    elapsed = time.time() - start
    print(f"✓ Driver created in {elapsed:.2f} seconds")
    driver.quit()
    print("✓ Driver quit successfully")
except Exception as e:
    elapsed = time.time() - start
    print(f"✗ Failed after {elapsed:.2f} seconds: {e}")
    import traceback
    traceback.print_exc()