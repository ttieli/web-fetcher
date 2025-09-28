#!/usr/bin/env python3
"""详细测试新华网内容提取问题"""

import re
import html as ihtml
from pathlib import Path

def test_span_extraction():
    """测试span标签的内容提取"""
    html = Path("test_xinhua.html").read_text(encoding='utf-8')
    
    print("=== 测试span#detailContent提取 ===\n")
    
    # 使用generic_to_markdown中不会匹配的模式
    # 注意：generic_to_markdown搜索的是<div>标签，不是<span>标签！
    patterns_that_wont_match = [
        r'<div[^>]+class=["\'][^"\']*content[^"\']*["\'][^>]*>(.*?)</div>',
        r'<div[^>]+id=["\'][^"\']*content[^"\']*["\'][^>]*>(.*?)</div>',
    ]
    
    for pattern in patterns_that_wont_match:
        m = re.search(pattern, html, re.I|re.S)
        if m:
            print(f"✓ Pattern matched: {pattern[:50]}...")
        else:
            print(f"✗ Pattern NOT matched: {pattern[:50]}...")
    
    print("\n=== 正确的新华网选择器 ===\n")
    
    # 新华网使用<span id="detailContent">，而不是<div>
    correct_pattern = r'<span[^>]+id=["\']detailContent["\'][^>]*>(.*?)</span>'
    m = re.search(correct_pattern, html, re.I|re.S)
    if m:
        print("✓ Found span#detailContent")
        content = m.group(1)
        
        # 提取所有段落
        p_pattern = r'<p[^>]*>(.*?)</p>'
        paragraphs = re.findall(p_pattern, content, re.I|re.S)
        
        print(f"  Found {len(paragraphs)} paragraphs")
        
        # 清理并显示内容
        clean_paragraphs = []
        for p in paragraphs:
            text = re.sub(r'<[^>]+>', '', p)
            text = ihtml.unescape(text).strip()
            if text:
                clean_paragraphs.append(text)
                
        print(f"  Clean paragraphs: {len(clean_paragraphs)}")
        print(f"  Total text length: {sum(len(p) for p in clean_paragraphs)}")
        
        # 显示完整内容
        print("\n=== 完整内容 ===\n")
        for i, p in enumerate(clean_paragraphs, 1):
            print(f"段落{i}: {p}\n")
    
    print("\n=== 问题分析 ===\n")
    print("1. 新华网使用 <span id='detailContent'> 包裹内容，而不是 <div>")
    print("2. generic_to_markdown 函数只搜索 <div> 标签，不搜索 <span> 标签")
    print("3. 因此内容无法通过 Priority 3 的选择器提取")
    print("4. 最终依赖 Priority 4 的通用段落提取，只能获取到标题（前两个段落）")
    print("\n结论：generic_to_markdown 需要增加对 <span id='detailContent'> 的支持")

if __name__ == "__main__":
    test_span_extraction()