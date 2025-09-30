#!/usr/bin/env python3
"""测试不使用Service的连接方式"""

import signal
import sys

def timeout_handler(signum, frame):
    print("\n✗ Timed out!")
    sys.exit(1)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(10)

print("Test WITHOUT Service (as in original code)")
print("-" * 40)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

print("1. Creating Options...")
options = Options()
options.add_experimental_option("debuggerAddress", "localhost:9222")

print("2. Creating driver WITHOUT service...")
try:
    # 完全按照原代码的方式
    driver = webdriver.Chrome(options=options)
    print("✓ Success! Driver created")
    print(f"   Current URL: {driver.current_url}")
    driver.quit()
except Exception as e:
    print(f"✗ Failed: {e}")
finally:
    signal.alarm(0)