#!/usr/bin/env python3
"""
Selenium Feasibility Test Runner
运行所有可行性测试并生成综合报告

作者: Archy-Principle-Architect
日期: 2025-09-25
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0
            },
            'feasibility_assessment': {}
        }
        
        # 测试脚本列表（按执行顺序）
        self.test_scripts = [
            {
                'name': 'Connection Test',
                'script': 'selenium_debug_connection_test.py',
                'description': '验证Selenium连接Chrome Debug端口的基础能力',
                'critical': True
            },
            {
                'name': 'Session Reuse Test',
                'script': 'selenium_session_reuse_test.py',
                'description': '验证会话复用和登录态保持功能',
                'critical': True
            },
            {
                'name': 'Content Extraction Test',
                'script': 'selenium_content_extraction_test.py',
                'description': '验证不同类型网页的内容提取能力',
                'critical': True
            },
            {
                'name': 'Error Handling Test',
                'script': 'selenium_error_handling_test.py',
                'description': '验证错误处理和恢复机制',
                'critical': False
            }
        ]
    
    def log(self, message, level='INFO'):
        """日志输出"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")
    
    def check_prerequisites(self):
        """检查前置条件"""
        self.log("检查测试前置条件...")
        
        prerequisites = {
            'selenium_installed': False,
            'chrome_debug_running': False,
            'test_scripts_exist': False
        }
        
        # 检查Selenium
        try:
            import selenium
            prerequisites['selenium_installed'] = True
            self.log(f"✅ Selenium已安装 (版本: {selenium.__version__})")
        except ImportError:
            self.log("❌ Selenium未安装，请运行: pip install selenium", 'ERROR')
        
        # 检查Chrome Debug端口
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', 9222))
            sock.close()
            
            if result == 0:
                prerequisites['chrome_debug_running'] = True
                self.log("✅ Chrome Debug端口9222已开放")
            else:
                self.log("⚠️  Chrome Debug未运行或端口9222未开放", 'WARN')
                self.log("   请运行: ./chrome-debug.sh", 'WARN')
        except Exception as e:
            self.log(f"⚠️  无法检查Chrome Debug状态: {str(e)}", 'WARN')
        
        # 检查测试脚本
        missing_scripts = []
        for test in self.test_scripts:
            script_path = self.test_dir / test['script']
            if not script_path.exists():
                missing_scripts.append(test['script'])
        
        if not missing_scripts:
            prerequisites['test_scripts_exist'] = True
            self.log(f"✅ 所有测试脚本都存在")
        else:
            self.log(f"❌ 缺少测试脚本: {', '.join(missing_scripts)}", 'ERROR')
        
        return prerequisites
    
    def run_test(self, test_info):
        """运行单个测试"""
        script_path = self.test_dir / test_info['script']
        
        self.log(f"\n{'='*60}")
        self.log(f"运行测试: {test_info['name']}")
        self.log(f"描述: {test_info['description']}")
        self.log(f"脚本: {test_info['script']}")
        self.log(f"{'='*60}\n")
        
        start_time = time.time()
        
        try:
            # 运行测试脚本
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            execution_time = time.time() - start_time
            
            # 判断测试结果
            test_result = {
                'name': test_info['name'],
                'script': test_info['script'],
                'description': test_info['description'],
                'critical': test_info['critical'],
                'execution_time': f"{execution_time:.2f}s",
                'return_code': result.returncode,
                'status': 'PASS' if result.returncode == 0 else 'FAIL'
            }
            
            # 尝试找到测试报告
            report_files = list(self.test_dir.glob(f"*report*.json"))
            if report_files:
                # 找到最新的报告文件
                latest_report = max(report_files, key=lambda f: f.stat().st_mtime)
                try:
                    with open(latest_report, 'r') as f:
                        test_report = json.load(f)
                        test_result['detailed_results'] = test_report.get('summary', {})
                except:
                    pass
            
            # 提取关键输出
            if result.stdout:
                lines = result.stdout.split('\n')
                summary_lines = [l for l in lines if any(
                    keyword in l for keyword in ['成功率', '总测试数', '✅', '❌', 'PASS', 'FAIL']
                )]
                if summary_lines:
                    test_result['key_output'] = summary_lines[-5:]  # 最后5行关键输出
            
            return test_result
            
        except subprocess.TimeoutExpired:
            return {
                'name': test_info['name'],
                'script': test_info['script'],
                'status': 'TIMEOUT',
                'execution_time': '300s+',
                'error': 'Test execution timeout'
            }
        except Exception as e:
            return {
                'name': test_info['name'],
                'script': test_info['script'],
                'status': 'ERROR',
                'execution_time': f"{time.time() - start_time:.2f}s",
                'error': str(e)
            }
    
    def analyze_feasibility(self):
        """分析可行性"""
        self.log("\n分析测试结果...")
        
        # 统计关键测试通过情况
        critical_tests = [t for t in self.results['tests'] if t.get('critical', False)]
        critical_passed = sum(1 for t in critical_tests if t['status'] == 'PASS')
        
        # 计算可行性分数
        total_tests = len(self.results['tests'])
        passed_tests = sum(1 for t in self.results['tests'] if t['status'] == 'PASS')
        
        feasibility_score = 0
        if total_tests > 0:
            # 基础分数：通过测试的比例
            base_score = (passed_tests / total_tests) * 60
            
            # 关键测试加权
            if critical_tests:
                critical_score = (critical_passed / len(critical_tests)) * 40
            else:
                critical_score = 40
            
            feasibility_score = base_score + critical_score
        
        # 可行性评估
        assessment = {
            'score': round(feasibility_score, 1),
            'critical_tests_passed': f"{critical_passed}/{len(critical_tests)}",
            'total_tests_passed': f"{passed_tests}/{total_tests}",
            'recommendation': '',
            'risks': [],
            'strengths': [],
            'next_steps': []
        }
        
        # 根据分数给出建议
        if feasibility_score >= 80:
            assessment['recommendation'] = '✅ 强烈推荐：Selenium + debuggerAddress方案完全可行'
            assessment['confidence'] = 'HIGH'
        elif feasibility_score >= 60:
            assessment['recommendation'] = '⚠️  谨慎推荐：方案可行但需要处理一些问题'
            assessment['confidence'] = 'MEDIUM'
        else:
            assessment['recommendation'] = '❌ 不推荐：方案存在重大问题，需要重新评估'
            assessment['confidence'] = 'LOW'
        
        # 分析优势
        for test in self.results['tests']:
            if test['status'] == 'PASS':
                if 'Connection' in test['name']:
                    assessment['strengths'].append('Chrome Debug连接稳定可靠')
                elif 'Session' in test['name']:
                    assessment['strengths'].append('会话复用和登录态保持功能正常')
                elif 'Content' in test['name']:
                    assessment['strengths'].append('内容提取能力满足需求')
                elif 'Error' in test['name']:
                    assessment['strengths'].append('错误处理机制健壮')
        
        # 识别风险
        for test in self.results['tests']:
            if test['status'] != 'PASS':
                if test.get('critical', False):
                    assessment['risks'].append(f"关键功能失败: {test['name']}")
                else:
                    assessment['risks'].append(f"非关键功能问题: {test['name']}")
        
        # 下一步建议
        if feasibility_score >= 60:
            assessment['next_steps'] = [
                '开始设计Selenium插件架构',
                '实现基础的SeleniumFetcher类',
                '集成到现有插件系统',
                '进行性能优化和稳定性测试'
            ]
        else:
            assessment['next_steps'] = [
                '修复识别出的关键问题',
                '重新运行失败的测试',
                '考虑备选技术方案',
                '评估是否需要调整需求'
            ]
        
        self.results['feasibility_assessment'] = assessment
        return assessment
    
    def generate_report(self):
        """生成综合测试报告"""
        report = []
        report.append("\n" + "="*70)
        report.append("         Selenium + debuggerAddress 可行性测试报告")
        report.append("="*70)
        
        # 基本信息
        report.append(f"\n测试时间: {self.results['timestamp']}")
        report.append(f"测试数量: {self.results['summary']['total']}")
        report.append(f"通过数量: {self.results['summary']['passed']}")
        report.append(f"失败数量: {self.results['summary']['failed']}")
        
        # 详细结果
        report.append("\n" + "-"*70)
        report.append("详细测试结果:")
        report.append("-"*70)
        
        for test in self.results['tests']:
            status_icon = "✅" if test['status'] == 'PASS' else "❌"
            critical_tag = "[关键]" if test.get('critical', False) else ""
            report.append(f"\n{status_icon} {test['name']} {critical_tag}")
            report.append(f"   状态: {test['status']}")
            report.append(f"   耗时: {test.get('execution_time', 'N/A')}")
            if 'detailed_results' in test:
                details = test['detailed_results']
                report.append(f"   详情: 总测试 {details.get('total', 0)}, "
                            f"通过 {details.get('passed', 0)}, "
                            f"失败 {details.get('failed', 0)}")
        
        # 可行性评估
        assessment = self.results.get('feasibility_assessment', {})
        if assessment:
            report.append("\n" + "="*70)
            report.append("可行性评估")
            report.append("="*70)
            
            report.append(f"\n可行性分数: {assessment['score']}/100")
            report.append(f"置信度: {assessment.get('confidence', 'N/A')}")
            report.append(f"\n{assessment['recommendation']}")
            
            if assessment['strengths']:
                report.append("\n✅ 技术优势:")
                for strength in assessment['strengths']:
                    report.append(f"   • {strength}")
            
            if assessment['risks']:
                report.append("\n⚠️  识别的风险:")
                for risk in assessment['risks']:
                    report.append(f"   • {risk}")
            
            if assessment['next_steps']:
                report.append("\n📋 建议的后续步骤:")
                for i, step in enumerate(assessment['next_steps'], 1):
                    report.append(f"   {i}. {step}")
        
        # 技术建议
        report.append("\n" + "="*70)
        report.append("技术建议")
        report.append("="*70)
        
        if assessment.get('score', 0) >= 60:
            report.append("""
基于测试结果，建议采用以下架构：

1. **插件架构设计**
   - 创建SeleniumFetcher插件类
   - 继承自BaseFetcher接口
   - 支持配置Chrome Debug端口

2. **核心功能实现**
   - 连接管理：实现连接池和重试机制
   - 会话复用：维护长连接，支持登录态
   - 错误处理：优雅降级和自动恢复

3. **性能优化**
   - 页面加载策略优化
   - JavaScript执行缓存
   - 并发请求控制

4. **监控和日志**
   - 详细的操作日志
   - 性能指标收集
   - 错误追踪和报警
            """)
        
        report.append("\n" + "="*70)
        report.append("报告结束")
        report.append("="*70)
        
        return "\n".join(report)
    
    def save_results(self):
        """保存测试结果"""
        # 保存JSON格式
        json_file = self.test_dir / f"feasibility_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        self.log(f"JSON报告已保存: {json_file}")
        
        # 保存文本格式
        text_report = self.generate_report()
        text_file = self.test_dir / f"feasibility_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text_report)
        self.log(f"文本报告已保存: {text_file}")
        
        # 打印报告
        print(text_report)
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("="*70)
        self.log("     Selenium + debuggerAddress 可行性测试套件")
        self.log("="*70)
        
        # 检查前置条件
        prerequisites = self.check_prerequisites()
        
        if not prerequisites['selenium_installed']:
            self.log("\n❌ 无法运行测试：Selenium未安装", 'ERROR')
            self.log("请先安装: pip install selenium", 'ERROR')
            return False
        
        if not prerequisites['test_scripts_exist']:
            self.log("\n❌ 无法运行测试：测试脚本缺失", 'ERROR')
            return False
        
        if not prerequisites['chrome_debug_running']:
            self.log("\n⚠️  警告：Chrome Debug未运行，部分测试可能失败", 'WARN')
            response = input("是否继续？(y/n): ")
            if response.lower() != 'y':
                return False
        
        # 运行每个测试
        for test_info in self.test_scripts:
            result = self.run_test(test_info)
            self.results['tests'].append(result)
            self.results['summary']['total'] += 1
            
            if result['status'] == 'PASS':
                self.results['summary']['passed'] += 1
            elif result['status'] in ['FAIL', 'ERROR', 'TIMEOUT']:
                self.results['summary']['failed'] += 1
            else:
                self.results['summary']['skipped'] += 1
            
            # 短暂暂停
            time.sleep(2)
        
        # 分析可行性
        self.analyze_feasibility()
        
        # 保存和显示结果
        self.save_results()
        
        return self.results['summary']['failed'] == 0


def main():
    """主函数"""
    runner = TestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()