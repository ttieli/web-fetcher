"""Template-based parser implementation.

This module implements a parser that uses YAML templates to extract content
from web pages. It integrates with the TemplateLoader to match URLs to templates
and extract structured data based on template rules.
"""

from typing import Dict, Any, Optional, List
import html2text
from lxml import etree
from .base_parser import (
    BaseParser,
    ParseResult,
    ParserError,
    ExtractionError,
    TemplateNotFoundError
)
from .template_loader import TemplateLoader
from .strategies import CSSStrategy, XPathStrategy, TextPatternStrategy


class TemplateParser(BaseParser):
    """
    Parser that uses YAML templates for content extraction.

    This parser loads templates via TemplateLoader and applies template rules
    to extract structured content from HTML pages. It supports:
    - Automatic template selection based on URL
    - Fallback to generic template
    - Template-driven extraction rules
    - Extensible selector strategies

    Example:
        parser = TemplateParser()
        result = parser.parse(html_content, url)
        print(result.title, result.content)

    Attributes:
        template_loader: TemplateLoader instance for template management
        current_template: Currently active template (None until parse is called)
        template_cache: Cache of loaded templates by URL pattern
    """

    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize template parser.

        Args:
            template_dir: Optional directory path for templates.
                         If None, uses default location (parsers/templates)

        Raises:
            ParserError: If template loader initialization fails
        """
        super().__init__()

        # Initialize logger
        import logging
        self.logger = logging.getLogger(__name__)

        # Initialize template loader
        try:
            self.template_loader = TemplateLoader(template_dir)
        except Exception as e:
            raise ParserError(f"Failed to initialize template loader: {e}")

        # Current template and cache
        self.current_template: Optional[Dict[str, Any]] = None
        self.template_cache: Dict[str, Dict[str, Any]] = {}

        # Initialize extraction strategies
        self.strategies = {
            'css': CSSStrategy(),
            'xpath': XPathStrategy(),
            'text': TextPatternStrategy()
        }

        # Initialize HTML to Markdown converter
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.body_width = 0  # No wrapping

    def get_template_for_url(self, url: str) -> Dict[str, Any]:
        """
        Get matching template for URL.

        This method finds and caches the best matching template for the given URL.
        It uses the TemplateLoader's matching logic and caches results.

        Args:
            url: URL to find template for

        Returns:
            Dict[str, Any]: Template configuration

        Raises:
            TemplateNotFoundError: If no suitable template is found
        """
        # Check cache first
        if url in self.template_cache:
            return self.template_cache[url]

        # Find template
        template = self.template_loader.get_template_for_url(url)

        if template is None:
            raise TemplateNotFoundError(f"No template found for URL: {url}")

        # Cache and return
        self.template_cache[url] = template
        return template

    def _detect_strategy(self, selector: str) -> str:
        """
        Detect strategy type from selector string.

        Args:
            selector: Selector string to analyze

        Returns:
            str: Strategy type ('xpath' or 'css')
        """
        # XPath starts with // or /
        if selector.startswith('//') or selector.startswith('/'):
            return 'xpath'
        # Default to CSS
        return 'css'

    def _normalize_selector_config(self, field_config: Any) -> list:
        """
        Normalize selector configuration to list of (selector, strategy, options) tuples.

        Args:
            field_config: Field configuration in any supported format

        Returns:
            list: List of (selector, strategy, options) tuples
        """
        selectors = []

        # Format 1: String selector (comma-separated)
        if isinstance(field_config, str):
            for s in field_config.split(','):
                selector = s.strip()
                strategy = self._detect_strategy(selector)
                selectors.append((selector, strategy, {}))

        # Format 2: List of dicts (generic.yaml format)
        elif isinstance(field_config, list):
            for item in field_config:
                if isinstance(item, dict):
                    selector = item.get('selector', '').strip()
                    strategy = item.get('strategy', 'css')
                    # Pass through other options
                    options = {k: v for k, v in item.items() if k not in ['selector', 'strategy']}
                    if selector:
                        selectors.append((selector, strategy, options))
                elif isinstance(item, str):
                    # Handle list of strings (fallback)
                    selector = item.strip()
                    strategy = self._detect_strategy(selector)
                    selectors.append((selector, strategy, {}))

        # Format 3: Single dict (edge case)
        elif isinstance(field_config, dict):
            selector = field_config.get('selector', '').strip()
            strategy = field_config.get('strategy', 'css')
            options = {k: v for k, v in field_config.items() if k not in ['selector', 'strategy']}
            if selector:
                selectors.append((selector, strategy, options))

        return selectors

    def _extract_field(self, content: str, field_config: Any) -> Optional[str]:
        """
        Extract a field using configured selectors with fallback support.
        """
        # Process list of dicts with full config (including post_process)
        if isinstance(field_config, list):
            for item in field_config:
                if isinstance(item, dict):
                    selector = item.get('selector', '').strip()
                    strategy_type = item.get('strategy', 'css')
                    attribute = item.get('attribute')
                    post_process = item.get('post_process', [])

                    if not selector:
                        continue

                    try:
                        # Build full selector with attribute if needed
                        if attribute and selector.startswith('meta['):
                            full_selector = f"{selector}@{attribute}"
                        elif selector.startswith('meta[') and '@' not in selector:
                            full_selector = selector + '@content'
                        else:
                            full_selector = selector

                        # Get strategy
                        strategy = self.strategies.get(strategy_type, self.strategies['css'])

                        # Extract using strategy
                        result = strategy.extract(content, full_selector)

                        # Apply post-processing if result found
                        if result and result.strip():
                            result = self._apply_post_process(result, post_process)
                            if result and result.strip():
                                return result.strip()

                    except Exception as e:
                        self.logger.debug(f"Selector '{selector}' (strategy: {strategy_type}) failed: {e}")
                        continue

        # Fallback to original normalization for simple configs
        else:
            selectors = self._normalize_selector_config(field_config)

            if not selectors:
                return None

            # Try each selector in order until one succeeds
            for selector, strategy_type, _ in selectors:
                try:
                    # Auto-append @content for meta tags if not specified
                    if selector.startswith('meta[') and '@' not in selector:
                        selector = selector + '@content'

                    # Get strategy
                    strategy = self.strategies.get(strategy_type, self.strategies['css'])

                    # Extract using strategy
                    result = strategy.extract(content, selector)

                    # Return first non-empty result
                    if result and result.strip():
                        return result.strip()

                except Exception as e:
                    # Log and continue to next selector
                    self.logger.debug(f"Selector '{selector}' (strategy: {strategy_type}) failed: {e}")
                    continue

        return None

    def _apply_post_process(self, value: str, post_process: list) -> str:
        """
        Apply post-processing rules to extracted value.

        Args:
            value: Extracted value to process
            post_process: List of post-processing rules

        Returns:
            str: Processed value
        """
        import re

        if not post_process or not value:
            return value

        result = value

        for rule in post_process:
            if not isinstance(rule, dict):
                continue

            rule_type = rule.get('type')

            if rule_type == 'regex_replace':
                # Regex replacement
                pattern = rule.get('pattern', '')
                replacement = rule.get('replacement', '')
                flags_str = rule.get('flags', '')

                # Convert flags string to re flags
                flags = 0
                if 'i' in flags_str.lower():
                    flags |= re.IGNORECASE
                if 'm' in flags_str.lower():
                    flags |= re.MULTILINE
                if 's' in flags_str.lower():
                    flags |= re.DOTALL

                try:
                    result = re.sub(pattern, replacement, result, flags=flags)
                except Exception as e:
                    self.logger.debug(f"Regex post-process failed: {e}")

            elif rule_type == 'replace':
                # Simple string replacement
                old = rule.get('old', '')
                new = rule.get('new', '')
                result = result.replace(old, new)

            elif rule_type == 'strip':
                # Strip whitespace
                result = result.strip()

            elif rule_type == 'lower':
                # Convert to lowercase
                result = result.lower()

            elif rule_type == 'upper':
                # Convert to uppercase
                result = result.upper()

        return result

    def parse(self, content: str, url: str) -> ParseResult:
        """
        Parse content using template rules.

        Workflow:
        1. Find matching template for URL
        2. Extract content using template selectors
        3. Build structured result
        4. Return ParseResult

        Args:
            content: HTML content to parse
            url: Source URL of content

        Returns:
            ParseResult: Structured parsing result with title, content, metadata

        Raises:
            ExtractionError: If content extraction fails
            TemplateNotFoundError: If no template is found
        """
        try:
            # Save URL for media URL normalization
            self.current_url = url

            # Get template for this URL
            self.current_template = self.get_template_for_url(url)

            # Create result with template info
            result = ParseResult(
                parser_name="TemplateParser",
                template_name=self.current_template.get('name', 'Unknown')
            )

            # Extract content using template
            # NOTE: This is Phase 2.1 framework - actual extraction in Phase 2.2
            result.title = self._extract_title(content, url)
            result.content = self._extract_content(content, url)
            result.metadata = self._extract_metadata(content, url)

            result.success = True
            return result

        except TemplateNotFoundError as e:
            # No template found - return error result
            return ParseResult(
                success=False,
                errors=[str(e)],
                parser_name="TemplateParser"
            )

        except Exception as e:
            # Other errors
            return ParseResult(
                success=False,
                errors=[f"Extraction error: {str(e)}"],
                parser_name="TemplateParser"
            )

    def _extract_title(self, content: str, url: str) -> str:
        """
        Extract title from content using template rules.

        Tries template selectors first, then falls back to default <title> tag.

        Args:
            content: HTML content
            url: Source URL

        Returns:
            str: Extracted title or empty string
        """
        title = None

        # Try template selectors if available
        if self.current_template and 'selectors' in self.current_template:
            selectors = self.current_template['selectors']
            if 'title' in selectors:
                title = self._extract_field(content, selectors['title'])

        # Fallback to default <title> tag if no template result
        if not title:
            try:
                title = self._extract_field(content, 'title')
            except Exception as e:
                self.logger.debug(f"Fallback title extraction failed: {e}")

        return title or ""

    def _extract_content(self, content: str, url: str) -> str:
        """
        Extract main content from HTML using template rules.

        Extracts HTML content using template selectors and converts to Markdown.

        Args:
            content: HTML content
            url: Source URL

        Returns:
            str: Extracted content in markdown format or empty string
        """
        html_content = None

        # Try template selectors if available - need to extract HTML, not text
        if self.current_template and 'selectors' in self.current_template:
            selectors = self.current_template['selectors']
            if 'content' in selectors:
                # Extract HTML by finding the element and getting its inner HTML
                html_content = self._extract_html(content, selectors['content'])

        # If no content extracted, return empty string
        if not html_content:
            return ""

        # Check if this is Google Search - use custom processor BEFORE post-processing
        if (self.current_template and
            self.current_template.get('name') == 'Google Search Template'):
            try:
                from .google_search_processor import process_google_search
                markdown = process_google_search(html_content, url)
                return markdown
            except Exception as e:
                self.logger.warning(f"Google Search custom processor failed: {e}, falling back to standard processing")
                # Fall through to standard processing

        # Pre-process HTML to handle lazy-loaded images and remove unwanted elements
        # This is needed for WeChat and other sites that use lazy loading
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script, style, and noscript tags (especially important for XHS)
            for tag in soup.find_all(['script', 'style', 'noscript']):
                tag.decompose()

            # Apply post_processing.remove_elements rules from template
            if self.current_template and 'post_processing' in self.current_template:
                remove_elements = self.current_template['post_processing'].get('remove_elements', [])
                for remove_rule in remove_elements:
                    if not isinstance(remove_rule, dict):
                        continue

                    selector = remove_rule.get('selector', '')
                    strategy = remove_rule.get('strategy', 'css')

                    if not selector:
                        continue

                    try:
                        # Currently only support CSS selector strategy for removal
                        if strategy == 'css':
                            elements_to_remove = soup.select(selector)
                            for element in elements_to_remove:
                                element.decompose()
                            if elements_to_remove:
                                self.logger.debug(f"Removed {len(elements_to_remove)} elements matching '{selector}'")
                        elif strategy == 'tag':
                            # Tag strategy: remove all tags of given type
                            for tag in soup.find_all(selector):
                                tag.decompose()
                    except Exception as e:
                        self.logger.debug(f"Failed to remove elements with selector '{selector}': {e}")

            # Find all img tags with data-src attribute
            for img in soup.find_all('img'):
                data_src = img.get('data-src')
                if data_src and not img.get('src'):
                    # Copy data-src to src so html2text can pick it up
                    img['src'] = data_src

            # Normalize all image src URLs to absolute URLs
            from webfetcher.core import normalize_media_url
            for img in soup.find_all('img'):
                src = img.get('src')
                if src:
                    # Normalize URL using base URL from self.current_url
                    normalized_src = normalize_media_url(src, url)
                    img['src'] = normalized_src

            # Normalize all link href URLs to absolute URLs (fix relative links like /search?...)
            for link in soup.find_all('a'):
                href = link.get('href')
                if href:
                    # Normalize URL using base URL
                    normalized_href = normalize_media_url(href, url)
                    link['href'] = normalized_href

            # Enhanced table handling for better markdown conversion
            tables_found = soup.find_all('table')
            for table in tables_found:
                # Fix 1: Replace <br> in table headers with space
                # This prevents headers from splitting across multiple lines
                for th in table.find_all('th'):
                    for br in th.find_all('br'):
                        br.replace_with(' ')

                for td in table.find_all('td'):
                    # Fix 2: Replace <br> in table cells
                    for br in td.find_all('br'):
                        br.replace_with(' ')

                    # Fix 3: Replace empty cells with radio/checkbox inputs with placeholder
                    # Check if cell contains only form inputs and whitespace
                    inputs = td.find_all('input', type=['radio', 'checkbox'])
                    if inputs:
                        # Get cell text without the input tags
                        cell_text = td.get_text(strip=True)
                        # If cell is essentially empty (only whitespace/nbsp), add placeholder
                        if not cell_text or cell_text.replace('\xa0', '').strip() == '':
                            # Clear the cell and add a simple placeholder
                            td.clear()
                            td.string = '[ ]'

            # Update html_content with processed version
            html_content = str(soup)
        except Exception as e:
            self.logger.debug(f"HTML pre-processing failed: {e}, continuing with original HTML")

        # Convert HTML to Markdown
        try:
            # Note: Google Search Template is handled earlier before post-processing
            markdown = self.html_converter.handle(html_content)

            # Post-processing: Remove base64 data URLs from markdown
            # This catches any that slipped through BeautifulSoup processing
            import re
            # Remove markdown image syntax with data URLs: ![alt](data:image/...)
            markdown = re.sub(r'!\[([^\]]*)\]\(data:image/[^)]+\)', r'', markdown)
            # Remove any standalone data:image URLs
            markdown = re.sub(r'data:image/[^\s)]+', '', markdown)

            # Clean up excessive whitespace
            markdown = '\n'.join(line.rstrip() for line in markdown.split('\n'))
            # Remove multiple consecutive blank lines
            while '\n\n\n' in markdown:
                markdown = markdown.replace('\n\n\n', '\n\n')

            # Apply markdown post-processing from template
            if self.current_template and 'post_processing' in self.current_template:
                markdown_rules = self.current_template['post_processing'].get('markdown', [])
                markdown = self._apply_post_process(markdown, markdown_rules)

            return markdown.strip()
        except Exception as e:
            self.logger.error(f"Markdown conversion failed: {e}")
            # Return raw HTML as fallback
            return html_content

    def _extract_html(self, content: str, selector_config: Any) -> Optional[str]:
        """
        Extract HTML content (not text) from elements.

        Supports multiple selector formats:
        - String: "#id, .class"
        - List of dicts: [{"selector": "#id", "strategy": "css"}]
        - Single dict: {"selector": "#id", "strategy": "css"}

        Args:
            content: HTML content to extract from
            selector_config: Selector configuration in any supported format

        Returns:
            Optional[str]: Extracted HTML or None if not found
        """
        from bs4 import BeautifulSoup

        # Normalize configuration to list of (selector, strategy, options) tuples
        selectors = self._normalize_selector_config(selector_config)

        if not selectors:
            return None

        for selector, strategy_type, options in selectors:
            try:
                # Currently only CSS strategy is supported for HTML extraction
                # (BeautifulSoup's select_one uses CSS selectors)
                if strategy_type != 'css':
                    self.logger.debug(f"HTML extraction only supports CSS selectors, got: {strategy_type}")
                    continue

                # Parse HTML
                soup = BeautifulSoup(content, 'html.parser')

                # Check if multiple matches are requested
                if options.get('multiple'):
                    # Find all elements
                    elements = soup.select(selector)
                    if elements:
                        # Join all found elements
                        return "\n".join(str(el) for el in elements)
                else:
                    # Find element using CSS selector (default behavior)
                    element = soup.select_one(selector)
                    if element:
                        # Return inner HTML (all children as HTML string)
                        return str(element)

            except Exception as e:
                self.logger.debug(f"HTML extraction with selector '{selector}' (strategy: {strategy_type}) failed: {e}")
                continue

        return None

    def _extract_list(self, content: str, field_config: Any) -> List[str]:
        """
        Extract multiple values (e.g., images, links) using configured selectors.

        Args:
            content: HTML content to extract from
            field_config: Field configuration in any supported format

        Returns:
            List[str]: List of extracted values (validated URLs or text)
        """
        from bs4 import BeautifulSoup
        import re

        results = []

        # Use _normalize_selector_config to handle all formats consistent with other methods
        # This returns list of (selector, strategy, options)
        selectors = self._normalize_selector_config(field_config)

        if not selectors:
            return []

        # Preprocess HTML once before all extractions
        try:
            soup = BeautifulSoup(content, 'html.parser')

            # Remove script, style, and noscript tags (prevent JS code extraction)
            for tag in soup.find_all(['script', 'style', 'noscript']):
                tag.decompose()

            # Convert data-src to src for lazy-loaded images
            for img in soup.find_all('img'):
                data_src = img.get('data-src')
                if data_src and not img.get('src'):
                    img['src'] = data_src

            preprocessed_content = str(soup)
        except Exception as e:
            self.logger.debug(f"HTML preprocessing failed in _extract_list: {e}")
            preprocessed_content = content

        # Process each configuration item
        for selector, strategy_type, options in selectors:
            attribute = options.get('attribute')
            validation = options.get('validation', {})

            if not selector:
                continue

            try:
                # Parse preprocessed HTML
                soup = BeautifulSoup(preprocessed_content, 'html.parser')

                # Find all matching elements
                # List extraction inherently implies multiple matches, so we always use select()
                elements = soup.select(selector)

                for element in elements:
                    value = None

                    if attribute:
                        # Extract attribute value
                        value = element.get(attribute)
                    else:
                        # Extract text content
                        value = element.get_text(strip=True)

                    if not value or value in results:
                        continue

                    # Validate URLs (for images, links, etc.)
                    if self._should_validate_url(value):
                        if not self._validate_url(value, validation):
                            continue

                    results.append(value)

            except Exception as e:
                self.logger.debug(f"List extraction with selector '{selector}' failed: {e}")
                continue

        # Normalize media URLs if we have a current URL
        if hasattr(self, 'current_url') and self.current_url:
            from webfetcher.core import normalize_media_url
            results = [normalize_media_url(url, self.current_url) for url in results]

        return results

    def _should_validate_url(self, value: str) -> bool:
        """Check if value looks like a URL that needs validation."""
        if not value:
            return False
        return value.startswith('http://') or value.startswith('https://') or value.startswith('//') or value.startswith('data:')

    def _validate_url(self, url: str, validation: Dict[str, Any]) -> bool:
        """
        Validate URL against validation rules.

        Args:
            url: URL to validate
            validation: Validation rules dict

        Returns:
            bool: True if URL passes validation, False otherwise
        """
        import re

        # Filter out JavaScript code disguised as URLs
        # JavaScript keywords that shouldn't appear in image URLs
        js_keywords = [
            'function', 'window', 'document', 'var ', 'let ', 'const ',
            '=>', 'localStorage', 'JSON.', '.push(', '.forEach(',
            'return ', 'if(', 'for(', '!function', 'void 0'
        ]

        for keyword in js_keywords:
            if keyword in url:
                self.logger.debug(f"Filtered JavaScript code as URL: {url[:100]}")
                return False

        # Filter out data URLs (base64 images can be kept, but very long ones filtered)
        if url.startswith('data:'):
            # Allow small data URLs (like icons), filter large ones
            if len(url) > 500:
                self.logger.debug(f"Filtered large data URL: {len(url)} bytes")
                return False

        # Domain validation
        domain_contains = validation.get('domain_contains', [])
        if domain_contains:
            # Check if URL contains any of the required domains
            if not any(domain in url for domain in domain_contains):
                self.logger.debug(f"URL failed domain validation: {url[:100]}")
                return False

        # Exclude patterns
        exclude_patterns = validation.get('exclude_patterns', [])
        for pattern in exclude_patterns:
            if pattern in url.lower():
                self.logger.debug(f"URL matches exclude pattern '{pattern}': {url[:100]}")
                return False

        # URL patterns (must match at least one if specified)
        url_patterns = validation.get('url_patterns', [])
        if url_patterns:
            if not any(re.search(pattern, url) for pattern in url_patterns):
                self.logger.debug(f"URL failed pattern validation: {url[:100]}")
                return False

        return True

    def _extract_metadata(self, content: str, url: str) -> Dict[str, Any]:
        """
        Extract metadata using template rules.

        Extracts structured metadata fields like description, author, date, etc.
        Also extracts top-level selector fields (author, date, images) for compatibility.

        Args:
            content: HTML content
            url: Source URL

        Returns:
            Dict[str, Any]: Metadata dictionary
        """
        metadata = {
            'source_url': url,
            'template_name': self.current_template.get('name') if self.current_template else None,
            'template_version': self.current_template.get('version') if self.current_template else None
        }

        # Extract metadata fields from template
        if self.current_template and 'selectors' in self.current_template:
            selectors = self.current_template['selectors']

            # Extract from selectors.metadata dict if exists
            if 'metadata' in selectors and isinstance(selectors['metadata'], dict):
                # Extract each metadata field
                for field_name, field_selector in selectors['metadata'].items():
                    try:
                        value = self._extract_field(content, field_selector)
                        if value:
                            metadata[field_name] = value
                    except Exception as e:
                        self.logger.debug(f"Failed to extract metadata field '{field_name}': {e}")
                        continue

            # Also extract top-level selector fields for compatibility
            # (author, date, images, videos, etc.)
            top_level_fields = ['author', 'date', 'images', 'videos']
            for field_name in top_level_fields:
                if field_name in selectors:
                    try:
                        if field_name == 'images':
                            # Images need to extract all matching elements
                            images = self._extract_list(content, selectors['images'])
                            if images:
                                metadata['images'] = images
                        elif field_name == 'videos':
                            # Videos need to extract all matching elements
                            videos = self._extract_list(content, selectors['videos'])
                            if videos:
                                metadata['videos'] = videos
                        else:
                            # Single value fields
                            value = self._extract_field(content, selectors[field_name])
                            if value:
                                metadata[field_name] = value
                    except Exception as e:
                        self.logger.debug(f"Failed to extract top-level field '{field_name}': {e}")
                        continue

        return metadata

    def validate(self, result: ParseResult) -> bool:
        """
        Validate parsing result.

        Checks:
        - Result is not None
        - Has template name set
        - No critical errors

        Phase 2.1 Implementation: Basic validation
        Phase 2.2+ Will implement: Content quality validation

        Args:
            result: ParseResult to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if result is None:
            return False

        # Must have template name
        if not result.template_name:
            return False

        # Must be successful
        if not result.success:
            return False

        # Phase 2.2+: Validate content quality (min length, required fields, etc.)

        return True

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get parser metadata.

        Returns:
            Dict[str, Any]: Parser information including:
                - parser_name: Name of this parser
                - version: Parser version
                - templates_loaded: Number of loaded templates
                - current_template: Current active template name
                - supported_features: List of supported features
        """
        return {
            'parser_name': 'TemplateParser',
            'version': '1.0.0',
            'templates_loaded': len(self.template_loader.list_templates()),
            'current_template': self.current_template.get('name') if self.current_template else None,
            'supported_features': [
                'template_matching',
                'url_pattern_matching',
                'fallback_to_generic',
                'template_caching'
            ]
        }

    def list_available_templates(self) -> list[str]:
        """
        List all available template names.

        Returns:
            list[str]: List of template names
        """
        return self.template_loader.list_templates()

    def reload_templates(self):
        """
        Reload all templates from disk.

        This is useful when templates are updated during runtime.
        Clears the template cache and reinitializes the loader.
        """
        self.template_cache.clear()
        self.current_template = None
        self.template_loader._load_all_templates()
