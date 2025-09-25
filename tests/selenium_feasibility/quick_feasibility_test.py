#!/usr/bin/env python3
"""
Selenium + Chrome Debug 快速可行性测试
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
from datetime import datetime

class QuickFeasibilityTest:
    def __init__(self):
        self.driver = None
        self.results = []
        
    def connect(self):
        """连接到Chrome Debug实例"""
        try:
            print("🔗 正在连接到Chrome Debug实例...")
            chrome_options = Options()
            chrome_options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            print(f"✅ 连接成功！当前页面: {self.driver.title}")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    def test_url(self, url, name, wait_selector=None):
        """测试单个URL"""
        result = {
            'name': name,
            'url': url,
            'success': False,
            'title': '',
            'content_length': 0,
            'load_time': 0,
            'error': None
        }
        
        try:
            print(f"\n📍 测试: {name}")
            print(f"   URL: {url[:60]}...")
            
            start_time = time.time()
            self.driver.get(url)
            
            # 等待页面加载
            if wait_selector:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
                )
            else:
                time.sleep(3)  # 默认等待3秒
            
            result['load_time'] = time.time() - start_time
            result['title'] = self.driver.title
            
            # 获取页面内容
            page_source = self.driver.page_source
            result['content_length'] = len(page_source)
            
            # 检查JavaScript执行
            js_result = self.driver.execute_script("return document.readyState")
            
            result['success'] = True
            print(f"   ✅ 成功加载")
            print(f"   标题: {result['title'][:50]}...")
            print(f"   内容大小: {result['content_length']:,} 字节")
            print(f"   加载时间: {result['load_time']:.2f}秒")
            print(f"   JS状态: {js_result}")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"   ❌ 失败: {e}")
        
        self.results.append(result)
        return result['success']
    
    def run_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("🚀 开始Selenium可行性测试")
        print("="*60)
        
        if not self.connect():
            return False
        
        # 测试URL列表
        test_cases = [
            {
                'url': 'https://example.com',
                'name': '简单静态页面',
                'wait': None
            },
            {
                'url': 'https://mp.weixin.qq.com/s/xM_lYyQXmg4JCpd1w7kPxg',
                'name': '微信公众号文章',
                'wait': '#js_article'
            },
            {
                'url': 'https://www.xiaohongshu.com/explore/68be9ba0000000001c00f210',
                'name': '小红书笔记',
                'wait': None  # 小红书可能需要特殊处理
            },
            {
                'url': 'https://www.qstheory.cn/dukan/qs/2024-01/31/c_1130069364.htm',
                'name': '求是理论网',
                'wait': '.content'
            },
            {
                'url': 'https://zh.wikipedia.org/wiki/Python',
                'name': '维基百科',
                'wait': '#content'
            },
            {
                'url': 'https://www.news.cn/politics/leaders/index.htm',
                'name': '新华网',
                'wait': None
            }
        ]
        
        # 运行测试
        for case in test_cases:
            self.test_url(case['url'], case['name'], case.get('wait'))
            time.sleep(1)  # 测试之间短暂停顿
        
        # 生成报告
        self.generate_report()
        
        # 清理
        if self.driver:
            self.driver.quit()
        
        return True
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📊 测试报告")
        print("="*60)
        
        success_count = sum(1 for r in self.results if r['success'])
        total_count = len(self.results)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        print(f"\n总测试数: {total_count}")
        print(f"成功: {success_count}")
        print(f"失败: {total_count - success_count}")
        print(f"成功率: {success_rate:.1f}%")
        
        print("\n详细结果:")
        for r in self.results:
            status = "✅" if r['success'] else "❌"
            print(f"{status} {r['name']}")
            if r['success']:
                print(f"   - 加载时间: {r['load_time']:.2f}秒")
                print(f"   - 内容大小: {r['content_length']:,} 字节")
            else:
                print(f"   - 错误: {r['error']}")
        
        # 可行性评分
        score = self.calculate_score()
        print("\n" + "="*60)
        print(f"🎯 可行性评分: {score}/100")
        print("="*60)
        
        # 技术建议
        print("\n💡 技术建议:")
        if score >= 80:
            print("✅ 强烈推荐采用Selenium + debuggerAddress方案")
            print("   - Chrome Debug连接稳定可靠")
            print("   - 能够处理各种类型的网站")
            print("   - JavaScript渲染支持完善")
            print("   - 建议立即开始正式插件开发")
        elif score >= 60:
            print("⚠️ 可以采用，但需要优化")
            print("   - 基本功能正常")
            print("   - 部分网站可能需要特殊处理")
            print("   - 建议先优化已知问题")
        else:
            print("❌ 不建议采用当前方案")
            print("   - 存在较多问题")
            print("   - 建议检查环境配置")
        
        # 保存报告
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'results': self.results,
            'summary': {
                'total': total_count,
                'success': success_count,
                'failed': total_count - success_count,
                'success_rate': success_rate,
                'score': score
            }
        }
        
        with open('quick_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细报告已保存到: quick_test_report.json")
    
    def calculate_score(self):
        """计算可行性得分"""
        if not self.results:
            return 0
        
        # 基础分：成功率
        success_rate = sum(1 for r in self.results if r['success']) / len(self.results)
        base_score = success_rate * 70
        
        # 加分项
        bonus = 0
        
        # 如果微信公众号成功，加10分
        wechat = next((r for r in self.results if '微信' in r['name']), None)
        if wechat and wechat['success']:
            bonus += 10
        
        # 如果维基百科成功，加5分
        wiki = next((r for r in self.results if '维基' in r['name']), None)
        if wiki and wiki['success']:
            bonus += 5
        
        # 平均加载时间小于3秒，加10分
        success_results = [r for r in self.results if r['success']]
        if success_results:
            avg_load = sum(r['load_time'] for r in success_results) / len(success_results)
            if avg_load < 3:
                bonus += 10
        
        # 如果全部成功，额外加5分
        if success_rate == 1.0:
            bonus += 5
        
        return min(100, int(base_score + bonus))

if __name__ == '__main__':
    tester = QuickFeasibilityTest()
    tester.run_tests()