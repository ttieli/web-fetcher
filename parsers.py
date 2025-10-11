#!/usr/bin/env python3
"""
Web content parsers for different site types.
Extracted from webfetcher.py for better modularity.

Phase 3.5: Integration with template-based parsers
"""

__version__ = "3.5.0"
__author__ = "WebFetcher Team"

# Standard library imports
import os
import re
import json
import html as ihtml
import datetime
import urllib.parse
import logging
from typing import Optional, List, Dict, Set, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from html.parser import HTMLParser
import signal
import time

# BeautifulSoup import and availability flag
try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False

# Configure module logger
logger = logging.getLogger(__name__)

# Import template-based parsers from parsers_migrated
from parsers_migrated import (
    xhs_to_markdown as xhs_to_markdown_migrated,
    wechat_to_markdown as wechat_to_markdown_migrated,
    generic_to_markdown as generic_to_markdown_migrated
)

def get_beautifulsoup_parser():
    """
    Get the best available BeautifulSoup parser.
    Tries lxml first (faster), falls back to html.parser (built-in).
    """
    if not BEAUTIFULSOUP_AVAILABLE:
        # Return None to trigger fallback behavior
        return None
    
    parsers_order = ['lxml', 'html.parser']
    for parser in parsers_order:
        try:
            from bs4 import BeautifulSoup
            # Test if parser works
            BeautifulSoup('<html></html>', parser)
            return parser
        except:
            continue
    
    # Default to html.parser as last resort
    return 'html.parser' 

class PageType(Enum):
    """页面类型枚举"""
    ARTICLE = "article"      # 文章页面
    LIST_INDEX = "list"      # 列表索引页面

# Data classes that may be needed
@dataclass
class ListItem:
    """Represents a list item extracted from HTML content."""
    title: str
    url: str
    description: str = ""
    date: str = ""
    author: str = ""
    summary: str = ""
    index: int = 0

@dataclass
class XHSImageData:
    """Structured representation of XiaoHongShu image data"""
    url: str
    pic_id: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    is_cover: bool = False
    processing_params: Optional[Dict[str, str]] = None
    source: str = "unknown"  # Track extraction source for debugging

# NOTE: FetchMetrics stays in webfetcher.py for now, will be imported in Phase 2

def add_metrics_to_markdown(md_content: str, metrics) -> str:
    """Add fetch metrics to markdown content as HTML comment and footer."""
    # Add HTML comment at the top with detailed metrics
    detailed_comment = f"""<!-- Fetch Metrics:
  Method: {metrics.primary_method}
  Fallback: {metrics.fallback_method or 'None'}
  Attempts: {metrics.total_attempts}
  Fetch Duration: {metrics.fetch_duration:.3f}s
  Render Duration: {metrics.render_duration:.3f}s
  SSL Fallback: {metrics.ssl_fallback_used}
  Status: {metrics.final_status}
  Error: {metrics.error_message or 'None'}
-->

"""
    
    # Add visible footer with summary
    footer = f"\n\n---\n\n*{metrics.get_summary()}*\n"
    
    return detailed_comment + md_content + footer


# Helper functions for parsers

def extract_meta(html: str, name_or_prop: str) -> str:
    m = re.search(rf'<meta[^>]+(?:name|property)=["\']{re.escape(name_or_prop)}["\'][^>]+content=["\']([^"\']*)["\']', html, re.I)
    return ihtml.unescape(m.group(1).strip()) if m else ""


def extract_json_ld_content(html: str) -> dict:
    """Extract content from JSON-LD structured data."""
    import json
    
    result = {
        'description': '',
        'articleBody': '',
        'datePublished': '',
        'dateModified': '',
        'author': ''
    }
    
    # Find all JSON-LD scripts
    pattern = r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
    matches = re.findall(pattern, html, re.I | re.S)
    
    for match in matches:
        try:
            data = json.loads(match.strip())
            
            # Handle both single object and @graph array
            items = data.get('@graph', [data]) if isinstance(data, dict) else [data]
            
            for item in items:
                if not isinstance(item, dict):
                    continue
                    
                item_type = item.get('@type', '')
                
                # Check for Article-like types
                if any(t in str(item_type) for t in ['Article', 'NewsArticle', 'BlogPosting']):
                    result['description'] = item.get('description', result['description'])
                    result['articleBody'] = item.get('articleBody', item.get('text', result['articleBody']))
                    result['datePublished'] = item.get('datePublished', result['datePublished'])
                    result['dateModified'] = item.get('dateModified', result['dateModified'])
                    
                    # Extract author
                    author = item.get('author', {})
                    if isinstance(author, dict):
                        result['author'] = author.get('name', '')
                    elif isinstance(author, str):
                        result['author'] = author
                
                # Also check Person/Organization for government sites
                elif 'Person' in str(item_type) or 'Organization' in str(item_type):
                    if not result['description']:
                        result['description'] = item.get('description', '')
        except (json.JSONDecodeError, AttributeError):
            continue
    
    return result


def extract_from_modern_selectors(html: str) -> str:
    """
    Enhanced content extraction for modern static site generators and SPAs.

    Phase 1 Optimization:
    - Prioritize HTML5 semantic tags (main, article) for better SPA support
    - Add SPA container selectors (div#root, div#app, div#__next)
    - Increase content validation threshold to 500 bytes
    - Implement smart selection when multiple candidates exist
    """
    import re
    import html as ihtml

    # PHASE 1: Optimized selector priority order
    # Higher priority selectors come first for better performance
    content_selectors = [
        # Priority 1: HTML5 semantic elements (most reliable for SPAs like React.dev)
        r'<main[^>]*>(.*?)</main>',
        r'<article[^>]*>(.*?)</article>',

        # Priority 2: SPA framework containers (React, Vue, Next.js)
        r'<div[^>]*id=["\']root["\'][^>]*>(.*?)</div>',
        r'<div[^>]*id=["\']app["\'][^>]*>(.*?)</div>',
        r'<div[^>]*id=["\']__next["\'][^>]*>(.*?)</div>',

        # Priority 3: ARIA roles for accessibility-focused sites
        r'<div[^>]*role=["\']main["\'][^>]*>(.*?)</div>',

        # Priority 4: News sites specific patterns (news.cn uses span#detailContent)
        r'<span[^>]*id=["\']detailContent["\'][^>]*>(.*?)</span>',
        r'<div[^>]*id=["\']detailContent["\'][^>]*>(.*?)</div>',

        # Priority 5: Generic CMS patterns
        r'<div[^>]*class=["\'][^"\']*main-content[^"\']*["\'][^>]*>(.*?)</div>',
        r'<div[^>]*class=["\'][^"\']*entry-content[^"\']*["\'][^>]*>(.*?)</div>',

        # Priority 6: Hugo/Jekyll specific patterns
        r'<div[^>]*class=["\'][^"\']*post-content[^"\']*["\'][^>]*>(.*?)</div>',
        r'<div[^>]*class=["\'][^"\']*article-content[^"\']*["\'][^>]*>(.*?)</div>',
        r'<div[^>]*class=["\'][^"\']*hero-content[^"\']*["\'][^>]*>(.*?)</div>',
        r'<div[^>]*class=["\'][^"\']*content[^"\']*["\'][^>]*>(.*?)</div>',

        # Priority 7: Generic content sections
        r'<section[^>]*class=["\'][^"\']*content[^"\']*["\'][^>]*>(.*?)</section>',

        # Priority 8: Landing page patterns (LOWER priority to avoid short snippets)
        r'<div[^>]*class=["\'][^"\']*intro[^"\']*["\'][^>]*>(.*?)</div>',
        r'<div[^>]*class=["\'][^"\']*description[^"\']*["\'][^>]*>(.*?)</div>',
        # NOTE: div.lead moved to lower priority due to React.dev issue (25 bytes extracted)
    ]
    
    # FIXED: Collect ALL matching content instead of returning first match
    all_content = []
    seen_starts = set()  # For intelligent deduplication
    
    # Special handling for news.cn style span#detailContent (non-greedy won't work due to nested spans)
    if 'detailContent' in html:
        import re
        # Find the starting position of detailContent
        match = re.search(r'<span[^>]*id=["\']detailContent["\'][^>]*>', html, re.I)
        if match:
            start_pos = match.end()
            # Find the matching closing span by counting nested spans
            span_count = 1
            pos = start_pos
            while span_count > 0 and pos < len(html):
                # Look for opening span tags (must have > or space after 'span')
                if html[pos:pos+5].lower() == '<span' and (pos+5 >= len(html) or html[pos+5] in ' >'):
                    # Find the end of this opening tag
                    end_tag = html.find('>', pos)
                    if end_tag != -1:
                        span_count += 1
                        pos = end_tag + 1
                    else:
                        pos += 1
                elif html[pos:pos+7].lower() == '</span>':
                    span_count -= 1
                    if span_count == 0:
                        # Extract content between the tags
                        content_html = html[start_pos:pos]
                        text = extract_text_from_html_fragment(content_html)
                        if text and len(text.strip()) > 50:  # Lower threshold for news content
                            text_start = text[:100].strip()
                            if text_start not in seen_starts:
                                all_content.append(text.strip())
                                seen_starts.add(text_start)
                        break
                    pos += 7
                else:
                    pos += 1
    
    # PHASE 1: Smart content extraction with validation
    # Collect candidates with their metadata for intelligent selection
    candidates = []  # List of (selector_priority, content_length, text_content)

    for priority_index, pattern in enumerate(content_selectors):
        matches = re.findall(pattern, html, re.I | re.S)
        for match in matches:
            # Clean and extract text content
            text = extract_text_from_html_fragment(match)
            content_length = len(text.strip())

            # PHASE 1: Increased validation threshold from 200 to 500 bytes
            # This prevents extraction of short snippets like the 25-byte div.lead on React.dev
            if text and content_length >= 500:
                # Intelligent deduplication: use first 100 chars as signature
                text_start = text[:100].strip()
                if text_start not in seen_starts:
                    candidates.append((priority_index, content_length, text.strip()))
                    seen_starts.add(text_start)

    # PHASE 1: Smart selection strategy
    # If we have multiple candidates, prefer higher priority AND substantial content
    if candidates:
        # Sort by: 1) priority (lower index = higher priority), 2) content length (longer = better)
        # For same priority, choose the longest content
        candidates.sort(key=lambda x: (x[0], -x[1]))

        # Strategy: Take the best candidate from the highest priority level
        best_priority = candidates[0][0]
        best_candidates = [c for c in candidates if c[0] == best_priority]

        # If multiple candidates at same priority, take the longest
        best_candidate = max(best_candidates, key=lambda x: x[1])
        all_content.append(best_candidate[2])

        # Also include other high-quality candidates if they add value
        for priority, length, text in candidates:
            if priority != best_priority and length > 1000:  # Only add substantial additional content
                text_start = text[:100].strip()
                if text_start not in seen_starts:
                    all_content.append(text)
                    seen_starts.add(text_start)

    # Join all selected content blocks with proper paragraph spacing
    return '\n\n'.join(all_content) if all_content else ''


def extract_text_from_html_fragment(html_fragment: str) -> str:
    """Extract clean text from HTML fragment, preserving paragraph structure"""
    import re
    import html as ihtml
    
    # Replace common block elements with double newlines for paragraph separation
    html_fragment = re.sub(r'</(?:p|div|section|article|h[1-6]|li)>', '\n\n', html_fragment, flags=re.I)
    html_fragment = re.sub(r'<(?:br|hr)[^>]*/?>', '\n', html_fragment, flags=re.I)
    
    # Replace list items and other elements with single newlines
    html_fragment = re.sub(r'</(?:li|dd|dt)>', '\n', html_fragment, flags=re.I)
    
    # Remove all remaining HTML tags
    html_fragment = re.sub(r'<[^>]+>', '', html_fragment)
    
    # Decode HTML entities
    text = ihtml.unescape(html_fragment)
    
    # Clean up whitespace
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if line and not line.startswith('var ') and not line.startswith('function'):
            lines.append(line)
    
    # Join paragraphs with double newlines, remove excessive spacing
    result = '\n\n'.join(lines)
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result.strip()


def parse_date_like(s: Optional[str]) -> tuple[str, str]:
    if not s:
        now = datetime.datetime.now()
        return now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d %H:%M:%S")
    s = str(s)
    m = re.match(r"^(\d{10,})(?::\d{2})?$", s)
    dt = None
    if m:
        num = int(m.group(1))
        dt = datetime.datetime.fromtimestamp(num/1000 if num > 10_000_000_000 else num)
    if dt is None:
        s2 = s.replace('年','-').replace('月','-').replace('日','').replace('/','-')
        m2 = re.search(r'(20\d{2})-([01]?\d)-([0-3]?\d)', s2)
        if m2:
            y, mo, d = m2.groups()
            dt = datetime.datetime(int(y), int(mo), int(d))
    if dt is None:
        now = datetime.datetime.now()
        return now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d %H:%M:%S")
    return dt.strftime("%Y-%m-%d"), dt.strftime("%Y-%m-%d %H:%M:%S")


def resolve_url_with_context(base_url: str, href: str) -> str:
    """Smart URL resolution that preserves subdirectory context with enhanced edge case handling."""
    base_parts = urllib.parse.urlparse(base_url)
    
    # Handle protocol-relative URLs (starting with //)
    if href.startswith('//'):
        return f"{base_parts.scheme}:{href}"
    
    # Special case: root navigation '/' should go to domain root
    if href == '/':
        return f"{base_parts.scheme}://{base_parts.netloc}/"
    
    # Handle absolute paths - they start from the domain root
    if href.startswith('/'):
        parsed_base = urllib.parse.urlparse(base_url)
        return f"{parsed_base.scheme}://{parsed_base.netloc}{href}"
    
    # CRITICAL FIX: For relative paths (not starting with /), ensure base URL has trailing slash
    # This is essential for correct urljoin behavior with subdirectory deployments
    if not href.startswith('/') and base_parts.path and not base_parts.path.endswith('/'):
        # Check if this looks like a directory URL (common for documentation sites)
        # A URL without extension or ending with known directory patterns should be treated as directory
        if not any(base_parts.path.endswith(ext) for ext in ['.html', '.htm', '.php', '.asp', '.jsp']):
            # Add trailing slash to base URL for correct relative resolution
            base_url_fixed = base_url + '/'
            return urllib.parse.urljoin(base_url_fixed, href)
    
    # Default to standard urljoin for other cases
    return urllib.parse.urljoin(base_url, href)


def extract_list_content(html: str, base_url: str) -> tuple[str, List[ListItem]]:
    """
    从列表页面提取列表项内容
    
    提取策略：
    1. 识别主要列表容器
    2. 提取每个列表项的标题、链接、日期、摘要
    3. 清理和标准化数据
    
    Args:
        html: 页面HTML内容
        base_url: 基础URL，用于解析相对链接
        
    Returns:
        tuple: (页面标题, 列表项列表)
    """
    # 性能保护机制：内容大小和复杂度检测
    html_size = len(html)
    if html_size > 5 * 1024 * 1024:  # 超过5MB的HTML
        print(f"Warning: Large HTML content ({html_size // 1024}KB), using simplified processing")
    
    # 表格复杂度检测
    table_count = len(re.findall(r'<table[^>]*>', html, re.I))
    tr_count = len(re.findall(r'<tr[^>]*>', html, re.I))
    td_count = len(re.findall(r'<td[^>]*>', html, re.I))
    
    # 设置处理超时
    def timeout_handler(_, __):
        raise TimeoutError("List content extraction timeout after 5 seconds")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(5)  # 5秒超时
    
    try:
        # 1. 提取页面标题
        page_title = extract_meta(html, 'og:title') or extract_meta(html, 'twitter:title')
        if not page_title:
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.I | re.S)
            if title_match:
                page_title = ihtml.unescape(re.sub(r'<[^>]+>', '', title_match.group(1))).strip()
        page_title = page_title or '列表页面'
        
        # 检查是否为人民网，使用特殊处理策略
        is_people_site = 'cpc.people.com.cn' in base_url or 'people.com.cn' in base_url
        
        # 表格数量过多时使用简化策略
        if td_count > 500:
            print(f"Warning: Too many table cells ({td_count}), limiting to first 500")
            # 截断HTML以减少处理量
            html = html[:len(html)//2] if len(html) > 1024*1024 else html
        
        # 2. 定义多种列表项提取模式，针对不同网站结构
        list_patterns = []
        
        # 对于人民网使用优化的分步处理策略
        if is_people_site:
            list_patterns.append({
                'container': r'<table[^>]*>(.*?)</table>',
                'item': 'people_table_optimized',  # 标记使用优化处理
                'title_link': None,
                'date': r'(\d{4}年\d{1,2}月\d{1,2}日)',
                'special': 'people_table_optimized'
            })
        else:
            # 人民网政治局会议表格专用模式（原始版本，仅用于非人民网站点）
            list_patterns.append({
                'container': r'<table[^>]*>(.*?)</table>',
                'item': r'<tr[^>]*>.*?<td[^>]*>.*?</td>.*?<td[^>]*>.*?<center>(.*?)</center>.*?</td>.*?<td[^>]*>(.*?)</td>.*?</tr>',
                'title_link': None,  # 特殊处理
                'date': r'(\d{4}年\d{1,2}月\d{1,2}日)',
                'special': 'people_table'
            })
        
        # 添加通用模式
        list_patterns.extend([
            # 通用表格形式的列表
            {
                'container': r'<table[^>]*>(.*?)</table>',
                'item': r'<tr[^>]*>(.*?)</tr>',
                'title_link': r'<a[^>]*href=["\']([^"\']+)["\'][^>]*[^>]*>(.*?)</a>',
                'date': r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2})'
            },
            # 人民网等新闻网站的典型结构
            {
                'container': r'<ul[^>]*class=["\'][^"\']*list[^"\']*["\'][^>]*>(.*?)</ul>',
                'item': r'<li[^>]*>(.*?)</li>',
                'title_link': r'<a[^>]*href=["\']([^"\']+)["\'][^>]*[^>]*>(.*?)</a>',
                'date': r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2})'
            },
            # 带有div包装的列表项
            {
                'container': r'<div[^>]*class=["\'][^"\']*list[^"\']*["\'][^>]*>(.*?)</div>',
                'item': r'<div[^>]*class=["\'][^"\']*item[^"\']*["\'][^>]*>(.*?)</div>',
                'title_link': r'<a[^>]*href=["\']([^"\']+)["\'][^>]*[^>]*>(.*?)</a>',
                'date': r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2})'
            },
            # 通用链接提取（作为后备方案）
            {
                'container': r'<body[^>]*>(.*?)</body>',
                'item': r'<a[^>]*href=["\']([^"\']+)["\'][^>]*[^>]*>(.*?)</a>',
                'title_link': None,  # 已在item中处理
                'date': r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2})'
            }
        ])
        
        list_items = []
        
        # 3. 尝试每种模式提取列表项
        for pattern_config in list_patterns:
            container_match = re.search(pattern_config['container'], html, re.I | re.S)
            if container_match:
                container_content = container_match.group(1)
                
                # 优化的人民网表格处理
                if pattern_config.get('special') == 'people_table_optimized':
                    # 分步处理，避免复杂正则表达式的灾难性回溯
                    # 1. 先提取所有表格行
                    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', container_content, re.I | re.S)
                    row_count = 0
                    for row_html in rows:
                        row_count += 1
                        if row_count > 50:  # 限制处理行数
                            print(f"Warning: Too many table rows, stopping at {row_count}")
                            break
                            
                        # 2. 从每行中提取单元格
                        cells = re.findall(r'<td[^>]*>(.*?)</td>', row_html, re.I | re.S)
                        if len(cells) >= 3:  # 确保有足够的单元格
                            # 3. 分别处理日期和内容单元格
                            for i, cell in enumerate(cells):
                                if i >= 2:  # 只处理前3个单元格
                                    break
                                # 寻找包含center标签的单元格（通常是日期）
                                center_match = re.search(r'<center[^>]*>(.*?)</center>', cell, re.I | re.S)
                                if center_match:
                                    date_text = center_match.group(1)
                                    date = re.sub(r'<[^>]+>', '', date_text).strip()
                                    date = ihtml.unescape(date)
                                    
                                    # 从下一个单元格中提取内容
                                    if i + 1 < len(cells):
                                        content_cell = cells[i + 1]
                                        link_match = re.search(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*[^>]*>(.*?)</a>', content_cell, re.I | re.S)
                                        if link_match:
                                            href = link_match.group(1)
                                            link_text = re.sub(r'<[^>]+>', '', link_match.group(2)).strip()
                                            
                                            # 构建标题
                                            title = f"中央政治局会议 {date}"
                                            
                                            if title and href:
                                                full_url = resolve_url_with_context(base_url, href)
                                                list_items.append(ListItem(
                                                    title=title,
                                                    url=full_url,
                                                    date=date,
                                                    summary=None,
                                                    index=len(list_items) + 1
                                                ))
                                    break  # 找到一个有效的日期单元格后跳出
                
                # 特殊处理人民网表格格式（原始版本）
                elif pattern_config.get('special') == 'people_table':
                    # 人民网政治局会议特殊表格处理
                    items = re.findall(pattern_config['item'], container_content, re.I | re.S)
                    for date_text, content_html in items:
                        # 清理日期
                        date = re.sub(r'<[^>]+>', '', date_text).strip()
                        date = ihtml.unescape(date)
                        
                        # 提取链接
                        link_match = re.search(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*[^>]*>(.*?)</a>', content_html, re.I | re.S)
                        if link_match:
                            href = link_match.group(1)
                            link_text = re.sub(r'<[^>]+>', '', link_match.group(2)).strip()
                        else:
                            # 如果没有链接，跳过这项
                            continue
                        
                        # 清理内容作为摘要
                        summary_text = re.sub(r'<a[^>]*>.*?</a>', '', content_html, flags=re.I | re.S)
                        summary_text = re.sub(r'<[^>]+>', ' ', summary_text)
                        summary_text = ihtml.unescape(summary_text).strip()
                        summary = summary_text if len(summary_text) > 10 else None
                        
                        # 构建标题：会议名称 + 日期
                        title = f"中央政治局会议 {date}"
                        
                        if title and href:
                            full_url = resolve_url_with_context(base_url, href)
                            list_items.append(ListItem(
                                title=title,
                                url=full_url,
                                date=date,
                                summary=summary,
                                index=len(list_items) + 1
                            ))
                
                elif pattern_config['title_link']:
                    # 常规模式：先提取item，再提取链接
                    items = re.findall(pattern_config['item'], container_content, re.I | re.S)
                    for item_html in items:
                        link_match = re.search(pattern_config['title_link'], item_html, re.I | re.S)
                        if link_match:
                            href = link_match.group(1)
                            title_html = link_match.group(2)
                            
                            # 清理标题
                            title = re.sub(r'<[^>]+>', '', title_html).strip()
                            title = ihtml.unescape(title)
                            
                            # 提取日期
                            date_match = re.search(pattern_config['date'], item_html)
                            date = date_match.group(1) if date_match else None
                            
                            # 提取摘要（链接外的其他文本）
                            summary_text = re.sub(r'<a[^>]*>.*?</a>', '', item_html, flags=re.I | re.S)
                            summary_text = re.sub(r'<[^>]+>', ' ', summary_text)
                            summary_text = ihtml.unescape(summary_text).strip()
                            summary = summary_text if len(summary_text) > 10 else None
                            
                            if title and len(title) > 3:  # 过滤过短的标题
                                full_url = resolve_url_with_context(base_url, href)
                                list_items.append(ListItem(
                                    title=title,
                                    url=full_url,
                                    date=date,
                                    summary=summary,
                                    index=len(list_items) + 1
                                ))
                else:
                    # 直接链接模式：item就是链接
                    items = re.findall(pattern_config['item'], container_content, re.I | re.S)
                    for href, title_html in items:
                        title = re.sub(r'<[^>]+>', '', title_html).strip()
                        title = ihtml.unescape(title)
                        
                        # 过滤导航和无关链接
                        if (len(title) > 5 and 
                            not any(skip_word in title.lower() for skip_word in 
                                   ['首页', '返回', '登录', '注册', 'home', 'back', 'login', 'register', 
                                    '更多>>', '更多', '上一页', '下一页', 'prev', 'next'])):
                            
                            full_url = resolve_url_with_context(base_url, href)
                            list_items.append(ListItem(
                                title=title,
                                url=full_url,
                                date=None,
                                summary=None,
                                index=len(list_items) + 1
                            ))
        
            # 如果找到足够的列表项，就停止尝试其他模式
            if len(list_items) >= 5:
                break
        
        # 4. 去重和排序
        seen_urls = set()
        unique_items = []
        for item in list_items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                unique_items.append(item)
        
        # 限制数量，避免过多项目
        if len(unique_items) > 50:
            unique_items = unique_items[:50]
        
        # 重新编号
        for i, item in enumerate(unique_items):
            item.index = i + 1
        
        return page_title, unique_items
        
    except TimeoutError as e:
        print(f"List extraction timed out: {e}")
        return "页面处理超时", []
    except Exception as e:
        print(f"Error during list extraction: {e}")
        return "列表页面", []
    finally:
        # 清理超时设置
        signal.alarm(0)


def normalize_media_url(u: str) -> str:
    if not u:
        return u
    u = u.strip()
    if u.startswith('//'):
        return 'https:' + u
    return u


# XHSImageExtractor class - simplified version for Phase 1
class XHSImageExtractor:
    """
    Simplified XiaoHongShu image extraction for Phase 1.
    This is a minimal implementation that will trigger the fallback mechanism.
    """
    
    def __init__(self, html: str, url: str = "", debug: bool = False):
        self.html = html
        self.url = url
        self.debug = debug
    
    def extract_all(self) -> List[str]:
        """
        Simplified extraction that intentionally fails to trigger fallback.
        In Phase 2, this will be replaced with the full implementation.
        """
        # For Phase 1, we intentionally raise an exception to trigger fallback
        raise Exception("Phase 1: Using fallback extraction method")


# Site-specific parser functions









def xhs_to_markdown(html: str, url: str, url_metadata: dict = None) -> tuple[str, str, dict]:
    """
    XiaoHongShu (小红书) parser - Routes to template-based implementation

    Phase 3.5: Routing layer for xiaohongshu.com and xhslink.com domains
    Delegates to parsers_migrated for template-based parsing

    Args:
        html: HTML content of the page
        url: Source URL
        url_metadata: Optional URL tracking metadata from fetch (Task-003 Phase 1)

    Returns:
        tuple: (date_only, markdown_content, metadata)
    """
    logger.info("Phase 3.5: Routing XiaoHongShu to template-based parser")
    # Task-003 Phase 1: url_metadata accepted but not yet used (will be used in Phase 3)
    return xhs_to_markdown_migrated(html, url)


def wechat_to_markdown(html: str, url: str, url_metadata: dict = None) -> tuple[str, str, dict]:
    """
    WeChat (微信公众号) parser - Routes to template-based implementation

    Phase 3.5: Routing layer for mp.weixin.qq.com domain
    Delegates to parsers_migrated for template-based parsing

    Args:
        html: HTML content of the page
        url: Source URL
        url_metadata: Optional URL tracking metadata from fetch (Task-003 Phase 1)

    Returns:
        tuple: (date_only, markdown_content, metadata)
    """
    logger.info("Phase 3.5: Routing WeChat to template-based parser")
    # Task-003 Phase 1: url_metadata accepted but not yet used (will be used in Phase 3)
    return wechat_to_markdown_migrated(html, url)


def detect_page_type(html: str, url: Optional[str] = None, is_crawling: bool = False) -> PageType:
    """
    检测页面类型：文章页面还是列表索引页面
    
    检测策略：
    1. 链接密度分析 - 计算链接数量与文本总量的比值
    2. 列表容器识别 - 检测ul/ol/div[class*=list]等列表元素
    3. 内容结构分析 - 判断是否包含大量相似格式的链接项
    
    Args:
        html: 页面HTML内容
        url: 页面URL，用于特定网站的优先判断
        is_crawling: 是否在爬虫模式下，单页模式时跳过检测直接返回ARTICLE
        
    Returns:
        PageType: ARTICLE 或 LIST_INDEX
    """
    # Mode-aware detection: Skip detection in single-page mode
    if not is_crawling:
        # Check for emergency disable via environment variable
        if os.environ.get('WF_FORCE_PAGE_DETECTION', '').lower() == 'true':
            print("WF_FORCE_PAGE_DETECTION is set, proceeding with detection")
        else:
            print("Single-page mode: defaulting to ARTICLE type")
            return PageType.ARTICLE
    else:
        print("Crawl mode: performing full page type detection")
    
    # URL模式优先判断
    if url:
        # 12371.cn文章页面特征：包含日期路径和ARTI前缀
        if re.search(r'12371\.cn/\d{4}/\d{2}/\d{2}/ARTI\d+\.shtml', url):
            print(f"12371.cn article pattern detected: {url}")
            return PageType.ARTICLE
    
    # 1. 提取所有链接
    link_pattern = r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
    links = re.findall(link_pattern, html, re.I | re.S)
    
    # 2. 计算页面文本总量（去除HTML标签）
    # 移除脚本和样式
    clean_html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.I | re.S)
    clean_html = re.sub(r'<style[^>]*>.*?</style>', '', clean_html, flags=re.I | re.S)
    # 提取纯文本
    text_content = re.sub(r'<[^>]+>', ' ', clean_html)
    text_content = ihtml.unescape(text_content)
    total_text_length = len(text_content.strip())
    
    # 3. 计算有效链接数量（排除导航、页脚等）
    content_links = []
    anchor_links = []  # 添加锚点链接列表
    for href, link_text in links:
        link_text_clean = re.sub(r'<[^>]+>', '', link_text).strip()
        # 识别锚点链接
        if href.startswith('#'):
            anchor_links.append((href, link_text_clean))
        # 过滤掉明显的导航链接（放宽条件）
        elif (len(link_text_clean) > 2 and  # 降低最小长度要求
            not any(nav_word in link_text_clean.lower() for nav_word in 
                   ['首页', '返回', '登录', '注册', 'home', 'back', 'login', 'register']) and
            not link_text_clean.lower() in ['更多', '更多>>']):  # 分别检查常见的短导航词
            content_links.append((href, link_text_clean))
    
    # 4. 计算链接密度
    link_density = len(content_links) / max(total_text_length, 1) * 1000  # 每1000字符的链接数
    
    # 5. 检测列表容器
    list_containers = [
        r'<ul[^>]*class=["\'][^"\']*list[^"\']*["\']',  # ul.list*
        r'<ol[^>]*class=["\'][^"\']*list[^"\']*["\']',  # ol.list*
        r'<div[^>]*class=["\'][^"\']*list[^"\']*["\']', # div.list*
        r'<div[^>]*class=["\'][^"\']*index[^"\']*["\']', # div.index*
        r'<div[^>]*class=["\'][^"\']*content-list[^"\']*["\']', # div.content-list*
        r'<div[^>]*id=["\'][^"\']*list[^"\']*["\']',    # div#list*
        r'<table[^>]*>.*?<tr[^>]*>.*?<td[^>]*>.*?</td>.*?<td[^>]*>.*?</td>.*?<td[^>]*>.*?</td>', # 三列表格
    ]
    
    list_container_count = 0
    for pattern in list_containers:
        if re.search(pattern, html, re.I):
            list_container_count += 1
    
    # 6. 检测重复链接模式（相似的链接文本长度和格式）
    if len(content_links) >= 5:
        link_lengths = [len(text) for _, text in content_links]
        avg_length = sum(link_lengths) / len(link_lengths)
        # 检查链接文本长度的一致性
        similar_length_links = sum(1 for length in link_lengths 
                                 if abs(length - avg_length) <= avg_length * 0.5)
        pattern_consistency = similar_length_links / len(content_links)
    else:
        pattern_consistency = 0
    
    # 6.5. 锚点链接比例判定（解决章节导航误判问题）
    all_links = links
    if len(all_links) > 0:
        anchor_ratio = len(anchor_links) / len(all_links)
        
        # 如果锚点链接占比超过30%，或者锚点链接数量>=10，很可能是文章页面的章节导航
        if anchor_ratio > 0.3 or len(anchor_links) >= 10:
            return PageType.ARTICLE
        
        # 如果有较多锚点链接（如章节导航），降低列表页判定权重
        if len(anchor_links) >= 5:
            # 减少有效链接计数，避免误判
            content_links = content_links[:max(len(content_links)//2, 1)]
    
    # 7. 决策逻辑
    # 强列表信号：
    # - 高链接密度 (>1.5个链接/1000字符)
    # - 存在列表容器
    # - 链接模式一致性高 (>50%)
    # - 链接数量多 (>=5个)
    
    is_list_page = (
        (link_density > 1.5 and len(content_links) >= 5) or  # 降低密度要求
        (list_container_count >= 2) or  # 多个列表容器
        (len(content_links) >= 8 and pattern_consistency > 0.5) or  # 降低一致性要求
        (link_density > 1.0 and list_container_count >= 1 and len(content_links) >= 5) or  # 降低综合判断阈值
        (list_container_count >= 1 and len(content_links) >= 10)  # 如果有列表容器且链接多，直接判定为列表
    )
    
    # 调试信息（可选）
    print(f"[DEBUG] Links - Total: {len(all_links)}, Content: {len(content_links)}, Anchor: {len(anchor_links)}")
    print(f"Page type detection - Links: {len(content_links)}, "
                 f"Density: {link_density:.2f}, "
                 f"List containers: {list_container_count}, "
                 f"Pattern consistency: {pattern_consistency:.2f}, "
                 f"Result: {'LIST' if is_list_page else 'ARTICLE'}")
    
    return PageType.LIST_INDEX if is_list_page else PageType.ARTICLE


def format_list_page_markdown(page_title: str, list_items: List[ListItem], url: str) -> tuple[str, str, dict]:
    """
    将列表页面数据格式化为Markdown输出
    
    Args:
        page_title: 页面标题
        list_items: 列表项数据
        url: 原始URL
        
    Returns:
        tuple: (文件名用的日期, Markdown内容, 元数据)
    """
    # 生成文件名用的日期
    date_only = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # 构建Markdown内容
    lines = [
        f"# {page_title}",
        "",
        f"**页面类型**: 列表索引",
        f"**链接数量**: {len(list_items)}个",
        f"**来源**: [{url}]({url})",
        f"**抓取时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 内容列表",
        ""
    ]
    
    # 添加每个列表项
    for item in list_items:
        lines.append(f"### {item.index}. {item.title}")
        lines.append(f"- **链接**: [{item.url}]({item.url})")
        
        if item.date:
            lines.append(f"- **日期**: {item.date}")
        
        if item.summary:
            lines.append(f"- **摘要**: {item.summary}")
        
        lines.append("")
    
    # 元数据
    metadata = {
        'title': page_title,
        'url': url,
        'type': 'list_index',
        'item_count': len(list_items),
        'extracted_at': datetime.datetime.now().isoformat(),
        'items': [
            {
                'title': item.title,
                'url': item.url,
                'date': item.date,
                'summary': item.summary
            }
            for item in list_items
        ]
    }
    
    return date_only, "\n".join(lines), metadata



def generic_to_markdown(html: str, url: str, filter_level: str = 'safe', is_crawling: bool = False, url_metadata: dict = None) -> tuple[str, str, dict]:
    """
    Generic parser - Routes to template-based implementation

    Phase 3.5: Routing layer for generic/fallback parsing
    Delegates to parsers_migrated for template-based parsing

    Args:
        html: HTML content of the page
        url: Source URL
        filter_level: Content filtering level
        is_crawling: Whether in crawling mode
        url_metadata: Optional URL tracking metadata from fetch (Task-003 Phase 1)

    Returns:
        tuple: (date_only, markdown_content, metadata)
    """
    logger.info("Phase 3.5: Routing Generic parser to template-based implementation")
    # Task-003 Phase 1: url_metadata accepted but not yet used (will be used in Phase 3)
    return generic_to_markdown_migrated(html, url, filter_level, is_crawling)
