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
import urllib.error
import ssl
import sys
from typing import Optional, List, Dict, Set, Any
from dataclasses import dataclass
from enum import Enum
from html.parser import HTMLParser
from pathlib import Path
import logging
import time
import random
import signal
from collections import deque

# Selenium integration (Phase 2) - graceful degradation when not available
try:
    from selenium_config import SeleniumConfig
    from selenium_fetcher import SeleniumFetcher, SeleniumMetrics, ChromeConnectionError, SeleniumFetchError, SeleniumTimeoutError, SeleniumNotAvailableError
    SELENIUM_INTEGRATION_AVAILABLE = True
except ImportError as e:
    logging.debug(f"Selenium integration not available: {e}")
    SELENIUM_INTEGRATION_AVAILABLE = False
    # Create dummy classes to prevent import errors
    class SeleniumConfig: pass
    class SeleniumFetcher: pass
    class SeleniumMetrics: pass
    class ChromeConnectionError(Exception): pass
    class SeleniumFetchError(Exception): pass
    class SeleniumTimeoutError(Exception): pass
    class SeleniumNotAvailableError(Exception): pass

# Parser modules
import parsers

# Safari integration removed - using urllib only


# === EMBEDDED DOWNLOADER MODULE ===
# SSL context for unverified connections
ssl_context_unverified = ssl.create_default_context()
ssl_context_unverified.check_hostname = False
ssl_context_unverified.verify_mode = ssl.CERT_NONE


def sanitize_filename(name: str) -> str:
    invalid = set('/\\:*?"<>|\n\r\t')
    name = ''.join(ch if ch not in invalid else ' ' for ch in name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:160]


class SimpleDownloader:
    def __init__(self):
        self.downloadable_extensions = {
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf',
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'tiff', 'ico',
            'mp3', 'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'wav', 'ogg',
            'zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'dmg', 'iso', 'exe', 'msi', 'deb', 'rpm',
            'xml', 'json', 'csv', 'sql', 'log', 'conf', 'cfg', 'ini', 'yaml', 'yml'
        }
    
    def try_download(self, url, ua, timeout, outdir):
        # Check if this is a downloadable file based on URL extension
        parsed_url = urllib.parse.urlparse(url)
        file_extension = parsed_url.path.lower().split('.')[-1] if '.' in parsed_url.path else ''
        
        if file_extension in self.downloadable_extensions:
            logging.info(f"Detected downloadable file with extension: {file_extension}")
            
            # Extract filename from URL
            filename = parsed_url.path.split('/')[-1] if parsed_url.path else f"download.{file_extension}"
            if not filename or filename == f".{file_extension}":
                # Generate filename from domain and timestamp if path is empty
                domain = parsed_url.hostname or 'unknown'
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{domain}_{timestamp}.{file_extension}"
            
            # Sanitize filename for filesystem
            filename = sanitize_filename(filename)
            
            # Ensure unique filename to avoid conflicts
            outdir = Path(outdir)
            outdir.mkdir(parents=True, exist_ok=True)
            base_path = outdir / filename
            final_path = base_path
            
            counter = 1
            while final_path.exists():
                name_part, ext_part = filename.rsplit('.', 1) if '.' in filename else (filename, '')
                if ext_part:
                    final_path = outdir / f"{name_part}_{counter}.{ext_part}"
                else:
                    final_path = outdir / f"{filename}_{counter}"
                counter += 1
            
            try:
                # Download binary file directly
                logging.info(f"Downloading file to: {final_path}")
                
                # Re-fetch the content as binary data
                req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Language": "zh-CN,zh;q=0.9"})
                with urllib.request.urlopen(req, timeout=timeout, context=ssl_context_unverified) as response:
                    # Write binary data to file
                    with open(final_path, 'wb') as f:
                        while True:
                            chunk = response.read(8192)  # Read in 8KB chunks
                            if not chunk:
                                break
                            f.write(chunk)
                
                file_size = final_path.stat().st_size
                logging.info(f"File downloaded successfully: {final_path} ({file_size} bytes)")
                print(str(final_path))
                return True  # Downloaded successfully, skip HTML processing
                
            except Exception as e:
                logging.error(f"Failed to download file: {e}")
                # Continue with normal HTML processing if download fails
                logging.info("Falling back to HTML processing")
        
        return False  # Not a downloadable file or download failed
# === END EMBEDDED DOWNLOADER MODULE ===



@dataclass
class FetchMetrics:
    """Tracks metrics for web content fetching operations."""
    primary_method: str = ""  # urllib/playwright/local_file
    fallback_method: Optional[str] = None  # selenium (when used as fallback)
    total_attempts: int = 0
    fetch_duration: float = 0.0
    render_duration: float = 0.0
    ssl_fallback_used: bool = False
    final_status: str = "unknown"  # success/failed
    error_message: Optional[str] = None
    
    # Selenium-specific fields (Phase 2 integration)
    selenium_wait_time: float = 0.0
    chrome_connected: bool = False
    js_detection_used: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for JSON serialization."""
        return {
            'primary_method': self.primary_method,
            'fallback_method': self.fallback_method,
            'total_attempts': self.total_attempts,
            'fetch_duration': round(self.fetch_duration, 3),
            'render_duration': round(self.render_duration, 3),
            'ssl_fallback_used': self.ssl_fallback_used,
            'final_status': self.final_status,
            'error_message': self.error_message,
            'selenium_wait_time': round(self.selenium_wait_time, 3),
            'chrome_connected': self.chrome_connected,
            'js_detection_used': self.js_detection_used
        }
    
    def get_summary(self) -> str:
        """Generate a human-readable summary of fetch metrics."""
        method = self.fallback_method if self.fallback_method else self.primary_method
        duration = self.fetch_duration + self.render_duration
        
        summary = f"Fetched via: {method}"
        
        if self.total_attempts > 1:
            summary += f" | Attempts: {self.total_attempts}"
        
        if duration > 0:
            summary += f" | Duration: {duration:.2f}s"
        
        if self.ssl_fallback_used:
            summary += " | SSL fallback used"
        
        # Add Selenium-specific information
        if self.chrome_connected:
            summary += " | Chrome session connected"
        
        if self.selenium_wait_time > 0:
            summary += f" | Selenium wait: {self.selenium_wait_time:.2f}s"
        
        if self.js_detection_used:
            summary += " | JS detection used"
            
        return summary


def add_metrics_to_markdown(md_content: str, metrics: FetchMetrics) -> str:
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
# BeautifulSoup导入移至动态导入机制

def is_url_encoded(text: str) -> bool:
    """
    Check if a text string is already URL-encoded.
    
    Args:
        text: String to check for URL encoding
        
    Returns:
        bool: True if text appears to be URL-encoded, False otherwise
    """
    try:
        # If decoding changes the text, it was encoded
        # Also check for common encoded patterns
        return (urllib.parse.unquote(text, errors='strict') != text or 
                '%' in text and any(c in text for c in ['%20', '%2F', '%3A']))
    except:
        return False

def validate_and_encode_url(url: str) -> str:
    """
    Validate URL and ensure safe encoding for HTTP requests.
    
    Properly handles Unicode characters (e.g., Chinese), spaces, and already-encoded URLs.
    Converts IRI (Internationalized Resource Identifier) to proper URI format.
    
    Args:
        url: URL to validate and encode (can contain Unicode or spaces)
        
    Returns:
        str: Safely encoded URL ready for HTTP requests
        
    Raises:
        ValueError: If URL is invalid or contains unsafe patterns
        
    Examples:
        >>> validate_and_encode_url('https://zh.wikipedia.org/wiki/中文')
        'https://zh.wikipedia.org/wiki/%E4%B8%AD%E6%96%87'
        >>> validate_and_encode_url('https://example.com/path with spaces')
        'https://example.com/path%20with%20spaces'
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
        shell_special_chars = ['`', '$', '\\', '"', "'"]
        for char in shell_special_chars:
            if char in url:
                logging.warning(f"URL contains shell special character '{char}': {url}")
        
        # Encode path component (handles Unicode and spaces)
        if parsed.path:
            # Split path into segments to handle each separately
            path_segments = parsed.path.split('/')
            encoded_segments = []
            
            for segment in path_segments:
                if segment:  # Skip empty segments from leading/trailing slashes
                    if not is_url_encoded(segment):
                        # Encode Unicode and special characters, but preserve slashes
                        encoded_segment = urllib.parse.quote(segment, safe='')
                        encoded_segments.append(encoded_segment)
                    else:
                        # Already encoded, keep as-is
                        encoded_segments.append(segment)
                else:
                    encoded_segments.append(segment)
            
            encoded_path = '/'.join(encoded_segments)
        else:
            encoded_path = parsed.path
        
        # Handle query parameters
        if parsed.query:
            # Parse and re-encode to ensure consistency
            query_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
            encoded_query = urllib.parse.urlencode(query_params)
        else:
            encoded_query = parsed.query
        
        # Handle fragment (anchor)
        if parsed.fragment:
            if not is_url_encoded(parsed.fragment):
                encoded_fragment = urllib.parse.quote(parsed.fragment, safe='')
            else:
                encoded_fragment = parsed.fragment
        else:
            encoded_fragment = parsed.fragment
        
        # Reconstruct the URL with encoded components
        encoded_url = urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc,  # netloc (domain) stays as-is for international domains
            encoded_path,
            parsed.params,  # rarely used, keep as-is
            encoded_query,
            encoded_fragment
        ))
        
        if encoded_url != url:
            logging.debug(f"URL encoded: {url} -> {encoded_url}")
        
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

class ContentFilter:
    """Generic content filtering system for noise removal from any website"""
    
    def __init__(self, filter_level='safe'):
        self.filter_level = filter_level
        self.removed_elements = []
        
    def filter_content(self, soup):
        """Apply content filtering based on filter level"""
        if not soup:
            return soup
            
        self.removed_elements = []
        
        if self.filter_level == 'none':
            return soup
            
        # Safe filters (default) - remove obvious noise
        if self.filter_level in ['safe', 'moderate', 'aggressive']:
            self._remove_scripts_and_styles(soup)
            self._remove_hidden_elements(soup)
            self._remove_ads_and_popups(soup)
            
        # Moderate filters - also remove navigation
        if self.filter_level in ['moderate', 'aggressive']:
            self._remove_navigation_elements(soup)
            
        # Aggressive filters - remove all identified noise
        if self.filter_level == 'aggressive':
            self._remove_metadata_elements(soup)
            self._remove_social_elements(soup)
            self._clean_attributes(soup)
            
        return soup
    
    def _remove_scripts_and_styles(self, soup):
        """Remove script and style tags"""
        for tag in soup.find_all(['script', 'style', 'noscript']):
            self.removed_elements.append(f"script/style: {tag.name}")
            tag.decompose()
    
    def _remove_hidden_elements(self, soup):
        """Remove visually hidden elements with precise class matching

        Phase 2 Fix: Changed from substring matching to exact word matching.
        Previously matched any class containing "hidden" (e.g., "mx-auto-hidden"),
        now only matches complete class names like "hidden", "visually-hidden", etc.
        """
        # Semantic HTML5 tags white-list: NEVER delete these
        semantic_tags = {'body', 'html', 'main', 'article', 'section',
                        'nav', 'header', 'footer', 'aside'}

        # Elements with display:none or visibility:hidden
        for element in soup.find_all(style=lambda x: x and ('display:none' in x.replace(' ', '') or 'visibility:hidden' in x.replace(' ', ''))):
            # Protect semantic tags
            if element.name in semantic_tags:
                continue
            self.removed_elements.append(f"hidden: {element.name}")
            element.decompose()

        # Common hidden classes - Phase 2 Fix: exact class name matching only
        # Only match standalone "hidden" class, not Tailwind utility classes like "overflow-hidden"
        hidden_classes = [
            'hidden',           # Plain hidden class
            'sr-only',          # Screen reader only
            'screen-reader-only',
            'visually-hidden',  # Visually hidden
            'invisible',        # Invisible class
            'hide',             # Alternative hidden class
            'd-none'            # Bootstrap hidden class
        ]

        # Build list first to avoid modification during iteration
        elements_to_remove = []
        for element in soup.find_all():
            if not element or not hasattr(element, 'get'):
                continue

            elem_classes = element.get('class', [])
            if not elem_classes:
                continue

            # Check if element has any exact hidden class (not as substring)
            has_hidden_class = any(cls in hidden_classes for cls in elem_classes)

            if has_hidden_class:
                # Protect semantic tags
                if element.name in semantic_tags:
                    continue
                elements_to_remove.append(element)

        # Remove collected elements
        for element in elements_to_remove:
            self.removed_elements.append(f"hidden class: {element.name}")
            element.decompose()
    
    def _remove_ads_and_popups(self, soup):
        """Remove advertisement and popup elements with precise selectors

        Phase 2 Fix: Replaced broad selectors like '[class*="ad"]' which incorrectly
        matched semantic classes like "antialiased" (used by Tailwind CSS), causing
        entire body tags to be removed on 30-50% of modern websites.

        Now using precise selectors that match exact ad patterns while protecting
        semantic HTML5 tags (body, main, article, etc.).
        """
        # Precise ad selectors - Phase 2 Fix
        # Only match explicit ad-related patterns, not substrings in unrelated classes
        ad_selectors = [
            # ID selectors: precise prefix/suffix matching
            '[id^="ad-"]', '[id^="ad_"]', '[id$="-ad"]', '[id$="_ad"]',
            '[id="ad"]', '[id="ads"]', '[id="advertisement"]',

            # Class selectors: complete class names only
            '.ad', '.ads', '.ad-container', '.ad-wrapper',
            '.advertisement', '.adsbygoogle', '.ad-slot', '.ad-banner',
            '.ad-unit', '.ad-content', '.ad-box', '.ad-space',

            # Common ad networks
            '.google-ad', '.amazon-ad', '.facebook-ad',

            # Explicit banner and popup patterns (must contain both keywords)
            '[id*="banner"][id*="ad"]',
            '[class*="popup"][class*="modal"]',

            # Promotional and sponsored content
            '.promo', '.promo-banner', '.sponsored', '.sponsored-content'
        ]

        # Semantic HTML5 tags white-list: NEVER delete these
        semantic_tags = {'body', 'html', 'main', 'article', 'section',
                        'nav', 'header', 'footer', 'aside'}

        for selector in ad_selectors:
            try:
                for element in soup.select(selector):
                    # CRITICAL: Protect semantic tags (Phase 2 Fix)
                    if element.name in semantic_tags:
                        continue

                    # Protect main content areas (preserve original logic)
                    elem_classes = ' '.join(element.get('class', [])).lower()
                    elem_id = element.get('id', '').lower()

                    protected_keywords = ['main', 'content', 'article', 'post', 'entry']
                    if any(kw in elem_classes or kw in elem_id
                           for kw in protected_keywords):
                        continue

                    # Safe to remove: not semantic, not main content
                    self.removed_elements.append(f"ad: {element.name}")
                    element.decompose()
            except Exception as e:
                # Silently continue on selector errors
                continue
    
    def _remove_navigation_elements(self, soup):
        """Remove navigation, header, footer elements"""
        nav_tags = ['nav', 'header', 'footer', 'aside']
        for tag in nav_tags:
            for element in soup.find_all(tag):
                self.removed_elements.append(f"navigation: {element.name}")
                element.decompose()
        
        # Common navigation classes
        nav_classes = ['nav', 'navigation', 'menu', 'sidebar', 'breadcrumb', 'pagination']
        for class_name in nav_classes:
            for element in soup.find_all(class_=lambda x: x and any(cls for cls in x if class_name in cls.lower())):
                self.removed_elements.append(f"nav class: {element.name}")
                element.decompose()
    
    def _remove_metadata_elements(self, soup):
        """Remove metadata and tracking elements"""
        # Meta tags not needed for content
        for meta in soup.find_all('meta'):
            if meta.get('name') not in ['description', 'author', 'keywords']:
                meta.decompose()
        
        # Comments
        from bs4 import Comment
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            comment.extract()
            
        # Tracking and analytics
        tracking_classes = ['analytics', 'tracking', 'pixel', 'beacon']
        for class_name in tracking_classes:
            for element in soup.find_all(class_=lambda x: x and any(cls for cls in x if class_name in cls.lower())):
                element.decompose()
    
    def _remove_social_elements(self, soup):
        """Remove social media widgets and share buttons"""
        social_classes = ['social', 'share', 'facebook', 'twitter', 'linkedin', 'pinterest']
        for class_name in social_classes:
            for element in soup.find_all(class_=lambda x: x and any(cls for cls in x if class_name in cls.lower())):
                self.removed_elements.append(f"social: {element.name}")
                element.decompose()
    
    def _clean_attributes(self, soup):
        """Remove unnecessary attributes to clean up HTML"""
        for element in soup.find_all(True):
            # Keep only essential attributes
            essential_attrs = ['href', 'src', 'alt', 'title', 'id']
            attrs_to_remove = [attr for attr in element.attrs.keys() if attr not in essential_attrs]
            for attr in attrs_to_remove:
                del element.attrs[attr]
    
    def get_filter_stats(self):
        """Return filtering statistics"""
        stats = {}
        for item in self.removed_elements:
            category = item.split(':')[0]
            stats[category] = stats.get(category, 0) + 1
        return stats


class NavigationFilter:
    """Specialized filter for navigation and structural elements"""
    
    @staticmethod
    def remove_navigation_noise(soup):
        """Remove common navigation patterns that interfere with content"""
        if not soup:
            return soup
            
        removed_count = 0
        
        # Remove skip links (accessibility)
        for skip_link in soup.find_all('a', href=lambda x: x and x.startswith('#')):
            if 'skip' in skip_link.get_text().lower():
                skip_link.decompose()
                removed_count += 1
        
        # Remove empty navigation containers
        for nav in soup.find_all(['nav', 'div', 'section'], class_=lambda x: x and 'nav' in ' '.join(x).lower()):
            if not nav.get_text().strip() or len(nav.get_text().strip()) < 10:
                nav.decompose()
                removed_count += 1
        
        # Remove breadcrumb trails (often noise in conversion)
        for breadcrumb in soup.find_all(attrs={'aria-label': lambda x: x and 'breadcrumb' in x.lower()}):
            breadcrumb.decompose()
            removed_count += 1
            
        return soup, removed_count


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


def fetch_html_with_retry(url: str, ua: Optional[str] = None, timeout: int = 30, 
                         fetch_mode: str = 'auto') -> tuple[str, FetchMetrics]:
    """
    Fetch HTML with exponential backoff retry logic and optional Selenium fallback.
    
    Phase 2: Implements loop-free session-first fallback strategy:
    1. Try urllib first (existing retry logic)
    2. If urllib fails AND fetch_mode allows Selenium, check Chrome debug session availability
    3. If Chrome session available, use Selenium fallback (preserves login state)
    4. If no Chrome session OR Selenium unavailable, accept empty result (no retry loops)
    
    Args:
        url: Target URL to fetch
        ua: User agent string (optional)
        timeout: Network timeout in seconds
        fetch_mode: 'auto' (urllib->selenium), 'urllib' (urllib only), 'selenium' (selenium only)
    
    Returns:
        tuple[str, FetchMetrics]: (html_content, fetch_metrics)
    """
    metrics = FetchMetrics(primary_method="urllib")
    start_time = time.time()
    last_exception = None
    
    # Phase 2: Handle selenium-only mode first
    if fetch_mode == 'selenium':
        metrics.primary_method = "selenium"
        return _try_selenium_fetch(url, ua, timeout, metrics, start_time)
    
    # Try urllib first (fetch_mode: 'auto' or 'urllib')
    for attempt in range(MAX_RETRIES + 1):  # 0, 1, 2, 3 (4 total attempts)
        metrics.total_attempts = attempt + 1
        
        try:
            if attempt > 0:
                delay = calculate_backoff_delay(attempt - 1)
                logging.info(f"Retry attempt {attempt}/{MAX_RETRIES} for {url} after {delay:.1f}s delay")
                time.sleep(delay)
            
            # Call the original fetch_html function and track metrics
            html, fetch_metrics = fetch_html_original(url, ua, timeout)
            
            # Merge metrics from original fetch
            metrics.fetch_duration = time.time() - start_time
            metrics.ssl_fallback_used = fetch_metrics.ssl_fallback_used
            if fetch_metrics.fallback_method:
                metrics.fallback_method = fetch_metrics.fallback_method
            metrics.final_status = "success"
            
            return html, metrics
            
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
                
                # Phase 2: Immediate Selenium fallback for non-retryable errors (if enabled)
                if fetch_mode == 'auto':
                    return _try_selenium_fallback_after_urllib_failure(url, ua, timeout, metrics, start_time, str(e))
                
                # Store the exception for error reporting
                metrics.fetch_duration = time.time() - start_time
                metrics.final_status = "failed"
                metrics.error_message = str(e)
                raise e
            
            # If this was the last attempt, don't sleep
            if attempt == MAX_RETRIES:
                break
    
    # Phase 2: All urllib retry attempts exhausted - try Selenium fallback if enabled
    if fetch_mode == 'auto':
        return _try_selenium_fallback_after_urllib_failure(url, ua, timeout, metrics, start_time, str(last_exception))
    
    # urllib-only mode or Selenium not enabled - fail normally
    metrics.fetch_duration = time.time() - start_time
    metrics.final_status = "failed"
    metrics.error_message = str(last_exception)
    logging.error(f"All {MAX_RETRIES + 1} attempts failed for {url}, giving up")
    raise last_exception



def _create_empty_metrics_with_guidance() -> FetchMetrics:
    """
    Create empty metrics with helpful guidance message.
    Used when both urllib and Selenium fail or Selenium is unavailable.
    """
    metrics = FetchMetrics(
        primary_method="failed",
        final_status="failed",
        error_message="Both urllib and Selenium failed. To enable Selenium fallback, start Chrome debug session with: ./config/chrome-debug.sh"
    )
    return metrics


def _try_selenium_fetch(url: str, ua: Optional[str], timeout: int, metrics: FetchMetrics, start_time: float) -> tuple[str, FetchMetrics]:
    """
    Try Selenium fetch as primary method (selenium-only mode).

    Phase 2 Enhancement: Raises exceptions on failure instead of returning empty string.
    This ensures proper error propagation and non-zero exit codes.

    Args:
        url: Target URL
        ua: User agent (ignored - Chrome uses its own)
        timeout: Timeout in seconds
        metrics: FetchMetrics object to update
        start_time: Start time for duration calculation

    Returns:
        tuple[str, FetchMetrics]: (html_content, updated_metrics)

    Raises:
        SeleniumNotAvailableError: When Selenium integration is not available
        ChromeConnectionError: When Chrome connection fails
        SeleniumFetchError: When Selenium fetch fails
        SeleniumTimeoutError: When fetch times out
    """
    if not SELENIUM_INTEGRATION_AVAILABLE:
        error_msg = "Selenium integration not available - install requirements-selenium.txt"
        logging.error(f"Selenium mode requested but Selenium integration not available")
        metrics.fetch_duration = time.time() - start_time
        metrics.final_status = "failed"
        metrics.error_message = error_msg
        raise SeleniumNotAvailableError(error_msg)

    try:
        # Load Selenium configuration
        config = SeleniumConfig()

        # Check if actual Selenium package is available before creating fetcher
        from selenium_fetcher import SELENIUM_AVAILABLE
        if not SELENIUM_AVAILABLE:
            error_msg = "Selenium package not installed. Run: pip install selenium PyYAML lxml"
            logging.error(f"Selenium package not installed (selenium library missing)")
            metrics.fetch_duration = time.time() - start_time
            metrics.final_status = "failed"
            metrics.error_message = error_msg
            raise SeleniumNotAvailableError(error_msg)

        # Create and use Selenium fetcher
        with SeleniumFetcher(config._config) as fetcher:
            # Connect to Chrome - enhanced with version mismatch detection and better error messages
            success, message = fetcher.connect_to_chrome()
            if not success:
                metrics.fetch_duration = time.time() - start_time
                metrics.final_status = "failed"
                metrics.error_message = message

                # Log specific error types for better debugging
                if "version mismatch" in message.lower():
                    logging.error(f"Chrome/ChromeDriver version mismatch detected: {message}")
                elif "debug session not available" in message.lower():
                    logging.error(f"Chrome debug session unavailable: {message}")
                else:
                    logging.error(f"Chrome connection failed: {message}")

                # Phase 2: Raise exception instead of returning empty string
                raise ChromeConnectionError(message)

            # Fetch HTML using Selenium
            html_content, selenium_metrics = fetcher.fetch_html_selenium(url, ua, timeout)

            # Update main metrics with Selenium data
            metrics.fetch_duration = time.time() - start_time
            metrics.final_status = "success"
            metrics.selenium_wait_time = selenium_metrics.selenium_wait_time
            metrics.chrome_connected = selenium_metrics.chrome_connected
            metrics.js_detection_used = selenium_metrics.js_detection_used

            logging.info(f"✓ Selenium fetch successful for {url}")
            return html_content, metrics

    except (ChromeConnectionError, SeleniumFetchError, SeleniumTimeoutError, SeleniumNotAvailableError):
        # Re-raise Selenium-specific exceptions to propagate them up
        raise

    except Exception as e:
        logging.error(f"Unexpected error in Selenium fetch for {url}: {e}")
        metrics.fetch_duration = time.time() - start_time
        metrics.final_status = "failed"
        error_msg = f"Unexpected Selenium error: {e}"
        metrics.error_message = error_msg
        raise SeleniumFetchError(error_msg) from e


def _try_selenium_fallback_after_urllib_failure(url: str, ua: Optional[str], timeout: int, 
                                               metrics: FetchMetrics, start_time: float,
                                               urllib_error: str) -> tuple[str, FetchMetrics]:
    """
    Try Selenium fallback after urllib failure. Implements loop-free session-first strategy.
    
    CRITICAL: This function implements the core Phase 2 fallback logic:
    1. Check if Chrome debug session is available (NO new instance creation)
    2. If available, connect and fetch
    3. If not available, accept empty result with guidance (NO retry loops)
    
    Args:
        url: Target URL
        ua: User agent (ignored - Chrome uses its own)
        timeout: Timeout in seconds
        metrics: FetchMetrics object to update
        start_time: Start time for duration calculation
        urllib_error: Error message from urllib failure
        
    Returns:
        tuple[str, FetchMetrics]: (html_content, updated_metrics)
    """
    logging.info(f"urllib failed for {url}, attempting Selenium fallback...")
    
    if not SELENIUM_INTEGRATION_AVAILABLE:
        logging.warning("Selenium fallback requested but integration not available")
        metrics.fetch_duration = time.time() - start_time
        metrics.final_status = "failed"
        metrics.error_message = f"urllib failed: {urllib_error}. Selenium fallback not available - install requirements-selenium.txt"
        return "", metrics
    
    try:
        # Load Selenium configuration
        config = SeleniumConfig()
        
        # Check if actual Selenium package is available
        from selenium_fetcher import SELENIUM_AVAILABLE
        if not SELENIUM_AVAILABLE:
            logging.warning("Selenium package not installed, cannot use as fallback")
            metrics.fetch_duration = time.time() - start_time
            metrics.final_status = "failed"
            metrics.error_message = f"urllib failed: {urllib_error}. Selenium package not installed. Run: pip install selenium PyYAML lxml"
            return "", metrics
        
        # Create Selenium fetcher - graceful degradation approach
        fetcher = SeleniumFetcher(config._config)
        
        # CRITICAL: Check Chrome debug session availability BEFORE attempting connection
        if not fetcher.is_chrome_debug_available():
            logging.info("Chrome debug session not available for fallback, accepting empty result")
            metrics.fetch_duration = time.time() - start_time
            metrics.final_status = "failed"
            metrics.error_message = (
                f"urllib failed: {urllib_error}. "
                f"Chrome debug session not available on port {fetcher.debug_port}. "
                f"Start Chrome debug session with: ./config/chrome-debug.sh"
            )
            return "", metrics
        
        # Chrome debug session available - attempt connection and fetch
        with fetcher:
            success, message = fetcher.connect_to_chrome()
            if not success:
                logging.warning(f"Failed to connect to Chrome debug session: {message}")
                metrics.fetch_duration = time.time() - start_time
                metrics.final_status = "failed"
                metrics.error_message = f"urllib failed: {urllib_error}. Chrome connection failed: {message}"
                return "", metrics
            
            # Attempt Selenium fetch
            html_content, selenium_metrics = fetcher.fetch_html_selenium(url, ua, timeout)
            
            # Update metrics - urllib failed, Selenium succeeded
            metrics.fallback_method = "selenium"
            metrics.fetch_duration = time.time() - start_time
            metrics.final_status = "success"
            metrics.selenium_wait_time = selenium_metrics.selenium_wait_time
            metrics.chrome_connected = selenium_metrics.chrome_connected
            metrics.js_detection_used = selenium_metrics.js_detection_used
            
            logging.info(f"✓ Selenium fallback successful for {url} after urllib failure")
            return html_content, metrics
            
    except (ChromeConnectionError, SeleniumFetchError, SeleniumTimeoutError) as e:
        logging.error(f"Selenium fallback failed for {url}: {e}")
        metrics.fetch_duration = time.time() - start_time
        metrics.final_status = "failed"
        metrics.error_message = f"urllib failed: {urllib_error}. Selenium fallback failed: {e}"
        return "", metrics
        
    except Exception as e:
        logging.error(f"Unexpected error in Selenium fallback for {url}: {e}")
        metrics.fetch_duration = time.time() - start_time
        metrics.final_status = "failed"
        metrics.error_message = f"urllib failed: {urllib_error}. Unexpected Selenium error: {e}"
        return "", metrics


def extract_charset_from_headers(response) -> Optional[str]:
    """
    从HTTP响应头提取charset编码信息
    
    Args:
        response: HTTP响应对象
        
    Returns:
        Optional[str]: 提取到的编码名称，如果未找到则返回None
    """
    content_type = response.headers.get('Content-Type', '')
    if not content_type:
        return None
    
    # 查找charset参数
    charset_match = re.search(r'charset=([^;\s]+)', content_type, re.IGNORECASE)
    if charset_match:
        charset = charset_match.group(1).strip('"\'').lower()
        # 标准化常见的编码名称
        charset_mapping = {
            'gb2312': 'gb2312',
            'gbk': 'gbk', 
            'gb18030': 'gb18030',
            'utf-8': 'utf-8',
            'iso-8859-1': 'iso-8859-1'
        }
        return charset_mapping.get(charset, charset)
    
    return None


def extract_charset_from_html(data: bytes) -> Optional[str]:
    """
    从HTML前8KB检测meta标签中的编码信息
    
    Args:
        data: HTML字节数据
        
    Returns:
        Optional[str]: 提取到的编码名称，如果未找到则返回None
    """
    # 只检查前8KB内容以提升性能
    sample = data[:8192]
    
    try:
        # 尝试用ASCII解码来查找meta标签
        sample_str = sample.decode('ascii', errors='ignore')
    except:
        return None
    
    # 查找各种形式的charset声明
    patterns = [
        r'<meta[^>]+charset\s*=\s*["\']?([^"\'>;\s]+)',  # <meta charset="...">
        r'<meta[^>]+content\s*=\s*["\'][^"\']*charset=([^"\'>;\s]+)',  # <meta http-equiv content="...charset=...">
    ]
    
    for pattern in patterns:
        match = re.search(pattern, sample_str, re.IGNORECASE)
        if match:
            charset = match.group(1).lower()
            # 标准化常见的编码名称
            charset_mapping = {
                'gb2312': 'gb2312',
                'gbk': 'gbk',
                'gb18030': 'gb18030', 
                'utf-8': 'utf-8',
                'iso-8859-1': 'iso-8859-1'
            }
            return charset_mapping.get(charset, charset)
    
    return None


def try_decode_with_fallback(data: bytes, encoding: Optional[str] = None) -> str:
    """
    使用降级链进行解码尝试
    
    Args:
        data: 要解码的字节数据
        encoding: 优先尝试的编码（可选）
        
    Returns:
        str: 解码后的字符串
    """
    # 中文编码降级链：GB2312 → GBK → GB18030 → UTF-8
    fallback_encodings = ['gb2312', 'gbk', 'gb18030', 'utf-8']
    
    # 如果提供了特定编码，优先尝试
    encodings_to_try = []
    if encoding:
        encodings_to_try.append(encoding)
    
    # 添加降级链中未包含的编码
    for enc in fallback_encodings:
        if enc != encoding:
            encodings_to_try.append(enc)
    
    # 最后尝试一些其他常见编码
    encodings_to_try.extend(['iso-8859-1', 'windows-1252'])
    
    for enc in encodings_to_try:
        try:
            decoded = data.decode(enc)
            # 简单检查解码质量：如果包含常见的中文字符且没有明显乱码标志，认为解码成功
            if enc in ['gb2312', 'gbk', 'gb18030']:
                # 对于中文编码，检查是否有合理的中文字符
                if re.search(r'[\u4e00-\u9fff]', decoded):
                    return decoded
            else:
                # 对于其他编码，检查是否有明显的乱码
                if not re.search(r'�', decoded):
                    return decoded
        except (UnicodeDecodeError, LookupError):
            continue
    
    # 如果所有编码都失败，使用UTF-8并忽略错误
    return data.decode('utf-8', errors='ignore')


def smart_decode(data: bytes, response=None) -> str:
    """
    智能解码函数，支持多种编码检测
    优先级：HTTP头 > HTML meta > 降级链
    
    Args:
        data: 要解码的字节数据
        response: HTTP响应对象（可选）
        
    Returns:
        str: 解码后的字符串
    """
    detected_encoding = None
    
    # 1. 从HTTP响应头提取charset
    if response:
        detected_encoding = extract_charset_from_headers(response)
        if detected_encoding:
            logging.debug(f"Detected encoding from headers: {detected_encoding}")
    
    # 2. 如果HTTP头没有找到，从HTML meta标签检测
    if not detected_encoding:
        detected_encoding = extract_charset_from_html(data)
        if detected_encoding:
            logging.debug(f"Detected encoding from HTML meta: {detected_encoding}")
    
    # 3. 使用降级链解码
    try:
        return try_decode_with_fallback(data, detected_encoding)
    except Exception as e:
        logging.warning(f"Smart decode failed, falling back to UTF-8: {e}")
        return data.decode('utf-8', errors='ignore')


def fetch_html_original(url: str, ua: Optional[str] = None, timeout: int = 30) -> tuple[str, FetchMetrics]:
    """
    Fetch HTML using urllib with enhanced SSL error handling.
    
    Returns:
        tuple[str, FetchMetrics]: (html_content, fetch_metrics)
    """
    metrics = FetchMetrics(primary_method="urllib")
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
            # 使用智能解码替代简单的UTF-8解码
            html = smart_decode(data, r)
            metrics.final_status = "success"
            return html, metrics
            
    except Exception as e:
        # If SSL error, provide enhanced error reporting
        if "SSL" in str(e) or "CERTIFICATE" in str(e).upper():
            error_msg = f"SSL verification failed for {url}. Consider using different SSL handling."
            logging.error(error_msg)
            metrics.final_status = "failed"
            metrics.error_message = error_msg
            return "", metrics
            
        logging.error(f"Failed to fetch HTML from {url}: {e}")
        metrics.final_status = "failed"
        metrics.error_message = str(e)
        raise

# Public interface - using direct urllib with retry fallback
fetch_html = fetch_html_with_retry
fetch_html_with_metrics = fetch_html_with_retry


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


def try_render_with_metrics(url: str, ua: Optional[str] = None, timeout_ms: int = 60000) -> tuple[Optional[str], FetchMetrics]:
    """
    Try to render page with Playwright and track metrics.
    
    Returns:
        tuple[Optional[str], FetchMetrics]: (html_content, fetch_metrics)
    """
    metrics = FetchMetrics(primary_method="playwright")
    start_time = time.time()
    
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        metrics.render_duration = time.time() - start_time
        metrics.final_status = "failed"
        metrics.error_message = f"Playwright not available: {e}"
        return None, metrics
        
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
            
        metrics.render_duration = time.time() - start_time
        metrics.final_status = "success"
        return html, metrics
        
    except Exception as e:
        metrics.render_duration = time.time() - start_time
        metrics.final_status = "failed"
        metrics.error_message = str(e)
        return None, metrics


def try_render(url: str, ua: Optional[str] = None, timeout_ms: int = 60000) -> Optional[str]:
    """Legacy interface for try_render"""
    html, _ = try_render_with_metrics(url, ua, timeout_ms)
    return html












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
    title = parsers.extract_meta(html, 'og:title')
    if not title:
        m = re.search(r'<h1[^>]*class=["\'][^"\']*rich_media_title[^"\']*["\'][^>]*>(.*?)</h1>', html, re.I|re.S)
        if m:
            t = re.sub(r'<[^>]+>', '', m.group(1))
            title = ihtml.unescape(t).strip()
    if not title:
        title = '未命名'

    author = parsers.extract_meta(html, 'og:article:author')
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
    date_only, date_time = parsers.parse_date_like(pub)

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


class PageType(Enum):
    """页面类型枚举"""
    ARTICLE = "article"      # 文章页面
    LIST_INDEX = "list"      # 列表索引页面


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
    title = clean_title(parsers.extract_meta(html, 'og:title') or parsers.extract_meta(html, 'twitter:title') or '')
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
    date_only, date_time = parsers.parse_date_like(date_raw)

    desc = parsers.extract_meta(html, 'description').replace('\t','\n\n').strip()
    cover = parsers.extract_meta(html, 'og:image')
    
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
            logging.debug("WF_FORCE_PAGE_DETECTION is set, proceeding with detection")
        else:
            logging.debug("Single-page mode: defaulting to ARTICLE type")
            return PageType.ARTICLE
    else:
        logging.debug("Crawl mode: performing full page type detection")
    
    # URL模式优先判断
    if url:
        # 12371.cn文章页面特征：包含日期路径和ARTI前缀
        if re.search(r'12371\.cn/\d{4}/\d{2}/\d{2}/ARTI\d+\.shtml', url):
            logging.debug(f"12371.cn article pattern detected: {url}")
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
    logging.debug(f"Page type detection - Links: {len(content_links)}, "
                 f"Density: {link_density:.2f}, "
                 f"List containers: {list_container_count}, "
                 f"Pattern consistency: {pattern_consistency:.2f}, "
                 f"Result: {'LIST' if is_list_page else 'ARTICLE'}")
    
    return PageType.LIST_INDEX if is_list_page else PageType.ARTICLE


@dataclass
class ListItem:
    """列表项数据结构"""
    title: str
    url: str
    date: Optional[str] = None
    summary: Optional[str] = None
    index: Optional[int] = None


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
        page_title = parsers.extract_meta(html, 'og:title') or parsers.extract_meta(html, 'twitter:title')
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


def generic_to_markdown(html: str, url: str, filter_level: str = 'safe', is_crawling: bool = False) -> tuple[str, str, dict]:
    # 1. 页面类型检测
    page_type = detect_page_type(html, url, is_crawling)
    
    # 1.5. 内容过滤（如果启用）
    filter_stats = {}
    if filter_level != 'none':
        BeautifulSoup = get_beautifulsoup_parser()
        if BeautifulSoup:
            try:
                logging.info(f"Applying content filtering (level: {filter_level}) to: {url}")
                soup = BeautifulSoup(html, 'html.parser')
                content_filter = ContentFilter(filter_level)
                filtered_soup = content_filter.filter_content(soup)
                if filtered_soup:
                    html = str(filtered_soup)
                    filter_stats = content_filter.get_filter_stats()
                    logging.info(f"Content filtering completed. Removed elements: {filter_stats}")
                else:
                    logging.warning("Content filtering failed - soup is None")
            except Exception as e:
                logging.warning(f"Content filtering failed: {e}")
        else:
            logging.warning("BeautifulSoup not available, skipping content filtering")
    else:
        logging.info("Content filtering disabled (filter_level: none)")
    
    # 2. 如果是列表页面，使用专门的列表处理逻辑
    if page_type == PageType.LIST_INDEX:
        logging.info(f"Detected list page, using list extraction for: {url}")
        page_title, list_items = parsers.extract_list_content(html, url)
        
        # 如果成功提取到列表项，使用列表格式输出
        if list_items and len(list_items) >= 3:  # 至少3个项目才认为是有效列表
            return format_list_page_markdown(page_title, list_items, url)
        else:
            # 如果列表提取失败，fallback到文章模式
            logging.info(f"List extraction failed or insufficient items ({len(list_items) if list_items else 0}), falling back to article mode")
    
    # 3. 文章页面处理（原有逻辑）
    logging.info(f"Processing as article page: {url}")
    
    title = parsers.extract_meta(html, 'og:title') or parsers.extract_meta(html, 'twitter:title')
    if not title:
        m = re.search(r'<title[^>]*>(.*?)</title>', html, re.I|re.S)
        if m:
            title = ihtml.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip()
    title = title or '未命名'
    date_only, date_time = parsers.parse_date_like(parsers.extract_meta(html, 'article:published_time') or parsers.extract_meta(html, 'og:updated_time'))
    
    # Priority 1: Try JSON-LD extraction first
    desc = ''
    json_ld = parsers.extract_json_ld_content(html)
    if json_ld.get('articleBody'):
        desc = json_ld['articleBody']
    elif json_ld.get('description'):
        desc = json_ld['description']
    
    # Priority 1.5: Modern static site generators (Hugo, Jekyll, etc.)
    # PHASE 1: Using optimized parsers.extract_from_modern_selectors with 500-byte threshold
    if not desc:
        desc = parsers.extract_from_modern_selectors(html)
        if desc:
            # PHASE 1: Quality check threshold aligned with parser threshold (500 bytes minimum)
            # This prevents accepting short snippets that passed old 200-byte threshold
            if (len(desc) < 500 or
                any(keyword in desc.lower() for keyword in ['版权所有', 'copyright', '运维保障', 'icp备案'])):
                desc = ''  # 重置，继续后续priority
    
    # Priority 1.8: 12371.cn 共产党员网特定处理
    if not desc and "12371.cn" in html:
        # 针对12371.cn的专用选择器
        word_pattern = r'<div[^>]*class=["\']word["\'][^>]*>(.*?)</div>'
        m = re.search(word_pattern, html, re.I|re.S)
        if m:
            content = m.group(1)
            # 保留段落结构，将<p>转换为换行
            content = re.sub(r'<p[^>]*>', '\n\n', content)
            content = re.sub(r'</p>', '', content)
            # 处理列表项
            content = re.sub(r'<li[^>]*>', '\n• ', content)
            content = re.sub(r'</li>', '', content)
            # 移除其他HTML标签
            content = re.sub(r'<[^>]+>', '', content)
            desc = ihtml.unescape(content).strip()
    
    # Priority 2: Try to extract from multiple <p> tags (for sites like ebchina.com)
    if not desc:
        # Extract all paragraph content with various styles
        p_patterns = [
            r'<p[^>]*class=["\']p["\'][^>]*>(.*?)</p>',  # class="p"
            r'<p[^>]*style=[^>]*text-align[^>]*>(.*?)</p>',  # style with text-align (simplified)
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
    
    # Priority 3: Enhanced government and legal site content extraction
    if not desc:
        # Extended list of content container selectors for government sites
        content_selectors = [
            # 针对12371.cn共产党员网的特定结构 - 直接匹配word class
            r'<div[^>]*class=["\']word["\'][^>]*>(.*?)</div>',
            # 通用政府网站.word容器选择器  
            r'<div[^>]+class=["\'][^"\']*word[^"\']*["\'][^>]*>(.*?)</div>',
            # 通用政府网站.con容器选择器
            r'<div[^>]+class=["\'][^"\']*con[^"\']*["\'][^>]*>(.*?)</div>',
            # 现有北京政府网站选择器
            r'<div[^>]+class=["\']view[^>]*>(.*?)</div>',
            r'<div[^>]+class=["\']TRS_UEDITOR[^>]*>(.*?)</div>',
            # 司法部等政府网站常用选择器
            r'<div[^>]+class=["\'][^"\']*content-text[^"\']*["\'][^>]*>(.*?)</div>',
            r'<div[^>]+class=["\'][^"\']*text-content[^"\']*["\'][^>]*>(.*?)</div>',
            r'<div[^>]+class=["\'][^"\']*law-content[^"\']*["\'][^>]*>(.*?)</div>',
            r'<div[^>]+class=["\'][^"\']*regulation-text[^"\']*["\'][^>]*>(.*?)</div>',
            r'<div[^>]+class=["\'][^"\']*article-content[^"\']*["\'][^>]*>(.*?)</div>',
            # 通用内容容器（包含content关键字的class或id）
            r'<div[^>]+class=["\'][^"\']*content[^"\']*["\'][^>]*>(.*?)</div>',
            r'<div[^>]+id=["\'][^"\']*content[^"\']*["\'][^>]*>(.*?)</div>',
            # main标签内容提取
            r'<main[^>]*>(.*?)</main>',
        ]
        
        for pattern in content_selectors:
            m = re.search(pattern, html, re.I|re.S)
            if m:
                # 提取内容并清理HTML标签
                content = m.group(1)
                # 保留段落结构，将<p>转换为换行
                content = re.sub(r'<p[^>]*>', '\n\n', content)
                content = re.sub(r'</p>', '', content)
                # 处理列表项
                content = re.sub(r'<li[^>]*>', '\n• ', content)
                content = re.sub(r'</li>', '', content)
                # 移除其他HTML标签
                content = re.sub(r'<[^>]+>', '', content)
                desc = ihtml.unescape(content).strip()
                # 检查内容质量：如果提取的内容足够长，则使用
                if desc and len(desc) > 100:  # 降低质量阈值以适应政府网站
                    break
                else:
                    desc = ''  # 重置，继续尝试下一个选择器
    
    # Priority 4: Enhanced generic paragraph extraction with lower thresholds
    if not desc:
        # Extract all generic paragraphs with relaxed criteria for government sites
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
                # 降低段落长度阈值，从20降到10字符，以适应法规条文的简短段落
                if text and len(text) > 10 and not text.startswith('var ') and not text.startswith('function'):
                    # 过滤掉明显的导航、版权等无关内容
                    if not any(keyword in text.lower() for keyword in ['copyright', '版权', '备案', 'icp', '运维保障']):
                        paragraphs.append(text)
            # 降低段落数量阈值，从3降到2，以增加政府网站内容提取成功率
            if len(paragraphs) >= 2:  # 如果找到2个或更多段落就使用
                desc = '\n\n'.join(paragraphs)
        
        # 备用策略：如果段落提取失败且内容太少，尝试提取所有非脚本文本
        if not desc or len(desc) < 500:
            # 尝试提取页面主体文本作为最后的备用方案
            body_content = re.search(r'<body[^>]*>(.*?)</body>', html, re.I|re.S)
            if body_content:
                # 移除脚本和样式
                content = re.sub(r'<script[^>]*>.*?</script>', '', body_content.group(1), flags=re.I|re.S)
                content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.I|re.S)
                # 提取所有文本内容
                text_parts = re.findall(r'>([^<]+)<', content)
                meaningful_parts = []
                for part in text_parts:
                    part = ihtml.unescape(part).strip()
                    if (part and len(part) > 10 and 
                        not any(keyword in part.lower() for keyword in ['javascript', 'copyright', '版权', '备案', 'icp', '运维保障'])):
                        meaningful_parts.append(part)
                
                if meaningful_parts and len('\n'.join(meaningful_parts)) > len(desc or ''):
                    desc = '\n\n'.join(meaningful_parts)
    
    # Priority 5: Fallback to meta description (existing code)
    if not desc:
        desc = parsers.extract_meta(html, 'description').strip()
    
    # Update date if JSON-LD has it and no meta date was found
    original_meta_date = parsers.extract_meta(html, 'article:published_time') or parsers.extract_meta(html, 'og:updated_time')
    if json_ld.get('datePublished') and not original_meta_date:
        date_only, date_time = parsers.parse_date_like(json_ld['datePublished'])
    
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
        'publish_time': json_ld.get('datePublished') or parsers.extract_meta(html, 'article:published_time') or parsers.extract_meta(html, 'og:updated_time'),
        'author': json_ld.get('author', ''),
        'filter_level': filter_level,
        'filter_stats': filter_stats
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
            current_html, _ = fetch_html(next_url, ua=ua, timeout=30)  # Fix: properly unpack tuple return value
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

def extract_internal_links(html: str, base_url: str, enable_doc_filter: bool = False) -> dict:
    """Extract all internal links from HTML content with smart subdirectory resolution.
    Returns dict mapping normalized URLs to original URLs for case-preserving fetching.
    Enhanced to support both quoted and unquoted href attributes.
    
    Args:
        html: HTML content to extract links from
        base_url: Base URL for resolving relative links
        enable_doc_filter: If True, apply is_documentation_url filter during extraction
    """
    links = {}  # normalized_url -> original_url
    base_parts = urllib.parse.urlparse(base_url)
    
    # Support multiple href patterns for modern web compatibility
    href_patterns = [
        r'href\s*=\s*["\']([^"\']+)["\']',     # Quoted: href="..." or href='...' (优先)
        r'href\s*=\s*([^"\'\s>][^\s>]*)',      # Unquoted: href=value (排除引号开头，避免重叠)
    ]
    
    processed_hrefs = set()  # Avoid duplicate processing
    
    for pattern in href_patterns:
        for match in re.finditer(pattern, html, re.I):
            href = match.group(1)
            
            # Skip if already processed (to avoid duplicates from multiple patterns)
            if href in processed_hrefs:
                continue
            processed_hrefs.add(href)
            
            # Skip empty hrefs or anchors, javascript, mailto
            if not href or href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                continue
                
            # Convert to absolute URL using smart context resolution
            full_url = resolve_url_with_context(base_url, href)
            url_parts = urllib.parse.urlparse(full_url)
            
            # Check if same domain and should crawl
            if url_parts.netloc == base_parts.netloc and should_crawl_url(full_url):
                # Apply documentation URL filter during extraction if enabled (Stage 1.1 optimization)
                if enable_doc_filter and not is_documentation_url(full_url):
                    continue
                
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

def detect_government_site(url: str, html: str) -> bool:
    """
    Detect if a website is a government site based on domain patterns and HTML content.
    
    Args:
        url: The website URL to check
        html: HTML content of the homepage for additional verification
        
    Returns:
        bool: True if detected as government site, False otherwise
    """
    import urllib.parse
    
    # Parse the URL
    parsed_url = urllib.parse.urlparse(url)
    domain = parsed_url.netloc.lower()
    
    # Stage 2.1: Government domain pattern detection
    gov_domain_patterns = [
        r'\.gov\.cn$',    # Chinese government sites
        r'\.gov$',        # US government sites  
        r'\.org\.cn$',    # Chinese organizations (many government-related)
        r'\.mil\.cn$',    # Chinese military sites
        r'\.edu\.cn$',    # Chinese educational sites (government-funded)
        r'\.ac\.cn$',     # Chinese academic sites
        r'\.gov\.uk$',    # UK government sites
        r'\.europa\.eu$', # EU government sites
    ]
    
    # Check domain patterns
    for pattern in gov_domain_patterns:
        if re.search(pattern, domain):
            logging.info(f"Government site detected by domain pattern: {domain}")
            return True
    
    # Stage 2.1: HTML content-based detection
    if html:
        gov_content_indicators = [
            r'政府|Government|官方|Official',  # Government keywords
            r'政务|公告|通知|Public Notice',   # Government activity keywords
            r'党委|市委|区委|县委',              # Party committee keywords (Chinese)
            r'人民政府|People.*Government',    # People's government
            r'国务院|State Council',          # State council
            r'中华人民共和国|People.*Republic.*China', # PRC
            r'Gov\.cn|政府门户|Government Portal', # Government portal indicators
        ]
        
        # Check for government content indicators
        for pattern in gov_content_indicators:
            if re.search(pattern, html, re.I):
                logging.info(f"Government site detected by content pattern: {pattern}")
                return True
    
    return False

def extract_site_categories(url: str, html: str) -> list:
    """
    Extract website navigation structure and categories.
    
    Args:
        url: Base URL of the website
        html: HTML content of the homepage
        
    Returns:
        List[dict]: List of category dictionaries with 'name', 'url', 'priority' keys
    """
    import urllib.parse
    from bs4 import BeautifulSoup
    
    if not html:
        return []
    
    categories = []
    base_parts = urllib.parse.urlparse(url)
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Stage 2.2: Navigation menu detection patterns
        nav_selectors = [
            'nav ul li a',           # Standard navigation
            '.navbar ul li a',       # Bootstrap navbar
            '.nav ul li a',          # Navigation class
            '.menu ul li a',         # Menu class
            '.main-nav ul li a',     # Main navigation
            '.navigation ul li a',   # Navigation class variation
            'ul.nav li a',           # Direct nav class on ul
            'ul.menu li a',          # Direct menu class on ul
            '.header nav a',         # Header navigation
            '.top-nav a',            # Top navigation
        ]
        
        # Collect all potential navigation links
        nav_links = set()
        
        for selector in nav_selectors:
            try:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    text = link.get_text(strip=True)
                    
                    if href and text and len(text) > 1:
                        # Convert to absolute URL
                        full_url = urllib.parse.urljoin(url, href)
                        url_parts = urllib.parse.urlparse(full_url)
                        
                        # Only include same-domain links
                        if url_parts.netloc == base_parts.netloc:
                            nav_links.add((text, full_url))
                            
            except Exception as e:
                logging.debug(f"Failed to parse selector {selector}: {e}")
                continue
        
        # Stage 2.2: Government-specific category prioritization
        gov_priority_keywords = [
            ('政务公开', '政务', '公开', 'Public Affairs'),  # Public affairs - High priority
            ('通知公告', '公告', '通知', 'Notice'),          # Notices - High priority  
            ('新闻', '资讯', '动态', 'News'),               # News - Medium priority
            ('服务', '办事', '业务', 'Service'),            # Services - High priority
            ('政策', '法规', '规章', 'Policy'),             # Policies - High priority
            ('领导', '组织', '机构', 'Leadership'),         # Leadership - Medium priority
        ]
        
        # Convert nav_links to categories with priority scoring
        for text, link_url in nav_links:
            priority = 1  # Default priority
            
            # Check for government priority keywords
            for keywords in gov_priority_keywords:
                for keyword in keywords:
                    if keyword.lower() in text.lower():
                        if '公开' in keywords or '公告' in keywords or 'Service' in keywords or 'Policy' in keywords:
                            priority = 3  # High priority
                        elif '新闻' in keywords or 'News' in keywords or 'Leadership' in keywords:
                            priority = 2  # Medium priority
                        break
                if priority > 1:
                    break
            
            categories.append({
                'name': text,
                'url': link_url,
                'priority': priority
            })
        
        # Sort by priority (high to low) then by name
        categories.sort(key=lambda x: (-x['priority'], x['name']))
        
        logging.info(f"Extracted {len(categories)} site categories")
        if categories:
            high_priority = [c for c in categories if c['priority'] == 3]
            logging.info(f"High priority categories: {len(high_priority)}")
            
    except Exception as e:
        logging.warning(f"Failed to extract site categories: {e}")
        
    return categories

def crawl_site_by_categories(start_url: str, ua: str, categories: list, **kwargs):
    """
    Crawl site with category-first strategy for government sites.
    
    Args:
        start_url: Starting URL
        ua: User agent string
        categories: List of category dicts from extract_site_categories()
        **kwargs: Additional arguments passed to crawl_site()
        
    Yields:
        Iterator of (category_info, pages) tuples for progressive results
    """
    # Extract parameters for individual category crawls
    max_depth = kwargs.get('max_depth', 3)
    max_pages_per_category = min(kwargs.get('max_pages', 1000) // max(len(categories), 1), 100)
    delay = kwargs.get('delay', 0.5)
    enable_optimizations = kwargs.get('enable_optimizations', True)
    
    logging.info(f"Starting category-first crawl with {len(categories)} categories")
    logging.info(f"Max {max_pages_per_category} pages per category")
    
    all_pages = []
    total_crawled = 0
    
    # Sort categories by priority for crawling order
    sorted_categories = sorted(categories, key=lambda x: (-x['priority'], x['name']))
    
    for i, category in enumerate(sorted_categories):
        if total_crawled >= kwargs.get('max_pages', 1000):
            break
            
        category_name = category['name']
        category_url = category['url']
        category_priority = category['priority']
        
        logging.info(f"[{i+1}/{len(sorted_categories)}] Crawling category '{category_name}' (priority {category_priority})")
        
        try:
            # Crawl this category with limited scope
            category_pages = crawl_site(
                category_url,
                ua,
                max_depth=min(max_depth, 2),  # Limit depth per category
                max_pages=max_pages_per_category,
                delay=delay,
                enable_optimizations=enable_optimizations,
                crawl_strategy='default'  # Use default strategy for individual categories
            )
            
            logging.info(f"Category '{category_name}' yielded {len(category_pages)} pages")
            
            # Yield progressive results
            category_info = {
                'name': category_name,
                'url': category_url,
                'priority': category_priority,
                'pages_count': len(category_pages)
            }
            
            yield (category_info, category_pages)
            
            all_pages.extend(category_pages)
            total_crawled += len(category_pages)
            
        except Exception as e:
            logging.warning(f"Failed to crawl category '{category_name}': {e}")
            continue
    
    logging.info(f"Category-first crawl completed: {total_crawled} total pages from {len(sorted_categories)} categories")

def crawl_site(start_url: str, ua: str, max_depth: int = 10, 
               max_pages: int = 1000, delay: float = 0.5,
               # Stage 1 optimization parameters
               enable_optimizations: bool = True,
               crawl_strategy: str = 'default',
               # Stage 1.3 memory optimization
               memory_efficient: bool = False,
               page_callback = None) -> list:
    """
    Crawl entire site using BFS algorithm.
    Returns list of (url, html, depth) tuples.
    
    Args:
        start_url: Starting URL for crawling
        ua: User agent string for requests
        max_depth: Maximum crawling depth
        max_pages: Maximum number of pages to crawl
        delay: Delay between requests in seconds
        enable_optimizations: Enable Stage 1 optimizations (link pre-filtering, batch processing)
        crawl_strategy: Crawling strategy ('default', 'category_first' for Stage 2)
        memory_efficient: Enable memory optimization - pages processed in batches
        page_callback: Optional callback function for streaming page processing
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
    
    # Stage 1.3: Memory-efficient page storage
    if memory_efficient:
        pages = []  # Store only basic info for memory-efficient mode
        page_batch = []  # Temporary batch for processing
        batch_size = 50  # Process in batches of 50 pages
    else:
        pages = []  # Traditional full storage
    
    logging.info(f"Starting site crawl from {start_url}")
    logging.info(f"Settings: max_depth={max_depth}, max_pages={max_pages}, delay={delay}s, strategy={crawl_strategy}")
    
    # Stage 2.3: Check for government site and category-first strategy
    if crawl_strategy == 'category_first':
        # First, fetch the homepage to detect government site and extract categories
        try:
            homepage_html, _ = fetch_html(start_url, ua=ua, timeout=30)  # Fix: properly unpack tuple return value
            
            # Detect if it's a government site
            is_government = detect_government_site(start_url, homepage_html)
            
            if is_government:
                # Extract site categories
                categories = extract_site_categories(start_url, homepage_html)
                
                if categories:
                    logging.info(f"Government site detected with {len(categories)} categories. Using category-first strategy.")
                    
                    # Use category-first crawling
                    all_category_pages = []
                    crawl_params = {
                        'max_depth': max_depth,
                        'max_pages': max_pages,
                        'delay': delay,
                        'enable_optimizations': enable_optimizations
                    }
                    
                    for category_info, category_pages in crawl_site_by_categories(start_url, ua, categories, **crawl_params):
                        all_category_pages.extend(category_pages)
                        
                        # Check if we've reached the page limit
                        if len(all_category_pages) >= max_pages:
                            break
                    
                    # Update final statistics (simplified for category-first mode)
                    logging.info(f"Category-first crawl summary: {len(all_category_pages)} pages total")
                    return all_category_pages[:max_pages]  # Ensure we don't exceed limit
                else:
                    logging.info("Government site detected but no categories found. Falling back to default strategy.")
            else:
                logging.info("Non-government site detected. Falling back to default strategy.")
                
        except Exception as e:
            logging.warning(f"Category-first strategy failed: {e}. Falling back to default strategy.")
    
    # Default BFS crawling strategy (original logic)
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
            html, _ = fetch_html(current_url, ua=ua, timeout=30)  # Fix: properly unpack tuple return value
            visited_normalized.add(current_normalized)
            url_mapping[current_normalized] = current_url
            
            # Stage 1.3: Memory-efficient page handling
            if memory_efficient:
                # Add to batch for processing
                page_batch.append((current_url, html, depth))
                
                # Process batch when full
                if len(page_batch) >= batch_size:
                    if page_callback:
                        page_callback(page_batch.copy())  # Send copy to callback
                    # Keep only metadata for final result (no HTML content)
                    for url, _, d in page_batch:
                        pages.append((url, '', d))
                    page_batch.clear()
            else:
                # Traditional full storage
                pages.append((current_url, html, depth))
            
            # Update statistics
            stats['pages_success'] += 1
            stats['total_size'] += len(html.encode('utf-8'))
            
            # Extract and queue new links (only if not at max depth)
            if depth < max_depth:
                # Stage 1.1 optimization: Enable documentation filter during link extraction
                enable_doc_filter = enable_optimizations and crawl_strategy == 'default'
                link_mapping = extract_internal_links(html, current_url, enable_doc_filter=enable_doc_filter)
                
                # Stage 1.2 optimization: Batch process new links
                if enable_optimizations:
                    # Batch filtering and deduplication
                    new_normalized_links = set(link_mapping.keys()) - visited_normalized
                    
                    if enable_doc_filter:
                        # All links already pre-filtered for documentation
                        doc_links = [(norm, orig) for norm, orig in link_mapping.items() 
                                   if norm in new_normalized_links]
                        logging.info(f"Found {len(doc_links)} new documentation links (pre-filtered)")
                    else:
                        # Batch apply documentation filter
                        doc_links = [(norm, orig) for norm, orig in link_mapping.items() 
                                   if norm in new_normalized_links and is_documentation_url(orig)]
                        logging.info(f"Found {len(doc_links)} new documentation links")
                    
                    # Batch queue operations - sort and limit in one operation
                    links_to_queue = sorted(doc_links)[:50]  # Limit per-page discoveries
                    for normalized_link, original_link in links_to_queue:
                        queue.append((original_link, depth + 1))
                        
                else:
                    # Original non-optimized path for compatibility
                    new_normalized_links = set(link_mapping.keys()) - visited_normalized
                    doc_links = [(norm, orig) for norm, orig in link_mapping.items() 
                               if norm in new_normalized_links and is_documentation_url(orig)]
                    logging.info(f"Found {len(doc_links)} new documentation links")
                    
                    for normalized_link, original_link in sorted(doc_links)[:50]:
                        queue.append((original_link, depth + 1))
            
        except Exception as e:
            logging.warning(f"Failed to crawl {current_url}: {e}")
            stats['pages_failed'] += 1
            stats['failed_urls'].append((current_url, str(e)))
            continue
    
    # Stage 1.3: Process any remaining batch
    if memory_efficient and 'page_batch' in locals() and page_batch:
        if page_callback:
            page_callback(page_batch)
        # Add remaining pages as metadata only
        pages.extend([(url, '', d) for url, _, d in page_batch])
        page_batch.clear()
    
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
                # Pass is_crawling=True only to generic_to_markdown which supports it
                if parser_func == generic_to_markdown:
                    date, content, metadata = parser_func(html, url, 'safe', is_crawling=True)
                else:
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


def determine_output_format(args, url, content_type=None):
    """
    Determine the appropriate output format based on CLI args and context.
    
    Args:
        args: Parsed command line arguments containing format preference
        url: Target URL being processed  
        content_type: Optional content type hint
        
    Returns:
        tuple: (should_output_markdown: bool, should_output_html: bool)
        
    Examples:
        args.format='markdown' -> (True, False)
        args.format='html' -> (False, True) 
        args.format='both' -> (True, True)
    """
    # Validate input format preference
    format_choice = getattr(args, 'format', 'markdown')
    
    # Log format decision for debugging
    logging.debug(f"Output format requested: {format_choice} for URL: {url}")
    
    # Determine output requirements based on format choice
    if format_choice == 'html':
        return (False, True)
    elif format_choice == 'both':
        return (True, True) 
    else:  # 'markdown' or any other value defaults to markdown
        if format_choice != 'markdown':
            logging.warning(f"Unknown format '{format_choice}', defaulting to markdown")
        return (True, False)


def write_html_file(content, output_path, url, title=None):
    """
    Write HTML content to file with proper formatting and metadata.
    
    Args:
        content (str): Raw HTML content to write
        output_path (str): Full path where HTML file should be saved
        url (str): Source URL for metadata/comments  
        title (str, optional): Page title for HTML head
        
    Returns:
        str: Absolute path of written file
        
    Raises:
        IOError: If file writing fails
        ValueError: If content or path is invalid
    """
    import os
    from datetime import datetime
    
    # Validate inputs
    if not content:
        raise ValueError("Content cannot be empty")
    if not output_path:
        raise ValueError("Output path cannot be empty")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Generate HTML document if content is just a fragment
    if not content.strip().startswith('<!DOCTYPE') and not content.strip().startswith('<html'):
        # Create full HTML document
        page_title = title or "Web Content"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.6; margin: 2rem; }}
        .metadata {{ color: #666; font-size: 0.9em; border-bottom: 1px solid #eee; padding-bottom: 1rem; margin-bottom: 2rem; }}
        .content {{ max-width: 800px; }}
    </style>
</head>
<body>
    <div class="metadata">
        <p><strong>Source:</strong> <a href="{url}">{url}</a></p>
        <p><strong>Generated:</strong> {timestamp}</p>
        <p><strong>Tool:</strong> WebFetcher</p>
    </div>
    <div class="content">
        {content}
    </div>
</body>
</html>"""
        content = full_html
    
    # Write file with UTF-8 encoding
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logging.debug(f"HTML file written: {output_path}")
        return os.path.abspath(output_path)
        
    except IOError as e:
        logging.error(f"Failed to write HTML file {output_path}: {e}")
        raise


def get_html_output_path(args, url, base_filename=None):
    """
    Generate appropriate HTML output file path based on configuration.
    
    Args:
        args: Parsed command line arguments
        url (str): Source URL for filename generation
        base_filename (str, optional): Base name override
        
    Returns:
        str: Absolute path for HTML output file
        
    Examples:
        URL: https://example.com/article -> example.com_article.html
        With base_filename: custom -> custom.html
    """
    import os
    from urllib.parse import urlparse
    
    # Determine output directory
    if hasattr(args, 'outdir') and args.outdir:
        output_dir = args.outdir
    else:
        output_dir = "output"
    
    # Generate filename
    if base_filename:
        # Use provided base filename
        filename = f"{base_filename}.html"
    else:
        # Generate from URL using existing patterns
        try:
            parsed = urlparse(url)
            # Create safe filename from URL
            domain = parsed.netloc.replace('www.', '').replace(':', '_')
            path_part = parsed.path.strip('/').replace('/', '_').replace('.', '_')
            
            if path_part:
                filename = f"{domain}_{path_part}.html"
            else:
                filename = f"{domain}.html"
                
            # Clean up filename (remove unsafe characters)
            filename = "".join(c for c in filename if c.isalnum() or c in '._-')
            
        except Exception:
            # Fallback to simple timestamp-based name
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"webpage_{timestamp}.html"
    
    # Create full path
    full_path = os.path.join(output_dir, filename)
    
    # Handle duplicate files by adding counter
    counter = 1
    original_path = full_path
    while os.path.exists(full_path):
        name, ext = os.path.splitext(original_path)
        full_path = f"{name}_{counter}{ext}"
        counter += 1
    
    return os.path.abspath(full_path)


def format_selenium_error(exception):
    """
    格式化Selenium相关错误为用户友好的输出

    Args:
        exception: Selenium相关的异常对象

    Returns:
        str: 格式化的错误消息字符串
    """
    # Detect system language from LANG environment variable
    lang = os.environ.get('LANG', '').lower()
    is_chinese = 'zh' in lang or 'cn' in lang

    # Define bilingual labels
    if is_chinese:
        labels = {
            'error': '错误',
            'problem': '问题',
            'solution': '解决方案',
            'command': '命令'
        }
    else:
        labels = {
            'error': 'ERROR',
            'problem': 'PROBLEM',
            'solution': 'SOLUTION',
            'command': 'COMMAND'
        }

    exception_type = type(exception).__name__
    error_message = str(exception)

    # Split error message into sections
    problem = ""
    solution = ""
    command = ""

    # Parse the error message to extract PROBLEM, SOLUTION, and COMMAND
    lines = error_message.split('\n')
    current_section = None

    for line in lines:
        stripped = line.strip()

        # Identify sections
        if 'SOLUTION:' in line:
            current_section = 'solution'
            # Extract text after SOLUTION: on same line
            solution_text = line.split('SOLUTION:', 1)[-1].strip()
            if solution_text:
                solution += solution_text + '\n'
            continue

        # Extract commands (prioritize shell scripts, then chrome commands, then pip install)
        if './config/chrome-debug.sh' in line:
            # Extract shell script command (highest priority)
            if ':' in line:
                cmd_part = line.split(':', 1)[-1].strip()
            else:
                cmd_part = line.strip()
            if cmd_part:
                command = cmd_part  # Override any previous command
        elif ('--remote-debugging-port' in line or 'pip install' in line) and not command:
            # Extract chrome or pip command (lower priority)
            if ':' in line:
                cmd_part = line.split(':', 1)[-1].strip()
            else:
                cmd_part = line.strip()
            if cmd_part:
                command = cmd_part

        # Accumulate text based on current section
        if current_section == 'solution':
            if stripped and not stripped.startswith('SOLUTION:'):
                solution += stripped + '\n'
        elif not current_section:
            # Before SOLUTION section, this is the problem
            if stripped and 'SOLUTION:' not in line:
                problem += stripped + '\n'

    # Clean up sections
    problem = problem.strip()
    solution = solution.strip()
    command = command.strip()

    # If we couldn't parse sections, fall back to simple format
    if not problem:
        problem = error_message.split('SOLUTION:')[0].strip()

    if not solution and 'SOLUTION:' in error_message:
        solution = error_message.split('SOLUTION:', 1)[-1].strip()

    # Build formatted output
    output = []
    output.append("=" * 40)
    output.append(f"{labels['error']}: {exception_type}")
    output.append("=" * 40)
    output.append("")
    output.append(f"{labels['problem']}:")
    output.append(problem)
    output.append("")

    if solution:
        output.append(f"{labels['solution']}:")
        output.append(solution)
        output.append("")

    if command:
        output.append(f"{labels['command']}:")
        output.append(command)

    output.append("=" * 40)

    return '\n'.join(output)


def generate_failure_markdown(url: str, metrics: FetchMetrics, exception=None) -> str:
    """
    生成失败报告的Markdown内容

    Args:
        url: 目标URL
        metrics: FetchMetrics对象，包含失败详情
        exception: 可选的异常对象

    Returns:
        str: 格式化的失败Markdown内容
    """
    # Detect system language from LANG environment variable
    lang = os.environ.get('LANG', '').lower()
    is_chinese = 'zh' in lang or 'cn' in lang

    # Get current timestamp
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Extract error information
    error_type = type(exception).__name__ if exception else metrics.primary_method or "Unknown"
    error_description = metrics.error_message or str(exception) if exception else "No error details available"

    # Build markdown content
    output = []

    # Title with warning emoji
    if is_chinese:
        output.append("# ⚠️ 网页抓取失败\n")
    else:
        output.append("# ⚠️ Web Fetch Failed\n")

    # URL information
    if is_chinese:
        output.append(f"**目标URL**: {url}\n")
    else:
        output.append(f"**Target URL**: {url}\n")

    # Error summary (blockquote format)
    if is_chinese:
        output.append(f"> **错误类型**: {error_type}")
        output.append(f"> **失败时间**: {current_time}")
        output.append(f"> **错误描述**: {error_description}\n")
    else:
        output.append(f"> **Error Type**: {error_type}")
        output.append(f"> **Failed At**: {current_time}")
        output.append(f"> **Description**: {error_description}\n")

    # Troubleshooting steps
    if is_chinese:
        output.append("## 故障排除步骤\n")

        # Check if Selenium-related error
        if 'selenium' in metrics.primary_method.lower() or (exception and 'Chrome' in error_type):
            output.append("1. **检查Chrome浏览器是否正在运行**")
            output.append("   - 确保Chrome以调试模式启动")
            output.append("   - 运行命令: `./config/chrome-debug.sh` 或")
            output.append("   - 手动启动: `/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_debug_profile`\n")
            output.append("2. **验证网络连接**")
            output.append("   - 检查是否能访问目标网站")
            output.append("   - 尝试在浏览器中手动打开URL\n")
            output.append("3. **检查端口占用**")
            output.append("   - 确认9222端口未被其他程序占用")
            output.append("   - 运行: `lsof -i :9222`\n")
        else:
            output.append("1. **检查网络连接**")
            output.append("   - 验证互联网连接是否正常")
            output.append("   - 尝试访问其他网站\n")
            output.append("2. **验证URL有效性**")
            output.append("   - 确认URL格式正确")
            output.append("   - 检查目标网站是否可访问\n")
            output.append("3. **尝试其他抓取方法**")
            output.append("   - 使用 `--fetch-mode selenium` 尝试JavaScript渲染")
            output.append("   - 或使用 `--fetch-mode urllib` 尝试简单抓取\n")

        output.append("4. **查看详细日志**")
        output.append("   - 使用 `--verbose` 参数获取更多信息\n")
    else:
        output.append("## Troubleshooting Steps\n")

        # Check if Selenium-related error
        if 'selenium' in metrics.primary_method.lower() or (exception and 'Chrome' in error_type):
            output.append("1. **Check if Chrome browser is running**")
            output.append("   - Ensure Chrome is started in debug mode")
            output.append("   - Run command: `./config/chrome-debug.sh` or")
            output.append("   - Manual start: `/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_debug_profile`\n")
            output.append("2. **Verify network connection**")
            output.append("   - Check if you can access the target website")
            output.append("   - Try opening the URL manually in browser\n")
            output.append("3. **Check port availability**")
            output.append("   - Ensure port 9222 is not occupied by another program")
            output.append("   - Run: `lsof -i :9222`\n")
        else:
            output.append("1. **Check network connection**")
            output.append("   - Verify internet connection is working")
            output.append("   - Try accessing other websites\n")
            output.append("2. **Verify URL validity**")
            output.append("   - Ensure URL format is correct")
            output.append("   - Check if target website is accessible\n")
            output.append("3. **Try alternative fetch methods**")
            output.append("   - Use `--fetch-mode selenium` for JavaScript rendering")
            output.append("   - Or use `--fetch-mode urllib` for simple fetch\n")

        output.append("4. **View detailed logs**")
        output.append("   - Use `--verbose` flag for more information\n")

    # Technical details (collapsible)
    if is_chinese:
        output.append("<details>")
        output.append("<summary>技术细节 / Technical Details</summary>\n")
    else:
        output.append("<details>")
        output.append("<summary>Technical Details</summary>\n")

    output.append(f"- **Fetch Method**: {metrics.primary_method or 'N/A'}")
    if metrics.fallback_method:
        output.append(f"- **Fallback Method**: {metrics.fallback_method}")
    output.append(f"- **Status**: {metrics.final_status}")
    output.append(f"- **Duration**: {metrics.fetch_duration:.2f}s")
    output.append(f"- **Total Attempts**: {metrics.total_attempts}")
    if metrics.error_message:
        output.append(f"- **Error**: {metrics.error_message}")

    output.append("\n</details>")

    return '\n'.join(output)


def get_failure_filename(timestamp: str, url: str) -> str:
    """
    生成失败报告的文件名

    Args:
        timestamp: 时间戳字符串（格式：YYYY-MM-DD-HHMMSS）
        url: 目标URL

    Returns:
        str: 失败文件的基础名称（不含扩展名）
    """
    from urllib.parse import urlparse

    # Extract domain from URL
    parsed = urlparse(url)
    domain = parsed.hostname or 'unknown'

    # Clean domain name using existing sanitize_filename function
    sanitized_domain = sanitize_filename(domain)

    # Return formatted filename (without extension)
    return f"FAILED_{timestamp} - {sanitized_domain}"


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
    ap.add_argument('--filter', choices=['none', 'safe', 'moderate', 'aggressive'], default='safe',
                    help='Content filtering level: none (no filtering), safe (remove scripts/ads), moderate (+ navigation), aggressive (+ metadata) (default: safe)')
    ap.add_argument('--crawl-site', action='store_true',
                    help='Recursively crawl entire site (BFS traversal of all internal links)')
    ap.add_argument('--max-crawl-depth', type=int, default=10,
                    help='Maximum crawl depth for site crawling (default: 10, max: 10)')
    ap.add_argument('--max-pages', type=int, default=1000,
                    help='Maximum pages to crawl (default: 1000, max: 1000)')
    ap.add_argument('--crawl-delay', type=float, default=0.5,
                    help='Delay between crawl requests in seconds (default: 0.5)')
    ap.add_argument('--format', choices=['markdown', 'html', 'both'], default='markdown',
                    help='Output format: markdown (default), html, or both')
    
    # Phase 2: Selenium integration arguments
    ap.add_argument('--fetch-mode', choices=['auto', 'urllib', 'selenium'], default='auto',
                    help='Fetch method: auto (urllib->selenium fallback), urllib (urllib only), selenium (selenium only) (default: auto)')
    ap.add_argument('-s', '--selenium', action='store_true',
                    help='Shortcut for --fetch-mode selenium (force Selenium for JavaScript rendering)')
    ap.add_argument('-u', '--urllib', action='store_true',
                    help='Shortcut for --fetch-mode urllib (force urllib without Selenium fallback)')
    ap.add_argument('--selenium-timeout', type=int, default=30,
                    help='Selenium page load timeout in seconds (default: 30)')
    
    args = ap.parse_args()
    
    # Handle shortcuts for fetch modes
    if args.selenium:
        args.fetch_mode = 'selenium'
    elif args.urllib:
        args.fetch_mode = 'urllib'
    
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
    # Validate and encode URL for proper Unicode handling
    url = validate_and_encode_url(args.url)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    
    logging.info(f"Starting webfetcher for URL: {url}")
    if url != args.url:
        logging.info(f"URL encoded from: {args.url}")

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
            # Always use generic parser for crawling
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
            
            # Determine output formats needed
            output_markdown, output_html = determine_output_format(args, url)
            
            # Write markdown file if requested
            if output_markdown:
                path.write_text(md, encoding='utf-8')
                logging.info(f"Markdown file saved: {path}")
            
            # Write HTML file if requested
            if output_html:
                try:
                    html_path = get_html_output_path(args, url, base)
                    write_html_file(crawled_pages[0][1], html_path, url, title)  # Use first page's HTML
                    logging.info(f"HTML file saved: {html_path}")
                except Exception as e:
                    logging.error(f"Failed to write HTML output: {e}")
            
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
            
            # Print primary output path(s)
            if output_markdown and output_html:
                print(f"{path}\n{html_path}")
            elif output_html:
                print(str(html_path))
            else:
                print(str(path))
            return  # Exit the main function after crawling is complete
            
        else:
            logging.error("No pages crawled successfully")
            sys.exit(1)
    elif args.html:
        # Local HTML file
        html = Path(args.html).read_text(encoding='utf-8', errors='ignore')
        fetch_metrics = FetchMetrics(primary_method="local_file", final_status="success")
        rendered = False
    else:
        html = None
        fetch_metrics = None
        should_render = (args.render == 'always') or (args.render == 'auto' and ('xiaohongshu.com' in host or 'xhslink.com' in original_host or 'dianping.com' in host))
        logging.info(f"Render decision: {'will render' if should_render else 'static fetch only'}")
        
        if should_render:
            logging.info("Attempting headless rendering with Playwright")
            rendered_html, render_metrics = try_render_with_metrics(url, ua=ua, timeout_ms=max(1000, args.render_timeout*1000))
            if rendered_html:
                logging.info("Rendering successful")
                html = rendered_html
                fetch_metrics = render_metrics
                rendered = True
            else:
                logging.info("Rendering failed, falling back to static fetch")
                rendered = False
        else:
            rendered = False
            
        if html is None:
            logging.info("Fetching HTML statically")
            # Phase 2: Use selenium-timeout when selenium mode, otherwise use regular timeout
            fetch_timeout = args.selenium_timeout if args.fetch_mode == 'selenium' else args.timeout

            # Phase 2 Enhancement: Catch Selenium exceptions and exit with non-zero code
            try:
                html, fetch_metrics = fetch_html(url, ua=ua, timeout=fetch_timeout, fetch_mode=args.fetch_mode)
                logging.info("Static fetch completed")

                # Phase 2: Check if fetch failed
                if fetch_metrics and fetch_metrics.final_status == "failed":
                    logging.warning(f"Fetch failed: {fetch_metrics.error_message}")

                    # Generate failure report
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
                    failure_filename = get_failure_filename(timestamp, url)
                    failure_path = outdir / f"{failure_filename}.md"

                    failure_md = generate_failure_markdown(url, fetch_metrics, None)
                    failure_path.write_text(failure_md, encoding='utf-8')
                    logging.info(f"Failure report saved: {failure_path}")
                    print(str(failure_path))
                    sys.exit(1)

            except (ChromeConnectionError, SeleniumNotAvailableError, SeleniumFetchError, SeleniumTimeoutError) as e:
                logging.error(f"Selenium fetch failed: {e}")
                # Phase 3 Step 1: Use structured error formatting
                formatted_error = format_selenium_error(e)
                print(formatted_error, file=sys.stderr)

                # Phase 2: Generate failure report instead of exiting immediately
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
                failure_filename = get_failure_filename(timestamp, url)
                failure_path = outdir / f"{failure_filename}.md"

                # Create minimal FetchMetrics for failure report
                failure_metrics = FetchMetrics(
                    primary_method="selenium",
                    final_status="failed",
                    error_message=str(e)
                )

                failure_md = generate_failure_markdown(url, failure_metrics, e)
                failure_path.write_text(failure_md, encoding='utf-8')
                logging.info(f"Failure report saved: {failure_path}")
                print(str(failure_path))
                sys.exit(1)

            except Exception as e:
                # Phase 2: Catch urllib and other fetch failures
                logging.error(f"Fetch failed: {e}")
                print(f"Error: {e}", file=sys.stderr)

                # Generate failure report
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
                failure_filename = get_failure_filename(timestamp, url)
                failure_path = outdir / f"{failure_filename}.md"

                # Create minimal FetchMetrics for failure report
                failure_metrics = FetchMetrics(
                    primary_method="urllib",
                    final_status="failed",
                    error_message=str(e)
                )

                failure_md = generate_failure_markdown(url, failure_metrics, e)
                failure_path.write_text(failure_md, encoding='utf-8')
                logging.info(f"Failure report saved: {failure_path}")
                print(str(failure_path))
                sys.exit(1)

    # Try to download file if it's a downloadable type
    downloader = SimpleDownloader()
    if downloader.try_download(url, ua, args.timeout, args.outdir):
        return  # Exit early, skip HTML processing for binary files

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
    if 'mp.weixin.qq.com' in host:
        logging.info("Selected parser: WeChat")
        parser_name = "WeChat"
        date_only, md, metadata = wechat_to_markdown(html, url)
        rendered = 'wechat' in ua.lower()
    elif 'xiaohongshu.com' in host or 'xhslink.com' in original_host:
        logging.info("Selected parser: Xiaohongshu")
        parser_name = "Xiaohongshu"
        date_only, md, metadata = xhs_to_markdown(html, url)
        rendered = should_render
    else:
        logging.info("Selected parser: Generic")
        parser_name = "Generic"
        date_only, md, metadata = generic_to_markdown(html, url, getattr(args, 'filter', 'safe'), is_crawling=False)
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
    
    # Add fetch metrics to markdown content if available
    if fetch_metrics:
        md = add_metrics_to_markdown(md, fetch_metrics)
    
    # Determine output formats needed
    output_markdown, output_html = determine_output_format(args, url)
    
    # Write markdown file if requested
    if output_markdown:
        path.write_text(md, encoding='utf-8')
        logging.info(f"Markdown file saved: {path}")
    
    # Write HTML file if requested
    if output_html:
        try:
            html_path = get_html_output_path(args, url, base)
            write_html_file(html, html_path, url, title)
            logging.info(f"HTML file saved: {html_path}")
        except Exception as e:
            logging.error(f"Failed to write HTML output: {e}")
    
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
        
        # Add fetch metrics to JSON if available
        if fetch_metrics:
            json_data['metadata']['fetch_metrics'] = fetch_metrics.to_dict()
        json_path = path.with_suffix('.json')
        json_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding='utf-8')
        logging.info(f"JSON data saved: {json_path}")
    
    # Print primary output path(s)
    if output_markdown and output_html:
        print(f"{path}\n{html_path}")
    elif output_html:
        print(str(html_path))
    else:
        print(str(path))


if __name__ == '__main__':
    main()
