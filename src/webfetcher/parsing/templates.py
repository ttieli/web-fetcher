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


def wechat_to_markdown(html: str, url: str, url_metadata: dict = None) -> tuple[str, str, dict]:
    """
    WeChat (微信公众号) parser - Template-based implementation

    Phase 3.3: Migrated to template-based parsing engine

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

        # Parse date
        date_only, date_time = parse_date_like(publish_time)

        # Format markdown output
        lines = [f"# {title}"]
        meta = [f"- 标题: {title}"]
        if author:
            meta.append(f"- 作者: {author}")
        meta += [
            f"- 发布时间: {date_time}",
            f"- 来源: [{url}]({url})",
            f"- 抓取时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]

        # Combine header and content
        lines += meta + ["", result.content]
        markdown_content = "\n\n".join(lines).strip() + "\n"

        # Build metadata dictionary
        metadata = {
            'author': author,
            'images': images,
            'publish_time': publish_time
        }

        logger.info(f"Phase 3.3: Successfully parsed WeChat article using template engine")
        return date_only, markdown_content, metadata

    except Exception as e:
        # Fallback to legacy implementation if template parsing fails
        logger.warning(f"Template-based WeChat parser failed: {e}, using legacy parser")
        from webfetcher.parsing.legacy import wechat_to_markdown as legacy_wechat_parser
        return legacy_wechat_parser(html, url)


def generic_to_markdown(html: str, url: str, filter_level: str = 'safe', is_crawling: bool = False, url_metadata: dict = None) -> tuple[str, str, dict]:
    """
    Generic parser - Template-based implementation

    Phase 3.1: Framework with TODO markers
    Phase 3.3: Implement template-based generic parsing
    Phase 3.5 (Task-4): Added template-based parsing with fallback to legacy

    Args:
        html: HTML content of the page
        url: Source URL
        filter_level: Content filtering level
        is_crawling: Whether in crawling mode
        url_metadata: Optional URL metadata containing input_url and final_url

    Returns:
        tuple: (date_only, markdown_content, metadata)
    """
    try:
        # Phase 3.5: Try template-based parsing first
        from .engine.template_parser import TemplateParser
        from .engine.template_loader import TemplateLoader
        import os

        # Initialize template parser
        template_dir = os.path.join(
            os.path.dirname(__file__),
            'engine', 'templates'
        )
        parser = TemplateParser(template_dir=template_dir)
        parser.reload_templates()  # Force reload to get updated generic.yaml v2.1.0

        # Parse using template engine (will auto-select based on URL domain)
        result = parser.parse(html, url)

        if not result.success:
            # Template parsing failed or no template found, use legacy
            raise Exception(f"Template parsing failed: {result.errors}")

        # Template parsing succeeded
        logger.info(f"Phase 3.5: Successfully parsed using template '{result.template_name}' for {url}")

        # Extract parsed data
        title = result.title or "未命名"
        author = result.metadata.get('author', 'Wikipedia contributors')
        publish_time = result.metadata.get('date', '')
        images = result.metadata.get('images', [])
        content = result.content or ''

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
            f"- 来源: {url}",
            f"- 抓取时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]

        # Add metadata section
        lines += meta

        # Add main content
        if content:
            lines += ["", content]

        # Add images section if images exist AND not already in content
        # Check if content already contains images (news articles with inline images)
        content_has_images = content and '![' in content if content else False

        if images and not content_has_images:
            # Only add separate image section for posts where images are separate from content
            # (e.g., XiaoHongShu posts, not news articles with inline images)
            lines += ["", "## 图片", ""] + [f"![]({normalize_media_url(u, url)})" for u in images]

        # Combine into markdown
        markdown_content = "\n\n".join(lines).strip() + "\n"

        # Build metadata dictionary
        metadata = {
            'author': author,
            'images': [normalize_media_url(u, url) for u in images],
            'publish_time': publish_time,
            'template_used': result.template_name
        }

        return date_only, markdown_content, metadata

    except Exception as e:
        # Fallback to legacy implementation if template parsing fails
        logger.info(f"Phase 3.5: No template found or template parsing failed for {url}, using legacy parser")
        from webfetcher.parsing.legacy import generic_to_markdown as legacy_generic_parser
        return legacy_generic_parser(html, url, filter_level, is_crawling)


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
