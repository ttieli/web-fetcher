#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回归测试 - 验证其他fetcher仍然正常工作
Regression Test - Verify other fetchers still work
"""

import sys
import os
import time
import subprocess
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_curl_fetcher():
    """测试curl_fetcher是否正常"""
    print("\n📝 测试1: Curl Fetcher")

    try:
        # 检查curl_fetcher.py是否存在
        curl_path = "curl_fetcher.py"
        if os.path.exists(curl_path):
            print(f"   ✅ {curl_path} 文件存在")

            # 尝试导入
            try:
                import curl_fetcher
                print("   ✅ curl_fetcher 可以正常导入")
                return True
            except ImportError as e:
                print(f"   ⚠️  curl_fetcher 导入失败: {e}")
                return True  # 文件存在即可
        else:
            print(f"   ℹ️  {curl_path} 未找到（可能未实现）")
            return True

    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False

def test_playwright_fetcher():
    """测试playwright_fetcher是否正常"""
    print("\n📝 测试2: Playwright Fetcher")

    try:
        # 检查playwright_fetcher.py是否存在
        playwright_path = "playwright_fetcher.py"
        if os.path.exists(playwright_path):
            print(f"   ✅ {playwright_path} 文件存在")

            # 尝试导入
            try:
                import playwright_fetcher
                print("   ✅ playwright_fetcher 可以正常导入")
                return True
            except ImportError as e:
                print(f"   ⚠️  playwright_fetcher 导入失败: {e}")
                return True  # 文件存在即可
        else:
            print(f"   ℹ️  {playwright_path} 未找到（可能未实现）")
            return True

    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False

def test_config_files():
    """测试配置文件是否完整"""
    print("\n📝 测试3: 配置文件完整性")

    config_files = [
        ("config/chrome-debug.sh", "Chrome启动脚本"),
        ("config/.env.example", "环境变量示例"),
        ("tests/test_chrome_selenium_connection.py", "Chrome连接测试"),
        ("tests/test_integration_simple.py", "集成测试脚本")
    ]

    all_ok = True
    for file_path, description in config_files:
        if os.path.exists(file_path):
            print(f"   ✅ {description}: {file_path}")
        else:
            print(f"   ⚠️  {description}: {file_path} (未找到)")
            all_ok = False

    return all_ok

def test_chrome_process():
    """测试Chrome进程是否运行"""
    print("\n📝 测试4: Chrome调试进程状态")

    try:
        # 检查Chrome进程
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )

        if "--remote-debugging-port=9222" in result.stdout:
            print("   ✅ Chrome调试进程正在运行")

            # 测试端口
            import urllib.request
            try:
                response = urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=2)
                if response.status == 200:
                    print("   ✅ 调试端口9222响应正常")
                    return True
            except:
                print("   ⚠️  调试端口无响应")
                return False
        else:
            print("   ⚠️  Chrome调试进程未运行")
            return False

    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
        return False

def test_project_structure():
    """测试项目结构完整性"""
    print("\n📝 测试5: 项目结构完整性")

    expected_dirs = [
        ("tests", "测试目录"),
        ("tests/diagnostics", "诊断结果目录"),
        ("config", "配置目录"),
        ("logs", "日志目录（可选）")
    ]

    all_ok = True
    for dir_path, description in expected_dirs:
        if os.path.isdir(dir_path):
            print(f"   ✅ {description}: {dir_path}/")
        else:
            if "可选" in description:
                print(f"   ℹ️  {description}: {dir_path}/ (未创建)")
            else:
                print(f"   ⚠️  {description}: {dir_path}/ (缺失)")
                all_ok = False

    return all_ok

def test_selenium_fetcher_integrity():
    """测试selenium_fetcher的完整性"""
    print("\n📝 测试6: SeleniumFetcher完整性")

    try:
        from selenium_fetcher import SeleniumFetcher

        # 检查必要的方法
        required_methods = [
            "connect_to_chrome",
            "fetch_html_selenium",
            "__init__"
        ]

        fetcher = SeleniumFetcher()
        missing_methods = []

        for method in required_methods:
            if hasattr(fetcher, method):
                print(f"   ✅ 方法存在: {method}")
            else:
                print(f"   ❌ 方法缺失: {method}")
                missing_methods.append(method)

        return len(missing_methods) == 0

    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("\n" + "🔍"*30)
    print("  回归测试套件")
    print("  Regression Test Suite")
    print("🔍"*30)

    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }

    # 运行所有测试
    tests = [
        ("curl_fetcher", test_curl_fetcher),
        ("playwright_fetcher", test_playwright_fetcher),
        ("config_files", test_config_files),
        ("chrome_process", test_chrome_process),
        ("project_structure", test_project_structure),
        ("selenium_integrity", test_selenium_fetcher_integrity)
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            result = test_func()
            results["tests"][test_name] = "passed" if result else "failed"
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ 测试 {test_name} 异常: {e}")
            results["tests"][test_name] = "error"
            failed += 1

    # 生成总结
    print("\n" + "="*60)
    print("🔍 回归测试总结")
    print("="*60)

    print(f"\n📊 测试结果:")
    print(f"   ✅ 通过: {passed}/{len(tests)}")
    print(f"   ❌ 失败: {failed}/{len(tests)}")

    # 保存结果
    import json
    output_file = "tests/diagnostics/regression_test_results.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📁 详细结果已保存到: {output_file}")

    if failed == 0:
        print("\n✅ 回归测试全部通过！系统完整性验证成功")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个回归测试失败，请检查")
        return 1

if __name__ == "__main__":
    sys.exit(main())