#!/usr/bin/env python3
"""
CDP (Chrome DevTools Protocol) 使用示例

演示 WebFetcher 的 CDP 抓取功能的各种用法

运行前请确保:
1. 已安装 pychrome: pip install pychrome
2. Chrome 调试模式已启动: ./scripts/start_chrome.sh

Author: WebFetcher Team
Date: 2025-11-17
"""

import sys
import time
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from webfetcher.fetchers.cdp_scraper import (
    CDPScraper, CDPMetrics,
    is_cdp_available, check_chrome_debug_running
)


def demo_1_basic_fetch():
    """示例 1: 基础页面抓取"""
    print("\n" + "="*60)
    print("示例 1: 基础页面抓取")
    print("="*60)

    try:
        scraper = CDPScraper()

        # 抓取页面
        html, metrics = scraper.fetch_page(
            "https://httpbin.org/html",
            wait_load=2.0
        )

        print(f"✓ 抓取成功!")
        print(f"  HTML 长度: {len(html)} 字符")
        print(f"  总耗时: {metrics.total_time:.2f}秒")
        print(f"  连接耗时: {metrics.connection_time:.2f}秒")
        print(f"  导航耗时: {metrics.navigation_time:.2f}秒")

        # 显示 HTML 片段
        preview = html[:200] if len(html) > 200 else html
        print(f"\nHTML 预览:\n{preview}...")

    except Exception as e:
        print(f"✗ 抓取失败: {e}")


def demo_2_advanced_operations():
    """示例 2: 高级操作 - 元素选择、JS 执行、截图"""
    print("\n" + "="*60)
    print("示例 2: 高级操作")
    print("="*60)

    try:
        scraper = CDPScraper()

        # 创建标签页并访问
        print("正在访问 Example.com...")
        tab = scraper.new_tab("https://example.com", wait_load=2.0)

        # 执行 JavaScript 获取标题
        title = scraper.eval_js(tab, "document.title")
        print(f"✓ 页面标题: {title}")

        # 获取页面 URL
        url = scraper.eval_js(tab, "window.location.href")
        print(f"✓ 页面 URL: {url}")

        # 提取特定元素的文本
        h1_text = scraper.query_selector(tab, "h1")
        print(f"✓ H1 文本: {h1_text}")

        # 查询所有段落
        paragraphs = scraper.query_selector_all(tab, "p")
        print(f"✓ 找到 {len(paragraphs)} 个段落")
        if paragraphs:
            print(f"  第一段: {paragraphs[0][:100]}...")

        # 截图
        screenshot_path = "example_screenshot.png"
        if scraper.screenshot(tab, screenshot_path):
            print(f"✓ 截图已保存: {screenshot_path}")

        # 导出会话状态
        session_path = "example_session.json"
        session = scraper.export_session(tab, session_path)
        print(f"✓ 会话状态已导出: {session_path}")
        print(f"  Cookies 数量: {len(session.get('cookies', []))}")

        # 关闭标签页
        scraper.close_tab(tab)
        print("✓ 标签页已关闭")

    except Exception as e:
        print(f"✗ 操作失败: {e}")


def demo_3_network_monitoring():
    """示例 3: 网络请求监听"""
    print("\n" + "="*60)
    print("示例 3: 网络请求监听")
    print("="*60)

    try:
        scraper = CDPScraper()

        # 创建标签页
        tab = scraper.new_tab()

        # 启动网络监听
        print("启动网络监听...")
        scraper.watch_network(tab)

        # 访问页面
        print("正在访问 httpbin.org...")
        scraper.navigate(tab, "https://httpbin.org/", wait_load=3.0)

        # 获取所有请求
        if hasattr(tab, '_requests'):
            print(f"✓ 捕获到 {len(tab._requests)} 个请求:")
            for i, req in enumerate(tab._requests[:5], 1):  # 显示前5个
                print(f"  {i}. {req['method']} {req['url']}")

        # 获取所有响应
        if hasattr(tab, '_responses'):
            print(f"✓ 捕获到 {len(tab._responses)} 个响应:")
            for i, resp in enumerate(tab._responses[:5], 1):
                print(f"  {i}. [{resp['status']}] {resp['url']}")

        # 过滤 API 调用
        apis = scraper.get_api_calls(tab)
        print(f"✓ 发现 {len(apis)} 个 API 调用")

        scraper.close_tab(tab)

    except Exception as e:
        print(f"✗ 监听失败: {e}")


def demo_4_wait_for_elements():
    """示例 4: 等待元素出现"""
    print("\n" + "="*60)
    print("示例 4: 等待元素出现")
    print("="*60)

    try:
        scraper = CDPScraper()

        # 创建标签页
        tab = scraper.new_tab("https://example.com", wait_load=1.0)

        # 等待 body 元素出现
        print("等待 body 元素...")
        if scraper.wait_for_selector(tab, "body", timeout=5.0):
            print("✓ body 元素已出现")
        else:
            print("✗ 等待超时")

        # 尝试等待一个不存在的元素 (会超时)
        print("尝试等待不存在的元素...")
        if scraper.wait_for_selector(tab, ".nonexistent-class", timeout=2.0):
            print("✓ 元素已出现")
        else:
            print("✓ 正确处理了不存在的元素 (超时)")

        scraper.close_tab(tab)

    except Exception as e:
        print(f"✗ 操作失败: {e}")


def demo_5_scroll_and_lazy_load():
    """示例 5: 滚动页面 (触发懒加载)"""
    print("\n" + "="*60)
    print("示例 5: 滚动页面")
    print("="*60)

    try:
        scraper = CDPScraper()

        # 创建标签页
        tab = scraper.new_tab("https://example.com", wait_load=2.0)

        # 获取初始页面高度
        initial_height = scraper.eval_js(tab, "document.body.scrollHeight")
        print(f"初始页面高度: {initial_height}px")

        # 滚动到底部
        print("滚动到页面底部...")
        scraper.scroll_to_bottom(tab, wait=1.0)

        # 获取滚动后的位置
        scroll_position = scraper.eval_js(tab, "window.pageYOffset || document.documentElement.scrollTop")
        print(f"✓ 当前滚动位置: {scroll_position}px")

        scraper.close_tab(tab)

    except Exception as e:
        print(f"✗ 操作失败: {e}")


def demo_6_multiple_tabs():
    """示例 6: 多标签页管理"""
    print("\n" + "="*60)
    print("示例 6: 多标签页管理")
    print("="*60)

    try:
        scraper = CDPScraper()

        # 列出现有标签页
        tabs = scraper.list_tabs()
        print(f"当前有 {len(tabs)} 个标签页")

        # 创建多个新标签页
        print("\n创建 3 个新标签页...")
        tab1 = scraper.new_tab("https://example.com", wait_load=1.0)
        tab2 = scraper.new_tab("https://httpbin.org/", wait_load=1.0)
        tab3 = scraper.new_tab("https://www.iana.org/", wait_load=1.0)

        # 再次列出标签页
        tabs = scraper.list_tabs()
        print(f"✓ 现在有 {len(tabs)} 个标签页")

        # 从每个标签页获取标题
        title1 = scraper.eval_js(tab1, "document.title")
        title2 = scraper.eval_js(tab2, "document.title")
        title3 = scraper.eval_js(tab3, "document.title")

        print(f"✓ 标签页 1: {title1}")
        print(f"✓ 标签页 2: {title2}")
        print(f"✓ 标签页 3: {title3}")

        # 关闭所有标签页
        print("\n关闭所有新标签页...")
        scraper.close_tab(tab1)
        scraper.close_tab(tab2)
        scraper.close_tab(tab3)
        print("✓ 完成")

    except Exception as e:
        print(f"✗ 操作失败: {e}")


def main():
    """主函数"""
    print("="*60)
    print("CDP (Chrome DevTools Protocol) 使用示例")
    print("="*60)

    # 检查 CDP 是否可用
    if not is_cdp_available():
        print("\n✗ CDP 不可用!")
        print("请安装 pychrome: pip install pychrome")
        return

    print("✓ CDP 可用 (pychrome 已安装)")

    # 检查 Chrome 是否在调试模式运行
    if not check_chrome_debug_running():
        print("\n✗ Chrome 调试实例未运行!")
        print("请启动 Chrome 调试模式: ./scripts/start_chrome.sh")
        print("或手动运行: chrome --remote-debugging-port=9222")
        return

    print("✓ Chrome 调试实例正在运行")

    # 运行所有示例
    demos = [
        demo_1_basic_fetch,
        demo_2_advanced_operations,
        demo_3_network_monitoring,
        demo_4_wait_for_elements,
        demo_5_scroll_and_lazy_load,
        demo_6_multiple_tabs
    ]

    for demo in demos:
        try:
            demo()
            time.sleep(1)  # 示例之间短暂暂停
        except KeyboardInterrupt:
            print("\n\n用户中断")
            break
        except Exception as e:
            print(f"\n✗ 示例运行失败: {e}")
            continue

    print("\n" + "="*60)
    print("所有示例运行完成!")
    print("="*60)


if __name__ == "__main__":
    main()
