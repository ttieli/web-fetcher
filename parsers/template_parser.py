"""Template-based parser implementation.

This module implements a parser that uses YAML templates to extract content
from web pages. It integrates with the TemplateLoader to match URLs to templates
and extract structured data based on template rules.
"""

from typing import Dict, Any, Optional
import html2text
from lxml import etree
from parsers.base_parser import (
    BaseParser,
    ParseResult,
    ParserError,
    ExtractionError,
    TemplateNotFoundError
)
from parsers.engine.template_loader import TemplateLoader
from parsers.strategies import CSSStrategy, XPathStrategy, TextPatternStrategy


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

    def _extract_field(self, content: str, field_config: Any) -> Optional[str]:
        """
        Extract a field using configured selectors with fallback support.

        Args:
            content: HTML content to extract from
            field_config: Field configuration (string selector or dict)

        Returns:
            Optional[str]: Extracted value or None if not found
        """
        # Handle string selector (simple case)
        if isinstance(field_config, str):
            selectors = [s.strip() for s in field_config.split(',')]
        # Handle dict configuration (for metadata fields)
        elif isinstance(field_config, dict):
            # This shouldn't happen for simple fields, but handle gracefully
            return None
        else:
            return None

        # Try each selector in order until one succeeds
        for selector in selectors:
            try:
                # Auto-append @content for meta tags if not specified
                if selector.startswith('meta[') and '@' not in selector:
                    selector = selector + '@content'

                # Detect strategy type
                strategy_type = self._detect_strategy(selector)
                strategy = self.strategies[strategy_type]

                # Extract using strategy
                result = strategy.extract(content, selector)

                # Return first non-empty result
                if result and result.strip():
                    return result.strip()

            except Exception as e:
                # Log and continue to next selector
                self.logger.debug(f"Selector '{selector}' failed: {e}")
                continue

        return None

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

        # Convert HTML to Markdown
        try:
            markdown = self.html_converter.handle(html_content)
            # Clean up excessive whitespace
            markdown = '\n'.join(line.rstrip() for line in markdown.split('\n'))
            # Remove multiple consecutive blank lines
            while '\n\n\n' in markdown:
                markdown = markdown.replace('\n\n\n', '\n\n')
            return markdown.strip()
        except Exception as e:
            self.logger.error(f"Markdown conversion failed: {e}")
            # Return raw HTML as fallback
            return html_content

    def _extract_html(self, content: str, selector_config: str) -> Optional[str]:
        """
        Extract HTML content (not text) from elements.

        Args:
            content: HTML content to extract from
            selector_config: Selector configuration string

        Returns:
            Optional[str]: Extracted HTML or None if not found
        """
        from bs4 import BeautifulSoup

        selectors = [s.strip() for s in selector_config.split(',')]

        for selector in selectors:
            try:
                # Parse HTML
                soup = BeautifulSoup(content, 'html.parser')

                # Find element using CSS selector
                element = soup.select_one(selector)

                if element:
                    # Return inner HTML (all children as HTML string)
                    return str(element)

            except Exception as e:
                self.logger.debug(f"HTML extraction with selector '{selector}' failed: {e}")
                continue

        return None

    def _extract_metadata(self, content: str, url: str) -> Dict[str, Any]:
        """
        Extract metadata using template rules.

        Extracts structured metadata fields like description, author, date, etc.

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
