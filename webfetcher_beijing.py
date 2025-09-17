#!/usr/bin/env python3
import sys
import re
import requests
from bs4 import BeautifulSoup

def fetch_beijing_gov_page(url):
    """专门处理北京政府网站页面的抓取"""
    response = requests.get(url, timeout=30)
    response.encoding = 'utf-8'
    html = response.text
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # 提取标题
    title = soup.find('title')
    title = title.text if title else '未命名'
    
    # 查找正文内容 - 北京政府网站的正文通常在 class="view" 或 class="TRS_UEDITOR" 中
    content_div = soup.find('div', class_='view') or soup.find('div', class_='TRS_UEDITOR')
    
    if content_div:
        # 移除图片标签，保留文本
        for img in content_div.find_all('img'):
            img.decompose()
        content = content_div.get_text(strip=True)
    else:
        # 如果找不到特定div，尝试从meta标签获取
        meta_desc = soup.find('meta', attrs={'name': 'Description'})
        content = meta_desc.get('content', '') if meta_desc else ''
    
    # 提取发布时间
    pub_date = ''
    meta_date = soup.find('meta', attrs={'name': 'PubDate'})
    if meta_date:
        pub_date = meta_date.get('content', '')
    
    # 提取来源
    source = ''
    meta_source = soup.find('meta', attrs={'name': 'ContentSource'})
    if meta_source:
        source = meta_source.get('content', '')
    
    # 格式化输出
    print(f"# {title}\n")
    print(f"- 标题: {title}")
    if pub_date:
        print(f"- 发布时间: {pub_date}")
    if source:
        print(f"- 内容来源: {source}")
    print(f"- 页面URL: {url}")
    print(f"\n## 正文内容\n")
    print(content)
    
    # 同时显示meta描述（用于对比）
    meta_desc = soup.find('meta', attrs={'name': 'Description'})
    if meta_desc:
        meta_content = meta_desc.get('content', '')
        if meta_content and meta_content != content:
            print(f"\n## Meta描述信息（可能过时）\n")
            print(meta_content)

if __name__ == "__main__":
    url = "https://www.beijing.gov.cn/gongkai/sld/swld/swcw/202207/t20220701_2761154.html"
    if len(sys.argv) > 1:
        url = sys.argv[1]
    fetch_beijing_gov_page(url)
