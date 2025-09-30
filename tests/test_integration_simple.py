#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的集成测试 - 验证SeleniumFetcher基本功能
Simplified Integration Test for SeleniumFetcher
"""

import sys
import os
import time
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium_fetcher import SeleniumFetcher

def test_basic_functionality():
    """测试基本功能"""
    print("\n🧪 SeleniumFetcher 简化集成测试")
    print("="*60)

    results = []
    fetcher = None

    try:
        # 测试1：创建实例
        print("\n📝 测试1: 创建SeleniumFetcher实例...")
        start = time.time()
        fetcher = SeleniumFetcher()
        duration = time.time() - start
        print(f"   ✅ 实例创建成功 (耗时: {duration:.2f}秒)")
        results.append(("instance_creation", "passed", duration))

        # 测试2：连接到Chrome
        print("\n📝 测试2: 连接到Chrome调试实例...")
        start = time.time()
        success, message = fetcher.connect_to_chrome()
        duration = time.time() - start

        if success:
            print(f"   ✅ Chrome连接成功 (耗时: {duration:.2f}秒)")
            print(f"   📋 连接信息: {message}")
            results.append(("chrome_connection", "passed", duration))
        else:
            print(f"   ❌ Chrome连接失败: {message}")
            results.append(("chrome_connection", "failed", duration))
            return False

        # 测试3：抓取测试页面
        print("\n📝 测试3: 抓取测试页面...")
        test_url = "http://example.com"
        start = time.time()

        # 使用fetch_html_selenium方法
        content, metrics = fetcher.fetch_html_selenium(test_url)
        duration = time.time() - start

        if content:
            print(f"   ✅ 页面抓取成功 (耗时: {duration:.2f}秒)")
            print(f"   📋 内容长度: {len(content)} 字符")
            print(f"   📋 包含标题: {'Example Domain' in content}")
            print(f"   📊 性能指标:")
            print(f"      - 连接时间: {metrics.connection_time:.2f}秒")
            print(f"      - 加载时间: {metrics.page_load_time:.2f}秒")
            print(f"      - 会话保持: {metrics.session_preserved}")
            print(f"      - 调试端口: {metrics.debug_port}")
            results.append(("page_fetch", "passed", duration))
        else:
            print("   ❌ 页面抓取失败")
            results.append(("page_fetch", "failed", duration))

        # 测试4：连续抓取测试（验证会话保持）
        print("\n📝 测试4: 连续抓取测试（会话保持）...")
        test_urls = ["http://example.org", "http://example.net"]

        for i, url in enumerate(test_urls, 1):
            start = time.time()
            content, metrics = fetcher.fetch_html_selenium(url)
            duration = time.time() - start

            if content:
                print(f"   ✅ [{i}] {url}: 成功 ({duration:.2f}秒, {len(content)}字符)")
                results.append((f"batch_fetch_{i}", "passed", duration))
            else:
                print(f"   ❌ [{i}] {url}: 失败")
                results.append((f"batch_fetch_{i}", "failed", duration))

        # 测试5：错误处理
        print("\n📝 测试5: 错误处理测试...")
        invalid_url = "http://invalid-domain-12345.com"
        start = time.time()

        try:
            content, metrics = fetcher.fetch_html_selenium(invalid_url)
            duration = time.time() - start

            if not content:
                print(f"   ✅ 错误被正确处理（返回空内容）")
                results.append(("error_handling", "passed", duration))
            else:
                print(f"   ⚠️  意外成功")
                results.append(("error_handling", "unexpected", duration))
        except Exception as e:
            print(f"   ✅ 异常被正确捕获: {type(e).__name__}")
            results.append(("error_handling", "passed", time.time() - start))

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 清理资源
        if fetcher:
            try:
                # SeleniumFetcher可能有close方法
                if hasattr(fetcher, 'close'):
                    fetcher.close()
                print("\n✅ 资源清理完成")
            except:
                pass

    # 生成报告
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)

    passed = sum(1 for _, status, _ in results if status == "passed")
    failed = sum(1 for _, status, _ in results if status == "failed")
    total = len(results)

    print(f"✅ 通过: {passed}/{total}")
    print(f"❌ 失败: {failed}/{total}")

    if failed == 0:
        print("\n🎉 所有测试通过！")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)