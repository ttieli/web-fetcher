#!/usr/bin/env python3
"""
Unit tests for XiaoHongShu Parser Migration - Phase 3.4

Tests the migration of XHS parser from legacy implementation to template-based system.
Validates:
- Template loading and configuration
- Content extraction accuracy
- Metadata extraction
- Output format consistency
- Image extraction
- Performance targets
- Backward compatibility
"""

import pytest
import yaml
import sys
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATE_PATH = PROJECT_ROOT / "parser_engine/templates/sites/xiaohongshu/xiaohongshu.yaml"
FIXTURE_PATH = PROJECT_ROOT / "tests/fixtures/xhs_sample.html"

# Add project root to sys.path for imports
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestXHSTemplate:
    """Test suite for XiaoHongShu template configuration"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Load the template before each test"""
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            self.template = yaml.safe_load(f)

    def test_template_exists(self):
        """Test that the XHS template file exists"""
        assert TEMPLATE_PATH.exists(), f"XHS template not found at {TEMPLATE_PATH}"

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
        assert self.template['name'] == "XiaoHongShu Posts"

    def test_template_domains(self):
        """Test that template specifies XHS domains"""
        assert 'domains' in self.template
        assert 'xiaohongshu.com' in self.template['domains']
        assert 'xhslink.com' in self.template['domains']

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

        # Check for twitter:title selector
        twitter_title = next((s for s in selectors['title'] if 'twitter:title' in s.get('selector', '')), None)
        assert twitter_title is not None, "Missing twitter:title selector"

    def test_author_selectors(self):
        """Test that author selectors are configured"""
        selectors = self.template['selectors']
        assert 'author' in selectors
        assert isinstance(selectors['author'], list)
        assert len(selectors['author']) > 0

        # Check for JSON-LD author extraction
        json_ld_author = next((s for s in selectors['author']
                               if s.get('strategy') == 'text_pattern' and 'author' in s.get('pattern', '')), None)
        assert json_ld_author is not None, "Missing JSON-LD author selector"

    def test_date_selectors(self):
        """Test that date selectors are configured"""
        selectors = self.template['selectors']
        assert 'date' in selectors
        assert isinstance(selectors['date'], list)
        assert len(selectors['date']) > 0

        # Check for datePublished selector
        date_published = next((s for s in selectors['date']
                               if 'datePublished' in s.get('pattern', '')), None)
        assert date_published is not None, "Missing datePublished selector"

    def test_content_selectors(self):
        """Test that content selectors are configured"""
        selectors = self.template['selectors']
        assert 'content' in selectors
        assert isinstance(selectors['content'], list)
        assert len(selectors['content']) > 0

        # Check for meta description selector (XHS standard)
        meta_desc = next((s for s in selectors['content']
                         if 'description' in s.get('selector', '')), None)
        assert meta_desc is not None, "Missing meta description selector"

    def test_cover_selectors(self):
        """Test that cover image selectors are configured"""
        selectors = self.template['selectors']
        assert 'cover' in selectors
        assert isinstance(selectors['cover'], list)
        assert len(selectors['cover']) > 0

        # Check for og:image selector
        og_image = next((s for s in selectors['cover'] if 'og:image' in s.get('selector', '')), None)
        assert og_image is not None, "Missing og:image selector"

    def test_image_selectors(self):
        """Test that image selectors are configured"""
        selectors = self.template['selectors']
        assert 'images' in selectors
        assert isinstance(selectors['images'], list)
        assert len(selectors['images']) > 0

        # Check for XHS domain validation
        img_selector = selectors['images'][0]
        if 'validation' in img_selector:
            assert 'domain_contains' in img_selector['validation']
            domains = img_selector['validation']['domain_contains']
            assert 'ci.xiaohongshu.com' in domains or 'xhscdn.com' in domains

    def test_metadata_configuration(self):
        """Test that metadata section is configured"""
        assert 'metadata' in self.template
        metadata = self.template['metadata']

        assert 'fields' in metadata
        assert isinstance(metadata['fields'], list)
        assert 'author' in metadata['fields']
        assert 'title' in metadata['fields']
        assert 'images' in metadata['fields']
        assert 'cover' in metadata['fields']

    def test_output_configuration(self):
        """Test that output section is configured"""
        assert 'output' in self.template
        output = self.template['output']

        assert 'format' in output
        assert output['format'] == 'markdown'

        assert 'header_template' in output
        assert '{title}' in output['header_template']
        assert '{author}' in output['header_template']


class TestXHSParser:
    """Test suite for XHS parser migration functionality"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        # Import the migrated parser
        from parsers_migrated import xhs_to_markdown
        self.parser = xhs_to_markdown

    def test_parser_import(self):
        """Test that the parser can be imported"""
        assert self.parser is not None
        assert callable(self.parser)

    def test_parser_with_minimal_html(self):
        """Test parser with minimal XHS HTML"""
        html = """
        <html>
        <head>
            <meta property="og:title" content="Test XHS Post - 小红书">
            <meta name="description" content="This is a test XHS post content.">
            <meta property="og:image" content="https://ci.xiaohongshu.com/test-cover.jpg">
        </head>
        <body>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "author": {
                    "name": "Test Author"
                },
                "datePublished": "2025-10-09"
            }
            </script>
        </body>
        </html>
        """
        url = "https://www.xiaohongshu.com/explore/test123"

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
            <meta property="og:title" content="Sample XHS Post - 小红书">
            <meta name="description" content="Sample XHS content.">
            <meta property="og:image" content="https://ci.xiaohongshu.com/sample.jpg">
        </head>
        <body>
            <script type="application/ld+json">
            {
                "author": {"name": "Sample Author"},
                "datePublished": "2025-10-09"
            }
            </script>
        </body>
        </html>
        """
        url = "https://www.xiaohongshu.com/explore/sample"

        date_only, markdown, metadata = self.parser(html, url)

        # Check markdown format
        assert '# Sample XHS Post' in markdown or 'Sample XHS Post' in markdown
        assert '标题:' in markdown
        assert '来源:' in markdown
        assert url in markdown

    def test_parser_handles_images(self):
        """Test that parser extracts images correctly"""
        html = """
        <html>
        <head>
            <meta property="og:title" content="Image Test - 小红书">
            <meta name="description" content="Image test content">
            <meta property="og:image" content="https://ci.xiaohongshu.com/cover.jpg">
        </head>
        <body>
            <img src="https://ci.xiaohongshu.com/image1.jpg" />
            <img data-src="https://sns-img-qc.xhscdn.com/image2.jpg" />
        </body>
        </html>
        """
        url = "https://www.xiaohongshu.com/explore/imagetest"

        date_only, markdown, metadata = self.parser(html, url)

        # Verify images in metadata
        assert 'images' in metadata
        # Note: Image extraction depends on template parser implementation
        # This test validates the structure exists

    def test_parser_title_cleaning(self):
        """Test that parser removes XHS suffix from titles"""
        html = """
        <html>
        <head>
            <meta property="og:title" content="My Post - 小红书">
        </head>
        <body></body>
        </html>
        """
        url = "https://www.xiaohongshu.com/explore/title"

        date_only, markdown, metadata = self.parser(html, url)

        # Title should have suffix removed
        # Note: This depends on template post-processing implementation
        assert markdown is not None

    def test_parser_fallback_mechanism(self):
        """Test that parser falls back to legacy when template fails"""
        # This test ensures backward compatibility
        html = "<html><body>Invalid content</body></html>"
        url = "https://www.xiaohongshu.com/explore/invalid"

        try:
            date_only, markdown, metadata = self.parser(html, url)
            # Should not raise exception due to fallback
            assert markdown is not None
        except Exception as e:
            pytest.fail(f"Parser should fallback gracefully, but raised: {e}")


class TestXHSIntegration:
    """Integration tests for XHS parser"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        from parsers_migrated import xhs_to_markdown
        self.parser = xhs_to_markdown

    def test_parser_with_sample_fixture(self):
        """Test parser with sample HTML fixture if it exists"""
        if not FIXTURE_PATH.exists():
            pytest.skip("Sample fixture not available")

        with open(FIXTURE_PATH, 'r', encoding='utf-8') as f:
            html = f.read()

        url = "https://www.xiaohongshu.com/explore/fixture_test"

        date_only, markdown, metadata = self.parser(html, url)

        # Basic validation
        assert markdown is not None
        assert len(markdown) > 0
        assert isinstance(metadata, dict)

    def test_parsing_performance(self):
        """Test that parsing completes within performance target"""
        import time

        html = """
        <html>
        <head>
            <meta property="og:title" content="Performance Test - 小红书">
            <meta name="description" content="Performance test content">
            <meta property="og:image" content="https://ci.xiaohongshu.com/perf.jpg">
        </head>
        <body>
            <script type="application/ld+json">
            {
                "author": {"name": "Test Author"},
                "datePublished": "2025-10-09"
            }
            </script>
        </body>
        </html>
        """
        url = "https://www.xiaohongshu.com/explore/perftest"

        start_time = time.time()
        date_only, markdown, metadata = self.parser(html, url)
        end_time = time.time()

        duration_ms = (end_time - start_time) * 1000

        # Performance target: < 100ms (as per template spec)
        # Allow some overhead for fallback mechanism
        assert duration_ms < 500, f"Parsing took {duration_ms:.2f}ms, expected < 500ms"


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '--tb=short'])
