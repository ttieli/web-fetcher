#!/usr/bin/env python3
"""
Unified web fetcher CLI (single file).
Supports WeChat (mp.weixin.qq.com), Xiaohongshu (xiaohongshu.com), and generic sites.

Features
- Static fetch with UA control; optional headless rendering (Playwright) for JS-heavy pages.
- Site-specific adapters for WeChat and Xiaohongshu; generic fallback.
- Clean Markdown output named as: YYYY-MM-DD - 标题.md
"""

__version__ = "1.0.0"
__author__ = "WebFetcher Team"

import argparse
import datetime
import html as ihtml
import json
import os
import re
import http.client as http_client
import urllib.parse
import urllib.request
import ssl
import subprocess
import sys
from typing import Optional, List, Dict, Set, Any
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
import logging
import time
import random
from collections import deque
# BeautifulSoup导入移至动态导入机制

def validate_and_encode_url(url: str) -> str:
    """
    Validate URL and ensure safe encoding for subprocess calls.
    
    Checks for potentially problematic characters and ensures proper URL encoding.
    
    Args:
        url: URL to validate and encode
        
    Returns:
        str: Safely encoded URL
        
    Raises:
        ValueError: If URL is invalid or contains unsafe patterns
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")
    
    url = url.strip()
    if not url:
        raise ValueError("URL cannot be empty after stripping whitespace")
    
    try:
        # Parse URL to validate structure
        parsed = urllib.parse.urlparse(url)
        
        # Basic validation
        if not parsed.scheme:
            raise ValueError(f"URL missing scheme: {url}")
        if not parsed.netloc:
            raise ValueError(f"URL missing network location: {url}")
        
        # Check for potentially problematic characters in shell context
        # Note: & is actually fine in subprocess.run with list arguments,
        # but we log it for debugging purposes
        shell_special_chars = ['`', '$', '\\', '"', "'"]
        for char in shell_special_chars:
            if char in url:
                logging.warning(f"URL contains shell special character '{char}': {url}")
                # Don't raise error, just warn - subprocess.run with list args handles this
        
        # Re-encode the URL to ensure proper formatting
        # This handles cases where URLs might have been partially decoded
        if parsed.query:
            # Re-encode query parameters to handle & properly
            query_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
            new_query = urllib.parse.urlencode(query_params)
            parsed = parsed._replace(query=new_query)
        
        encoded_url = urllib.parse.urlunparse(parsed)
        
        if encoded_url != url:
            logging.debug(f"URL re-encoded: {url} -> {encoded_url}")
        
        return encoded_url
        
    except Exception as e:
        raise ValueError(f"URL validation failed for '{url}': {e}")


def get_beautifulsoup_parser():
    """动态导入BeautifulSoup，如果不可用则返回None"""
    try:
        from bs4 import BeautifulSoup
        return BeautifulSoup
    except ImportError:
        return None

# HTML解析降级支持
from html.parser import HTMLParser

class FallbackHTMLParser(HTMLParser):
    """基础HTML解析器作为BeautifulSoup的降级方案"""
    
    def __init__(self):
        super().__init__()
        self.title = ""
        self.in_title = False
        self.content_parts = []
        self.current_text = ""
        self.in_script = False
        self.in_style = False
        self.meta_attrs = []
        
    def handle_starttag(self, tag, attrs):
        if tag == 'title':
            self.in_title = True
        elif tag in ['script', 'style']:
            if tag == 'script':
                self.in_script = True
            else:
                self.in_style = True
        elif tag == 'meta':
            attr_dict = dict(attrs)
            self.meta_attrs.append(attr_dict)
        elif tag in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'li']:
            if self.current_text.strip():
                self.content_parts.append(self.current_text.strip())
                self.current_text = ""
                
    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        elif tag in ['script', 'style']:
            if tag == 'script':
                self.in_script = False
            else:
                self.in_style = False
        elif tag in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'li']:
            if self.current_text.strip():
                self.content_parts.append(self.current_text.strip())
                self.current_text = ""
                
    def handle_data(self, data):
        if self.in_title:
            self.title += data.strip()
        elif not self.in_script and not self.in_style:
            self.current_text += data
            
    def get_parsed_content(self):
        if self.current_text.strip():
            self.content_parts.append(self.current_text.strip())
        return {
            'title': self.title or '未命名',
            'content_parts': self.content_parts,
            'meta_attrs': self.meta_attrs
        }

def extract_with_htmlparser(html_content: str, url: str) -> tuple[str, str, dict]:
    """使用Python内置HTMLParser进行基础解析"""
    parser = FallbackHTMLParser()
    try:
        parser.feed(html_content)
    except Exception as e:
        logging.warning(f"HTMLParser解析出错: {e}")
        return datetime.datetime.now().strftime('%Y-%m-%d'), f"# 解析失败\n\n无法解析页面内容: {str(e)}", {'page_type': 'parse_error'}
    
    parsed = parser.get_parsed_content()
    
    # 构建markdown内容
    content_parts = [f"# {parsed['title']}\n"]
    
    # 添加meta信息
    if parsed['meta_attrs']:
        content_parts.append("## 页面元数据\n")
        for meta in parsed['meta_attrs']:
            if meta.get('name'):
                content_parts.append(f"- {meta.get('name')}: {meta.get('content', '')}")
            elif meta.get('property'):
                content_parts.append(f"- {meta.get('property')}: {meta.get('content', '')}")
    
    # 添加主要内容
    if parsed['content_parts']:
        content_parts.append("\n## 页面内容\n")
        for part in parsed['content_parts']:
            if part.strip():
                content_parts.append(part.strip() + "\n")
    
    markdown_content = '\n'.join(content_parts)
    date_only = datetime.datetime.now().strftime('%Y-%m-%d')
    
    metadata = {
        'page_type': 'basic_html',
        'parser_used': 'HTMLParser',
        'content_sections': len(parsed['content_parts'])
    }
    
    return date_only, markdown_content, metadata

# Create an SSL context that doesn't verify certificates for legacy sites
ssl_context_unverified = ssl.create_default_context()
ssl_context_unverified.check_hostname = False
ssl_context_unverified.verify_mode = ssl.CERT_NONE

# Multi-page document support constants
MAX_PAGINATION_DEPTH = 5

# Site crawling configuration
MAX_CRAWL_DEPTH = 10  # Absolute maximum to prevent infinite recursion
MAX_CRAWL_PAGES = 1000  # Absolute maximum pages (increased for larger documentation sites)
DEFAULT_CRAWL_DELAY = 0.5  # Polite crawling delay

# Memory protection constants
MAX_PAGE_SIZE = 10 * 1024 * 1024  # 10MB limit for individual pages

# Smart URL filtering constants
BINARY_EXTENSIONS = {'.pdf', '.zip', '.tar', '.gz', '.rar', '.7z', '.exe', '.dmg', '.iso'}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico', '.bmp'}
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'}
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}
API_PATTERNS = {'/api/', '/rest/', '/graphql', '.json', '.xml', '.rss'}
BUILD_PATTERNS = {'/node_modules/', '/dist/', '/build/', '/.git/', '/target/',
                  '/_next/', '/_nuxt/', '/.next/', '/static/'}

# Retry configuration constants  
MAX_RETRIES = 3
BASE_DELAY = 1.0  # Base delay in seconds (1s, 2s, 4s progression)
MAX_JITTER = 0.1  # Add small random jitter to prevent thundering herd

# Define which exceptions and HTTP status codes are retryable
RETRYABLE_EXCEPTIONS = (
    urllib.error.URLError,           # DNS resolution, connection refused
    http_client.RemoteDisconnected,  # Server closed connection unexpectedly
    http_client.BadStatusLine,       # Malformed HTTP response
    ConnectionResetError,            # Connection reset by peer
    TimeoutError,                    # Socket timeout
    OSError,                        # OS-level network errors
)

RETRYABLE_HTTP_STATUS_CODES = {
    429,  # Too Many Requests (rate limiting)
    500,  # Internal Server Error
    502,  # Bad Gateway
    503,  # Service Unavailable
    504,  # Gateway Timeout
    520, 521, 522, 523, 524,  # CloudFlare errors
}


def setup_logging(verbose: bool = False):
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def sanitize_filename(name: str) -> str:
    invalid = set('/\\:*?"<>|\n\r\t')
    name = ''.join(ch if ch not in invalid else ' ' for ch in name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:160]


def normalize_media_url(u: str) -> str:
    if not u:
        return u
    u = u.strip()
    if u.startswith('//'):
        return 'https:' + u
    return u


def docusaurus_to_markdown(html: str, url: str) -> tuple[str, str, dict]:
    # Detect title: prefer H1 within doc markdown; fallback to og/title
    title = ''
    # H1 inside theme-doc-markdown
    m = re.search(r'<(?:article|div)[^>]+class=["\'][^"\']*theme-doc-markdown[^"\']*["\'][\s\S]*?<h1[^>]*>(.*?)</h1>', html, re.I)
    if m:
        title = ihtml.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip()
    if not title:
        title = extract_meta(html, 'og:title') or extract_meta(html, 'twitter:title')
    if not title:
        m2 = re.search(r'<title[^>]*>(.*?)</title>', html, re.I|re.S)
        if m2:
            title = ihtml.unescape(re.sub(r'<[^>]+>', '', m2.group(1))).strip()
    title = title or '未命名'

    # Choose a root container: element with class including theme-doc-markdown or markdown
    root_start = None
    for pat in (r'<(?:article|div)[^>]+class=["\'][^"\']*theme-doc-markdown[^"\']*["\']',
                r'<(?:article|div)[^>]+class=["\'][^"\']*\bmarkdown\b[^"\']*["\']'):
        ms = re.search(pat, html, re.I)
        if ms:
            root_start = ms.start()
            break
    # If not found, fallback to <main>
    if root_start is None:
        ms = re.search(r'<main[^>]*>', html, re.I)
        root_start = ms.start() if ms else 0
    html_tail = html[root_start:]

    base_url = url

    class DocParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.capture = False
            self.depth = 0
            self.parts: list[str] = []
            self.link_stack: list[Optional[str]] = []  # None means no bracket opened
            self.list_stack: list[tuple[bool,int]] = []  # (ordered, next_index)
            self.in_pre = False
            self.code_lang = ''
            self.blockquote_level = 0
            self.in_script = False
            self.images: list[str] = []

        def push_parbreak(self):
            if self.parts and not self.parts[-1].endswith('\n\n'):
                self.parts.append('\n\n')

        def handle_starttag(self, tag, attrs):
            a = dict(attrs)
            cls = a.get('class','') or ''
            if not self.capture and ('theme-doc-markdown' in cls or re.search(r'\bmarkdown\b', cls or '') or tag == 'main'):
                self.capture = True
                self.depth = 1
                return
            if self.capture:
                self.depth += 1
                if tag in ('p','div','section'): self.push_parbreak()
                elif tag == 'br': self.parts.append('\n')
                elif tag == 'h1': self.parts.append('\n\n# ')
                elif tag == 'h2': self.parts.append('\n\n## ')
                elif tag == 'h3': self.parts.append('\n\n### ')
                elif tag == 'h4': self.parts.append('\n\n#### ')
                elif tag == 'h5': self.parts.append('\n\n##### ')
                elif tag == 'h6': self.parts.append('\n\n###### ')
                elif tag == 'blockquote':
                    self.blockquote_level += 1
                    self.parts.append('\n\n' + '> ' * self.blockquote_level)
                elif tag == 'ul':
                    self.list_stack.append((False, 0))
                    self.parts.append('\n')
                elif tag == 'ol':
                    self.list_stack.append((True, 1))
                    self.parts.append('\n')
                elif tag == 'li':
                    indent = '  ' * max(0, len(self.list_stack)-1)
                    if self.list_stack and self.list_stack[-1][0]:
                        ordered, idx = self.list_stack[-1]
                        self.parts.append(f"\n{indent}{idx}. ")
                        self.list_stack[-1] = (ordered, idx+1)
                    else:
                        self.parts.append(f"\n{indent}- ")
                elif tag == 'pre':
                    self.in_pre = True
                    self.code_lang = ''
                    self.parts.append('\n\n```\n')
                elif tag == 'script':
                    self.in_script = True
                elif tag == 'code':
                    if self.in_pre:
                        # language from class like language-python
                        cls = a.get('class','') or ''
                        m = re.search(r'language-([\w+-]+)', cls)
                        if m:
                            # replace opening fence with language
                            if self.parts and self.parts[-1].endswith('```\n'):
                                self.parts[-1] = self.parts[-1][:-4] + m.group(1) + '\n'
                    else:
                        self.parts.append('`')
                elif tag == 'img':
                    src = a.get('src') or a.get('data-src')
                    if src:
                        src = resolve_url_with_context(base_url, src)
                        src = normalize_media_url(src)
                        self.images.append(src)
                        self.parts.append(f"\n\n![]({src})\n\n")
                elif tag == 'a':
                    href = a.get('href') or ''
                    if href and not href.startswith('#'):
                        href = href.strip().split()[0]
                        href = href.split(' target=')[0]
                        href = href.strip('"\'')
                        href = resolve_url_with_context(base_url, href)
                        href = normalize_media_url(href)
                        self.link_stack.append(href)
                        self.parts.append('[')
                    else:
                        self.link_stack.append(None)

        def handle_endtag(self, tag):
            if self.capture:
                if tag == 'a':
                    href = self.link_stack.pop() if self.link_stack else None
                    if href is not None:
                        self.parts.append(f"]({href})")
                elif tag == 'blockquote':
                    self.blockquote_level = max(0, self.blockquote_level-1)
                    self.parts.append('\n\n')
                elif tag == 'pre':
                    self.in_pre = False
                    self.parts.append('\n```\n\n')
                elif tag == 'script':
                    self.in_script = False
                elif tag == 'code':
                    if not self.in_pre:
                        self.parts.append('`')
                elif tag in ('ul','ol'):
                    if self.list_stack:
                        self.list_stack.pop()
                        self.parts.append('\n')
                self.depth -= 1
                if self.depth == 0:
                    self.capture = False

        def handle_data(self, data):
            if self.capture and not self.in_script:
                if self.in_pre:
                    self.parts.append(data)
                else:
                    t = data.replace('\r','')
                    if t.strip():
                        if t.strip() == '¶':
                            return
                        if self.blockquote_level:
                            # indent blockquote lines
                            pref = '> ' * self.blockquote_level
                            lines = [pref + ihtml.unescape(x) for x in t.splitlines() if x.strip()]
                            self.parts.append('\n'.join(lines))
                        else:
                            self.parts.append(ihtml.unescape(t))

    parser = DocParser()
    parser.feed(html_tail)
    body = ''.join(parser.parts)
    body = re.sub(r'\n{3,}', '\n\n', body).strip()
    date_only, date_time = parse_date_like(extract_meta(html, 'article:published_time') or extract_meta(html, 'og:updated_time'))
    desc = extract_meta(html, 'description')
    lines = [f"# {title}", f"- 标题: {title}", f"- 发布时间: {date_time}", f"- 来源: [{url}]({url})", f"- 抓取时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
    if body:
        lines += ["", body]
    else:
        lines += ["", '(未能提取正文)']
    
    metadata = {
        'description': desc,
        'images': parser.images,
        'publish_time': extract_meta(html, 'article:published_time') or extract_meta(html, 'og:updated_time')
    }
    return date_only, "\n\n".join(lines).strip() + "\n", metadata


def mkdocs_to_markdown(html: str, url: str) -> tuple[str, str, dict]:
    # Title from h1 within md-typeset, else <title>
    title = ''
    m = re.search(r'<article[^>]+class=["\'][^"\']*md-content__inner[^"\']*["\'][\s\S]*?<h1[^>]*>(.*?)</h1>', html, re.I)
    if m:
        title = ihtml.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip()
    if not title:
        m2 = re.search(r'<title[^>]*>(.*?)</title>', html, re.I|re.S)
        if m2:
            title = ihtml.unescape(re.sub(r'<[^>]+>', '', m2.group(1))).strip()
    title = title or '未命名'

    # Use the article md-typeset region as root
    ms = re.search(r'<article[^>]+class=["\'][^"\']*md-content__inner[^"\']*["\']', html, re.I)
    root_start = ms.start() if ms else 0
    html_tail = html[root_start:]

    base_url = url

    class MkParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.capture = False
            self.depth = 0
            self.parts: list[str] = []
            self.link_stack: list[Optional[str]] = []
            self.list_stack: list[tuple[bool,int]] = []
            self.in_pre = False
            self.blockquote_level = 0
            self.in_script = False
            self.images: list[str] = []

        def handle_starttag(self, tag, attrs):
            a = dict(attrs)
            cls = a.get('class','') or ''
            if not self.capture and ('md-content__inner' in cls or tag == 'article'):
                self.capture = True
                self.depth = 1
                return
            if self.capture:
                self.depth += 1
                if tag in ('p','div','section'): self.parts.append('\n\n')
                elif tag == 'br': self.parts.append('\n')
                elif tag == 'h1': self.parts.append('\n\n# ')
                elif tag == 'h2': self.parts.append('\n\n## ')
                elif tag == 'h3': self.parts.append('\n\n### ')
                elif tag == 'h4': self.parts.append('\n\n#### ')
                elif tag == 'h5': self.parts.append('\n\n##### ')
                elif tag == 'h6': self.parts.append('\n\n###### ')
                elif tag == 'blockquote':
                    self.blockquote_level += 1
                    self.parts.append('\n\n' + '> ' * self.blockquote_level)
                elif tag == 'ul':
                    self.list_stack.append((False, 0))
                    self.parts.append('\n')
                elif tag == 'ol':
                    self.list_stack.append((True, 1))
                    self.parts.append('\n')
                elif tag == 'li':
                    indent = '  ' * max(0, len(self.list_stack)-1)
                    if self.list_stack and self.list_stack[-1][0]:
                        ordered, idx = self.list_stack[-1]
                        self.parts.append(f"\n{indent}{idx}. ")
                        self.list_stack[-1] = (ordered, idx+1)
                    else:
                        self.parts.append(f"\n{indent}- ")
                elif tag == 'pre':
                    self.in_pre = True
                    self.parts.append('\n\n```\n')
                elif tag == 'script':
                    self.in_script = True
                elif tag == 'code':
                    if not self.in_pre:
                        self.parts.append('`')
                elif tag == 'img':
                    src = a.get('src') or a.get('data-src')
                    if src:
                        src = resolve_url_with_context(base_url, src)
                        src = normalize_media_url(src)
                        self.images.append(src)
                        self.parts.append(f"\n\n![]({src})\n\n")
                elif tag == 'a':
                    href = a.get('href') or ''
                    if href and not href.startswith('#'):
                        href = href.strip().split()[0]
                        href = href.split(' target=')[0]
                        href = href.strip('"\'')
                        href = resolve_url_with_context(base_url, href)
                        href = normalize_media_url(href)
                        self.link_stack.append(href)
                        self.parts.append('[')
                    else:
                        self.link_stack.append(None)

        def handle_endtag(self, tag):
            if self.capture:
                if tag == 'a':
                    href = self.link_stack.pop() if self.link_stack else None
                    if href is not None:
                        self.parts.append(f"]({href})")
                elif tag == 'blockquote':
                    self.blockquote_level = max(0, self.blockquote_level-1)
                    self.parts.append('\n\n')
                elif tag == 'pre':
                    self.in_pre = False
                    self.parts.append('\n```\n\n')
                elif tag == 'script':
                    self.in_script = False
                elif tag == 'code':
                    if not self.in_pre:
                        self.parts.append('`')
                elif tag in ('ul','ol'):
                    if self.list_stack:
                        self.list_stack.pop()
                        self.parts.append('\n')
                self.depth -= 1
                if self.depth == 0:
                    self.capture = False

        def handle_data(self, data):
            if self.capture and not self.in_script:
                if self.in_pre:
                    self.parts.append(data)
                else:
                    t = data.replace('\r','')
                    if t.strip():
                        if t.strip() == '¶':
                            return
                        self.parts.append(ihtml.unescape(t))

    parser = MkParser()
    parser.feed(html_tail)
    body = ''.join(parser.parts)
    body = re.sub(r'\n{3,}', '\n\n', body).strip()
    date_only, date_time = parse_date_like(extract_meta(html, 'article:published_time') or extract_meta(html, 'og:updated_time'))
    desc = extract_meta(html, 'description')
    lines = [f"# {title}", f"- 标题: {title}", f"- 发布时间: {date_time}", f"- 来源: [{url}]({url})", f"- 抓取时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
    lines += ["", body or '(未能提取正文)']
    
    metadata = {
        'description': desc,
        'images': parser.images,
        'publish_time': extract_meta(html, 'article:published_time') or extract_meta(html, 'og:updated_time')
    }
    return date_only, "\n\n".join(lines).strip() + "\n", metadata


def should_retry_exception(exc: Exception) -> bool:
    """Determine if an exception warrants a retry attempt."""
    if isinstance(exc, urllib.error.HTTPError):
        return exc.status in RETRYABLE_HTTP_STATUS_CODES
    return isinstance(exc, RETRYABLE_EXCEPTIONS)

def calculate_backoff_delay(attempt: int, base_delay: float = BASE_DELAY) -> float:
    """Calculate exponential backoff delay with jitter."""
    delay = base_delay * (2 ** attempt)  # 1s, 2s, 4s
    jitter = random.uniform(0, MAX_JITTER)
    return delay + jitter

def fetch_html_with_retry(url: str, ua: Optional[str] = None, timeout: int = 30) -> str:
    """
    Fetch HTML with exponential backoff retry logic.
    
    Retries network/temporary errors up to MAX_RETRIES times with exponential backoff.
    Immediately fails on client errors (4xx) and non-retryable server errors.
    """
    last_exception = None
    
    for attempt in range(MAX_RETRIES + 1):  # 0, 1, 2, 3 (4 total attempts)
        try:
            if attempt > 0:
                delay = calculate_backoff_delay(attempt - 1)
                logging.info(f"Retry attempt {attempt}/{MAX_RETRIES} for {url} after {delay:.1f}s delay")
                time.sleep(delay)
            
            # Call the original fetch_html function
            return fetch_html_original(url, ua, timeout)
            
        except Exception as e:
            last_exception = e
            
            # Log the error with context
            if attempt == 0:
                logging.warning(f"Initial fetch failed for {url}: {type(e).__name__}: {e}")
            else:
                logging.warning(f"Retry {attempt}/{MAX_RETRIES} failed for {url}: {type(e).__name__}: {e}")
            
            # Check if we should retry this exception
            if not should_retry_exception(e):
                # Special handling for HTTP 307 redirect loops
                if isinstance(e, urllib.error.HTTPError) and e.status == 307:
                    logging.error(f"HTTP 307 redirect loop detected for {url}. "
                                 f"This may indicate a redirect loop. "
                                 f"Try using a specific page URL instead of the root domain.")
                else:
                    logging.info(f"Non-retryable error for {url}, failing immediately: {type(e).__name__}")
                raise e
            
            # If this was the last attempt, don't sleep
            if attempt == MAX_RETRIES:
                break
    
    # All retry attempts exhausted
    logging.error(f"All {MAX_RETRIES + 1} attempts failed for {url}, giving up")
    raise last_exception

def fetch_html_with_curl(url: str, ua: Optional[str] = None, timeout: int = 30) -> str:
    """Fallback to curl for sites with SSL issues"""
    ua = ua or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36"
    
    try:
        # Validate and encode URL for safe subprocess execution
        validated_url = validate_and_encode_url(url)
        
        cmd = [
            'curl', '-k', '-s', '-L',  # -k ignores SSL, -s silent, -L follow redirects
            '--max-time', str(timeout),
            '-H', f'User-Agent: {ua}',
            '-H', 'Accept-Language: zh-CN,zh;q=0.9',
            '--compressed',  # Accept compressed responses
            validated_url
        ]
        
        logging.debug(f"Executing curl command for URL: {validated_url}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+5)
        
        if result.returncode == 0:
            return result.stdout
        else:
            # Log curl error details for debugging
            logging.error(f"curl failed for {validated_url}: return code {result.returncode}, stderr: {result.stderr}")
            raise Exception(f"curl failed with code {result.returncode}: {result.stderr}")
            
    except ValueError as e:
        # URL validation error
        logging.error(f"URL validation failed for curl: {e}")
        raise Exception(f"Invalid URL for curl: {e}")
    except subprocess.TimeoutExpired:
        logging.error(f"curl timeout for {url}")
        raise Exception(f"curl timeout for {url}")
    except Exception as e:
        logging.error(f"Failed to fetch with curl from {url}: {e}")
        raise

def fetch_html_original(url: str, ua: Optional[str] = None, timeout: int = 30) -> str:
    ua = ua or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36"
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Language": "zh-CN,zh;q=0.9"})
    try:
        # Use unverified SSL context for sites with legacy SSL configurations
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_context_unverified) as r:
            try:
                data = r.read(MAX_PAGE_SIZE)  # Limit read size
                # Check if there's more data and truncate if needed
                remaining = r.read(1)
                if remaining:
                    logging.warning(f"Page truncated at {MAX_PAGE_SIZE} bytes: {url}")
            except http_client.IncompleteRead as e:
                logging.warning(f"Incomplete read, using partial data: {len(e.partial or b'')} bytes")
                data = (e.partial or b"")
        return data.decode("utf-8", errors="ignore")
    except Exception as e:
        # If SSL error, try curl as fallback
        if "SSL" in str(e) or "CERTIFICATE" in str(e).upper():
            logging.info(f"SSL error detected, falling back to curl for {url}")
            return fetch_html_with_curl(url, ua, timeout)
        logging.error(f"Failed to fetch HTML from {url}: {e}")
        raise

# Replace the public interface to use the retry wrapper
fetch_html = fetch_html_with_retry


def resolve_final_url(url: str, ua: Optional[str] = None, timeout: int = 10, max_redirects: int = 5) -> tuple[str, bool]:
    """
    Resolves URL redirects to get the final destination URL using HEAD requests.
    
    Args:
        url: Original URL to resolve
        ua: User agent string (optional)
        timeout: Request timeout in seconds
        max_redirects: Maximum number of redirects to follow
        
    Returns:
        tuple[str, bool]: (final_url, was_redirected)
    """
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")
    
    ua = ua or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36"
    current_url = url.strip()
    redirect_count = 0
    was_redirected = False
    
    try:
        while redirect_count < max_redirects:
            logging.debug(f"Checking redirect for: {current_url}")
            
            # Create HEAD request to check for redirects
            req = urllib.request.Request(current_url, headers={
                "User-Agent": ua,
                "Accept-Language": "zh-CN,zh;q=0.9"
            })
            req.get_method = lambda: 'HEAD'
            
            try:
                with urllib.request.urlopen(req, timeout=timeout, context=ssl_context_unverified) as response:
                    # If we get here without exception, no redirect occurred
                    final_url = response.geturl()
                    if final_url != current_url:
                        was_redirected = True
                        logging.info(f"URL resolved via response: {url} -> {final_url}")
                    return final_url, was_redirected
                    
            except urllib.error.HTTPError as e:
                # Check if it's a redirect status code
                if e.code in (301, 302, 303, 307, 308):
                    location = e.headers.get('Location')
                    if not location:
                        # No location header, return current URL
                        return current_url, was_redirected
                    
                    # Handle relative URLs
                    if location.startswith('/'):
                        parsed = urllib.parse.urlparse(current_url)
                        location = f"{parsed.scheme}://{parsed.netloc}{location}"
                    elif not location.startswith(('http://', 'https://')):
                        # Relative URL, resolve against current URL
                        location = urllib.parse.urljoin(current_url, location)
                    
                    logging.debug(f"Redirect {e.code}: {current_url} -> {location}")
                    current_url = location
                    redirect_count += 1
                    was_redirected = True
                    continue
                else:
                    # Non-redirect HTTP error, return current URL
                    logging.warning(f"HTTP error {e.code} for {current_url}")
                    return current_url, was_redirected
                    
            except Exception as e:
                logging.warning(f"Error resolving redirects for {current_url}: {e}")
                return current_url, was_redirected
        
        # Max redirects exceeded
        logging.warning(f"Max redirects ({max_redirects}) exceeded for {url}")
        return current_url, was_redirected
        
    except Exception as e:
        logging.error(f"Failed to resolve URL {url}: {e}")
        return url, False


def resolve_final_url_with_fallback(url: str, ua: Optional[str] = None, timeout: int = 10, max_redirects: int = 5) -> tuple[str, bool]:
    """
    Enhanced redirect resolver with fallback strategies for problematic redirect services.
    
    Some redirect services (like xhslink.com) return 404 on HEAD requests but work with GET.
    This function implements a fallback strategy for such services.
    
    Args:
        url: Original URL to resolve
        ua: User agent string (optional)
        timeout: Request timeout in seconds
        max_redirects: Maximum number of redirects to follow
        
    Returns:
        tuple[str, bool]: (final_url, was_redirected)
    """
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")
    
    ua = ua or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36"
    current_url = url.strip()
    redirect_count = 0
    was_redirected = False
    
    # Check if this is a known problematic redirect service
    parsed_original = urllib.parse.urlparse(current_url)
    is_known_redirect_service = parsed_original.hostname and 'xhslink.com' in parsed_original.hostname
    
    # For known problematic services, try GET-based resolution immediately
    if is_known_redirect_service:
        logging.debug(f"Using GET-based redirect resolution for known service: {parsed_original.hostname}")
        return resolve_redirects_with_get(current_url, ua, timeout, max_redirects)
    
    # First attempt: Use the standard HEAD-based resolution
    try:
        final_url, was_redirected = resolve_final_url(current_url, ua, timeout, max_redirects)
        return final_url, was_redirected
    except Exception as e:
        logging.debug(f"Standard redirect resolution failed for {current_url}: {e}")
        
        # Check if this might be a redirect service that blocks HEAD requests
        if "404" in str(e) or "HTTP Error 404" in str(e):
            parsed = urllib.parse.urlparse(current_url)
            hostname = parsed.hostname or ""
            
            # Heuristic: domains that might be redirect services
            redirect_indicators = ['link', 'short', 'redirect', 'go', 'r', 'l']
            might_be_redirect_service = any(indicator in hostname.lower() for indicator in redirect_indicators)
            
            if might_be_redirect_service:
                logging.info(f"404 response detected on potential redirect service {hostname}, attempting GET fallback")
                try:
                    return resolve_redirects_with_get(current_url, ua, timeout, max_redirects)
                except Exception as fallback_error:
                    logging.warning(f"GET fallback also failed for {current_url}: {fallback_error}")
                    return current_url, False
        
        # For other errors, return original URL
        logging.warning(f"Redirect resolution failed for {current_url}: {e}")
        return current_url, False


def resolve_redirects_with_get(url: str, ua: str, timeout: int, max_redirects: int) -> tuple[str, bool]:
    """
    Resolve redirects using GET requests instead of HEAD.
    
    This is a fallback for services that return 404 on HEAD but work with GET.
    
    Args:
        url: URL to resolve
        ua: User agent string
        timeout: Request timeout
        max_redirects: Maximum redirects to follow
        
    Returns:
        tuple[str, bool]: (final_url, was_redirected)
    """
    current_url = url
    redirect_count = 0
    was_redirected = False
    
    while redirect_count < max_redirects:
        logging.debug(f"GET-based redirect check for: {current_url}")
        
        try:
            req = urllib.request.Request(current_url, headers={
                "User-Agent": ua,
                "Accept-Language": "zh-CN,zh;q=0.9"
            })
            
            with urllib.request.urlopen(req, timeout=timeout, context=ssl_context_unverified) as response:
                final_url = response.geturl()
                if final_url != current_url:
                    was_redirected = True
                    logging.info(f"GET-based redirect resolved: {url} -> {final_url}")
                return final_url, was_redirected
                
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308):
                location = e.headers.get('Location')
                if not location:
                    return current_url, was_redirected
                
                # Handle relative URLs
                if location.startswith('/'):
                    parsed = urllib.parse.urlparse(current_url)
                    location = f"{parsed.scheme}://{parsed.netloc}{location}"
                elif not location.startswith(('http://', 'https://')):
                    location = urllib.parse.urljoin(current_url, location)
                
                logging.debug(f"GET-based redirect {e.code}: {current_url} -> {location}")
                current_url = location
                redirect_count += 1
                was_redirected = True
                continue
            else:
                # Non-redirect HTTP error
                logging.warning(f"GET-based resolution HTTP error {e.code} for {current_url}")
                return current_url, was_redirected
                
        except Exception as e:
            logging.warning(f"GET-based resolution error for {current_url}: {e}")
            return current_url, was_redirected
    
    # Max redirects exceeded
    logging.warning(f"Max redirects ({max_redirects}) exceeded in GET-based resolution for {url}")
    return current_url, was_redirected


def get_effective_host(url: str, ua: Optional[str] = None) -> str:
    """
    Gets the effective hostname after resolving redirects.
    Implements caching for performance.
    
    Args:
        url: Original URL
        ua: User agent string (optional)
        
    Returns:
        str: Effective hostname for parser selection
    """
    try:
        final_url, was_redirected = resolve_final_url_with_fallback(url, ua=ua, timeout=10)
        if was_redirected:
            logging.info(f"Redirect resolved for parser selection: {url} -> {final_url}")
        return urllib.parse.urlparse(final_url).hostname or ''
    except Exception as e:
        logging.warning(f"Failed to resolve redirects for parser selection: {e}")
        # Fallback to original URL parsing
        return urllib.parse.urlparse(url).hostname or ''


def try_render(url: str, ua: Optional[str] = None, timeout_ms: int = 60000) -> Optional[str]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None
    html = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox','--disable-blink-features=AutomationControlled'])
            ctx = browser.new_context(user_agent=ua or 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148', locale='zh-CN', viewport={'width':390,'height':844}, device_scale_factor=3)
            page = ctx.new_page()
            page.set_extra_http_headers({'Accept-Language':'zh-CN,zh;q=0.9'})
            # Relaxed waiting strategy to avoid networkidle stalls
            page.goto(url, wait_until='domcontentloaded', timeout=timeout_ms)
            page.wait_for_load_state('load', timeout=timeout_ms)
            page.wait_for_timeout(800)
            try:
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(600)
            except Exception:
                pass
            html = page.content()
            ctx.close(); browser.close()
    except Exception:
        html = None
    return html


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


def ensure_unique_path(outdir: Path, base: str) -> Path:
    p = outdir / f"{base}.md"
    if not p.exists():
        return p
    n = 2
    while True:
        cand = outdir / f"{base} ({n}).md"
        if not cand.exists():
            return cand
        n += 1


def wechat_to_markdown(html: str, url: str) -> tuple[str, str, dict]:
    title = extract_meta(html, 'og:title')
    if not title:
        m = re.search(r'<h1[^>]*class=["\'][^"\']*rich_media_title[^"\']*["\'][^>]*>(.*?)</h1>', html, re.I|re.S)
        if m:
            t = re.sub(r'<[^>]+>', '', m.group(1))
            title = ihtml.unescape(t).strip()
    if not title:
        title = '未命名'

    author = extract_meta(html, 'og:article:author')
    if not author:
        m = re.search(r'<span[^>]*class=["\'][^"\']*rich_media_meta\s+rich_media_meta_text[^"\']*["\'][^>]*>(.*?)</span>', html, re.I|re.S)
        if m:
            author = ihtml.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip()

    pub = ''
    for pat in [r'id=["\']publish_time["\'][^>]*>([^<]+)<', r'property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)["\']']:
        m = re.search(pat, html, re.I)
        if m:
            pub = ihtml.unescape(m.group(1).strip())
            break
    date_only, date_time = parse_date_like(pub)

    class WxParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.capture = False
            self.depth = 0
            self.parts: list[str] = []
            self.link = None
            self.images: list[str] = []
            self.in_script = False
            self.in_style = False
        def handle_starttag(self, tag, attrs):
            a = dict(attrs)
            if not self.capture and a.get('id') == 'js_content':
                self.capture = True
                self.depth = 1
                return
            if self.capture:
                self.depth += 1
                if tag in ('p','div','section'): self.parts.append('\n\n')
                elif tag in ('br','hr'): self.parts.append('\n')
                elif tag == 'li': self.parts.append('\n- ')
                elif tag == 'h1': self.parts.append('\n\n# ')
                elif tag == 'h2': self.parts.append('\n\n## ')
                elif tag == 'h3': self.parts.append('\n\n### ')
                elif tag == 'img':
                    src = a.get('data-src') or a.get('src')
                    if src:
                        src = normalize_media_url(src)
                        self.images.append(src)
                        self.parts.append(f"\n\n![]({src})\n\n")
                elif tag == 'script':
                    self.in_script = True
                elif tag == 'style':
                    self.in_style = True
                elif tag == 'a':
                    self.link = a.get('href')
        def handle_endtag(self, tag):
            if self.capture:
                if tag == 'a' and self.link:
                    self.parts.append(f" ({self.link})")
                    self.link = None
                elif tag == 'script':
                    self.in_script = False
                elif tag == 'style':
                    self.in_style = False
                self.depth -= 1
                if self.depth == 0:
                    self.capture = False
        def handle_data(self, data):
            if self.capture and not self.in_script and not self.in_style:
                t = data.strip('\n')
                if t.strip(): self.parts.append(ihtml.unescape(t))

    p = WxParser()
    p.feed(html)
    body = ''.join(p.parts)
    body = re.sub(r'\n{3,}', '\n\n', body).strip() or '(未能提取正文)'

    lines = [f"# {title}"]
    meta = [f"- 标题: {title}"]
    if author: meta.append(f"- 作者: {author}")
    meta += [f"- 发布时间: {date_time}", f"- 来源: [{url}]({url})", f"- 抓取时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
    lines += meta + ["", body]
    
    metadata = {
        'author': author,
        'images': p.images,
        'publish_time': pub
    }
    return date_only, "\n\n".join(lines).strip() + "\n", metadata


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

class XHSImageExtractor:
    """
    Enhanced XiaoHongShu image extraction engine.
    
    Replaces the simple regex-based approach in the current xhs_to_markdown()
    function with comprehensive JSON/JavaScript data mining and lazy loading detection.
    """
    
    def __init__(self, html: str, url: str = "", debug: bool = False):
        """Initialize extractor with HTML content and optional source URL."""
        self.html = html
        self.url = url
        self.images: List[XHSImageData] = []
        self.seen_urls: Set[str] = set()
        self.debug = debug
    
    def extract_all(self) -> List[str]:
        """
        Main extraction orchestrator - executes all extraction strategies.
        
        Returns:
            List[str]: Ordered list of unique, validated image URLs
        """
        extraction_strategies = [
            self._extract_from_initial_state,
            self._extract_from_api_responses,
            self._extract_from_lazy_loading,
            self._extract_from_html_attributes,
            self._extract_from_json_ld
        ]
        
        for strategy in extraction_strategies:
            try:
                strategy()
            except Exception as e:
                # Strategy failed, continue to next
                continue
        
        return self._dedupe_and_order()
    
    def _extract_from_initial_state(self) -> None:
        """Extract images from window.__INITIAL_STATE__ and similar XHS globals."""
        state_patterns = [
            r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
            r'window\.initialState\s*=\s*({.+?});',  
            r'__NUXT__\s*=\s*({.+?});',
            r'window\.__store\s*=\s*({.+?});'
        ]
        
        for pattern in state_patterns:
            matches = re.finditer(pattern, self.html, re.DOTALL)
            for match in matches:
                try:
                    state_json = match.group(1)
                    # Clean up common JavaScript to JSON issues
                    state_json = self._clean_javascript_json(state_json)
                    data = json.loads(state_json)
                    self._parse_state_object(data, source="initial_state")
                except json.JSONDecodeError as e:
                    continue
                except Exception as e:
                    continue
    
    def _parse_state_object(self, data: Any, source: str = "state", path: str = "") -> None:
        """Recursively parse XHS state objects to find image data structures."""
        if isinstance(data, dict):
            # Check for XHS-specific image structures
            if 'imageList' in data:
                self._process_image_list(data['imageList'], source=f"{source}.imageList")
            
            if 'pics' in data:
                self._process_pics_array(data['pics'], source=f"{source}.pics")
            
            if 'noteDetailMap' in data:
                # XHS note detail structure
                note_map = data['noteDetailMap']
                for note_id, note_data in note_map.items():
                    if isinstance(note_data, dict):
                        self._parse_state_object(note_data, source=f"{source}.noteDetailMap.{note_id}")
            
            # Recursively search other dict keys
            for key, value in data.items():
                if key in ['imageList', 'pics', 'noteDetailMap']:
                    continue  # Already processed
                self._parse_state_object(value, source, f"{path}.{key}")
        
        elif isinstance(data, list):
            # Process array elements
            for i, item in enumerate(data):
                self._parse_state_object(item, source, f"{path}[{i}]")
    
    def _process_image_list(self, image_list: Any, source: str = "imageList") -> None:
        """Process XHS imageList array structure"""
        if not isinstance(image_list, list):
            return
        
        for i, img_data in enumerate(image_list):
            if isinstance(img_data, dict):
                url = img_data.get('url') or img_data.get('pic')
                pic_id = img_data.get('picId') or img_data.get('id')
                
                if url and self._is_valid_xhs_image_url(url):
                    self._add_image(XHSImageData(
                        url=url,
                        pic_id=pic_id,
                        width=img_data.get('width'),
                        height=img_data.get('height'),
                        is_cover=(i == 0),  # First image often cover
                        source=source
                    ))
            elif isinstance(img_data, str):
                # Sometimes imageList contains direct URL strings
                if self._is_valid_xhs_image_url(img_data):
                    self._add_image(XHSImageData(
                        url=img_data,
                        is_cover=(i == 0),
                        source=source
                    ))
    
    def _process_pics_array(self, pics: Any, source: str = "pics") -> None:
        """Process XHS pics array structure"""
        if not isinstance(pics, list):
            return
        
        for pic_data in pics:
            if isinstance(pic_data, dict):
                # Multiple URL formats in XHS pics structure
                url_candidates = [
                    pic_data.get('url'),
                    pic_data.get('original'),
                    pic_data.get('large'),
                    pic_data.get('medium'),
                    pic_data.get('small')
                ]
                
                for url in url_candidates:
                    if url and self._is_valid_xhs_image_url(url):
                        self._add_image(XHSImageData(
                            url=url,
                            pic_id=pic_data.get('picId'),
                            width=pic_data.get('width'),
                            height=pic_data.get('height'),
                            source=source
                        ))
                        break  # Use first valid URL found
    
    def _extract_from_api_responses(self) -> None:
        """Extract images from embedded API response data in script tags."""
        # Enhanced patterns for robust API response extraction
        # Use a custom balanced bracket/brace matching approach
        import re
        
        # Find all potential starting points for imageList or pics
        imageList_starts = list(re.finditer(r'"imageList"\s*:\s*\[', self.html))
        pics_starts = list(re.finditer(r'"pics"\s*:\s*\[', self.html))
        
        # Process each potential match
        all_starts = [(match.start(), match.end(), 'imageList') for match in imageList_starts]
        all_starts.extend([(match.start(), match.end(), 'pics') for match in pics_starts])
        
        for start_pos, end_pos, list_type in all_starts:
            try:
                # Extract balanced JSON array from this position
                json_array = self._extract_balanced_json_array(self.html, end_pos - 1)  # -1 to include the opening [
                if json_array and len(json_array) > 10:  # Minimum reasonable length
                    if self.debug:
                        print(f"DEBUG: Found balanced {list_type} array ({len(json_array)} chars): {json_array[:100]}...")
                        print(f"DEBUG: Last 50 chars of array: ...{json_array[-50:]}")
                    
                    # Clean and parse
                    cleaned_json = self._clean_unicode_escapes(json_array)
                    if self.debug:
                        print(f"DEBUG: Cleaned JSON ({len(cleaned_json)} chars): {cleaned_json[:200]}...")
                    
                    try:
                        data = {"imageList": json.loads(cleaned_json)} if list_type == 'imageList' else {"pics": json.loads(cleaned_json)}
                        self._extract_images_from_api_data(data, source="api_response")
                        if self.debug:
                            print(f"DEBUG: Successfully processed {list_type} data")
                        return  # Success, no need to try fallback patterns
                    except json.JSONDecodeError as e:
                        if self.debug:
                            print(f"DEBUG: Failed to parse {list_type} array: {e}")
                            print(f"DEBUG: Error position around: {cleaned_json[max(0, e.pos-20):e.pos+20]}")
                        continue
            except Exception as e:
                if self.debug:
                    print(f"DEBUG: Error extracting {list_type}: {e}")
                continue
        
        # Fallback to original regex patterns if balanced extraction fails
        api_patterns = [
            r'"note"\s*:\s*({[^{}]*"imageList"[^{}]*})',
            r'"data"\s*:\s*({[^{}]*"pics"[^{}]*})',
        ]
        
        for i, pattern in enumerate(api_patterns):
            if self.debug:
                print(f"DEBUG: Trying API pattern {i+1}: {pattern[:50]}...")
            
            matches = re.finditer(pattern, self.html, re.DOTALL)
            for match in matches:
                try:
                    json_data = match.group(1)
                    if self.debug:
                        print(f"DEBUG: Found API match with pattern {i+1}: {json_data[:100]}...")
                    
                    # Handle Unicode escapes and clean JSON
                    cleaned_json = self._clean_unicode_escapes(json_data)
                    
                    # Try multiple parsing approaches
                    data = None
                    try:
                        data = json.loads(cleaned_json)
                    except json.JSONDecodeError as e:
                        if self.debug:
                            print(f"DEBUG: Standard JSON parsing failed: {e}")
                        # Try parsing as just the array if it looks like one
                        if cleaned_json.startswith('[') and cleaned_json.endswith(']'):
                            try:
                                # Wrap in object for consistent processing
                                data = {"imageList": json.loads(cleaned_json)}
                                if self.debug:
                                    print("DEBUG: Successfully parsed as array")
                            except json.JSONDecodeError:
                                continue
                    
                    if data:
                        # Enhanced extraction with new method
                        self._extract_images_from_api_data(data, source="api_response")
                        if self.debug:
                            print(f"DEBUG: Successfully processed data from pattern {i+1}")
                    
                except json.JSONDecodeError as e:
                    if self.debug:
                        print(f"DEBUG: JSON decode failed for pattern {i+1}: {e}")
                    continue
    
    def _extract_from_lazy_loading(self) -> None:
        """Extract images from lazy loading configurations."""
        lazy_patterns = [
            r'data-src=["\']([^"\']*(?:ci\.xiaohongshu|xhscdn|sns-img)[^"\']*)["\']',
            r'data-original=["\']([^"\']*(?:ci\.xiaohongshu|xhscdn|sns-img)[^"\']*)["\']',
            r'data-lazy-src=["\']([^"\']*(?:ci\.xiaohongshu|xhscdn|sns-img)[^"\']*)["\']',
            r'"lazyLoad"\s*:\s*true[^}]*"src"\s*:\s*"([^"]*(?:ci\.xiaohongshu|xhscdn|sns-img)[^"]*)"',
        ]
        
        for pattern in lazy_patterns:
            matches = re.finditer(pattern, self.html, re.IGNORECASE)
            for match in matches:
                url = match.group(1).strip()
                if self._is_valid_xhs_image_url(url):
                    self._add_image(XHSImageData(
                        url=url,
                        source="lazy_loading"
                    ))
    
    def _extract_from_html_attributes(self) -> None:
        """Enhanced HTML attribute scanning with XHS-specific patterns."""
        attribute_patterns = [
            r'src=["\']([^"\']*(?:ci\.xiaohongshu|xhscdn|sns-img)[^"\']*)["\']',
            r'srcset=["\']([^"\']*(?:ci\.xiaohongshu|xhscdn|sns-img)[^"\']*)["\']',
            r'background-image:\s*url\(["\']?([^"\']*(?:ci\.xiaohongshu|xhscdn|sns-img)[^"\']*)["\']?\)',
        ]
        
        for pattern in attribute_patterns:
            matches = re.finditer(pattern, self.html, re.IGNORECASE)
            for match in matches:
                url_data = match.group(1)
                
                # Handle srcset (contains multiple URLs)
                if 'srcset' in pattern:
                    urls = self._parse_srcset(url_data)
                    for url in urls:
                        if self._is_valid_xhs_image_url(url):
                            self._add_image(XHSImageData(
                                url=url,
                                source="html_srcset"
                            ))
                else:
                    if self._is_valid_xhs_image_url(url_data):
                        self._add_image(XHSImageData(
                            url=url_data,
                            source="html_attributes"
                        ))
    
    def _extract_from_json_ld(self) -> None:
        """Extract from JSON-LD structured data (existing implementation)."""
        json_ld_pattern = r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
        matches = re.finditer(json_ld_pattern, self.html, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            try:
                data = json.loads(match.group(1).strip())
                self._parse_json_ld_images(data)
            except json.JSONDecodeError:
                continue
    
    def _parse_json_ld_images(self, data: Any) -> None:
        """Parse JSON-LD data for image references"""
        if isinstance(data, dict):
            # Look for image properties
            for key in ['image', 'thumbnail', 'url']:
                if key in data:
                    img_data = data[key]
                    if isinstance(img_data, str) and self._is_valid_xhs_image_url(img_data):
                        self._add_image(XHSImageData(
                            url=img_data,
                            source="json_ld"
                        ))
                    elif isinstance(img_data, list):
                        for img_url in img_data:
                            if isinstance(img_url, str) and self._is_valid_xhs_image_url(img_url):
                                self._add_image(XHSImageData(
                                    url=img_url,
                                    source="json_ld"
                                ))
        elif isinstance(data, list):
            for item in data:
                self._parse_json_ld_images(item)
    
    def _is_valid_xhs_image_url(self, url: str) -> bool:
        """Enhanced validation for XiaoHongShu image URLs."""
        if not url or not isinstance(url, str):
            return False
        
        url_clean = url.strip().strip('"\'')
        
        # Domain validation (expanded from current implementation)
        valid_domains = [
            'ci.xiaohongshu.com',
            'sns-img',
            'xhscdn.com',
            'sns-webpic-qc.xhscdn.com',
            'picasso-static.xiaohongshu.com',
            'sns-avatar-qc.xhscdn.com',  # Profile images
        ]
        
        domain_ok = any(domain in url_clean for domain in valid_domains)
        if not domain_ok:
            return False
        
        # Exclude avatars and icons (from current implementation)
        exclusions = ['avatar', 'favicon', 'icon', 'logo']
        if any(exclusion in url_clean.lower() for exclusion in exclusions):
            return False
        
        # Image format validation (enhanced)
        format_indicators = [
            r'\.(?:jpg|jpeg|png|webp|gif)(?:\?|$)',
            r'imageMogr2',      # XHS image processing
            r'imageView2',      # XHS image processing  
            r'thumbnail',
            r'format=',
            r'/photos/',        # XHS photo URLs
        ]
        
        format_ok = any(
            re.search(indicator, url_clean, re.IGNORECASE) 
            for indicator in format_indicators
        )
        
        return format_ok
    
    def _add_image(self, image_data: XHSImageData) -> None:
        """Add image if not already seen"""
        if image_data.url not in self.seen_urls:
            self.seen_urls.add(image_data.url)
            self.images.append(image_data)
    
    def _dedupe_and_order(self) -> List[str]:
        """Deduplicate and order images for final output."""
        if not self.images:
            return []
        
        # Remove duplicates while preserving order
        seen = set()
        unique_images = []
        for img in self.images:
            if img.url not in seen:
                seen.add(img.url)
                unique_images.append(img)
        
        # Prioritize cover images first
        cover_images = [img for img in unique_images if img.is_cover]
        non_cover_images = [img for img in unique_images if not img.is_cover]
        
        # Enhanced priority with quality validation
        # Prioritize API response extraction for high-quality images
        source_priority = {
            "initial_state": 1,
            "api_response": 1,  # Elevated to highest priority  
            "lazy_loading": 3,
            "html_attributes": 4,
            "html_srcset": 4,
            "json_ld": 5,
            "unknown": 6
        }
        
        # Enhanced sorting with quality metrics
        def get_image_quality_score(img):
            url = img.url
            quality_score = 0
            
            # Higher resolution gets better score
            if 'w/1080' in url:
                quality_score += 100
            elif 'w/720' in url:
                quality_score += 50
            elif 'w/480' in url:
                quality_score += 25
            # XiaoHongShu specific patterns - 'dft' (default) is typically higher quality than 'prv' (preview)
            elif 'nd_dft' in url:
                quality_score += 80  # High quality default format
            elif 'nd_prv' in url:
                quality_score += 40  # Lower quality preview format
            
            # API response images get bonus points
            if img.source == "api_response":
                quality_score += 200
                
            return quality_score
        
        # Sort by source priority first, then by quality score
        non_cover_images.sort(key=lambda img: (
            source_priority.get(img.source.split('.')[0], 6),
            -get_image_quality_score(img),  # Negative for descending order
            img.source
        ))
        
        ordered_images = cover_images + non_cover_images
        
        # Quality validation and smart fallback
        final_urls = []
        api_response_count = 0
        high_quality_count = 0
        
        for img in ordered_images:
            url = img.url
            final_urls.append(url)
            
            if img.source == "api_response":
                api_response_count += 1
            # Count high-quality images (1080p or XHS high-quality patterns)
            if 'w/1080' in url or 'nd_dft' in url:
                high_quality_count += 1
        
        # Log extraction quality metrics
        if self.debug:
            print(f"DEBUG: Total images extracted: {len(final_urls)}")
            print(f"DEBUG: API response images: {api_response_count}")
            print(f"DEBUG: High quality (1080p) images: {high_quality_count}")
            if api_response_count > 0:
                print("DEBUG: API extraction successful - using high-quality source")
            else:
                print("DEBUG: Falling back to HTML extraction methods")
        
        return final_urls
    
    def _clean_javascript_json(self, js_string: str) -> str:
        """Clean JavaScript object syntax to valid JSON"""
        # Remove JavaScript comments
        js_string = re.sub(r'//.*?$', '', js_string, flags=re.MULTILINE)
        js_string = re.sub(r'/\*.*?\*/', '', js_string, flags=re.DOTALL)
        
        # Handle undefined values
        js_string = re.sub(r'\bundefined\b', 'null', js_string)
        
        # Handle trailing commas (basic cleanup)
        js_string = re.sub(r',(\s*[}\]])', r'\1', js_string)
        
        return js_string
    
    def _clean_unicode_escapes(self, json_str: str) -> str:
        """Clean Unicode escapes and prepare JSON for parsing."""
        if self.debug:
            print(f"DEBUG: Input JSON length: {len(json_str)}")
        
        # Only handle the most common Unicode escape that causes issues
        json_str = json_str.replace('\\u002F', '/')
        
        if self.debug:
            print(f"DEBUG: After Unicode cleaning length: {len(json_str)}")
        
        return json_str
    
    def _extract_balanced_json_array(self, html: str, start_pos: int) -> str:
        """Extract a balanced JSON array starting from a given position."""
        if start_pos >= len(html) or html[start_pos] != '[':
            return ""
        
        bracket_count = 0
        in_string = False
        escape_next = False
        i = start_pos
        
        while i < len(html):
            char = html[i]
            
            if escape_next:
                escape_next = False
            elif char == '\\':
                escape_next = True
            elif char == '"':
                in_string = not in_string
            elif not in_string:
                if char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        # Found the closing bracket for our array
                        return html[start_pos:i+1]
            
            i += 1
            
            # Safety check - if we've gone too far, return what we have
            if i - start_pos > 100000:  # 100KB limit
                break
        
        # If we reach here, we didn't find a proper closing bracket
        # Return what we have up to a reasonable limit
        max_length = min(50000, len(html) - start_pos)
        return html[start_pos:start_pos + max_length]
    
    def _parse_srcset(self, srcset: str) -> List[str]:
        """Parse srcset attribute to extract individual URLs"""
        urls = []
        parts = srcset.split(',')
        for part in parts:
            # Extract URL (first part before any space)
            url = part.strip().split(' ')[0]
            if url:
                urls.append(url)
        return urls
    
    def _extract_images_from_api_data(self, data: dict, source: str = "api_response") -> None:
        """Enhanced method to extract images from API response data."""
        if not isinstance(data, dict):
            return
        
        # Deep traverse the data structure
        images_found = self._deep_extract_images(data)
        
        if self.debug:
            print(f"DEBUG: Found {len(images_found)} image objects in API data")
        
        for img_data in images_found:
            # Try to get the highest quality image URL
            image_url = self._upgrade_image_quality(img_data)
            
            if self.debug:
                print(f"DEBUG: Processing image data: {str(img_data)[:200]}...")
                print(f"DEBUG: Upgraded image URL: {image_url}")
            
            if image_url and self._is_valid_image_url(image_url):
                if self.debug:
                    print(f"DEBUG: Extracted high-quality image: {image_url}")
                
                self.images.append(XHSImageData(
                    url=image_url,
                    source=source,
                    is_cover=img_data.get('is_cover', False)
                ))
            elif self.debug:
                print(f"DEBUG: Skipped invalid image URL: {image_url}")
    
    def _upgrade_image_quality(self, img_data: dict) -> str:
        """Upgrade image quality from 720px to 1080px resolution."""
        image_url = ""
        
        if self.debug:
            print(f"DEBUG: Looking for URLs in keys: {list(img_data.keys())}")
        
        # Priority order for image URLs (highest quality first) - updated for XiaoHongShu
        url_keys = ['urlDefault', 'url_default', 'urlPre', 'url_pre', 'url', 'live_photo_url', 'src']
        
        for key in url_keys:
            if key in img_data and img_data[key]:
                candidate_url = img_data[key]
                if isinstance(candidate_url, str) and candidate_url.strip():
                    if self.debug:
                        print(f"DEBUG: Found URL in {key}: {candidate_url}")
                    # Upgrade to highest resolution
                    if 'w/720' in candidate_url:
                        image_url = candidate_url.replace('w/720', 'w/1080')
                        if self.debug:
                            print(f"DEBUG: Upgraded resolution: {candidate_url} -> {image_url}")
                        break
                    elif 'w/1080' in candidate_url:
                        image_url = candidate_url
                        break
                    elif any(size in candidate_url for size in ['w/480', 'w/360']):
                        # Upgrade lower resolutions to 1080p
                        image_url = re.sub(r'w/\d+', 'w/1080', candidate_url)
                        if self.debug:
                            print(f"DEBUG: Upgraded low resolution: {candidate_url} -> {image_url}")
                        break
                    else:
                        # Use the URL as-is if no specific resolution pattern
                        image_url = candidate_url
                        if self.debug:
                            print(f"DEBUG: Using URL as-is: {candidate_url}")
                        break
        
        # Also check nested infoList for URLs
        if not image_url and 'infoList' in img_data and isinstance(img_data['infoList'], list):
            for info_item in img_data['infoList']:
                if isinstance(info_item, dict) and 'url' in info_item and info_item['url']:
                    candidate_url = info_item['url']
                    if isinstance(candidate_url, str) and candidate_url.strip():
                        if self.debug:
                            print(f"DEBUG: Found URL in infoList: {candidate_url}")
                        # Apply same upgrade logic
                        if 'w/720' in candidate_url:
                            image_url = candidate_url.replace('w/720', 'w/1080')
                        elif any(size in candidate_url for size in ['w/480', 'w/360']):
                            image_url = re.sub(r'w/\d+', 'w/1080', candidate_url)
                        else:
                            image_url = candidate_url
                        break
        
        if self.debug and not image_url:
            print(f"DEBUG: No valid URL found in image data")
        
        return image_url
    
    def _is_valid_image_url(self, url: str) -> bool:
        """Check if URL is a valid image URL."""
        if not url or not isinstance(url, str):
            return False
        
        # Basic URL validation
        if not (url.startswith('http://') or url.startswith('https://')):
            return False
        
        # Check for common image-related patterns in XiaoHongShu URLs
        if 'sns-webpic' in url or 'xhscdn' in url:
            return True
        
        # Check for image file extensions
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        return any(ext in url.lower() for ext in image_extensions)
    
    def _deep_extract_images(self, obj: any, path: str = "") -> List[dict]:
        """Recursively traverse JSON to find image data."""
        images = []
        
        if isinstance(obj, dict):
            # Check for image list patterns
            if 'imageList' in obj and isinstance(obj['imageList'], list):
                for img in obj['imageList']:
                    if isinstance(img, dict):
                        images.append(img)
            
            if 'pics' in obj and isinstance(obj['pics'], list):
                for img in obj['pics']:
                    if isinstance(img, dict):
                        images.append(img)
            
            # Check for individual image objects
            if 'url' in obj or 'url_default' in obj:
                # This looks like an image object
                images.append(obj)
            
            # Recursively search other keys
            for key, value in obj.items():
                if key not in ['imageList', 'pics'] and isinstance(value, (dict, list)):
                    images.extend(self._deep_extract_images(value, f"{path}.{key}" if path else key))
        
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                images.extend(self._deep_extract_images(item, f"{path}[{i}]" if path else f"[{i}]"))
        
        return images


def xhs_to_markdown(html: str, url: str) -> tuple[str, str, dict]:
    def clean_title(t: str) -> str:
        t = t.strip()
        t = re.sub(r"\s*-\s*小红书\s*$", "", t)
        return t
    # title
    title = clean_title(extract_meta(html, 'og:title') or extract_meta(html, 'twitter:title') or '')
    if not title:
        m = re.search(r'<title[^>]*>(.*?)</title>', html, re.I|re.S)
        if m:
            title = clean_title(ihtml.unescape(re.sub(r'<[^>]+>', '', m.group(1)))).strip()
    title = title or '未命名'
    # author/date from JSON-LD
    author = ''
    date_raw = ''
    for m in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I|re.S):
        txt = m.group(1).strip()
        try:
            obj = json.loads(txt)
        except Exception:
            continue
        def visit(o):
            nonlocal author, date_raw
            if not isinstance(o, dict):
                return
            if not author:
                a = o.get('author') or {}
                if isinstance(a, dict):
                    nm = (a.get('name') or '').strip()
                    if nm and nm.lower() != 'undefined':
                        author = nm
            if not date_raw:
                for k in ('datePublished','uploadDate'):
                    v = o.get(k)
                    if v and re.search(r"\d{6,}|20\d{2}", str(v)):
                        date_raw = str(v)
                        break
        if isinstance(obj, list):
            for it in obj: visit(it)
        elif isinstance(obj, dict):
            visit(obj)
            if isinstance(obj.get('@graph'), list):
                for it in obj['@graph']: visit(it)
    # fallback date scan
    if not date_raw:
        m = re.search(r'"(datePublished|uploadDate)"\s*:\s*"([^"]+)"', html)
        if m: date_raw = m.group(2)
    date_only, date_time = parse_date_like(date_raw)

    desc = extract_meta(html, 'description').replace('\t','\n\n').strip()
    cover = extract_meta(html, 'og:image')
    
    # ENHANCED IMAGE EXTRACTION - Using XHSImageExtractor for comprehensive extraction
    try:
        extractor = XHSImageExtractor(html, url, debug=False)
        imgs = extractor.extract_all()
        
        # Apply legacy validation for backward compatibility
        def _validate_image_url_legacy(url: str) -> bool:
            """Legacy validation function to maintain backward compatibility."""
            if not url:
                return False
            
            url_clean = url.strip().strip('"\'')
            
            # Current domain validation logic
            ok_domain = any(x in url_clean for x in (
                'ci.xiaohongshu.com',
                'sns-img',
                'xhscdn.com',
            ))
            if not ok_domain:
                return False
            
            if any(bad in url_clean for bad in ('avatar', 'favicon')):
                return False
            
            # Current format validation logic - enhanced for XiaoHongShu
            if not (re.search(r'\.(?:jpg|jpeg|png|webp|gif)(?:\?|$)', url_clean, re.I) or 
                    ('imageMogr2' in url_clean) or ('imageView2' in url_clean) or
                    ('nd_dft' in url_clean) or ('nd_prv' in url_clean)):  # XiaoHongShu patterns
                return False
            
            return True
        
        # Filter through legacy validation
        validated_imgs = []
        for img_url in imgs:
            if _validate_image_url_legacy(img_url):
                validated_imgs.append(img_url)
        
        imgs = validated_imgs
        
        # Ensure cover is handled properly
        if cover:
            if _validate_image_url_legacy(cover):
                if cover not in imgs:
                    imgs.insert(0, cover)
                elif imgs and imgs[0] != cover and cover in imgs:
                    imgs.remove(cover)
                    imgs.insert(0, cover)
        
        # Enhanced extraction completed
        
    except Exception as e:
        # Fall back to legacy extraction method
        
        # FALLBACK TO LEGACY EXTRACTION
        imgs: list[str] = []
        seen = set()
        def consider(u: str):
            if not u:
                return
            # strip quotes and spaces
            u2 = u.strip().strip('"\'')
            # heuristic filters for XHS media images (exclude avatars/icons)
            ok_domain = any(x in u2 for x in (
                'ci.xiaohongshu.com',
                'sns-img',
                'xhscdn.com',
            ))
            if not ok_domain:
                return
            if any(bad in u2 for bad in ('avatar','favicon')):
                return
            # must look like an image URL (extension or image processing params)
            if not (re.search(r'\.(?:jpg|jpeg|png|webp|gif)(?:\?|$)', u2, re.I) or ('imageMogr2' in u2) or ('imageView2' in u2)):
                return
            if u2 not in seen:
                seen.add(u2)
                imgs.append(u2)

        # 1) common attributes: src, data-src, srcset
        for m in re.finditer(r'(?:src|data-src)=["\']([^"\']+)["\']', html, re.I):
            consider(m.group(1))
        # srcset can contain multiple URLs
        for m in re.finditer(r'srcset=["\']([^"\']+)["\']', html, re.I):
            chunk = m.group(1)
            for part in chunk.split(','):
                consider(part.strip().split(' ')[0])
        # 2) generic URLs inside scripts/JSON
        for m in re.finditer(r'"(https?://[^"\s]+\.(?:jpg|jpeg|png|webp)(?:\?[^"\s]*)?)"', html, re.I):
            consider(m.group(1))
        # Ensure cover first
        if cover:
            consider(cover)
            # move cover to front if present later
            if imgs and imgs[0] != cover and cover in imgs:
                imgs.remove(cover)
                imgs.insert(0, cover)

    lines = [f"# {title}"]
    meta = [f"- 标题: {title}"]
    if author: meta.append(f"- 作者: {author}")
    meta += [f"- 发布时间: {date_time}", f"- 来源: {url}", f"- 抓取时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
    lines += meta
    if cover:
        lines += ["", f"![]({normalize_media_url(cover)})"]
    body = desc or '(未能从页面提取正文摘要)'
    lines += ["", body]
    if imgs:
        lines += ["", "## 图片", ""] + [f"![]({normalize_media_url(u)})" for u in imgs]
    
    metadata = {
        'author': author,
        'images': [normalize_media_url(u) for u in imgs],
        'cover': normalize_media_url(cover) if cover else '',
        'description': desc,
        'publish_time': date_raw
    }
    return date_only, "\n\n".join(lines).strip() + "\n", metadata

def dianping_to_markdown(html: str, url: str) -> tuple[str, str, dict]:
    def clean_title(t: str) -> str:
        t = t.strip()
        t = re.sub(r"\s*[-|]\s*大众点评\s*$", "", t)
        return t

    # Prefer page/og/twitter titles
    title = clean_title(extract_meta(html, 'og:title') or extract_meta(html, 'twitter:title') or '')
    if not title:
        m = re.search(r'<title[^>]*>(.*?)</title>', html, re.I | re.S)
        if m:
            title = clean_title(ihtml.unescape(re.sub(r'<[^>]+>', '', m.group(1)))).strip()
    title = title or '未命名'

    # Try to parse JSON-LD for LocalBusiness-like info
    biz = {}
    for m in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I | re.S):
        txt = m.group(1).strip()
        try:
            obj = json.loads(txt)
        except Exception:
            continue
        cand_list = obj if isinstance(obj, list) else [obj]
        for o in cand_list:
            if not isinstance(o, dict):
                continue
            tp = o.get('@type')
            # Accept LocalBusiness / Restaurant / FoodEstablishment etc.
            if (isinstance(tp, str) and re.search(r'LocalBusiness|Restaurant|FoodEstablishment', tp, re.I)) or (
                isinstance(tp, list) and any(re.search(r'LocalBusiness|Restaurant|FoodEstablishment', str(t), re.I) for t in tp)
            ):
                biz = o
                break
        if biz:
            break

    # Extract fields
    name = (biz.get('name') if isinstance(biz, dict) else '') or title
    telephone = biz.get('telephone') if isinstance(biz, dict) else ''
    price_range = biz.get('priceRange') if isinstance(biz, dict) else ''
    rating = ''
    review_count = ''
    if isinstance(biz, dict) and isinstance(biz.get('aggregateRating'), dict):
        rating = str(biz['aggregateRating'].get('ratingValue') or '')
        review_count = str(biz['aggregateRating'].get('reviewCount') or '')
    # Address may be string or structured
    address = ''
    if isinstance(biz, dict):
        addr = biz.get('address')
        if isinstance(addr, str):
            address = addr
        elif isinstance(addr, dict):
            parts = [addr.get('addressRegion'), addr.get('addressLocality'), addr.get('streetAddress')]
            address = ' '.join([p for p in parts if p])

    # Opening hours
    hours = ''
    if isinstance(biz, dict):
        oh = biz.get('openingHours')
        if isinstance(oh, list):
            hours = '; '.join([str(x) for x in oh if x])
        elif isinstance(oh, str):
            hours = oh
        elif isinstance(biz.get('openingHoursSpecification'), list):
            chunks = []
            for spec in biz['openingHoursSpecification']:
                if not isinstance(spec, dict):
                    continue
                day = spec.get('dayOfWeek')
                opens = spec.get('opens')
                closes = spec.get('closes')
                seg = ' '.join([str(day or '').strip(), f"{opens or ''}-{closes or ''}" ]).strip()
                if seg:
                    chunks.append(seg)
            hours = '; '.join(chunks)

    # Description
    desc = extract_meta(html, 'description').strip()

    # Publish time is not meaningful for shops; use now
    date_only, date_time = parse_date_like(None)

    # Images: collect likely shop images from HTML and script JSONs
    cover = extract_meta(html, 'og:image')
    imgs: list[str] = []
    seen = set()
    def consider(u: str):
        if not u:
            return
        u2 = u.strip().strip('"\'')
        ok_domain = any(x in u2 for x in (
            'dpfile.com',   # Dianping CDN
            'meituan.net',  # Meituan CDN variants p0/p1...
            'dianping.com', # fallback
        ))
        if not ok_domain:
            return
        if any(bad in u2 for bad in ('avatar', 'favicon', 'icon')):
            return
        if not re.search(r'\.(?:jpg|jpeg|png|webp|gif)(?:\?|$)', u2, re.I):
            return
        if u2 not in seen:
            seen.add(u2)
            imgs.append(u2)

    for m in re.finditer(r'(?:src|data-src)=["\']([^"\']+)["\']', html, re.I):
        consider(m.group(1))
    for m in re.finditer(r'srcset=["\']([^"\']+)["\']', html, re.I):
        chunk = m.group(1)
        for part in chunk.split(','):
            consider(part.strip().split(' ')[0])
    for m in re.finditer(r'"(https?://[^"\s]+\.(?:jpg|jpeg|png|webp|gif)(?:\?[^"\s]*)?)"', html, re.I):
        consider(m.group(1))
    if cover:
        consider(cover)
        if imgs and imgs[0] != cover and cover in imgs:
            imgs.remove(cover)
            imgs.insert(0, cover)

    # Compose markdown
    lines = [f"# {name}"]
    meta = [f"- 标题: {name}"]
    if rating:
        meta.append(f"- 评分: {rating}{(' / ' + review_count + '条') if review_count else ''}")
    if price_range:
        meta.append(f"- 人均/价位: {price_range}")
    if telephone:
        meta.append(f"- 电话: {telephone}")
    if address:
        meta.append(f"- 地址: {address}")
    if hours:
        meta.append(f"- 营业时间: {hours}")
    meta += [f"- 发布时间: {date_time}", f"- 来源: [{url}]({url})", f"- 抓取时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
    lines += meta
    if cover:
        lines += ["", f"![]({normalize_media_url(cover)})"]
    body = desc or '（暂无描述，已抓取基础信息）'
    lines += ["", body]
    if imgs:
        lines += ["", "## 图片", ""] + [f"![]({normalize_media_url(u)})" for u in imgs]
    
    metadata = {
        'rating': rating,
        'review_count': review_count,
        'price_range': price_range,
        'telephone': telephone,
        'address': address,
        'hours': hours,
        'images': [normalize_media_url(u) for u in imgs],
        'cover': normalize_media_url(cover) if cover else '',
        'description': desc
    }
    return date_only, "\n\n".join(lines).strip() + "\n", metadata


def ebchina_news_list_to_markdown(html: str, url: str) -> tuple[str, str, dict]:
    """Parse EB China news list page."""
    # Extract page title
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.I|re.S)
    title = ihtml.unescape(re.sub(r'<[^>]+>', '', title_match.group(1))).strip() if title_match else '新闻列表'
    
    # Extract news items
    news_items = []
    
    # Pattern to extract news items with title, summary, date, and link
    # More specific pattern to correctly capture the title attribute
    item_pattern = r'<p class="N_title"[^>]*><a href="([^"]+)"[^>]*\stitle="([^"]+)"[^>]*>.*?</a></p>.*?<p class="N_summary">(.*?)</p>.*?<p class="N_date">发布时间：([^<]+)</p>'
    
    items = re.findall(item_pattern, html, re.I|re.S)
    
    for link, item_title, summary, date in items:
        # Clean summary
        summary = re.sub(r'<[^>]+>', '', summary)
        summary = ihtml.unescape(summary).strip()
        
        # Clean title
        item_title = ihtml.unescape(item_title).strip()
        
        # Make full URL
        full_url = resolve_url_with_context(url, link)
        
        news_items.append({
            'title': item_title,
            'summary': summary,
            'date': date.strip(),
            'url': full_url
        })
    
    # Build markdown content
    lines = [f"# {title}", ""]
    lines.append(f"- 来源: [{url}]({url})")
    lines.append(f"- 抓取时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- 新闻数量: {len(news_items)} 条")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Add news items
    for item in news_items:
        lines.append(f"## [{item['title']}]({item['url']})")
        lines.append("")
        lines.append(f"**发布时间:** {item['date']}")
        lines.append("")
        lines.append(item['summary'])
        lines.append("")
        lines.append("---")
        lines.append("")
    
    metadata = {
        'news_count': len(news_items),
        'news_items': news_items,
        'page_type': 'news_list'
    }
    
    date_only = datetime.datetime.now().strftime('%Y-%m-%d')
    return date_only, "\n".join(lines).strip() + "\n", metadata


def raw_to_markdown(html: str, url: str) -> tuple[str, str, dict]:
    """
    Raw mode parser - 尽可能保留所有内容的解析器
    
    设计原则：
    1. 宁可冗余，不可遗漏
    2. 保持原始结构
    3. 最小化处理
    4. 明确标记不同类型的内容
    """
    
    # 智能解析：优先使用BeautifulSoup，降级到HTMLParser
    BeautifulSoup = get_beautifulsoup_parser()
    
    if BeautifulSoup:
        # 使用BeautifulSoup进行解析（更宽容的解析器）
        soup = BeautifulSoup(html, 'html.parser')
        parser_used = "BeautifulSoup"
    else:
        # 降级到HTMLParser方案
        logging.warning("BeautifulSoup不可用，使用HTMLParser降级解析。建议安装: pip install beautifulsoup4")
        return extract_with_htmlparser(html, url)
    
    # 1. 提取基本元数据
    title = soup.title.string if soup.title else '未命名'
    
    # 2. 移除不需要的元素（但保守处理）
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    
    # 3. 构建内容列表
    content_parts = []
    
    # 3.1 保留所有meta信息
    meta_section = ["## 页面元数据\n"]
    for meta in soup.find_all('meta'):
        if meta.get('name'):
            meta_section.append(f"- {meta.get('name')}: {meta.get('content', '')}")
        elif meta.get('property'):
            meta_section.append(f"- {meta.get('property')}: {meta.get('content', '')}")
    
    if len(meta_section) > 1:
        content_parts.append('\n'.join(meta_section))
    
    # 3.2 提取主体内容（保持结构）
    content_parts.append("\n## 页面内容\n")
    
    def extract_text_with_structure(element, level=0):
        """递归提取文本，保持结构"""
        output = []
        
        if element.name:
            # 处理标题
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                h_level = int(element.name[1])
                output.append('#' * h_level + ' ' + element.get_text(strip=True))
            
            # 处理段落
            elif element.name == 'p':
                text = element.get_text(strip=True)
                if text:  # 即使很短也保留
                    output.append(text)
            
            # 处理列表
            elif element.name in ['ul', 'ol']:
                for li in element.find_all('li', recursive=False):
                    output.append('- ' + li.get_text(strip=True))
            
            # 处理表格（简单ASCII表示）
            elif element.name == 'table':
                output.append("\n[表格内容]")
                for row in element.find_all('tr'):
                    cells = row.find_all(['td', 'th'])
                    if cells:
                        row_text = ' | '.join(cell.get_text(strip=True) for cell in cells)
                        output.append('| ' + row_text + ' |')
            
            # 处理图片
            elif element.name == 'img':
                alt = element.get('alt', '')
                src = element.get('src', '')
                output.append(f"[图片: {alt or src}]")
            
            # 处理视频
            elif element.name == 'video':
                src = element.get('src', '多个源')
                output.append(f"[视频: {src}]")
            
            # 处理音频
            elif element.name == 'audio':
                src = element.get('src', '多个源')
                output.append(f"[音频: {src}]")
            
            # 处理链接（保留链接文本和URL）
            elif element.name == 'a':
                href = element.get('href', '')
                text = element.get_text(strip=True)
                if text and href:
                    output.append(f"[{text}]({href})")
                elif text:
                    output.append(text)
            
            # 处理块引用
            elif element.name == 'blockquote':
                text = element.get_text(strip=True)
                if text:
                    output.append('> ' + text)
            
            # 处理预格式化文本
            elif element.name in ['pre', 'code']:
                text = element.get_text(strip=False)  # 保留空白
                if text:
                    output.append('```\n' + text + '\n```')
            
            # 其他块级元素
            elif element.name in ['div', 'section', 'article', 'main', 'aside', 'header', 'footer']:
                # 递归处理子元素
                for child in element.children:
                    if hasattr(child, 'name'):
                        child_output = extract_text_with_structure(child, level + 1)
                        output.extend(child_output)
                    elif isinstance(child, str):
                        text = child.strip()
                        if text and len(text) > 1:  # 保留几乎所有文本
                            output.append(text)
            
            # 处理其他内联元素
            elif element.name in ['span', 'strong', 'em', 'b', 'i', 'u']:
                text = element.get_text(strip=True)
                if text:
                    output.append(text)
        
        return output
    
    # 提取body内容
    body = soup.body if soup.body else soup
    body_content = []
    
    # 直接处理body的子元素
    for child in body.children:
        if hasattr(child, 'name'):
            child_output = extract_text_with_structure(child, 0)
            body_content.extend(child_output)
        elif isinstance(child, str):
            text = child.strip()
            if text and len(text) > 1:  # 保留几乎所有文本
                body_content.append(text)
    
    # 去除连续空行，但保留段落结构
    cleaned_content = []
    prev_empty = False
    for line in body_content:
        if not line:
            if not prev_empty:
                cleaned_content.append('')
                prev_empty = True
        else:
            cleaned_content.append(line)
            prev_empty = False
    
    content_parts.extend(cleaned_content)
    
    # 3.3 提取所有链接（作为附录）
    all_links = []
    for a in soup.find_all('a', href=True):
        href = a.get('href')
        text = a.get_text(strip=True)
        if href and not href.startswith('#'):
            # 解析相对URL
            if not href.startswith(('http://', 'https://', '//')):
                from urllib.parse import urljoin
                href = urljoin(url, href)
            all_links.append(f"- [{text or '无文本'}]({href})")
    
    if all_links:
        content_parts.append("\n## 页面链接汇总\n")
        content_parts.extend(all_links[:100])  # 限制最多100个链接
        if len(all_links) > 100:
            content_parts.append(f"\n... 还有 {len(all_links) - 100} 个链接未显示")
    
    # 3.4 提取所有图片
    all_images = []
    for img in soup.find_all('img', src=True):
        src = img.get('src')
        alt = img.get('alt', '')
        if src and not src.startswith('data:'):
            # 解析相对URL
            if not src.startswith(('http://', 'https://', '//')):
                from urllib.parse import urljoin
                src = urljoin(url, src)
            all_images.append(src)
    
    if all_images:
        content_parts.append("\n## 页面图片汇总\n")
        for img_url in all_images[:50]:  # 限制最多50张图片
            content_parts.append(f"![]({img_url})")
        if len(all_images) > 50:
            content_parts.append(f"\n... 还有 {len(all_images) - 50} 张图片未显示")
    
    # 4. 构建最终的Markdown
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    date_only = datetime.datetime.now().strftime('%Y-%m-%d')
    
    md_lines = [
        f"# {title}",
        "",
        "## 文档信息",
        f"- 标题: {title}",
        f"- 来源: [{url}]({url})",
        f"- 抓取时间: {current_time}",
        f"- 解析模式: Raw (完整内容模式)",
        "",
        *content_parts
    ]
    
    # 5. 构建元数据
    metadata = {
        'parser': 'raw',
        'parser_used': parser_used,
        'title': title,
        'url': url,
        'scraped_at': current_time,
        'content_length': len(html),
        'text_length': sum(len(part) for part in content_parts if isinstance(part, str)),
        'images_count': len(all_images),
        'links_count': len(all_links),
        'description': f'Raw mode extraction using {parser_used} - complete content preservation'
    }
    
    return date_only, '\n'.join(md_lines), metadata


def generic_to_markdown(html: str, url: str) -> tuple[str, str, dict]:
    title = extract_meta(html, 'og:title') or extract_meta(html, 'twitter:title')
    if not title:
        m = re.search(r'<title[^>]*>(.*?)</title>', html, re.I|re.S)
        if m:
            title = ihtml.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip()
    title = title or '未命名'
    date_only, date_time = parse_date_like(extract_meta(html, 'article:published_time') or extract_meta(html, 'og:updated_time'))
    
    # Priority 1: Try JSON-LD extraction first
    desc = ''
    json_ld = extract_json_ld_content(html)
    if json_ld.get('articleBody'):
        desc = json_ld['articleBody']
    elif json_ld.get('description'):
        desc = json_ld['description']
    
    # Priority 2: Try to extract from multiple <p> tags (for sites like ebchina.com)
    if not desc:
        # Extract all paragraph content with various styles
        p_patterns = [
            r'<p[^>]*class=["\']p["\'][^>]*>(.*?)</p>',  # class="p"
            r'<p[^>]*style=["\'][^"\']*text-align[^"\']*["\'][^>]*>(.*?)</p>',  # style with text-align
        ]
        
        all_paragraphs = []
        for pattern in p_patterns:
            p_matches = re.findall(pattern, html, re.I|re.S)
            for p in p_matches:
                # Clean HTML but preserve structure indicators
                text = re.sub(r'<video[^>]*>.*?</video>', '[视频]', p, flags=re.I|re.S)
                text = re.sub(r'<img[^>]*>', '', text)  # Remove img tags (will be handled separately)
                text = re.sub(r'<[^>]+>', '', text)  # Remove other HTML tags
                text = ihtml.unescape(text).strip()
                if text and len(text) > 5 and text not in all_paragraphs:  # Skip duplicates and very short text
                    all_paragraphs.append(text)
        
        if all_paragraphs:
            desc = '\n\n'.join(all_paragraphs)
    
    # Priority 3: Beijing gov site specific content divs (existing code)
    if not desc:
        for pattern in [r'<div[^>]+class=["\']view[^>]*>(.*?)</div>',
                       r'<div[^>]+class=["\']TRS_UEDITOR[^>]*>(.*?)</div>']:
            m = re.search(pattern, html, re.I|re.S)
            if m:
                desc = re.sub(r'<[^>]+>', '', m.group(1))
                desc = ihtml.unescape(desc).strip()
                break
    
    # Priority 4: Try to extract content from generic <p> tags
    if not desc:
        # Extract all generic paragraphs with substantial content
        generic_p_pattern = r'<p[^>]*>(.*?)</p>'
        generic_p_matches = re.findall(generic_p_pattern, html, re.I|re.S)
        if generic_p_matches:
            paragraphs = []
            for p in generic_p_matches:
                # Clean HTML tags
                text = re.sub(r'<img[^>]*>', '[图片]', p)  # Replace images with placeholder
                text = re.sub(r'<video[^>]*>.*?</video>', '[视频]', text, flags=re.I|re.S)  # Replace videos
                text = re.sub(r'<[^>]+>', '', text)
                text = ihtml.unescape(text).strip()
                # Only include substantial paragraphs (more than 20 chars)
                if text and len(text) > 20 and not text.startswith('var ') and not text.startswith('function'):
                    paragraphs.append(text)
            if len(paragraphs) >= 3:  # Only use if we found multiple paragraphs
                desc = '\n\n'.join(paragraphs)
    
    # Priority 5: Fallback to meta description (existing code)
    if not desc:
        desc = extract_meta(html, 'description').strip()
    
    # Update date if JSON-LD has it and no meta date was found
    original_meta_date = extract_meta(html, 'article:published_time') or extract_meta(html, 'og:updated_time')
    if json_ld.get('datePublished') and not original_meta_date:
        date_only, date_time = parse_date_like(json_ld['datePublished'])
    
    # Extract images and videos from content
    images = []
    videos = []
    
    # Find all img tags
    img_pattern = r'<img[^>]*src=["\']*([^"\'\s>]+)["\']*[^>]*>'
    img_matches = re.findall(img_pattern, html, re.I)
    for img_url in img_matches:
        if img_url and not img_url.startswith('data:'):
            full_url = resolve_url_with_context(url, img_url)
            if full_url not in images:
                images.append(full_url)
    
    # Find all video tags
    video_pattern = r'<video[^>]*src=["\']*([^"\'\s>]+)["\']*[^>]*>'
    video_matches = re.findall(video_pattern, html, re.I)
    for video_url in video_matches:
        if video_url:
            full_url = resolve_url_with_context(url, video_url)
            if full_url not in videos:
                videos.append(full_url)
    
    lines = [f"# {title}", f"- 标题: {title}", f"- 发布时间: {date_time}", f"- 来源: [{url}]({url})", f"- 抓取时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "", desc or '(未能提取正文)']
    
    # Add images section if any images found
    if images:
        lines.append("\n## 图片\n")
        for img_url in images:
            lines.append(f"![]({img_url})")
    
    # Add videos section if any videos found
    if videos:
        lines.append("\n## 视频\n")
        for video_url in videos:
            lines.append(f"[视频链接]({video_url})")
    
    metadata = {
        'description': desc,
        'images': images,
        'videos': videos,
        'publish_time': json_ld.get('datePublished') or extract_meta(html, 'article:published_time') or extract_meta(html, 'og:updated_time'),
        'author': json_ld.get('author', '')
    }
    return date_only, "\n\n".join(lines).strip() + "\n", metadata


def find_next_url(html: str, current_url: str, parser_name: str) -> Optional[str]:
    """Find next page URL based on parser type."""
    if 'mkdocs' in parser_name.lower():
        return find_mkdocs_next_url(html, current_url)
    elif 'docusaurus' in parser_name.lower():
        return find_docusaurus_next_url(html, current_url)
    return None

def find_mkdocs_next_url(html: str, current_url: str) -> Optional[str]:
    """Find next URL in MkDocs navigation."""
    patterns = [
        r'<a[^>]+class=["\'][^"\']*md-footer-nav__link--next[^"\']*["\'][^>]*href=["\']([^"\']+)["\']',
        r'<a[^>]+href=["\']([^"\']+)["\'][^>]*class=["\'][^"\']*md-footer-nav__link--next[^"\']*["\']',
        r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>[\s\S]*?Next[\s\S]*?</a>'
    ]
    for pat in patterns:
        m = re.search(pat, html, re.I)
        if m:
            next_url = m.group(1)
            # Skip same-page anchors and relative anchors
            if next_url.startswith('#'):
                continue
            full_url = resolve_url_with_context(current_url, next_url)
            # Skip if it's the same URL (just with different anchor)
            if full_url.split('#')[0] == current_url.split('#')[0]:
                continue
            return full_url
    return None

def find_docusaurus_next_url(html: str, current_url: str) -> Optional[str]:
    """Find next URL in Docusaurus navigation."""
    patterns = [
        r'<a[^>]+class=["\'][^"\']*pagination-nav__link--next[^"\']*["\'][^>]*href=["\']([^"\']+)["\']',
        r'<a[^>]+href=["\']([^"\']+)["\'][^>]*class=["\'][^"\']*pagination-nav__link--next[^"\']*["\']'
    ]
    for pat in patterns:
        m = re.search(pat, html, re.I)
        if m:
            next_url = m.group(1)
            # Skip same-page anchors and relative anchors
            if next_url.startswith('#'):
                continue
            full_url = resolve_url_with_context(current_url, next_url)
            # Skip if it's the same URL (just with different anchor)
            if full_url.split('#')[0] == current_url.split('#')[0]:
                continue
            return full_url
    return None

def is_same_section(current_url: str, next_url: str) -> bool:
    """Check if next URL belongs to same documentation section."""
    c_parts = urllib.parse.urlparse(current_url)
    n_parts = urllib.parse.urlparse(next_url)
    return (c_parts.netloc == n_parts.netloc and 
            n_parts.path.startswith(c_parts.path.rsplit('/', 2)[0]))

def process_pagination(initial_url: str, initial_html: str, parser_func, ua: str) -> list:
    """Follow pagination links and collect all pages."""
    visited = set()
    pages = []
    current_url = initial_url
    current_html = initial_html
    depth = 0
    
    while depth < MAX_PAGINATION_DEPTH and current_url not in visited:
        try:
            visited.add(current_url)
            logging.info(f"Processing page {depth + 1}: {current_url}")
            pages.append(parser_func(current_html, current_url))
            
            next_url = find_next_url(current_html, current_url, parser_func.__name__)
            if not next_url or not is_same_section(current_url, next_url):
                logging.info(f"Pagination stopped: {'no next URL' if not next_url else 'different section'}")
                break
                
            logging.info(f"Following pagination to: {next_url}")
            current_html = fetch_html(next_url, ua=ua, timeout=30)
            current_url = next_url
            depth += 1
            
        except Exception as e:
            logging.warning(f"Pagination stopped at depth {depth}: {e}")
            break
    
    return pages

def aggregate_multi_page_content(pages: list) -> tuple[str, str, dict]:
    """Merge multiple page contents into single markdown document."""
    if not pages:
        return '', '', {}
    
    first_date, first_content, first_metadata = pages[0]
    if len(pages) == 1:
        return first_date, first_content, first_metadata
    
    # Combine all content
    all_content = [first_content]
    all_images = list(first_metadata.get('images', []))
    
    for i in range(1, len(pages)):
        date, content, metadata = pages[i]
        # Extract body content (skip header metadata lines)
        lines = content.split('\n')
        body_start = 0
        for j, line in enumerate(lines):
            if line.strip() and not line.startswith('- ') and not line.startswith('#'):
                body_start = j
                break
        
        body_content = '\n'.join(lines[body_start:]).strip()
        if body_content:
            all_content.append(f"\n---\n\n{body_content}")
        
        # Aggregate images
        all_images.extend(metadata.get('images', []))
    
    # Create combined metadata
    combined_metadata = first_metadata.copy()
    combined_metadata['images'] = list(set(all_images))
    combined_metadata['pages_count'] = len(pages)
    
    return first_date, '\n'.join(all_content), combined_metadata


def normalize_url_for_dedup(url: str) -> str:
    """Normalize URL for deduplication: lowercase scheme and netloc only, preserve path case, remove fragments, sort query params."""
    parsed = urllib.parse.urlparse(url)
    
    # Only lowercase the scheme and netloc (domain), preserve path case
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    
    # Sort query parameters alphabetically
    query_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    sorted_query = urllib.parse.urlencode(sorted(query_params))
    
    # Normalize path (remove trailing slash except for root) - preserve case
    path = parsed.path.rstrip('/') if parsed.path != '/' else parsed.path
    
    # Reconstruct URL without fragment - preserving original case for path, params
    normalized = urllib.parse.urlunparse((
        scheme, netloc, path, 
        parsed.params, sorted_query, ''
    ))
    return normalized

def should_crawl_url(url: str) -> bool:
    """Smart filtering to skip binary files, APIs, and build artifacts."""
    url_lower = url.lower()
    parsed = urllib.parse.urlparse(url_lower)
    path = parsed.path
    
    # Check file extensions
    for ext_set in [BINARY_EXTENSIONS, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, AUDIO_EXTENSIONS]:
        if any(path.endswith(ext) for ext in ext_set):
            return False
    
    # Check API and build patterns
    for pattern_set in [API_PATTERNS, BUILD_PATTERNS]:
        if any(pattern in url_lower for pattern in pattern_set):
            return False
    
    return True

def should_preserve_subdirectory(base_url: str) -> bool:
    """Determine if the base URL represents a subdirectory deployment that should be preserved."""
    base_parts = urllib.parse.urlparse(base_url)
    path_segments = [s for s in base_parts.path.strip('/').split('/') if s]
    
    if not path_segments:
        return False
    
    first_segment = path_segments[0]
    
    # GitHub Pages subdirectory deployments
    if base_parts.netloc.endswith('.github.io'):
        return True
    
    # Documentation sites with 'docs' in path
    if 'docs' in first_segment.lower():
        return True
    
    # Multi-level paths indicate subdirectory deployment
    if len(path_segments) > 1:
        return True
    
    # Sites with common project/documentation patterns
    doc_patterns = ['project', 'manual', 'guide', 'api', 'reference', 'book']
    if any(pattern in first_segment.lower() for pattern in doc_patterns):
        return True
    
    return False

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

def extract_internal_links(html: str, base_url: str) -> dict:
    """Extract all internal links from HTML content with smart subdirectory resolution.
    Returns dict mapping normalized URLs to original URLs for case-preserving fetching."""
    links = {}  # normalized_url -> original_url
    base_parts = urllib.parse.urlparse(base_url)
    
    # Find all href attributes
    href_pattern = r'href=["\']([^"\']*)["\']'
    for match in re.finditer(href_pattern, html, re.I):
        href = match.group(1)
        
        # Skip empty hrefs or anchors, javascript, mailto
        if not href or href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
            continue
            
        # Convert to absolute URL using smart context resolution
        full_url = resolve_url_with_context(base_url, href)
        url_parts = urllib.parse.urlparse(full_url)
        
        # Check if same domain and should crawl
        if url_parts.netloc == base_parts.netloc and should_crawl_url(full_url):
            # Map normalized URL to original URL for case-preserving fetching
            normalized = normalize_url_for_dedup(full_url)
            links[normalized] = full_url
    
    return links

def is_documentation_url(url: str) -> bool:
    """Filter URLs to likely documentation pages."""
    # Skip common non-doc patterns
    skip_patterns = [
        r'/api/', r'/download', r'\.zip$', r'\.tar', r'\.pdf$',
        r'/signin', r'/login', r'/auth', r'/search\?',
        r'\.xml$', r'\.json$', r'/feed', r'/rss'
    ]
    
    for pattern in skip_patterns:
        if re.search(pattern, url, re.I):
            return False
    
    return True  # Default: include

def crawl_site(start_url: str, ua: str, max_depth: int = 10, 
               max_pages: int = 1000, delay: float = 0.5) -> list:
    """
    Crawl entire site using BFS algorithm.
    Returns list of (url, html, depth) tuples.
    """
    # Initialize crawl statistics
    stats = {
        'pages_crawled': 0,
        'pages_success': 0, 
        'pages_failed': 0,
        'total_size': 0,
        'start_time': time.time(),
        'failed_urls': []  # Track failed URLs for detailed reporting
    }
    
    visited_normalized = set()  # For deduplication using normalized URLs
    url_mapping = {}  # Maps normalized URLs to original URLs for fetching
    queue = deque([(start_url, 0)])  # (original_url, depth) - keep original URL
    pages = []
    
    logging.info(f"Starting site crawl from {start_url}")
    logging.info(f"Settings: max_depth={max_depth}, max_pages={max_pages}, delay={delay}s")
    
    while queue and len(visited_normalized) < max_pages:
        current_url, depth = queue.popleft()
        current_normalized = normalize_url_for_dedup(current_url)
        
        # Skip if already visited or too deep
        if current_normalized in visited_normalized or depth > max_depth:
            continue
        
        # Rate limiting
        if visited_normalized and delay > 0:
            time.sleep(delay)
        
        stats['pages_crawled'] += 1
        
        try:
            # Progress reporting: verbose logging vs progress line
            if logging.getLogger().level <= logging.INFO:
                # Verbose mode: full logging
                logging.info(f"[{len(visited_normalized)+1}/{max_pages}] Crawling depth {depth}: {current_url}")
            else:
                # Normal mode: updating progress line on stderr
                elapsed = time.time() - stats['start_time']
                rate = stats['pages_success'] / (elapsed / 60) if elapsed > 0 else 0  # pages per minute
                
                # Progress line that overwrites itself
                sys.stderr.write(f"\rCrawling: {len(visited_normalized)+1}/{max_pages} pages ({rate:.1f} pages/min)")
                sys.stderr.flush()
            
            # Fetch page using original URL (preserves case)
            html = fetch_html(current_url, ua=ua, timeout=30)
            visited_normalized.add(current_normalized)
            url_mapping[current_normalized] = current_url
            pages.append((current_url, html, depth))
            
            # Update statistics
            stats['pages_success'] += 1
            stats['total_size'] += len(html.encode('utf-8'))
            
            # Extract and queue new links (only if not at max depth)
            if depth < max_depth:
                link_mapping = extract_internal_links(html, current_url)
                new_normalized_links = set(link_mapping.keys()) - visited_normalized
                
                # Filter to documentation URLs (check both normalized and original)
                doc_links = [(norm, orig) for norm, orig in link_mapping.items() 
                           if norm in new_normalized_links and is_documentation_url(orig)]
                
                logging.info(f"Found {len(doc_links)} new documentation links")
                
                for normalized_link, original_link in sorted(doc_links)[:50]:  # Limit per-page discoveries
                    # Queue the original URL for case-preserving fetching
                    queue.append((original_link, depth + 1))
            
        except Exception as e:
            logging.warning(f"Failed to crawl {current_url}: {e}")
            stats['pages_failed'] += 1
            stats['failed_urls'].append((current_url, str(e)))
            continue
    
    # Clear progress line if we were showing it
    if logging.getLogger().level > logging.INFO:
        sys.stderr.write('\r' + ' ' * 80 + '\r')  # Clear the line
        sys.stderr.flush()
    
    # Enhanced crawl summary and visibility reporting
    duration = time.time() - stats['start_time']
    size_mb = stats['total_size'] / (1024 * 1024)
    success_rate = (stats['pages_success'] / stats['pages_crawled'] * 100) if stats['pages_crawled'] > 0 else 0
    
    # 1. Crawl quality summary (5-8 lines)
    logging.info(f"Crawl Quality Summary: {success_rate:.1f}% success rate ({stats['pages_success']}/{stats['pages_crawled']} pages)")
    logging.info(f"Data Retrieved: {size_mb:.1f}MB in {duration:.1f}s ({size_mb/duration:.2f} MB/s)")
    
    # 2. Failed URL details in verbose mode (3-5 lines)
    if stats['failed_urls'] and logging.getLogger().level <= logging.INFO:
        logging.info(f"Failed URLs ({len(stats['failed_urls'])}):") 
        for failed_url, error in stats['failed_urls'][:5]:  # Show first 5 failures
            logging.info(f"  - {failed_url}: {error}")
        if len(stats['failed_urls']) > 5:
            logging.info(f"  ... and {len(stats['failed_urls']) - 5} more failures")
    
    # 3. Completeness indicator (2-3 lines)
    hit_max_pages = len(visited_normalized) >= max_pages
    hit_max_depth = any(depth >= max_depth for _, _, depth in pages)
    if hit_max_pages or hit_max_depth:
        limits_hit = []
        if hit_max_pages: limits_hit.append(f"max-pages({max_pages})")
        if hit_max_depth: limits_hit.append(f"max-depth({max_depth})")
        logging.info(f"Crawl Status: INCOMPLETE - stopped due to {' and '.join(limits_hit)} limit")
    else:
        logging.info("Crawl Status: COMPLETE - all discoverable pages crawled")
    
    return pages

def aggregate_crawled_site(pages: list, parser_func) -> tuple[str, str, dict]:
    """
    Aggregate crawled site pages into single comprehensive document.
    Organizes content by depth and URL structure.
    """
    if not pages:
        return '', '', {}
    
    # Group pages by depth for hierarchical organization
    by_depth = {}
    for url, html, depth in pages:
        if depth not in by_depth:
            by_depth[depth] = []
        by_depth[depth].append((url, html))
    
    # Parse all pages
    all_content = []
    all_images = []
    toc_entries = []
    
    for depth in sorted(by_depth.keys()):
        if depth > 0:
            all_content.append(f"\n{'#' * (depth + 1)} Level {depth} Pages\n")
        
        for url, html in by_depth[depth]:
            try:
                date, content, metadata = parser_func(html, url)
                
                # Extract title from content
                title_match = re.search(r'^#\s+(.+)$', content, re.M)
                title = title_match.group(1) if title_match else urllib.parse.urlparse(url).path
                
                # Add to TOC
                indent = '  ' * depth
                toc_entries.append(f"{indent}- [{title}](#{depth}-{len(toc_entries)})")
                
                # Add content with section anchor
                all_content.append(f"\n<a id='{depth}-{len(toc_entries)-1}'></a>\n")
                all_content.append(content)
                all_content.append("\n---\n")
                
                # Collect images
                all_images.extend(metadata.get('images', []))
                
            except Exception as e:
                logging.warning(f"Failed to parse {url}: {e}")
    
    # Build final document with TOC
    toc = "## Table of Contents\n\n" + '\n'.join(toc_entries)
    final_content = toc + "\n\n" + '\n'.join(all_content)
    
    # Create metadata
    metadata = {
        'total_pages': len(pages),
        'max_depth': max(by_depth.keys()) if by_depth else 0,
        'images': list(set(all_images)),
        'crawl_complete': True
    }
    
    return datetime.datetime.now().strftime("%Y-%m-%d"), final_content, metadata


def rewrite_and_download_assets(md: str, md_base: str, outdir: Path, ua: str, assets_root: str) -> str:
    # Find all http(s) images
    urls = []
    for m in re.finditer(r'!\[[^\]]*\]\((https?://[^)]+)\)', md, re.I):
        url = m.group(1)
        if url not in urls:
            urls.append(url)
    # Also capture regular links that are image-like
    for m in re.finditer(r'\[[^\]]*\]\((https?://[^)]+)\)', md, re.I):
        url = m.group(1)
        if url in urls:
            continue
        if re.search(r'\.(?:jpg|jpeg|png|webp|gif)(?:\?|$)', url, re.I) or ('imageMogr2' in url) or ('imageView2' in url):
            urls.append(url)
    if not urls:
        return md
    # Prepare asset directory
    assets_dir = outdir / assets_root / sanitize_filename(md_base)
    assets_dir.mkdir(parents=True, exist_ok=True)

    def filename_for(i: int, url: str) -> str:
        # derive extension from URL path; fallback to .jpg
        path = urllib.parse.urlparse(url).path
        ext = ''
        m = re.search(r'\.([a-zA-Z0-9]{3,4})$', path)
        if m:
            ext = '.' + m.group(1).lower()
        elif 'imageMogr2' in url or 'imageView2' in url:
            ext = '.jpg'
        else:
            ext = '.jpg'
        return f"{i:02d}{ext}"

    # Download and build mapping
    mapping = {}
    for idx, u in enumerate(urls, start=1):
        fname = filename_for(idx, u)
        dest = assets_dir / fname
        if not dest.exists():
            # download with UA
            try:
                req = urllib.request.Request(u, headers={"User-Agent": ua, "Accept-Language": "zh-CN,zh;q=0.9"})
                with urllib.request.urlopen(req, timeout=60, context=ssl_context_unverified) as r:
                    data = r.read()
                dest.write_bytes(data)
            except Exception:
                # skip failures; leave URL as is
                continue
        rel_path = os.path.relpath(dest, outdir)
        mapping[u] = rel_path

    # Replace in Markdown
    def repl_img(m):
        u = m.group(1)
        return m.group(0).replace(u, mapping.get(u, u))
    def repl_link(m):
        u = m.group(2)
        if u in mapping:
            return f"[{m.group(1)}]({mapping[u]})"
        return m.group(0)
    md2 = re.sub(r'!\[[^\]]*\]\((https?://[^)]+)\)', repl_img, md)
    md2 = re.sub(r'\[([^\]]*)\]\((https?://[^)]+)\)', repl_link, md2)
    return md2


def main():
    ap = argparse.ArgumentParser(
        description='Fetch a URL (WeChat/XHS/generic) and save as Markdown.',
        prog='webfetcher'
    )
    ap.add_argument('url', help='Target URL')
    ap.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    ap.add_argument('-o','--outdir', default='.', help='Output directory (default: current)')
    ap.add_argument('--render', choices=['auto','always','never'], default='auto', help='Use headless rendering (default: auto)')
    ap.add_argument('--timeout', type=int, default=60, help='Network timeout in seconds (fetch). Default: 60')
    ap.add_argument('--render-timeout', type=int, default=90, help='Rendering timeout in seconds (Playwright). Default: 90')
    ap.add_argument('--html', help='Use local HTML file instead of fetching/rendering')
    ap.add_argument('--download-assets', action='store_true', help='Download images to assets/<file>/ and rewrite links (default: preserve URLs only)')
    ap.add_argument('--assets-root', default='assets', help='Assets root directory name (default: assets)')
    ap.add_argument('--save-html', nargs='?', const=True, help='Save fetched/rendered HTML snapshot before parsing (optional path).')
    ap.add_argument('--json', action='store_true', help='Output structured JSON alongside Markdown')
    ap.add_argument('--verbose', action='store_true', help='Enable verbose logging (INFO level)')
    ap.add_argument('--follow-pagination', action='store_true', 
                    help='Follow next/previous links to aggregate multi-page documents (MkDocs/Docusaurus only)')
    ap.add_argument('--raw', action='store_true', 
                    help='Use raw parser mode (complete content preservation, no filtering)')
    ap.add_argument('--crawl-site', action='store_true',
                    help='Recursively crawl entire site (BFS traversal of all internal links)')
    ap.add_argument('--max-crawl-depth', type=int, default=10,
                    help='Maximum crawl depth for site crawling (default: 10, max: 10)')
    ap.add_argument('--max-pages', type=int, default=1000,
                    help='Maximum pages to crawl (default: 1000, max: 1000)')
    ap.add_argument('--crawl-delay', type=float, default=0.5,
                    help='Delay between crawl requests in seconds (default: 0.5)')
    args = ap.parse_args()
    
    # Check for legacy mode environment variable
    if os.environ.get('WF_LEGACY_IMAGE_MODE'):
        logging.warning("DEPRECATION: WF_LEGACY_IMAGE_MODE is set. Auto-download behavior will be removed in future versions.")
        # Set a flag for legacy behavior
        args.legacy_image_mode = True
    else:
        args.legacy_image_mode = False
    
    # Validate crawl limits against absolute maximums
    if args.max_crawl_depth > MAX_CRAWL_DEPTH:
        logging.warning(f"Requested depth {args.max_crawl_depth} exceeds maximum {MAX_CRAWL_DEPTH}, using {MAX_CRAWL_DEPTH}")
        args.max_crawl_depth = MAX_CRAWL_DEPTH
    if args.max_pages > MAX_CRAWL_PAGES:
        logging.warning(f"Requested pages {args.max_pages} exceeds maximum {MAX_CRAWL_PAGES}, using {MAX_CRAWL_PAGES}")
        args.max_pages = MAX_CRAWL_PAGES
    
    setup_logging(args.verbose)
    url = args.url
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    
    logging.info(f"Starting webfetcher for URL: {url}")

    # Resolve redirects to get effective host for parser selection
    host = get_effective_host(url, ua=None)  # UA will be determined after this
    original_host = urllib.parse.urlparse(url).hostname or ''
    ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36"
    # Use a mobile WeChat UA for WeChat pages; desktop Chrome UA for XHS
    if 'mp.weixin.qq.com' in host or 'weixin.qq.com' in host:
        ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.42(0x18002a2c) NetType/WIFI Language/zh_CN'
    elif 'xiaohongshu.com' in host or 'xhslink.com' in original_host:
        ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    elif 'dianping.com' in host:
        ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'

    # Site crawling mode (overrides single-page fetch)
    if args.crawl_site:
        logging.info("Site crawling mode activated")
        
        # Check if supported site type
        if 'mp.weixin.qq.com' in host or 'xiaohongshu.com' in host or 'xhslink.com' in original_host or 'dianping.com' in host:
            logging.error("Site crawling not supported for social media sites")
            sys.exit(1)
        
        # Crawl the site
        crawled_pages = crawl_site(
            url, ua, 
            max_depth=args.max_crawl_depth,
            max_pages=args.max_pages,
            delay=args.crawl_delay
        )
        
        if crawled_pages:
            # Detect appropriate parser from first page
            first_html = crawled_pages[0][1]
            if args.raw:
                parser_func = raw_to_markdown
                parser_name = "Raw"
                logging.info("Using Raw parser for site content (user requested)")
            elif re.search(r'theme-doc-markdown|class="[^"]*\\bmarkdown\\b', first_html, re.I):
                parser_func = docusaurus_to_markdown
                parser_name = "Docusaurus"
            elif re.search(r'md-content__inner\s+md-typeset', first_html, re.I):
                parser_func = mkdocs_to_markdown
                parser_name = "MkDocs"
            else:
                parser_func = generic_to_markdown
                parser_name = "Generic"
            
            logging.info(f"Using {parser_name} parser for site content")
            
            # Aggregate all content
            date_only, md, metadata = aggregate_crawled_site(crawled_pages, parser_func)
            metadata['parser_used'] = parser_name
            rendered = False
            
            # Process and save file directly in crawl mode
            # Title for filename comes from first heading
            m = re.match(r'^#\s*(.+)$', md.splitlines()[0].strip())
            title = m.group(1) if m else '未命名'
            # Use current timestamp for filename to avoid conflicts
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
            base = f"{timestamp} - {sanitize_filename(title)}"
            path = ensure_unique_path(outdir, base)
            
            # Optionally download images and rewrite links
            if hasattr(args, 'legacy_image_mode') and args.legacy_image_mode:
                # Legacy behavior for backward compatibility
                do_download_assets = args.download_assets or ('mp.weixin.qq.com' in host) or ('xiaohongshu.com' in host) or ('xhslink.com' in original_host)
            else:
                # New default: only download if explicitly requested
                do_download_assets = args.download_assets
            if do_download_assets:
                logging.info("Starting asset downloads")
                md_base = base  # same base as filename
                md = rewrite_and_download_assets(md, md_base, outdir, ua, args.assets_root)
                logging.info("Asset downloads completed")
            
            path.write_text(md, encoding='utf-8')
            logging.info(f"Markdown file saved: {path}")
            
            # Generate JSON output if requested
            if args.json:
                json_data = {
                    'url': url,
                    'title': title,
                    'date': f"{date_only} {datetime.datetime.now().strftime('%H:%M:%S')}",
                    'content': md,
                    'images': metadata.get('images', []),
                    'metadata': {
                        **metadata,
                        'parser_used': parser_name,
                        'fetch_method': 'crawl',
                        'scraped_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                }
                json_path = path.with_suffix('.json')
                json_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding='utf-8')
                logging.info(f"JSON data saved: {json_path}")
            
            print(str(path))
            return  # Exit the main function after crawling is complete
            
        else:
            logging.error("No pages crawled successfully")
            sys.exit(1)
    elif args.html:
        html = Path(args.html).read_text(encoding='utf-8', errors='ignore')
    else:
        html = None
        should_render = (args.render == 'always') or (args.render == 'auto' and ('xiaohongshu.com' in host or 'xhslink.com' in original_host or 'dianping.com' in host))
        logging.info(f"Render decision: {'will render' if should_render else 'static fetch only'}")
        if should_render:
            logging.info("Attempting headless rendering with Playwright")
            rendered = try_render(url, ua=ua, timeout_ms=max(1000, args.render_timeout*1000))
            if rendered:
                logging.info("Rendering successful")
                html = rendered
            else:
                logging.info("Rendering failed, falling back to static fetch")
        if html is None:
            logging.info("Fetching HTML statically")
            html = fetch_html(url, ua=ua, timeout=args.timeout)
            logging.info("Static fetch completed")

    # Optionally save HTML snapshot before parsing
    if args.save_html:
        if args.save_html is True:
            ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            host_safe = (urllib.parse.urlparse(url).hostname or 'page').replace(':','_')
            snapshot_path = Path(args.outdir) / f"snapshot_{host_safe}_{ts}.html"
        else:
            snapshot_path = Path(str(args.save_html))
            if snapshot_path.is_dir():
                ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                host_safe = (urllib.parse.urlparse(url).hostname or 'page').replace(':','_')
                snapshot_path = snapshot_path / f"snapshot_{host_safe}_{ts}.html"
        try:
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot_path.write_text(html, encoding='utf-8')
            logging.info(f"HTML snapshot saved to: {snapshot_path}")
        except Exception as e:
            logging.warning(f"Failed to save HTML snapshot: {e}")

    # Parser selection
    if args.raw:
        logging.info("Selected parser: Raw (user requested)")
        parser_name = "Raw"
        date_only, md, metadata = raw_to_markdown(html, url)
        rendered = False
    elif 'mp.weixin.qq.com' in host:
        logging.info("Selected parser: WeChat")
        parser_name = "WeChat"
        date_only, md, metadata = wechat_to_markdown(html, url)
        rendered = 'wechat' in ua.lower()
    elif 'xiaohongshu.com' in host or 'xhslink.com' in original_host:
        logging.info("Selected parser: Xiaohongshu")
        parser_name = "Xiaohongshu"
        date_only, md, metadata = xhs_to_markdown(html, url)
        rendered = should_render
    elif 'dianping.com' in host:
        logging.info("Selected parser: Dianping")
        parser_name = "Dianping"
        date_only, md, metadata = dianping_to_markdown(html, url)
        rendered = should_render
    elif 'ebchina.com' in host and 'class="N_title"' in html:
        # EB China news list page
        logging.info("Selected parser: EB China News List")
        parser_name = "EBChina_NewsList"
        date_only, md, metadata = ebchina_news_list_to_markdown(html, url)
        rendered = False
    elif re.search(r'theme-doc-markdown|class=\"[^\"]*\\bmarkdown\\b', html, re.I):
        logging.info("Selected parser: Docusaurus")
        parser_name = "Docusaurus"
        # Multi-page support for Docusaurus
        if args.follow_pagination:
            logging.info("Multi-page mode enabled, following pagination links...")
            pages = process_pagination(url, html, docusaurus_to_markdown, ua)
            if len(pages) > 1:
                logging.info(f"Aggregated {len(pages)} pages into single document")
                date_only, md, metadata = aggregate_multi_page_content(pages)
            else:
                date_only, md, metadata = pages[0]
        else:
            date_only, md, metadata = docusaurus_to_markdown(html, url)
        rendered = False
    elif re.search(r'md-content__inner\s+md-typeset', html, re.I):
        logging.info("Selected parser: MkDocs")
        parser_name = "MkDocs"
        # Multi-page support for MkDocs
        if args.follow_pagination:
            logging.info("Multi-page mode enabled, following pagination links...")
            pages = process_pagination(url, html, mkdocs_to_markdown, ua)
            if len(pages) > 1:
                logging.info(f"Aggregated {len(pages)} pages into single document")
                date_only, md, metadata = aggregate_multi_page_content(pages)
            else:
                date_only, md, metadata = pages[0]
        else:
            date_only, md, metadata = mkdocs_to_markdown(html, url)
        rendered = False
    else:
        logging.info("Selected parser: Generic")
        parser_name = "Generic"
        date_only, md, metadata = generic_to_markdown(html, url)
        rendered = False

    # Title for filename comes from first heading
    m = re.match(r'^#\s*(.+)$', md.splitlines()[0].strip())
    title = m.group(1) if m else '未命名'
    # Use current timestamp for filename to avoid conflicts
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    base = f"{timestamp} - {sanitize_filename(title)}"
    path = ensure_unique_path(outdir, base)
    # Optionally download images and rewrite links
    if hasattr(args, 'legacy_image_mode') and args.legacy_image_mode:
        # Legacy behavior for backward compatibility
        do_download_assets = args.download_assets or ('mp.weixin.qq.com' in host) or ('xiaohongshu.com' in host) or ('xhslink.com' in original_host)
    else:
        # New default: only download if explicitly requested
        do_download_assets = args.download_assets
    if do_download_assets:
        logging.info("Starting asset downloads")
        md_base = base  # same base as filename (includes timestamp)
        md = rewrite_and_download_assets(md, md_base, outdir, ua, args.assets_root)
        logging.info("Asset downloads completed")
    
    path.write_text(md, encoding='utf-8')
    logging.info(f"Markdown file saved: {path}")
    
    # Generate JSON output if requested
    if args.json:
        json_data = {
            'url': url,
            'title': title,
            'date': f"{date_only} {datetime.datetime.now().strftime('%H:%M:%S')}",
            'content': md,
            'images': metadata.get('images', []),
            'metadata': {
                **metadata,
                'parser_mode': parser_name,
                'fetch_method': 'rendered' if rendered else 'static',
                'scraped_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        json_path = path.with_suffix('.json')
        json_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding='utf-8')
        logging.info(f"JSON data saved: {json_path}")
    
    print(str(path))


if __name__ == '__main__':
    main()
