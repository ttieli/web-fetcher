"""Base parser abstract class for web content parsing.

This module defines the abstract base class that all parsers must implement.
It provides the interface contract for parsing web content into structured data.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


# Custom Exceptions
class ParserError(Exception):
    """Base exception for parser errors."""
    pass


class ValidationError(ParserError):
    """Exception raised when validation fails."""
    pass


class ExtractionError(ParserError):
    """Exception raised when content extraction fails."""
    pass


class TemplateNotFoundError(ParserError):
    """Exception raised when no matching template is found."""
    pass


@dataclass
class ParseResult:
    """
    Structured result from parsing operation.

    Attributes:
        title: Extracted page title
        content: Main content in markdown format
        metadata: Additional metadata about the page
        success: Whether parsing was successful
        errors: List of errors encountered during parsing
        parser_name: Name of parser used
        template_name: Name of template used (if applicable)
        parse_time: Timestamp when parsing occurred
    """
    title: str = ""
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    errors: list[str] = field(default_factory=list)
    parser_name: str = ""
    template_name: Optional[str] = None
    parse_time: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'title': self.title,
            'content': self.content,
            'metadata': self.metadata,
            'success': self.success,
            'errors': self.errors,
            'parser_name': self.parser_name,
            'template_name': self.template_name,
            'parse_time': self.parse_time.isoformat()
        }


class BaseParser(ABC):
    """
    Abstract base class for all web content parsers.

    This class defines the interface that all parsers must implement.
    Subclasses must implement parse(), validate(), and get_metadata() methods.

    The parser follows a standard workflow:
    1. Parse content using parse() method
    2. Validate result using validate() method
    3. Return structured ParseResult

    Example:
        class MyParser(BaseParser):
            def parse(self, content: str, url: str) -> ParseResult:
                # Implementation here
                pass

            def validate(self, result: ParseResult) -> bool:
                # Validation logic here
                pass

            def get_metadata(self) -> Dict[str, Any]:
                return {"parser": "MyParser", "version": "1.0.0"}
    """

    def __init__(self):
        """Initialize base parser."""
        self._metadata = self._initialize_metadata()

    def _initialize_metadata(self) -> Dict[str, Any]:
        """Initialize parser metadata."""
        return {
            'parser_class': self.__class__.__name__,
            'created_at': datetime.now().isoformat()
        }

    @abstractmethod
    def parse(self, content: str, url: str) -> ParseResult:
        """
        Parse web content into structured data.

        This is the main parsing method that must be implemented by subclasses.
        It should extract title, content, and metadata from the HTML content.

        Args:
            content: HTML content to parse
            url: Source URL of the content

        Returns:
            ParseResult: Structured parsing result

        Raises:
            ParserError: If parsing fails
            ExtractionError: If content extraction fails
        """
        pass

    @abstractmethod
    def validate(self, result: ParseResult) -> bool:
        """
        Validate parsing result.

        Checks if the parsed result meets quality standards.
        Should verify that required fields are present and valid.

        Args:
            result: ParseResult to validate

        Returns:
            bool: True if valid, False otherwise

        Raises:
            ValidationError: If validation fails critically
        """
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get parser metadata.

        Returns information about the parser including:
        - Parser name and version
        - Supported features
        - Configuration details

        Returns:
            Dict[str, Any]: Parser metadata
        """
        pass

    def preprocess(self, content: str, url: str) -> str:
        """
        Preprocess content before parsing (optional).

        Subclasses can override this to perform preprocessing.
        Default implementation returns content unchanged.

        Args:
            content: Raw HTML content
            url: Source URL

        Returns:
            str: Preprocessed content
        """
        return content

    def postprocess(self, result: ParseResult) -> ParseResult:
        """
        Postprocess parsing result (optional).

        Subclasses can override this to perform post-processing.
        Default implementation returns result unchanged.

        Args:
            result: ParseResult to postprocess

        Returns:
            ParseResult: Postprocessed result
        """
        return result

    def parse_with_validation(self, content: str, url: str) -> ParseResult:
        """
        Parse content and validate result.

        This is a convenience method that combines parsing and validation.
        It handles the full workflow: preprocess -> parse -> validate -> postprocess.

        Args:
            content: HTML content to parse
            url: Source URL

        Returns:
            ParseResult: Validated parsing result

        Raises:
            ParserError: If parsing or validation fails
        """
        try:
            # Preprocess
            preprocessed = self.preprocess(content, url)

            # Parse
            result = self.parse(preprocessed, url)

            # Validate
            if not self.validate(result):
                result.success = False
                result.errors.append("Validation failed")

            # Postprocess
            result = self.postprocess(result)

            return result

        except Exception as e:
            # Return failed result instead of raising
            return ParseResult(
                success=False,
                errors=[f"Parse error: {str(e)}"],
                parser_name=self.__class__.__name__
            )

    def __repr__(self) -> str:
        """String representation of parser."""
        metadata = self.get_metadata()
        return f"{self.__class__.__name__}({metadata})"
