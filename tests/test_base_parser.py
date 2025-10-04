"""Tests for base_parser.py module.

Tests the BaseParser abstract class to ensure:
1. Cannot be directly instantiated
2. All abstract methods must be implemented
3. ParseResult dataclass works correctly
4. Custom exceptions are defined
"""

import pytest
from parsers.base_parser import (
    BaseParser,
    ParseResult,
    ParserError,
    ValidationError,
    ExtractionError,
    TemplateNotFoundError
)


class TestBaseParserAbstract:
    """Test BaseParser abstract class behavior."""

    def test_cannot_instantiate_base_parser(self):
        """BaseParser should not be instantiable directly."""
        with pytest.raises(TypeError) as exc_info:
            BaseParser()

        # Should mention abstract methods
        error_msg = str(exc_info.value)
        assert "abstract" in error_msg.lower()

    def test_must_implement_parse(self):
        """Subclass must implement parse() method."""
        class IncompleteParser(BaseParser):
            def validate(self, result):
                return True

            def get_metadata(self):
                return {}

        with pytest.raises(TypeError) as exc_info:
            IncompleteParser()

        assert "parse" in str(exc_info.value).lower()

    def test_must_implement_validate(self):
        """Subclass must implement validate() method."""
        class IncompleteParser(BaseParser):
            def parse(self, content, url):
                return ParseResult()

            def get_metadata(self):
                return {}

        with pytest.raises(TypeError) as exc_info:
            IncompleteParser()

        assert "validate" in str(exc_info.value).lower()

    def test_must_implement_get_metadata(self):
        """Subclass must implement get_metadata() method."""
        class IncompleteParser(BaseParser):
            def parse(self, content, url):
                return ParseResult()

            def validate(self, result):
                return True

        with pytest.raises(TypeError) as exc_info:
            IncompleteParser()

        assert "get_metadata" in str(exc_info.value).lower()

    def test_complete_implementation_works(self):
        """Complete implementation should work."""
        class CompleteParser(BaseParser):
            def parse(self, content, url):
                return ParseResult(title="Test", content="Content")

            def validate(self, result):
                return result.title != ""

            def get_metadata(self):
                return {"name": "CompleteParser"}

        # Should instantiate successfully
        parser = CompleteParser()
        assert parser is not None
        assert isinstance(parser, BaseParser)


class TestParseResult:
    """Test ParseResult dataclass."""

    def test_default_initialization(self):
        """ParseResult should have sensible defaults."""
        result = ParseResult()

        assert result.title == ""
        assert result.content == ""
        assert result.metadata == {}
        assert result.success is True
        assert result.errors == []
        assert result.parser_name == ""
        assert result.template_name is None
        assert result.parse_time is not None

    def test_custom_initialization(self):
        """ParseResult should accept custom values."""
        result = ParseResult(
            title="Test Title",
            content="Test Content",
            metadata={"author": "Test Author"},
            success=True,
            errors=[],
            parser_name="TestParser",
            template_name="test.yaml"
        )

        assert result.title == "Test Title"
        assert result.content == "Test Content"
        assert result.metadata["author"] == "Test Author"
        assert result.parser_name == "TestParser"
        assert result.template_name == "test.yaml"

    def test_to_dict_conversion(self):
        """ParseResult should convert to dictionary."""
        result = ParseResult(
            title="Title",
            content="Content",
            parser_name="Parser"
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict['title'] == "Title"
        assert result_dict['content'] == "Content"
        assert result_dict['parser_name'] == "Parser"
        assert 'parse_time' in result_dict


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_parser_error(self):
        """ParserError should be raisable."""
        with pytest.raises(ParserError) as exc_info:
            raise ParserError("Test error")

        assert str(exc_info.value) == "Test error"

    def test_validation_error(self):
        """ValidationError should inherit from ParserError."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Validation failed")

        assert str(exc_info.value) == "Validation failed"
        assert isinstance(exc_info.value, ParserError)

    def test_extraction_error(self):
        """ExtractionError should inherit from ParserError."""
        with pytest.raises(ExtractionError) as exc_info:
            raise ExtractionError("Extraction failed")

        assert str(exc_info.value) == "Extraction failed"
        assert isinstance(exc_info.value, ParserError)

    def test_template_not_found_error(self):
        """TemplateNotFoundError should inherit from ParserError."""
        with pytest.raises(TemplateNotFoundError) as exc_info:
            raise TemplateNotFoundError("Template not found")

        assert str(exc_info.value) == "Template not found"
        assert isinstance(exc_info.value, ParserError)


class TestBaseParserMethods:
    """Test BaseParser optional methods."""

    def test_preprocess_default(self):
        """Default preprocess should return content unchanged."""
        class MinimalParser(BaseParser):
            def parse(self, content, url):
                return ParseResult()

            def validate(self, result):
                return True

            def get_metadata(self):
                return {}

        parser = MinimalParser()
        content = "<html>Test</html>"
        result = parser.preprocess(content, "http://test.com")

        assert result == content

    def test_postprocess_default(self):
        """Default postprocess should return result unchanged."""
        class MinimalParser(BaseParser):
            def parse(self, content, url):
                return ParseResult()

            def validate(self, result):
                return True

            def get_metadata(self):
                return {}

        parser = MinimalParser()
        result = ParseResult(title="Test")
        processed = parser.postprocess(result)

        assert processed.title == "Test"

    def test_parse_with_validation_success(self):
        """parse_with_validation should work for valid results."""
        class ValidParser(BaseParser):
            def parse(self, content, url):
                return ParseResult(title="Title", content="Content")

            def validate(self, result):
                return result.title != "" and result.content != ""

            def get_metadata(self):
                return {}

        parser = ValidParser()
        result = parser.parse_with_validation("<html>Test</html>", "http://test.com")

        assert result.success is True
        assert result.title == "Title"
        assert result.content == "Content"

    def test_parse_with_validation_failure(self):
        """parse_with_validation should handle validation failure."""
        class FailingParser(BaseParser):
            def parse(self, content, url):
                return ParseResult(title="", content="")

            def validate(self, result):
                return False  # Always fails

            def get_metadata(self):
                return {}

        parser = FailingParser()
        result = parser.parse_with_validation("<html>Test</html>", "http://test.com")

        assert result.success is False
        assert "Validation failed" in result.errors

    def test_parse_with_validation_exception(self):
        """parse_with_validation should handle exceptions gracefully."""
        class ErrorParser(BaseParser):
            def parse(self, content, url):
                raise ValueError("Parse error")

            def validate(self, result):
                return True

            def get_metadata(self):
                return {}

        parser = ErrorParser()
        result = parser.parse_with_validation("<html>Test</html>", "http://test.com")

        assert result.success is False
        assert len(result.errors) > 0
        assert "Parse error" in result.errors[0]
