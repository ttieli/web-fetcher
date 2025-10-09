#!/usr/bin/env python3
"""
Routing Verification Test for Phase 3.5

Tests that webfetcher.py correctly routes different URL types to the appropriate parsers:
- WeChat URLs → wechat_to_markdown
- XiaoHongShu URLs → xhs_to_markdown
- Generic URLs → generic_to_markdown
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from parsers import wechat_to_markdown, xhs_to_markdown, generic_to_markdown


class TestParserRouting:
    """Test suite for parser routing verification"""

    def test_wechat_routing(self):
        """Verify WeChat parser routes to template-based implementation"""
        # Sample WeChat HTML
        html = """
        <html>
        <head><meta property="og:title" content="Test WeChat Article"></head>
        <body>
            <div id="js_content">Test content</div>
        </body>
        </html>
        """
        url = "https://mp.weixin.qq.com/s/test123"

        # Call the routing function
        with patch('parsers.wechat_to_markdown_migrated') as mock_migrated:
            mock_migrated.return_value = ("2025-01-15", "# Test Content", {"title": "Test"})

            date, content, metadata = wechat_to_markdown(html, url)

            # Verify the migrated function was called
            mock_migrated.assert_called_once_with(html, url)

    def test_xhs_routing(self):
        """Verify XiaoHongShu parser routes to template-based implementation"""
        # Sample XHS HTML
        html = """
        <html>
        <head><title>Test XHS Post</title></head>
        <body>
            <div class="content">Test content</div>
        </body>
        </html>
        """
        url = "https://www.xiaohongshu.com/explore/test123"

        # Call the routing function
        with patch('parsers.xhs_to_markdown_migrated') as mock_migrated:
            mock_migrated.return_value = ("2025-01-15", "# Test Content", {"title": "Test"})

            date, content, metadata = xhs_to_markdown(html, url)

            # Verify the migrated function was called
            mock_migrated.assert_called_once_with(html, url)

    def test_generic_routing(self):
        """Verify generic parser routes to template-based implementation"""
        # Sample generic HTML
        html = """
        <html>
        <head><title>Generic Article</title></head>
        <body>
            <article>Test content</article>
        </body>
        </html>
        """
        url = "https://example.com/article"

        # Call the routing function
        with patch('parsers.generic_to_markdown_migrated') as mock_migrated:
            mock_migrated.return_value = ("2025-01-15", "# Test Content", {"title": "Test"})

            date, content, metadata = generic_to_markdown(html, url)

            # Verify the migrated function was called
            mock_migrated.assert_called_once_with(html, url, 'safe', False)

    def test_wechat_returns_valid_tuple(self):
        """Verify WeChat parser returns valid tuple structure"""
        html = "<html><body>Test</body></html>"
        url = "https://mp.weixin.qq.com/s/test"

        result = wechat_to_markdown(html, url)

        # Verify it returns a 3-tuple
        assert isinstance(result, tuple)
        assert len(result) == 3

        date, content, metadata = result
        assert isinstance(date, str)
        assert isinstance(content, str)
        assert isinstance(metadata, dict)

    def test_xhs_returns_valid_tuple(self):
        """Verify XHS parser returns valid tuple structure"""
        html = "<html><body>Test</body></html>"
        url = "https://www.xiaohongshu.com/explore/test"

        result = xhs_to_markdown(html, url)

        # Verify it returns a 3-tuple
        assert isinstance(result, tuple)
        assert len(result) == 3

        date, content, metadata = result
        assert isinstance(date, str)
        assert isinstance(content, str)
        assert isinstance(metadata, dict)

    def test_generic_returns_valid_tuple(self):
        """Verify generic parser returns valid tuple structure"""
        html = "<html><body>Test</body></html>"
        url = "https://example.com/test"

        result = generic_to_markdown(html, url)

        # Verify it returns a 3-tuple
        assert isinstance(result, tuple)
        assert len(result) == 3

        date, content, metadata = result
        assert isinstance(date, str)
        assert isinstance(content, str)
        assert isinstance(metadata, dict)

    def test_routing_with_invalid_html(self):
        """Test routing handles invalid HTML gracefully"""
        invalid_html = "<<<invalid>>>"

        # All parsers should handle invalid HTML without crashing
        try:
            wechat_to_markdown(invalid_html, "https://mp.weixin.qq.com/s/test")
            xhs_to_markdown(invalid_html, "https://www.xiaohongshu.com/test")
            generic_to_markdown(invalid_html, "https://example.com/test")
        except Exception as e:
            pytest.fail(f"Parser routing crashed on invalid HTML: {e}")

    def test_routing_with_empty_content(self):
        """Test routing handles empty content gracefully"""
        empty_html = "<html><head></head><body></body></html>"

        # All parsers should handle empty content without crashing
        try:
            date1, content1, meta1 = wechat_to_markdown(empty_html, "https://mp.weixin.qq.com/s/test")
            date2, content2, meta2 = xhs_to_markdown(empty_html, "https://www.xiaohongshu.com/test")
            date3, content3, meta3 = generic_to_markdown(empty_html, "https://example.com/test")

            # All should return valid tuples even with empty content
            assert isinstance(date1, str) and isinstance(content1, str) and isinstance(meta1, dict)
            assert isinstance(date2, str) and isinstance(content2, str) and isinstance(meta2, dict)
            assert isinstance(date3, str) and isinstance(content3, str) and isinstance(meta3, dict)
        except Exception as e:
            pytest.fail(f"Parser routing crashed on empty content: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
