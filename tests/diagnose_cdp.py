#!/usr/bin/env python3
"""
CDP Diagnostics Script
诊断CDP连接和HTML获取问题
"""
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    import pychrome
    print("✓ pychrome已安装")
except ImportError:
    print("✗ pychrome未安装")
    sys.exit(1)

def test_basic_connection():
    """测试基本连接"""
    print("\n" + "="*70)
    print("测试1: 基本CDP连接")
    print("="*70)

    try:
        browser = pychrome.Browser(url="http://127.0.0.1:9222")
        print("✓ 连接到Chrome成功")

        # 列出所有标签页
        tabs = browser.list_tab()
        print(f"✓ 找到 {len(tabs)} 个标签页")

        for i, tab in enumerate(tabs):
            try:
                # pychrome的tab.url可能是GenericAttr对象，需要特殊处理
                url = str(tab.url) if hasattr(tab, 'url') else 'N/A'
                print(f"  [{i}] {url[:80] if len(url) > 80 else url}")
            except:
                print(f"  [{i}] <无法获取URL>")

        return browser, tabs
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        return None, None

def test_create_new_tab(browser):
    """测试创建新标签页"""
    print("\n" + "="*70)
    print("测试2: 创建新标签页")
    print("="*70)

    try:
        tab = browser.new_tab()
        print("✓ 创建新标签页成功")

        # 启动标签页
        tab.start()
        print("✓ 启动标签页成功")

        # 启用必要的域
        tab.Network.enable()
        tab.Page.enable()
        tab.Runtime.enable()
        print("✓ 启用Network/Page/Runtime成功")

        return tab
    except Exception as e:
        print(f"✗ 创建标签页失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_navigate_and_fetch(tab, url="https://www.example.com"):
    """测试导航和HTML获取"""
    print("\n" + "="*70)
    print(f"测试3: 导航到 {url}")
    print("="*70)

    try:
        # 导航
        result = tab.Page.navigate(url=url)
        print(f"✓ 导航命令发送成功")
        print(f"  Frame ID: {result.get('frameId', 'N/A')}")

        # 等待页面加载
        print("  等待3秒页面加载...")
        time.sleep(3)

        # 获取HTML
        print("\n  尝试获取HTML...")
        js_result = tab.Runtime.evaluate(expression="document.documentElement.outerHTML")
        print(f"✓ JavaScript执行成功")
        print(f"  返回类型: {type(js_result)}")
        print(f"  返回内容: {str(js_result)[:200]}...")

        if "result" in js_result and "value" in js_result["result"]:
            html = js_result["result"]["value"]
            print(f"\n✓ 成功获取HTML: {len(html)} 字符")
            print(f"  前100字符: {html[:100]}")
            return True
        else:
            print(f"✗ 返回格式不正确")
            print(f"  完整返回: {js_result}")
            return False

    except Exception as e:
        print(f"✗ 导航或获取失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_reuse_tab(browser):
    """测试复用已有标签页"""
    print("\n" + "="*70)
    print("测试4: 复用已有标签页")
    print("="*70)

    try:
        tabs = browser.list_tab()
        if not tabs:
            print("✗ 没有可用的标签页")
            return None

        # 使用第一个标签页
        tab = tabs[0]
        url = str(tab.url) if hasattr(tab, 'url') else 'N/A'
        print(f"✓ 选择标签页: {url[:80] if len(url) > 80 else url}")

        # 启动并启用域
        tab.start()
        tab.Network.enable()
        tab.Page.enable()
        tab.Runtime.enable()
        print("✓ 启动和启用成功")

        return tab
    except Exception as e:
        print(f"✗ 复用标签页失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_wait_for_load_event(tab, url="https://www.example.com"):
    """测试使用Page.loadEventFired等待页面加载"""
    print("\n" + "="*70)
    print(f"测试5: 使用事件等待页面加载")
    print("="*70)

    try:
        # 设置回调来捕获加载事件
        load_event_fired = False

        def on_load(event):
            nonlocal load_event_fired
            load_event_fired = True
            print("✓ 页面加载完成事件触发")

        tab.Page.loadEventFired = on_load

        # 导航
        print(f"  导航到: {url}")
        tab.Page.navigate(url=url)

        # 等待加载完成（最多10秒）
        start = time.time()
        while not load_event_fired and time.time() - start < 10:
            time.sleep(0.1)

        if load_event_fired:
            print("✓ 页面加载完成")
        else:
            print("⚠️  超时，但继续尝试获取HTML")

        # 获取HTML
        result = tab.Runtime.evaluate(expression="document.documentElement.outerHTML")
        if "result" in result and "value" in result["result"]:
            html = result["result"]["value"]
            print(f"✓ 成功获取HTML: {len(html)} 字符")
            return True
        else:
            print(f"✗ HTML获取失败")
            return False

    except Exception as e:
        print(f"✗ 事件等待失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("CDP诊断工具")
    print("="*70)
    print("确保Chrome已经在调试模式下运行:")
    print("  ./config/start_chrome_debug.sh")
    print("="*70)

    # 测试1: 基本连接
    browser, tabs = test_basic_connection()
    if not browser:
        print("\n❌ 无法连接到Chrome，请确保Chrome调试模式已启动")
        return

    # 测试2: 创建新标签页
    tab = test_create_new_tab(browser)
    if tab:
        # 测试3: 导航和获取
        success = test_navigate_and_fetch(tab)

        if success:
            print("\n✅ CDP基本功能正常")
        else:
            print("\n⚠️  CDP连接正常，但HTML获取有问题")

        # 清理
        try:
            tab.stop()
            print("\n✓ 标签页已关闭")
        except:
            pass

    # 测试4: 复用标签页
    tab2 = test_reuse_tab(browser)
    if tab2:
        # 测试5: 事件等待
        test_wait_for_load_event(tab2)

        try:
            tab2.stop()
        except:
            pass

    print("\n" + "="*70)
    print("诊断完成")
    print("="*70)

if __name__ == '__main__':
    main()
