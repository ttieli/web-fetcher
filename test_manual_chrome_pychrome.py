#!/usr/bin/env python3
"""
Test using pychrome CDP to extract from manually-opened Chrome
使用pychrome CDP从手动打开的Chrome中提取内容

Usage:
1. First start Chrome with debug port:
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
     --remote-debugging-port=9222 \
     --user-data-dir=/tmp/chrome-manual-test \
     --no-first-run \
     --disable-extensions

2. Manually navigate to target URL in that Chrome

3. Run this script to extract content via CDP
"""
import os
import json
import time
import base64
from datetime import datetime

try:
    import pychrome
    PYCHROME_AVAILABLE = True
except ImportError:
    PYCHROME_AVAILABLE = False
    print("WARNING: pychrome not available, install with: pip install pychrome")

OUT_DIR = "test_artifacts"
os.makedirs(OUT_DIR, exist_ok=True)

def pychrome_capture():
    """
    Use Chrome DevTools Protocol to capture content
    使用Chrome开发者工具协议捕获内容
    """
    if not PYCHROME_AVAILABLE:
        print("ERROR: pychrome is not installed")
        print("Please install it with: pip install pychrome")
        return None

    print("=" * 60)
    print("Manual Chrome CDP/pychrome Test")
    print("手动Chrome CDP/pychrome测试")
    print("=" * 60)
    print(f"\n时间 / Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nConnecting to Chrome via CDP on http://127.0.0.1:9222...")
    print("通过CDP连接到Chrome http://127.0.0.1:9222...")

    try:
        # Connect to Chrome
        browser = pychrome.Browser(url="http://127.0.0.1:9222")
        tabs = browser.list_tab()

        print(f"\n✓ Connected successfully")
        print(f"✓ 连接成功")
        print(f"\nFound {len(tabs)} tabs")
        print(f"找到 {len(tabs)} 个标签页")

        results = []

        for i, tab in enumerate(tabs):
            print(f"\n{'='*50}")
            print(f"Tab {i+1} / 标签页 {i+1}")
            print(f"{'='*50}")

            # Start the tab
            tab.start()

            try:
                # Enable necessary domains
                tab.call_method("Page.enable")
                tab.call_method("DOM.enable")
                tab.call_method("Runtime.enable")
                tab.call_method("Network.enable")

                # Wait for page to stabilize
                time.sleep(2)

                # Get page info
                try:
                    # Get URL
                    url_result = tab.call_method("Runtime.evaluate",
                                                expression="location.href",
                                                returnByValue=True)
                    url = url_result.get('result', {}).get('value', 'unknown')

                    # Get title
                    title_result = tab.call_method("Runtime.evaluate",
                                                  expression="document.title",
                                                  returnByValue=True)
                    title = title_result.get('result', {}).get('value', 'No title')

                    print(f"URL: {url}")
                    print(f"Title: {title}")

                except Exception as e:
                    print(f"Error getting page info: {e}")
                    url = tab.url if hasattr(tab, 'url') else 'unknown'
                    title = 'Error getting title'

                # Get document HTML
                try:
                    # Method 1: Using DOM.getDocument
                    doc = tab.call_method("DOM.getDocument", depth=-1)
                    root_id = doc['root']['nodeId']
                    outer_html = tab.call_method("DOM.getOuterHTML", nodeId=root_id)
                    html = outer_html['outerHTML']

                    print(f"✓ HTML extracted via DOM API")
                    print(f"HTML Length: {len(html)} bytes")

                except Exception as e:
                    print(f"DOM extraction failed, trying Runtime.evaluate: {e}")

                    # Method 2: Fallback to Runtime.evaluate
                    try:
                        html_result = tab.call_method("Runtime.evaluate",
                                                     expression="document.documentElement.outerHTML",
                                                     returnByValue=True)
                        html = html_result.get('result', {}).get('value', '')
                        print(f"✓ HTML extracted via Runtime.evaluate")
                        print(f"HTML Length: {len(html)} bytes")
                    except Exception as e2:
                        print(f"Runtime.evaluate also failed: {e2}")
                        html = "<html><body>Error extracting HTML</body></html>"

                # Save HTML
                html_filename = f"pychrome_tab{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                html_path = os.path.join(OUT_DIR, html_filename)
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"HTML saved: {html_path}")

                # Take screenshot
                screenshot_path = None
                try:
                    # Ensure page is visible
                    tab.call_method("Page.bringToFront")
                    time.sleep(0.5)

                    # Capture screenshot
                    screenshot_result = tab.call_method("Page.captureScreenshot",
                                                       format="png",
                                                       quality=90,
                                                       fromSurface=True)

                    if 'data' in screenshot_result:
                        img_data = base64.b64decode(screenshot_result['data'])
                        screenshot_filename = f"pychrome_tab{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        screenshot_path = os.path.join(OUT_DIR, screenshot_filename)
                        with open(screenshot_path, 'wb') as f:
                            f.write(img_data)
                        print(f"Screenshot saved: {screenshot_path}")
                    else:
                        print("Screenshot capture returned no data")

                except Exception as e:
                    print(f"Screenshot failed: {e}")

                # Analyze content
                body_len = len(html)
                has_real_content = body_len > 1000
                is_empty_html = html.strip() == '<html><head></head><body></body></html>'

                # Check for specific content indicators
                has_article_content = False
                article_indicators = ['article', 'content', '内容', '正文', 'main-content', 'post-content']
                for indicator in article_indicators:
                    if indicator in html.lower():
                        has_article_content = True
                        break

                # Check for JavaScript-rendered content
                js_check = None
                try:
                    js_result = tab.call_method("Runtime.evaluate",
                                               expression="document.querySelectorAll('*').length",
                                               returnByValue=True)
                    dom_elements = js_result.get('result', {}).get('value', 0)
                    print(f"DOM elements count: {dom_elements}")

                    # Check if content is dynamically loaded
                    dynamic_check = tab.call_method("Runtime.evaluate",
                                                   expression="!!window.React || !!window.Vue || !!window.angular",
                                                   returnByValue=True)
                    has_spa_framework = dynamic_check.get('result', {}).get('value', False)
                    if has_spa_framework:
                        print("✓ SPA framework detected (React/Vue/Angular)")

                    js_check = {'dom_elements': dom_elements, 'has_spa': has_spa_framework}

                except Exception as e:
                    print(f"JavaScript check failed: {e}")

                # Determine status
                if has_real_content and has_article_content:
                    status = "SUCCESS"
                elif has_real_content:
                    status = "PARTIAL"
                elif is_empty_html:
                    status = "EMPTY"
                else:
                    status = "SUSPICIOUS"

                result = {
                    'tab_index': i+1,
                    'url': url,
                    'title': title,
                    'html_path': html_path,
                    'screenshot': screenshot_path,
                    'body_len': body_len,
                    'has_real_content': has_real_content,
                    'has_article_content': has_article_content,
                    'is_empty_html': is_empty_html,
                    'js_check': js_check,
                    'status': status,
                    'timestamp': datetime.now().isoformat()
                }
                results.append(result)

                print(f"\nAnalysis / 分析:")
                print(f"  Status: {status}")
                print(f"  Has real content: {has_real_content}")
                print(f"  Has article indicators: {has_article_content}")
                print(f"  Body length: {body_len} bytes")

                # Show content preview if available
                if has_real_content:
                    print(f"\nContent preview / 内容预览:")
                    body_start = html.find('<body')
                    if body_start > 0:
                        body_end = body_start + 500
                        preview = html[body_start:body_end]
                        print(preview[:200] + "..." if len(preview) > 200 else preview)

                # Try to extract specific content using CDP
                if 'cebbank' in url.lower():
                    print(f"\n特定内容检查 / Specific content check for CEB Bank:")

                    # Try to find article content directly
                    try:
                        article_check = tab.call_method("Runtime.evaluate",
                                                       expression="""
                                                       (function() {
                                                           var article = document.querySelector('article, .article, .content, .main-content');
                                                           return article ? article.innerText.substring(0, 200) : 'No article found';
                                                       })()
                                                       """,
                                                       returnByValue=True)
                        article_preview = article_check.get('result', {}).get('value', '')
                        if article_preview and article_preview != 'No article found':
                            print(f"  ✓ Article content found: {article_preview[:100]}...")
                        else:
                            print(f"  ✗ No article content found via JavaScript")

                    except Exception as e:
                        print(f"  Error checking for article: {e}")

            except Exception as e:
                print(f"Error processing tab {i+1}: {e}")
                result = {
                    'tab_index': i+1,
                    'error': str(e),
                    'status': 'ERROR',
                    'timestamp': datetime.now().isoformat()
                }
                results.append(result)

            finally:
                tab.stop()

        # Save results JSON
        results_file = os.path.join(OUT_DIR, f'pychrome_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print(f"Results saved to: {results_file}")
        print(f"结果已保存到: {results_file}")

        # Summary
        print(f"\n{'='*60}")
        print("SUMMARY / 总结")
        print(f"{'='*60}")
        for r in results:
            status_emoji = {
                'SUCCESS': '✅',
                'PARTIAL': '⚠️',
                'EMPTY': '❌',
                'SUSPICIOUS': '🔍',
                'ERROR': '💥'
            }.get(r['status'], '❓')

            print(f"{status_emoji} Tab {r['tab_index']}: {r['status']}")
            if 'url' in r:
                print(f"   URL: {r['url'][:80]}...")
                print(f"   Size: {r.get('body_len', 0)} bytes")
            else:
                print(f"   Error: {r.get('error', 'Unknown error')}")

        return results

    except Exception as e:
        print(f"\n✗ Connection Error: {e}")
        print(f"✗ 连接错误: {e}")

        # Save error log
        error_log = os.path.join(OUT_DIR, f'pychrome_error_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
        with open(error_log, 'w') as f:
            f.write(f"Error connecting to Chrome via CDP\n")
            f.write(f"错误：无法通过CDP连接Chrome\n\n")
            f.write(f"Error details: {str(e)}\n")
            f.write(f"\nPossible causes:\n")
            f.write("1. Chrome not started with --remote-debugging-port=9222\n")
            f.write("2. Chrome debug port blocked or in use\n")
            f.write("3. pychrome not properly installed\n")
            f.write("4. Network/firewall blocking local connection\n")

        print(f"\nError log saved to: {error_log}")
        return None

if __name__ == '__main__':
    print("\n" + "="*60)
    print("MANUAL CHROME CDP/PYCHROME TEST")
    print("手动Chrome CDP/pychrome测试")
    print("="*60)

    if not PYCHROME_AVAILABLE:
        print("\n❌ pychrome is not installed!")
        print("Please install it first:")
        print("  pip install pychrome")
        exit(1)

    print("\nPre-flight checklist / 预检清单:")
    print("1. ✓ Chrome started with debug port 9222?")
    print("2. ✓ Target page manually opened in Chrome?")
    print("3. ✓ Page fully loaded?")
    print("4. ✓ pychrome installed?")

    input("\nPress Enter to continue... / 按回车继续...")

    results = pychrome_capture()

    if results:
        print("\n" + "="*60)
        print("TEST COMPLETED SUCCESSFULLY")
        print("测试成功完成")
        print("="*60)

        # Provide next steps
        print("\nNext steps / 下一步:")
        print("1. Review HTML files in test_artifacts/")
        print("2. Compare with Selenium test results")
        print("3. Check if CDP extracted more content than Selenium")
        print("4. Document all findings in comprehensive report")
    else:
        print("\n" + "="*60)
        print("TEST FAILED")
        print("测试失败")
        print("="*60)
        print("\nTroubleshooting steps:")
        print("1. Verify Chrome is running with --remote-debugging-port=9222")
        print("2. Try: curl http://127.0.0.1:9222/json/version")
        print("3. Check if another process is using port 9222")
        print("4. Restart Chrome with debug port and try again")