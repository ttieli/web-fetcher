#!/usr/bin/env python3
"""
Test attaching Selenium to manually-opened Chrome
测试将Selenium附加到手动打开的Chrome浏览器

Usage:
1. First start Chrome with debug port:
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
     --remote-debugging-port=9222 \
     --user-data-dir=/tmp/chrome-manual-test \
     --no-first-run \
     --disable-extensions

2. Manually navigate to target URL in that Chrome

3. Run this script to extract content
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import os
import time
import json
from datetime import datetime

OUT_DIR = "test_artifacts"
os.makedirs(OUT_DIR, exist_ok=True)

def attach_and_capture():
    """
    Attach to manually-opened Chrome and capture content
    附加到手动打开的Chrome并捕获内容
    """
    print("=" * 60)
    print("Manual Chrome Selenium Attachment Test")
    print("手动Chrome Selenium附加测试")
    print("=" * 60)
    print(f"\n时间 / Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nAttempting to attach to Chrome debug session on port 9222...")
    print("尝试连接到9222端口的Chrome调试会话...")

    options = Options()
    options.debugger_address = "127.0.0.1:9222"

    try:
        # Attach to existing Chrome
        driver = webdriver.Chrome(options=options)
        print("✓ Successfully attached to Chrome")
        print("✓ 成功连接到Chrome")

        # Get all window handles (tabs)
        handles = driver.window_handles
        print(f"\nFound {len(handles)} tabs")
        print(f"找到 {len(handles)} 个标签页")

        results = []

        for i, handle in enumerate(handles):
            driver.switch_to.window(handle)

            url = driver.current_url
            title = driver.title
            html = driver.page_source

            print(f"\n{'='*50}")
            print(f"Tab {i+1} / 标签页 {i+1}")
            print(f"{'='*50}")
            print(f"URL: {url}")
            print(f"Title: {title}")
            print(f"HTML Length: {len(html)} bytes")

            # Save HTML
            html_filename = f"selenium_tab{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            html_path = os.path.join(OUT_DIR, html_filename)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"HTML saved: {html_path}")

            # Save screenshot
            screenshot_filename = f"selenium_tab{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            screenshot_path = os.path.join(OUT_DIR, screenshot_filename)
            try:
                driver.save_screenshot(screenshot_path)
                print(f"Screenshot saved: {screenshot_path}")
            except Exception as e:
                print(f"Screenshot failed: {e}")
                screenshot_path = None

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

            # Try to find specific CEB Bank content
            if 'cebbank' in url.lower():
                print(f"\n特定内容检查 / Specific content check for CEB Bank:")
                ceb_indicators = ['中国光大银行', '光大银行', '公告', '招标', '采购']
                found_indicators = []
                for indicator in ceb_indicators:
                    if indicator in html:
                        found_indicators.append(indicator)

                if found_indicators:
                    print(f"  ✓ Found CEB indicators: {', '.join(found_indicators)}")
                else:
                    print(f"  ✗ No CEB specific content found")

        # Save results JSON
        results_file = os.path.join(OUT_DIR, f'selenium_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
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
                'SUSPICIOUS': '🔍'
            }.get(r['status'], '❓')

            print(f"{status_emoji} Tab {r['tab_index']}: {r['status']} - {r['body_len']} bytes")
            print(f"   URL: {r['url'][:80]}...")

        return results

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print(f"✗ 错误: {e}")

        # Save error log
        error_log = os.path.join(OUT_DIR, f'selenium_error_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
        with open(error_log, 'w') as f:
            f.write(f"Error attaching to Chrome debug session\n")
            f.write(f"错误：无法连接Chrome调试会话\n\n")
            f.write(f"Error details: {str(e)}\n")
            f.write(f"\nPossible causes:\n")
            f.write("1. Chrome not started with --remote-debugging-port=9222\n")
            f.write("2. Chrome debug port blocked or in use\n")
            f.write("3. WebDriver version mismatch\n")

        print(f"\nError log saved to: {error_log}")
        return None

if __name__ == '__main__':
    print("\n" + "="*60)
    print("MANUAL CHROME SELENIUM TEST")
    print("手动Chrome Selenium测试")
    print("="*60)

    print("\nPre-flight checklist / 预检清单:")
    print("1. ✓ Chrome started with debug port 9222?")
    print("2. ✓ Target page manually opened in Chrome?")
    print("3. ✓ Page fully loaded?")

    input("\nPress Enter to continue... / 按回车继续...")

    results = attach_and_capture()

    if results:
        print("\n" + "="*60)
        print("TEST COMPLETED SUCCESSFULLY")
        print("测试成功完成")
        print("="*60)

        # Provide next steps
        print("\nNext steps / 下一步:")
        print("1. Review HTML files in test_artifacts/")
        print("2. Compare screenshots with what you saw manually")
        print("3. Run pychrome test for comparison")
        print("4. Document findings in TASKS/test-manual-chrome-hybrid-approach.md")
    else:
        print("\n" + "="*60)
        print("TEST FAILED")
        print("测试失败")
        print("="*60)
        print("\nPlease check:")
        print("1. Chrome is running with --remote-debugging-port=9222")
        print("2. No other process is using port 9222")
        print("3. Selenium and ChromeDriver are properly installed")