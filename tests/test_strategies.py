"""Tests for extraction strategies.

Tests the extraction strategy framework to ensure:
1. ExtractionStrategy abstract class cannot be instantiated
2. CSSStrategy implements all required methods
3. CSS selector extraction works correctly
4. Attribute extraction (@href, @src) works
5. XPathStrategy works with XPath expressions
6. TextPatternStrategy works with regex patterns
7. Error handling works as expected
"""

import pytest
import re
from parsers.strategies import (
    ExtractionStrategy,
    CSSStrategy,
    XPathStrategy,
    TextPatternStrategy,
    StrategyError,
    SelectionError,
    ExtractionError
)


# Test HTML fixtures
SIMPLE_HTML = """
<html>
<head><title>Test Page</title></head>
<body>
    <h1 class="title">Main Title</h1>
    <h2>Subtitle</h2>
    <p class="content">First paragraph</p>
    <p class="content">Second paragraph</p>
    <p>Third paragraph</p>
    <a href="/page1" class="link">Link One</a>
    <a href="/page2">Link Two</a>
    <img src="/image1.jpg" alt="Image 1" class="thumbnail">
    <img src="/image2.jpg" alt="Image 2">
</body>
</html>
"""

EMPTY_HTML = "<html><body></body></html>"

NESTED_HTML = """
<html>
<body>
    <div class="container">
        <div class="item">
            <h3>Item 1</h3>
            <p>Description 1</p>
        </div>
        <div class="item">
            <h3>Item 2</h3>
            <p>Description 2</p>
        </div>
    </div>
</body>
</html>
"""


class TestExtractionStrategyAbstract:
    """Test ExtractionStrategy abstract class behavior."""

    def test_cannot_instantiate_base_strategy(self):
        """ExtractionStrategy should not be instantiable directly."""
        with pytest.raises(TypeError) as exc_info:
            ExtractionStrategy()

        # Should mention abstract methods
        error_msg = str(exc_info.value)
        assert "abstract" in error_msg.lower()

    def test_must_implement_extract(self):
        """Subclass must implement extract() method."""
        class IncompleteStrategy(ExtractionStrategy):
            def extract_all(self, content, selector):
                return []

        with pytest.raises(TypeError) as exc_info:
            IncompleteStrategy()

        assert "extract" in str(exc_info.value).lower()

    def test_must_implement_extract_all(self):
        """Subclass must implement extract_all() method."""
        class IncompleteStrategy(ExtractionStrategy):
            def extract(self, content, selector):
                return None

        with pytest.raises(TypeError) as exc_info:
            IncompleteStrategy()

        assert "extract_all" in str(exc_info.value).lower()

    def test_complete_implementation_works(self):
        """Complete implementation should work."""
        class CompleteStrategy(ExtractionStrategy):
            def extract(self, content, selector):
                return "test"

            def extract_all(self, content, selector):
                return ["test1", "test2"]

        # Should not raise
        strategy = CompleteStrategy()
        assert strategy is not None
        assert strategy.extract("content", "selector") == "test"
        assert strategy.extract_all("content", "selector") == ["test1", "test2"]


class TestCSSStrategyBasic:
    """Test CSSStrategy basic functionality."""

    def test_initialization(self):
        """CSSStrategy should initialize correctly."""
        strategy = CSSStrategy()
        assert strategy is not None
        assert strategy.parser == 'html.parser'

    def test_custom_parser(self):
        """CSSStrategy should accept custom parser."""
        strategy = CSSStrategy(parser='lxml')
        assert strategy.parser == 'lxml'

    def test_repr(self):
        """CSSStrategy should have string representation."""
        strategy = CSSStrategy()
        repr_str = repr(strategy)
        assert "CSSStrategy" in repr_str
        assert "html.parser" in repr_str


class TestCSSStrategyExtractText:
    """Test CSSStrategy text extraction."""

    def test_extract_h1(self):
        """Should extract h1 text."""
        strategy = CSSStrategy()
        result = strategy.extract(SIMPLE_HTML, "h1")
        assert result == "Main Title"

    def test_extract_h1_with_class(self):
        """Should extract h1 with class selector."""
        strategy = CSSStrategy()
        result = strategy.extract(SIMPLE_HTML, "h1.title")
        assert result == "Main Title"

    def test_extract_h2(self):
        """Should extract h2 text."""
        strategy = CSSStrategy()
        result = strategy.extract(SIMPLE_HTML, "h2")
        assert result == "Subtitle"

    def test_extract_paragraph(self):
        """Should extract first paragraph."""
        strategy = CSSStrategy()
        result = strategy.extract(SIMPLE_HTML, "p")
        assert result == "First paragraph"

    def test_extract_paragraph_with_class(self):
        """Should extract paragraph with class."""
        strategy = CSSStrategy()
        result = strategy.extract(SIMPLE_HTML, "p.content")
        assert result == "First paragraph"

    def test_extract_nested_element(self):
        """Should extract nested element."""
        strategy = CSSStrategy()
        result = strategy.extract(NESTED_HTML, ".item h3")
        assert result == "Item 1"

    def test_extract_with_descendant_selector(self):
        """Should work with descendant selectors."""
        strategy = CSSStrategy()
        result = strategy.extract(NESTED_HTML, "div.container div.item h3")
        assert result == "Item 1"


class TestCSSStrategyExtractAll:
    """Test CSSStrategy extract_all functionality."""

    def test_extract_all_paragraphs(self):
        """Should extract all paragraphs."""
        strategy = CSSStrategy()
        results = strategy.extract_all(SIMPLE_HTML, "p")
        assert len(results) == 3
        assert results[0] == "First paragraph"
        assert results[1] == "Second paragraph"
        assert results[2] == "Third paragraph"

    def test_extract_all_with_class(self):
        """Should extract all elements with class."""
        strategy = CSSStrategy()
        results = strategy.extract_all(SIMPLE_HTML, "p.content")
        assert len(results) == 2
        assert results[0] == "First paragraph"
        assert results[1] == "Second paragraph"

    def test_extract_all_links(self):
        """Should extract all link texts."""
        strategy = CSSStrategy()
        results = strategy.extract_all(SIMPLE_HTML, "a")
        assert len(results) == 2
        assert results[0] == "Link One"
        assert results[1] == "Link Two"

    def test_extract_all_nested(self):
        """Should extract all nested elements."""
        strategy = CSSStrategy()
        results = strategy.extract_all(NESTED_HTML, ".item h3")
        assert len(results) == 2
        assert results[0] == "Item 1"
        assert results[1] == "Item 2"


class TestCSSStrategyAttributes:
    """Test CSSStrategy attribute extraction."""

    def test_extract_href_attribute(self):
        """Should extract href attribute using @ syntax."""
        strategy = CSSStrategy()
        result = strategy.extract(SIMPLE_HTML, "a@href")
        assert result == "/page1"

    def test_extract_href_with_class(self):
        """Should extract href from specific link."""
        strategy = CSSStrategy()
        result = strategy.extract(SIMPLE_HTML, "a.link@href")
        assert result == "/page1"

    def test_extract_src_attribute(self):
        """Should extract src attribute."""
        strategy = CSSStrategy()
        result = strategy.extract(SIMPLE_HTML, "img@src")
        assert result == "/image1.jpg"

    def test_extract_src_with_class(self):
        """Should extract src from specific image."""
        strategy = CSSStrategy()
        result = strategy.extract(SIMPLE_HTML, "img.thumbnail@src")
        assert result == "/image1.jpg"

    def test_extract_alt_attribute(self):
        """Should extract alt attribute."""
        strategy = CSSStrategy()
        result = strategy.extract(SIMPLE_HTML, "img@alt")
        assert result == "Image 1"

    def test_extract_all_href_attributes(self):
        """Should extract all href attributes."""
        strategy = CSSStrategy()
        results = strategy.extract_all(SIMPLE_HTML, "a@href")
        assert len(results) == 2
        assert results[0] == "/page1"
        assert results[1] == "/page2"

    def test_extract_all_src_attributes(self):
        """Should extract all src attributes."""
        strategy = CSSStrategy()
        results = strategy.extract_all(SIMPLE_HTML, "img@src")
        assert len(results) == 2
        assert results[0] == "/image1.jpg"
        assert results[1] == "/image2.jpg"

    def test_extract_attribute_method(self):
        """Should extract attribute using extract_attribute method."""
        strategy = CSSStrategy()
        result = strategy.extract_attribute(SIMPLE_HTML, "a", "href")
        assert result == "/page1"

    def test_extract_all_attributes_method(self):
        """Should extract all attributes using extract_all_attributes method."""
        strategy = CSSStrategy()
        results = strategy.extract_all_attributes(SIMPLE_HTML, "a", "href")
        assert len(results) == 2
        assert results[0] == "/page1"
        assert results[1] == "/page2"


class TestCSSStrategyEdgeCases:
    """Test CSSStrategy edge cases and error handling."""

    def test_extract_no_match(self):
        """Should return None when no element matches."""
        strategy = CSSStrategy()
        result = strategy.extract(SIMPLE_HTML, "article")
        assert result is None

    def test_extract_all_no_match(self):
        """Should return empty list when no elements match."""
        strategy = CSSStrategy()
        results = strategy.extract_all(SIMPLE_HTML, "article")
        assert results == []

    def test_extract_empty_html(self):
        """Should handle empty HTML gracefully."""
        strategy = CSSStrategy()
        result = strategy.extract(EMPTY_HTML, "p")
        assert result is None

    def test_extract_all_empty_html(self):
        """Should handle empty HTML in extract_all."""
        strategy = CSSStrategy()
        results = strategy.extract_all(EMPTY_HTML, "p")
        assert results == []

    def test_extract_empty_content(self):
        """Should raise StrategyError for empty content."""
        strategy = CSSStrategy()
        with pytest.raises(StrategyError):
            strategy.extract("", "p")

    def test_extract_none_content(self):
        """Should raise StrategyError for None content."""
        strategy = CSSStrategy()
        with pytest.raises(StrategyError):
            strategy.extract(None, "p")

    def test_extract_whitespace_content(self):
        """Should raise StrategyError for whitespace-only content."""
        strategy = CSSStrategy()
        with pytest.raises(StrategyError):
            strategy.extract("   ", "p")

    def test_extract_missing_attribute(self):
        """Should return None when attribute doesn't exist."""
        strategy = CSSStrategy()
        result = strategy.extract(SIMPLE_HTML, "p@href")
        assert result is None

    def test_extract_all_missing_attribute(self):
        """Should return empty list when attribute doesn't exist on any element."""
        strategy = CSSStrategy()
        results = strategy.extract_all(SIMPLE_HTML, "p@href")
        assert results == []

    def test_extract_invalid_selector_empty(self):
        """Should raise SelectionError for empty selector."""
        strategy = CSSStrategy()
        with pytest.raises(SelectionError):
            strategy.extract(SIMPLE_HTML, "")

    def test_extract_invalid_selector_whitespace(self):
        """Should raise SelectionError for whitespace-only selector."""
        strategy = CSSStrategy()
        with pytest.raises(SelectionError):
            strategy.extract(SIMPLE_HTML, "   ")

    def test_extract_whitespace_in_text(self):
        """Should strip whitespace from extracted text."""
        html = "<p>  Text with spaces  </p>"
        strategy = CSSStrategy()
        result = strategy.extract(html, "p")
        assert result == "Text with spaces"

    def test_extract_empty_element(self):
        """Should return None for empty element."""
        html = "<p></p>"
        strategy = CSSStrategy()
        result = strategy.extract(html, "p")
        assert result is None

    def test_extract_all_filters_empty(self):
        """Should filter out empty values in extract_all."""
        html = "<p>First</p><p></p><p>Third</p>"
        strategy = CSSStrategy()
        results = strategy.extract_all(html, "p")
        assert len(results) == 2
        assert results[0] == "First"
        assert results[1] == "Third"


class TestCSSStrategySelectorValidation:
    """Test CSSStrategy selector validation."""

    def test_validate_selector_valid(self):
        """Should validate correct selectors."""
        strategy = CSSStrategy()
        assert strategy.validate_selector("p")
        assert strategy.validate_selector("p.class")
        assert strategy.validate_selector("p#id")
        assert strategy.validate_selector("div > p")
        assert strategy.validate_selector("a@href")

    def test_validate_selector_empty(self):
        """Should reject empty selector."""
        strategy = CSSStrategy()
        assert not strategy.validate_selector("")

    def test_validate_selector_whitespace(self):
        """Should reject whitespace-only selector."""
        strategy = CSSStrategy()
        assert not strategy.validate_selector("   ")

    def test_validate_selector_unbalanced_brackets(self):
        """Should reject selector with unbalanced brackets."""
        strategy = CSSStrategy()
        assert not strategy.validate_selector("p[class")
        assert not strategy.validate_selector("p]class")

    def test_validate_selector_unbalanced_parentheses(self):
        """Should reject selector with unbalanced parentheses."""
        strategy = CSSStrategy()
        assert not strategy.validate_selector("p:nth-child(2")
        assert not strategy.validate_selector("p:nth-child2)")


class TestCSSStrategyExceptions:
    """Test CSSStrategy exception classes."""

    def test_strategy_error_exists(self):
        """StrategyError should be defined."""
        with pytest.raises(StrategyError):
            raise StrategyError("Test error")

    def test_selection_error_exists(self):
        """SelectionError should be defined."""
        with pytest.raises(SelectionError):
            raise SelectionError("Test error")

    def test_extraction_error_exists(self):
        """ExtractionError should be defined."""
        with pytest.raises(ExtractionError):
            raise ExtractionError("Test error")

    def test_selection_error_is_strategy_error(self):
        """SelectionError should inherit from StrategyError."""
        assert issubclass(SelectionError, StrategyError)

    def test_extraction_error_is_strategy_error(self):
        """ExtractionError should inherit from StrategyError."""
        assert issubclass(ExtractionError, StrategyError)


class TestCSSStrategyIntegration:
    """Integration tests for CSSStrategy."""

    def test_complex_extraction_workflow(self):
        """Should handle complex extraction workflow."""
        html = """
        <article>
            <header>
                <h1>Article Title</h1>
                <a href="/author">Author Name</a>
            </header>
            <div class="content">
                <p>Paragraph 1</p>
                <p>Paragraph 2</p>
                <img src="/image.jpg" alt="Featured">
            </div>
        </article>
        """
        strategy = CSSStrategy()

        # Extract different parts
        title = strategy.extract(html, "article h1")
        author_link = strategy.extract(html, "header a@href")
        author_name = strategy.extract(html, "header a")
        paragraphs = strategy.extract_all(html, ".content p")
        image = strategy.extract(html, ".content img@src")

        assert title == "Article Title"
        assert author_link == "/author"
        assert author_name == "Author Name"
        assert len(paragraphs) == 2
        assert paragraphs[0] == "Paragraph 1"
        assert paragraphs[1] == "Paragraph 2"
        assert image == "/image.jpg"

    def test_switching_between_text_and_attributes(self):
        """Should switch between text and attribute extraction."""
        html = '<a href="/page" class="link">Click Here</a>'
        strategy = CSSStrategy()

        # Extract text
        text = strategy.extract(html, "a.link")
        assert text == "Click Here"

        # Extract attribute
        href = strategy.extract(html, "a.link@href")
        assert href == "/page"

        # Extract using method
        href2 = strategy.extract_attribute(html, "a.link", "href")
        assert href2 == "/page"


# ==================== XPath Strategy Tests ====================


class TestXPathStrategyBasic:
    """Test XPathStrategy basic functionality."""

    def test_initialization(self):
        """XPathStrategy should initialize correctly."""
        strategy = XPathStrategy()
        assert strategy is not None

    def test_repr(self):
        """XPathStrategy should have string representation."""
        strategy = XPathStrategy()
        repr_str = repr(strategy)
        assert "XPathStrategy" in repr_str


class TestXPathStrategyExtractText:
    """Test XPathStrategy text extraction."""

    def test_extract_h1(self):
        """Should extract h1 text using XPath."""
        strategy = XPathStrategy()
        result = strategy.extract(SIMPLE_HTML, "//h1")
        assert result == "Main Title"

    def test_extract_h1_with_class(self):
        """Should extract h1 with class using XPath."""
        strategy = XPathStrategy()
        result = strategy.extract(SIMPLE_HTML, "//h1[@class='title']")
        assert result == "Main Title"

    def test_extract_h2(self):
        """Should extract h2 text using XPath."""
        strategy = XPathStrategy()
        result = strategy.extract(SIMPLE_HTML, "//h2")
        assert result == "Subtitle"

    def test_extract_paragraph(self):
        """Should extract first paragraph using XPath."""
        strategy = XPathStrategy()
        result = strategy.extract(SIMPLE_HTML, "//p")
        assert result == "First paragraph"

    def test_extract_paragraph_with_class(self):
        """Should extract paragraph with class using XPath."""
        strategy = XPathStrategy()
        result = strategy.extract(SIMPLE_HTML, "//p[@class='content']")
        assert result == "First paragraph"

    def test_extract_nested_element(self):
        """Should extract nested element using XPath."""
        strategy = XPathStrategy()
        result = strategy.extract(NESTED_HTML, "//div[@class='item']//h3")
        assert result == "Item 1"

    def test_extract_with_predicate(self):
        """Should work with XPath predicates."""
        strategy = XPathStrategy()
        result = strategy.extract(NESTED_HTML, "//div[@class='item'][1]//h3")
        assert result == "Item 1"

    def test_extract_with_position(self):
        """Should work with position predicates."""
        strategy = XPathStrategy()
        # Get second paragraph
        result = strategy.extract(SIMPLE_HTML, "(//p)[2]")
        assert result == "Second paragraph"


class TestXPathStrategyExtractAll:
    """Test XPathStrategy extract_all functionality."""

    def test_extract_all_paragraphs(self):
        """Should extract all paragraphs using XPath."""
        strategy = XPathStrategy()
        results = strategy.extract_all(SIMPLE_HTML, "//p")
        assert len(results) == 3
        assert results[0] == "First paragraph"
        assert results[1] == "Second paragraph"
        assert results[2] == "Third paragraph"

    def test_extract_all_with_class(self):
        """Should extract all elements with class using XPath."""
        strategy = XPathStrategy()
        results = strategy.extract_all(SIMPLE_HTML, "//p[@class='content']")
        assert len(results) == 2
        assert results[0] == "First paragraph"
        assert results[1] == "Second paragraph"

    def test_extract_all_links(self):
        """Should extract all link texts using XPath."""
        strategy = XPathStrategy()
        results = strategy.extract_all(SIMPLE_HTML, "//a")
        assert len(results) == 2
        assert results[0] == "Link One"
        assert results[1] == "Link Two"

    def test_extract_all_nested(self):
        """Should extract all nested elements using XPath."""
        strategy = XPathStrategy()
        results = strategy.extract_all(NESTED_HTML, "//div[@class='item']//h3")
        assert len(results) == 2
        assert results[0] == "Item 1"
        assert results[1] == "Item 2"


class TestXPathStrategyAttributes:
    """Test XPathStrategy attribute extraction."""

    def test_extract_href_attribute(self):
        """Should extract href attribute using XPath."""
        strategy = XPathStrategy()
        result = strategy.extract(SIMPLE_HTML, "//a/@href")
        assert result == "/page1"

    def test_extract_href_with_class(self):
        """Should extract href from specific link using XPath."""
        strategy = XPathStrategy()
        result = strategy.extract(SIMPLE_HTML, "//a[@class='link']/@href")
        assert result == "/page1"

    def test_extract_src_attribute(self):
        """Should extract src attribute using XPath."""
        strategy = XPathStrategy()
        result = strategy.extract(SIMPLE_HTML, "//img/@src")
        assert result == "/image1.jpg"

    def test_extract_src_with_class(self):
        """Should extract src from specific image using XPath."""
        strategy = XPathStrategy()
        result = strategy.extract(SIMPLE_HTML, "//img[@class='thumbnail']/@src")
        assert result == "/image1.jpg"

    def test_extract_alt_attribute(self):
        """Should extract alt attribute using XPath."""
        strategy = XPathStrategy()
        result = strategy.extract(SIMPLE_HTML, "//img/@alt")
        assert result == "Image 1"

    def test_extract_all_href_attributes(self):
        """Should extract all href attributes using XPath."""
        strategy = XPathStrategy()
        results = strategy.extract_all(SIMPLE_HTML, "//a/@href")
        assert len(results) == 2
        assert results[0] == "/page1"
        assert results[1] == "/page2"

    def test_extract_all_src_attributes(self):
        """Should extract all src attributes using XPath."""
        strategy = XPathStrategy()
        results = strategy.extract_all(SIMPLE_HTML, "//img/@src")
        assert len(results) == 2
        assert results[0] == "/image1.jpg"
        assert results[1] == "/image2.jpg"

    def test_extract_attribute_method(self):
        """Should extract attribute using extract_attribute method."""
        strategy = XPathStrategy()
        result = strategy.extract_attribute(SIMPLE_HTML, "//a", "href")
        assert result == "/page1"

    def test_extract_all_attributes_method(self):
        """Should extract all attributes using extract_all_attributes method."""
        strategy = XPathStrategy()
        results = strategy.extract_all_attributes(SIMPLE_HTML, "//a", "href")
        assert len(results) == 2
        assert results[0] == "/page1"
        assert results[1] == "/page2"


class TestXPathStrategyEdgeCases:
    """Test XPathStrategy edge cases and error handling."""

    def test_extract_no_match(self):
        """Should return None when no element matches."""
        strategy = XPathStrategy()
        result = strategy.extract(SIMPLE_HTML, "//article")
        assert result is None

    def test_extract_all_no_match(self):
        """Should return empty list when no elements match."""
        strategy = XPathStrategy()
        results = strategy.extract_all(SIMPLE_HTML, "//article")
        assert results == []

    def test_extract_empty_html(self):
        """Should handle empty HTML gracefully."""
        strategy = XPathStrategy()
        result = strategy.extract(EMPTY_HTML, "//p")
        assert result is None

    def test_extract_all_empty_html(self):
        """Should handle empty HTML in extract_all."""
        strategy = XPathStrategy()
        results = strategy.extract_all(EMPTY_HTML, "//p")
        assert results == []

    def test_extract_empty_content(self):
        """Should raise StrategyError for empty content."""
        strategy = XPathStrategy()
        with pytest.raises(StrategyError):
            strategy.extract("", "//p")

    def test_extract_none_content(self):
        """Should raise StrategyError for None content."""
        strategy = XPathStrategy()
        with pytest.raises(StrategyError):
            strategy.extract(None, "//p")

    def test_extract_whitespace_content(self):
        """Should raise StrategyError for whitespace-only content."""
        strategy = XPathStrategy()
        with pytest.raises(StrategyError):
            strategy.extract("   ", "//p")

    def test_extract_missing_attribute(self):
        """Should return None when attribute doesn't exist."""
        strategy = XPathStrategy()
        result = strategy.extract(SIMPLE_HTML, "//p/@href")
        assert result is None

    def test_extract_all_missing_attribute(self):
        """Should return empty list when attribute doesn't exist."""
        strategy = XPathStrategy()
        results = strategy.extract_all(SIMPLE_HTML, "//p/@href")
        assert results == []

    def test_extract_invalid_xpath(self):
        """Should raise SelectionError for invalid XPath."""
        strategy = XPathStrategy()
        with pytest.raises(SelectionError):
            strategy.extract(SIMPLE_HTML, "//p[")

    def test_extract_text_node(self):
        """Should extract text nodes using /text()."""
        html = "<p>First text</p>"
        strategy = XPathStrategy()
        result = strategy.extract(html, "//p/text()")
        assert result == "First text"

    def test_extract_all_text_nodes(self):
        """Should extract all text nodes using /text()."""
        html = "<div><p>First</p><p>Second</p></div>"
        strategy = XPathStrategy()
        results = strategy.extract_all(html, "//p/text()")
        assert len(results) == 2
        assert results[0] == "First"
        assert results[1] == "Second"


class TestXPathStrategySelectorValidation:
    """Test XPathStrategy selector validation."""

    def test_validate_selector_valid(self):
        """Should validate correct XPath expressions."""
        strategy = XPathStrategy()
        assert strategy.validate_selector("//p")
        assert strategy.validate_selector("//p[@class='content']")
        assert strategy.validate_selector("//div//p")
        assert strategy.validate_selector("//a/@href")

    def test_validate_selector_empty(self):
        """Should reject empty selector."""
        strategy = XPathStrategy()
        assert not strategy.validate_selector("")

    def test_validate_selector_whitespace(self):
        """Should reject whitespace-only selector."""
        strategy = XPathStrategy()
        assert not strategy.validate_selector("   ")

    def test_validate_selector_unbalanced_brackets(self):
        """Should reject XPath with unbalanced brackets."""
        strategy = XPathStrategy()
        assert not strategy.validate_selector("//p[@class")
        assert not strategy.validate_selector("//p]@class")

    def test_validate_selector_unbalanced_parentheses(self):
        """Should reject XPath with unbalanced parentheses."""
        strategy = XPathStrategy()
        assert not strategy.validate_selector("(//p")
        assert not strategy.validate_selector("//p)")


class TestXPathStrategyIntegration:
    """Integration tests for XPathStrategy."""

    def test_complex_xpath_workflow(self):
        """Should handle complex XPath workflow."""
        html = """
        <article>
            <header>
                <h1>Article Title</h1>
                <a href="/author">Author Name</a>
            </header>
            <div class="content">
                <p>Paragraph 1</p>
                <p>Paragraph 2</p>
                <img src="/image.jpg" alt="Featured">
            </div>
        </article>
        """
        strategy = XPathStrategy()

        # Extract different parts
        title = strategy.extract(html, "//article//h1")
        author_link = strategy.extract(html, "//header//a/@href")
        author_name = strategy.extract(html, "//header//a")
        paragraphs = strategy.extract_all(html, "//div[@class='content']//p")
        image = strategy.extract(html, "//div[@class='content']//img/@src")

        assert title == "Article Title"
        assert author_link == "/author"
        assert author_name == "Author Name"
        assert len(paragraphs) == 2
        assert paragraphs[0] == "Paragraph 1"
        assert paragraphs[1] == "Paragraph 2"
        assert image == "/image.jpg"


# ==================== TextPattern Strategy Tests ====================


# Additional text fixtures for pattern matching
SAMPLE_TEXT = """
Name: John Doe
Email: john.doe@example.com
Phone: (555) 123-4567
Price: $19.99
Date: 2024-01-15

Contact: jane@company.org
Phone: 555-987-6543
"""

CODE_SAMPLE = """
```python
def hello():
    print("Hello World")
```

```javascript
function greet() {
    console.log("Hi");
}
```
"""


class TestTextPatternStrategyBasic:
    """Test TextPatternStrategy basic functionality."""

    def test_initialization(self):
        """TextPatternStrategy should initialize correctly."""
        strategy = TextPatternStrategy()
        assert strategy is not None
        assert strategy.default_flags == 0

    def test_initialization_with_flags(self):
        """TextPatternStrategy should accept flags."""
        strategy = TextPatternStrategy(flags=re.IGNORECASE)
        assert strategy.default_flags == re.IGNORECASE

    def test_repr(self):
        """TextPatternStrategy should have string representation."""
        strategy = TextPatternStrategy()
        repr_str = repr(strategy)
        assert "TextPatternStrategy" in repr_str


class TestTextPatternStrategyExtract:
    """Test TextPatternStrategy extraction."""

    def test_extract_email(self):
        """Should extract email address."""
        strategy = TextPatternStrategy()
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        result = strategy.extract(SAMPLE_TEXT, pattern)
        assert result == "john.doe@example.com"

    def test_extract_with_group(self):
        """Should extract using capture group."""
        strategy = TextPatternStrategy()
        pattern = r'Name:\s*(.+)'
        result = strategy.extract(SAMPLE_TEXT, pattern)
        assert result == "John Doe"

    def test_extract_price(self):
        """Should extract price with group."""
        strategy = TextPatternStrategy()
        pattern = r'Price:\s*\$?(\d+\.?\d*)'
        result = strategy.extract(SAMPLE_TEXT, pattern)
        assert result == "19.99"

    def test_extract_phone(self):
        """Should extract phone number."""
        strategy = TextPatternStrategy()
        pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        result = strategy.extract(SAMPLE_TEXT, pattern)
        assert result == "(555) 123-4567"

    def test_extract_date(self):
        """Should extract date."""
        strategy = TextPatternStrategy()
        pattern = r'\d{4}-\d{2}-\d{2}'
        result = strategy.extract(SAMPLE_TEXT, pattern)
        assert result == "2024-01-15"

    def test_extract_no_match(self):
        """Should return None when no match."""
        strategy = TextPatternStrategy()
        pattern = r'Address:\s*(.+)'
        result = strategy.extract(SAMPLE_TEXT, pattern)
        assert result is None


class TestTextPatternStrategyExtractAll:
    """Test TextPatternStrategy extract_all functionality."""

    def test_extract_all_emails(self):
        """Should extract all email addresses."""
        strategy = TextPatternStrategy()
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        results = strategy.extract_all(SAMPLE_TEXT, pattern)
        assert len(results) == 2
        assert results[0] == "john.doe@example.com"
        assert results[1] == "jane@company.org"

    def test_extract_all_phones(self):
        """Should extract all phone numbers."""
        strategy = TextPatternStrategy()
        pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        results = strategy.extract_all(SAMPLE_TEXT, pattern)
        assert len(results) == 2

    def test_extract_all_with_groups(self):
        """Should extract all matches with groups."""
        strategy = TextPatternStrategy()
        pattern = r'Phone:\s*(.+)'
        results = strategy.extract_all(SAMPLE_TEXT, pattern)
        assert len(results) == 2

    def test_extract_all_no_match(self):
        """Should return empty list when no matches."""
        strategy = TextPatternStrategy()
        pattern = r'Address:\s*(.+)'
        results = strategy.extract_all(SAMPLE_TEXT, pattern)
        assert results == []


class TestTextPatternStrategyMultiline:
    """Test TextPatternStrategy multiline matching."""

    def test_extract_multiline_code_block(self):
        """Should extract multiline code block."""
        strategy = TextPatternStrategy()
        pattern = r'```python\n(.*?)\n```'
        result = strategy.extract(CODE_SAMPLE, pattern, multiline=True)
        assert result is not None
        assert 'def hello()' in result
        assert 'print("Hello World")' in result

    def test_extract_all_code_blocks(self):
        """Should extract all code blocks."""
        strategy = TextPatternStrategy()
        pattern = r'```\w+\n(.*?)\n```'
        results = strategy.extract_all(CODE_SAMPLE, pattern, multiline=True)
        assert len(results) == 2

    def test_multiline_flag_effect(self):
        """Should respect multiline flag."""
        strategy = TextPatternStrategy()
        pattern = r'```python.*?```'

        # Without multiline - won't match across lines
        result_no_multiline = strategy.extract(CODE_SAMPLE, pattern, multiline=False)
        assert result_no_multiline is None

        # With multiline - will match
        result_multiline = strategy.extract(CODE_SAMPLE, pattern, multiline=True)
        assert result_multiline is not None


class TestTextPatternStrategyIgnoreCase:
    """Test TextPatternStrategy case-insensitive matching."""

    def test_extract_ignore_case(self):
        """Should extract with case insensitivity."""
        text = "EMAIL: contact@example.com"
        strategy = TextPatternStrategy()
        pattern = r'email:\s*(.+)'

        # Case sensitive - no match
        result_sensitive = strategy.extract(text, pattern, ignore_case=False)
        assert result_sensitive is None

        # Case insensitive - matches
        result_insensitive = strategy.extract(text, pattern, ignore_case=True)
        assert result_insensitive == "contact@example.com"


class TestTextPatternStrategyNamedGroups:
    """Test TextPatternStrategy named group extraction."""

    def test_extract_named_groups(self):
        """Should extract named groups."""
        strategy = TextPatternStrategy()
        pattern = r'Name:\s*(?P<name>[^\n]+).*?Email:\s*(?P<email>[^\n]+)'
        result = strategy.extract_named_groups(SAMPLE_TEXT, pattern, multiline=True)

        assert result is not None
        assert result['name'] == 'John Doe'
        assert result['email'] == 'john.doe@example.com'

    def test_extract_named_groups_no_match(self):
        """Should return None when no match for named groups."""
        strategy = TextPatternStrategy()
        pattern = r'Address:\s*(?P<address>.+)'
        result = strategy.extract_named_groups(SAMPLE_TEXT, pattern)
        assert result is None

    def test_extract_all_named_groups(self):
        """Should extract named groups from all matches."""
        text = "User: Alice, Age: 25\nUser: Bob, Age: 30"
        strategy = TextPatternStrategy()
        pattern = r'User:\s*(?P<name>\w+),\s*Age:\s*(?P<age>\d+)'
        results = strategy.extract_all_named_groups(text, pattern)

        assert len(results) == 2
        assert results[0] == {'name': 'Alice', 'age': '25'}
        assert results[1] == {'name': 'Bob', 'age': '30'}


class TestTextPatternStrategyEdgeCases:
    """Test TextPatternStrategy edge cases."""

    def test_extract_none_content(self):
        """Should raise StrategyError for None content."""
        strategy = TextPatternStrategy()
        with pytest.raises(StrategyError):
            strategy.extract(None, r'test')

    def test_extract_invalid_pattern(self):
        """Should raise SelectionError for invalid regex."""
        strategy = TextPatternStrategy()
        with pytest.raises(SelectionError):
            strategy.extract("text", r'[invalid(')

    def test_extract_empty_match(self):
        """Should handle empty matches."""
        text = "Hello  World"
        strategy = TextPatternStrategy()
        # Pattern that might match empty string
        pattern = r'\s*'
        result = strategy.extract(text, pattern)
        # Should return None for empty match
        assert result is None or result == ""

    def test_validate_selector_valid(self):
        """Should validate correct regex patterns."""
        strategy = TextPatternStrategy()
        assert strategy.validate_selector(r'\d+')
        assert strategy.validate_selector(r'[a-z]+')
        assert strategy.validate_selector(r'test')

    def test_validate_selector_invalid(self):
        """Should reject invalid regex patterns."""
        strategy = TextPatternStrategy()
        assert not strategy.validate_selector(r'[invalid(')
        assert not strategy.validate_selector("")

    def test_extract_with_escaped_characters(self):
        """Should handle escaped characters in pattern."""
        text = "Price: $19.99"
        strategy = TextPatternStrategy()
        pattern = r'\$(\d+\.\d+)'
        result = strategy.extract(text, pattern)
        assert result == "19.99"


class TestTextPatternStrategyIntegration:
    """Integration tests for TextPatternStrategy."""

    def test_complex_pattern_workflow(self):
        """Should handle complex pattern matching workflow."""
        text = """
        Product: Widget Pro
        Price: $149.99
        Stock: 25 units
        Contact: sales@widget.com
        Phone: 555-1234
        """
        strategy = TextPatternStrategy()

        # Extract different fields
        product = strategy.extract(text, r'Product:\s*(.+)')
        price = strategy.extract(text, r'Price:\s*\$(\d+\.\d+)')
        stock = strategy.extract(text, r'Stock:\s*(\d+)')
        email = strategy.extract(text, r'[a-z]+@[a-z]+\.[a-z]+')
        phone = strategy.extract(text, r'\d{3}-\d{4}')

        assert product == "Widget Pro"
        assert price == "149.99"
        assert stock == "25"
        assert email == "sales@widget.com"
        assert phone == "555-1234"


# ==================== Cross-Strategy Compatibility Tests ====================


class TestCrossStrategyCompatibility:
    """Test compatibility and consistency across strategies."""

    def test_all_strategies_inherit_base(self):
        """All strategies should inherit from ExtractionStrategy."""
        assert issubclass(CSSStrategy, ExtractionStrategy)
        assert issubclass(XPathStrategy, ExtractionStrategy)
        assert issubclass(TextPatternStrategy, ExtractionStrategy)

    def test_all_strategies_have_extract(self):
        """All strategies should implement extract method."""
        css = CSSStrategy()
        xpath = XPathStrategy()
        pattern = TextPatternStrategy()

        assert hasattr(css, 'extract')
        assert hasattr(xpath, 'extract')
        assert hasattr(pattern, 'extract')

    def test_all_strategies_have_extract_all(self):
        """All strategies should implement extract_all method."""
        css = CSSStrategy()
        xpath = XPathStrategy()
        pattern = TextPatternStrategy()

        assert hasattr(css, 'extract_all')
        assert hasattr(xpath, 'extract_all')
        assert hasattr(pattern, 'extract_all')

    def test_css_vs_xpath_same_result(self):
        """CSS and XPath should produce same results for equivalent selectors."""
        html = "<h1>Test Title</h1>"

        css = CSSStrategy()
        xpath = XPathStrategy()

        css_result = css.extract(html, "h1")
        xpath_result = xpath.extract(html, "//h1")

        assert css_result == xpath_result == "Test Title"

    def test_all_strategies_handle_no_match_consistently(self):
        """All strategies should return None/empty for no matches."""
        html = "<div>Content</div>"

        css = CSSStrategy()
        xpath = XPathStrategy()

        assert css.extract(html, "article") is None
        assert xpath.extract(html, "//article") is None
        assert css.extract_all(html, "article") == []
        assert xpath.extract_all(html, "//article") == []

    def test_all_strategies_handle_errors_consistently(self):
        """All strategies should handle errors consistently."""
        css = CSSStrategy()
        xpath = XPathStrategy()
        pattern = TextPatternStrategy()

        # All should raise StrategyError for empty content
        with pytest.raises(StrategyError):
            css.extract("", "selector")
        with pytest.raises(StrategyError):
            xpath.extract("", "//xpath")
        with pytest.raises(StrategyError):
            pattern.extract(None, r'pattern')
