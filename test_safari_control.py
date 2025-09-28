#!/usr/bin/env python3
"""
Safari Fallback Control Test Suite
验证Safari fallback机制的用户控制功能
"""

import subprocess
import sys
import time
from pathlib import Path

def run_test(description, command):
    """运行单个测试并报告结果"""
    print(f"\n{'='*60}")
    print(f"测试: {description}")
    print(f"命令: {command}")
    print(f"{'='*60}")
    
    result = subprocess.run(
        command, 
        shell=True, 
        capture_output=True, 
        text=True,
        cwd=Path(__file__).parent
    )
    
    # 分析输出
    output = result.stdout + result.stderr
    
    # 检查关键指标
    safari_triggered = "Safari" in output and ("Using Safari" in output or "Safari plugin" in output)
    urllib_used = "http_urllib" in output or "Using urllib" in output
    fallback_disabled = "--no-fallback" in output or "fallback disabled" in output.lower()
    error_occurred = "Error:" in output or "Failed to fetch" in output
    
    print(f"结果分析:")
    print(f"  - Safari触发: {'是' if safari_triggered else '否'}")
    print(f"  - Urllib使用: {'是' if urllib_used else '否'}")
    print(f"  - Fallback禁用: {'是' if fallback_disabled else '否'}")
    print(f"  - 错误发生: {'是' if error_occurred else '否'}")
    
    # 输出关键日志
    print(f"\n关键日志:")
    for line in output.split('\n'):
        if any(keyword in line for keyword in ['Safari', 'urllib', 'fallback', 'preference', 'Error']):
            print(f"  {line[:100]}")
    
    return {
        'safari_triggered': safari_triggered,
        'urllib_used': urllib_used,
        'fallback_disabled': fallback_disabled,
        'error_occurred': error_occurred
    }

def main():
    """执行测试套件"""
    print("Safari Fallback控制测试套件")
    print("="*60)
    
    test_url = "https://mp.weixin.qq.com/s/2_cHDRsWhpaP4k9DUBXZYQ?poc_token=HGKW2Gijq9uShoyNgPnn2jg7mYJvKfjo1852bfkT"
    invalid_url = "https://invalid-test-url-12345.com"
    
    tests = [
        {
            'name': '测试1: -u参数（强制urllib）',
            'command': f'python webfetcher.py -u "{test_url}" 2>&1',
            'expected': {
                'safari_triggered': False,
                'urllib_used': True,
                'fallback_disabled': False
            }
        },
        {
            'name': '测试2: 无参数（auto模式）',
            'command': f'python webfetcher.py "{test_url}" 2>&1',
            'expected': {
                'safari_triggered': False,  # 对于微信URL，通常不需要Safari
                'urllib_used': True,
                'fallback_disabled': False
            }
        },
        {
            'name': '测试3: --no-fallback（禁用fallback）',
            'command': f'python webfetcher.py --no-fallback "{invalid_url}" 2>&1',
            'expected': {
                'safari_triggered': False,
                'error_occurred': True,
                'fallback_disabled': True
            }
        },
        {
            'name': '测试4: -u + --no-fallback组合',
            'command': f'python webfetcher.py -u --no-fallback "{test_url}" 2>&1',
            'expected': {
                'safari_triggered': False,
                'urllib_used': True,
                'fallback_disabled': True
            }
        }
    ]
    
    results = []
    for test in tests:
        result = run_test(test['name'], test['command'])
        
        # 验证期望结果
        passed = True
        for key, expected_value in test['expected'].items():
            if key in result and result[key] != expected_value:
                print(f"  ⚠️ 期望 {key}={expected_value}, 实际={result[key]}")
                passed = False
        
        results.append({
            'test': test['name'],
            'passed': passed,
            'result': result
        })
        
        # 清理生成的文件
        subprocess.run('rm -f 2025-*-*.md', shell=True)
        time.sleep(1)
    
    # 总结
    print(f"\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")
    
    for r in results:
        status = "✅ 通过" if r['passed'] else "❌ 失败"
        print(f"{r['test']}: {status}")
    
    total_passed = sum(1 for r in results if r['passed'])
    print(f"\n总计: {total_passed}/{len(results)} 测试通过")
    
    # 架构师评估
    print(f"\n{'='*60}")
    print("架构师评估")
    print(f"{'='*60}")
    
    if total_passed == len(results):
        print("✅ 步骤1修复验证成功！")
        print("Safari fallback机制已被正确控制:")
        print("  1. -u参数成功禁用Safari fallback")
        print("  2. --no-fallback参数正常工作")
        print("  3. 用户偏好得到正确尊重")
        print("\n建议: 可以进行步骤2的内容提取优化")
    else:
        print("⚠️ 部分测试未通过，需要进一步调查")
        print("请检查失败的测试场景并修复相关问题")

if __name__ == "__main__":
    main()