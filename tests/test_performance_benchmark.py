#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能基准测试
Performance Benchmark Test for Selenium Integration
"""

import sys
import os
import time
import statistics
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium_fetcher import SeleniumFetcher

def run_performance_test():
    """运行性能基准测试"""
    print("\n⚡ 性能基准测试")
    print("="*60)

    fetcher = None
    results = {
        "timestamp": datetime.now().isoformat(),
        "connection_tests": [],
        "fetch_tests": [],
        "stability_tests": []
    }

    try:
        # 初始化
        fetcher = SeleniumFetcher()

        # 测试1：连接稳定性测试（10次连续连接）
        print("\n📝 测试1: 连接稳定性测试（10次）")
        connection_times = []

        for i in range(10):
            start = time.time()
            success, message = fetcher.connect_to_chrome()
            duration = time.time() - start

            if success:
                connection_times.append(duration)
                print(f"   [{i+1:2d}] ✅ 连接成功: {duration:.3f}秒")
            else:
                print(f"   [{i+1:2d}] ❌ 连接失败: {message}")

            # 短暂延迟避免过快重连
            time.sleep(0.1)

        if connection_times:
            avg_time = statistics.mean(connection_times)
            min_time = min(connection_times)
            max_time = max(connection_times)
            std_dev = statistics.stdev(connection_times) if len(connection_times) > 1 else 0

            print(f"\n   📊 连接性能统计:")
            print(f"      - 成功率: {len(connection_times)}/10")
            print(f"      - 平均时间: {avg_time:.3f}秒")
            print(f"      - 最快: {min_time:.3f}秒")
            print(f"      - 最慢: {max_time:.3f}秒")
            print(f"      - 标准差: {std_dev:.3f}秒")

            results["connection_tests"] = {
                "success_rate": f"{len(connection_times)}/10",
                "average": avg_time,
                "min": min_time,
                "max": max_time,
                "std_dev": std_dev,
                "samples": connection_times
            }

        # 测试2：页面抓取性能测试
        print("\n📝 测试2: 页面抓取性能测试（5个页面）")

        # 确保已连接
        fetcher.connect_to_chrome()

        test_urls = [
            "http://example.com",
            "http://example.org",
            "http://example.net",
            "http://httpbin.org/html",
            "http://httpbin.org/status/200"
        ]

        fetch_times = []
        for i, url in enumerate(test_urls, 1):
            start = time.time()
            content, metrics = fetcher.fetch_html_selenium(url)
            duration = time.time() - start

            if content:
                fetch_times.append({
                    "url": url,
                    "total_time": duration,
                    "page_load_time": metrics.page_load_time,
                    "content_size": len(content)
                })
                print(f"   [{i}] ✅ {url[:30]:30s} {duration:.3f}秒 ({len(content):,}字节)")
            else:
                print(f"   [{i}] ❌ {url[:30]:30s} 失败")

        if fetch_times:
            avg_fetch = statistics.mean(t["total_time"] for t in fetch_times)
            avg_load = statistics.mean(t["page_load_time"] for t in fetch_times)

            print(f"\n   📊 抓取性能统计:")
            print(f"      - 成功率: {len(fetch_times)}/{len(test_urls)}")
            print(f"      - 平均总时间: {avg_fetch:.3f}秒")
            print(f"      - 平均加载时间: {avg_load:.3f}秒")
            print(f"      - 总数据量: {sum(t['content_size'] for t in fetch_times):,}字节")

            results["fetch_tests"] = {
                "success_rate": f"{len(fetch_times)}/{len(test_urls)}",
                "average_total": avg_fetch,
                "average_load": avg_load,
                "details": fetch_times
            }

        # 测试3：连续负载测试
        print("\n📝 测试3: 连续负载测试（20次快速抓取）")

        rapid_test_url = "http://example.com"
        rapid_times = []
        failures = 0

        start_batch = time.time()
        for i in range(20):
            start = time.time()
            content, metrics = fetcher.fetch_html_selenium(rapid_test_url)
            duration = time.time() - start

            if content:
                rapid_times.append(duration)
                if (i + 1) % 5 == 0:
                    print(f"   [{i+1:2d}] ✅ 批次完成: 平均{statistics.mean(rapid_times[-5:]):.3f}秒")
            else:
                failures += 1

        total_batch_time = time.time() - start_batch

        if rapid_times:
            print(f"\n   📊 负载测试统计:")
            print(f"      - 成功率: {len(rapid_times)}/20")
            print(f"      - 失败次数: {failures}")
            print(f"      - 总耗时: {total_batch_time:.2f}秒")
            print(f"      - 平均响应: {statistics.mean(rapid_times):.3f}秒")
            print(f"      - 吞吐量: {len(rapid_times)/total_batch_time:.2f}次/秒")

            results["stability_tests"] = {
                "success_rate": f"{len(rapid_times)}/20",
                "failures": failures,
                "total_time": total_batch_time,
                "average_response": statistics.mean(rapid_times),
                "throughput": len(rapid_times)/total_batch_time
            }

    except Exception as e:
        print(f"\n❌ 测试错误: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        if fetcher:
            try:
                if hasattr(fetcher, 'close'):
                    fetcher.close()
            except:
                pass

    # 生成总结
    print("\n" + "="*60)
    print("⚡ 性能测试总结")
    print("="*60)

    if "connection_tests" in results and results["connection_tests"]:
        print(f"\n✅ 连接性能: 平均{results['connection_tests']['average']:.3f}秒")

    if "fetch_tests" in results and results["fetch_tests"]:
        print(f"✅ 抓取性能: 平均{results['fetch_tests']['average_total']:.3f}秒")

    if "stability_tests" in results and results["stability_tests"]:
        print(f"✅ 系统吞吐: {results['stability_tests']['throughput']:.2f}页面/秒")

    # 保存结果
    import json
    output_file = "tests/diagnostics/performance_benchmark_results.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📁 详细结果已保存到: {output_file}")

    return results

if __name__ == "__main__":
    run_performance_test()