#!/usr/bin/env python3
"""测试新华网内容提取"""

import re
import html as ihtml

def test_extraction():
    with open("test_xinhua.html", 'r', encoding='utf-8') as f:
        html = f.read()
    
    print("=== 测试新华网内容提取 ===\n")
    
    # 1. 检查span#detailContent
    pattern1 = r'<span[^>]+id=["\']detailContent["\'][^>]*>(.*?)</span>'
    m1 = re.search(pattern1, html, re.I|re.S)
    if m1:
        print("✓ Found span#detailContent")
        raw_content = m1.group(1)
        print(f"  Raw content length: {len(raw_content)}")
        
        # 清理HTML标签
        content = re.sub(r'<p[^>]*>', '\n\n', raw_content)
        content = re.sub(r'</p>', '', content)
        content = re.sub(r'<[^>]+>', '', content)
        content = ihtml.unescape(content).strip()
        
        print(f"  Clean text length: {len(content)}")
        print(f"  First 200 chars: {content[:200]}...")
    else:
        print("✗ span#detailContent not found")
    
    # 2. 测试generic_to_markdown使用的通用模式
    print("\n=== 测试通用内容选择器 ===\n")
    
    content_selectors = [
        r'<div[^>]+class=["\'][^"\']*content[^"\']*["\'][^>]*>(.*?)</div>',
        r'<div[^>]+id=["\'][^"\']*content[^"\']*["\'][^>]*>(.*?)</div>',
    ]
    
    for i, pattern in enumerate(content_selectors, 1):
        m = re.search(pattern, html, re.I|re.S)
        if m:
            print(f"✓ Pattern {i} matched: {pattern[:50]}...")
            content_raw = m.group(1)
            print(f"  Raw content length: {len(content_raw)}")
            # 检查是否包含实际内容
            if 'detailContent' in content_raw:
                print("  Contains detailContent span")
            break
    
    # 3. 检查段落提取
    print("\n=== 测试段落提取 ===\n")
    generic_p_pattern = r'<p[^>]*>(.*?)</p>'
    p_matches = re.findall(generic_p_pattern, html, re.I|re.S)
    
    meaningful_paragraphs = []
    for p in p_matches:
        # 清理HTML标签
        text = re.sub(r'<[^>]+>', '', p)
        text = ihtml.unescape(text).strip()
        # 过滤短文本和脚本内容
        if text and len(text) > 10 and not text.startswith('var '):
            meaningful_paragraphs.append(text)
    
    print(f"Total <p> tags found: {len(p_matches)}")
    print(f"Meaningful paragraphs: {len(meaningful_paragraphs)}")
    if meaningful_paragraphs:
        print(f"First paragraph: {meaningful_paragraphs[0][:100]}...")
        print(f"Total content length: {sum(len(p) for p in meaningful_paragraphs)}")

if __name__ == "__main__":
    test_extraction()