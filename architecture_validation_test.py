#!/usr/bin/env python3
"""
架构验证测试脚本
用于验证智能编码检测系统的实施效果
"""

import sys
import time
import logging
import statistics
from typing import List, Tuple, Dict, Any

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# 导入被测试的模块
import webfetcher

# 测试用例定义
TEST_CASES = [
    {
        "name": "人民网GB2312页面",
        "url": "http://cpc.people.com.cn/n/2012/1119/c352110-19621695.html",
        "expected_encoding": "gb2312",
        "validation_keywords": ["十八届", "中央政治局", "会议"],
        "should_not_contain": ["�", "锟斤拷", "烂码"],
        "category": "chinese_legacy"
    },
    {
        "name": "新浪UTF-8页面",
        "url": "https://www.sina.com.cn",
        "expected_encoding": "utf-8",
        "validation_keywords": ["新浪"],
        "should_not_contain": ["�"],
        "category": "chinese_modern"
    },
    {
        "name": "Example.com ASCII页面",
        "url": "http://example.com",
        "expected_encoding": "utf-8",  # ASCII兼容UTF-8
        "validation_keywords": ["Example Domain"],
        "should_not_contain": ["�"],
        "category": "international"
    }
]

def validate_content(content: str, test_case: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    验证内容是否符合预期
    
    Returns:
        (是否通过, 错误信息列表)
    """
    errors = []
    
    # 检查必须包含的关键词
    for keyword in test_case.get("validation_keywords", []):
        if keyword not in content:
            errors.append(f"Missing expected keyword: {keyword}")
    
    # 检查不应该包含的内容（乱码标志）
    for bad_pattern in test_case.get("should_not_contain", []):
        if bad_pattern in content:
            errors.append(f"Contains unwanted pattern: {bad_pattern}")
    
    return len(errors) == 0, errors

def test_encoding_detection():
    """运行编码检测测试"""
    
    logger.info("=" * 70)
    logger.info("智能编码检测系统 - 架构验证测试")
    logger.info("=" * 70)
    
    results = []
    
    for test_case in TEST_CASES:
        logger.info(f"\n测试: {test_case['name']}")
        logger.info(f"URL: {test_case['url']}")
        logger.info(f"期望编码: {test_case['expected_encoding']}")
        
        try:
            # 获取内容
            start_time = time.time()
            content = webfetcher.fetch_html(test_case['url'])
            fetch_time = time.time() - start_time
            
            # 验证内容
            passed, errors = validate_content(content, test_case)
            
            # 记录结果
            result = {
                "name": test_case['name'],
                "url": test_case['url'],
                "category": test_case['category'],
                "passed": passed,
                "errors": errors,
                "fetch_time": fetch_time,
                "content_length": len(content)
            }
            results.append(result)
            
            # 输出结果
            if passed:
                logger.info(f"✓ 通过 - 耗时: {fetch_time:.2f}秒")
                # 显示前500个字符作为验证
                preview = content[:500].replace('\n', ' ')
                logger.info(f"  内容预览: {preview}...")
            else:
                logger.info(f"✗ 失败")
                for error in errors:
                    logger.info(f"  - {error}")
        
        except Exception as e:
            logger.info(f"✗ 异常: {e}")
            results.append({
                "name": test_case['name'],
                "url": test_case['url'],
                "category": test_case['category'],
                "passed": False,
                "errors": [str(e)],
                "fetch_time": 0,
                "content_length": 0
            })
    
    return results

def test_performance_impact():
    """测试性能影响"""
    
    logger.info("\n" + "=" * 70)
    logger.info("性能影响测试")
    logger.info("=" * 70)
    
    # 测试UTF-8页面（不需要编码转换的基准）
    test_url = "http://example.com"
    
    times = []
    for i in range(5):
        start = time.time()
        _ = webfetcher.fetch_html(test_url)
        elapsed = time.time() - start
        times.append(elapsed)
        logger.info(f"  第{i+1}次: {elapsed:.3f}秒")
    
    avg_time = statistics.mean(times)
    std_dev = statistics.stdev(times) if len(times) > 1 else 0
    
    logger.info(f"\n  平均时间: {avg_time:.3f}秒")
    logger.info(f"  标准差: {std_dev:.3f}秒")
    
    # 判断性能是否在可接受范围内
    if avg_time < 2.0:
        logger.info("  ✓ 性能影响在可接受范围内")
        return True
    else:
        logger.info("  ✗ 性能影响可能过大")
        return False

def generate_report(results: List[Dict]):
    """生成验证报告"""
    
    logger.info("\n" + "=" * 70)
    logger.info("架构验证报告")
    logger.info("=" * 70)
    
    # 统计信息
    total = len(results)
    passed = sum(1 for r in results if r['passed'])
    failed = total - passed
    
    logger.info(f"\n测试统计:")
    logger.info(f"  总计: {total}")
    logger.info(f"  通过: {passed}")
    logger.info(f"  失败: {failed}")
    logger.info(f"  通过率: {(passed/total*100):.1f}%")
    
    # 按类别统计
    categories = {}
    for r in results:
        cat = r['category']
        if cat not in categories:
            categories[cat] = {'total': 0, 'passed': 0}
        categories[cat]['total'] += 1
        if r['passed']:
            categories[cat]['passed'] += 1
    
    logger.info(f"\n按类别统计:")
    for cat, stats in categories.items():
        pass_rate = stats['passed'] / stats['total'] * 100
        logger.info(f"  {cat}: {stats['passed']}/{stats['total']} ({pass_rate:.1f}%)")
    
    # 失败详情
    if failed > 0:
        logger.info(f"\n失败详情:")
        for r in results:
            if not r['passed']:
                logger.info(f"  - {r['name']}:")
                for error in r['errors']:
                    logger.info(f"    {error}")
    
    # 性能分析
    avg_fetch_time = statistics.mean([r['fetch_time'] for r in results if r['fetch_time'] > 0])
    logger.info(f"\n性能分析:")
    logger.info(f"  平均获取时间: {avg_fetch_time:.2f}秒")
    
    return passed == total

def main():
    """主测试流程"""
    
    # 1. 编码检测测试
    encoding_results = test_encoding_detection()
    
    # 2. 性能影响测试  
    perf_ok = test_performance_impact()
    
    # 3. 生成报告
    all_passed = generate_report(encoding_results)
    
    # 最终结论
    logger.info("\n" + "=" * 70)
    logger.info("最终结论")
    logger.info("=" * 70)
    
    if all_passed and perf_ok:
        logger.info("\n✓ 架构验证通过：智能编码检测系统符合设计要求")
        return 0
    else:
        logger.info("\n✗ 架构验证未完全通过，需要进一步优化")
        return 1

if __name__ == "__main__":
    sys.exit(main())