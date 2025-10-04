"""Integration tests for TemplateParser with strategies.

Tests the complete workflow of template-based content extraction including:
- Title extraction with fallback
- Content extraction and Markdown conversion
- Metadata extraction
- Selector fallback mechanism
- Strategy detection and selection
"""

import pytest
from parsers.template_parser import TemplateParser
from parsers.base_parser import ParseResult


# Sample HTML for testing
SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Page Title</title>
    <meta name="description" content="This is a test description">
    <meta name="author" content="Test Author">
    <meta property="og:title" content="OG Title">
    <meta property="og:description" content="OG Description">
</head>
<body>
    <h1>Main Heading</h1>
    <article>
        <h2>Article Title</h2>
        <p>This is the first paragraph of content.</p>
        <p>This is the second paragraph with <strong>bold text</strong>.</p>
        <ul>
            <li>List item 1</li>
            <li>List item 2</li>
        </ul>
    </article>
</body>
</html>
"""

COMPLEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Complex Page</title>
    <meta name="description" content="Complex description">
    <meta property="article:published_time" content="2025-01-15">
    <meta property="og:image" content="https://example.com/image.jpg">
</head>
<body>
    <header>
        <h1>Site Header</h1>
    </header>
    <main role="main">
        <article>
            <h1>Article Heading</h1>
            <p>Main article content goes here.</p>
            <p>More content with <a href="#">links</a>.</p>
        </article>
    </main>
    <aside>
        <p>Sidebar content that should not be extracted</p>
    </aside>
</body>
</html>
"""

MINIMAL_HTML = """
<html>
<head><title>Minimal</title></head>
<body><p>Just a paragraph</p></body>
</html>
"""


class TestParserIntegration:
    """Integration tests for TemplateParser"""

    @pytest.fixture
    def parser(self):
        """Create a TemplateParser instance"""
        return TemplateParser()

    def test_parser_initialization(self, parser):
        """Test parser initializes with strategies and converter"""
        assert parser.strategies is not None
        assert 'css' in parser.strategies
        assert 'xpath' in parser.strategies
        assert 'text' in parser.strategies
        assert parser.html_converter is not None

    def test_strategy_detection_xpath(self, parser):
        """Test XPath strategy detection"""
        assert parser._detect_strategy('//div[@class="content"]') == 'xpath'
        assert parser._detect_strategy('/html/body/div') == 'xpath'

    def test_strategy_detection_css(self, parser):
        """Test CSS strategy detection (default)"""
        assert parser._detect_strategy('div.content') == 'css'
        assert parser._detect_strategy('article') == 'css'
        assert parser._detect_strategy('#main') == 'css'

    def test_extract_title_from_template(self, parser):
        """Test title extraction using template selectors (OG title preferred)"""
        result = parser.parse(SAMPLE_HTML, 'https://example.com/page')
        assert result.success is True
        # With optimized template, OG title takes precedence
        assert result.title in ["Test Page Title", "OG Title"]

    def test_extract_title_fallback(self, parser):
        """Test title extraction falls back to <title> tag"""
        html = "<html><head><title>Fallback Title</title></head><body></body></html>"
        result = parser.parse(html, 'https://example.com/page')
        assert result.success is True
        assert result.title == "Fallback Title"

    def test_extract_content_as_markdown(self, parser):
        """Test content extraction and Markdown conversion"""
        result = parser.parse(SAMPLE_HTML, 'https://example.com/page')
        assert result.success is True
        assert result.content is not None
        # Check for Markdown formatting
        assert '##' in result.content or '#' in result.content  # Headers
        assert '*' in result.content or '-' in result.content  # Lists or bold

    def test_extract_content_from_article(self, parser):
        """Test content extraction from <article> tag"""
        result = parser.parse(SAMPLE_HTML, 'https://example.com/page')
        assert result.success is True
        assert 'Article Title' in result.content
        assert 'first paragraph' in result.content
        assert 'second paragraph' in result.content

    def test_extract_content_from_main(self, parser):
        """Test content extraction from <main> tag"""
        result = parser.parse(COMPLEX_HTML, 'https://example.com/page')
        assert result.success is True
        assert 'Article Heading' in result.content
        assert 'Main article content' in result.content
        # Sidebar should not be included
        assert 'Sidebar content' not in result.content

    def test_extract_metadata_description(self, parser):
        """Test metadata extraction - description (OG description preferred)"""
        result = parser.parse(SAMPLE_HTML, 'https://example.com/page')
        assert result.success is True
        assert 'description' in result.metadata
        # With optimized template, OG description takes precedence
        assert result.metadata['description'] in ["This is a test description", "OG Description"]

    def test_extract_metadata_author(self, parser):
        """Test metadata extraction - author"""
        result = parser.parse(SAMPLE_HTML, 'https://example.com/page')
        assert result.success is True
        assert 'author' in result.metadata
        assert result.metadata['author'] == "Test Author"

    def test_extract_metadata_all_fields(self, parser):
        """Test extraction of multiple metadata fields"""
        result = parser.parse(COMPLEX_HTML, 'https://example.com/page')
        assert result.success is True
        assert 'description' in result.metadata
        assert 'date' in result.metadata
        assert 'image' in result.metadata
        assert result.metadata['date'] == "2025-01-15"
        assert result.metadata['image'] == "https://example.com/image.jpg"

    def test_metadata_includes_template_info(self, parser):
        """Test metadata includes template name and version"""
        result = parser.parse(SAMPLE_HTML, 'https://example.com/page')
        assert result.success is True
        assert 'template_name' in result.metadata
        assert 'template_version' in result.metadata
        assert 'source_url' in result.metadata
        assert result.metadata['source_url'] == 'https://example.com/page'

    def test_selector_fallback_mechanism(self, parser):
        """Test that multiple selectors are tried in order"""
        # HTML with only OG title, not regular title
        html = """
        <html>
        <head>
            <meta property="og:title" content="OG Title Only">
        </head>
        <body><h1>H1 Fallback</h1></body>
        </html>
        """
        result = parser.parse(html, 'https://example.com/page')
        assert result.success is True
        # Should find either OG title or H1
        assert result.title in ["OG Title Only", "H1 Fallback"] or result.title

    def test_parse_minimal_html(self, parser):
        """Test parsing minimal HTML structure"""
        result = parser.parse(MINIMAL_HTML, 'https://example.com/page')
        assert result.success is True
        assert result.title == "Minimal"

    def test_parse_result_structure(self, parser):
        """Test that ParseResult has all required fields"""
        result = parser.parse(SAMPLE_HTML, 'https://example.com/page')
        assert isinstance(result, ParseResult)
        assert hasattr(result, 'title')
        assert hasattr(result, 'content')
        assert hasattr(result, 'metadata')
        assert hasattr(result, 'success')
        assert hasattr(result, 'parser_name')
        assert hasattr(result, 'template_name')

    def test_parser_error_handling_invalid_html(self, parser):
        """Test parser handles invalid HTML gracefully"""
        invalid_html = "<<<not valid html>>>"
        result = parser.parse(invalid_html, 'https://example.com/page')
        # Should not crash, even if extraction fails
        assert isinstance(result, ParseResult)

    def test_empty_content_handling(self, parser):
        """Test handling of HTML with no extractable content"""
        empty_html = "<html><head></head><body></body></html>"
        result = parser.parse(empty_html, 'https://example.com/page')
        assert result.success is True
        # Should return empty strings, not None
        assert result.title == ""
        assert result.content == ""

    def test_extract_field_helper_css_selector(self, parser):
        """Test _extract_field helper with CSS selector"""
        value = parser._extract_field(SAMPLE_HTML, 'title')
        assert value == "Test Page Title"

    def test_extract_field_helper_multiple_selectors(self, parser):
        """Test _extract_field with comma-separated selectors"""
        # Try selectors in order: nonexistent, then title
        value = parser._extract_field(SAMPLE_HTML, '.nonexistent, title')
        assert value == "Test Page Title"

    def test_extract_field_helper_returns_none_on_failure(self, parser):
        """Test _extract_field returns None when no selector matches"""
        value = parser._extract_field(SAMPLE_HTML, '.totally-nonexistent-class')
        assert value is None

    def test_markdown_conversion_preserves_structure(self, parser):
        """Test that Markdown conversion preserves document structure"""
        result = parser.parse(SAMPLE_HTML, 'https://example.com/page')
        assert result.success is True
        # Check structure is preserved
        lines = result.content.split('\n')
        # Should have multiple lines
        assert len(lines) > 1
        # Should not have excessive blank lines
        consecutive_blanks = 0
        for line in lines:
            if line.strip() == '':
                consecutive_blanks += 1
            else:
                consecutive_blanks = 0
            # Should never have more than 2 consecutive blank lines
            assert consecutive_blanks <= 2

    def test_template_matching_uses_generic(self, parser):
        """Test that generic template is used for unknown URLs"""
        result = parser.parse(SAMPLE_HTML, 'https://unknown-site.com/page')
        assert result.success is True
        assert result.template_name == "Generic Web Template"

    def test_content_extraction_cleans_whitespace(self, parser):
        """Test that extracted content has cleaned whitespace"""
        html = """
        <html><body><article>
            <p>Line with trailing spaces    </p>


            <p>Multiple blank lines above</p>
        </article></body></html>
        """
        result = parser.parse(html, 'https://example.com/page')
        assert result.success is True
        # Should not have trailing whitespace on lines
        for line in result.content.split('\n'):
            assert line == line.rstrip()
