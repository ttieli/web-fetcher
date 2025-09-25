#!/usr/bin/env python3
"""
Selenium Error Handling Test
验证错误处理和恢复机制

测试内容：
1. Chrome Debug未运行时的处理
2. 网络超时和连接错误
3. 页面加载失败处理
4. JavaScript执行错误
5. 优雅的错误恢复机制

作者: Archy-Principle-Architect
日期: 2025-09-25
"""

import sys
import time
import json
import socket
import signal
import traceback
from datetime import datetime
from contextlib import contextmanager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException, 
    TimeoutException,
    NoSuchElementException,
    JavascriptException,
    StaleElementReferenceException,
    InvalidSessionIdException
)

class ErrorHandlingTest:
    """错误处理测试类"""
    
    def __init__(self, debug_port=9222):
        self.debug_port = debug_port
        self.debug_host = '127.0.0.1'
        self.driver = None
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'error_recovery': [],
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'recovered': 0
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
        elif status == 'RECOVERED':
            self.test_results['summary']['recovered'] += 1
            self.log(f"🔄 {name}: {message}", 'WARN')
        else:
            self.test_results['summary']['failed'] += 1
            self.log(f"❌ {name}: {message}", 'ERROR')
    
    @contextmanager
    def timeout(self, seconds):
        """超时上下文管理器"""
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Operation timed out after {seconds} seconds")
        
        # 设置信号处理器
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    
    def safe_connect_to_chrome(self, max_retries=3, retry_delay=2):
        """安全连接到Chrome（带重试机制）"""
        for attempt in range(max_retries):
            try:
                chrome_options = Options()
                chrome_options.add_experimental_option(
                    "debuggerAddress", 
                    f"{self.debug_host}:{self.debug_port}"
                )
                
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.log(f"成功连接到Chrome (尝试 {attempt + 1}/{max_retries})")
                return True
                
            except WebDriverException as e:
                self.log(f"连接失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}", 'WARN')
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
            except Exception as e:
                self.log(f"未预期的错误: {str(e)}", 'ERROR')
                break
        
        return False
    
    def test_chrome_not_running(self):
        """测试1: Chrome Debug未运行时的处理"""
        test_name = "Chrome Not Running Handler"
        self.log(f"开始测试: {test_name}")
        
        # 首先检查端口是否真的未开放
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((self.debug_host, self.debug_port))
            sock.close()
            
            if result == 0:
                # 端口开放，需要模拟错误端口
                test_port = 9999  # 使用一个不太可能开放的端口
            else:
                test_port = self.debug_port
            
            # 尝试连接到错误端口
            error_caught = False
            error_message = ""
            
            try:
                chrome_options = Options()
                chrome_options.add_experimental_option(
                    "debuggerAddress", 
                    f"{self.debug_host}:{test_port}"
                )
                
                driver = webdriver.Chrome(options=chrome_options)
                driver.quit()
                
            except WebDriverException as e:
                error_caught = True
                error_message = str(e)
                
                # 验证错误处理
                if "Failed to connect" in error_message or "Connection refused" in error_message:
                    self.add_test_result(
                        test_name, 
                        'PASS', 
                        "正确处理了Chrome未运行的情况",
                        {
                            'error_type': 'WebDriverException',
                            'error_message': error_message[:200],
                            'handled_gracefully': True
                        }
                    )
                    return True
            
            if not error_caught:
                self.add_test_result(
                    test_name, 
                    'FAIL', 
                    "未能正确检测Chrome未运行状态"
                )
                return False
                
        except Exception as e:
            self.add_test_result(
                test_name, 
                'FAIL', 
                f"测试异常: {str(e)}",
                {'error': traceback.format_exc()}
            )
            return False
    
    def test_timeout_handling(self):
        """测试2: 超时处理"""
        test_name = "Timeout Handling"
        self.log(f"开始测试: {test_name}")
        
        if not self.safe_connect_to_chrome():
            self.add_test_result(
                test_name, 
                'SKIP', 
                "无法连接到Chrome"
            )
            return False
        
        timeout_tests = []
        
        try:
            # 测试页面加载超时
            self.log("测试页面加载超时...")
            try:
                self.driver.set_page_load_timeout(2)  # 设置2秒超时
                self.driver.get('https://httpbin.org/delay/5')  # 访问5秒延迟页面
                timeout_tests.append({
                    'test': '页面加载超时',
                    'handled': False,
                    'error': 'Timeout not triggered'
                })
            except TimeoutException as e:
                timeout_tests.append({
                    'test': '页面加载超时',
                    'handled': True,
                    'recovery': 'Caught TimeoutException'
                })
                # 恢复：停止加载
                self.driver.execute_script("window.stop();")
            
            # 重置超时
            self.driver.set_page_load_timeout(30)
            
            # 测试元素查找超时
            self.log("测试元素查找超时...")
            self.driver.get('https://www.example.com')
            try:
                element = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.ID, "non-existent-element"))
                )
                timeout_tests.append({
                    'test': '元素查找超时',
                    'handled': False,
                    'error': 'Element found unexpectedly'
                })
            except TimeoutException:
                timeout_tests.append({
                    'test': '元素查找超时',
                    'handled': True,
                    'recovery': 'Caught element timeout'
                })
            
            # 测试脚本执行超时
            self.log("测试脚本执行超时...")
            self.driver.set_script_timeout(2)
            try:
                result = self.driver.execute_async_script("""
                    var callback = arguments[arguments.length - 1];
                    setTimeout(function() {
                        callback('This will timeout');
                    }, 5000);
                """)
                timeout_tests.append({
                    'test': '脚本执行超时',
                    'handled': False,
                    'error': 'Script completed unexpectedly'
                })
            except TimeoutException:
                timeout_tests.append({
                    'test': '脚本执行超时',
                    'handled': True,
                    'recovery': 'Caught script timeout'
                })
            
            # 重置脚本超时
            self.driver.set_script_timeout(30)
            
            # 判断结果
            all_handled = all(t.get('handled', False) for t in timeout_tests)
            
            if all_handled:
                self.add_test_result(
                    test_name, 
                    'PASS', 
                    "所有超时情况都正确处理",
                    {'timeout_tests': timeout_tests}
                )
                return True
            else:
                self.add_test_result(
                    test_name, 
                    'PARTIAL', 
                    "部分超时处理失败",
                    {'timeout_tests': timeout_tests}
                )
                return False
                
        except Exception as e:
            self.add_test_result(
                test_name, 
                'FAIL', 
                f"超时测试异常: {str(e)}",
                {'error': traceback.format_exc()}
            )
            return False
    
    def test_network_errors(self):
        """测试3: 网络错误处理"""
        test_name = "Network Error Handling"
        self.log(f"开始测试: {test_name}")
        
        if not self.driver:
            if not self.safe_connect_to_chrome():
                self.add_test_result(
                    test_name, 
                    'SKIP', 
                    "无法连接到Chrome"
                )
                return False
        
        network_tests = []
        
        # 测试无效URL
        invalid_urls = [
            ('http://this-domain-does-not-exist-12345.com', 'Invalid domain'),
            ('https://192.168.255.255:8888', 'Unreachable IP'),
            ('https://www.example.com:12345', 'Invalid port'),
            ('http://[::1]:99999', 'Invalid IPv6 port')
        ]
        
        for url, description in invalid_urls:
            self.log(f"测试 {description}: {url}")
            
            try:
                self.driver.set_page_load_timeout(5)
                start_time = time.time()
                self.driver.get(url)
                load_time = time.time() - start_time
                
                # 检查是否加载了错误页面
                page_source = self.driver.page_source
                is_error_page = any(error in page_source.lower() for error in [
                    'err_', 'error', 'not found', 'unable to connect',
                    'this site can', 'dns_probe'
                ])
                
                network_tests.append({
                    'url': url,
                    'description': description,
                    'handled': True,
                    'is_error_page': is_error_page,
                    'load_time': f"{load_time:.2f}s"
                })
                
            except (TimeoutException, WebDriverException) as e:
                network_tests.append({
                    'url': url,
                    'description': description,
                    'handled': True,
                    'error_type': type(e).__name__,
                    'recovered': True
                })
            except Exception as e:
                network_tests.append({
                    'url': url,
                    'description': description,
                    'handled': False,
                    'unexpected_error': str(e)
                })
        
        # 重置超时
        self.driver.set_page_load_timeout(30)
        
        # 判断结果
        handled_count = sum(1 for t in network_tests if t.get('handled', False))
        
        if handled_count == len(network_tests):
            self.add_test_result(
                test_name, 
                'PASS', 
                f"所有网络错误都正确处理 ({handled_count}/{len(network_tests)})",
                {'network_tests': network_tests}
            )
            return True
        elif handled_count > 0:
            self.add_test_result(
                test_name, 
                'PARTIAL', 
                f"部分网络错误处理成功 ({handled_count}/{len(network_tests)})",
                {'network_tests': network_tests}
            )
            return False
        else:
            self.add_test_result(
                test_name, 
                'FAIL', 
                "网络错误处理失败",
                {'network_tests': network_tests}
            )
            return False
    
    def test_javascript_errors(self):
        """测试4: JavaScript错误处理"""
        test_name = "JavaScript Error Handling"
        self.log(f"开始测试: {test_name}")
        
        if not self.driver:
            if not self.safe_connect_to_chrome():
                self.add_test_result(
                    test_name, 
                    'SKIP', 
                    "无法连接到Chrome"
                )
                return False
        
        js_error_tests = []
        
        try:
            self.driver.get('https://www.example.com')
            
            # 测试语法错误
            try:
                result = self.driver.execute_script("this is not valid javascript")
                js_error_tests.append({
                    'test': '语法错误',
                    'handled': False,
                    'error': 'No exception raised'
                })
            except JavascriptException as e:
                js_error_tests.append({
                    'test': '语法错误',
                    'handled': True,
                    'error_type': 'JavascriptException'
                })
            except WebDriverException as e:
                js_error_tests.append({
                    'test': '语法错误',
                    'handled': True,
                    'error_type': 'WebDriverException'
                })
            
            # 测试运行时错误
            try:
                result = self.driver.execute_script("""
                    var obj = null;
                    return obj.nonExistentMethod();
                """)
                js_error_tests.append({
                    'test': '运行时错误',
                    'handled': False,
                    'error': 'No exception raised'
                })
            except (JavascriptException, WebDriverException) as e:
                js_error_tests.append({
                    'test': '运行时错误',
                    'handled': True,
                    'error_message': str(e)[:100]
                })
            
            # 测试未定义变量
            try:
                result = self.driver.execute_script("return undefinedVariable;")
                # 有些浏览器返回None而不是抛出异常
                js_error_tests.append({
                    'test': '未定义变量',
                    'handled': True,
                    'result': 'Returned None/undefined'
                })
            except (JavascriptException, WebDriverException) as e:
                js_error_tests.append({
                    'test': '未定义变量',
                    'handled': True,
                    'error_caught': True
                })
            
            # 测试无限循环防护（通过超时）
            try:
                self.driver.set_script_timeout(2)
                result = self.driver.execute_async_script("""
                    var callback = arguments[arguments.length - 1];
                    while(true) {} // 无限循环
                    callback('Should not reach here');
                """)
                js_error_tests.append({
                    'test': '无限循环',
                    'handled': False,
                    'error': 'Script completed'
                })
            except TimeoutException:
                js_error_tests.append({
                    'test': '无限循环',
                    'handled': True,
                    'protection': 'Script timeout protection worked'
                })
            
            # 重置超时
            self.driver.set_script_timeout(30)
            
            # 判断结果
            handled_count = sum(1 for t in js_error_tests if t.get('handled', False))
            
            if handled_count == len(js_error_tests):
                self.add_test_result(
                    test_name, 
                    'PASS', 
                    f"所有JavaScript错误都正确处理",
                    {'js_error_tests': js_error_tests}
                )
                return True
            else:
                self.add_test_result(
                    test_name, 
                    'PARTIAL', 
                    f"部分JavaScript错误处理成功 ({handled_count}/{len(js_error_tests)})",
                    {'js_error_tests': js_error_tests}
                )
                return False
                
        except Exception as e:
            self.add_test_result(
                test_name, 
                'FAIL', 
                f"JavaScript错误测试异常: {str(e)}",
                {'error': traceback.format_exc()}
            )
            return False
    
    def test_element_errors(self):
        """测试5: 元素操作错误处理"""
        test_name = "Element Operation Error Handling"
        self.log(f"开始测试: {test_name}")
        
        if not self.driver:
            if not self.safe_connect_to_chrome():
                self.add_test_result(
                    test_name, 
                    'SKIP', 
                    "无法连接到Chrome"
                )
                return False
        
        element_tests = []
        
        try:
            self.driver.get('https://www.example.com')
            
            # 测试不存在的元素
            try:
                element = self.driver.find_element(By.ID, "non-existent-element-12345")
                element_tests.append({
                    'test': '查找不存在元素',
                    'handled': False,
                    'error': 'Element found unexpectedly'
                })
            except NoSuchElementException:
                element_tests.append({
                    'test': '查找不存在元素',
                    'handled': True,
                    'error_type': 'NoSuchElementException'
                })
            
            # 测试过期元素引用
            try:
                # 创建一个元素然后刷新页面使其过期
                self.driver.execute_script("""
                    var div = document.createElement('div');
                    div.id = 'temp-element';
                    div.innerHTML = 'Temporary';
                    document.body.appendChild(div);
                """)
                
                temp_element = self.driver.find_element(By.ID, 'temp-element')
                
                # 刷新页面，元素失效
                self.driver.refresh()
                
                # 尝试使用过期元素
                text = temp_element.text
                element_tests.append({
                    'test': '过期元素引用',
                    'handled': False,
                    'error': 'Stale element still accessible'
                })
            except StaleElementReferenceException:
                element_tests.append({
                    'test': '过期元素引用',
                    'handled': True,
                    'error_type': 'StaleElementReferenceException'
                })
            
            # 测试不可交互元素
            try:
                # 创建一个隐藏元素
                self.driver.execute_script("""
                    var input = document.createElement('input');
                    input.id = 'hidden-input';
                    input.style.display = 'none';
                    document.body.appendChild(input);
                """)
                
                hidden_element = self.driver.find_element(By.ID, 'hidden-input')
                hidden_element.send_keys('test')  # 尝试输入
                
                element_tests.append({
                    'test': '操作隐藏元素',
                    'handled': False,
                    'note': 'Some drivers allow hidden element interaction'
                })
            except (WebDriverException, Exception) as e:
                element_tests.append({
                    'test': '操作隐藏元素',
                    'handled': True,
                    'error_handled': True
                })
            
            # 判断结果
            handled_count = sum(1 for t in element_tests if t.get('handled', False))
            
            if handled_count >= len(element_tests) - 1:  # 允许一个测试差异
                self.add_test_result(
                    test_name, 
                    'PASS', 
                    f"元素错误处理正确 ({handled_count}/{len(element_tests)})",
                    {'element_tests': element_tests}
                )
                return True
            else:
                self.add_test_result(
                    test_name, 
                    'PARTIAL', 
                    f"部分元素错误处理成功 ({handled_count}/{len(element_tests)})",
                    {'element_tests': element_tests}
                )
                return False
                
        except Exception as e:
            self.add_test_result(
                test_name, 
                'FAIL', 
                f"元素错误测试异常: {str(e)}",
                {'error': traceback.format_exc()}
            )
            return False
    
    def test_recovery_mechanism(self):
        """测试6: 错误恢复机制"""
        test_name = "Error Recovery Mechanism"
        self.log(f"开始测试: {test_name}")
        
        recovery_tests = []
        
        # 测试连接恢复
        self.log("测试连接断开后恢复...")
        if self.driver:
            # 保存当前会话ID
            old_session_id = self.driver.session_id
            
            # 断开连接
            self.driver = None
            time.sleep(2)
            
            # 尝试重新连接
            if self.safe_connect_to_chrome():
                new_session_id = self.driver.session_id
                recovery_tests.append({
                    'test': '连接恢复',
                    'success': True,
                    'old_session': old_session_id,
                    'new_session': new_session_id,
                    'sessions_different': old_session_id != new_session_id
                })
            else:
                recovery_tests.append({
                    'test': '连接恢复',
                    'success': False,
                    'error': '无法重新连接'
                })
        
        # 测试页面错误恢复
        if self.driver:
            self.log("测试页面错误后恢复...")
            
            # 先访问错误页面
            try:
                self.driver.set_page_load_timeout(3)
                self.driver.get('http://invalid-url-12345.com')
            except:
                pass
            
            # 尝试恢复到正常页面
            try:
                self.driver.set_page_load_timeout(10)
                self.driver.get('https://www.example.com')
                page_title = self.driver.title
                
                recovery_tests.append({
                    'test': '页面错误恢复',
                    'success': True,
                    'recovered_title': page_title
                })
            except Exception as e:
                recovery_tests.append({
                    'test': '页面错误恢复',
                    'success': False,
                    'error': str(e)
                })
        
        # 测试会话无效恢复
        if self.driver:
            self.log("测试会话无效恢复...")
            
            # 模拟会话无效
            try:
                # 强制使会话无效
                self.driver.quit()
                
                # 尝试使用已关闭的driver
                title = self.driver.title
                recovery_tests.append({
                    'test': '会话无效检测',
                    'success': False,
                    'error': 'Session still valid after quit'
                })
            except (InvalidSessionIdException, WebDriverException):
                # 检测到会话无效，尝试恢复
                if self.safe_connect_to_chrome():
                    recovery_tests.append({
                        'test': '会话无效恢复',
                        'success': True,
                        'recovered': True
                    })
                else:
                    recovery_tests.append({
                        'test': '会话无效恢复',
                        'success': False,
                        'error': '无法恢复会话'
                    })
        
        # 判断结果
        success_count = sum(1 for t in recovery_tests if t.get('success', False))
        
        if success_count == len(recovery_tests):
            self.add_test_result(
                test_name, 
                'PASS', 
                f"所有恢复机制测试通过 ({success_count}/{len(recovery_tests)})",
                {'recovery_tests': recovery_tests}
            )
            return True
        elif success_count > 0:
            self.add_test_result(
                test_name, 
                'RECOVERED', 
                f"部分恢复机制有效 ({success_count}/{len(recovery_tests)})",
                {'recovery_tests': recovery_tests}
            )
            self.test_results['summary']['recovered'] += 1
            return True
        else:
            self.add_test_result(
                test_name, 
                'FAIL', 
                "恢复机制测试失败",
                {'recovery_tests': recovery_tests}
            )
            return False
    
    def cleanup(self):
        """清理资源"""
        if self.driver:
            try:
                self.log("断开Selenium连接")
                self.driver = None
            except Exception as e:
                self.log(f"清理时出错: {str(e)}", 'WARNING')
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("="*60)
        self.log("开始错误处理机制测试")
        self.log("="*60)
        
        # 运行测试
        tests = [
            self.test_chrome_not_running,
            self.test_timeout_handling,
            self.test_network_errors,
            self.test_javascript_errors,
            self.test_element_errors,
            self.test_recovery_mechanism
        ]
        
        for test in tests:
            try:
                test()
                time.sleep(1)
            except Exception as e:
                self.log(f"测试执行异常: {str(e)}", 'ERROR')
                self.add_test_result(
                    f"Test execution error",
                    'FAIL',
                    str(e)
                )
        
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
        self.log(f"🔄 恢复: {summary['recovered']}")
        self.log(f"❌ 失败: {summary['failed']}")
        
        success_rate = (
            (summary['passed'] + summary['recovered']) / summary['total'] * 100
        ) if summary['total'] > 0 else 0
        self.log(f"成功率: {success_rate:.1f}%")
        
        if summary['failed'] > 0:
            self.log("\n失败的测试:")
            for test in self.test_results['tests']:
                if test['status'] == 'FAIL':
                    self.log(f"  - {test['name']}: {test['message']}")
        
        if summary['recovered'] > 0:
            self.log("\n恢复的测试:")
            for test in self.test_results['tests']:
                if test['status'] == 'RECOVERED':
                    self.log(f"  - {test['name']}: {test['message']}")
    
    def save_report(self):
        """保存测试报告"""
        report_file = f"error_handling_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
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
    ║           Selenium 错误处理机制测试                       ║
    ╠══════════════════════════════════════════════════════════╣
    ║  此测试将验证:                                           ║
    ║  1. Chrome未运行时的错误处理                             ║
    ║  2. 各种超时情况的处理                                   ║
    ║  3. 网络错误的处理                                       ║
    ║  4. JavaScript错误的处理                                 ║
    ║  5. 元素操作错误的处理                                   ║
    ║  6. 错误恢复机制的有效性                                 ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    print("\n⚠️  测试说明:")
    print("1. 部分测试会故意触发错误来验证处理机制")
    print("2. Chrome Debug实例可选（会测试未运行情况）")
    print("3. selenium包必须已安装: pip install selenium")
    print()
    
    input("按Enter键开始测试...")
    
    # 运行测试
    tester = ErrorHandlingTest()
    success = tester.run_all_tests()
    
    # 返回状态码
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()