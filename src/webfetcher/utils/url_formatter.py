"""
URL Formatter Module for Web_Fetcher

Provides utilities for consistent URL formatting in markdown output.
Handles URL detection, markdown link generation, and edge cases.

Task-003 Phase 2: URL Formatter Module
Author: Web_Fetcher Team
Version: 1.0
"""

import re
import logging
from typing import Optional, List, Tuple
from urllib.parse import urlparse

# Configure logging
logger = logging.getLogger(__name__)

# ================================================================================
# URL Pattern Constants
# ================================================================================

# Comprehensive URL pattern matching
URL_PATTERNS = {
    # Full URLs with protocol (http/https)
    'full_url': r'https?://[^\s\)\]\>\`\"\']+',

    # Protocol-relative URLs (//example.com)
    'protocol_relative': r'//[a-zA-Z0-9][^\s\)\]\>\`\"\']+',

    # Bare domains (optional, less strict)
    'bare_domain': r'\b(?:www\.)?[a-z0-9-]+(?:\.[a-z]{2,})+(?:/[^\s\)\]\>\`\"\']*)?',

    # Email addresses (for mailto: links)
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
}

# Code block patterns for preservation
CODE_BLOCK_PATTERNS = {
    # Inline code: `code`
    'inline': r'`[^`\n]+`',

    # Fenced code blocks: ```code```
    'fenced': r'```[\s\S]*?```',

    # Indented code (4 spaces or tab at line start)
    'indented': r'^(?:    |\t).+$'
}

# Markdown link pattern to avoid double-formatting
MARKDOWN_LINK_PATTERN = r'\[([^\]]+)\]\(([^\)]+)\)'


# ================================================================================
# Core URL Formatting Functions
# ================================================================================

def format_url_as_markdown(url: str, text: Optional[str] = None) -> str:
    """
    Convert URL to markdown link format.

    Args:
        url: The URL to format
        text: Optional link text (uses URL if not provided)

    Returns:
        Markdown formatted link: [text](url)

    Examples:
        >>> format_url_as_markdown("https://example.com")
        '[https://example.com](https://example.com)'

        >>> format_url_as_markdown("https://example.com", "Example Site")
        '[Example Site](https://example.com)'
    """
    # Validate URL first
    if not is_valid_url(url):
        # Use debug level for JavaScript URLs and other expected invalid formats
        logger.debug(f"Task-003 Phase 2: Invalid URL format, returning as-is: {url}")
        return url  # Return as-is if invalid

    # Use URL as text if not provided
    display_text = text if text else url

    # Return markdown format
    return f"[{display_text}]({url})"


def is_valid_url(url: str) -> bool:
    """
    Validate URL format.

    Args:
        url: URL string to validate

    Returns:
        True if URL is valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False

    # Basic validation: should have a scheme or be a valid domain
    try:
        result = urlparse(url)
        # Has scheme (http/https) and netloc (domain)
        if result.scheme in ('http', 'https') and result.netloc:
            return True
        # Protocol-relative URL
        if url.startswith('//') and len(url) > 3:
            return True
        # For other cases, check if it looks like a domain
        if '.' in url and len(url) > 4:
            return True
        return False
    except Exception as e:
        logger.debug(f"Task-003 Phase 2: URL validation error for '{url}': {e}")
        return False


def normalize_url_for_display(url: str) -> str:
    """
    Normalize URL for display (add protocol if missing, etc.)

    Args:
        url: URL to normalize

    Returns:
        Normalized URL string
    """
    if not url:
        return url

    url = url.strip()

    # Already has protocol
    if url.startswith(('http://', 'https://', '//', 'mailto:', 'ftp://')):
        return url

    # Add https:// for bare domains
    if '.' in url:
        return f"https://{url}"

    return url


# ================================================================================
# URL Detection Functions
# ================================================================================

# Compile pattern once for performance
_URL_PATTERN_COMPILED = None

def _compile_url_pattern() -> re.Pattern:
    """Compile comprehensive URL pattern for detection."""
    global _URL_PATTERN_COMPILED
    if _URL_PATTERN_COMPILED is None:
        # Combine patterns (prioritize full URLs)
        pattern = '|'.join([
            URL_PATTERNS['full_url'],
            URL_PATTERNS['protocol_relative'],
            # Uncomment if you want to match bare domains:
            # URL_PATTERNS['bare_domain'],
        ])
        _URL_PATTERN_COMPILED = re.compile(pattern)
    return _URL_PATTERN_COMPILED


def detect_urls_in_text(text: str) -> List[Tuple[str, int, int]]:
    """
    Find all URLs in text with their positions.

    Args:
        text: Input text to search for URLs

    Returns:
        List of (url, start_pos, end_pos) tuples

    Example:
        >>> text = "Visit https://example.com for info"
        >>> urls = detect_urls_in_text(text)
        >>> urls[0]
        ('https://example.com', 6, 25)
    """
    pattern = _compile_url_pattern()
    urls = []

    for match in pattern.finditer(text):
        url = match.group(0)
        start = match.start()
        end = match.end()

        # Clean up URL (remove trailing punctuation that might be sentence end)
        while url and url[-1] in '.,;:!?)':
            url = url[:-1]
            end -= 1

        if is_valid_url(url):
            urls.append((url, start, end))
            logger.debug(f"Task-003 Phase 2: Detected URL '{url}' at position {start}-{end}")

    return urls


# ================================================================================
# Code Block Protection Functions
# ================================================================================

def _is_in_code_block(text: str, position: int) -> bool:
    """
    Check if a position in text is inside a code block.

    Args:
        text: Full text
        position: Character position to check

    Returns:
        True if position is within a code block, False otherwise
    """
    # Check inline code blocks
    inline_pattern = re.compile(CODE_BLOCK_PATTERNS['inline'])
    for match in inline_pattern.finditer(text):
        if match.start() <= position < match.end():
            logger.debug(f"Task-003 Phase 2: Position {position} is in inline code block")
            return True

    # Check fenced code blocks
    fenced_pattern = re.compile(CODE_BLOCK_PATTERNS['fenced'], re.DOTALL)
    for match in fenced_pattern.finditer(text):
        if match.start() <= position < match.end():
            logger.debug(f"Task-003 Phase 2: Position {position} is in fenced code block")
            return True

    # Check indented code blocks (per line basis)
    lines = text.split('\n')
    current_pos = 0
    for line in lines:
        line_end = current_pos + len(line)
        if current_pos <= position < line_end:
            # Check if this line is indented code
            if re.match(CODE_BLOCK_PATTERNS['indented'], line):
                logger.debug(f"Task-003 Phase 2: Position {position} is in indented code block")
                return True
            break
        current_pos = line_end + 1  # +1 for newline

    return False


def _is_existing_markdown_link(text: str, url_start: int) -> bool:
    """
    Check if URL at given position is already part of a markdown link.

    Args:
        text: Full text
        url_start: Start position of URL

    Returns:
        True if URL is already in a markdown link, False otherwise
    """
    # Look backwards for markdown link syntax: [text](url)
    # Check if there's "](" before the URL
    search_start = max(0, url_start - 100)  # Look back up to 100 chars
    substring = text[search_start:url_start + 10]

    # Pattern: Check if URL is inside (...)  after ](
    if '](' in substring:
        # Find position of ](
        bracket_pos = substring.rfind('](')
        if bracket_pos >= 0:
            # URL should be right after ](
            if search_start + bracket_pos + 2 == url_start or \
               search_start + bracket_pos + 2 == url_start - 1:
                logger.debug(f"Task-003 Phase 2: URL at {url_start} is already a markdown link")
                return True

    return False


# ================================================================================
# Main URL Replacement Function
# ================================================================================

def replace_urls_with_markdown(text: str, preserve_code_blocks: bool = True) -> str:
    """
    Replace plain URLs in text with markdown links.

    This is the main function that combines all the utilities to convert
    plain text URLs into properly formatted markdown links.

    Args:
        text: Input text with plain URLs
        preserve_code_blocks: Don't format URLs in code blocks (default True)

    Returns:
        Text with URLs converted to markdown links

    Example:
        >>> text = "Visit https://example.com for more info"
        >>> result = replace_urls_with_markdown(text)
        >>> result
        'Visit [https://example.com](https://example.com) for more info'
    """
    if not text:
        return text

    # Detect all URLs in text
    urls = detect_urls_in_text(text)

    if not urls:
        logger.debug("Task-003 Phase 2: No URLs detected in text")
        return text

    logger.info(f"Task-003 Phase 2: Found {len(urls)} URL(s) to process")

    # Process URLs in reverse order to maintain position accuracy
    result = text
    for url, start, end in reversed(urls):
        # Skip if in code block
        if preserve_code_blocks and _is_in_code_block(result, start):
            logger.debug(f"Task-003 Phase 2: Skipping URL in code block: {url}")
            continue

        # Skip if already a markdown link
        if _is_existing_markdown_link(result, start):
            logger.debug(f"Task-003 Phase 2: Skipping existing markdown link: {url}")
            continue

        # Replace with markdown link
        markdown_link = format_url_as_markdown(url)
        result = result[:start] + markdown_link + result[end:]
        logger.debug(f"Task-003 Phase 2: Replaced '{url}' with '{markdown_link}'")

    return result


# ================================================================================
# Task-003 Phase 3: Dual URL Metadata Section Functions
# ================================================================================

def format_dual_url_section(url_metadata: dict) -> str:
    """
    Format the dual URL metadata section with bilingual labels.

    This function creates a professional, bilingual metadata section that displays
    both the original input URL and the final fetched URL, along with fetch timestamp.

    Args:
        url_metadata: Dictionary containing URL tracking information with keys:
                     - input_url: Original URL from command line
                     - final_url: Final URL after redirects
                     - fetch_date: ISO formatted timestamp (optional)
                     - fetch_mode: Fetch method used (optional)

    Returns:
        Formatted markdown string with dual URL section
        Returns empty string if url_metadata is None/empty

    Example:
        >>> metadata = {
        ...     'input_url': 'example.com',
        ...     'final_url': 'https://www.example.com/page',
        ...     'fetch_date': '2025-10-13 12:00:00'
        ... }
        >>> section = format_dual_url_section(metadata)
        >>> print(section)

        **Fetch Information / 采集信息:**
        - Original Request / 原始请求: [example.com](https://example.com)
        - Final Location / 最终地址: [https://www.example.com/page](https://www.example.com/page)
        - Fetch Date / 采集时间: 2025-10-13 12:00:00

        ---
    """
    # Graceful degradation - return empty if no metadata
    if not url_metadata:
        logger.debug("Task-003 Phase 3: No url_metadata provided, skipping dual URL section")
        return ""

    # Extract URL fields
    input_url = url_metadata.get('input_url', '')
    final_url = url_metadata.get('final_url', '')
    fetch_date = url_metadata.get('fetch_date', '')

    # If both URLs are empty, skip section
    if not input_url and not final_url:
        logger.warning("Task-003 Phase 3: Both input_url and final_url are empty")
        return ""

    # Format URLs as markdown links (with normalization)
    if input_url:
        normalized_input = normalize_url_for_display(input_url)
        input_link = format_url_as_markdown(normalized_input, input_url)
    else:
        input_link = "N/A"

    if final_url:
        normalized_final = normalize_url_for_display(final_url)
        final_link = format_url_as_markdown(normalized_final, final_url)
    else:
        final_link = "N/A"

    # Generate current timestamp if fetch_date is missing
    if not fetch_date:
        from datetime import datetime
        fetch_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.debug(f"Task-003 Phase 3: Generated fetch_date: {fetch_date}")

    # Build the dual URL section with bilingual labels
    section = f"""
**Fetch Information / 采集信息:**
- Original Request / 原始请求: {input_link}
- Final Location / 最终地址: {final_link}
- Fetch Date / 采集时间: {fetch_date}

---
"""

    logger.info("Task-003 Phase 3: Created dual URL section successfully")
    return section


def insert_dual_url_section(markdown: str, url_metadata: dict) -> str:
    """
    Insert dual URL section after the title in markdown content.

    This function intelligently inserts the dual URL metadata section after
    the first H1 heading (#) and before any existing metadata lines (- 标题:, etc.).

    Args:
        markdown: Original markdown content
        url_metadata: URL metadata dictionary (from create_url_metadata)

    Returns:
        Enhanced markdown with dual URL section inserted
        Returns original markdown if url_metadata is None (graceful degradation)

    Edge Cases Handled:
        - No H1 title: Insert at beginning of document
        - Multiple H1 titles: Insert after first one only
        - Missing url_metadata: Return original markdown unchanged
        - Empty markdown: Still insert section with proper formatting

    Example:
        >>> markdown = '''# Test Article
        ...
        ... - 标题: Test
        ... - 作者: Author
        ...
        ... Content here...
        ... '''
        >>> metadata = {'input_url': 'example.com', 'final_url': 'https://example.com'}
        >>> result = insert_dual_url_section(markdown, metadata)
        # Result will have dual URL section after "# Test Article"
    """
    # Graceful degradation - return original if no metadata
    if not url_metadata:
        logger.debug("Task-003 Phase 3: No url_metadata, returning original markdown")
        return markdown

    # Generate the dual URL section
    dual_url_section = format_dual_url_section(url_metadata)

    # If section is empty (e.g., empty URLs), return original
    if not dual_url_section:
        logger.debug("Task-003 Phase 3: Dual URL section is empty, returning original markdown")
        return markdown

    # Split markdown into lines for processing
    lines = markdown.splitlines() if markdown else []

    # Find the first H1 heading (# Title)
    title_index = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('# ') and len(stripped) > 2:
            title_index = i
            logger.debug(f"Task-003 Phase 3: Found title at line {i}: {stripped[:50]}")
            break

    # Build enhanced markdown
    if title_index == -1:
        # No title found - insert section at beginning
        logger.info("Task-003 Phase 3: No H1 title found, inserting at beginning")
        result_lines = [dual_url_section.strip(), ''] + lines
    else:
        # Insert after title (with proper spacing)
        logger.info(f"Task-003 Phase 3: Inserting dual URL section after title at line {title_index}")
        result_lines = (
            lines[:title_index + 1] +     # Include title line
            [''] +                         # Blank line after title
            [dual_url_section.strip()] +   # Dual URL section
            ['']                           # Blank line before rest
        )

        # Add remaining lines (skip blank line immediately after title if exists)
        remaining_start = title_index + 1
        if remaining_start < len(lines) and not lines[remaining_start].strip():
            remaining_start += 1  # Skip existing blank line

        result_lines.extend(lines[remaining_start:])

    # Join lines back together
    enhanced_markdown = '\n'.join(result_lines)

    logger.info("Task-003 Phase 3: Successfully inserted dual URL section")
    return enhanced_markdown
