"""Text pattern (regex) extraction strategy.

This module implements the ExtractionStrategy interface using regular expressions
for pattern-based text extraction.
"""

from typing import Optional, List, Pattern
import logging
import re

from .base_strategy import (
    ExtractionStrategy,
    StrategyError,
    SelectionError,
    ExtractionError
)

# Setup logger
logger = logging.getLogger(__name__)


class TextPatternStrategy(ExtractionStrategy):
    """
    Regular expression-based text extraction strategy.

    This strategy uses Python's re module to extract content from text using
    regex patterns. It supports:
    - Standard regex patterns with groups
    - Single match extraction with extract()
    - Multiple match extraction with extract_all()
    - Multiline matching with MULTILINE and DOTALL flags
    - Named and numbered capture groups
    - Robust error handling with logging

    Example:
        strategy = TextPatternStrategy()

        # Extract single match
        email = strategy.extract(text, r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

        # Extract with groups
        price = strategy.extract(text, r'Price:\s*\$?(\d+\.?\d*)')

        # Extract all matches
        urls = strategy.extract_all(text, r'https?://[^\s]+')

        # Multiline matching
        code_block = strategy.extract(text, r'```python\n(.*?)\n```', multiline=True)
    """

    def __init__(self, flags: int = 0):
        """
        Initialize text pattern strategy.

        Args:
            flags: Default regex flags to use (e.g., re.IGNORECASE, re.MULTILINE)
        """
        super().__init__()
        self.default_flags = flags
        logger.debug(f"TextPatternStrategy initialized with flags: {flags}")

    def _compile_pattern(self, pattern: str, flags: Optional[int] = None) -> Pattern:
        """
        Compile regex pattern with flags.

        Args:
            pattern: Regular expression pattern
            flags: Optional regex flags (uses default_flags if not specified)

        Returns:
            Pattern: Compiled regex pattern

        Raises:
            SelectionError: If pattern compilation fails
        """
        try:
            use_flags = flags if flags is not None else self.default_flags
            compiled = re.compile(pattern, use_flags)
            return compiled

        except re.error as e:
            logger.error(f"Invalid regex pattern '{pattern}': {e}")
            raise SelectionError(f"Invalid regex pattern: {e}")

    def _extract_from_match(self, match: re.Match) -> str:
        """
        Extract text from regex match object.

        If the pattern has groups, returns the first group.
        Otherwise, returns the entire match.

        Args:
            match: Regex match object

        Returns:
            str: Extracted text from match
        """
        if match is None:
            return ""

        # If pattern has groups, return first group
        if match.groups():
            # Return first non-None group
            for group in match.groups():
                if group is not None:
                    return group.strip()
            return ""

        # Otherwise return entire match
        return match.group(0).strip()

    def extract(
        self,
        content: str,
        selector: str,
        multiline: bool = False,
        ignore_case: bool = False
    ) -> Optional[str]:
        """
        Extract first match from content using regex pattern.

        The pattern can include capture groups to extract specific parts:
        - No groups: Returns entire match
        - With groups: Returns first non-None group

        Args:
            content: Text content to extract from
            selector: Regular expression pattern
            multiline: Enable multiline mode (. matches newlines)
            ignore_case: Enable case-insensitive matching

        Returns:
            Optional[str]: Extracted text, or None if not found

        Raises:
            StrategyError: If content is invalid
            SelectionError: If regex pattern is invalid

        Example:
            >>> strategy = TextPatternStrategy()
            >>> text = 'Price: $19.99'
            >>> strategy.extract(text, r'Price:\s*\$?(\d+\.?\d*)')
            '19.99'
            >>> text = 'Email: user@example.com'
            >>> strategy.extract(text, r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
            'user@example.com'
        """
        try:
            # Validate selector
            if not self.validate_selector(selector):
                raise SelectionError(f"Invalid regex pattern: '{selector}'")

            # Validate content
            if content is None:
                raise StrategyError("Content is None")

            # Build flags
            flags = self.default_flags
            if multiline:
                flags |= re.MULTILINE | re.DOTALL
            if ignore_case:
                flags |= re.IGNORECASE

            # Compile pattern
            pattern = self._compile_pattern(selector, flags)

            # Search for match
            match = pattern.search(content)

            if match is None:
                logger.debug(f"No match found for pattern: '{selector}'")
                return None

            # Extract text from match
            text = self._extract_from_match(match)
            logger.debug(f"Extracted text: '{text[:50]}...'")

            return text if text else None

        except (StrategyError, SelectionError):
            # Re-raise our custom exceptions
            raise

        except Exception as e:
            logger.error(f"Extraction failed for pattern '{selector}': {e}")
            # Don't raise - return None to allow graceful degradation
            return None

    def extract_all(
        self,
        content: str,
        selector: str,
        multiline: bool = False,
        ignore_case: bool = False
    ) -> List[str]:
        """
        Extract all matches from content using regex pattern.

        The pattern can include capture groups to extract specific parts:
        - No groups: Returns all entire matches
        - With groups: Returns first non-None group from each match

        Args:
            content: Text content to extract from
            selector: Regular expression pattern
            multiline: Enable multiline mode (. matches newlines)
            ignore_case: Enable case-insensitive matching

        Returns:
            List[str]: List of extracted text (empty list if no matches)

        Raises:
            StrategyError: If content is invalid
            SelectionError: If regex pattern is invalid

        Example:
            >>> strategy = TextPatternStrategy()
            >>> text = 'Prices: $10, $20, $30'
            >>> strategy.extract_all(text, r'\$(\d+)')
            ['10', '20', '30']
            >>> text = 'Emails: alice@ex.com bob@ex.com'
            >>> strategy.extract_all(text, r'[a-z]+@[a-z]+\.[a-z]+')
            ['alice@ex.com', 'bob@ex.com']
        """
        try:
            # Validate selector
            if not self.validate_selector(selector):
                raise SelectionError(f"Invalid regex pattern: '{selector}'")

            # Validate content
            if content is None:
                raise StrategyError("Content is None")

            # Build flags
            flags = self.default_flags
            if multiline:
                flags |= re.MULTILINE | re.DOTALL
            if ignore_case:
                flags |= re.IGNORECASE

            # Compile pattern
            pattern = self._compile_pattern(selector, flags)

            # Find all matches
            matches = pattern.finditer(content)

            # Extract text from all matches
            results = []
            for match in matches:
                text = self._extract_from_match(match)
                if text:  # Only include non-empty values
                    results.append(text)

            logger.debug(f"Extracted {len(results)} matches for pattern '{selector}'")
            return results

        except (StrategyError, SelectionError):
            # Re-raise our custom exceptions
            raise

        except Exception as e:
            logger.error(f"Extraction failed for pattern '{selector}': {e}")
            # Don't raise - return empty list to allow graceful degradation
            return []

    def extract_named_groups(
        self,
        content: str,
        selector: str,
        multiline: bool = False,
        ignore_case: bool = False
    ) -> Optional[dict]:
        """
        Extract named groups from first match.

        This is a specialized method for extracting multiple named capture groups
        from a single match.

        Args:
            content: Text content to extract from
            selector: Regular expression pattern with named groups
            multiline: Enable multiline mode
            ignore_case: Enable case-insensitive matching

        Returns:
            Optional[dict]: Dictionary of named groups, or None if no match

        Example:
            >>> strategy = TextPatternStrategy()
            >>> text = 'User: John Doe, Age: 30'
            >>> pattern = r'User:\s*(?P<name>[^,]+),\s*Age:\s*(?P<age>\d+)'
            >>> strategy.extract_named_groups(text, pattern)
            {'name': 'John Doe', 'age': '30'}
        """
        try:
            # Build flags
            flags = self.default_flags
            if multiline:
                flags |= re.MULTILINE | re.DOTALL
            if ignore_case:
                flags |= re.IGNORECASE

            # Compile pattern
            pattern = self._compile_pattern(selector, flags)

            # Search for match
            match = pattern.search(content)

            if match is None:
                logger.debug(f"No match found for pattern: '{selector}'")
                return None

            # Extract named groups
            groups = match.groupdict()
            logger.debug(f"Extracted named groups: {groups}")

            return groups if groups else None

        except Exception as e:
            logger.error(f"Named group extraction failed for pattern '{selector}': {e}")
            return None

    def extract_all_named_groups(
        self,
        content: str,
        selector: str,
        multiline: bool = False,
        ignore_case: bool = False
    ) -> List[dict]:
        """
        Extract named groups from all matches.

        This is a specialized method for extracting multiple named capture groups
        from all matches.

        Args:
            content: Text content to extract from
            selector: Regular expression pattern with named groups
            multiline: Enable multiline mode
            ignore_case: Enable case-insensitive matching

        Returns:
            List[dict]: List of dictionaries with named groups (empty if no matches)

        Example:
            >>> strategy = TextPatternStrategy()
            >>> text = 'User: Alice, Age: 25\\nUser: Bob, Age: 30'
            >>> pattern = r'User:\s*(?P<name>[^,]+),\s*Age:\s*(?P<age>\d+)'
            >>> strategy.extract_all_named_groups(text, pattern)
            [{'name': 'Alice', 'age': '25'}, {'name': 'Bob', 'age': '30'}]
        """
        try:
            # Build flags
            flags = self.default_flags
            if multiline:
                flags |= re.MULTILINE | re.DOTALL
            if ignore_case:
                flags |= re.IGNORECASE

            # Compile pattern
            pattern = self._compile_pattern(selector, flags)

            # Find all matches
            matches = pattern.finditer(content)

            # Extract named groups from all matches
            results = []
            for match in matches:
                groups = match.groupdict()
                if groups:
                    results.append(groups)

            logger.debug(f"Extracted {len(results)} named group sets for pattern '{selector}'")
            return results

        except Exception as e:
            logger.error(f"Named group extraction failed for pattern '{selector}': {e}")
            return []

    def validate_selector(self, selector: str) -> bool:
        """
        Validate regex pattern syntax.

        Performs basic validation by attempting to compile the pattern.

        Args:
            selector: Regular expression pattern to validate

        Returns:
            bool: True if pattern is valid, False otherwise
        """
        if not super().validate_selector(selector):
            return False

        try:
            # Try to compile the pattern
            re.compile(selector)
            return True

        except re.error as e:
            logger.warning(f"Invalid regex pattern '{selector}': {e}")
            return False

    def __repr__(self) -> str:
        """String representation of strategy."""
        flag_names = []
        if self.default_flags & re.IGNORECASE:
            flag_names.append('IGNORECASE')
        if self.default_flags & re.MULTILINE:
            flag_names.append('MULTILINE')
        if self.default_flags & re.DOTALL:
            flag_names.append('DOTALL')

        flags_str = '|'.join(flag_names) if flag_names else 'None'
        return f"TextPatternStrategy(flags={flags_str})"
