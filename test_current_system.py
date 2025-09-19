#!/usr/bin/env python3
"""
测试当前webfetcher.py系统的能力和局限性
用于验证升级方案的必要性
"""

import subprocess
import json
import time
from pathlib import Path

def run_webfetcher(url, extra_args=None):
    """运行webfetcher并返回结果"""
    cmd = ["python", "webfetcher.py", url]
    if extra_args:
        cmd.extend(extra_args)
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd="/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher"
        )
        elapsed = time.time() - start_time
        
        # 获取输出的文件名
        output_file = result.stdout.strip() if result.stdout else None
        
        return {
            "success": result.returncode == 0,
            "output_file": output_file,
            "stderr": result.stderr,
            "elapsed_time": elapsed,
            "error": None
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output_file": None,
            "stderr": "Timeout exceeded",
            "elapsed_time": 60,
            "error": "TIMEOUT"
        }
    except Exception as e:
        return {
            "success": False,
            "output_file": None,
            "stderr": str(e),
            "elapsed_time": time.time() - start_time,
            "error": str(e)
        }

def read_output_content(filename):
    """读取输出文件内容"""
    if not filename:
        return None
    
    file_path = Path(f"/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher") / filename
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 简单统计
            return {
                "lines": len(content.splitlines()),
                "chars": len(content),
                "has_content": len(content.strip()) > 100,
                "preview": content[:500] if content else ""
            }
    return None

# 测试用例
test_cases = [
    {
        "name": "静态HTML页面",
        "url": "https://example.com",
        "expected": "应该能正确提取",
        "render": False
    },
    {
        "name": "React官网（SPA）",
        "url": "https://react.dev/learn",
        "expected": "可能只能提取到框架，无法获取动态内容",
        "render": False
    },
    {
        "name": "React官网（带渲染）",
        "url": "https://react.dev/learn",
        "expected": "使用Playwright应该能获取更多内容",
        "render": True
    },
    {
        "name": "Medium文章（懒加载）",
        "url": "https://medium.com/@tusharaggarwal272/python-vs-javascript-what-to-choose-in-2024-33eca4ceb9a6",
        "expected": "可能无法获取懒加载的图片和评论",
        "render": False
    },
    {
        "name": "Twitter/X（需要登录）",
        "url": "https://x.com/OpenAI",
        "expected": "应该无法获取，需要认证",
        "render": False
    },
    {
        "name": "GitHub API文档（多页面）",
        "url": "https://docs.github.com/en/rest",
        "expected": "只能获取单页，无法自动翻页",
        "render": False
    },
    {
        "name": "YouTube视频页面",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "expected": "只能获取页面框架，无法获取评论等动态内容",
        "render": False
    },
    {
        "name": "Cloudflare保护的网站",
        "url": "https://www.cloudflare.com/",
        "expected": "可能被反爬虫机制阻止",
        "render": False
    }
]

print("=" * 80)
print("当前 webfetcher.py 系统能力测试")
print("=" * 80)
print()

results = []

for i, test in enumerate(test_cases, 1):
    print(f"\n测试 {i}/{len(test_cases)}: {test['name']}")
    print(f"URL: {test['url']}")
    print(f"预期: {test['expected']}")
    print(f"使用渲染: {'是' if test.get('render') else '否'}")
    print("-" * 40)
    
    # 准备参数
    args = []
    if test.get('render'):
        args.extend(['--render', 'always'])
    
    # 运行测试
    print("正在运行...")
    result = run_webfetcher(test['url'], args)
    
    # 分析结果
    if result['success']:
        print(f"✓ 成功 - 耗时: {result['elapsed_time']:.2f}秒")
        content = read_output_content(result['output_file'])
        if content:
            print(f"  内容: {content['lines']} 行, {content['chars']} 字符")
            print(f"  有效内容: {'是' if content['has_content'] else '否'}")
    else:
        print(f"✗ 失败 - 错误: {result['error'] or '未知'}")
        if result['stderr']:
            print(f"  错误信息: {result['stderr'][:200]}")
    
    # 记录结果
    results.append({
        "test": test['name'],
        "url": test['url'],
        "success": result['success'],
        "time": result['elapsed_time'],
        "error": result['error'],
        "render_used": test.get('render', False)
    })

# 总结
print("\n" + "=" * 80)
print("测试总结")
print("=" * 80)

success_count = sum(1 for r in results if r['success'])
fail_count = len(results) - success_count

print(f"\n成功: {success_count}/{len(results)}")
print(f"失败: {fail_count}/{len(results)}")
print(f"成功率: {success_count/len(results)*100:.1f}%")

print("\n失败的测试:")
for r in results:
    if not r['success']:
        print(f"  - {r['test']}: {r['error'] or '提取失败'}")

print("\n性能统计:")
successful_times = [r['time'] for r in results if r['success']]
if successful_times:
    print(f"  平均耗时: {sum(successful_times)/len(successful_times):.2f}秒")
    print(f"  最快: {min(successful_times):.2f}秒")
    print(f"  最慢: {max(successful_times):.2f}秒")

# 保存测试报告
report = {
    "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
    "results": results,
    "summary": {
        "total": len(results),
        "success": success_count,
        "fail": fail_count,
        "success_rate": success_count/len(results)*100
    }
}

with open("test_current_system_report.json", "w", encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print("\n测试报告已保存到: test_current_system_report.json")