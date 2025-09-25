#!/usr/bin/env python3
"""
自动化运行所有Selenium可行性测试
"""

import sys
import os
import time
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def run_connection_test():
    """运行Chrome Debug连接测试"""
    print("\n" + "="*60)
    print("1. Chrome Debug 连接测试")
    print("="*60)
    
    from selenium_debug_connection_test import ChromeDebugConnectionTest
    tester = ChromeDebugConnectionTest()
    return tester.run_all_tests()

def run_content_extraction_test():
    """运行内容提取测试"""
    print("\n" + "="*60)
    print("2. 内容提取测试")
    print("="*60)
    
    from selenium_content_extraction_test import ContentExtractionTest
    tester = ContentExtractionTest()
    return tester.run_all_tests()

def run_session_reuse_test():
    """运行会话复用测试"""
    print("\n" + "="*60)
    print("3. 会话复用测试")
    print("="*60)
    
    from selenium_session_reuse_test import SessionReuseTest
    tester = SessionReuseTest()
    return tester.run_all_tests()

def run_error_handling_test():
    """运行错误处理测试"""
    print("\n" + "="*60)
    print("4. 错误处理测试")
    print("="*60)
    
    from selenium_error_handling_test import ErrorHandlingTest
    tester = ErrorHandlingTest()
    return tester.run_all_tests()

def main():
    """主测试流程"""
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " "*10 + "Selenium + Chrome Debug 完整可行性测试" + " "*10 + "║")
    print("╚" + "="*58 + "╝\n")
    
    # 测试URL列表
    test_urls = [
        "https://mp.weixin.qq.com/s/xM_lYyQXmg4JCpd1w7kPxg?scene=1&click_id=5",
        "https://www.xiaohongshu.com/explore/68be9ba0000000001c00f210",
        "https://www.qstheory.cn/dukan/qs/2024-01/31/c_1130069364.htm",
        "https://arxiv.org/pdf/2508.18190",
        "http://www.news.cn/politics/leaders/20250305/0d1eaaa64ec74dd5916d29b28fe4fda8/c.html",
        "https://zh.wikipedia.org/zh-hans/%E8%8C%83%E6%9B%BE"
    ]
    
    print("📋 测试URL列表:")
    for i, url in enumerate(test_urls, 1):
        print(f"   {i}. {url[:60]}...")
    
    results = {
        "connection": False,
        "content_extraction": False,
        "session_reuse": False,
        "error_handling": False
    }
    
    # 运行各项测试
    try:
        print("\n开始测试套件...")
        time.sleep(1)
        
        # 1. 连接测试
        try:
            results["connection"] = run_connection_test()
        except Exception as e:
            print(f"❌ 连接测试失败: {e}")
            results["connection"] = False
        
        # 2. 内容提取测试
        if results["connection"]:
            try:
                results["content_extraction"] = run_content_extraction_test()
            except Exception as e:
                print(f"❌ 内容提取测试失败: {e}")
                results["content_extraction"] = False
        
        # 3. 会话复用测试
        if results["connection"]:
            try:
                results["session_reuse"] = run_session_reuse_test()
            except Exception as e:
                print(f"❌ 会话复用测试失败: {e}")
                results["session_reuse"] = False
        
        # 4. 错误处理测试
        if results["connection"]:
            try:
                results["error_handling"] = run_error_handling_test()
            except Exception as e:
                print(f"❌ 错误处理测试失败: {e}")
                results["error_handling"] = False
    
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        return
    
    # 生成测试报告
    print("\n" + "="*60)
    print("📊 测试结果总结")
    print("="*60)
    
    passed_tests = sum(1 for v in results.values() if v)
    total_tests = len(results)
    
    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    # 计算可行性得分
    score = (passed_tests / total_tests) * 100
    
    print("\n" + "-"*60)
    print(f"📈 可行性得分: {score:.0f}/100")
    print("-"*60)
    
    # 给出建议
    print("\n💡 技术建议:")
    if score >= 75:
        print("✅ 强烈推荐: Selenium + debuggerAddress方案表现优秀")
        print("   - Chrome Debug连接稳定")
        print("   - 内容提取能力强")
        print("   - 适合处理复杂JavaScript渲染页面")
        print("   - 建议立即开始正式插件开发")
    elif score >= 50:
        print("⚠️  谨慎推荐: 方案可行但需要优化")
        print("   - 部分功能正常但存在问题")
        print("   - 需要加强错误处理")
        print("   - 建议先解决已知问题再开发")
    else:
        print("❌ 不推荐: 当前环境下方案存在严重问题")
        print("   - Chrome Debug连接不稳定")
        print("   - 建议检查Chrome调试模式配置")
        print("   - 考虑其他替代方案")
    
    # 保存测试报告
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "results": results,
        "score": score,
        "test_urls": test_urls
    }
    
    report_file = Path(__file__).parent / "test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 详细报告已保存到: {report_file}")
    
    return score >= 75

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)