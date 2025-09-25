#!/usr/bin/env python3
"""
Selenium Debug Connection Test
验证Selenium能否成功连接到Chrome调试端口

测试内容：
1. 检测Chrome Debug端口9222是否可用
2. 尝试Selenium连接到远程调试端口
3. 验证基础页面访问功能
4. 测试浏览器控制能力

作者: Archy-Principle-Architect
日期: 2025-09-25
"""

import socket
import sys
import time
import json
import traceback
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException

class ChromeDebugConnectionTest:
    """Chrome Debug连接测试类"""
    
    def __init__(self, debug_port=9222):
        self.debug_port = debug_port
        self.debug_host = '127.0.0.1'
        self.driver = None
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0
            }
        }
    
    def log(self, message, level='INFO'):
        """日志输出"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")
    
    def add_test_result(self, name, status, message='', details=None):
        """记录测试结果"""
        result = {
            'name': name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        if details:
            result['details'] = details
        
        self.test_results['tests'].append(result)
        self.test_results['summary']['total'] += 1
        
        if status == 'PASS':
            self.test_results['summary']['passed'] += 1
            self.log(f"✅ {name}: {message}", 'SUCCESS')
        else:
            self.test_results['summary']['failed'] += 1
            self.log(f"❌ {name}: {message}", 'ERROR')
    
    def test_port_availability(self):
        """测试1: 检查Chrome Debug端口是否开放"""
        test_name = "Port Availability Test"
        self.log(f"开始测试: {test_name}")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.debug_host, self.debug_port))
            sock.close()
            
            if result == 0:
                self.add_test_result(
                    test_name, 
                    'PASS', 
                    f"端口 {self.debug_port} 已开放且可访问"
                )
                return True
            else:
                self.add_test_result(
                    test_name, 
                    'FAIL', 
                    f"端口 {self.debug_port} 未开放或不可访问",
                    {'error': f"Connection result: {result}"}
                )
                return False
        except Exception as e:
            self.add_test_result(
                test_name, 
                'FAIL', 
                f"端口检测失败: {str(e)}",
                {'error': traceback.format_exc()}
            )
            return False
    
    def test_selenium_connection(self):
        """测试2: 尝试Selenium连接到Chrome Debug实例"""
        test_name = "Selenium Connection Test"
        self.log(f"开始测试: {test_name}")
        
        try:
            # 配置Chrome选项
            chrome_options = Options()
            chrome_options.add_experimental_option(
                "debuggerAddress", 
                f"{self.debug_host}:{self.debug_port}"
            )
            
            # 使用webdriver_manager自动管理ChromeDriver版本
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            
            # 尝试连接
            self.log("正在连接到Chrome Debug实例...")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 验证连接
            if self.driver:
                # 获取当前窗口句柄
                current_window = self.driver.current_window_handle
                
                # 获取所有窗口句柄
                all_windows = self.driver.window_handles
                
                self.add_test_result(
                    test_name, 
                    'PASS', 
                    f"成功连接到Chrome Debug实例",
                    {
                        'current_window': current_window,
                        'total_windows': len(all_windows),
                        'session_id': self.driver.session_id
                    }
                )
                return True
            else:
                self.add_test_result(
                    test_name, 
                    'FAIL', 
                    "无法创建WebDriver实例"
                )
                return False
                
        except WebDriverException as e:
            self.add_test_result(
                test_name, 
                'FAIL', 
                f"Selenium连接失败: {str(e)}",
                {'error': str(e)}
            )
            return False
        except Exception as e:
            self.add_test_result(
                test_name, 
                'FAIL', 
                f"未知错误: {str(e)}",
                {'error': traceback.format_exc()}
            )
            return False
    
    def test_page_navigation(self):
        """测试3: 验证页面导航功能"""
        test_name = "Page Navigation Test"
        self.log(f"开始测试: {test_name}")
        
        if not self.driver:
            self.add_test_result(
                test_name, 
                'SKIP', 
                "WebDriver未初始化，跳过测试"
            )
            return False
        
        try:
            # 测试导航到不同页面
            test_urls = [
                ('https://www.example.com', 'Example Domain'),
                ('https://www.google.com', 'Google'),
                ('https://httpbin.org/html', 'httpbin')
            ]
            
            navigation_results = []
            
            for url, expected_title_part in test_urls:
                self.log(f"导航到: {url}")
                start_time = time.time()
                
                self.driver.get(url)
                
                # 等待页面加载
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                load_time = time.time() - start_time
                current_url = self.driver.current_url
                page_title = self.driver.title
                
                navigation_results.append({
                    'url': url,
                    'current_url': current_url,
                    'title': page_title,
                    'load_time': f"{load_time:.2f}s",
                    'success': expected_title_part.lower() in page_title.lower() or url in current_url
                })
                
                self.log(f"  - 标题: {page_title}")
                self.log(f"  - 加载时间: {load_time:.2f}秒")
            
            # 判断测试结果
            all_success = all(r['success'] for r in navigation_results)
            
            if all_success:
                self.add_test_result(
                    test_name, 
                    'PASS', 
                    f"成功导航到所有测试页面",
                    {'navigation_results': navigation_results}
                )
                return True
            else:
                self.add_test_result(
                    test_name, 
                    'PARTIAL', 
                    f"部分页面导航失败",
                    {'navigation_results': navigation_results}
                )
                return False
                
        except TimeoutException as e:
            self.add_test_result(
                test_name, 
                'FAIL', 
                f"页面加载超时: {str(e)}"
            )
            return False
        except Exception as e:
            self.add_test_result(
                test_name, 
                'FAIL', 
                f"导航测试失败: {str(e)}",
                {'error': traceback.format_exc()}
            )
            return False
    
    def test_browser_control(self):
        """测试4: 验证浏览器控制能力"""
        test_name = "Browser Control Test"
        self.log(f"开始测试: {test_name}")
        
        if not self.driver:
            self.add_test_result(
                test_name, 
                'SKIP', 
                "WebDriver未初始化，跳过测试"
            )
            return False
        
        try:
            control_tests = []
            
            # 测试获取页面源码
            self.driver.get('https://www.example.com')
            page_source = self.driver.page_source
            control_tests.append({
                'test': '获取页面源码',
                'success': len(page_source) > 100,
                'details': f"源码长度: {len(page_source)}"
            })
            
            # 测试执行JavaScript
            js_result = self.driver.execute_script("return navigator.userAgent;")
            control_tests.append({
                'test': '执行JavaScript',
                'success': js_result is not None,
                'details': f"User-Agent: {js_result[:50]}..."
            })
            
            # 测试获取Cookies
            cookies = self.driver.get_cookies()
            control_tests.append({
                'test': '获取Cookies',
                'success': isinstance(cookies, list),
                'details': f"Cookie数量: {len(cookies)}"
            })
            
            # 测试窗口管理
            original_size = self.driver.get_window_size()
            self.driver.set_window_size(1024, 768)
            new_size = self.driver.get_window_size()
            self.driver.set_window_size(original_size['width'], original_size['height'])
            control_tests.append({
                'test': '窗口大小控制',
                'success': new_size['width'] == 1024 and new_size['height'] == 768,
                'details': f"调整窗口: {original_size} -> {new_size}"
            })
            
            # 测试截图功能
            screenshot = self.driver.get_screenshot_as_base64()
            control_tests.append({
                'test': '截图功能',
                'success': len(screenshot) > 0,
                'details': f"截图大小: {len(screenshot)} bytes"
            })
            
            # 判断整体结果
            all_success = all(t['success'] for t in control_tests)
            
            if all_success:
                self.add_test_result(
                    test_name, 
                    'PASS', 
                    "所有浏览器控制功能正常",
                    {'control_tests': control_tests}
                )
                return True
            else:
                failed_tests = [t['test'] for t in control_tests if not t['success']]
                self.add_test_result(
                    test_name, 
                    'PARTIAL', 
                    f"部分控制功能失败: {', '.join(failed_tests)}",
                    {'control_tests': control_tests}
                )
                return False
                
        except Exception as e:
            self.add_test_result(
                test_name, 
                'FAIL', 
                f"浏览器控制测试失败: {str(e)}",
                {'error': traceback.format_exc()}
            )
            return False
    
    def test_performance_metrics(self):
        """测试5: 收集性能指标"""
        test_name = "Performance Metrics Test"
        self.log(f"开始测试: {test_name}")
        
        if not self.driver:
            self.add_test_result(
                test_name, 
                'SKIP', 
                "WebDriver未初始化，跳过测试"
            )
            return False
        
        try:
            # 测试页面加载性能
            self.driver.get('https://www.example.com')
            
            # 收集性能指标
            performance_data = self.driver.execute_script("""
                var performance = window.performance || {};
                var timing = performance.timing || {};
                var navigation = performance.navigation || {};
                
                return {
                    timing: {
                        domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
                        loadComplete: timing.loadEventEnd - timing.navigationStart,
                        domInteractive: timing.domInteractive - timing.navigationStart,
                        responseEnd: timing.responseEnd - timing.requestStart
                    },
                    memory: performance.memory ? {
                        usedJSHeapSize: performance.memory.usedJSHeapSize,
                        totalJSHeapSize: performance.memory.totalJSHeapSize,
                        jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
                    } : null,
                    navigation: {
                        type: navigation.type,
                        redirectCount: navigation.redirectCount
                    }
                };
            """)
            
            # 测试多次导航的响应时间
            response_times = []
            test_urls = ['https://httpbin.org/html', 'https://www.example.com', 'https://httpbin.org/json']
            
            for url in test_urls:
                start_time = time.time()
                self.driver.get(url)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                response_time = time.time() - start_time
                response_times.append({
                    'url': url,
                    'response_time': f"{response_time:.3f}s"
                })
            
            metrics = {
                'performance_data': performance_data,
                'response_times': response_times,
                'average_response_time': f"{sum(float(rt['response_time'][:-1]) for rt in response_times) / len(response_times):.3f}s"
            }
            
            self.add_test_result(
                test_name, 
                'PASS', 
                "成功收集性能指标",
                metrics
            )
            return True
            
        except Exception as e:
            self.add_test_result(
                test_name, 
                'FAIL', 
                f"性能测试失败: {str(e)}",
                {'error': traceback.format_exc()}
            )
            return False
    
    def cleanup(self):
        """清理资源"""
        if self.driver:
            try:
                # 不关闭浏览器，只断开连接
                self.log("断开Selenium连接（保持浏览器运行）")
                # 注意：我们不调用 quit() 以保持浏览器继续运行
                self.driver = None
            except Exception as e:
                self.log(f"清理时出错: {str(e)}", 'WARNING')
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("="*60)
        self.log("开始Chrome Debug连接可行性测试")
        self.log("="*60)
        
        # 测试顺序很重要
        tests = [
            self.test_port_availability,
            self.test_selenium_connection,
            self.test_page_navigation,
            self.test_browser_control,
            self.test_performance_metrics
        ]
        
        for test in tests:
            try:
                test()
                time.sleep(1)  # 测试间隔
            except Exception as e:
                self.log(f"测试执行异常: {str(e)}", 'ERROR')
        
        # 清理
        self.cleanup()
        
        # 输出测试摘要
        self.print_summary()
        
        # 保存测试报告
        self.save_report()
        
        return self.test_results['summary']['failed'] == 0
    
    def print_summary(self):
        """打印测试摘要"""
        self.log("="*60)
        self.log("测试摘要")
        self.log("="*60)
        
        summary = self.test_results['summary']
        self.log(f"总测试数: {summary['total']}")
        self.log(f"✅ 通过: {summary['passed']}")
        self.log(f"❌ 失败: {summary['failed']}")
        
        success_rate = (summary['passed'] / summary['total'] * 100) if summary['total'] > 0 else 0
        self.log(f"成功率: {success_rate:.1f}%")
        
        if summary['failed'] > 0:
            self.log("\n失败的测试:")
            for test in self.test_results['tests']:
                if test['status'] == 'FAIL':
                    self.log(f"  - {test['name']}: {test['message']}")
    
    def save_report(self):
        """保存测试报告"""
        report_file = f"connection_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            self.log(f"\n测试报告已保存到: {report_file}")
        except Exception as e:
            self.log(f"保存报告失败: {str(e)}", 'ERROR')


def main():
    """主函数"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     Selenium + Chrome Debug 连接可行性测试               ║
    ╠══════════════════════════════════════════════════════════╣
    ║  此测试将验证:                                           ║
    ║  1. Chrome Debug端口(9222)的可访问性                     ║
    ║  2. Selenium连接到远程调试端口的能力                     ║
    ║  3. 基础的页面导航功能                                   ║
    ║  4. 浏览器控制能力                                       ║
    ║  5. 性能指标收集                                         ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    print("\n⚠️  测试前请确保:")
    print("1. Chrome已通过调试模式启动 (端口9222)")
    print("2. 使用命令: ./chrome-debug.sh")
    print("3. selenium包已安装: pip install selenium")
    print()
    
    input("按Enter键开始测试...")
    
    # 运行测试
    tester = ChromeDebugConnectionTest()
    success = tester.run_all_tests()
    
    # 返回状态码
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()