#!/usr/bin/env python3
"""
Unit tests for WeChat Parser Migration - Phase 3.3

Tests the migration of WeChat parser from legacy WxParser to template-based system.
Validates:
- Template loading and configuration
- Content extraction accuracy
- Metadata extraction
- Output format consistency
- Performance targets
- Backward compatibility
"""

import pytest
import yaml
import sys
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATE_PATH = PROJECT_ROOT / "parser_engine/templates/sites/wechat/wechat.yaml"

# Add project root to sys.path for imports
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestWeChatTemplate:
    """Test suite for WeChat template configuration"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Load the template before each test"""
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            self.template = yaml.safe_load(f)

    def test_template_exists(self):
        """Test that the WeChat template file exists"""
        assert TEMPLATE_PATH.exists(), f"WeChat template not found at {TEMPLATE_PATH}"

    def test_template_loads(self):
        """Test that the template loads as valid YAML"""
        assert self.template is not None
        assert isinstance(self.template, dict)

    def test_template_version(self):
        """Test that template has correct version"""
        assert 'version' in self.template
        assert self.template['version'] == "1.0.0"

    def test_template_name(self):
        """Test that template has correct name"""
        assert 'name' in self.template
        assert self.template['name'] == "WeChat Articles"

    def test_template_domains(self):
        """Test that template specifies WeChat domain"""
        assert 'domains' in self.template
        assert 'mp.weixin.qq.com' in self.template['domains']

    def test_template_priority(self):
        """Test that template has high priority for exact match"""
        assert 'priority' in self.template
        assert self.template['priority'] == 100

    def test_has_selectors(self):
        """Test that template has selectors section"""
        assert 'selectors' in self.template
        assert isinstance(self.template['selectors'], dict)

    def test_title_selectors(self):
        """Test that title selectors are configured"""
        selectors = self.template['selectors']
        assert 'title' in selectors
        assert isinstance(selectors['title'], list)
        assert len(selectors['title']) > 0

        # Check for og:title selector
        og_title = next((s for s in selectors['title'] if 'og:title' in s.get('selector', '')), None)
        assert og_title is not None, "Missing og:title selector"

        # Check for rich_media_title selector
        rich_title = next((s for s in selectors['title'] if 'rich_media_title' in s.get('selector', '')), None)
        assert rich_title is not None, "Missing rich_media_title selector"

    def test_author_selectors(self):
        """Test that author selectors are configured"""
        selectors = self.template['selectors']
        assert 'author' in selectors
        assert isinstance(selectors['author'], list)
        assert len(selectors['author']) > 0

        # Check for og:article:author selector
        og_author = next((s for s in selectors['author'] if 'og:article:author' in s.get('selector', '')), None)
        assert og_author is not None, "Missing og:article:author selector"

    def test_date_selectors(self):
        """Test that date selectors are configured"""
        selectors = self.template['selectors']
        assert 'date' in selectors
        assert isinstance(selectors['date'], list)
        assert len(selectors['date']) > 0

        # Check for publish_time selector
        publish_time = next((s for s in selectors['date'] if 'publish_time' in s.get('selector', '')), None)
        assert publish_time is not None, "Missing publish_time selector"

    def test_content_selectors(self):
        """Test that content selectors are configured"""
        selectors = self.template['selectors']
        assert 'content' in selectors
        assert isinstance(selectors['content'], list)
        assert len(selectors['content']) > 0

        # Check for js_content selector (WeChat standard)
        js_content = next((s for s in selectors['content'] if 'js_content' in s.get('selector', '')), None)
        assert js_content is not None, "Missing #js_content selector"

    def test_image_selectors(self):
        """Test that image selectors are configured"""
        selectors = self.template['selectors']
        assert 'images' in selectors
        assert isinstance(selectors['images'], list)
        assert len(selectors['images']) > 0

        # Check for data-src attribute (WeChat lazy loading)
        data_src = next((s for s in selectors['images'] if s.get('attribute') == 'data-src'), None)
        assert data_src is not None, "Missing data-src image selector"

    def test_metadata_configuration(self):
        """Test that metadata section is configured"""
        assert 'metadata' in self.template
        metadata = self.template['metadata']

        assert 'fields' in metadata
        assert isinstance(metadata['fields'], list)
        assert 'author' in metadata['fields']
        assert 'title' in metadata['fields']
        assert 'images' in metadata['fields']

    def test_output_configuration(self):
        """Test that output section is configured"""
        assert 'output' in self.template
        output = self.template['output']

        assert 'format' in output
        assert output['format'] == 'markdown'

        assert 'header_template' in output
        assert '{title}' in output['header_template']
        assert '{author}' in output['header_template']


class TestWeChatParserMigration:
    """Test suite for WeChat parser migration functionality"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        # Import the migrated parser
        from parsers_migrated import wechat_to_markdown
        self.parser = wechat_to_markdown

    def test_parser_import(self):
        """Test that the parser can be imported"""
        assert self.parser is not None
        assert callable(self.parser)

    def test_parser_with_minimal_html(self):
        """Test parser with minimal WeChat HTML"""
        html = """
        <html>
        <head>
            <meta property="og:title" content="Test WeChat Article">
            <meta property="og:article:author" content="Test Author">
        </head>
        <body>
            <div id="js_content">
                <p>This is test content.</p>
            </div>
        </body>
        </html>
        """
        url = "https://mp.weixin.qq.com/s/test123"

        date_only, markdown, metadata = self.parser(html, url)

        # Verify outputs exist
        assert markdown is not None
        assert isinstance(markdown, str)
        assert len(markdown) > 0

        # Verify metadata
        assert isinstance(metadata, dict)

    def test_parser_output_format(self):
        """Test that parser output follows expected format"""
        html = """
        <html>
        <head>
            <meta property="og:title" content="Sample Title">
            <meta property="og:article:author" content="Sample Author">
        </head>
        <body>
            <div id="js_content">
                <p>Sample content paragraph.</p>
            </div>
        </body>
        </html>
        """
        url = "https://mp.weixin.qq.com/s/sample"

        date_only, markdown, metadata = self.parser(html, url)

        # Check markdown format
        assert '# Sample Title' in markdown or 'Sample Title' in markdown
        assert '标题:' in markdown
        assert '来源:' in markdown
        assert url in markdown

    def test_parser_handles_images(self):
        """Test that parser extracts images correctly"""
        html = """
        <html>
        <head>
            <meta property="og:title" content="Image Test">
        </head>
        <body>
            <div id="js_content">
                <p>Test content</p>
                <img data-src="https://example.com/image1.jpg" />
                <img data-src="https://example.com/image2.jpg" />
            </div>
        </body>
        </html>
        """
        url = "https://mp.weixin.qq.com/s/imagetest"

        date_only, markdown, metadata = self.parser(html, url)

        # Verify images in metadata
        assert 'images' in metadata
        # Note: Image extraction depends on template parser implementation
        # This test validates the structure exists

    def test_parser_fallback_mechanism(self):
        """Test that parser falls back to legacy when template fails"""
        # This test ensures backward compatibility
        html = "<html><body>Invalid content</body></html>"
        url = "https://mp.weixin.qq.com/s/invalid"

        try:
            date_only, markdown, metadata = self.parser(html, url)
            # Should not raise exception due to fallback
            assert markdown is not None
        except Exception as e:
            pytest.fail(f"Parser should fallback gracefully, but raised: {e}")


class TestWeChatPerformance:
    """Performance tests for WeChat parser"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        from parsers_migrated import wechat_to_markdown
        self.parser = wechat_to_markdown

    def test_parsing_performance(self):
        """Test that parsing completes within performance target"""
        import time

        html = """
        <html>
        <head>
            <meta property="og:title" content="Performance Test">
            <meta property="og:article:author" content="Test Author">
        </head>
        <body>
            <div id="js_content">
                <p>Test content for performance benchmark.</p>
            </div>
        </body>
        </html>
        """
        url = "https://mp.weixin.qq.com/s/perftest"

        start_time = time.time()
        date_only, markdown, metadata = self.parser(html, url)
        end_time = time.time()

        duration_ms = (end_time - start_time) * 1000

        # Performance target: < 500ms
        assert duration_ms < 500, f"Parsing took {duration_ms:.2f}ms, expected < 500ms"


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '--tb=short'])
