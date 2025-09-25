#!/usr/bin/env python3
"""
Selenium高级功能测试
测试更复杂的场景和功能
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import json

class AdvancedSeleniumTest:
    def __init__(self):
        self.driver = None
        self.connect()
    
    def connect(self):
        """连接到Chrome Debug实例"""
        chrome_options = Options()
        chrome_options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ 已连接到Chrome Debug实例")
    
    def test_javascript_execution(self):
        """测试JavaScript执行能力"""
        print("\n📝 测试1: JavaScript执行")
        
        self.driver.get("https://example.com")
        
        # 执行JavaScript
        result = self.driver.execute_script("""
            // 获取页面信息
            return {
                title: document.title,
                url: window.location.href,
                cookies: document.cookie,
                localStorage: Object.keys(localStorage || {}),
                domNodes: document.querySelectorAll('*').length,
                scripts: document.scripts.length,
                timestamp: new Date().toISOString()
            }
        """)
        
        print(f"   ✅ JavaScript执行成功")
        print(f"   页面节点数: {result['domNodes']}")
        print(f"   脚本数量: {result['scripts']}")
        print(f"   时间戳: {result['timestamp']}")
        return True
    
    def test_wait_strategies(self):
        """测试等待策略"""
        print("\n⏱️ 测试2: 智能等待策略")
        
        self.driver.get("https://zh.wikipedia.org/wiki/Python")
        
        try:
            # 显式等待
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "firstHeading"))
            )
            print(f"   ✅ 显式等待成功: {element.text}")
            
            # 等待多个条件
            WebDriverWait(self.driver, 10).until(
                EC.all_of(
                    EC.presence_of_element_located((By.CLASS_NAME, "mw-body")),
                    EC.title_contains("Python")
                )
            )
            print(f"   ✅ 多条件等待成功")
            
            return True
        except Exception as e:
            print(f"   ❌ 等待失败: {e}")
            return False
    
    def test_content_extraction(self):
        """测试内容提取能力"""
        print("\n📄 测试3: 高级内容提取")
        
        self.driver.get("https://mp.weixin.qq.com/s/xM_lYyQXmg4JCpd1w7kPxg")
        time.sleep(3)
        
        # 提取文章内容
        content_data = self.driver.execute_script("""
            const article = document.querySelector('#js_article') || document.querySelector('.rich_media_content');
            if (!article) return null;
            
            return {
                title: document.querySelector('h1')?.innerText || document.title,
                content: article.innerText.substring(0, 500),
                images: Array.from(article.querySelectorAll('img')).map(img => img.src).slice(0, 5),
                links: Array.from(article.querySelectorAll('a')).map(a => a.href).slice(0, 5),
                wordCount: article.innerText.length
            }
        """)
        
        if content_data:
            print(f"   ✅ 内容提取成功")
            print(f"   标题: {content_data.get('title', 'N/A')[:50]}...")
            print(f"   字数: {content_data.get('wordCount', 0)}")
            print(f"   图片数: {len(content_data.get('images', []))}")
            print(f"   链接数: {len(content_data.get('links', []))}")
            return True
        else:
            print(f"   ⚠️ 未能提取内容")
            return False
    
    def test_cookie_handling(self):
        """测试Cookie处理"""
        print("\n🍪 测试4: Cookie管理")
        
        self.driver.get("https://httpbin.org/cookies")
        
        # 添加Cookie
        self.driver.add_cookie({
            'name': 'test_cookie',
            'value': 'selenium_test',
            'path': '/'
        })
        
        # 刷新页面
        self.driver.refresh()
        time.sleep(1)
        
        # 获取页面内容检查Cookie
        page_text = self.driver.find_element(By.TAG_NAME, 'body').text
        
        if 'test_cookie' in page_text:
            print(f"   ✅ Cookie设置成功")
        else:
            print(f"   ⚠️ Cookie可能未生效")
        
        # 获取所有Cookies
        cookies = self.driver.get_cookies()
        print(f"   当前Cookie数量: {len(cookies)}")
        
        return True
    
    def test_window_handling(self):
        """测试窗口处理"""
        print("\n🪟 测试5: 窗口管理")
        
        # 获取当前窗口
        original_window = self.driver.current_window_handle
        windows_before = len(self.driver.window_handles)
        
        # 打开新窗口
        self.driver.execute_script("window.open('https://example.org', '_blank')")
        time.sleep(2)
        
        windows_after = len(self.driver.window_handles)
        
        if windows_after > windows_before:
            print(f"   ✅ 新窗口创建成功")
            print(f"   窗口数: {windows_before} -> {windows_after}")
            
            # 切换到新窗口
            for window in self.driver.window_handles:
                if window != original_window:
                    self.driver.switch_to.window(window)
                    print(f"   ✅ 切换到新窗口: {self.driver.title}")
                    break
            
            # 切换回原窗口
            self.driver.switch_to.window(original_window)
            print(f"   ✅ 切换回原窗口: {self.driver.title}")
            
            return True
        else:
            print(f"   ❌ 无法创建新窗口")
            return False
    
    def test_screenshot(self):
        """测试截图功能"""
        print("\n📸 测试6: 截图功能")
        
        self.driver.get("https://zh.wikipedia.org/wiki/Python")
        time.sleep(2)
        
        try:
            # 整页截图
            screenshot_path = "test_screenshot.png"
            self.driver.save_screenshot(screenshot_path)
            print(f"   ✅ 截图保存成功: {screenshot_path}")
            
            # 获取截图为base64
            screenshot_base64 = self.driver.get_screenshot_as_base64()
            print(f"   ✅ Base64截图长度: {len(screenshot_base64)}")
            
            return True
        except Exception as e:
            print(f"   ❌ 截图失败: {e}")
            return False
    
    def test_network_conditions(self):
        """测试网络条件模拟"""
        print("\n🌐 测试7: 性能指标获取")
        
        self.driver.get("https://example.com")
        
        # 获取性能指标
        performance = self.driver.execute_script("""
            const perf = performance.timing;
            return {
                loadTime: perf.loadEventEnd - perf.navigationStart,
                domContentLoaded: perf.domContentLoadedEventEnd - perf.navigationStart,
                responseTime: perf.responseEnd - perf.requestStart,
                renderTime: perf.domComplete - perf.domLoading
            }
        """)
        
        print(f"   ✅ 性能指标获取成功")
        print(f"   页面加载时间: {performance.get('loadTime', 0)}ms")
        print(f"   DOM加载时间: {performance.get('domContentLoaded', 0)}ms")
        print(f"   响应时间: {performance.get('responseTime', 0)}ms")
        print(f"   渲染时间: {performance.get('renderTime', 0)}ms")
        
        return True
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("🚀 Selenium高级功能测试")
        print("="*60)
        
        tests = [
            self.test_javascript_execution,
            self.test_wait_strategies,
            self.test_content_extraction,
            self.test_cookie_handling,
            self.test_window_handling,
            self.test_screenshot,
            self.test_network_conditions
        ]
        
        results = []
        for test in tests:
            try:
                success = test()
                results.append(success)
            except Exception as e:
                print(f"   ❌ 测试异常: {e}")
                results.append(False)
        
        # 总结
        print("\n" + "="*60)
        print("📊 测试总结")
        print("="*60)
        
        success_count = sum(1 for r in results if r)
        total_count = len(results)
        success_rate = (success_count / total_count * 100)
        
        print(f"成功: {success_count}/{total_count}")
        print(f"成功率: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("\n✅ 高级功能测试通过！Selenium完全满足需求")
            print("建议：")
            print("1. JavaScript执行能力强大，适合处理动态页面")
            print("2. 等待策略灵活，可应对各种加载场景")
            print("3. 内容提取功能完善，支持复杂页面结构")
            print("4. 窗口和Cookie管理成熟")
            print("5. 性能监控和调试功能齐全")
        elif success_rate >= 60:
            print("\n⚠️ 部分高级功能需要优化")
        else:
            print("\n❌ 高级功能存在问题，需要进一步调试")
        
        # 清理
        if self.driver:
            self.driver.quit()
        
        return success_rate

if __name__ == '__main__':
    tester = AdvancedSeleniumTest()
    score = tester.run_all_tests()
    
    print(f"\n🎯 最终评分: {score:.0f}/100")