#!/usr/bin/env python3
"""
Selenium Session Reuse Test
验证会话复用和登录态保持功能

测试内容：
1. 模拟用户在Chrome Debug中手动登录
2. Selenium接管后验证登录态保持
3. 多次接管的稳定性测试
4. Cookie和LocalStorage持久化验证

作者: Archy-Principle-Architect
日期: 2025-09-25
"""

import sys
import time
import json
import traceback
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException

class SessionReuseTest:
    """会话复用测试类"""
    
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
        
        # 测试站点配置
        self.test_sites = {
            'github': {
                'url': 'https://github.com',
                'login_check': 'meta[name="user-login"]',
                'logged_in_element': 'summary[aria-label*="account"]',
                'name': 'GitHub'
            },
            'httpbin': {
                'url': 'https://httpbin.org/cookies',
                'cookie_test': True,
                'name': 'HTTPBin'
            },
            'example': {
                'url': 'https://www.example.com',
                'storage_test': True,
                'name': 'Example.com'
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
    
    def connect_to_chrome(self):
        """连接到Chrome Debug实例"""
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
            return True
        except Exception as e:
            self.log(f"连接Chrome失败: {str(e)}", 'ERROR')
            return False
    
    def disconnect_from_chrome(self):
        """断开Chrome连接（不关闭浏览器）"""
        if self.driver:
            # 保存当前会话信息
            session_info = {
                'session_id': self.driver.session_id,
                'window_handles': self.driver.window_handles
            }
            # 不调用quit()，只是释放driver对象
            self.driver = None
            return session_info
        return None
    
    def test_initial_state(self):
        """测试1: 记录初始状态"""
        test_name = "Initial State Recording"
        self.log(f"开始测试: {test_name}")
        
        if not self.connect_to_chrome():
            self.add_test_result(
                test_name, 
                'FAIL', 
                "无法连接到Chrome"
            )
            return False
        
        try:
            initial_state = {
                'windows': len(self.driver.window_handles),
                'current_url': self.driver.current_url,
                'cookies': {},
                'storage': {}
            }
            
            # 访问测试站点并设置一些状态
            for site_key, site_info in self.test_sites.items():
                self.driver.get(site_info['url'])
                time.sleep(2)
                
                # 获取Cookies
                cookies = self.driver.get_cookies()
                initial_state['cookies'][site_key] = cookies
                
                # 设置LocalStorage测试数据
                if site_info.get('storage_test'):
                    test_data = {
                        'test_key': f'test_value_{datetime.now().isoformat()}',
                        'session_id': 'selenium_test_123',
                        'timestamp': str(time.time())
                    }
                    
                    for key, value in test_data.items():
                        self.driver.execute_script(
                            f"localStorage.setItem('{key}', '{value}');"
                        )
                    
                    # 验证设置
                    stored_value = self.driver.execute_script(
                        "return localStorage.getItem('test_key');"
                    )
                    initial_state['storage'][site_key] = {
                        'set_data': test_data,
                        'verified': stored_value == test_data['test_key']
                    }
                
                # 设置测试Cookie
                if site_info.get('cookie_test'):
                    self.driver.add_cookie({
                        'name': 'selenium_test',
                        'value': f'test_{int(time.time())}',
                        'path': '/'
                    })
            
            self.add_test_result(
                test_name, 
                'PASS', 
                "成功记录初始状态",
                initial_state
            )
            
            # 断开连接
            session_info = self.disconnect_from_chrome()
            self.log(f"已断开连接，会话ID: {session_info['session_id']}")
            
            return initial_state
            
        except Exception as e:
            self.add_test_result(
                test_name, 
                'FAIL', 
                f"记录初始状态失败: {str(e)}",
                {'error': traceback.format_exc()}
            )
            return None
    
    def test_session_reuse(self, expected_state):
        """测试2: 重新连接并验证会话状态"""
        test_name = "Session Reuse Verification"
        self.log(f"开始测试: {test_name}")
        
        # 等待一段时间后重新连接
        self.log("等待3秒后重新连接...")
        time.sleep(3)
        
        if not self.connect_to_chrome():
            self.add_test_result(
                test_name, 
                'FAIL', 
                "无法重新连接到Chrome"
            )
            return False
        
        try:
            verification_results = {
                'cookies_preserved': {},
                'storage_preserved': {},
                'session_continuous': True
            }
            
            # 验证各站点的状态保持
            for site_key, site_info in self.test_sites.items():
                self.driver.get(site_info['url'])
                time.sleep(1)
                
                # 验证Cookies
                if site_key in expected_state.get('cookies', {}):
                    current_cookies = self.driver.get_cookies()
                    expected_cookies = expected_state['cookies'][site_key]
                    
                    # 检查关键cookies是否保持
                    if site_info.get('cookie_test'):
                        test_cookie = next(
                            (c for c in current_cookies if c['name'] == 'selenium_test'),
                            None
                        )
                        verification_results['cookies_preserved'][site_key] = {
                            'found': test_cookie is not None,
                            'value': test_cookie['value'] if test_cookie else None
                        }
                
                # 验证LocalStorage
                if site_info.get('storage_test') and site_key in expected_state.get('storage', {}):
                    stored_values = {}
                    for key in ['test_key', 'session_id', 'timestamp']:
                        value = self.driver.execute_script(
                            f"return localStorage.getItem('{key}');"
                        )
                        stored_values[key] = value
                    
                    expected_data = expected_state['storage'][site_key]['set_data']
                    verification_results['storage_preserved'][site_key] = {
                        'match': all(
                            stored_values.get(k) == v 
                            for k, v in expected_data.items()
                        ),
                        'stored_values': stored_values,
                        'expected_values': expected_data
                    }
            
            # 判断整体结果
            all_cookies_ok = all(
                v.get('found', True) 
                for v in verification_results['cookies_preserved'].values()
            )
            all_storage_ok = all(
                v.get('match', True) 
                for v in verification_results['storage_preserved'].values()
            )
            
            if all_cookies_ok and all_storage_ok:
                self.add_test_result(
                    test_name, 
                    'PASS', 
                    "会话状态完全保持",
                    verification_results
                )
                return True
            else:
                self.add_test_result(
                    test_name, 
                    'PARTIAL', 
                    "部分会话状态丢失",
                    verification_results
                )
                return False
                
        except Exception as e:
            self.add_test_result(
                test_name, 
                'FAIL', 
                f"会话验证失败: {str(e)}",
                {'error': traceback.format_exc()}
            )
            return False
    
    def test_multiple_reconnections(self, num_reconnects=5):
        """测试3: 多次重连稳定性测试"""
        test_name = "Multiple Reconnection Stability"
        self.log(f"开始测试: {test_name} (重连{num_reconnects}次)")
        
        reconnection_results = []
        
        for i in range(num_reconnects):
            self.log(f"第 {i+1}/{num_reconnects} 次重连测试")
            
            # 连接
            connect_start = time.time()
            connect_success = self.connect_to_chrome()
            connect_time = time.time() - connect_start
            
            if not connect_success:
                reconnection_results.append({
                    'attempt': i + 1,
                    'success': False,
                    'error': "连接失败"
                })
                continue
            
            try:
                # 执行一些操作
                self.driver.get('https://httpbin.org/uuid')
                uuid_element = self.driver.find_element(By.TAG_NAME, 'body')
                uuid_text = uuid_element.text
                
                # 获取当前状态
                current_state = {
                    'windows': len(self.driver.window_handles),
                    'cookies': len(self.driver.get_cookies()),
                    'url': self.driver.current_url,
                    'uuid': uuid_text
                }
                
                reconnection_results.append({
                    'attempt': i + 1,
                    'success': True,
                    'connect_time': f"{connect_time:.3f}s",
                    'state': current_state
                })
                
                # 断开连接
                self.disconnect_from_chrome()
                
                # 短暂等待
                time.sleep(1)
                
            except Exception as e:
                reconnection_results.append({
                    'attempt': i + 1,
                    'success': False,
                    'error': str(e)
                })
        
        # 统计结果
        successful_reconnects = sum(1 for r in reconnection_results if r['success'])
        success_rate = (successful_reconnects / num_reconnects) * 100
        
        if success_rate == 100:
            self.add_test_result(
                test_name, 
                'PASS', 
                f"所有{num_reconnects}次重连都成功",
                {
                    'total_attempts': num_reconnects,
                    'successful': successful_reconnects,
                    'success_rate': f"{success_rate:.1f}%",
                    'details': reconnection_results
                }
            )
            return True
        elif success_rate >= 80:
            self.add_test_result(
                test_name, 
                'PARTIAL', 
                f"重连成功率: {success_rate:.1f}%",
                {
                    'total_attempts': num_reconnects,
                    'successful': successful_reconnects,
                    'success_rate': f"{success_rate:.1f}%",
                    'details': reconnection_results
                }
            )
            return False
        else:
            self.add_test_result(
                test_name, 
                'FAIL', 
                f"重连成功率过低: {success_rate:.1f}%",
                {
                    'total_attempts': num_reconnects,
                    'successful': successful_reconnects,
                    'success_rate': f"{success_rate:.1f}%",
                    'details': reconnection_results
                }
            )
            return False
    
    def test_login_state_persistence(self):
        """测试4: 登录态持久化测试（手动）"""
        test_name = "Login State Persistence"
        self.log(f"开始测试: {test_name}")
        
        print("\n" + "="*60)
        print("手动登录测试")
        print("="*60)
        print("请在Chrome浏览器中手动执行以下操作：")
        print("1. 访问一个需要登录的网站（如GitHub、Google等）")
        print("2. 完成登录流程")
        print("3. 确保登录成功")
        print("="*60)
        
        input("\n完成登录后，按Enter键继续测试...")
        
        if not self.connect_to_chrome():
            self.add_test_result(
                test_name, 
                'FAIL', 
                "无法连接到Chrome"
            )
            return False
        
        try:
            # 获取当前页面信息
            current_url = self.driver.current_url
            page_title = self.driver.title
            cookies = self.driver.get_cookies()
            
            # 查找可能的登录标识
            login_indicators = {
                'cookies': [],
                'elements': []
            }
            
            # 检查常见的登录Cookie
            login_cookie_patterns = [
                'session', 'token', 'auth', 'login', 
                'user', 'logged_in', 'sid', 'ssid'
            ]
            
            for cookie in cookies:
                cookie_name = cookie['name'].lower()
                if any(pattern in cookie_name for pattern in login_cookie_patterns):
                    login_indicators['cookies'].append({
                        'name': cookie['name'],
                        'domain': cookie['domain'],
                        'httpOnly': cookie.get('httpOnly', False),
                        'secure': cookie.get('secure', False)
                    })
            
            # 断开并重连
            self.log("断开连接...")
            self.disconnect_from_chrome()
            
            time.sleep(3)
            
            self.log("重新连接...")
            if not self.connect_to_chrome():
                self.add_test_result(
                    test_name, 
                    'FAIL', 
                    "无法重新连接"
                )
                return False
            
            # 返回原页面
            self.driver.get(current_url)
            time.sleep(2)
            
            # 验证登录状态
            new_cookies = self.driver.get_cookies()
            
            # 检查登录Cookie是否保持
            preserved_cookies = []
            for indicator in login_indicators['cookies']:
                found = any(
                    c['name'] == indicator['name'] 
                    for c in new_cookies
                )
                if found:
                    preserved_cookies.append(indicator['name'])
            
            preservation_rate = (
                len(preserved_cookies) / len(login_indicators['cookies']) * 100
                if login_indicators['cookies'] else 0
            )
            
            result_details = {
                'url': current_url,
                'title': page_title,
                'login_cookies_found': len(login_indicators['cookies']),
                'cookies_preserved': preserved_cookies,
                'preservation_rate': f"{preservation_rate:.1f}%",
                'total_cookies_before': len(cookies),
                'total_cookies_after': len(new_cookies)
            }
            
            if preservation_rate >= 80 or len(preserved_cookies) > 0:
                self.add_test_result(
                    test_name, 
                    'PASS', 
                    f"登录态保持成功 (保持率: {preservation_rate:.1f}%)",
                    result_details
                )
                return True
            else:
                self.add_test_result(
                    test_name, 
                    'WARN', 
                    "无法验证登录态（可能未登录或站点不适用）",
                    result_details
                )
                return False
                
        except Exception as e:
            self.add_test_result(
                test_name, 
                'FAIL', 
                f"登录态测试失败: {str(e)}",
                {'error': traceback.format_exc()}
            )
            return False
    
    def test_concurrent_access(self):
        """测试5: 并发访问测试"""
        test_name = "Concurrent Access Test"
        self.log(f"开始测试: {test_name}")
        
        try:
            # 创建两个连接
            self.log("创建第一个连接...")
            chrome_options1 = Options()
            chrome_options1.add_experimental_option(
                "debuggerAddress", 
                f"{self.debug_host}:{self.debug_port}"
            )
            driver1 = webdriver.Chrome(options=chrome_options1)
            
            self.log("创建第二个连接...")
            chrome_options2 = Options()
            chrome_options2.add_experimental_option(
                "debuggerAddress", 
                f"{self.debug_host}:{self.debug_port}"
            )
            driver2 = webdriver.Chrome(options=chrome_options2)
            
            # 测试两个连接的独立性
            driver1.get('https://httpbin.org/uuid')
            uuid1 = driver1.find_element(By.TAG_NAME, 'body').text
            
            driver2.get('https://httpbin.org/uuid')
            uuid2 = driver2.find_element(By.TAG_NAME, 'body').text
            
            # 验证两个连接获取到不同的UUID（说明是独立的请求）
            concurrent_test_passed = uuid1 != uuid2
            
            # 清理
            driver1 = None
            driver2 = None
            
            if concurrent_test_passed:
                self.add_test_result(
                    test_name, 
                    'PASS', 
                    "支持多个Selenium实例并发连接",
                    {
                        'uuid1': uuid1[:50],
                        'uuid2': uuid2[:50],
                        'independent': True
                    }
                )
                return True
            else:
                self.add_test_result(
                    test_name, 
                    'WARN', 
                    "并发连接可能存在问题",
                    {
                        'uuid1': uuid1[:50],
                        'uuid2': uuid2[:50],
                        'independent': False
                    }
                )
                return False
                
        except Exception as e:
            self.add_test_result(
                test_name, 
                'FAIL', 
                f"并发访问测试失败: {str(e)}",
                {'error': traceback.format_exc()}
            )
            return False
    
    def cleanup(self):
        """清理资源"""
        if self.driver:
            try:
                self.log("断开Selenium连接（保持浏览器运行）")
                self.driver = None
            except Exception as e:
                self.log(f"清理时出错: {str(e)}", 'WARNING')
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("="*60)
        self.log("开始会话复用可行性测试")
        self.log("="*60)
        
        # 测试1: 记录初始状态
        initial_state = self.test_initial_state()
        time.sleep(2)
        
        # 测试2: 会话复用验证
        if initial_state:
            self.test_session_reuse(initial_state)
            time.sleep(2)
        
        # 测试3: 多次重连稳定性
        self.test_multiple_reconnections(5)
        time.sleep(2)
        
        # 测试4: 登录态持久化（需要手动操作）
        self.test_login_state_persistence()
        time.sleep(2)
        
        # 测试5: 并发访问
        self.test_concurrent_access()
        
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
                if test['status'] in ['FAIL', 'PARTIAL']:
                    self.log(f"  - {test['name']}: {test['message']}")
    
    def save_report(self):
        """保存测试报告"""
        report_file = f"session_reuse_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
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
    ║        Selenium 会话复用与登录态保持测试                  ║
    ╠══════════════════════════════════════════════════════════╣
    ║  此测试将验证:                                           ║
    ║  1. Chrome Debug会话的状态记录                           ║
    ║  2. 断开重连后的会话状态保持                             ║
    ║  3. 多次重连的稳定性                                     ║
    ║  4. 登录态的持久化（需要手动操作）                       ║
    ║  5. 并发访问的支持                                       ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    print("\n⚠️  测试前请确保:")
    print("1. Chrome已通过调试模式启动 (端口9222)")
    print("2. 使用命令: ./chrome-debug.sh")
    print("3. selenium包已安装: pip install selenium")
    print()
    
    input("按Enter键开始测试...")
    
    # 运行测试
    tester = SessionReuseTest()
    success = tester.run_all_tests()
    
    # 返回状态码
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()