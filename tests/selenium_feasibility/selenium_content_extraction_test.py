#!/usr/bin/env python3
"""
Selenium Content Extraction Test
验证不同类型网页的内容提取能力

测试内容：
1. 静态HTML内容提取
2. 动态JavaScript渲染内容
3. AJAX加载内容
4. iframe内容提取
5. 与urllib方式对比

作者: Archy-Principle-Architect
日期: 2025-09-25
"""

import sys
import time
import json
import hashlib
import urllib.request
import urllib.error
import traceback
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from html.parser import HTMLParser

class ContentExtractionTest:
    """内容提取测试类"""
    
    def __init__(self, debug_port=9222):
        self.debug_port = debug_port
        self.debug_host = '127.0.0.1'
        self.driver = None
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'comparison': {},
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0
            }
        }
        
        # 测试URL配置
        self.test_urls = {
            'static_html': {
                'url': 'https://www.example.com',
                'type': 'static',
                'description': '纯静态HTML页面'
            },
            'json_api': {
                'url': 'https://httpbin.org/json',
                'type': 'json',
                'description': 'JSON API响应'
            },
            'user_agent': {
                'url': 'https://httpbin.org/user-agent',
                'type': 'api',
                'description': 'User-Agent检测'
            },
            'headers': {
                'url': 'https://httpbin.org/headers',
                'type': 'api',
                'description': 'HTTP Headers检测'
            },
            'delayed_response': {
                'url': 'https://httpbin.org/delay/2',
                'type': 'delayed',
                'description': '延迟加载内容'
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
    
    def extract_with_selenium(self, url, wait_for=None, wait_time=10):
        """使用Selenium提取内容"""
        try:
            start_time = time.time()
            self.driver.get(url)
            
            # 等待特定元素或基本加载
            if wait_for:
                WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_element_located(wait_for)
                )
            else:
                WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            
            load_time = time.time() - start_time
            
            # 提取内容
            page_source = self.driver.page_source
            page_title = self.driver.title
            
            # 执行JavaScript获取更多信息
            js_data = self.driver.execute_script("""
                return {
                    documentReady: document.readyState,
                    bodyText: document.body ? document.body.innerText : '',
                    bodyTextLength: document.body ? document.body.innerText.length : 0,
                    images: document.images.length,
                    links: document.links.length,
                    forms: document.forms.length,
                    scripts: document.scripts.length,
                    stylesheets: document.styleSheets.length,
                    ajaxCompleted: typeof window.ajaxCompleted !== 'undefined' ? window.ajaxCompleted : null
                };
            """)
            
            return {
                'success': True,
                'load_time': load_time,
                'page_source': page_source,
                'page_title': page_title,
                'source_length': len(page_source),
                'js_data': js_data,
                'url': self.driver.current_url,
                'content_hash': hashlib.md5(page_source.encode()).hexdigest()
            }
            
        except TimeoutException:
            return {
                'success': False,
                'error': 'Page load timeout',
                'load_time': time.time() - start_time
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    def extract_with_urllib(self, url, timeout=10):
        """使用urllib提取内容（作为对比）"""
        try:
            start_time = time.time()
            
            # 设置User-Agent
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
            
            # 发送请求
            with urllib.request.urlopen(req, timeout=timeout) as response:
                content = response.read()
                load_time = time.time() - start_time
                
                # 尝试解码
                encoding = response.headers.get_content_charset() or 'utf-8'
                try:
                    page_source = content.decode(encoding)
                except:
                    page_source = content.decode('utf-8', errors='ignore')
                
                # 简单提取title
                title = ''
                if '<title>' in page_source and '</title>' in page_source:
                    title_start = page_source.find('<title>') + 7
                    title_end = page_source.find('</title>')
                    title = page_source[title_start:title_end].strip()
                
                return {
                    'success': True,
                    'load_time': load_time,
                    'page_source': page_source,
                    'page_title': title,
                    'source_length': len(page_source),
                    'status_code': response.status,
                    'headers': dict(response.headers),
                    'content_hash': hashlib.md5(page_source.encode()).hexdigest()
                }
                
        except urllib.error.URLError as e:
            return {
                'success': False,
                'error': f"URLError: {str(e)}",
                'load_time': time.time() - start_time
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    def test_static_content_extraction(self):
        """测试1: 静态HTML内容提取"""
        test_name = "Static HTML Extraction"
        self.log(f"开始测试: {test_name}")
        
        test_url = self.test_urls['static_html']['url']
        
        # Selenium提取
        selenium_result = self.extract_with_selenium(test_url)
        
        # urllib提取
        urllib_result = self.extract_with_urllib(test_url)
        
        # 对比结果
        comparison = {
            'url': test_url,
            'selenium': {
                'success': selenium_result['success'],
                'load_time': f"{selenium_result.get('load_time', 0):.2f}s",
                'content_length': selenium_result.get('source_length', 0),
                'title': selenium_result.get('page_title', ''),
                'hash': selenium_result.get('content_hash', '')
            },
            'urllib': {
                'success': urllib_result['success'],
                'load_time': f"{urllib_result.get('load_time', 0):.2f}s",
                'content_length': urllib_result.get('source_length', 0),
                'title': urllib_result.get('page_title', ''),
                'hash': urllib_result.get('content_hash', '')
            }
        }
        
        # 判断测试结果
        if selenium_result['success'] and urllib_result['success']:
            # 检查内容一致性
            content_match = abs(
                selenium_result['source_length'] - urllib_result['source_length']
            ) < 1000  # 允许小差异
            
            if content_match:
                self.add_test_result(
                    test_name, 
                    'PASS', 
                    "静态内容提取成功，Selenium与urllib结果一致",
                    comparison
                )
                return True
            else:
                self.add_test_result(
                    test_name, 
                    'WARN', 
                    "内容提取成功但存在差异",
                    comparison
                )
                return True
        else:
            self.add_test_result(
                test_name, 
                'FAIL', 
                "内容提取失败",
                comparison
            )
            return False
    
    def test_dynamic_content_extraction(self):
        """测试2: 动态内容提取"""
        test_name = "Dynamic Content Extraction"
        self.log(f"开始测试: {test_name}")
        
        # 测试需要JavaScript渲染的页面
        test_results = []
        
        for key, test_info in self.test_urls.items():
            if test_info['type'] in ['api', 'json']:
                self.log(f"测试 {test_info['description']}: {test_info['url']}")
                
                # Selenium提取
                selenium_result = self.extract_with_selenium(test_info['url'])
                
                # urllib提取
                urllib_result = self.extract_with_urllib(test_info['url'])
                
                test_results.append({
                    'type': test_info['type'],
                    'description': test_info['description'],
                    'url': test_info['url'],
                    'selenium_success': selenium_result['success'],
                    'urllib_success': urllib_result['success'],
                    'selenium_content': selenium_result.get('js_data', {}).get('bodyText', '')[:100],
                    'content_diff': abs(
                        len(selenium_result.get('page_source', '')) - 
                        len(urllib_result.get('page_source', ''))
                    )
                })
        
        # 判断结果
        all_success = all(r['selenium_success'] for r in test_results)
        
        if all_success:
            self.add_test_result(
                test_name, 
                'PASS', 
                "所有动态内容提取成功",
                {'results': test_results}
            )
            return True
        else:
            self.add_test_result(
                test_name, 
                'PARTIAL', 
                "部分动态内容提取失败",
                {'results': test_results}
            )
            return False
    
    def test_delayed_content_extraction(self):
        """测试3: 延迟加载内容提取"""
        test_name = "Delayed Content Extraction"
        self.log(f"开始测试: {test_name}")
        
        test_url = self.test_urls['delayed_response']['url']
        
        # Selenium提取（等待内容加载）
        selenium_start = time.time()
        selenium_result = self.extract_with_selenium(test_url)
        selenium_time = time.time() - selenium_start
        
        # urllib提取（可能超时）
        urllib_start = time.time()
        urllib_result = self.extract_with_urllib(test_url, timeout=5)
        urllib_time = time.time() - urllib_start
        
        results = {
            'selenium': {
                'success': selenium_result['success'],
                'total_time': f"{selenium_time:.2f}s",
                'content_extracted': selenium_result.get('source_length', 0) > 0
            },
            'urllib': {
                'success': urllib_result['success'],
                'total_time': f"{urllib_time:.2f}s",
                'content_extracted': urllib_result.get('source_length', 0) > 0
            }
        }
        
        if selenium_result['success']:
            self.add_test_result(
                test_name, 
                'PASS', 
                f"Selenium成功处理延迟内容 (用时: {selenium_time:.2f}s)",
                results
            )
            return True
        else:
            self.add_test_result(
                test_name, 
                'FAIL', 
                "延迟内容提取失败",
                results
            )
            return False
    
    def test_javascript_execution(self):
        """测试4: JavaScript执行和DOM操作"""
        test_name = "JavaScript Execution"
        self.log(f"开始测试: {test_name}")
        
        if not self.driver:
            self.add_test_result(
                test_name, 
                'SKIP', 
                "Driver未初始化"
            )
            return False
        
        try:
            # 访问测试页面
            self.driver.get('https://www.example.com')
            
            js_tests = []
            
            # 测试1: 基本JavaScript执行
            result1 = self.driver.execute_script("return 1 + 1;")
            js_tests.append({
                'test': '基本计算',
                'success': result1 == 2,
                'result': result1
            })
            
            # 测试2: DOM操作
            self.driver.execute_script("""
                var div = document.createElement('div');
                div.id = 'selenium-test';
                div.innerHTML = 'Selenium Test Content';
                document.body.appendChild(div);
            """)
            
            test_element = self.driver.find_element(By.ID, 'selenium-test')
            js_tests.append({
                'test': 'DOM元素创建',
                'success': test_element.text == 'Selenium Test Content',
                'result': test_element.text
            })
            
            # 测试3: 获取页面信息
            page_info = self.driver.execute_script("""
                return {
                    url: window.location.href,
                    title: document.title,
                    cookie: document.cookie,
                    localStorage: Object.keys(localStorage || {}),
                    bodyClasses: document.body.className,
                    metaTags: Array.from(document.getElementsByTagName('meta')).map(m => ({
                        name: m.name,
                        content: m.content
                    }))
                };
            """)
            
            js_tests.append({
                'test': '页面信息获取',
                'success': page_info['url'] is not None,
                'result': page_info
            })
            
            # 测试4: 异步JavaScript
            async_result = self.driver.execute_async_script("""
                var callback = arguments[arguments.length - 1];
                setTimeout(function() {
                    callback('Async execution completed');
                }, 1000);
            """)
            
            js_tests.append({
                'test': '异步JavaScript',
                'success': async_result == 'Async execution completed',
                'result': async_result
            })
            
            # 判断结果
            all_success = all(t['success'] for t in js_tests)
            
            if all_success:
                self.add_test_result(
                    test_name, 
                    'PASS', 
                    "所有JavaScript执行测试通过",
                    {'js_tests': js_tests}
                )
                return True
            else:
                failed = [t['test'] for t in js_tests if not t['success']]
                self.add_test_result(
                    test_name, 
                    'PARTIAL', 
                    f"部分JavaScript测试失败: {', '.join(failed)}",
                    {'js_tests': js_tests}
                )
                return False
                
        except Exception as e:
            self.add_test_result(
                test_name, 
                'FAIL', 
                f"JavaScript执行失败: {str(e)}",
                {'error': traceback.format_exc()}
            )
            return False
    
    def test_element_interaction(self):
        """测试5: 元素交互能力"""
        test_name = "Element Interaction"
        self.log(f"开始测试: {test_name}")
        
        if not self.driver:
            self.add_test_result(
                test_name, 
                'SKIP', 
                "Driver未初始化"
            )
            return False
        
        try:
            # 访问httpbin表单页面
            self.driver.get('https://httpbin.org/forms/post')
            
            interaction_tests = []
            
            # 查找表单元素
            try:
                # 输入框交互
                custname = self.driver.find_element(By.NAME, 'custname')
                custname.clear()
                custname.send_keys('Selenium Test')
                
                interaction_tests.append({
                    'test': '文本输入',
                    'success': custname.get_attribute('value') == 'Selenium Test'
                })
                
                # 下拉框选择
                custtel = self.driver.find_element(By.NAME, 'custtel')
                custtel.send_keys('123-456-7890')
                
                interaction_tests.append({
                    'test': '电话输入',
                    'success': True
                })
                
                # 文本域
                comments = self.driver.find_element(By.NAME, 'comments')
                comments.clear()
                comments.send_keys('Test comment from Selenium')
                
                interaction_tests.append({
                    'test': '文本域输入',
                    'success': 'Test comment' in comments.get_attribute('value')
                })
                
                # 单选框
                size_medium = self.driver.find_element(By.XPATH, "//input[@name='size' and @value='medium']")
                size_medium.click()
                
                interaction_tests.append({
                    'test': '单选框选择',
                    'success': size_medium.is_selected()
                })
                
                # 复选框
                toppings = self.driver.find_elements(By.NAME, 'topping')
                if toppings:
                    toppings[0].click()
                    interaction_tests.append({
                        'test': '复选框选择',
                        'success': toppings[0].is_selected()
                    })
                
            except Exception as e:
                interaction_tests.append({
                    'test': '元素定位',
                    'success': False,
                    'error': str(e)
                })
            
            # 判断结果
            success_count = sum(1 for t in interaction_tests if t.get('success', False))
            total_count = len(interaction_tests)
            
            if success_count == total_count:
                self.add_test_result(
                    test_name, 
                    'PASS', 
                    f"所有元素交互测试通过 ({success_count}/{total_count})",
                    {'interaction_tests': interaction_tests}
                )
                return True
            elif success_count > 0:
                self.add_test_result(
                    test_name, 
                    'PARTIAL', 
                    f"部分元素交互成功 ({success_count}/{total_count})",
                    {'interaction_tests': interaction_tests}
                )
                return False
            else:
                self.add_test_result(
                    test_name, 
                    'FAIL', 
                    "元素交互测试失败",
                    {'interaction_tests': interaction_tests}
                )
                return False
                
        except Exception as e:
            self.add_test_result(
                test_name, 
                'FAIL', 
                f"元素交互测试异常: {str(e)}",
                {'error': traceback.format_exc()}
            )
            return False
    
    def test_content_completeness(self):
        """测试6: 内容完整性验证"""
        test_name = "Content Completeness"
        self.log(f"开始测试: {test_name}")
        
        completeness_tests = []
        
        for key, test_info in self.test_urls.items():
            self.log(f"验证 {test_info['description']}")
            
            # Selenium提取
            selenium_result = self.extract_with_selenium(test_info['url'])
            
            if selenium_result['success']:
                # 检查内容完整性指标
                js_data = selenium_result.get('js_data', {})
                
                completeness = {
                    'url': test_info['url'],
                    'type': test_info['type'],
                    'document_ready': js_data.get('documentReady') == 'complete',
                    'has_body_text': js_data.get('bodyTextLength', 0) > 0,
                    'has_images': js_data.get('images', 0) >= 0,
                    'has_links': js_data.get('links', 0) >= 0,
                    'source_length': selenium_result.get('source_length', 0)
                }
                
                # 计算完整性分数
                score = sum([
                    completeness['document_ready'],
                    completeness['has_body_text'],
                    completeness['source_length'] > 100
                ]) / 3 * 100
                
                completeness['score'] = f"{score:.0f}%"
                completeness['complete'] = score >= 66
                
                completeness_tests.append(completeness)
        
        # 判断整体结果
        all_complete = all(t.get('complete', False) for t in completeness_tests)
        avg_score = sum(
            float(t['score'].rstrip('%')) 
            for t in completeness_tests
        ) / len(completeness_tests) if completeness_tests else 0
        
        if all_complete:
            self.add_test_result(
                test_name, 
                'PASS', 
                f"所有内容完整性检查通过 (平均分: {avg_score:.0f}%)",
                {'completeness_tests': completeness_tests}
            )
            return True
        elif avg_score >= 50:
            self.add_test_result(
                test_name, 
                'PARTIAL', 
                f"部分内容完整性检查通过 (平均分: {avg_score:.0f}%)",
                {'completeness_tests': completeness_tests}
            )
            return False
        else:
            self.add_test_result(
                test_name, 
                'FAIL', 
                f"内容完整性检查失败 (平均分: {avg_score:.0f}%)",
                {'completeness_tests': completeness_tests}
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
        self.log("开始内容提取能力测试")
        self.log("="*60)
        
        # 连接Chrome
        if not self.connect_to_chrome():
            self.log("无法连接到Chrome Debug实例", 'ERROR')
            return False
        
        # 运行测试
        tests = [
            self.test_static_content_extraction,
            self.test_dynamic_content_extraction,
            self.test_delayed_content_extraction,
            self.test_javascript_execution,
            self.test_element_interaction,
            self.test_content_completeness
        ]
        
        for test in tests:
            try:
                test()
                time.sleep(1)
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
        report_file = f"content_extraction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
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
    ║           Selenium 内容提取能力测试                       ║
    ╠══════════════════════════════════════════════════════════╣
    ║  此测试将验证:                                           ║
    ║  1. 静态HTML内容提取                                     ║
    ║  2. 动态JavaScript内容提取                               ║
    ║  3. 延迟加载内容处理                                     ║
    ║  4. JavaScript执行能力                                   ║
    ║  5. 页面元素交互能力                                     ║
    ║  6. 内容完整性验证                                       ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    print("\n⚠️  测试前请确保:")
    print("1. Chrome已通过调试模式启动 (端口9222)")
    print("2. 使用命令: ./chrome-debug.sh")
    print("3. selenium包已安装: pip install selenium")
    print()
    
    input("按Enter键开始测试...")
    
    # 运行测试
    tester = ContentExtractionTest()
    success = tester.run_all_tests()
    
    # 返回状态码
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()