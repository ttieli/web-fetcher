#!/usr/bin/env python3
"""
Environment checker for manual Chrome hybrid testing
检查手动Chrome混合测试的环境
"""
import subprocess
import sys
import os
import json
import socket
from datetime import datetime

def check_command(command, name):
    """Check if a command is available"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5)
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)

def check_port(port):
    """Check if a port is in use"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def check_chrome_debug():
    """Check Chrome debug port"""
    import requests
    try:
        response = requests.get('http://127.0.0.1:9222/json/version', timeout=2)
        if response.status_code == 200:
            return True, response.json()
        return False, f"Status code: {response.status_code}"
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 60)
    print("Manual Chrome Hybrid Test - Environment Check")
    print("手动Chrome混合测试 - 环境检查")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = {
        'timestamp': datetime.now().isoformat(),
        'checks': {}
    }

    # Check Python version
    print("1. Python Version / Python版本:")
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"   {py_version}")
    results['checks']['python_version'] = py_version

    # Check required Python packages
    print("\n2. Required Packages / 必需的包:")
    packages = ['selenium', 'pychrome', 'requests']

    for package in packages:
        try:
            # Try to import the package
            __import__(package)
            # Get version
            cmd = f"pip show {package} | grep Version"
            success, output = check_command(cmd, package)
            if success and output:
                version = output.split(':')[-1].strip() if ':' in output else 'unknown'
                print(f"   ✓ {package}: {version}")
                results['checks'][package] = {'installed': True, 'version': version}
            else:
                print(f"   ✓ {package}: installed (version unknown)")
                results['checks'][package] = {'installed': True, 'version': 'unknown'}
        except ImportError:
            print(f"   ✗ {package}: NOT INSTALLED")
            results['checks'][package] = {'installed': False}

    # Check if Chrome is installed
    print("\n3. Chrome Installation / Chrome安装:")
    chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]

    chrome_found = False
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"   ✓ Chrome found at: {path}")
            chrome_found = True
            results['checks']['chrome_path'] = path

            # Try to get Chrome version
            cmd = f'"{path}" --version 2>/dev/null'
            success, output = check_command(cmd, "Chrome version")
            if success:
                print(f"   ✓ Version: {output}")
                results['checks']['chrome_version'] = output
            break

    if not chrome_found:
        print("   ✗ Chrome not found in standard locations")
        results['checks']['chrome_path'] = None

    # Check ChromeDriver
    print("\n4. ChromeDriver / Chrome驱动:")
    success, output = check_command("chromedriver --version 2>/dev/null", "ChromeDriver")
    if success:
        print(f"   ✓ ChromeDriver: {output}")
        results['checks']['chromedriver'] = output
    else:
        print("   ✗ ChromeDriver not found or not in PATH")
        results['checks']['chromedriver'] = None

    # Check port 9222
    print("\n5. Port 9222 Status / 端口9222状态:")
    if check_port(9222):
        print("   ✓ Port 9222 is in use (possibly Chrome debug)")

        # Try to connect to Chrome debug
        success, data = check_chrome_debug()
        if success:
            print("   ✓ Chrome debug server is responding")
            print(f"   Browser: {data.get('Browser', 'unknown')}")
            print(f"   Protocol: {data.get('Protocol-Version', 'unknown')}")
            print(f"   V8: {data.get('V8-Version', 'unknown')}")
            results['checks']['chrome_debug'] = data
        else:
            print(f"   ⚠ Port is in use but not Chrome debug: {data}")
            results['checks']['chrome_debug'] = None
    else:
        print("   ⚠ Port 9222 is NOT in use")
        print("   You need to start Chrome with: --remote-debugging-port=9222")
        results['checks']['chrome_debug'] = None

    # Check for existing Chrome processes
    print("\n6. Chrome Processes / Chrome进程:")
    cmd = "ps aux | grep -i 'chrome.*remote-debugging' | grep -v grep"
    success, output = check_command(cmd, "Chrome debug processes")
    if success and output:
        lines = output.split('\n')
        print(f"   ✓ Found {len(lines)} Chrome debug process(es)")
        for line in lines[:2]:  # Show first 2 processes
            print(f"      {line[:100]}...")
    else:
        print("   ⚠ No Chrome debug processes found")

    # Generate launch command
    print("\n" + "=" * 60)
    print("SETUP INSTRUCTIONS / 设置说明")
    print("=" * 60)

    if not results['checks'].get('chrome_debug'):
        print("\n⚠ Chrome debug server is NOT running!")
        print("⚠ Chrome调试服务器未运行！\n")
        print("Start Chrome with this command / 使用此命令启动Chrome:")
        print("-" * 60)

        if chrome_found:
            chrome_path = results['checks']['chrome_path']
            print(f'"{chrome_path}" \\')
        else:
            print('/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\')

        print('  --remote-debugging-port=9222 \\')
        print('  --user-data-dir=/tmp/chrome-manual-test \\')
        print('  --no-first-run \\')
        print('  --disable-extensions')
        print("-" * 60)
    else:
        print("\n✓ Chrome debug server is already running!")
        print("✓ Chrome调试服务器已在运行！")
        print("\nYou can now:")
        print("1. Manually navigate to your target URL in that Chrome")
        print("2. Run the test scripts")

    # Check for missing packages
    missing_packages = [p for p in packages if not results['checks'][p]['installed']]
    if missing_packages:
        print("\n" + "=" * 60)
        print("MISSING PACKAGES / 缺少的包")
        print("=" * 60)
        print("\nInstall missing packages with / 使用以下命令安装缺少的包:")
        print(f"pip install {' '.join(missing_packages)}")

    # Save results
    results_file = 'test_artifacts/env_check_results.json'
    os.makedirs('test_artifacts', exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 60)
    print("Environment check complete!")
    print(f"Results saved to: {results_file}")
    print("=" * 60)

    # Return status
    all_good = (
        results['checks'].get('selenium', {}).get('installed', False) and
        results['checks'].get('pychrome', {}).get('installed', False) and
        chrome_found
    )

    if all_good:
        print("\n✅ Environment is ready for testing!")
        print("✅ 环境已准备好进行测试！")
        return 0
    else:
        print("\n⚠️ Some requirements are missing. Please fix them first.")
        print("⚠️ 缺少一些要求。请先修复它们。")
        return 1

if __name__ == '__main__':
    sys.exit(main())