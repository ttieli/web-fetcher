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
from parsers_legacy import (
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
# from parser_engine.template_parser import TemplateParser
# from parser_engine.engine.template_loader import TemplateLoader

# Configure module logger
logger = logging.getLogger(__name__)


# ============================================================================
# MIGRATION ADAPTER LAYER
# ============================================================================

def xhs_to_markdown(html: str, url: str) -> tuple[str, str, dict]:
    """
    XiaoHongShu (小红书) parser - Migration adapter

    Phase 3.1: Framework with TODO markers
    Phase 3.2: Implement template-based parsing

    Args:
        html: HTML content of the page
        url: Source URL

    Returns:
        tuple: (date_only, markdown_content, metadata)
    """
    # TODO Phase 3.2: Implement template-based XHS parsing
    # 1. Load XHS template from parser_engine/templates/sites/xiaohongshu/
    # 2. Initialize TemplateParser with template
    # 3. Parse HTML using template selectors
    # 4. Transform parsed data to markdown
    # 5. Return formatted result

    # For now, delegate to legacy implementation
    logger.info("Phase 3.1: Using legacy XHS parser (template-based migration pending)")
    from parsers_legacy import xhs_to_markdown as legacy_xhs_parser
    return legacy_xhs_parser(html, url)


def wechat_to_markdown(html: str, url: str) -> tuple[str, str, dict]:
    """
    WeChat (微信公众号) parser - Template-based implementation

    Phase 3.3: Migrated to template-based parsing engine

    Args:
        html: HTML content of the page
        url: Source URL

    Returns:
        tuple: (date_only, markdown_content, metadata)
    """
    try:
        # Import template-based parsing engine
        from parser_engine.template_parser import TemplateParser
        from parser_engine.engine.template_loader import TemplateLoader
        import os

        # Initialize template parser with WeChat template directory
        template_dir = os.path.join(
            os.path.dirname(__file__),
            'parser_engine', 'templates'
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
        from parsers_legacy import wechat_to_markdown as legacy_wechat_parser
        return legacy_wechat_parser(html, url)


def generic_to_markdown(html: str, url: str, filter_level: str = 'safe', is_crawling: bool = False) -> tuple[str, str, dict]:
    """
    Generic parser - Migration adapter

    Phase 3.1: Framework with TODO markers
    Phase 3.3: Implement template-based generic parsing

    Args:
        html: HTML content of the page
        url: Source URL
        filter_level: Content filtering level
        is_crawling: Whether in crawling mode

    Returns:
        tuple: (date_only, markdown_content, metadata)
    """
    # TODO Phase 3.3: Implement template-based generic parsing
    # 1. Use adaptive template selection based on content analysis
    # 2. Initialize TemplateParser with selected template
    # 3. Parse HTML using template selectors
    # 4. Transform parsed data to markdown
    # 5. Return formatted result

    # For now, delegate to legacy implementation
    logger.info("Phase 3.1: Using legacy generic parser (template-based migration pending)")
    from parsers_legacy import generic_to_markdown as legacy_generic_parser
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
    from parsers_legacy import extract_list_content as legacy_extract_list
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
    from parsers_legacy import detect_page_type as legacy_detect_page_type
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
    from parsers_legacy import format_list_page_markdown as legacy_format_list
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
        from parsers_legacy import XHSImageExtractor as LegacyExtractor
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
