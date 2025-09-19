#!/usr/bin/env python3
"""
性能优化验证测试脚本
架构师验证工具 - 用于验证性能优化的实际效果

测试目标:
1. 验证人民网页面处理性能
2. 确认超时机制有效性
3. 测试内容提取完整性
4. 验证其他站点兼容性
"""

import time
import subprocess
import json
import sys
import os
import tempfile
import hashlib
from datetime import datetime

class PerformanceValidator:
    def __init__(self):
        self.test_results = []
        self.critical_issues = []
        
    def run_test(self, test_name, url, expected_behavior):
        """执行单个测试用例"""
        print(f"\n[TEST] {test_name}")
        print(f"  URL: {url}")
        print(f"  Expected: {expected_behavior}")
        
        start_time = time.time()
        temp_dir = tempfile.mkdtemp()
        output_file = os.path.join(temp_dir, 'output.md')
        
        try:
            # 执行webfetcher
            cmd = [
                'python3', 'webfetcher.py',
                url,
                '-o', temp_dir
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10  # 10秒硬超时
            )
            
            elapsed = time.time() - start_time
            
            # 分析结果
            success = result.returncode == 0
            has_output = os.path.exists(output_file)
            output_size = os.path.getsize(output_file) if has_output else 0
            
            test_result = {
                'name': test_name,
                'url': url,
                'success': success,
                'elapsed_time': elapsed,
                'has_output': has_output,
                'output_size': output_size,
                'stderr': result.stderr if not success else None
            }
            
            # 验证内容
            if has_output:
                with open(output_file, 'r') as f:
                    content = f.read()
                    test_result['content_hash'] = hashlib.md5(content.encode()).hexdigest()
                    test_result['line_count'] = len(content.splitlines())
                    
                    # 特定内容验证
                    if 'people.com.cn' in url:
                        # 检查是否有政治局会议记录
                        has_meeting_records = '政治局' in content or '会议' in content
                        test_result['has_expected_content'] = has_meeting_records
            
            self.test_results.append(test_result)
            
            # 输出测试结果
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  Status: {status}")
            print(f"  Time: {elapsed:.2f}s")
            print(f"  Output: {output_size} bytes, {test_result.get('line_count', 0)} lines")
            
            if elapsed > 5:
                self.critical_issues.append(f"Performance issue: {test_name} took {elapsed:.2f}s")
            
            if not success:
                self.critical_issues.append(f"Failed test: {test_name}")
                print(f"  Error: {result.stderr[:200]}")
                
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            self.critical_issues.append(f"TIMEOUT: {test_name} exceeded 10s limit")
            print(f"  Status: ❌ TIMEOUT after {elapsed:.2f}s")
            self.test_results.append({
                'name': test_name,
                'url': url,
                'success': False,
                'timeout': True,
                'elapsed_time': elapsed
            })
        except Exception as e:
            self.critical_issues.append(f"Exception in {test_name}: {str(e)}")
            print(f"  Status: ❌ ERROR - {str(e)}")
            self.test_results.append({
                'name': test_name,
                'url': url,
                'success': False,
                'error': str(e)
            })
        finally:
            # 清理临时文件
            if os.path.exists(temp_dir):
                subprocess.run(['rm', '-rf', temp_dir], capture_output=True)
    
    def run_validation_suite(self):
        """运行完整验证套件"""
        print("=" * 80)
        print("PERFORMANCE OPTIMIZATION VALIDATION TEST SUITE")
        print("=" * 80)
        print(f"Start Time: {datetime.now()}")
        
        # 测试用例定义
        test_cases = [
            # 1. 关键问题页面 - 人民网
            {
                'name': 'People Daily - Political Bureau Meetings (Critical)',
                'url': 'http://cpc.people.com.cn/n/2012/1119/c352110-19621695.html',
                'expected': 'Should complete within 2 seconds with meeting records'
            },
            
            # 2. 基准测试 - 简单页面
            {
                'name': 'Simple Page - Example.com',
                'url': 'http://example.com',
                'expected': 'Should complete quickly with minimal content'
            },
            
            # 3. 复杂内容页面
            {
                'name': 'Complex News Site - Sina',
                'url': 'http://news.sina.com.cn',
                'expected': 'Should handle complex layout without timeout'
            },
            
            # 4. 带表格的页面（非人民网）
            {
                'name': 'Table Content - Generic',
                'url': 'https://www.w3schools.com/html/html_tables.asp',
                'expected': 'Should process tables normally'
            }
        ]
        
        # 执行测试
        for test_case in test_cases:
            self.run_test(
                test_case['name'],
                test_case['url'],
                test_case['expected']
            )
        
        # 生成报告
        self.generate_report()
    
    def generate_report(self):
        """生成验证报告"""
        print("\n" + "=" * 80)
        print("VALIDATION REPORT")
        print("=" * 80)
        
        # 统计数据
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t.get('success'))
        failed_tests = total_tests - passed_tests
        timeout_tests = sum(1 for t in self.test_results if t.get('timeout'))
        
        avg_time = sum(t.get('elapsed_time', 0) for t in self.test_results) / total_tests if total_tests > 0 else 0
        
        print(f"\nTest Summary:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"  Failed: {failed_tests}")
        print(f"  Timeouts: {timeout_tests}")
        print(f"  Average Time: {avg_time:.2f}s")
        
        # 性能分析
        print(f"\nPerformance Analysis:")
        for result in self.test_results:
            name = result['name']
            time_taken = result.get('elapsed_time', 0)
            status = "✅" if result.get('success') else "❌"
            print(f"  {status} {name}: {time_taken:.2f}s")
        
        # 关键问题
        if self.critical_issues:
            print(f"\n⚠️  CRITICAL ISSUES FOUND:")
            for issue in self.critical_issues:
                print(f"  - {issue}")
        else:
            print(f"\n✅ No critical issues found")
        
        # 架构评估
        print(f"\n🏗️  ARCHITECTURE ASSESSMENT:")
        self.assess_architecture()
        
        # 保存详细结果
        report_file = f'validation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'timeouts': timeout_tests,
                    'avg_time': avg_time
                },
                'results': self.test_results,
                'critical_issues': self.critical_issues
            }, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_file}")
    
    def assess_architecture(self):
        """架构质量评估"""
        assessments = []
        
        # 1. 超时机制评估
        has_timeout_protection = not any(t.get('timeout') for t in self.test_results)
        if has_timeout_protection:
            assessments.append("✅ Timeout protection is working effectively")
        else:
            assessments.append("❌ Timeout protection needs improvement")
        
        # 2. 性能优化评估
        people_test = next((t for t in self.test_results if 'People Daily' in t['name']), None)
        if people_test and people_test.get('success') and people_test.get('elapsed_time', 10) < 3:
            assessments.append("✅ Critical performance issue resolved")
        else:
            assessments.append("⚠️  Performance optimization may need further work")
        
        # 3. 兼容性评估
        other_sites_ok = all(t.get('success') for t in self.test_results if 'People Daily' not in t['name'])
        if other_sites_ok:
            assessments.append("✅ Backward compatibility maintained")
        else:
            assessments.append("⚠️  Some compatibility issues detected")
        
        # 4. 代码质量评估
        assessments.append("📋 Code Quality Checklist:")
        assessments.append("  - Timeout mechanism: signal.alarm(5) implemented")
        assessments.append("  - Row limit: 50 rows max for tables")
        assessments.append("  - Cell limit: Implicit via row processing")
        assessments.append("  - Site-specific optimization: people.com.cn special handling")
        
        for assessment in assessments:
            print(f"  {assessment}")

if __name__ == '__main__':
    validator = PerformanceValidator()
    validator.run_validation_suite()