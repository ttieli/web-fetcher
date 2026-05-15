#!/usr/bin/env python3
"""
Web content parsers migration layer - Phase 3.1
This is the new adapter layer that will use the template-based parsing engine.

Phase 3.1: Framework setup with TODO markers for future implementation
Phase 3.2+: Actual migration of WeChat, XHS, and Generic parsers
"""

__version__ = "3.1.0"
__author__ = "WebFetcher Team - Phase 3 Migration"

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

# Import existing utilities and classes from parsers_legacy
# These will be reused during migration
from webfetcher.parsing.legacy import (
    # Enums and data classes
    PageType,
    ListItem,
    XHSImageData,

    # Helper functions that will be reused
    extract_meta,
    extract_json_ld_content,
    extract_from_modern_selectors,
    extract_text_from_html_fragment,
    parse_date_like,
    resolve_url_with_context,
    normalize_media_url,

    # Utility functions
    add_metrics_to_markdown,

    # BeautifulSoup availability
    BEAUTIFULSOUP_AVAILABLE,
    get_beautifulsoup_parser,
)

# TODO Phase 3.2: Import template-based parsing engine
# from .engine.template_parser import TemplateParser
# from .engine.template_loader import TemplateLoader

# Configure module logger
logger = logging.getLogger(__name__)


class AntiBotDetectedError(Exception):
    """Raised when anti-bot/verification page is detected instead of real content."""
    pass


# WeChat anti-bot / JS-required signatures
_WECHAT_ANTIBOT_KEYWORDS = ['环境异常', '完成验证后即可继续访问', '去验证']


def _detect_wechat_antibot(html: str) -> bool:
    """Check if WeChat returned a page without real content.

    Triggers on:
    - Anti-bot verification page ("环境异常")
    - JS-required mobile page (no js_content div, needs rendering)
    """
    # If js_content exists, the real article HTML was served
    if 'id="js_content"' in html or "id='js_content'" in html:
        return False
    # Anti-bot keywords
    if any(kw in html for kw in _WECHAT_ANTIBOT_KEYWORDS):
        return True
    # No js_content and it's a WeChat page → JS rendering needed
    if 'mp.weixin.qq.com' in html or '微信' in html:
        return True
    return False


# ============================================================================
# MIGRATION ADAPTER LAYER
# ============================================================================

def xhs_to_markdown(html: str, url: str, url_metadata: dict = None) -> tuple[str, str, dict]:
    """
    XiaoHongShu (小红书) parser - Template-based implementation

    Phase 3.4: Migrated to template-based parsing engine

    Args:
        html: HTML content of the page
        url: Source URL
        url_metadata: Optional URL metadata containing input_url and final_url

    Returns:
        tuple: (date_only, markdown_content, metadata)
    """
    try:
        # Import template-based parsing engine
        from .engine.template_parser import TemplateParser
        from .engine.template_loader import TemplateLoader
        import os

        # Initialize template parser with XiaoHongShu template directory
        template_dir = os.path.join(
            os.path.dirname(__file__),
            'engine', 'templates'
        )
        parser = TemplateParser(template_dir=template_dir)

        # Parse using template engine
        result = parser.parse(html, url)

        if not result.success:
            logger.warning(f"Template parsing failed: {result.errors}, falling back to legacy parser")
            raise Exception("Template parsing failed")

        # Extract parsed data
        title = result.title or "未命名"
        author = result.metadata.get('author', '')
        publish_time = result.metadata.get('date', '')
        description = result.metadata.get('description', '(未能从页面提取正文摘要)')
        cover = result.metadata.get('cover', '')
        images = result.metadata.get('images', [])
        videos = result.metadata.get('videos', [])

        # Detect if this is a video post
        # Use final_url from url_metadata if available (contains redirect params like type=video)
        detection_url = url_metadata.get('final_url', url) if url_metadata else url
        is_video_post = 'type=video' in detection_url.lower()
        logger.info(f"XHS: Video detection - url_metadata={bool(url_metadata)}, detection_url={detection_url[:100]}, is_video_post={is_video_post}")

        # Manual image extraction if template parser didn't extract them
        # XiaoHongShu uses <meta name="og:image"> (not property="og:image")
        if not images:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            # Extract all og:image meta tags (XiaoHongShu uses name attribute)
            og_images = soup.find_all('meta', {'name': 'og:image'})
            images = [tag.get('content', '') for tag in og_images if tag.get('content')]
            logger.debug(f"Manually extracted {len(images)} images from meta[name='og:image']")

        # Parse date
        date_only, date_time = parse_date_like(publish_time)

        # Format markdown output
        lines = [f"# {title}"]
        meta = [f"- 标题: {title}"]
        if author:
            meta.append(f"- 作者: {author}")
        meta += [
            f"- 发布时间: {date_time}",
            f"- 来源: {url}",
            f"- 抓取时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]

        # Add metadata section
        lines += meta

        # Add cover image if exists
        if cover:
            lines += ["", f"![]({normalize_media_url(cover, url)})"]

        # Add description/content
        body = description or result.content or '(未能从页面提取正文摘要)'
        lines += ["", body]

        # Add videos section - either with URLs or notification
        if videos:
            # Successfully extracted video URLs
            lines += ["", "## 视频"]
            for video_url in videos:
                lines.append(f"- 视频链接: {normalize_media_url(video_url, url)}")
        elif is_video_post:
            # Detected video post but couldn't extract URL (urllib limitation)
            lines += [
                "",
                "## 视频",
                "",
                "⚠️ **检测到视频内容，但无法通过静态采集获取视频链接**",
                "",
                "说明：小红书视频链接通过JavaScript动态加载，urllib方式无法提取。如需获取视频，请直接访问原网页。"
            ]

        # Add images section if images exist
        if images:
            lines += ["", "## 图片", ""] + [f"![]({normalize_media_url(u, url)})" for u in images]

        # Combine into markdown
        markdown_content = "\n\n".join(lines).strip() + "\n"

        # DEBUG: Log markdown generation
        if is_video_post:
            logger.info(f"XHS: Generated markdown for video post (length={len(markdown_content)})")
            logger.info(f"XHS: Lines count={len(lines)}, videos={len(videos)}, is_video_post={is_video_post}")
            # Check if '## 视频' is in the content
            if '## 视频' in markdown_content:
                logger.info("XHS: Video section confirmed in markdown")
            else:
                logger.warning("XHS: Video section NOT found in markdown despite being video post!")
                logger.info(f"XHS: Lines preview: {lines[-10:]}")  # Last 10 lines

        # Build metadata dictionary
        metadata = {
            'author': author,
            'images': [normalize_media_url(u, url) for u in images],
            'videos': [normalize_media_url(u, url) for u in videos],
            'cover': normalize_media_url(cover, url) if cover else '',
            'description': description,
            'publish_time': publish_time
        }

        logger.info(f"Phase 3.4: Successfully parsed XHS article using template engine")
        return date_only, markdown_content, metadata

    except Exception as e:
        # Fallback to legacy implementation if template parsing fails
        logger.warning(f"Template-based XHS parser failed: {e}, using legacy parser")
        from webfetcher.parsing.legacy import xhs_to_markdown as legacy_xhs_parser
        return legacy_xhs_parser(html, url)


def _clean_wechat_content(content: str, title: str = '') -> str:
    """Remove WeChat UI noise from converted markdown content.

    Strips: duplicate title, reward dialog text, number pad digits,
    share/close buttons, and other non-article elements.
    """
    if not content:
        return content

    lines = content.split('\n')
    cleaned: list[str] = []

    # Noise patterns (exact match or substring)
    _noise_exact = {
        '关闭 __', '****', '更多 __', '__', '名称已清空',
        '确定', '返回 __', '¥', '.', '文章', '暂无文章',
    }
    _noise_substr = [
        '微信扫一扫', '赞赏作者', '喜欢作者', '其它金额', '赞赏金额',
        '最低赞赏', '赞赏后展示', 'javascript:',
    ]

    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned.append(line)
            continue
        # Skip duplicate title (heading that matches the title)
        if stripped.lstrip('#').strip() == title.strip():
            continue
        # Skip single digit/dot (number pad)
        if stripped in set('0123456789.'):
            continue
        # Skip exact noise
        if stripped in _noise_exact:
            continue
        # Skip substring noise
        if any(ns in stripped for ns in _noise_substr):
            continue
        cleaned.append(line)

    # Collapse excessive blank lines
    result = re.sub(r'\n{3,}', '\n\n', '\n'.join(cleaned))
    return result.strip()


def _extract_wechat_gallery_images(html: str) -> list[str]:
    """Extract images from WeChat image-set articles (图集模式).

    WeChat gallery articles store images as:
    - <div data-src="https://mmbiz..."> (full-size)
    - <li style="background-image: url(...)"> (thumbnails, same URLs)
    We prefer <div data-src> as they are the full-size versions.
    """
    urls: list[str] = []
    seen: set[str] = set()

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # 1) <div data-src="mmbiz..."> inside gallery
        for div in soup.find_all('div', attrs={'data-src': True}):
            src = div['data-src'].strip()
            if 'mmbiz' in src and src not in seen:
                seen.add(src)
                urls.append(src)

        # 2) Fallback: background-image in style attribute
        if not urls:
            import re as _re
            for tag in soup.find_all(style=_re.compile(r'background-image')):
                m = _re.search(r'url\(["\']?(https?://mmbiz[^"\')\s]+)', tag.get('style', ''))
                if m and m.group(1) not in seen:
                    seen.add(m.group(1))
                    urls.append(m.group(1))

        # 3) Fallback: og:image meta
        if not urls:
            og = soup.find('meta', {'property': 'og:image'})
            if og and og.get('content') and 'mmbiz' in og['content']:
                urls.append(og['content'])
    except Exception as e:
        logger.debug(f"WeChat gallery image extraction failed: {e}")

    return urls


def wechat_to_markdown(html: str, url: str, url_metadata: dict = None) -> tuple[str, str, dict]:
    """
    WeChat (微信公众号) parser - Template-based implementation

    Args:
        html: HTML content of the page
        url: Source URL
        url_metadata: Optional URL metadata containing input_url and final_url

    Returns:
        tuple: (date_only, markdown_content, metadata)

    Raises:
        AntiBotDetectedError: When WeChat returns an anti-bot verification page
    """
    # Detect anti-bot page BEFORE any parsing attempt
    if _detect_wechat_antibot(html):
        raise AntiBotDetectedError("WeChat anti-bot verification page detected (环境异常)")

    try:
        # Import template-based parsing engine
        from .engine.template_parser import TemplateParser
        from .engine.template_loader import TemplateLoader
        import os

        # Initialize template parser with WeChat template directory
        template_dir = os.path.join(
            os.path.dirname(__file__),
            'engine', 'templates'
        )
        parser = TemplateParser(template_dir=template_dir)

        # Parse using template engine
        result = parser.parse(html, url)

        if not result.success:
            logger.warning(f"Template parsing failed: {result.errors}, falling back to legacy parser")
            raise Exception("Template parsing failed")

        # Extract parsed data
        title = result.title or "未命名"
        author = result.metadata.get('author', '')
        publish_time = result.metadata.get('date', '')
        images = result.metadata.get('images', [])

        # WeChat image-set articles store images in <div data-src> and
        # <li style="background-image:url(...)"> instead of <img> tags.
        # is_gallery 严格由 js_image_content 容器存在性判定，不能用"提取到图片"反推
        # （因为 _extract_wechat_gallery_images 的 og:image fallback 对任何文章都会命中封面图）
        is_gallery = 'js_image_content' in html
        if not images:
            images = _extract_wechat_gallery_images(html)
            if images:
                source = "gallery" if is_gallery else "og:image fallback"
                logger.info(f"Extracted {len(images)} images from WeChat ({source})")

        # Clean content: remove WeChat UI noise (赞赏弹窗, 数字键盘, etc.)
        content = result.content or ''
        content = _clean_wechat_content(content, title)

        # For gallery articles, text content is just UI noise — discard it
        if is_gallery and images:
            content = ''

        # Parse date
        date_only, date_time = parse_date_like(publish_time)

        # Format markdown output
        lines = [f"# {title}"]
        meta = [f"- 标题: {title}"]
        if author:
            meta.append(f"- 作者: {author}")
        if publish_time:
            meta.append(f"- 发布时间: {date_time}")
        meta += [
            f"- 来源: [{url}]({url})",
            f"- 抓取时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        lines += meta

        if content.strip():
            lines.append("")
            lines.append(content)

        # Embed images that aren't already in the converted content
        if images and (not content or '![' not in content):
            lines.append("")
            for img_url in images:
                lines.append(f"![]({normalize_media_url(img_url, url)})")

        markdown_content = "\n\n".join(lines).strip() + "\n"

        # Build metadata dictionary
        metadata = {
            'author': author,
            'images': [normalize_media_url(u, url) for u in images],
            'publish_time': publish_time
        }

        logger.info(f"Successfully parsed WeChat article using template engine")
        return date_only, markdown_content, metadata

    except Exception as e:
        # Fallback to legacy implementation if template parsing fails
        logger.warning(f"Template-based WeChat parser failed: {e}, using legacy parser")
        from webfetcher.parsing.legacy import wechat_to_markdown as legacy_wechat_parser
        return legacy_wechat_parser(html, url)


def generic_to_markdown(html: str, url: str, filter_level: str = 'safe', is_crawling: bool = False, url_metadata: dict = None) -> tuple[str, str, dict]:
    """
    Generic parser — site templates first, then trafilatura for content extraction.

    Args:
        html: HTML content of the page
        url: Source URL
        filter_level: Content filtering level
        is_crawling: Whether in crawling mode
        url_metadata: Optional URL metadata containing input_url and final_url

    Returns:
        tuple: (date_only, markdown_content, metadata)
    """
    from .engine.template_parser import TemplateParser
    import os

    # --- Step 1: TemplateParser for metadata (and site-specific content) ---
    template_dir = os.path.join(os.path.dirname(__file__), 'engine', 'templates')
    parser = TemplateParser(template_dir=template_dir)
    parser.reload_templates()

    tp_title = ''
    tp_author = ''
    tp_date = ''
    tp_content = ''
    tp_images: list = []
    template_name = ''
    is_generic_template = True

    try:
        result = parser.parse(html, url)
        if result.success:
            template_name = result.template_name or ''
            is_generic_template = 'generic' in template_name.lower()
            tp_title = result.title or ''
            tp_author = result.metadata.get('author', '')
            tp_date = result.metadata.get('date', '')
            tp_images = result.metadata.get('images', [])
            tp_content = result.content or ''
            logger.info(f"TemplateParser matched '{template_name}' for {url}")
    except Exception as e:
        logger.debug(f"TemplateParser failed: {e}")

    # If a site-specific template produced content, use it directly
    if not is_generic_template and tp_content.strip():
        return _build_generic_output(
            title=tp_title, author=tp_author, publish_time=tp_date,
            content=tp_content, images=tp_images, url=url,
            template_name=template_name,
        )

    # --- Step 2: trafilatura for content extraction ---
    content = ''
    traf_title = ''
    traf_author = ''
    traf_date = ''

    try:
        from trafilatura import bare_extraction
        extracted = bare_extraction(
            html, url=url,
            include_tables=True, include_links=True,
            include_images=True, include_formatting=True,
            favor_precision=False, as_dict=True,
        )
        if extracted:
            traf_title = extracted.get('title') or ''
            traf_author = extracted.get('author') or ''
            traf_date = extracted.get('date') or ''
            raw_text = extracted.get('text') or ''
            if raw_text:
                content = raw_text
                logger.info(f"trafilatura extracted {len(content)} chars for {url}")
    except Exception as e:
        logger.warning(f"trafilatura extraction failed: {e}")

    # Merge: prefer TemplateParser metadata, fill gaps with trafilatura
    title = tp_title or traf_title or '未命名'
    author = tp_author or traf_author
    publish_time = tp_date or traf_date

    # If trafilatura also failed, fall back to legacy
    if not content.strip():
        logger.warning(f"trafilatura returned empty content for {url}, falling back to legacy")
        from webfetcher.parsing.legacy import generic_to_markdown as legacy_generic_parser
        return legacy_generic_parser(html, url, filter_level, is_crawling)

    return _build_generic_output(
        title=title, author=author, publish_time=publish_time,
        content=content, images=tp_images, url=url,
        template_name=template_name or 'trafilatura',
    )


def _build_generic_output(
    *, title: str, author: str, publish_time: str,
    content: str, images: list, url: str, template_name: str,
) -> tuple[str, str, dict]:
    """Format the standard (date_only, markdown, metadata) output tuple."""
    title = title or '未命名'
    date_only, date_time = parse_date_like(publish_time)

    lines = [f"# {title}"]
    meta = [f"- 标题: {title}"]
    if author:
        meta.append(f"- 作者: {author}")
    if publish_time:
        meta.append(f"- 发布时间: {date_time}")
    meta += [
        f"- 来源: {url}",
        f"- 抓取时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    lines += meta

    if content:
        lines += ["", content]

    # Only add separate images if content doesn't already include them
    if images and (not content or '![' not in content):
        lines += ["", "## 图片", ""] + [f"![]({normalize_media_url(u, url)})" for u in images]

    markdown_content = "\n\n".join(lines).strip() + "\n"

    metadata = {
        'author': author,
        'images': [normalize_media_url(u, url) for u in images],
        'publish_time': publish_time,
        'template_used': template_name,
    }

    return date_only, markdown_content, metadata


# ============================================================================
# YAML FRONT MATTER CONVERSION
# ============================================================================

def apply_yaml_frontmatter(md: str, url: str, metadata: dict) -> str:
    """将内嵌元数据替换为标准 YAML front matter 格式。

    Converts inline metadata lines (- 标题/作者/发布时间/来源/抓取时间: value)
    into a standard YAML front matter block (--- delimited) compatible with
    Hugo, Jekyll, Obsidian, etc. Other content (Fetch Metrics comment,
    Fetch Information section, body) is preserved.

    Args:
        md: Markdown content with inline metadata
        url: Source URL
        metadata: Metadata dictionary from the parser

    Returns:
        Markdown with YAML front matter prepended and inline metadata removed
    """
    lines = md.split('\n')
    if not lines:
        return md

    # Known inline metadata keys to strip
    _META_KEYS = re.compile(
        r'^- (?:标题|作者|发布时间|来源|抓取时间|视频链接)\s*[:：]'
    )

    # Step 1: Extract title from the first `# ` heading
    title = ''
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('# '):
            title = stripped[2:].strip()
            break

    # Step 2: Remove inline metadata lines and surrounding blank lines
    filtered = []
    i = 0
    while i < len(lines):
        if _META_KEYS.match(lines[i].strip()):
            # Skip this metadata line and any immediately following blank line
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            continue
        filtered.append(lines[i])
        i += 1

    # Step 3: Build YAML front matter block
    fm = ['---']

    if title:
        fm.append(f'title: "{title}"')

    author = metadata.get('author', '')
    if author:
        fm.append(f'author: "{author}"')

    publish_time = metadata.get('publish_time', '')
    if publish_time:
        fm.append(f'date: "{publish_time}"')

    if url:
        fm.append(f'url: "{url}"')

    fm.append(f'scraped_at: "{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"')

    template_used = metadata.get('template_used', '')
    if template_used:
        fm.append(f'template: "{template_used}"')

    fm.append('---')

    # Step 4: Prepend frontmatter to the cleaned content
    return '\n'.join(fm) + '\n\n' + '\n'.join(filtered)


# ============================================================================
# LIST CONTENT EXTRACTION (Reuse legacy for now)
# ============================================================================

def extract_list_content(html: str, base_url: str) -> tuple[str, List[ListItem]]:
    """
    Extract list content from HTML

    Phase 3.1: Reuse legacy implementation
    Phase 3.4: Consider migration if needed

    Args:
        html: HTML content
        base_url: Base URL for resolving relative links

    Returns:
        tuple: (page_title, list_items)
    """
    # TODO Phase 3.4: Consider template-based list extraction
    from webfetcher.parsing.legacy import extract_list_content as legacy_extract_list
    return legacy_extract_list(html, base_url)


def detect_page_type(html: str, url: Optional[str] = None, is_crawling: bool = False) -> PageType:
    """
    Detect page type (article or list)

    Phase 3.1: Reuse legacy implementation
    Phase 3.4: Consider enhancement

    Args:
        html: HTML content
        url: Optional URL for context
        is_crawling: Whether in crawling mode

    Returns:
        PageType: Detected page type
    """
    # TODO Phase 3.4: Consider ML-based page type detection
    from webfetcher.parsing.legacy import detect_page_type as legacy_detect_page_type
    return legacy_detect_page_type(html, url, is_crawling)


def format_list_page_markdown(page_title: str, list_items: List[ListItem], url: str) -> tuple[str, str, dict]:
    """
    Format list page as markdown

    Phase 3.1: Reuse legacy implementation

    Args:
        page_title: Page title
        list_items: List of extracted items
        url: Source URL

    Returns:
        tuple: (date_only, markdown_content, metadata)
    """
    from webfetcher.parsing.legacy import format_list_page_markdown as legacy_format_list
    return legacy_format_list(page_title, list_items, url)


# ============================================================================
# XHS IMAGE EXTRACTOR (Legacy compatibility)
# ============================================================================

class XHSImageExtractor:
    """
    XiaoHongShu image extractor - Legacy compatibility wrapper

    Phase 3.1: Delegate to legacy implementation
    Phase 3.2: Migrate to template-based extraction
    """

    def __init__(self, html: str, url: str = "", debug: bool = False):
        # TODO Phase 3.2: Implement template-based image extraction
        from webfetcher.parsing.legacy import XHSImageExtractor as LegacyExtractor
        self._legacy_extractor = LegacyExtractor(html, url, debug)

    def extract_all(self) -> List[str]:
        """Extract all images using legacy implementation"""
        # TODO Phase 3.2: Use template-based extraction
        return self._legacy_extractor.extract_all()


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Main parser functions
    'xhs_to_markdown',
    'wechat_to_markdown',
    'generic_to_markdown',

    # Exceptions
    'AntiBotDetectedError',

    # List handling
    'extract_list_content',
    'detect_page_type',
    'format_list_page_markdown',

    # Data classes and enums
    'PageType',
    'ListItem',
    'XHSImageData',

    # Image extraction
    'XHSImageExtractor',

    # Helper functions
    'extract_meta',
    'extract_json_ld_content',
    'extract_from_modern_selectors',
    'extract_text_from_html_fragment',
    'parse_date_like',
    'resolve_url_with_context',
    'normalize_media_url',
    'add_metrics_to_markdown',

    # BeautifulSoup
    'BEAUTIFULSOUP_AVAILABLE',
    'get_beautifulsoup_parser',
]
