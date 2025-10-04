"""XPath selector extraction strategy.

This module implements the ExtractionStrategy interface using XPath expressions
and lxml for HTML parsing and element selection.
"""

from typing import Optional, List
import logging
from lxml import html, etree
from lxml.html import HtmlElement

from .base_strategy import (
    ExtractionStrategy,
    StrategyError,
    SelectionError,
    ExtractionError
)

# Setup logger
logger = logging.getLogger(__name__)


class XPathStrategy(ExtractionStrategy):
    """
    XPath expression-based extraction strategy.

    This strategy uses lxml's XPath support to extract content from HTML documents.
    It supports:
    - Standard XPath expressions (//tag, //tag[@attr='value'], etc.)
    - Attribute extraction using /@attribute syntax (e.g., "//a/@href")
    - Text extraction using /text() (explicit) or default text_content()
    - Multiple element extraction with extract_all()
    - Namespace handling
    - Robust error handling with logging

    Example:
        strategy = XPathStrategy()

        # Extract text
        title = strategy.extract(html, "//h1[@class='title']")

        # Extract attribute directly in XPath
        link = strategy.extract(html, "//a[@class='main-link']/@href")

        # Extract all elements
        paragraphs = strategy.extract_all(html, "//p[@class='content']")

        # Complex XPath with predicates
        first_item = strategy.extract(html, "//ul[@id='menu']/li[1]")
    """

    def __init__(self):
        """Initialize XPath strategy."""
        super().__init__()
        logger.debug("XPathStrategy initialized")

    def _parse_html(self, content: str) -> HtmlElement:
        """
        Parse HTML content into lxml element tree.

        Args:
            content: HTML string to parse

        Returns:
            HtmlElement: Parsed HTML tree

        Raises:
            StrategyError: If HTML parsing fails
        """
        try:
            if not content or not content.strip():
                raise StrategyError("Content is empty or None")

            # Use html.fromstring for HTML content
            tree = html.fromstring(content)
            return tree

        except etree.ParserError as e:
            logger.error(f"Failed to parse HTML with lxml: {e}")
            raise StrategyError(f"HTML parsing failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during HTML parsing: {e}")
            raise StrategyError(f"HTML parsing failed: {e}")

    def _is_attribute_xpath(self, xpath_expr: str) -> bool:
        """
        Check if XPath expression ends with attribute selector.

        Examples:
            "//a/@href" -> True
            "//img/@src" -> True
            "//div[@id='test']" -> False
            "//p/text()" -> False

        Args:
            xpath_expr: XPath expression to check

        Returns:
            bool: True if expression selects an attribute
        """
        # Check if XPath ends with /@attribute
        import re
        return bool(re.search(r'/@[\w-]+\s*$', xpath_expr.strip()))

    def _is_text_xpath(self, xpath_expr: str) -> bool:
        """
        Check if XPath expression ends with text() selector.

        Examples:
            "//p/text()" -> True
            "//div[@id='test']/text()" -> True
            "//a/@href" -> False
            "//div" -> False

        Args:
            xpath_expr: XPath expression to check

        Returns:
            bool: True if expression selects text nodes
        """
        return xpath_expr.strip().endswith('/text()')

    def _extract_text(self, element) -> str:
        """
        Extract text content from element or text result.

        Args:
            element: lxml element, text string, or attribute value

        Returns:
            str: Extracted and cleaned text
        """
        if element is None:
            return ""

        # If it's already a string (from /@attr or /text())
        if isinstance(element, str):
            return element.strip()

        # If it's an HtmlElement, get all text content
        if isinstance(element, HtmlElement):
            text = element.text_content()
            return text.strip() if text else ""

        # For other types, convert to string
        return str(element).strip()

    def extract(self, content: str, selector: str) -> Optional[str]:
        """
        Extract first matching element from content using XPath expression.

        Supports multiple XPath patterns:
        - Element selection: "//h1" -> extracts text from first h1
        - Attribute selection: "//a/@href" -> extracts href attribute
        - Text nodes: "//p/text()" -> extracts first text node
        - Predicates: "//div[@class='content']" -> filters by attribute
        - Complex paths: "//ul[@id='menu']/li[1]/a" -> nested navigation

        Args:
            content: HTML content to extract from
            selector: XPath expression

        Returns:
            Optional[str]: Extracted content, or None if not found

        Raises:
            StrategyError: If content parsing fails
            SelectionError: If XPath expression is invalid

        Example:
            >>> strategy = XPathStrategy()
            >>> html = '<h1 class="title">Hello</h1>'
            >>> strategy.extract(html, "//h1[@class='title']")
            'Hello'
            >>> html = '<a href="/page">Link</a>'
            >>> strategy.extract(html, "//a/@href")
            '/page'
        """
        try:
            # Validate selector
            if not self.validate_selector(selector):
                raise SelectionError(f"Invalid XPath expression: '{selector}'")

            # Parse HTML
            tree = self._parse_html(content)

            # Apply XPath expression
            results = tree.xpath(selector)

            if not results:
                logger.debug(f"No element found for XPath: '{selector}'")
                return None

            # Get first result
            first_result = results[0]

            # Extract text
            text = self._extract_text(first_result)
            logger.debug(f"Extracted text: '{text[:50]}...'")

            return text if text else None

        except etree.XPathEvalError as e:
            logger.error(f"Invalid XPath expression '{selector}': {e}")
            raise SelectionError(f"Invalid XPath expression: {e}")

        except (StrategyError, SelectionError):
            # Re-raise our custom exceptions
            raise

        except Exception as e:
            logger.error(f"Extraction failed for XPath '{selector}': {e}")
            # Don't raise - return None to allow graceful degradation
            return None

    def extract_all(self, content: str, selector: str) -> List[str]:
        """
        Extract all matching elements from content using XPath expression.

        Supports multiple XPath patterns:
        - Elements: "//p" -> extracts text from all p tags
        - Attributes: "//a/@href" -> extracts all href attributes
        - Text nodes: "//p/text()" -> extracts all text nodes
        - Filtered: "//div[@class='item']" -> all matching divs

        Args:
            content: HTML content to extract from
            selector: XPath expression

        Returns:
            List[str]: List of extracted content (empty list if no matches)

        Raises:
            StrategyError: If content parsing fails
            SelectionError: If XPath expression is invalid

        Example:
            >>> strategy = XPathStrategy()
            >>> html = '<p>First</p><p>Second</p><p>Third</p>'
            >>> strategy.extract_all(html, "//p")
            ['First', 'Second', 'Third']
            >>> html = '<a href="/1">One</a><a href="/2">Two</a>'
            >>> strategy.extract_all(html, "//a/@href")
            ['/1', '/2']
        """
        try:
            # Validate selector
            if not self.validate_selector(selector):
                raise SelectionError(f"Invalid XPath expression: '{selector}'")

            # Parse HTML
            tree = self._parse_html(content)

            # Apply XPath expression
            results = tree.xpath(selector)

            if not results:
                logger.debug(f"No elements found for XPath: '{selector}'")
                return []

            # Extract text from all results
            texts = []
            for result in results:
                text = self._extract_text(result)
                if text:  # Only include non-empty values
                    texts.append(text)

            logger.debug(f"Extracted {len(texts)} elements for XPath '{selector}'")
            return texts

        except etree.XPathEvalError as e:
            logger.error(f"Invalid XPath expression '{selector}': {e}")
            raise SelectionError(f"Invalid XPath expression: {e}")

        except (StrategyError, SelectionError):
            # Re-raise our custom exceptions
            raise

        except Exception as e:
            logger.error(f"Extraction failed for XPath '{selector}': {e}")
            # Don't raise - return empty list to allow graceful degradation
            return []

    def extract_attribute(self, content: str, selector: str, attribute: str) -> Optional[str]:
        """
        Extract a specific attribute from the first matching element.

        This is a convenience method that constructs an XPath expression
        to extract the attribute.

        Args:
            content: HTML content to extract from
            selector: XPath expression for element selection
            attribute: Attribute name to extract

        Returns:
            Optional[str]: Attribute value, or None if not found

        Example:
            >>> strategy = XPathStrategy()
            >>> html = '<a href="/page" class="link">Link</a>'
            >>> strategy.extract_attribute(html, "//a[@class='link']", "href")
            '/page'
        """
        # Construct XPath with attribute selector
        # Handle case where selector already ends with /
        selector = selector.rstrip('/')
        xpath_with_attr = f"{selector}/@{attribute}"
        return self.extract(content, xpath_with_attr)

    def extract_all_attributes(
        self, content: str, selector: str, attribute: str
    ) -> List[str]:
        """
        Extract a specific attribute from all matching elements.

        This is a convenience method that constructs an XPath expression
        to extract the attribute from all matching elements.

        Args:
            content: HTML content to extract from
            selector: XPath expression for element selection
            attribute: Attribute name to extract

        Returns:
            List[str]: List of attribute values (empty list if no matches)

        Example:
            >>> strategy = XPathStrategy()
            >>> html = '<a href="/1">One</a><a href="/2">Two</a>'
            >>> strategy.extract_all_attributes(html, "//a", "href")
            ['/1', '/2']
        """
        # Construct XPath with attribute selector
        selector = selector.rstrip('/')
        xpath_with_attr = f"{selector}/@{attribute}"
        return self.extract_all(content, xpath_with_attr)

    def validate_selector(self, selector: str) -> bool:
        """
        Validate XPath expression syntax.

        Performs basic validation:
        - Selector is not empty
        - Selector starts with valid XPath indicator (/ or //)
        - Balanced brackets and parentheses

        Args:
            selector: XPath expression to validate

        Returns:
            bool: True if selector appears valid, False otherwise
        """
        if not super().validate_selector(selector):
            return False

        selector = selector.strip()

        # XPath should typically start with / or // or contain (
        # Allow expressions like "//div" or "(//div)[1]"
        if not (selector.startswith('/') or selector.startswith('(')):
            logger.warning(f"XPath should start with '/' or '//': '{selector}'")
            # Don't fail - some XPath expressions might be valid without //
            # But log a warning

        # Check balanced brackets
        if selector.count('[') != selector.count(']'):
            logger.warning(f"Unbalanced brackets in XPath: '{selector}'")
            return False

        if selector.count('(') != selector.count(')'):
            logger.warning(f"Unbalanced parentheses in XPath: '{selector}'")
            return False

        return True

    def __repr__(self) -> str:
        """String representation of strategy."""
        return "XPathStrategy()"
