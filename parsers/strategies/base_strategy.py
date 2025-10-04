"""Base strategy abstract class for content extraction.

This module defines the abstract base class that all extraction strategies must implement.
It provides the interface contract for extracting content from HTML using different methods
(CSS selectors, XPath, regex, etc.).
"""

from abc import ABC, abstractmethod
from typing import Optional, List
import logging

# Setup logger
logger = logging.getLogger(__name__)


# Custom Exceptions
class StrategyError(Exception):
    """Base exception for strategy errors."""
    pass


class SelectionError(StrategyError):
    """Exception raised when element selection fails."""
    pass


class ExtractionError(StrategyError):
    """Exception raised when content extraction fails."""
    pass


class ExtractionStrategy(ABC):
    """
    Abstract base class for all content extraction strategies.

    This class defines the interface that all extraction strategies must implement.
    Subclasses must implement extract() and extract_all() methods to provide
    specific extraction logic (CSS selectors, XPath, regex, etc.).

    The strategy follows a standard workflow:
    1. Parse content using the strategy's method
    2. Apply selector to find elements
    3. Extract text or attributes from matched elements
    4. Return extracted content

    Example:
        class CSSStrategy(ExtractionStrategy):
            def extract(self, content: str, selector: str) -> Optional[str]:
                # Use BeautifulSoup with CSS selectors
                soup = BeautifulSoup(content, 'html.parser')
                element = soup.select_one(selector)
                return element.get_text(strip=True) if element else None

            def extract_all(self, content: str, selector: str) -> List[str]:
                soup = BeautifulSoup(content, 'html.parser')
                elements = soup.select(selector)
                return [e.get_text(strip=True) for e in elements]
    """

    def __init__(self):
        """Initialize extraction strategy."""
        self._name = self.__class__.__name__
        logger.debug(f"Initialized {self._name}")

    @abstractmethod
    def extract(self, content: str, selector: str) -> Optional[str]:
        """
        Extract a single element from content using selector.

        This method should find the first matching element and return its content.
        If no element matches, it should return None instead of raising an exception.

        Args:
            content: HTML or text content to extract from
            selector: Selector expression (CSS, XPath, regex, etc.)

        Returns:
            Optional[str]: Extracted text content, or None if not found

        Raises:
            StrategyError: If extraction process fails (invalid content, etc.)
            SelectionError: If selector is invalid or malformed
        """
        pass

    @abstractmethod
    def extract_all(self, content: str, selector: str) -> List[str]:
        """
        Extract all matching elements from content using selector.

        This method should find all matching elements and return their content as a list.
        If no elements match, it should return an empty list instead of raising an exception.

        Args:
            content: HTML or text content to extract from
            selector: Selector expression (CSS, XPath, regex, etc.)

        Returns:
            List[str]: List of extracted text content (empty list if no matches)

        Raises:
            StrategyError: If extraction process fails (invalid content, etc.)
            SelectionError: If selector is invalid or malformed
        """
        pass

    def extract_attribute(self, content: str, selector: str, attribute: str) -> Optional[str]:
        """
        Extract a specific attribute from the first matching element.

        This is a convenience method that can be overridden by subclasses.
        Default implementation raises NotImplementedError.

        Args:
            content: HTML content to extract from
            selector: Selector expression
            attribute: Attribute name to extract (e.g., 'href', 'src')

        Returns:
            Optional[str]: Attribute value, or None if not found

        Raises:
            NotImplementedError: If strategy doesn't support attribute extraction
        """
        raise NotImplementedError(
            f"{self._name} does not support attribute extraction. "
            "Override extract_attribute() to implement this feature."
        )

    def extract_all_attributes(
        self, content: str, selector: str, attribute: str
    ) -> List[str]:
        """
        Extract a specific attribute from all matching elements.

        This is a convenience method that can be overridden by subclasses.
        Default implementation raises NotImplementedError.

        Args:
            content: HTML content to extract from
            selector: Selector expression
            attribute: Attribute name to extract (e.g., 'href', 'src')

        Returns:
            List[str]: List of attribute values (empty list if no matches)

        Raises:
            NotImplementedError: If strategy doesn't support attribute extraction
        """
        raise NotImplementedError(
            f"{self._name} does not support attribute extraction. "
            "Override extract_all_attributes() to implement this feature."
        )

    def validate_selector(self, selector: str) -> bool:
        """
        Validate selector syntax (optional).

        Subclasses can override this to provide selector validation.
        Default implementation accepts all selectors.

        Args:
            selector: Selector expression to validate

        Returns:
            bool: True if selector is valid, False otherwise
        """
        return bool(selector and selector.strip())

    def __repr__(self) -> str:
        """String representation of strategy."""
        return f"{self._name}()"
