#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实际场景集成测试
Real Scenario Integration Test
测试selenium_fetcher在实际使用中的表现
"""

import sys
import os
import time
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium_fetcher import SeleniumFetcher

def print_section(title):
    """打印测试节标题"""
    print("\n" + "="*60)
    print(f"{title}")
    print("="*60)

def test_selenium_fetcher_integration():
    """测试SeleniumFetcher的完整功能"""

    print("\n🧪 实际场景集成测试")
    print("   Real Scenario Integration Test")
    print_section("测试SeleniumFetcher完整工作流程")

    results = {
        "start_time": datetime.now().isoformat(),
        "tests": {}
    }

    try:
        # 测试1：创建fetcher实例
        print("\n📝 测试1: 创建SeleniumFetcher实例")
        start_time = time.time()

        fetcher = SeleniumFetcher()
        creation_time = time.time() - start_time

        print(f"   ✅ 实例创建成功 (耗时: {creation_time:.2f}秒)")
        results["tests"]["instance_creation"] = {
            "status": "passed",
            "duration": creation_time
        }

        # 测试2：连接到Chrome
        print("\n📝 测试2: 连接到Chrome调试实例")
        start_time = time.time()

        driver = fetcher.get_driver()
        connection_time = time.time() - start_time

        if driver:
            print(f"   ✅ 连接成功 (耗时: {connection_time:.2f}秒)")
            print(f"   📋 浏览器: {driver.capabilities.get('browserName')}")
            print(f"   📋 版本: {driver.capabilities.get('browserVersion')}")
            results["tests"]["chrome_connection"] = {
                "status": "passed",
                "duration": connection_time,
                "browser": driver.capabilities.get('browserName'),
                "version": driver.capabilities.get('browserVersion')
            }
        else:
            print("   ❌ 连接失败")
            results["tests"]["chrome_connection"] = {"status": "failed"}
            return results

        # 测试3：抓取单个页面
        print("\n📝 测试3: 抓取单个页面")
        test_url = "http://example.com"
        start_time = time.time()

        content = fetcher.fetch(test_url)
        fetch_time = time.time() - start_time

        if content:
            print(f"   ✅ 页面抓取成功 (耗时: {fetch_time:.2f}秒)")
            print(f"   📋 内容长度: {len(content)} 字符")
            print(f"   📋 包含标题: {'Example Domain' in content}")
            results["tests"]["single_fetch"] = {
                "status": "passed",
                "duration": fetch_time,
                "content_length": len(content),
                "url": test_url
            }
        else:
            print("   ❌ 抓取失败")
            results["tests"]["single_fetch"] = {"status": "failed"}

        # 测试4：批量抓取测试
        print("\n📝 测试4: 批量抓取测试")
        test_urls = [
            "http://example.com",
            "http://example.org",
            "http://example.net"
        ]

        batch_results = []
        start_time = time.time()

        for url in test_urls:
            fetch_start = time.time()
            content = fetcher.fetch(url)
            fetch_duration = time.time() - fetch_start

            if content:
                print(f"   ✅ {url}: 成功 ({fetch_duration:.2f}秒, {len(content)}字符)")
                batch_results.append({
                    "url": url,
                    "success": True,
                    "duration": fetch_duration,
                    "length": len(content)
                })
            else:
                print(f"   ❌ {url}: 失败")
                batch_results.append({
                    "url": url,
                    "success": False
                })

        total_batch_time = time.time() - start_time
        success_count = sum(1 for r in batch_results if r["success"])

        print(f"\n   📊 批量结果: {success_count}/{len(test_urls)} 成功")
        print(f"   ⏱️  总耗时: {total_batch_time:.2f}秒")
        print(f"   ⏱️  平均时间: {total_batch_time/len(test_urls):.2f}秒/页")

        results["tests"]["batch_fetch"] = {
            "status": "passed" if success_count == len(test_urls) else "partial",
            "total_duration": total_batch_time,
            "success_rate": f"{success_count}/{len(test_urls)}",
            "details": batch_results
        }

        # 测试5：JavaScript执行测试
        print("\n📝 测试5: JavaScript执行能力")
        driver.get("http://example.com")

        js_tests = [
            ("document.title", "获取页面标题"),
            ("window.location.href", "获取当前URL"),
            ("document.body.innerText.length", "获取页面文本长度"),
            ("navigator.userAgent", "获取User-Agent")
        ]

        js_results = []
        for js_code, description in js_tests:
            try:
                result = driver.execute_script(f"return {js_code}")
                print(f"   ✅ {description}: {str(result)[:50]}...")
                js_results.append({
                    "test": description,
                    "success": True,
                    "result": str(result)[:100]
                })
            except Exception as e:
                print(f"   ❌ {description}: {str(e)}")
                js_results.append({
                    "test": description,
                    "success": False,
                    "error": str(e)
                })

        js_success = sum(1 for r in js_results if r["success"])
        results["tests"]["javascript_execution"] = {
            "status": "passed" if js_success == len(js_tests) else "partial",
            "success_rate": f"{js_success}/{len(js_tests)}",
            "details": js_results
        }

        # 测试6：错误处理测试
        print("\n📝 测试6: 错误处理能力")
        error_tests = [
            ("http://invalid-domain-that-does-not-exist-12345.com", "无效域名"),
            ("http://127.0.0.1:99999", "无效端口"),
            ("ftp://example.com", "非HTTP协议")
        ]

        error_handling_results = []
        for test_url, description in error_tests:
            try:
                content = fetcher.fetch(test_url)
                if content:
                    print(f"   ⚠️  {description}: 意外成功")
                    error_handling_results.append({
                        "test": description,
                        "handled": False
                    })
                else:
                    print(f"   ✅ {description}: 正确处理错误")
                    error_handling_results.append({
                        "test": description,
                        "handled": True
                    })
            except Exception as e:
                print(f"   ✅ {description}: 异常被捕获 - {type(e).__name__}")
                error_handling_results.append({
                    "test": description,
                    "handled": True,
                    "exception": type(e).__name__
                })

        handled_count = sum(1 for r in error_handling_results if r.get("handled", False))
        results["tests"]["error_handling"] = {
            "status": "passed" if handled_count == len(error_tests) else "partial",
            "handled_rate": f"{handled_count}/{len(error_tests)}",
            "details": error_handling_results
        }

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        results["error"] = str(e)

    finally:
        # 清理
        try:
            if 'fetcher' in locals():
                fetcher.close()
                print("\n✅ 资源清理完成")
        except:
            pass

        results["end_time"] = datetime.now().isoformat()

    return results

def main():
    """主测试函数"""
    print("\n" + "🧪"*30)
    print("  SeleniumFetcher 实际场景集成测试")
    print("  Real Scenario Integration Test Suite")
    print("🧪"*30)

    # 运行测试
    results = test_selenium_fetcher_integration()

    # 生成测试总结
    print_section("测试总结 / Test Summary")

    passed = sum(1 for t in results["tests"].values() if t.get("status") == "passed")
    partial = sum(1 for t in results["tests"].values() if t.get("status") == "partial")
    failed = sum(1 for t in results["tests"].values() if t.get("status") == "failed")
    total = len(results["tests"])

    print(f"\n📊 测试结果统计:")
    print(f"   ✅ 通过: {passed}/{total}")
    print(f"   ⚠️  部分通过: {partial}/{total}")
    print(f"   ❌ 失败: {failed}/{total}")

    # 保存结果到文件
    output_file = "tests/diagnostics/real_scenario_test_results.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📁 详细结果已保存到: {output_file}")

    # 返回状态
    if failed > 0:
        print("\n❌ 集成测试失败")
        return 1
    elif partial > 0:
        print("\n⚠️  集成测试部分通过")
        return 0
    else:
        print("\n✅ 集成测试全部通过！")
        return 0

if __name__ == "__main__":
    sys.exit(main())