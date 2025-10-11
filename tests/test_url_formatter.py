"""
Unit tests for url_formatter module
Task-003 Phase 2: URL Formatter Module Tests
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from url_formatter import (
    format_url_as_markdown,
    is_valid_url,
    normalize_url_for_display,
    detect_urls_in_text,
    replace_urls_with_markdown
)


class TestFormatUrlAsMarkdown:
    """Test format_url_as_markdown function"""

    def test_basic_url(self):
        """Test basic URL formatting"""
        result = format_url_as_markdown("https://example.com")
        assert result == "[https://example.com](https://example.com)"

    def test_url_with_text(self):
        """Test URL with custom text"""
        result = format_url_as_markdown("https://example.com", "Example Site")
        assert result == "[Example Site](https://example.com)"

    def test_invalid_url(self):
        """Test invalid URL returns as-is"""
        result = format_url_as_markdown("not-a-url")
        assert result == "not-a-url"

    def test_url_with_path(self):
        """Test URL with path"""
        result = format_url_as_markdown("https://example.com/path/to/page")
        assert result == "[https://example.com/path/to/page](https://example.com/path/to/page)"

    def test_url_with_query(self):
        """Test URL with query parameters"""
        result = format_url_as_markdown("https://example.com/page?id=123&name=test")
        assert result == "[https://example.com/page?id=123&name=test](https://example.com/page?id=123&name=test)"

    def test_empty_string(self):
        """Test empty string"""
        result = format_url_as_markdown("")
        assert result == ""

    def test_url_with_fragment(self):
        """Test URL with fragment"""
        result = format_url_as_markdown("https://example.com/page#section")
        assert result == "[https://example.com/page#section](https://example.com/page#section)"


class TestIsValidUrl:
    """Test is_valid_url function"""

    def test_valid_https_url(self):
        assert is_valid_url("https://example.com") == True

    def test_valid_http_url(self):
        assert is_valid_url("http://example.com") == True

    def test_protocol_relative(self):
        assert is_valid_url("//example.com") == True

    def test_invalid_url(self):
        assert is_valid_url("not-a-url") == False

    def test_empty_string(self):
        assert is_valid_url("") == False

    def test_none_value(self):
        assert is_valid_url(None) == False

    def test_url_with_path(self):
        assert is_valid_url("https://example.com/path/to/page") == True

    def test_url_with_port(self):
        assert is_valid_url("https://example.com:8080") == True

    def test_localhost(self):
        assert is_valid_url("http://localhost:3000") == True

    def test_ip_address(self):
        assert is_valid_url("http://192.168.1.1") == True

    def test_domain_only(self):
        """Test domain without protocol"""
        # Should return True based on the '.' check in the function
        assert is_valid_url("example.com") == True

    def test_single_word(self):
        assert is_valid_url("example") == False


class TestNormalizeUrlForDisplay:
    """Test normalize_url_for_display function"""

    def test_already_has_https(self):
        result = normalize_url_for_display("https://example.com")
        assert result == "https://example.com"

    def test_already_has_http(self):
        result = normalize_url_for_display("http://example.com")
        assert result == "http://example.com"

    def test_protocol_relative(self):
        result = normalize_url_for_display("//example.com")
        assert result == "//example.com"

    def test_bare_domain(self):
        result = normalize_url_for_display("example.com")
        assert result == "https://example.com"

    def test_empty_string(self):
        result = normalize_url_for_display("")
        assert result == ""

    def test_with_spaces(self):
        result = normalize_url_for_display("  example.com  ")
        assert result == "https://example.com"

    def test_mailto_url(self):
        result = normalize_url_for_display("mailto:test@example.com")
        assert result == "mailto:test@example.com"

    def test_ftp_url(self):
        result = normalize_url_for_display("ftp://files.example.com")
        assert result == "ftp://files.example.com"


class TestDetectUrlsInText:
    """Test detect_urls_in_text function"""

    def test_single_url(self):
        text = "Visit https://example.com for info"
        urls = detect_urls_in_text(text)
        assert len(urls) == 1
        assert urls[0][0] == "https://example.com"

    def test_multiple_urls(self):
        text = "Check https://example.com and http://test.org"
        urls = detect_urls_in_text(text)
        assert len(urls) == 2
        assert urls[0][0] == "https://example.com"
        assert urls[1][0] == "http://test.org"

    def test_no_urls(self):
        text = "Just plain text with no URLs"
        urls = detect_urls_in_text(text)
        assert len(urls) == 0

    def test_url_positions(self):
        text = "Visit https://example.com here"
        urls = detect_urls_in_text(text)
        url, start, end = urls[0]
        assert text[start:end] == url

    def test_url_with_trailing_punctuation(self):
        """Test URL followed by punctuation"""
        text = "Visit https://example.com. More text"
        urls = detect_urls_in_text(text)
        assert len(urls) == 1
        # Trailing period should be stripped
        assert urls[0][0] == "https://example.com"

    def test_url_in_parentheses(self):
        """Test URL in parentheses"""
        text = "See documentation (https://example.com) for details"
        urls = detect_urls_in_text(text)
        assert len(urls) == 1
        # Trailing ) should be stripped
        assert urls[0][0] == "https://example.com"

    def test_url_at_end_of_sentence(self):
        """Test URL at end with multiple punctuation"""
        text = "Visit https://example.com!"
        urls = detect_urls_in_text(text)
        assert len(urls) == 1
        assert urls[0][0] == "https://example.com"

    def test_protocol_relative_url(self):
        """Test protocol-relative URL"""
        text = "See //example.com for info"
        urls = detect_urls_in_text(text)
        assert len(urls) == 1
        assert urls[0][0] == "//example.com"

    def test_url_with_query_params(self):
        """Test URL with query parameters"""
        text = "Search at https://example.com/search?q=test&lang=en"
        urls = detect_urls_in_text(text)
        assert len(urls) == 1
        assert "search?q=test&lang=en" in urls[0][0]

    def test_multiline_text(self):
        """Test URLs in multiline text"""
        text = """First line with https://example.com
        Second line with http://test.org
        Third line with no URL"""
        urls = detect_urls_in_text(text)
        assert len(urls) == 2


class TestReplaceUrlsWithMarkdown:
    """Test replace_urls_with_markdown function"""

    def test_basic_replacement(self):
        text = "Visit https://example.com for info"
        result = replace_urls_with_markdown(text)
        assert "[https://example.com](https://example.com)" in result

    def test_preserve_inline_code(self):
        text = "Use `https://api.example.com/v1` for API"
        result = replace_urls_with_markdown(text)
        assert "`https://api.example.com/v1`" in result
        assert "[https://api.example.com/v1]" not in result

    def test_preserve_existing_links(self):
        text = "See [docs](https://example.com) for details"
        result = replace_urls_with_markdown(text)
        assert text == result  # Should be unchanged

    def test_mixed_content(self):
        text = """Visit https://example.com for info.

Code: `https://api.example.com`

Link: [Documentation](https://docs.example.com)
"""
        result = replace_urls_with_markdown(text)
        # First URL should be formatted
        assert "[https://example.com](https://example.com)" in result
        # Code URL should be preserved
        assert "`https://api.example.com`" in result
        # Existing link should be preserved
        assert "[Documentation](https://docs.example.com)" in result

    def test_preserve_fenced_code_blocks(self):
        """Test that URLs in fenced code blocks are preserved"""
        text = """Normal text https://example.com

```
Code block with https://code.example.com
```

More text https://test.org
"""
        result = replace_urls_with_markdown(text)
        assert "[https://example.com](https://example.com)" in result
        # Code block URL should be preserved
        assert "https://code.example.com" in result
        assert "[https://test.org](https://test.org)" in result

    def test_multiple_urls_in_line(self):
        """Test multiple URLs in same line"""
        text = "Compare https://example.com with https://test.org"
        result = replace_urls_with_markdown(text)
        assert "[https://example.com](https://example.com)" in result
        assert "[https://test.org](https://test.org)" in result

    def test_empty_text(self):
        """Test empty text"""
        result = replace_urls_with_markdown("")
        assert result == ""

    def test_text_without_urls(self):
        """Test text without URLs"""
        text = "This is plain text without any URLs"
        result = replace_urls_with_markdown(text)
        assert result == text

    def test_url_with_trailing_punctuation(self):
        """Test URL with trailing punctuation"""
        text = "Visit https://example.com. More text here."
        result = replace_urls_with_markdown(text)
        assert "[https://example.com](https://example.com)" in result
        assert "More text here" in result

    def test_disable_code_block_preservation(self):
        """Test with code block preservation disabled"""
        text = "Use `https://api.example.com` for API"
        result = replace_urls_with_markdown(text, preserve_code_blocks=False)
        # With preservation disabled, URL should still be formatted
        # (though this might break the code block formatting)
        assert "https://api.example.com" in result

    def test_url_in_list(self):
        """Test URLs in markdown list"""
        text = """
- Item 1: https://example.com
- Item 2: https://test.org
- Item 3: Regular text
"""
        result = replace_urls_with_markdown(text)
        assert "[https://example.com](https://example.com)" in result
        assert "[https://test.org](https://test.org)" in result

    def test_complex_markdown(self):
        """Test with complex markdown containing various elements"""
        text = """# Heading

Visit https://example.com for documentation.

## Code Example

```python
url = "https://api.example.com/v1"
response = requests.get(url)
```

See [official docs](https://docs.example.com) for more info.

Another URL: https://test.org
"""
        result = replace_urls_with_markdown(text)
        # First URL should be formatted
        assert "[https://example.com](https://example.com)" in result
        # Code block URL should be preserved
        assert 'url = "https://api.example.com/v1"' in result
        # Existing link should be preserved
        assert "[official docs](https://docs.example.com)" in result
        # Last URL should be formatted
        assert "[https://test.org](https://test.org)" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
