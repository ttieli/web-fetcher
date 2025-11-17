"""CSS selector extraction strategy.

This module implements the ExtractionStrategy interface using CSS selectors
and BeautifulSoup for HTML parsing and element selection.
"""

from typing import Optional, List
import logging
from bs4 import BeautifulSoup, Tag
import re

from .base_strategy import (
    ExtractionStrategy,
    StrategyError,
    SelectionError,
    ExtractionError
)

# Setup logger
logger = logging.getLogger(__name__)


class CSSStrategy(ExtractionStrategy):
    """
    CSS selector-based extraction strategy.

    This strategy uses BeautifulSoup's CSS selector support to extract content
    from HTML documents. It supports:
    - Standard CSS selectors (tag, class, id, attribute selectors)
    - Attribute extraction using @attribute syntax (e.g., "a@href", "img@src")
    - Multiple element extraction with extract_all()
    - Robust error handling with logging

    Example:
        strategy = CSSStrategy()

        # Extract text
        title = strategy.extract(html, "h1.title")

        # Extract attribute
        link = strategy.extract(html, "a.main-link@href")

        # Extract all elements
        paragraphs = strategy.extract_all(html, "p.content")
    """

    def __init__(self, parser: str = 'html.parser'):
        """
        Initialize CSS strategy.

        Args:
            parser: BeautifulSoup parser to use ('html.parser', 'lxml', etc.)
        """
        super().__init__()
        self.parser = parser
        logger.debug(f"CSSStrategy initialized with parser: {parser}")

    def _parse_selector(self, selector: str) -> tuple[str, Optional[str]]:
        """
        Parse selector to extract CSS selector and optional attribute.

        Supports syntax: "selector@attribute" for attribute extraction.
        Examples:
            "a" -> ("a", None)
            "a@href" -> ("a", "href")
            "img.thumbnail@src" -> ("img.thumbnail", "src")

        Args:
            selector: Selector string (may include @attribute)

        Returns:
            tuple[str, Optional[str]]: (css_selector, attribute_name)
        """
        if '@' in selector:
            parts = selector.split('@', 1)
            css_selector = parts[0].strip()
            attribute = parts[1].strip()
            logger.debug(f"Parsed selector: CSS='{css_selector}', attribute='{attribute}'")
            return css_selector, attribute
        return selector.strip(), None

    def _parse_html(self, content: str) -> BeautifulSoup:
        """
        Parse HTML content into BeautifulSoup object.

        Args:
            content: HTML string to parse

        Returns:
            BeautifulSoup: Parsed HTML tree

        Raises:
            StrategyError: If HTML parsing fails
        """
        try:
            if not content or not content.strip():
                raise StrategyError("Content is empty or None")

            soup = BeautifulSoup(content, self.parser)
            return soup

        except Exception as e:
            logger.error(f"Failed to parse HTML: {e}")
            raise StrategyError(f"HTML parsing failed: {e}")

    def _extract_text(self, element: Tag) -> str:
        """
        Extract text content from element.

        Args:
            element: BeautifulSoup Tag element

        Returns:
            str: Extracted and cleaned text
        """
        if element is None:
            return ""
        return element.get_text(strip=True)

    def _extract_attr(self, element: Tag, attribute: str) -> str:
        """
        Extract attribute value from element.

        Args:
            element: BeautifulSoup Tag element
            attribute: Attribute name to extract

        Returns:
            str: Attribute value (empty string if not found)
        """
        if element is None:
            return ""
        value = element.get(attribute, '')
        return str(value) if value else ""

    def extract(self, content: str, selector: str) -> Optional[str]:
        """
        Extract first matching element from content using CSS selector.

        Supports attribute extraction using @attribute syntax:
        - "h1" -> extracts text from first h1
        - "a@href" -> extracts href attribute from first a tag
        - "img.thumbnail@src" -> extracts src from first img.thumbnail

        Args:
            content: HTML content to extract from
            selector: CSS selector (with optional @attribute)

        Returns:
            Optional[str]: Extracted content, or None if not found

        Raises:
            StrategyError: If content parsing fails
            SelectionError: If selector is invalid

        Example:
            >>> strategy = CSSStrategy()
            >>> html = '<h1 class="title">Hello</h1>'
            >>> strategy.extract(html, "h1.title")
            'Hello'
            >>> html = '<a href="/page">Link</a>'
            >>> strategy.extract(html, "a@href")
            '/page'
        """
        try:
            # Validate selector
            if not self.validate_selector(selector):
                raise SelectionError(f"Invalid selector: '{selector}'")

            # Parse selector
            css_selector, attribute = self._parse_selector(selector)

            # Parse HTML
            soup = self._parse_html(content)

            # Find first matching element
            element = soup.select_one(css_selector)

            if element is None:
                logger.debug(f"No element found for selector: '{css_selector}'")
                return None

            # Extract text or attribute
            if attribute:
                result = self._extract_attr(element, attribute)
                logger.debug(f"Extracted attribute '{attribute}': '{result[:50]}...'")
            else:
                result = self._extract_text(element)
                logger.debug(f"Extracted text: '{result[:50]}...'")

            return result if result else None

        except (StrategyError, SelectionError):
            # Re-raise our custom exceptions
            raise

        except Exception as e:
            logger.error(f"Extraction failed for selector '{selector}': {e}")
            # Don't raise - return None to allow graceful degradation
            return None

    def extract_all(self, content: str, selector: str) -> List[str]:
        """
        Extract all matching elements from content using CSS selector.

        Supports attribute extraction using @attribute syntax:
        - "p" -> extracts text from all p tags
        - "a@href" -> extracts href attributes from all a tags
        - "img@src" -> extracts src attributes from all img tags

        Args:
            content: HTML content to extract from
            selector: CSS selector (with optional @attribute)

        Returns:
            List[str]: List of extracted content (empty list if no matches)

        Raises:
            StrategyError: If content parsing fails
            SelectionError: If selector is invalid

        Example:
            >>> strategy = CSSStrategy()
            >>> html = '<p>First</p><p>Second</p><p>Third</p>'
            >>> strategy.extract_all(html, "p")
            ['First', 'Second', 'Third']
            >>> html = '<a href="/1">One</a><a href="/2">Two</a>'
            >>> strategy.extract_all(html, "a@href")
            ['/1', '/2']
        """
        try:
            # Validate selector
            if not self.validate_selector(selector):
                raise SelectionError(f"Invalid selector: '{selector}'")

            # Parse selector
            css_selector, attribute = self._parse_selector(selector)

            # Parse HTML
            soup = self._parse_html(content)

            # Find all matching elements
            elements = soup.select(css_selector)

            if not elements:
                logger.debug(f"No elements found for selector: '{css_selector}'")
                return []

            # Extract text or attributes
            results = []
            for element in elements:
                if attribute:
                    value = self._extract_attr(element, attribute)
                else:
                    value = self._extract_text(element)

                if value:  # Only include non-empty values
                    results.append(value)

            logger.debug(f"Extracted {len(results)} elements for selector '{css_selector}'")
            return results

        except (StrategyError, SelectionError):
            # Re-raise our custom exceptions
            raise

        except Exception as e:
            logger.error(f"Extraction failed for selector '{selector}': {e}")
            # Don't raise - return empty list to allow graceful degradation
            return []

    def extract_attribute(self, content: str, selector: str, attribute: str) -> Optional[str]:
        """
        Extract a specific attribute from the first matching element.

        This is a convenience method that's equivalent to using extract()
        with selector@attribute syntax.

        Args:
            content: HTML content to extract from
            selector: CSS selector
            attribute: Attribute name to extract

        Returns:
            Optional[str]: Attribute value, or None if not found

        Example:
            >>> strategy = CSSStrategy()
            >>> html = '<a href="/page" class="link">Link</a>'
            >>> strategy.extract_attribute(html, "a.link", "href")
            '/page'
        """
        combined_selector = f"{selector}@{attribute}"
        return self.extract(content, combined_selector)

    def extract_all_attributes(
        self, content: str, selector: str, attribute: str
    ) -> List[str]:
        """
        Extract a specific attribute from all matching elements.

        This is a convenience method that's equivalent to using extract_all()
        with selector@attribute syntax.

        Args:
            content: HTML content to extract from
            selector: CSS selector
            attribute: Attribute name to extract

        Returns:
            List[str]: List of attribute values (empty list if no matches)

        Example:
            >>> strategy = CSSStrategy()
            >>> html = '<a href="/1">One</a><a href="/2">Two</a>'
            >>> strategy.extract_all_attributes(html, "a", "href")
            ['/1', '/2']
        """
        combined_selector = f"{selector}@{attribute}"
        return self.extract_all(content, combined_selector)

    def validate_selector(self, selector: str) -> bool:
        """
        Validate CSS selector syntax.

        Performs basic validation:
        - Selector is not empty
        - Selector doesn't contain obvious syntax errors

        Args:
            selector: CSS selector to validate

        Returns:
            bool: True if selector appears valid, False otherwise
        """
        if not super().validate_selector(selector):
            return False

        # Parse out attribute part if present
        css_selector, _ = self._parse_selector(selector)

        # Basic syntax validation
        # Reject selectors with unbalanced brackets or invalid characters
        if css_selector.count('[') != css_selector.count(']'):
            logger.warning(f"Unbalanced brackets in selector: '{css_selector}'")
            return False

        if css_selector.count('(') != css_selector.count(')'):
            logger.warning(f"Unbalanced parentheses in selector: '{css_selector}'")
            return False

        return True

    def __repr__(self) -> str:
        """String representation of strategy."""
        return f"CSSStrategy(parser='{self.parser}')"
