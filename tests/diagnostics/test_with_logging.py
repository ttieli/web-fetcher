#!/usr/bin/env python3
"""使用详细日志测试ChromeDriver"""

import sys
import os
import signal

def timeout_handler(signum, frame):
    print("\n✗ Timed out after 15 seconds")
    sys.exit(1)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(15)

print("ChromeDriver Detailed Test with Logging")
print("=" * 60)

# 启用Selenium日志
import logging
logging.basicConfig(level=logging.DEBUG)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# 创建日志文件路径
log_path = "/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher/tests/diagnostics/chromedriver.log"

print(f"\n1. Setting up Service with logging to: {log_path}")
service = Service(
    '/usr/local/bin/chromedriver',
    log_path=log_path
)

print("\n2. Setting up Options")
options = Options()
options.add_experimental_option("debuggerAddress", "localhost:9222")
# 添加更多日志选项
options.add_argument("--verbose")
options.add_argument("--log-level=0")

print("\n3. Attempting to create driver...")
try:
    driver = webdriver.Chrome(service=service, options=options)
    print("✓ Driver created successfully!")
    driver.quit()
except Exception as e:
    print(f"✗ Failed: {e}")
    # 尝试读取日志
    if os.path.exists(log_path):
        print(f"\nChromeDriver log contents:")
        with open(log_path, 'r') as f:
            print(f.read())
finally:
    signal.alarm(0)