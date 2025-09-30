#!/usr/bin/env python3
"""
Chrome-Selenium Connection Test Script
测试Chrome调试端口和Selenium连接的验证脚本

Phase 2: 验证Chrome启动后Selenium能否正常连接
"""

import sys
import time
import signal
import json
import urllib.request
import urllib.error
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException


# 全局超时配置
TIMEOUT_SECONDS = 30
DEBUG_PORT = 9222
DEBUG_HOST = "127.0.0.1"


class TimeoutException(Exception):
    """超时异常"""
    pass


def timeout_handler(signum, frame):
    """超时信号处理器"""
    print(f"\n❌ 测试超时！已超过 {TIMEOUT_SECONDS} 秒")
    raise TimeoutException("Operation timed out")


def test_chrome_debug_port():
    """
    测试1：Chrome调试端口验证
    Test 1: Verify Chrome Debug Port Accessibility

    验证Chrome调试端口是否可访问，并返回正确的版本信息
    """
    print("\n" + "="*60)
    print("测试1：Chrome调试端口验证")
    print("Test 1: Chrome Debug Port Verification")
    print("="*60)

    debug_url = f"http://{DEBUG_HOST}:{DEBUG_PORT}/json/version"
    print(f"\n📡 正在访问调试端口: {debug_url}")

    try:
        # 设置超时保护
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(10)

        request = urllib.request.Request(debug_url)
        with urllib.request.urlopen(request, timeout=5) as response:
            signal.alarm(0)  # 取消超时

            if response.status == 200:
                print(f"✅ 调试端口响应成功 (状态码: {response.status})")

                # 解析JSON响应
                data = response.read().decode('utf-8')
                version_info = json.loads(data)
                print("\n📋 Chrome版本信息:")
                print(f"   Browser: {version_info.get('Browser', 'N/A')}")
                print(f"   Protocol-Version: {version_info.get('Protocol-Version', 'N/A')}")
                print(f"   User-Agent: {version_info.get('User-Agent', 'N/A')[:80]}...")
                print(f"   WebSocket-Debugger-Url: {version_info.get('webSocketDebuggerUrl', 'N/A')[:60]}...")

                # 验证必需字段
                if 'Browser' in version_info or 'browserVersion' in version_info:
                    print("\n✅ 测试1通过: Chrome调试端口正常工作")
                    return True
                else:
                    print("\n❌ 测试1失败: 响应缺少Browser版本信息")
                    return False
            else:
                print(f"❌ 调试端口响应失败 (状态码: {response.status})")
                return False

    except urllib.error.URLError as e:
        signal.alarm(0)
        if isinstance(e.reason, TimeoutError):
            print("❌ 请求超时: Chrome调试端口未响应")
        else:
            print("❌ 连接错误: 无法连接到Chrome调试端口")
            print("   提示: 请确保Chrome已启动并监听9222端口")
        return False
    except TimeoutException:
        print("❌ 操作超时")
        return False
    except Exception as e:
        signal.alarm(0)
        print(f"❌ 测试失败: {type(e).__name__}: {e}")
        return False


def test_selenium_debugger_connection():
    """
    测试2：Selenium debuggerAddress连接
    Test 2: Selenium Connection via debuggerAddress

    验证Selenium能否通过debuggerAddress连接到已启动的Chrome
    """
    print("\n" + "="*60)
    print("测试2：Selenium debuggerAddress连接")
    print("Test 2: Selenium debuggerAddress Connection")
    print("="*60)

    driver = None

    try:
        # 设置超时保护
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(TIMEOUT_SECONDS)

        print("\n🔧 配置Chrome Options...")
        options = Options()
        options.debugger_address = f"{DEBUG_HOST}:{DEBUG_PORT}"

        print(f"   debuggerAddress: {options.debugger_address}")

        print("\n🚀 正在创建WebDriver实例...")
        print("   (这可能需要几秒钟...)")

        start_time = time.time()
        driver = webdriver.Chrome(options=options)
        elapsed_time = time.time() - start_time

        signal.alarm(0)  # 取消超时

        print(f"✅ Selenium连接成功！(耗时: {elapsed_time:.2f}秒)")

        # 获取capabilities
        print("\n📋 WebDriver Capabilities:")
        caps = driver.capabilities
        print(f"   browserName: {caps.get('browserName', 'N/A')}")
        print(f"   browserVersion: {caps.get('browserVersion', 'N/A')}")
        print(f"   platformName: {caps.get('platformName', 'N/A')}")

        # 获取当前URL
        current_url = driver.current_url
        print(f"\n🌐 当前页面URL: {current_url[:80]}...")

        print("\n✅ 测试2通过: Selenium成功连接到Chrome")
        return True

    except TimeoutException:
        print("❌ 连接超时: Selenium无法在规定时间内连接")
        print("   可能原因:")
        print("   1. Chrome未正确启动")
        print("   2. 调试端口未正确配置")
        print("   3. ChromeDriver版本不匹配")
        return False
    except WebDriverException as e:
        signal.alarm(0)
        print(f"❌ WebDriver错误: {e}")
        print("\n   诊断信息:")
        if "chrome not reachable" in str(e).lower():
            print("   - Chrome进程可能已崩溃或未启动")
        elif "session not created" in str(e).lower():
            print("   - 会话创建失败，可能是版本不匹配")
        return False
    except Exception as e:
        signal.alarm(0)
        print(f"❌ 测试失败: {type(e).__name__}: {e}")
        return False
    finally:
        if driver:
            try:
                # 注意：不关闭driver，保持Chrome实例继续运行
                print("\n💡 保持Chrome实例运行（未关闭driver）")
            except:
                pass


def test_basic_page_operations():
    """
    测试3：基本页面操作
    Test 3: Basic Page Operations

    验证Selenium能否执行基本的页面操作（导航、获取信息、执行JS）
    """
    print("\n" + "="*60)
    print("测试3：基本页面操作")
    print("Test 3: Basic Page Operations")
    print("="*60)

    driver = None

    try:
        # 设置超时保护
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(TIMEOUT_SECONDS)

        print("\n🔧 连接到Chrome...")
        options = Options()
        options.debugger_address = f"{DEBUG_HOST}:{DEBUG_PORT}"
        driver = webdriver.Chrome(options=options)

        print("✅ 连接成功")

        # 测试页面导航
        test_url = "http://example.com"
        print(f"\n🌐 导航到测试页面: {test_url}")
        driver.get(test_url)

        # 等待页面加载
        time.sleep(2)

        # 获取页面标题
        title = driver.title
        print(f"✅ 页面标题: {title}")

        if not title or len(title.strip()) == 0:
            print("❌ 页面标题为空")
            return False

        # 获取页面URL
        current_url = driver.current_url
        print(f"✅ 当前URL: {current_url}")

        # 执行JavaScript
        print("\n🔧 执行JavaScript测试...")
        js_result = driver.execute_script("return document.title;")
        print(f"✅ JS执行结果: {js_result}")

        # 验证JS结果与title一致
        if js_result == title:
            print("✅ JavaScript执行验证通过")
        else:
            print("⚠️  JavaScript结果与标题不一致")

        # 获取页面源码长度
        page_source_length = len(driver.page_source)
        print(f"\n📄 页面源码长度: {page_source_length} 字符")

        if page_source_length > 0:
            print("✅ 页面内容正常加载")
        else:
            print("❌ 页面内容为空")
            return False

        signal.alarm(0)  # 取消超时
        print("\n✅ 测试3通过: 基本页面操作功能正常")
        return True

    except TimeoutException:
        print("❌ 操作超时")
        return False
    except WebDriverException as e:
        signal.alarm(0)
        print(f"❌ WebDriver错误: {e}")
        return False
    except Exception as e:
        signal.alarm(0)
        print(f"❌ 测试失败: {type(e).__name__}: {e}")
        return False
    finally:
        if driver:
            try:
                # 不关闭driver，保持Chrome实例继续运行
                print("\n💡 保持Chrome实例运行（未关闭driver）")
            except:
                pass


def main():
    """主测试流程"""
    print("\n" + "🔬" + "="*58 + "🔬")
    print("  Chrome-Selenium Connection Test Suite")
    print("  Chrome与Selenium连接测试套件")
    print("🔬" + "="*58 + "🔬")

    # 测试结果记录
    results = {}

    # 执行测试1
    try:
        results['test1'] = test_chrome_debug_port()
    except Exception as e:
        print(f"\n❌ 测试1异常终止: {e}")
        results['test1'] = False

    # 如果测试1失败，终止后续测试
    if not results['test1']:
        print("\n⚠️  测试1失败，跳过后续测试")
        print("   建议: 请先确保Chrome正确启动并监听9222端口")
        return False

    # 执行测试2
    try:
        results['test2'] = test_selenium_debugger_connection()
    except Exception as e:
        print(f"\n❌ 测试2异常终止: {e}")
        results['test2'] = False

    # 如果测试2失败，终止后续测试
    if not results['test2']:
        print("\n⚠️  测试2失败，跳过后续测试")
        print("   建议: 检查ChromeDriver版本和Chrome版本是否匹配")
        return False

    # 执行测试3
    try:
        results['test3'] = test_basic_page_operations()
    except Exception as e:
        print(f"\n❌ 测试3异常终止: {e}")
        results['test3'] = False

    # 输出总结
    print("\n" + "="*60)
    print("测试总结 / Test Summary")
    print("="*60)

    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {test_name}: {status}")

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 所有测试通过！Chrome和Selenium连接正常工作")
        print("   Chrome-Selenium integration is working correctly!")
        return True
    else:
        print("\n❌ 部分测试失败，请查看上述详细信息")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ 测试套件异常: {type(e).__name__}: {e}")
        sys.exit(1)