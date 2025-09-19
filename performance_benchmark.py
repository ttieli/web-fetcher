#!/usr/bin/env python3
"""
性能基准测试脚本
评估智能编码检测系统的性能影响
"""

import sys
import time
import statistics
import re
from typing import List, Dict, Tuple
import logging

logging.basicConfig(level=logging.WARNING)  # 减少日志干扰

import webfetcher

# 测试配置
ITERATIONS = 10  # 每个测试的迭代次数
WARMUP_ROUNDS = 2  # 预热轮次

# 测试用例
PERFORMANCE_TEST_CASES = [
    {
        "name": "UTF-8页面（无编码转换）",
        "url": "http://example.com",
        "encoding_type": "utf-8",
        "expected_overhead": 0.05  # 预期开销 < 5%
    },
    {
        "name": "GB2312页面（需要编码检测）",
        "url": "http://cpc.people.com.cn/n/2012/1119/c352110-19621695.html",
        "encoding_type": "gb2312",
        "expected_overhead": 0.10  # 预期开销 < 10%
    }
]

def measure_encoding_detection_overhead():
    """测量编码检测函数本身的开销"""
    
    print("\n编码检测函数开销测试")
    print("-" * 50)
    
    # 准备测试数据
    test_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="gb2312">
    <title>Test Page</title>
</head>
<body>
    <h1>测试页面</h1>
    <p>这是一个测试页面，用于测量编码检测的性能开销。</p>
</body>
</html>"""
    test_data = test_html.encode('utf-8')
    
    # 测试从HTML检测编码的速度
    times = []
    for _ in range(100):
        start = time.perf_counter()
        webfetcher.extract_charset_from_html(test_data)
        elapsed = time.perf_counter() - start
        times.append(elapsed * 1000)  # 转换为毫秒
    
    avg_time = statistics.mean(times)
    print(f"  HTML编码检测平均时间: {avg_time:.3f}ms")
    
    # 测试解码函数的速度
    times = []
    for _ in range(100):
        start = time.perf_counter()
        webfetcher.smart_decode(test_data)
        elapsed = time.perf_counter() - start
        times.append(elapsed * 1000)
    
    avg_time = statistics.mean(times)
    print(f"  智能解码平均时间: {avg_time:.3f}ms")
    
    return avg_time < 10  # 应该小于10ms

def benchmark_fetch_performance():
    """基准测试页面获取性能"""
    
    print("\n页面获取性能基准测试")
    print("-" * 50)
    
    results = []
    
    for test_case in PERFORMANCE_TEST_CASES:
        print(f"\n测试: {test_case['name']}")
        print(f"  URL: {test_case['url']}")
        
        # 预热
        print("  预热中...", end="")
        for _ in range(WARMUP_ROUNDS):
            try:
                _ = webfetcher.fetch_html(test_case['url'])
            except:
                pass
        print("完成")
        
        # 正式测试
        times = []
        errors = 0
        
        print(f"  运行 {ITERATIONS} 次测试...")
        for i in range(ITERATIONS):
            try:
                start = time.perf_counter()
                content = webfetcher.fetch_html(test_case['url'])
                elapsed = time.perf_counter() - start
                times.append(elapsed)
                
                # 验证内容正确性
                if "�" in content:
                    errors += 1
            except Exception as e:
                print(f"    错误: {e}")
                errors += 1
        
        if times:
            avg_time = statistics.mean(times)
            std_dev = statistics.stdev(times) if len(times) > 1 else 0
            min_time = min(times)
            max_time = max(times)
            
            print(f"  结果:")
            print(f"    平均时间: {avg_time:.3f}秒")
            print(f"    标准差: {std_dev:.3f}秒")
            print(f"    最小/最大: {min_time:.3f}s / {max_time:.3f}s")
            print(f"    错误率: {errors}/{ITERATIONS}")
            
            results.append({
                "name": test_case['name'],
                "avg_time": avg_time,
                "std_dev": std_dev,
                "errors": errors,
                "encoding": test_case['encoding_type']
            })
    
    return results

def compare_encoding_performance():
    """比较不同编码的处理性能"""
    
    print("\n编码处理性能对比")
    print("-" * 50)
    
    # 准备不同编码的测试数据
    test_strings = {
        "utf-8": "这是UTF-8编码的测试字符串：你好世界！",
        "gb2312": "这是GB2312编码的测试字符串：你好世界！",
        "gbk": "这是GBK编码的测试字符串：你好世界！€",  # 包含欧元符号，GB2312不支持
    }
    
    for encoding, text in test_strings.items():
        try:
            # 编码成字节
            data = text.encode(encoding)
            
            # 测试解码速度
            times = []
            for _ in range(1000):
                start = time.perf_counter()
                decoded = webfetcher.smart_decode(data)
                elapsed = time.perf_counter() - start
                times.append(elapsed * 1000)
            
            avg_time = statistics.mean(times)
            print(f"  {encoding.upper():8} 解码时间: {avg_time:.3f}ms")
        except Exception as e:
            print(f"  {encoding.upper():8} 测试失败: {e}")

def generate_performance_report(results: List[Dict]):
    """生成性能报告"""
    
    print("\n" + "=" * 60)
    print("性能影响评估报告")
    print("=" * 60)
    
    # 计算UTF-8基准
    utf8_result = next((r for r in results if r['encoding'] == 'utf-8'), None)
    if utf8_result:
        baseline = utf8_result['avg_time']
        
        print(f"\nUTF-8基准时间: {baseline:.3f}秒")
        print("\n相对性能影响:")
        
        for result in results:
            overhead = (result['avg_time'] - baseline) / baseline * 100
            status = "✓" if overhead < 15 else "✗"
            print(f"  {result['name']}")
            print(f"    平均时间: {result['avg_time']:.3f}秒")
            print(f"    相对开销: {overhead:+.1f}%")
            print(f"    状态: {status}")
    
    # 总体评估
    print("\n总体评估:")
    all_acceptable = all(r['errors'] == 0 for r in results)
    
    if all_acceptable:
        print("  ✓ 所有测试通过，无编码错误")
    else:
        print("  ✗ 存在编码错误，需要检查")
    
    # 判断性能影响是否可接受
    if utf8_result:
        max_overhead = max((r['avg_time'] - baseline) / baseline * 100 
                          for r in results if r != utf8_result)
        if max_overhead < 15:
            print(f"  ✓ 最大性能开销 {max_overhead:.1f}% 在可接受范围内（<15%）")
            return True
        else:
            print(f"  ✗ 最大性能开销 {max_overhead:.1f}% 超出预期")
            return False
    
    return True

def main():
    """主测试流程"""
    
    print("=" * 60)
    print("智能编码检测系统 - 性能基准测试")
    print("=" * 60)
    
    # 1. 测量编码检测开销
    detection_ok = measure_encoding_detection_overhead()
    
    # 2. 基准测试页面获取
    fetch_results = benchmark_fetch_performance()
    
    # 3. 编码性能对比
    compare_encoding_performance()
    
    # 4. 生成报告
    perf_ok = generate_performance_report(fetch_results)
    
    # 最终结论
    print("\n" + "=" * 60)
    print("性能验证结论")
    print("=" * 60)
    
    if detection_ok and perf_ok:
        print("\n✓ 性能验证通过：智能编码检测系统的性能影响在可接受范围内")
        print("  - 编码检测开销 < 10ms")
        print("  - 整体性能影响 < 15%")
        return 0
    else:
        print("\n✗ 性能验证未通过：需要优化性能")
        return 1

if __name__ == "__main__":
    sys.exit(main())