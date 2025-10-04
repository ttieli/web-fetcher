"""Tests for template_parser.py initialization and template loading.

Tests the TemplateParser class to ensure:
1. Initializes correctly with default template directory
2. Loads templates successfully
3. Can find templates for URLs
4. Integrates properly with TemplateLoader
5. Handles template caching
"""

import pytest
from pathlib import Path
from parsers.template_parser import TemplateParser
from parsers.base_parser import (
    ParseResult,
    ParserError,
    TemplateNotFoundError
)


class TestTemplateParserInitialization:
    """Test TemplateParser initialization."""

    def test_default_initialization(self):
        """TemplateParser should initialize with default template directory."""
        parser = TemplateParser()

        assert parser is not None
        assert parser.template_loader is not None
        assert parser.current_template is None
        assert parser.template_cache == {}

    def test_custom_template_directory(self):
        """TemplateParser should accept custom template directory."""
        # Get the default templates path
        base_dir = Path(__file__).parent.parent / "parsers" / "templates"

        parser = TemplateParser(template_dir=str(base_dir))

        assert parser is not None
        assert parser.template_loader is not None

    def test_initialization_creates_loader(self):
        """TemplateParser should create TemplateLoader instance."""
        parser = TemplateParser()

        # Check that template loader exists and has loaded templates
        assert hasattr(parser, 'template_loader')
        templates = parser.template_loader.list_templates()
        assert isinstance(templates, list)

    def test_initialization_error_handling(self):
        """TemplateParser should handle initialization gracefully."""
        # Initialize with non-existent path
        # Should not crash, just have empty template list
        parser = TemplateParser(template_dir="/nonexistent/path/to/templates")

        # Should initialize successfully but have no templates
        assert parser is not None
        assert parser.template_loader is not None
        # May have empty template list or just no custom templates


class TestTemplateLoading:
    """Test template loading functionality."""

    def test_templates_loaded(self):
        """TemplateParser should load available templates."""
        parser = TemplateParser()

        templates = parser.list_available_templates()
        assert isinstance(templates, list)
        # Should have at least generic template from Phase 1
        assert len(templates) > 0

    def test_get_generic_template(self):
        """TemplateParser should find generic template."""
        parser = TemplateParser()

        # Generic template should match any URL
        template = parser.get_template_for_url("http://example.com")

        assert template is not None
        assert isinstance(template, dict)
        assert 'name' in template

    def test_template_caching(self):
        """TemplateParser should cache templates by URL."""
        parser = TemplateParser()

        url = "http://example.com"

        # First call - should load and cache
        template1 = parser.get_template_for_url(url)

        # Should be cached now
        assert url in parser.template_cache

        # Second call - should return from cache
        template2 = parser.get_template_for_url(url)

        # Should be same template
        assert template1 == template2

    def test_reload_templates(self):
        """TemplateParser should be able to reload templates."""
        parser = TemplateParser()

        # Load a template
        parser.get_template_for_url("http://example.com")
        assert len(parser.template_cache) > 0

        # Reload
        parser.reload_templates()

        # Cache should be cleared
        assert len(parser.template_cache) == 0
        assert parser.current_template is None


class TestTemplateMatching:
    """Test template matching for URLs."""

    def test_matches_generic_template(self):
        """Should match generic template for any URL."""
        parser = TemplateParser()

        urls = [
            "http://example.com",
            "https://test.org",
            "http://unknown-site.net/page.html"
        ]

        for url in urls:
            template = parser.get_template_for_url(url)
            assert template is not None
            # Should get generic template
            assert 'name' in template

    def test_template_has_required_fields(self):
        """Loaded template should have required fields."""
        parser = TemplateParser()

        template = parser.get_template_for_url("http://example.com")

        # Check template structure
        assert 'name' in template
        assert 'version' in template
        assert 'domains' in template


class TestParserIntegration:
    """Test TemplateParser integration with BaseParser."""

    def test_inherits_from_base_parser(self):
        """TemplateParser should inherit from BaseParser."""
        from parsers.base_parser import BaseParser

        parser = TemplateParser()
        assert isinstance(parser, BaseParser)

    def test_implements_parse_method(self):
        """TemplateParser should implement parse() method."""
        parser = TemplateParser()

        # Should have parse method
        assert hasattr(parser, 'parse')
        assert callable(parser.parse)

    def test_implements_validate_method(self):
        """TemplateParser should implement validate() method."""
        parser = TemplateParser()

        # Should have validate method
        assert hasattr(parser, 'validate')
        assert callable(parser.validate)

    def test_implements_get_metadata_method(self):
        """TemplateParser should implement get_metadata() method."""
        parser = TemplateParser()

        # Should have get_metadata method
        assert hasattr(parser, 'get_metadata')
        metadata = parser.get_metadata()

        assert isinstance(metadata, dict)
        assert 'parser_name' in metadata
        assert metadata['parser_name'] == 'TemplateParser'


class TestBasicParsing:
    """Test basic parsing functionality (Phase 2.1 framework)."""

    def test_parse_returns_result(self):
        """parse() should return ParseResult."""
        parser = TemplateParser()

        result = parser.parse("<html><body>Test</body></html>", "http://example.com")

        assert isinstance(result, ParseResult)
        assert result.parser_name == "TemplateParser"
        assert result.template_name is not None

    def test_parse_sets_template_name(self):
        """parse() should set template name in result."""
        parser = TemplateParser()

        result = parser.parse("<html><body>Test</body></html>", "http://example.com")

        assert result.template_name is not None
        assert isinstance(result.template_name, str)

    def test_parse_with_generic_template(self):
        """parse() should work with generic template."""
        parser = TemplateParser()

        result = parser.parse("<html><body>Test</body></html>", "http://example.com")

        # Should succeed (even if content is empty in Phase 2.1)
        assert result is not None
        assert result.parser_name == "TemplateParser"

    def test_validate_basic(self):
        """validate() should perform basic validation."""
        parser = TemplateParser()

        # Valid result
        result = ParseResult(
            success=True,
            template_name="Test Template"
        )

        is_valid = parser.validate(result)
        assert is_valid is True

        # Invalid result - no template name
        invalid_result = ParseResult(
            success=True,
            template_name=None
        )

        is_valid = parser.validate(invalid_result)
        assert is_valid is False

    def test_get_metadata_complete(self):
        """get_metadata() should return complete metadata."""
        parser = TemplateParser()

        metadata = parser.get_metadata()

        assert 'parser_name' in metadata
        assert 'version' in metadata
        assert 'templates_loaded' in metadata
        assert 'supported_features' in metadata

        # Check types
        assert isinstance(metadata['parser_name'], str)
        assert isinstance(metadata['templates_loaded'], int)
        assert isinstance(metadata['supported_features'], list)


class TestPhase21Framework:
    """Test Phase 2.1 framework implementation (placeholders OK)."""

    def test_extract_methods_exist(self):
        """Extract methods should exist (even if returning placeholders)."""
        parser = TemplateParser()

        # Should have private extract methods
        assert hasattr(parser, '_extract_title')
        assert hasattr(parser, '_extract_content')
        assert hasattr(parser, '_extract_metadata')

    def test_parse_workflow(self):
        """parse() should follow complete workflow."""
        parser = TemplateParser()

        html = "<html><head><title>Test</title></head><body>Content</body></html>"
        url = "http://example.com"

        result = parser.parse(html, url)

        # Should complete workflow
        assert result is not None
        assert result.parser_name == "TemplateParser"
        assert result.template_name is not None
        assert isinstance(result.metadata, dict)

        # Metadata should include URL
        assert 'source_url' in result.metadata
        assert result.metadata['source_url'] == url

    def test_current_template_set_after_parse(self):
        """current_template should be set after parsing."""
        parser = TemplateParser()

        # Initially None
        assert parser.current_template is None

        # Parse
        parser.parse("<html>Test</html>", "http://example.com")

        # Should be set now
        assert parser.current_template is not None
        assert isinstance(parser.current_template, dict)

    def test_list_available_templates(self):
        """list_available_templates() should return template list."""
        parser = TemplateParser()

        templates = parser.list_available_templates()

        assert isinstance(templates, list)
        assert len(templates) > 0
        # Should include generic template from Phase 1
        assert any('Generic' in name for name in templates)
